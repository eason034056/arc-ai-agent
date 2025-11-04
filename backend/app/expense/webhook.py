"""
Expense webhook handler
處理費用系統的 webhook 回調
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
import logging

logger = logging.getLogger(__name__)

# router 供 FastAPI 使用
router = APIRouter(prefix="/expense", tags=["expense"])


@router.post("/webhook")
async def expense_webhook(payload: Dict[str, Any]):
    """
    接收費用系統的回寫結果
    
    Args:
        payload: 費用系統回傳的資料
        
    Returns:
        確認訊息
    """
    try:
        logger.info(f"Received expense webhook: {payload}")
        # TODO: 處理費用回寫邏輯
        # 1. 驗證 payload
        # 2. 更新資料庫
        # 3. 記錄審計日誌
        return {"status": "ok", "message": "Webhook received"}
    except Exception as e:
        logger.error(f"Error processing expense webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

