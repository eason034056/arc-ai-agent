"""
Slack Application

Handles interactive approvals and slash commands for payroll workflow.

Features:
- Interactive button handling (Approve/Reject/Partial)
- Slash commands (/payroll)
- Async background tasks to avoid Slack 3s timeout
- Clean DB integration and structured logging

Setup Required:
1. Create Slack app at https://api.slack.com/apps
2. Enable Interactive Components
3. Add Bot Token Scopes: chat:write, commands, im:write
4. Install app to workspace
5. Copy Bot Token and Signing Secret to .env
"""

import uuid
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.connection import SessionLocal
from app.db.models import Approval, ApprovalDecision, PayrollBatch, BatchStatus

logger = get_logger(__name__)
settings = get_settings()

# ========================================
# INITIALIZATION
# ========================================

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler

slack_app: Optional[AsyncApp] = None
slack_handler: Optional[AsyncSlackRequestHandler] = None

try:
    if settings.slack_bot_token and settings.slack_signing_secret:
        slack_app = AsyncApp(
            token=settings.slack_bot_token,
            signing_secret=settings.slack_signing_secret
        )
        slack_handler = AsyncSlackRequestHandler(slack_app)
        logger.info("Slack integration initialized successfully (Async)")
    else:
        logger.warning("Slack credentials not configured. Slack integration disabled.")
except Exception as e:
    logger.error("Failed to initialize Slack app", extra={"error": str(e)}, exc_info=True)
    slack_app = None
    slack_handler = None


# ========================================
# BACKGROUND TASKS
# ========================================

async def process_approval(
    batch_id: str,
    approver: str,
    body: Dict[str, Any],
    client
) -> None:
    """
    Background task for full approval.
    
    This function runs asynchronously after ack() is called,
    allowing us to perform time-consuming operations without
    blocking the Slack 3-second timeout.
    
    Args:
        batch_id: Batch identifier
        approver: User ID who approved
        body: Full request body from Slack
        client: Slack Web API client
    """
    db = SessionLocal()
    try:
        # Check if batch exists, create if not
        batch = db.query(PayrollBatch).filter_by(id=batch_id).first()
        if not batch:
            # Create placeholder batch if it doesn't exist
            # Extract month from batch_id if possible (format: batch_YYYYMM or similar)
            # Otherwise use current month
            month = datetime.utcnow().strftime("%Y-%m")
            if "_" in batch_id:
                # Try to extract month from batch_id
                parts = batch_id.split("_")
                if len(parts) > 1:
                    # Assume format like batch_2025-11 or batch_202511
                    month_part = parts[-1]
                    if len(month_part) == 6:  # YYYYMM
                        month = f"{month_part[:4]}-{month_part[4:]}"
            
            batch = PayrollBatch(
                id=batch_id,
                month=month,
                status=BatchStatus.PENDING_APPROVAL,
                total_amount=0,
                line_count=0,
                anomaly_count=0
            )
            db.add(batch)
            db.flush()  # Flush to get the batch ID for foreign key
        
        # Create approval record
        approval = Approval(
            id=str(uuid.uuid4()),
            batch_id=batch_id,
            decision=ApprovalDecision.APPROVE_ALL,
            approver=approver,
            slack_ts=body.get("message", {}).get("ts")
        )
        db.add(approval)
        
        # Update batch status
        batch.status = BatchStatus.APPROVED
        batch.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Update Slack message
        try:
            await client.chat_update(
                channel=body.get("channel", {}).get("id"),
                ts=body.get("message", {}).get("ts"),
                text=f"✅ Approved by <@{approver}>",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"✅ *Approved All* by <@{approver}>\n_Batch: {batch_id}_"
                        }
                    }
                ]
            )
        except Exception as slack_error:
            logger.error(
                "Failed to update Slack message",
                extra={
                    "batch_id": batch_id,
                    "error": str(slack_error)
                },
                exc_info=True
            )
        
        logger.info(
            "Batch approved (all)",
            extra={
                "batch_id": batch_id,
                "approver": approver
            }
        )
        
    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to process approval",
            extra={
                "batch_id": batch_id,
                "approver": approver,
                "error": str(e)
            },
            exc_info=True
        )
    finally:
        db.close()


