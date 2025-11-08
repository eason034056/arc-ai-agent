"""
Slack Application - Production Version
Handles interactive approvals and slash commands for payroll workflow.
Fixed: 
1. Slack 3-second timeout issue with proper async background tasks
2. Robust month extraction from batch_id
"""

import uuid
import asyncio
import re
from datetime import datetime
from typing import Optional, Dict, Any, List
from decimal import Decimal
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.connection import SessionLocal
from app.db.models import Approval, ApprovalDecision, PayrollBatch, BatchStatus

logger = get_logger(__name__)
settings = get_settings()

# =========================================================
# Initialization
# =========================================================
slack_app: Optional[AsyncApp] = None
slack_handler: Optional[AsyncSlackRequestHandler] = None

try:
    if settings.slack_bot_token and settings.slack_signing_secret:
        slack_app = AsyncApp(
            token=settings.slack_bot_token,
            signing_secret=settings.slack_signing_secret
        )
        slack_handler = AsyncSlackRequestHandler(slack_app)
        logger.info("✅ Slack integration initialized successfully (Async)")
    else:
        logger.warning("⚠️ Slack credentials not configured. Slack integration disabled.")
except Exception as e:
    logger.exception(f"❌ Failed to initialize Slack app: {e}")
    slack_app = None
    slack_handler = None


# =========================================================
# Utility: Run blocking DB operations in background
# =========================================================
async def run_in_thread(func, *args, **kwargs):
    """Safely run blocking DB code without blocking event loop"""
    return await asyncio.to_thread(func, *args, **kwargs)


# =========================================================
# Utility: Extract month from batch_id
# =========================================================
def extract_month_from_batch_id(batch_id: str) -> str:
    """
    Extract month from batch_id with multiple fallback strategies
    
    Supported formats:
    - batch_202511_abc123 -> 2025-11
    - batch_20251115_abc123 -> 2025-11
    - batch_2025-11_abc123 -> 2025-11
    - batch_abc123 -> current month (fallback)
    
    Args:
        batch_id: Batch identifier
        
    Returns:
        Month in YYYY-MM format
    """
    # Strategy 1: Look for YYYY-MM pattern
    match = re.search(r'(\d{4})-(\d{2})', batch_id)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    
    # Strategy 2: Look for YYYYMM pattern (6 digits)
    match = re.search(r'(\d{6})', batch_id)
    if match:
        ym = match.group(1)
        year = ym[:4]
        month = ym[4:]
        # Validate month (01-12)
        if 1 <= int(month) <= 12:
            return f"{year}-{month}"
    
    # Strategy 3: Look for YYYYMMDD pattern (8 digits) and extract YYYY-MM
    match = re.search(r'(\d{8})', batch_id)
    if match:
        ymd = match.group(1)
        year = ymd[:4]
        month = ymd[4:6]
        if 1 <= int(month) <= 12:
            return f"{year}-{month}"
    
    # Fallback: Use current month
    current_month = datetime.utcnow().strftime("%Y-%m")
    logger.warning(
        f"⚠️ Could not extract month from batch_id '{batch_id}', using current month {current_month}"
    )
    return current_month


# =========================================================
# Background Handlers (Synchronous DB operations)
# =========================================================
def _process_approval_sync(batch_id: str, approver: str, body: Dict[str, Any]):
    """Run in thread (synchronous DB) - Process approval"""
    db = SessionLocal()
    try:
        batch = db.query(PayrollBatch).filter_by(id=batch_id).first()
        
        if not batch:
            # Extract month from batch_id
            month = extract_month_from_batch_id(batch_id)
            
            logger.info(f"Creating placeholder batch: {batch_id}, month: {month}")
            batch = PayrollBatch(
                id=batch_id,
                month=month,
                status=BatchStatus.PENDING_APPROVAL,
                total_amount=0,
                line_count=0,
                anomaly_count=0,
            )
            db.add(batch)
            db.flush()

        # Create approval record
        approval = Approval(
            id=str(uuid.uuid4()),
            batch_id=batch_id,
            decision=ApprovalDecision.APPROVE_ALL,
            approver=approver,
            slack_ts=body.get("message", {}).get("ts"),
        )
        db.add(approval)
        
        # Update batch status
        batch.status = BatchStatus.APPROVED
        batch.updated_at = datetime.utcnow()
        
        db.commit()
        logger.info(f"✅ Batch approved (all): {batch_id} by {approver}")
        
    except Exception as e:
        db.rollback()
        logger.exception(f"❌ Error in _process_approval_sync: {e}")
        raise  # Re-raise to be caught by caller
    finally:
        db.close()


