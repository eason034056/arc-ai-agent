"""
Writeback Node

This node writes transaction results back to external systems.

Responsibilities:
- Send transaction data to expense system webhook
- Update internal database with transaction records
- Handle failures with retry logic
- Dead letter queue for failed webhooks

External systems might include:
- Expense management system
- Accounting software (QuickBooks, Xero, etc.)
- HRIS (Human Resources Information System)
- Data warehouse
"""

import json
from datetime import datetime
from typing import Dict, Any

from app.db.schema import AgentState
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def run(state: AgentState, webhook_client=None, db_repo=None) -> AgentState:
    """
    Write transaction results to external systems
    
    Args:
        state: Current agent state (with tx_hashes)
        webhook_client: HTTP client for webhook calls
        db_repo: Database repository for storing records
        
    Returns:
        Updated state with writeback status
        
    Example:
        state = AgentState(
            batch_id="batch_123",
            month="2025-11",
            lines=[...],
            tx_hashes=["0xabc123...", "0xdef456..."]
        )
        
        new_state = run(state, webhook_client)
        
        print(new_state.metadata["writeback_complete"])  # True
    """
    settings = get_settings()
    
    logger.info(
        "Starting transaction writeback",
        extra={
            "batch_id": state.batch_id,
            "tx_count": len(state.tx_hashes)
        }
    )
    
    errors = list(state.errors)
    
    # ========================================
    # PREPARE WEBHOOK PAYLOAD
    # ========================================
    payload = prepare_webhook_payload(state)
    
    # ========================================
    # SEND TO EXPENSE SYSTEM WEBHOOK
    # ========================================
    if settings.expense_webhook_url:
        try:
            if webhook_client:
                # Send POST request to webhook
                # See app/expense/webhook.py for client implementation
                response = send_expense_webhook(
                    webhook_client,
                    settings.expense_webhook_url,
                    payload,
                    settings.expense_webhook_token
                )
                
                logger.info(
                    "Expense webhook sent successfully",
                    extra={
                        "batch_id": state.batch_id,
                        "response_status": response.get("status")
                    }
                )
            else:
                logger.warning(
                    "No webhook client provided, skipping webhook",
                    extra={"batch_id": state.batch_id}
                )
        
        except Exception as e:
            error_msg = f"Expense webhook failed: {str(e)}"
            errors.append(error_msg)
            
            logger.error(
                "Expense webhook error",
                extra={
                    "batch_id": state.batch_id,
                    "error": str(e)
                },
                exc_info=True
            )
            
            # TODO: Add to dead letter queue for retry
    else:
        logger.info(
            "No expense webhook URL configured, skipping",
            extra={"batch_id": state.batch_id}
        )
    
    # ========================================
    # SAVE TO DATABASE
    # ========================================
    if db_repo:
        try:
            # Save transaction records to database
            # See app/db/repository.py for implementation
            db_repo.save_batch_transactions(
                batch_id=state.batch_id,
                month=state.month,
                lines=state.lines,
                tx_hashes=state.tx_hashes,
                approval=state.approval
            )
            
            logger.info(
                "Batch saved to database",
                extra={"batch_id": state.batch_id}
            )
        
        except Exception as e:
            error_msg = f"Database save failed: {str(e)}"
            errors.append(error_msg)
            
            logger.error(
                "Database save error",
                extra={
                    "batch_id": state.batch_id,
                    "error": str(e)
                },
                exc_info=True
            )
    
    # ========================================
    # UPDATE STATE
    # ========================================
    new_state = state.model_copy(
        update={
            "errors": errors,
            "metadata": {
                **state.metadata,
                "writeback_complete": True,
                "writeback_timestamp": datetime.utcnow().isoformat()
            }
        }
    )
    
    return new_state


def prepare_webhook_payload(state: AgentState) -> Dict[str, Any]:
    """
    Prepare payload for expense system webhook
    
    Args:
        state: Agent state with transaction results
        
    Returns:
        Dictionary payload ready for JSON serialization
        
    Example:
        payload = prepare_webhook_payload(state)
        
        print(json.dumps(payload, indent=2))
        # {
        #   "batch_id": "batch_123",
        #   "month": "2025-11",
        #   "transactions": [...],
        #   "total_amount": "26700.00",
        #   "recipient_count": 5,
        #   "timestamp": "2025-11-04T10:30:00"
        # }
    """
    # Calculate totals
    total_amount = sum(line.amount_usdc for line in state.lines)
    
    # Format transaction details
    transactions = []
    for tx_hash in state.tx_hashes:
        transactions.append({
            "tx_hash": tx_hash,
            "network": "arc_testnet",
            "status": "submitted",  # Initial status
        })
    
    # Format payroll lines
    payroll_lines = [
        {
            "employee_id": line.employee_id,
            "wallet": line.wallet,
            "amount": str(line.amount_usdc),
            "flags": line.flags
        }
        for line in state.lines
    ]
    
    payload = {
        "batch_id": state.batch_id,
        "month": state.month,
        "transactions": transactions,
        "payroll_lines": payroll_lines,
        "total_amount": str(total_amount),
        "recipient_count": len(state.lines),
        "approval": state.approval,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return payload


def send_expense_webhook(
    client,
    url: str,
    payload: Dict[str, Any],
    auth_token: str = None
) -> Dict[str, Any]:
    """
    Send POST request to expense webhook
    
    Args:
        client: HTTP client (requests or httpx)
        url: Webhook URL
        payload: Data to send
        auth_token: Optional authentication token
        
    Returns:
        Response data
        
    Raises:
        Exception: If webhook call fails
        
    Example:
        import requests
        
        response = send_expense_webhook(
            client=requests,
            url="https://expense.example.com/webhook",
            payload=payload,
            auth_token="secret_token_123"
        )
    """
    headers = {
        "Content-Type": "application/json"
    }
    
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    # Send POST request
    response = client.post(
        url,
        json=payload,
        headers=headers,
        timeout=30  # 30 second timeout
    )
    
    # Check response
    response.raise_for_status()  # Raises exception for 4xx/5xx
    
    return response.json()