async def process_rejection(
    batch_id: str,
    approver: str,
    body: Dict[str, Any],
    client
) -> None:
    """
    Background task for rejection.
    
    Args:
        batch_id: Batch identifier
        approver: User ID who rejected
        body: Full request body from Slack
        client: Slack Web API client
    """
    db = SessionLocal()
    try:
        # Check if batch exists, create if not
        batch = db.query(PayrollBatch).filter_by(id=batch_id).first()
        if not batch:
            # Create placeholder batch if it doesn't exist
            month = datetime.utcnow().strftime("%Y-%m")
            if "_" in batch_id:
                parts = batch_id.split("_")
                if len(parts) > 1:
                    month_part = parts[-1]
                    if len(month_part) == 6:  # YYYYMM
                        month = f"{month_part[:4]}-{month_part[4:]}"
            
            batch = PayrollBatch(
                id=batch_id,
                month=month,
                status=BatchStatus.PENDING_APPROVAL,
                total_amount=0,
                line_count=0,
                anomaly_count=0
            )
            db.add(batch)
            db.flush()  # Flush to get the batch ID for foreign key
        
        # Create rejection record
        approval = Approval(
            id=str(uuid.uuid4()),
            batch_id=batch_id,
            decision=ApprovalDecision.REJECT,
            approver=approver,
            slack_ts=body.get("message", {}).get("ts")
        )
        db.add(approval)
        
        # Update batch status
        batch.status = BatchStatus.REJECTED
        batch.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Update Slack message
        try:
            await client.chat_update(
                channel=body.get("channel", {}).get("id"),
                ts=body.get("message", {}).get("ts"),
                text=f"❌ Rejected by <@{approver}>",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"❌ *Rejected* by <@{approver}>\n_Batch: {batch_id}_"
                        }
                    }
                ]
            )
        except Exception as slack_error:
            logger.error(
                "Failed to update Slack message",
                extra={
                    "batch_id": batch_id,
                    "error": str(slack_error)
                },
                exc_info=True
            )
        
        logger.info(
            "Batch rejected",
            extra={
                "batch_id": batch_id,
                "approver": approver
            }
        )
        
    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to process rejection",
            extra={
                "batch_id": batch_id,
                "approver": approver,
                "error": str(e)
            },
            exc_info=True
        )
    finally:
        db.close()


# ========================================
# ACTION HANDLERS
# ========================================

