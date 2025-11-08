"""
Propose Node

This node prepares the approval request and sends it to Slack.
It creates an approval card with batch summary and action buttons.

Responsibilities:
- Create PayrollBatch record in database (NEW!)
- Format summary for Slack Block Kit
- Create approval card
- Send message to Slack channel
- Store message timestamp for later updates
"""

from typing import Dict, Any
import asyncio
from datetime import datetime

from app.db.schema import AgentState
from app.core.logging import get_logger

logger = get_logger(__name__)


def run(state: AgentState, slack_client=None) -> AgentState:
    """
    Prepare and send approval request to Slack
    
    Args:
        state: Current agent state
        slack_client: Slack client (injected dependency)
        
    Returns:
        Updated state with Slack message timestamp
        
    Example:
        state = AgentState(
            batch_id="batch_123",
            month="2025-11",
            lines=[...],
            metadata={"summary": {...}}
        )
        
        new_state = run(state, slack_client)
        
        # Message sent to Slack, timestamp stored
        print(new_state.metadata["slack_ts"])  # "1699012345.123456"
    """
    logger.info(
        "Preparing approval request",
        extra={"batch_id": state.batch_id}
    )
    
    # Get summary from metadata
    summary = state.metadata.get("summary", {})
    
    if not summary:
        error_msg = "No summary available for approval request"
        logger.error(error_msg, extra={"batch_id": state.batch_id})
        
        new_state = state.model_copy(
            update={
                "errors": state.errors + [error_msg]
            }
        )
        return new_state
    
    # ========================================
    # CREATE DATABASE RECORD (NEW!)
    # ========================================
    # This ensures the batch exists in DB before Slack buttons are clicked
    try:
        create_batch_in_database(state, summary)
    except Exception as e:
        logger.error(
            "Failed to create batch in database",
            extra={
                "batch_id": state.batch_id,
                "error": str(e)
            },
            exc_info=True
        )
        # Continue anyway - Slack handler will create it as fallback
    
    # ========================================
    # FORMAT FOR SLACK
    # ========================================
    # Create approval card blocks (see app/slack/templates.py for actual implementation)
    slack_blocks = format_approval_card(summary)
    
    # ========================================
    # SEND TO SLACK (if client provided)
    # ========================================
    slack_ts = None
    
    if slack_client:
        try:
            # Import Slack function (actual implementation in app/slack/)
            from app.slack.app import send_approval_request
            
            # Run async function in sync context
            # Use a new event loop in a separate thread to avoid conflicts
            import concurrent.futures
            
            def run_async():
                """Run async function in a new event loop"""
                return asyncio.run(
                    send_approval_request(
                        slack_client,
                        state.batch_id,
                        slack_blocks
                    )
                )
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_async)
                slack_ts = future.result(timeout=30)  # 30 second timeout
            
            logger.info(
                "Approval request sent to Slack",
                extra={
                    "batch_id": state.batch_id,
                    "slack_ts": slack_ts
                }
            )
            
        except Exception as e:
            logger.error(
                "Failed to send Slack message",
                extra={
                    "batch_id": state.batch_id,
                    "error": str(e)
                },
                exc_info=True
            )
            
            new_state = state.model_copy(
                update={
                    "errors": state.errors + [f"Slack error: {str(e)}"]
                }
            )
            return new_state
    else:
        logger.warning(
            "No Slack client provided, skipping Slack message",
            extra={"batch_id": state.batch_id}
        )
        
        # Log approval request details for debugging
        logger.info(
            "Approval request ready (Slack not configured)",
            extra={
                "batch_id": state.batch_id,
                "month": state.month,
                "total_amount": summary.get("total_amount", 0),
                "recipient_count": summary.get("recipient_count", 0),
                "anomaly_count": summary.get("anomaly_count", 0)
            }
        )
    
    # ========================================
    # UPDATE STATE
    # ========================================
    new_state = state.model_copy(
        update={
            "metadata": {
                **state.metadata,
                "slack_ts": slack_ts,
                "approval_requested": True
            }
        }
    )
    
    return new_state


