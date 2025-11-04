"""
Expense webhook handler
Handles webhook callbacks from the expense system
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
import logging

logger = logging.getLogger(__name__)

# Router for FastAPI
router = APIRouter(prefix="/expense", tags=["expense"])


@router.post("/webhook")
async def expense_webhook(payload: Dict[str, Any]):
    """
    Receive writeback results from the expense system
    
    Args:
        payload: Data returned from the expense system
        
    Returns:
        Confirmation message
    """
    try:
        logger.info(f"Received expense webhook: {payload}")
        # TODO: Implement expense writeback logic
        # 1. Validate payload
        # 2. Update database
        # 3. Record audit log
        return {"status": "ok", "message": "Webhook received"}
    except Exception as e:
        logger.error(f"Error processing expense webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))