if slack_app:
    logger.info("📝 Registering Slack action handlers")
    
    @slack_app.action("approve_all")
    async def handle_approve_all(ack, body: Dict[str, Any], client):
        """
        Handle "Approve All" button click.
        
        CRITICAL: Must call ack() within 3 seconds.
        """
        try:
            await ack()
            logger.debug("✅ Acknowledged button click immediately")
        except Exception as e:
            logger.error(
                "Failed to acknowledge button click",
                extra={"error": str(e)},
                exc_info=True
            )
            # Try to acknowledge anyway
            try:
                await ack()
            except:
                pass
        
        try:
            batch_id = body.get("actions", [{}])[0].get("value")
            approver = body.get("user", {}).get("id")
            
            if not batch_id or not approver:
                logger.error(
                    "Missing required fields in button click",
                    extra={"body": body}
                )
                return
            
            logger.info(
                "✅ Approve All button clicked",
                extra={
                    "batch_id": batch_id,
                    "approver": approver,
                    "user_name": body.get("user", {}).get("name", "unknown"),
                    "body_keys": list(body.keys()) if body else []
                }
            )
            
            # Process in background to avoid timeout
            asyncio.create_task(process_approval(batch_id, approver, body, client))
            
        except Exception as e:
            logger.error(
                "Error handling approve_all action",
                extra={"error": str(e)},
                exc_info=True
            )

    @slack_app.action("reject")
    async def handle_reject(ack, body: Dict[str, Any], client):
        """
        Handle "Reject" button click.
        
        CRITICAL: Must call ack() within 3 seconds.
        """
        try:
            await ack()
            logger.debug("✅ Acknowledged button click immediately")
        except Exception as e:
            logger.error(
                "Failed to acknowledge button click",
                extra={"error": str(e)},
                exc_info=True
            )
            try:
                await ack()
            except:
                pass
        
        try:
            batch_id = body.get("actions", [{}])[0].get("value")
            approver = body.get("user", {}).get("id")
            
            if not batch_id or not approver:
                logger.error(
                    "Missing required fields in button click",
                    extra={"body": body}
                )
                return
            
            logger.info(
                "❌ Reject button clicked",
                extra={
                    "batch_id": batch_id,
                    "approver": approver,
                    "user_name": body.get("user", {}).get("name", "unknown")
                }
            )
            
            # Process in background to avoid timeout
            asyncio.create_task(process_rejection(batch_id, approver, body, client))
            
        except Exception as e:
            logger.error(
                "Error handling reject action",
                extra={"error": str(e)},
                exc_info=True
            )

    @slack_app.action("approve_partial")
    async def handle_approve_partial(ack, body: Dict[str, Any], client):
        """
        Handle "Approve Partial" button click.
        
        TODO: Open modal for employee selection.
        For now, just acknowledge and log.
        """
        try:
            await ack()
            logger.debug("✅ Acknowledged button click immediately")
        except Exception as e:
            logger.error(
                "Failed to acknowledge button click",
                extra={"error": str(e)},
                exc_info=True
            )
            try:
                await ack()
            except:
                pass
        
        try:
            batch_id = body.get("actions", [{}])[0].get("value")
            user = body.get("user", {}).get("id")
            
            logger.info(
                "⚡ Approve Partial button clicked",
                extra={
                    "batch_id": batch_id,
                    "user": user,
                    "user_name": body.get("user", {}).get("name", "unknown")
                }
            )
            
            # TODO: Open modal with employee selection
            # For now, just update message
            try:
                await client.chat_update(
                    channel=body.get("channel", {}).get("id"),
                    ts=body.get("message", {}).get("ts"),
                    text=f"⚡ Partial approval by <@{user}> (modal TBD)",
                    blocks=[
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"⚡ *Partial Approval* by <@{user}>\n_Batch: {batch_id}_\n_Modal selection not yet implemented_"
                            }
                        }
                    ]
                )
            except Exception as slack_error:
                logger.error(
                    "Failed to update Slack message",
                    extra={
                        "batch_id": batch_id,
                        "error": str(slack_error)
                    },
                    exc_info=True
                )
                
        except Exception as e:
            logger.error(
                "Error handling approve_partial action",
                extra={"error": str(e)},
                exc_info=True
            )

    # ========================================
    # SLASH COMMANDS
    # ========================================

    @slack_app.command("/payroll")
    async def handle_payroll_command(ack, command: Dict[str, Any], client):
        """
        Handle /payroll slash command.
        
        Usage:
            /payroll status <batch_id>
            /payroll trigger <month>
        """
        try:
            await ack()
        except Exception as e:
            logger.error(
                "Failed to acknowledge slash command",
                extra={"error": str(e)},
                exc_info=True
            )
            try:
                await ack()
            except:
                pass
        
        try:
            user = command.get("user_id")
            text = command.get("text", "").strip().split()
            
            logger.info(
                "Payroll command received",
                extra={
                    "user": user,
                    "text": text
                }
            )
            
            if not text:
                await client.chat_postMessage(
                    channel=command.get("channel_id"),
                    text="Usage: `/payroll status <batch_id>` or `/payroll trigger <month>`"
                )
                return
            
            action = text[0].lower()
            
            if action == "status" and len(text) > 1:
                batch_id = text[1]
                # TODO: Fetch actual batch status from database
                await client.chat_postMessage(
                    channel=command.get("channel_id"),
                    text=f"Batch {batch_id} status: Processing (mock response)"
                )
                
            elif action == "trigger" and len(text) > 1:
                month = text[1]
                # TODO: Trigger actual payroll workflow
                await client.chat_postMessage(
                    channel=command.get("channel_id"),
                    text=f"Triggering payroll for {month}... (mock response)"
                )
                
            else:
                await client.chat_postMessage(
                    channel=command.get("channel_id"),
                    text="Invalid command. Usage: `/payroll status <batch_id>` or `/payroll trigger <month>`"
                )
                
        except Exception as e:
            logger.error(
                "Error handling payroll command",
                extra={"error": str(e)},
                exc_info=True
            )
            try:
                await client.chat_postMessage(
                    channel=command.get("channel_id"),
                    text="❌ Error processing command. Please try again."
                )
            except:
                pass

    # ========================================
    # GLOBAL ERROR HANDLER
    # ========================================

    @slack_app.error
    async def custom_error_handler(error, body, logger):
        """
        Global error handler for Slack app.
        
        Catches any unhandled exceptions in Slack event handlers.
        """
        logger.error(
            "Slack app error",
            extra={
                "error": str(error),
                "body": body
            },
            exc_info=True
        )


# ========================================
# HELPER FUNCTIONS
# ========================================

async def send_approval_request(client, batch_id: str, blocks: List[Dict[str, Any]]) -> Optional[str]:
    """
    Send approval request message to Slack channel.
    
    Args:
        client: Slack Web API client (AsyncWebClient)
        batch_id: Batch identifier
        blocks: Slack Block Kit blocks
        
    Returns:
        Message timestamp (ts) for future updates, or None if failed
        
    Example:
        from app.slack.app import slack_app, send_approval_request
        
        blocks = [...approval card blocks...]
        ts = await send_approval_request(
            slack_app.client,
            "batch_123",
            blocks
        )
    """
    channel = settings.slack_approval_channel
    
    if not channel:
        logger.warning(
            "No approval channel configured, cannot send message",
            extra={"batch_id": batch_id}
        )
        return None
    
    try:
        response = await client.chat_postMessage(
            channel=channel,
            text=f"Payroll approval request for batch {batch_id}",
            blocks=blocks
        )
        
        ts = response.get("ts")
        
        logger.info(
            "Approval request sent to Slack",
            extra={
                "batch_id": batch_id,
                "channel": channel,
                "ts": ts
            }
        )
        
        return ts
        
    except Exception as e:
        logger.error(
            "Failed to send approval request",
            extra={
                "batch_id": batch_id,
                "channel": channel,
                "error": str(e)
            },
            exc_info=True
        )
        raise