def create_batch_in_database(state: AgentState, summary: Dict[str, Any]) -> None:
    """Create PayrollBatch and PayrollLine records in database"""
    from app.db.connection import SessionLocal
    from app.db.models import PayrollBatch, PayrollLine, BatchStatus
    import uuid
    from decimal import Decimal
    
    db = SessionLocal()
    try:
        batch = db.query(PayrollBatch).filter_by(id=state.batch_id).first()
        
        if batch:
            logger.debug("Batch already exists in database", extra={"batch_id": state.batch_id})
        else:
            # ✅ 方法 1: 優先使用 summary 中已計算好的資料
            total_amount = float(summary.get("total_amount", 0))
            anomaly_count = int(summary.get("anomaly_count", 0))
            
            # 如果 summary 沒有資料,才從 lines 計算
            if total_amount == 0 and len(state.lines) > 0:
                for line in state.lines:
                    try:
                        # ✅ PayrollLineDTO 的正確屬性名
                        if hasattr(line, 'amount_usdc'):
                            total_amount += float(line.amount_usdc)
                        elif isinstance(line, dict):
                            total_amount += float(line.get("amount_usdc", 0) or line.get("amount", 0))
                        
                        # 檢查 flags (有 flag 就算 anomaly)
                        if hasattr(line, 'flags') and line.flags:
                            anomaly_count += 1
                        elif isinstance(line, dict) and line.get("flags"):
                            anomaly_count += 1
                            
                    except (AttributeError, TypeError, ValueError) as e:
                        logger.warning(f"Failed to process line: {e}")
                        continue
            
            # Create batch
            batch = PayrollBatch(
                id=state.batch_id,
                month=state.month,
                status=BatchStatus.PENDING_APPROVAL,
                total_amount=total_amount,
                line_count=len(state.lines),
                anomaly_count=anomaly_count,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(batch)
            db.flush()  # Flush to get batch ID before adding lines
            logger.info(
                "✅ Created PayrollBatch record in database",
                extra={
                    "batch_id": state.batch_id,
                    "month": state.month,
                    "total_amount": total_amount,
                    "line_count": len(state.lines),
                    "anomaly_count": anomaly_count
                }
            )
        
        # ✅ 保存 PayrollLine 记录（这样 partial approval 才能看到数据）
        lines_saved = 0
        for line in state.lines:
            try:
                # Extract line data
                if hasattr(line, 'employee_id'):
                    employee_id = line.employee_id
                    wallet = line.wallet
                    amount_usdc = Decimal(str(line.amount_usdc))
                    flags = line.flags or []
                elif isinstance(line, dict):
                    employee_id = line.get("employee_id")
                    wallet = line.get("wallet")
                    amount_usdc = Decimal(str(line.get("amount_usdc", 0)))
                    flags = line.get("flags", [])
                else:
                    logger.warning(f"Skipping invalid line format: {type(line)}")
                    continue
                
                # Check if line already exists
                existing_line = db.query(PayrollLine).filter_by(
                    batch_id=state.batch_id,
                    employee_id=employee_id
                ).first()
                
                if not existing_line:
                    payroll_line = PayrollLine(
                        id=str(uuid.uuid4()),
                        batch_id=state.batch_id,
                        employee_id=employee_id,
                        wallet=wallet,
                        amount_usdc=amount_usdc,
                        flags=flags if isinstance(flags, list) else [],
                    )
                    db.add(payroll_line)
                    lines_saved += 1
                    
            except Exception as e:
                logger.warning(f"Failed to save line for employee {employee_id}: {e}")
                continue
        
        db.commit()
        
        if lines_saved > 0:
            logger.info(
                "✅ Saved PayrollLine records to database",
                extra={
                    "batch_id": state.batch_id,
                    "lines_saved": lines_saved,
                    "total_lines": len(state.lines)
                }
            )
        
    except Exception as e:
        db.rollback()
        logger.error("❌ Failed to create batch record", extra={"batch_id": state.batch_id, "error": str(e)}, exc_info=True)
        raise
    finally:
        db.close()


def format_approval_card(summary: Dict[str, Any]) -> list:
    """
    Format summary as Slack Block Kit blocks
    
    Slack Block Kit is a UI framework for creating rich messages.
    See: https://api.slack.com/block-kit
    
    Args:
        summary: Batch summary dictionary
        
    Returns:
        List of Slack block dictionaries
        
    Example return:
        [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "November 2025 Payroll"}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": "*Total:*\n$26,700.00 USDC"},
                    {"type": "mrkdwn", "text": "*Recipients:*\n5"}
                ]
            },
            ...
        ]
    """
    blocks = [
        # ========================================
        # HEADER
        # ========================================
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"💰 {summary.get('month', 'Unknown')} Payroll Approval"
            }
        },
        
        # ========================================
        # MAIN STATISTICS
        # ========================================
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Total Amount:*\n${summary.get('total_amount', '0.00')} USDC"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Recipients:*\n{summary.get('recipient_count', 0)}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Average:*\n${summary.get('average_amount', '0.00')}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Anomalies:*\n{summary.get('anomaly_count', 0)} ⚠️"
                },
            ]
        },
        
        # ========================================
        # AMOUNT RANGE
        # ========================================
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Min Amount:*\n${summary.get('min_amount', '0.00')}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Max Amount:*\n${summary.get('max_amount', '0.00')}"
                },
            ]
        },
        
        # ========================================
        # DIVIDER
        # ========================================
        {"type": "divider"},
    ]
    
    # ========================================
    # DEPARTMENT BREAKDOWN (if available)
    # ========================================
    department_breakdown = summary.get("department_breakdown", {})
    if department_breakdown:
        dept_text = "*Department Breakdown:*\n"
        for dept, info in list(department_breakdown.items())[:5]:  # Show first 5 departments
            dept_text += f"• {dept}: {info['count']} employees, ${info['total']} total\n"
        
        if len(department_breakdown) > 5:
            remaining = len(department_breakdown) - 5
            dept_text += f"_...and {remaining} more departments_\n"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": dept_text
            }
        })
        
        blocks.append({"type": "divider"})
    
    # ========================================
    # TOP AMOUNTS (if available)
    # ========================================
    top_amounts = summary.get("top_amounts", [])
    if top_amounts:
        top_text = "*Top Payments:*\n"
        for i, item in enumerate(top_amounts[:5], 1):  # Show top 5
            flags_indicator = " ⚠️" if item.get("flags") else ""
            top_text += f"{i}. {item['employee_id']}: ${item['amount']}{flags_indicator}\n"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": top_text
            }
        })
        
        blocks.append({"type": "divider"})
    
    # ========================================
    # ANOMALIES (if any)
    # ========================================
    if summary.get("flagged_items"):
        anomaly_text = "*Flagged Items:*\n"
        for item in summary["flagged_items"][:5]:  # Show first 5
            flags_str = ", ".join(item["flags"])
            anomaly_text += f"• {item['employee_id']}: ${item['amount']} ({flags_str})\n"
        
        if len(summary["flagged_items"]) > 5:
            remaining = len(summary["flagged_items"]) - 5
            anomaly_text += f"_...and {remaining} more_\n"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": anomaly_text
            }
        })
        
        blocks.append({"type": "divider"})
    
    # ========================================
    # AI NARRATIVE (if available)
    # ========================================
    if summary.get("ai_narrative"):
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*AI Summary:*\n_{summary['ai_narrative']}_"
            }
        })
        
        blocks.append({"type": "divider"})
    
    # ========================================
    # ACTION BUTTONS
    # ========================================
    blocks.append({
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "✅ Approve All"
                },
                "style": "primary",
                "action_id": "approve_all",
                "value": summary["batch_id"]
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "⚡ Approve Partial"
                },
                "action_id": "approve_partial",
                "value": summary["batch_id"]
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "❌ Reject"
                },
                "style": "danger",
                "action_id": "reject",
                "value": summary["batch_id"]
            }
        ]
    })
    
    return blocks