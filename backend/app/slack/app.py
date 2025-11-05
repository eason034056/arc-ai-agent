"""
Slack Application

This module sets up the Slack Bolt app and defines event handlers.

Key Features:
- Interactive button handling (Approve/Reject)
- Slash commands for manual triggers
- Message posting to channels
- Error handling and logging

Setup Required:
1. Create Slack app at https://api.slack.com/apps
2. Enable Interactive Components
3. Add Bot Token Scopes: chat:write, commands, im:write
4. Install app to workspace
5. Copy Bot Token and Signing Secret to .env
"""

import uuid
from datetime import datetime
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.connection import SessionLocal
from app.db.models import Approval, ApprovalDecision, PayrollBatch

logger = get_logger(__name__)
settings = get_settings()

# ========================================
# CREATE SLACK APP
# ========================================
# Initialize Slack Bolt app with credentials
slack_app = App(
    token=settings.slack_bot_token,
    signing_secret=settings.slack_signing_secret
)

# Create FastAPI adapter for handling Slack requests
# This allows us to integrate Slack with FastAPI
slack_handler = SlackRequestHandler(slack_app)


# ========================================
# BUTTON CLICK HANDLERS
# ========================================

@slack_app.action("approve_all")
def handle_approve_all(ack, body, client):
    """
    Handle "Approve All" button click
    
    When a user clicks the "Approve All" button in Slack,
    this function is called automatically by Slack Bolt.
    
    Args:
        ack: Acknowledgment function (must be called within 3 seconds)
        body: Full request body from Slack
        client: Slack Web API client
    
    Flow:
        1. Acknowledge the button click immediately
        2. Extract batch_id from button value
        3. Update database with approval decision
        4. Update Slack message to show approval
        
    Example button value: "batch_123"
    """
    # CRITICAL: Acknowledge within 3 seconds or Slack will timeout
    ack()
    
    logger.info("Approve All button clicked", extra={
        "user": body["user"]["id"],
        "channel": body["channel"]["id"]
    })
    
    # Extract batch_id from button value
    batch_id = body["actions"][0]["value"]
    
    # Extract user who clicked
    approver = body["user"]["id"]
    approver_name = body["user"].get("name", "Unknown")
    
    # Update database with approval
    db = SessionLocal()
    try:
        # Save approval decision
        approval = Approval(
            id=str(uuid.uuid4()),
            batch_id=batch_id,
            decision=ApprovalDecision.APPROVE_ALL,
            approver=approver,
            slack_ts=body["message"]["ts"]
        )
        db.add(approval)
        
        # Update batch status
        batch = db.query(PayrollBatch).filter_by(id=batch_id).first()
        if batch:
            batch.status = 'approved'
            batch.approved_at = datetime.utcnow()
            batch.approver_id = approver
        
        db.commit()
        
        logger.info(
            "Batch approved (all)",
            extra={
                "batch_id": batch_id,
                "approver": approver,
                "approver_name": approver_name
            }
        )
    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to save approval",
            extra={
                "batch_id": batch_id,
                "error": str(e)
            },
            exc_info=True
        )
    finally:
        db.close()
    
    # Update the Slack message to show approval
    try:
        client.chat_update(
            channel=body["channel"]["id"],
            ts=body["message"]["ts"],
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
    except Exception as e:
        logger.error(
            "Failed to update Slack message",
            extra={
                "batch_id": batch_id,
                "error": str(e)
            },
            exc_info=True
        )


@slack_app.action("approve_partial")
def handle_approve_partial(ack, body, client):
    """
    Handle "Approve Partial" button click
    
    This opens a modal where the user can select specific employees to approve.
    """
    ack()
    
    logger.info("Approve Partial button clicked", extra={
        "user": body["user"]["id"]
    })
    
    batch_id = body["actions"][0]["value"]
    
    # TODO: Open modal with employee selection
    # For now, treat as approve all
    # In production, you'd show a modal with checkboxes
    
    logger.info(
        "Partial approval requested (modal not implemented)",
        extra={"batch_id": batch_id}
    )
    
    # Placeholder: Update message
    try:
        client.chat_update(
            channel=body["channel"]["id"],
            ts=body["message"]["ts"],
            text=f"⚡ Partial approval by <@{body['user']['id']}>",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"⚡ *Partial Approval* by <@{body['user']['id']}>\n_Batch: {batch_id}_"
                    }
                }
            ]
        )
    except Exception as e:
        logger.error(
            "Failed to update Slack message",
            extra={"error": str(e)},
            exc_info=True
        )


