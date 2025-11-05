"""
Approve Gate Node

This node waits for human approval from Slack.
It's a blocking node that pauses the workflow until a decision is made.

Approval Options:
- APPROVE_ALL: Process all payroll lines
- APPROVE_PARTIAL: Process only selected lines
- REJECT: Cancel the batch

This node polls the database for approval status.
When a user clicks a button in Slack, the Slack webhook updates the database,
and this node detects the change.
"""

import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from app.db.schema import AgentState
from app.agent.policies import PayrollPolicy
from app.core.logging import get_logger
from app.db.connection import SessionLocal
from app.db.models import Approval, ApprovalDecision

logger = get_logger(__name__)


def run(
    state: AgentState,
    policy: PayrollPolicy = None,
    approval_repo=None
) -> AgentState:
    """
    Wait for approval decision
    
    This node blocks until:
    1. An approval is received
    2. Timeout is reached
    3. An error occurs
    
    Args:
        state: Current agent state
        policy: Payroll policy (for timeout setting)
        approval_repo: Repository for checking approval status
        
    Returns:
        Updated state with approval decision
        
    Example:
        state = AgentState(
            batch_id="batch_123",
            month="2025-11",
            lines=[...],
            approval=None  # No decision yet
        )
        
        # This call blocks until approval received
        new_state = run(state)
        
        print(new_state.approval)
        # {"decision": "APPROVE_ALL", "approver": "U01234", "timestamp": "..."}
    """
    if policy is None:
        policy = PayrollPolicy()
    
    logger.info(
        "Waiting for approval",
        extra={
            "batch_id": state.batch_id,
            "timeout_minutes": policy.approval_timeout_minutes
        }
    )
    
    # ========================================
    # CALCULATE TIMEOUT
    # ========================================
    timeout_minutes = policy.approval_timeout_minutes
    deadline = datetime.utcnow() + timedelta(minutes=timeout_minutes)
    
    # Poll interval (seconds)
    poll_interval = 5
    
    # ========================================
    # POLLING LOOP
    # ========================================
    # Keep checking for approval until we get one or timeout
    
    approval: Optional[Dict[str, Any]] = None
    
    while datetime.utcnow() < deadline:
        # Check for approval in database
        # Query directly from database if approval_repo is not provided
        if approval_repo:
            approval_dict = approval_repo.get_approval(state.batch_id)
            if approval_dict and approval_dict.get("decision") != "PENDING":
                approval = approval_dict
                logger.info(
                    "Approval received",
                    extra={
                        "batch_id": state.batch_id,
                        "decision": approval["decision"],
                        "approver": approval.get("approver")
                    }
                )
                break
        else:
            # Direct database query (fallback)
            db = SessionLocal()
            try:
                approval_record = db.query(Approval).filter_by(
                    batch_id=state.batch_id
                ).order_by(Approval.created_at.desc()).first()
                
                if approval_record and approval_record.decision != ApprovalDecision.PENDING:
                    # Convert to dict
                    approval = {
                        "decision": approval_record.decision.value.upper(),
                        "approver": approval_record.approver,
                        "timestamp": approval_record.created_at.isoformat(),
                        "selected_ids": approval_record.selected_ids,
                        "comment": approval_record.comment
                    }
                    logger.info(
                        "Approval received (direct query)",
                        extra={
                            "batch_id": state.batch_id,
                            "decision": approval["decision"],
                            "approver": approval.get("approver")
                        }
                    )
                    break
            except Exception as e:
                logger.error(
                    "Error checking approval",
                    extra={"batch_id": state.batch_id, "error": str(e)},
                    exc_info=True
                )
            finally:
                db.close()
        
        # No decision yet, wait and retry
        time.sleep(poll_interval)
        
        logger.debug(
            "Still waiting for approval",
            extra={
                "batch_id": state.batch_id,
                "elapsed_minutes": (datetime.utcnow() - (deadline - timedelta(minutes=timeout_minutes))).seconds // 60
            }
        )
    
    # ========================================
    # HANDLE TIMEOUT
    # ========================================
    if not approval or approval.get("decision") == "PENDING":
        logger.warning(
            "Approval timeout reached",
            extra={
                "batch_id": state.batch_id,
                "timeout_minutes": timeout_minutes
            }
        )
        
        # Default to reject on timeout
        approval = {
            "decision": "REJECT",
            "approver": "SYSTEM",
            "reason": "Timeout",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # ========================================
    # HANDLE PARTIAL APPROVAL
    # ========================================
    # If partial approval, filter lines to only approved ones
    if approval["decision"] == "APPROVE_PARTIAL":
        selected_ids = approval.get("selected_ids", [])
        
        if not selected_ids:
            logger.warning(
                "Partial approval with no selections, treating as reject",
                extra={"batch_id": state.batch_id}
            )
            approval["decision"] = "REJECT"
        else:
            # Filter lines to only selected employees
            filtered_lines = [
                line for line in state.lines
                if line.employee_id in selected_ids
            ]
            
            logger.info(
                "Partial approval applied",
                extra={
                    "batch_id": state.batch_id,
                    "original_count": len(state.lines),
                    "approved_count": len(filtered_lines)
                }
            )
            
            # Update state with filtered lines
            new_state = state.model_copy(
                update={
                    "lines": filtered_lines,
                    "approval": approval
                }
            )
            
            return new_state
    
    # ========================================
    # UPDATE STATE
    # ========================================
    new_state = state.model_copy(
        update={"approval": approval}
    )
    
    return new_state


def wait_for_approval_async(
    batch_id: str,
    timeout_minutes: int,
    approval_repo
) -> Dict[str, Any]:
    """
    Asynchronous version of approval waiting
    
    This could be used with asyncio for better performance.
    For simplicity, the main run() function uses blocking polling.
    
    Args:
        batch_id: Batch identifier
        timeout_minutes: How long to wait
        approval_repo: Repository for checking approval
        
    Returns:
        Approval decision dictionary
    """
    # Placeholder for async implementation
    raise NotImplementedError("Async version not implemented")

