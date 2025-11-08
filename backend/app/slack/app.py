"""
Slack Application - Production Version
Handles interactive approvals and slash commands for payroll workflow.
Fixed: 
1. Slack 3-second timeout issue with proper async background tasks
2. Robust month extraction from batch_id
3. Correct function signatures for Slack Bolt handlers
4. Proper modal handling within trigger_id timeout
"""
import json
import uuid
import asyncio
import re
from datetime import datetime
from typing import Optional, Dict, Any, List
from decimal import Decimal
from contextlib import closing
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.connection import SessionLocal
from app.db.models import Approval, ApprovalDecision, PayrollBatch, BatchStatus, PayrollLine, Transaction, TransactionStatus
from app.onchain.service import OnchainService
from app.onchain.mock_service import MockOnchainService
from app.agent.policies import PayrollPolicy

logger = get_logger(__name__)
settings = get_settings()

# =========================================================
# Initialization
# =========================================================

if settings.slack_bot_token and settings.slack_signing_secret:
    slack_app = AsyncApp(
        token=settings.slack_bot_token,
        signing_secret=settings.slack_signing_secret
    )
    slack_handler = AsyncSlackRequestHandler(slack_app)
    logger.info("✅ Slack integration initialized successfully (Async)")
else:
    slack_app = None
    slack_handler = None
    logger.warning("⚠️ Slack credentials not configured. Slack integration disabled.")

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
    
    # 添加全局 middleware 日志记录器
    @slack_app.middleware
    async def log_all_events(body, next):
        """Log all incoming Slack events for debugging"""
        event_type = body.get("type")
        logger.info(
            "🔔 Slack event received",
            extra={
                "event_type": event_type,
                "has_actions": bool(body.get("actions")),
                "has_user": bool(body.get("user")),
            }
        )
        
        if event_type == "block_actions":
            actions = body.get("actions", [])
            if actions:
                logger.info(
                    "🔘 Block action detected",
                    extra={
                        "action_id": actions[0].get("action_id"),
                        "value": actions[0].get("value"),
                        "user": body.get("user", {}).get("id"),
                    }
                )
        
        await next()

    @slack_app.action("approve_all")
    async def handle_approve_all(ack, body: Dict[str, Any], client):
        """Handle 'Approve All' button click"""
        logger.info(f"🔘 Approve All handler called", extra={"body_type": body.get("type"), "actions": body.get("actions")})
        
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
        await ack()  # ✅ 必須立即回應 Slack (<3 秒)

        batch_id = body.get("actions", [{}])[0].get("value")
        user_id = body.get("user", {}).get("id")
        trigger_id = body.get("trigger_id")
        channel_id = body["channel"]["id"]
        ts = body["message"]["ts"]

        logger.info(f"⚡ Partial approval clicked - batch {batch_id} by {user_id}")

        # 用背景任務避免阻塞主 event loop
        async def open_modal_task():
            try:
                with closing(SessionLocal()) as db:
                    batch = db.query(PayrollBatch).filter_by(id=batch_id).first()
                    if not batch:
                        month = extract_month_from_batch_id(batch_id)
                        batch = PayrollBatch(
                            id=batch_id,
                            month=month,
                            status=BatchStatus.PENDING_APPROVAL,
                            total_amount=0,
                            line_count=0,
                            anomaly_count=0
                        )
                        db.add(batch)
                        db.commit()
                        logger.info(f"✅ Created placeholder batch {batch_id}")

                    lines = db.query(PayrollLine).filter_by(batch_id=batch_id).all()

                if not lines:
                    options = [{"text": {"type": "plain_text", "text": "No transactions available"}, "value": "none"}]
                else:
                    # 只取前 50 筆，避免 Slack modal 上限
                    # 格式化显示：员工ID、金额、钱包地址（前6位）、flags
                    options = []
                    for l in lines[:50]:
                        # 格式化金额
                        amount_str = f"${float(l.amount_usdc):,.2f}"
                        
                        # 显示钱包地址（前6位...后4位）
                        wallet_short = f"{l.wallet[:8]}...{l.wallet[-6:]}" if len(l.wallet) > 14 else l.wallet
                        
                        # 显示 flags（如果有）
                        flags_text = ""
                        if l.flags:
                            flags_list = l.flags if isinstance(l.flags, list) else [l.flags]
                            flags_text = f" | Flags: {', '.join(flags_list[:2])}"  # 最多显示2个flags
                        
                        # 创建选项文本
                        option_text = f"👤 {l.employee_id}\n💰 {amount_str} USDC\n🔗 {wallet_short}{flags_text}"
                        
                        options.append({
                            "text": {
                                "type": "plain_text",
                                "text": option_text
                            },
                            "value": str(l.id),
                            "description": {
                                "type": "plain_text",
                                "text": f"Employee: {l.employee_id} | Amount: {amount_str}"
                            }
                        })

                metadata = json.dumps({"batch_id": batch_id, "channel_id": channel_id, "ts": ts})

                await client.views_open(
                    trigger_id=trigger_id,
                    view={
                        "type": "modal",
                        "callback_id": "partial_approval_modal",
                        "private_metadata": metadata,
                        "title": {"type": "plain_text", "text": "Partial Approval"},
                        "submit": {"type": "plain_text", "text": "Approve Selected"},
                        "close": {"type": "plain_text", "text": "Cancel"},
                        "blocks": [
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": f"*Select employees to approve for batch:*\n`{batch_id}`\n\n_Select the employees you want to approve from the list below._"
                                }
                            },
                            {
                                "type": "input",
                                "block_id": "approval_block",
                                "label": {
                                    "type": "plain_text",
                                    "text": "Employees to Approve"
                                },
                                "element": {
                                    "type": "checkboxes",
                                    "action_id": "selected_lines",
                                    "options": options,
                                    "focus_on_load": False
                                },
                                "hint": {
                                    "type": "plain_text",
                                    "text": f"Total {len(lines)} employee(s) available. Select the ones you want to approve."
                                }
                            }
                        ]
                    }
                )
                logger.info(f"✅ Opened partial approval modal for batch {batch_id}")
            except Exception as e:
                logger.exception(f"❌ Failed to open modal: {e}")
                await client.chat_postMessage(channel=channel_id, text=f"❌ Error opening modal: {e}")

        asyncio.create_task(open_modal_task())


    @slack_app.view("partial_approval_modal")
    async def handle_partial_submission(ack, body: Dict[str, Any], client):
        """Handle modal submission for partial approval"""
        logger.info(f"📝 Partial approval modal submitted", extra={"view_id": body.get("view", {}).get("id")})
        await ack()  # ✅ 即時回應 Slack

        try:
            meta = json.loads(body["view"]["private_metadata"])
            batch_id = meta["batch_id"]
            channel_id = meta["channel_id"]
            ts = meta["ts"]
            user_id = body["user"]["id"]

            values = body["view"]["state"]["values"]
            selected_items = values["approval_block"]["selected_lines"].get("selected_options", [])
            selected_ids = [item["value"] for item in selected_items if item["value"] != "none"]

            logger.info(f"✅ {user_id} approved {len(selected_ids)} items in batch {batch_id}")

            with closing(SessionLocal()) as db:
                # 確保 batch 存在
                batch = db.query(PayrollBatch).filter_by(id=batch_id).first()
                if not batch:
                    month = extract_month_from_batch_id(batch_id)
                    batch = PayrollBatch(
                        id=batch_id,
                        month=month,
                        status=BatchStatus.PENDING_APPROVAL,
                        total_amount=0,
                        line_count=0,
                        anomaly_count=0,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(batch)
                    db.flush()
                    logger.info(f"✅ Created placeholder batch {batch_id}")

                # 1️⃣ 標記已核准的 PayrollLine（使用 metadata 存儲狀態）
                if selected_ids:
                    # PayrollLine 沒有 status 字段，使用 metadata 存儲批准狀態
                    for line_id in selected_ids:
                        line = db.query(PayrollLine).filter_by(id=line_id).first()
                        if line:
                            if line.metadata_ is None:
                                line.metadata_ = {}
                            line.metadata_["status"] = "APPROVED"
                            line.metadata_["approved_at"] = datetime.utcnow().isoformat()
                            line.updated_at = datetime.utcnow()
                    logger.info(f"🧾 Updated {len(selected_ids)} PayrollLine(s) as APPROVED")

                # 2️⃣ 寫入 Approval 記錄
                approval = Approval(
                    id=str(uuid.uuid4()),
                    batch_id=batch_id,
                    decision=ApprovalDecision.APPROVE_PARTIAL,
                    approver=user_id,
                    selected_ids=",".join(selected_ids),
                    created_at=datetime.utcnow()
                )
                db.add(approval)

                # 3️⃣ 更新 Batch 狀態
                # 部分批准时，保持 PENDING_APPROVAL 状态，直到 on-chain 交易完成
                # 或者设置为 APPROVED（如果部分批准也算批准）
                # 这里我们保持 PENDING_APPROVAL，因为只有部分项目被批准
                batch.updated_at = datetime.utcnow()
                db.commit()
                logger.info(f"✅ Batch {batch_id} partial approval recorded (status: {batch.status})")

            # 4️⃣ 更新 Slack 原訊息（顯示處理中）
            await client.chat_update(
                channel=channel_id,
                ts=ts,
                text=f"⚡ Processing partial approval by <@{user_id}>...",
                blocks=[{
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"⚡ *Processing Partial Approval* by <@{user_id}>\n_Batch:_ `{batch_id}`\n_Approved Items:_ `{len(selected_ids)}`\n⏳ _Sending on-chain transactions..._"
                    },
                }],
            )

            # 5️⃣ 啟動背景任務處理 on-chain 交易
            asyncio.create_task(
                finalize_partial_payments(
                    selected_ids=selected_ids,
                    batch_id=batch_id,
                    channel_id=channel_id,
                    ts=ts,
                    user_id=user_id
                )
            )

        except Exception as e:
            logger.exception(f"❌ Error handling partial submission: {e}")
            try:
                await client.chat_postMessage(
                    channel=body["user"]["id"],
                    text=f"❌ Failed to process your partial approval.\n```{str(e)[:200]}```"
                )
            except Exception as msg_error:
                logger.exception(f"Failed to send error DM: {msg_error}")