def _process_rejection_sync(batch_id: str, approver: str, body: Dict[str, Any]):
    """Run in thread (synchronous DB) - Process rejection"""
    db = SessionLocal()
    try:
        batch = db.query(PayrollBatch).filter_by(id=batch_id).first()
        
        if not batch:
            # Extract month from batch_id
            month = extract_month_from_batch_id(batch_id)
            
            logger.info(f"Creating placeholder batch: {batch_id}, month: {month}")
            batch = PayrollBatch(
                id=batch_id,
                month=month,
                status=BatchStatus.PENDING_APPROVAL,
                total_amount=0,
                line_count=0,
                anomaly_count=0,
            )
            db.add(batch)
            db.flush()

        # Create rejection record
        approval = Approval(
            id=str(uuid.uuid4()),
            batch_id=batch_id,
            decision=ApprovalDecision.REJECT,
            approver=approver,
            slack_ts=body.get("message", {}).get("ts"),
        )
        db.add(approval)
        
        # Update batch status
        batch.status = BatchStatus.REJECTED
        batch.updated_at = datetime.utcnow()
        
        db.commit()
        logger.info(f"❌ Batch rejected: {batch_id} by {approver}")
        
    except Exception as e:
        db.rollback()
        logger.exception(f"❌ Error in _process_rejection_sync: {e}")
        raise  # Re-raise to be caught by caller
    finally:
        db.close()


