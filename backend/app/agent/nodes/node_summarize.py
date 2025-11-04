"""
Summarize Node

This node creates a human-readable summary of the payroll batch.
The summary is used in the Slack approval message.

Summary includes:
- Total amount and recipient count
- Number of anomalies detected
- Department breakdown (if available)
- Top amounts
- Comparison to previous months

Can optionally use AI (OpenAI) for natural language generation.
"""

from decimal import Decimal
from typing import Dict, Any, List

from app.db.schema import AgentState, PayrollLineDTO
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def run(state: AgentState, use_ai: bool = False) -> AgentState:
    """
    Summarize payroll batch for human review
    
    Args:
        state: Current agent state
        use_ai: Whether to use AI for summary generation
        
    Returns:
        Updated state with summary in metadata
        
    Example:
        state = AgentState(
            batch_id="batch_123",
            month="2025-11",
            lines=[...]
        )
        
        new_state = run(state)
        
        print(new_state.metadata["summary"])
        # {
        #     "month": "2025-11",
        #     "total_amount": "26700.00",
        #     "recipient_count": 5,
        #     "anomaly_count": 2,
        #     "average_amount": "5340.00",
        #     ...
        # }
    """
    logger.info(
        "Starting batch summarization",
        extra={
            "batch_id": state.batch_id,
            "use_ai": use_ai
        }
    )
    
    # ========================================
    # CALCULATE BASIC STATISTICS
    # ========================================
    total_amount = sum(line.amount_usdc for line in state.lines)
    recipient_count = len(state.lines)
    
    # Count anomalies
    anomaly_count = sum(1 for line in state.lines if line.flags)
    
    # Calculate average
    average_amount = total_amount / recipient_count if recipient_count > 0 else Decimal("0")
    
    # Find min and max
    amounts = [line.amount_usdc for line in state.lines if line.amount_usdc > 0]
    min_amount = min(amounts) if amounts else Decimal("0")
    max_amount = max(amounts) if amounts else Decimal("0")
    
    # ========================================
    # DEPARTMENT BREAKDOWN (if available)
    # ========================================
    departments: Dict[str, Dict[str, Any]] = {}
    
    for line in state.lines:
        dept = line.metadata.get("department", "Unknown")
        
        if dept not in departments:
            departments[dept] = {
                "count": 0,
                "total": Decimal("0")
            }
        
        departments[dept]["count"] += 1
        departments[dept]["total"] += line.amount_usdc
    
    # ========================================
    # TOP AMOUNTS (for review)
    # ========================================
    # Sort by amount descending
    sorted_lines = sorted(state.lines, key=lambda x: x.amount_usdc, reverse=True)
    top_5 = [
        {
            "employee_id": line.employee_id,
            "amount": str(line.amount_usdc),
            "flags": line.flags
        }
        for line in sorted_lines[:5]
    ]
    
    # ========================================
    # FLAGGED ITEMS
    # ========================================
    flagged_items = [
        {
            "employee_id": line.employee_id,
            "amount": str(line.amount_usdc),
            "flags": line.flags
        }
        for line in state.lines
        if line.flags
    ]
    
    # ========================================
    # CREATE SUMMARY
    # ========================================
    summary = {
        "month": state.month,
        "batch_id": state.batch_id,
        "total_amount": str(total_amount),
        "recipient_count": recipient_count,
        "anomaly_count": anomaly_count,
        "average_amount": str(average_amount),
        "min_amount": str(min_amount),
        "max_amount": str(max_amount),
        "department_breakdown": {
            dept: {
                "count": info["count"],
                "total": str(info["total"])
            }
            for dept, info in departments.items()
        },
        "department_count": len(departments),
        "top_amounts": top_5,
        "flagged_items": flagged_items,
    }
    
    # ========================================
    # AI-GENERATED NARRATIVE (optional)
    # ========================================
    if use_ai:
        try:
            narrative = generate_ai_narrative(summary)
            summary["ai_narrative"] = narrative
        except Exception as e:
            logger.warning(
                "AI narrative generation failed",
                extra={
                    "batch_id": state.batch_id,
                    "error": str(e)
                }
            )
            summary["ai_narrative"] = None
    
    logger.info(
        "Batch summarization completed",
        extra={
            "batch_id": state.batch_id,
            "summary": {
                "total": str(total_amount),
                "count": recipient_count,
                "anomalies": anomaly_count
            }
        }
    )
    
    # ========================================
    # UPDATE STATE
    # ========================================
    new_state = state.model_copy(
        update={
            "metadata": {
                **state.metadata,
                "summary": summary,
                "summarization_complete": True
            }
        }
    )
    
    return new_state


def generate_ai_narrative(summary: Dict[str, Any]) -> str:
    """
    Generate natural language summary using OpenAI
    
    This is optional and requires OPENAI_API_KEY in settings.
    
    Args:
        summary: Statistical summary dictionary
        
    Returns:
        Natural language narrative
        
    Example output:
        "November 2025 payroll includes 5 recipients totaling $26,700.00 USDC.
        The average payment is $5,340.00. Two anomalies were detected:
        Employee emp_005 has an unusually high amount ($8,000), and
        Employee emp_004 is a first-time recipient."
    """
    settings = get_settings()
    
    if not settings.openai_api_key:
        return "AI narrative unavailable (no API key)"
    
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=settings.openai_api_key)
        
        # Create prompt for AI
        prompt = f"""
        Summarize this payroll batch in 2-3 sentences for management review:
        
        Month: {summary['month']}
        Total: ${summary['total_amount']} USDC
        Recipients: {summary['recipient_count']}
        Anomalies: {summary['anomaly_count']}
        Average: ${summary['average_amount']}
        
        Flagged items: {summary['flagged_items']}
        
        Write a concise, professional summary highlighting key points and any concerns.
        """
        
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You are a financial analyst summarizing payroll data."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )
        
        narrative = response.choices[0].message.content.strip()
        
        logger.info(
            "AI narrative generated",
            extra={"batch_id": summary["batch_id"]}
        )
        
        return narrative
        
    except Exception as e:
        logger.error(
            "AI narrative generation error",
            extra={
                "batch_id": summary["batch_id"],
                "error": str(e)
            },
            exc_info=True
        )
        raise

