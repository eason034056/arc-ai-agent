"""
Propose Node

This node prepares the approval request and sends it to Slack.
It creates an approval card with batch summary and action buttons.

Responsibilities:
- Format summary for Slack Block Kit
- Create approval card
- Send message to Slack channel
- Store message timestamp for later updates
"""

from typing import Dict, Any

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
            
            slack_ts = send_approval_request(
                slack_client,
                state.batch_id,
                slack_blocks
            )
            
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
            "No Slack client provided, skipping message send",
            extra={"batch_id": state.batch_id}
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
                "text": f"💰 {summary['month']} Payroll Approval"
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
                    "text": f"*Total Amount:*\n${summary['total_amount']} USDC"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Recipients:*\n{summary['recipient_count']}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Average:*\n${summary['average_amount']}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Anomalies:*\n{summary['anomaly_count']} ⚠️"
                },
            ]
        },
        
        # ========================================
        # DIVIDER
        # ========================================
        {"type": "divider"},
    ]
    
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