# =========================================================
# Slack Action Handlers
# =========================================================
if slack_app:
    logger.info("📝 Registering Slack action handlers")

    @slack_app.action("approve_all")
    async def handle_approve_all(ack, body: Dict[str, Any], client):
        """Handle 'Approve All' button click"""
        # 1️⃣ Immediately acknowledge to Slack (< 3 seconds required)
        await ack()
        
        # 2️⃣ Extract data from payload
        batch_id = body.get("actions", [{}])[0].get("value")
        approver = body.get("user", {}).get("id")
        channel_id = body["channel"]["id"]
        ts = body["message"]["ts"]
        
        logger.info(f"✅ Approve All clicked - batch {batch_id} by {approver}")

        # 3️⃣ Immediately update UI to show processing (fast feedback)
        try:
            await client.chat_update(
                channel=channel_id,
                ts=ts,
                text=f"⏳ Processing approval...",
                blocks=[{
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"⏳ *Processing approval* by <@{approver}>...\n_Batch: {batch_id}_"
                    },
                }],
            )
        except Exception as e:
            logger.exception(f"Slack update failed (processing): {e}")

        # 4️⃣ Launch background task for DB operations
        async def background_approval():
            """Background task that processes DB and updates Slack"""
            try:
                # Run blocking DB operation in thread pool
                await run_in_thread(_process_approval_sync, batch_id, approver, body)
                
                # DB operation succeeded - update Slack with success
                await client.chat_update(
                    channel=channel_id,
                    ts=ts,
                    text=f"✅ Approved by <@{approver}>",
                    blocks=[{
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"✅ *Approved All* by <@{approver}>\n_Batch: {batch_id}_"
                        },
                    }],
                )
                logger.info(f"✅ Background approval completed for {batch_id}")
                
            except Exception as e:
                logger.exception(f"❌ Background approval failed: {e}")
                # Update Slack with error message
                try:
                    await client.chat_update(
                        channel=channel_id,
                        ts=ts,
                        text=f"❌ Error processing approval",
                        blocks=[{
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"❌ *Error processing approval*\n_Batch: {batch_id}_\n```{str(e)[:200]}```"
                            },
                        }],
                    )
                except Exception as update_error:
                    logger.exception(f"Failed to update Slack with error: {update_error}")
        
        # Launch background task (fire and forget - does not block)
        asyncio.create_task(background_approval())


    @slack_app.action("reject")
    async def handle_reject(ack, body: Dict[str, Any], client):
        """Handle 'Reject' button click"""
        # 1️⃣ Immediately acknowledge
        await ack()
        
        # 2️⃣ Extract data
        batch_id = body.get("actions", [{}])[0].get("value")
        approver = body.get("user", {}).get("id")
        channel_id = body["channel"]["id"]
        ts = body["message"]["ts"]
        
        logger.info(f"❌ Reject clicked - batch {batch_id} by {approver}")

        # 3️⃣ Update UI immediately
        try:
            await client.chat_update(
                channel=channel_id,
                ts=ts,
                text=f"⏳ Processing rejection...",
                blocks=[{
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"⏳ *Processing rejection* by <@{approver}>...\n_Batch: {batch_id}_"
                    },
                }],
            )
        except Exception as e:
            logger.exception(f"Slack update failed (processing): {e}")

        # 4️⃣ Background task
        async def background_rejection():
            try:
                await run_in_thread(_process_rejection_sync, batch_id, approver, body)
                
                await client.chat_update(
                    channel=channel_id,
                    ts=ts,
                    text=f"❌ Rejected by <@{approver}>",
                    blocks=[{
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"❌ *Rejected* by <@{approver}>\n_Batch: {batch_id}_"
                        },
                    }],
                )
                logger.info(f"✅ Background rejection completed for {batch_id}")
                
            except Exception as e:
                logger.exception(f"❌ Background rejection failed: {e}")
                try:
                    await client.chat_update(
                        channel=channel_id,
                        ts=ts,
                        text=f"❌ Error processing rejection",
                        blocks=[{
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"❌ *Error processing rejection*\n_Batch: {batch_id}_\n```{str(e)[:200]}```"
                            },
                        }],
                    )
                except Exception as update_error:
                    logger.exception(f"Failed to update Slack with error: {update_error}")
        
        asyncio.create_task(background_rejection())


    @slack_app.action("approve_partial")
    async def handle_approve_partial(ack, body: Dict[str, Any], client):
        """Handle 'Approve Partial' button click"""
        await ack()
        
        batch_id = body.get("actions", [{}])[0].get("value")
        user = body.get("user", {}).get("id")
        channel_id = body["channel"]["id"]
        ts = body["message"]["ts"]
        
        logger.info(f"⚡ Partial approval clicked - batch {batch_id} by {user}")

        # Update immediately
        try:
            await client.chat_update(
                channel=channel_id,
                ts=ts,
                text=f"⚡ Partial approval by <@{user}>",
                blocks=[{
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"⚡ *Partial Approval* by <@{user}>\n_Batch: {batch_id}_\n\n_Note: Modal selection UI coming soon..._"
                    },
                }],
            )
        except Exception as e:
            logger.exception(f"Slack update failed: {e}")

        # TODO: Open modal for line-by-line approval
        # See: https://api.slack.com/surfaces/modals


    # =====================================================
    # Slash Command Handler
    # =====================================================
    @slack_app.command("/payroll")
    async def handle_payroll_command(ack, command, client):
        """
        Handle /payroll slash commands
        
        Supported commands:
        - /payroll status <batch_id>
        - /payroll trigger <month>
        """
        await ack()
        
        text = command.get("text", "").strip().split()
        user = command.get("user_id")
        channel = command.get("channel_id")
        
        logger.info(f"💬 /payroll command by {user}: {text}")

        # No arguments - show help
        if not text:
            await client.chat_postMessage(
                channel=channel,
                text="*Payroll Command Help*\n\nUsage:\n• `/payroll status <batch_id>` - Check batch status\n• `/payroll trigger <month>` - Manually trigger payroll for a month (YYYY-MM)"
            )
            return

        action = text[0].lower()
        
        # Status command
        if action == "status" and len(text) > 1:
            batch_id = text[1]
            await client.chat_postMessage(
                channel=channel,
                text=f"📊 Fetching status for batch `{batch_id}`..."
            )
            # TODO: Query database for actual status
            # from app.db.models import PayrollBatch
            # db = SessionLocal()
            # batch = db.query(PayrollBatch).filter_by(id=batch_id).first()
            # ...
        
        # Trigger command
        elif action == "trigger" and len(text) > 1:
            month = text[1]
            await client.chat_postMessage(
                channel=channel,
                text=f"🚀 Triggering payroll workflow for `{month}`...\n_This may take a few minutes._"
            )
            # TODO: Trigger workflow via API call
            # import httpx
            # response = await httpx.post(f"http://localhost:8080/admin/trigger?month={month}")
        
        # Invalid command
        else:
            await client.chat_postMessage(
                channel=channel,
                text=f"❌ Invalid command: `{' '.join(text)}`\n\nUse `/payroll` (no arguments) for help."
            )


    # =====================================================
    # Global Error Handler
    # =====================================================
    @slack_app.error
    async def global_error_handler(error, body, logger):
        """Catch-all error handler for Slack events"""
        logger.exception(f"⚠️ Slack handler error: {error}")
        logger.debug(f"Error body: {body}")


# =========================================================
# Helper: Send Approval Request to Slack
# =========================================================
async def send_approval_request(
    client, 
    batch_id: str, 
    blocks: List[Dict[str, Any]]
) -> Optional[str]:
    """
    Send approval request message to Slack channel
    
    Args:
        client: Slack WebClient instance
        batch_id: Batch identifier
        blocks: Block Kit message blocks
        
    Returns:
        Message timestamp (ts) if successful, None otherwise
    """
    channel = settings.slack_approval_channel
    if not channel:
        logger.warning("⚠️ No Slack approval channel configured")
        return None
    
    try:
        response = await client.chat_postMessage(
            channel=channel,
            text=f"Payroll approval request for batch {batch_id}",
            blocks=blocks,
        )
        ts = response.get("ts")
        logger.info(f"📤 Sent approval request to Slack channel {channel} (batch {batch_id}, ts={ts})")
        return ts
    except Exception as e:
        logger.exception(f"❌ Failed to send Slack message: {e}")
        return None