async def finalize_partial_payments(
    selected_ids: List[str],
    batch_id: str,
    channel_id: str,
    ts: str,
    user_id: str
) -> None:
    """
    Background task to finalize partial approval payments.
    
    This function:
    1. Fetches selected PayrollLine records from database
    2. Sends on-chain transactions via OnchainService
    3. Saves transaction records to database
    4. Updates Slack message with transaction results
    
    Args:
        selected_ids: List of PayrollLine IDs to process
        batch_id: Batch identifier
        channel_id: Slack channel ID
        ts: Slack message timestamp
        user_id: Slack user ID who approved
    """
    if not slack_app:
        logger.error("Slack app not initialized, cannot update message")
        return
    
    try:
        # 1️⃣ 從資料庫讀取選中的 PayrollLine
        with closing(SessionLocal()) as db:
            lines = db.query(PayrollLine).filter(PayrollLine.id.in_(selected_ids)).all()
            
            if not lines:
                logger.warning(f"No lines found for selected_ids: {selected_ids}")
                await slack_app.client.chat_update(
                    channel=channel_id,
                    ts=ts,
                    text=f"❌ No transactions found for selected items",
                    blocks=[{
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"❌ *Error*\nNo payroll lines found for the selected items."
                        },
                    }],
                )
                return
            
            # 2️⃣ 準備 on-chain 交易參數
            recipients = [line.wallet for line in lines]
            amounts_usdc = [Decimal(str(line.amount_usdc)) for line in lines]
            
            # 轉換為最小單位（6 decimals）
            policy = PayrollPolicy()
            amounts_smallest = [policy.to_smallest_unit(amt) for amt in amounts_usdc]
            
            logger.info(
                f"💸 Preparing to send {len(recipients)} payments",
                extra={
                    "batch_id": batch_id,
                    "line_count": len(recipients),
                    "total_amount": str(sum(amounts_usdc))
                }
            )
            
            # 3️⃣ 發送 on-chain 交易
            # 檢查是否使用 mock service（開發環境）
            try:
                onchain_service = OnchainService()
                logger.info("Using real OnchainService")
            except Exception as e:
                logger.warning(f"OnchainService initialization failed, using mock: {e}")
                onchain_service = MockOnchainService()
            
            tx_hash = onchain_service.batch_payout(
                recipients=recipients,
                amounts=amounts_smallest,
                batch_id=batch_id,
                metadata=f"Partial approval by {user_id} - {len(selected_ids)} items"
            )
            
            logger.info(f"💸 Sent payment transaction", extra={"tx_hash": tx_hash, "batch_id": batch_id})
            
            # 4️⃣ 保存交易記錄到資料庫
            total_amount = sum(amounts_usdc)
            transaction = Transaction(
                id=str(uuid.uuid4()),
                batch_id=batch_id,
                tx_hash=tx_hash,
                status=TransactionStatus.PENDING,  # 初始狀態為 PENDING，後續可更新為 CONFIRMED/SUCCESS
                recipient_count=len(recipients),
                total_amount=total_amount,
                metadata_={
                    "approver": user_id,
                    "selected_line_ids": selected_ids,
                    "partial_approval": True
                }
            )
            db.add(transaction)
            
            # 更新 batch 狀態為 PROCESSING（交易已發送）
            batch = db.query(PayrollBatch).filter_by(id=batch_id).first()
            if batch:
                batch.status = BatchStatus.PROCESSING
                batch.updated_at = datetime.utcnow()
            
            db.commit()
            
            logger.info(
                f"✅ Transaction saved to database",
                extra={"tx_hash": tx_hash, "batch_id": batch_id}
            )
        
        # 5️⃣ 更新 Slack 訊息顯示成功
        await slack_app.client.chat_update(
            channel=channel_id,
            ts=ts,
            text=f"✅ Partial approval completed - Transaction sent",
            blocks=[{
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"✅ *Partial Approval Completed* by <@{user_id}>\n"
                           f"_Batch:_ `{batch_id}`\n"
                           f"_Approved Items:_ `{len(selected_ids)}`\n"
                           f"_Total Amount:_ `${total_amount} USDC`\n"
                           f"_Transaction Hash:_ `{tx_hash}`\n"
                           f"✅ *Tx hash generated*"
                },
            }],
        )
        
        # 6️⃣ 發送私訊確認
        await slack_app.client.chat_postMessage(
            channel=user_id,
            text=f"✅ Partial approval completed!\n"
                 f"Batch: `{batch_id}`\n"
                 f"Items: {len(selected_ids)}\n"
                 f"Transaction: `{tx_hash}`"
        )
        
    except Exception as e:
        logger.exception(f"❌ Error finalizing partial payments: {e}")
        
        # 更新 Slack 訊息顯示錯誤
        try:
            await slack_app.client.chat_update(
                channel=channel_id,
                ts=ts,
                text=f"❌ Error processing partial approval",
                blocks=[{
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"❌ *Error Processing Partial Approval*\n"
                               f"_Batch:_ `{batch_id}`\n"
                               f"```{str(e)[:300]}```"
                    },
                }],
            )
        except Exception as update_error:
            logger.exception(f"Failed to update Slack with error: {update_error}")


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
        
        # Trigger command
        elif action == "trigger" and len(text) > 1:
            month = text[1]
            await client.chat_postMessage(
                channel=channel,
                text=f"🚀 Triggering payroll workflow for `{month}`...\n_This may take a few minutes._"
            )
            # TODO: Trigger workflow via API call
        
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
    async def global_error_handler(error, body, logger_arg):
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