@slack_app.action("reject")
def handle_reject(ack, body, client):
    """
    Handle "Reject" button click
    """
    ack()
    
    logger.info("Reject button clicked", extra={
        "user": body["user"]["id"]
    })
    
    batch_id = body["actions"][0]["value"]
    approver = body["user"]["id"]
    
    # Update database with rejection
    db = SessionLocal()
    try:
        # Save rejection decision
        approval = Approval(
            id=str(uuid.uuid4()),
            batch_id=batch_id,
            decision=ApprovalDecision.REJECT,
            approver=approver,
            slack_ts=body["message"]["ts"]
        )
        db.add(approval)
        
        # Update batch status
        batch = db.query(PayrollBatch).filter_by(id=batch_id).first()
        if batch:
            batch.status = 'rejected'
        
        db.commit()
        
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
            "Failed to save rejection",
            extra={
                "batch_id": batch_id,
                "error": str(e)
            },
            exc_info=True
        )
    finally:
        db.close()
    
    # Update message
    try:
        client.chat_update(
            channel=body["channel"]["id"],
            ts=body["message"]["ts"],
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
    except Exception as e:
        logger.error(
            "Failed to update Slack message",
            extra={"error": str(e)},
            exc_info=True
        )


# ========================================
# SLASH COMMANDS
# ========================================

@slack_app.command("/payroll")
def handle_payroll_command(ack, command, client):
    """
    Handle /payroll slash command
    
    Usage:
        /payroll status batch_123
        /payroll trigger 2025-11
    
    Args:
        ack: Acknowledgment function
        command: Command data from Slack
        client: Slack Web API client
    """
    ack()
    
    logger.info("Payroll command received", extra={
        "user": command["user_id"],
        "text": command["text"]
    })
    
    # Parse command text
    parts = command["text"].strip().split()
    
    if not parts:
        client.chat_postMessage(
            channel=command["channel_id"],
            text="Usage: `/payroll status <batch_id>` or `/payroll trigger <month>`"
        )
        return
    
    action = parts[0].lower()
    
    if action == "status" and len(parts) > 1:
        batch_id = parts[1]
        # TODO: Fetch batch status from database
        client.chat_postMessage(
            channel=command["channel_id"],
            text=f"Batch {batch_id} status: Processing (mock response)"
        )
    
    elif action == "trigger" and len(parts) > 1:
        month = parts[1]
        # TODO: Trigger payroll workflow
        client.chat_postMessage(
            channel=command["channel_id"],
            text=f"Triggering payroll for {month}... (mock response)"
        )
    
    else:
        client.chat_postMessage(
            channel=command["channel_id"],
            text="Invalid command. Usage: `/payroll status <batch_id>` or `/payroll trigger <month>`"
        )


# ========================================
# HELPER FUNCTIONS
# ========================================

def send_approval_request(client, batch_id: str, blocks: list) -> str:
    """
    Send approval request message to Slack channel
    
    Args:
        client: Slack Web API client
        batch_id: Batch identifier
        blocks: Slack Block Kit blocks
        
    Returns:
        Message timestamp (ts) for future updates
        
    Example:
        from app.slack.app import slack_app, send_approval_request
        
        blocks = [...approval card blocks...]
        ts = send_approval_request(
            slack_app.client,
            "batch_123",
            blocks
        )
        
        print(f"Message sent: {ts}")
    """
    channel = settings.slack_approval_channel
    
    if not channel:
        logger.warning("No approval channel configured, cannot send message")
        return None
    
    try:
        response = client.chat_postMessage(
            channel=channel,
            text=f"Payroll approval request for batch {batch_id}",
            blocks=blocks
        )
        
        # Extract timestamp from response
        # This is used to update the message later
        ts = response["ts"]
        
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
                "error": str(e)
            },
            exc_info=True
        )
        raise


# ========================================
# ERROR HANDLING
# ========================================

@slack_app.error
def custom_error_handler(error, body, logger):
    """
    Global error handler for Slack app
    
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

