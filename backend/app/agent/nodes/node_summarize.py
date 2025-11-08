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

Can optionally use AI (Google Gemini) for natural language generation.
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
    Generate natural language summary using Google Gemini
    
    This is optional and requires GEMINI_API_KEY in settings.
    
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
    
    if not settings.gemini_api_key:
        return "AI narrative unavailable (no API key)"
    
    try:
        import google.generativeai as genai
        
        # Configure Gemini API
        genai.configure(api_key=settings.gemini_api_key)
        
        # Create prompt for AI
        prompt = f"""
        You are an AI payroll analyst preparing a short Slack summary.

        Write exactly 3 sentences:
        1. State the payroll month, total amount, and employee count.
        2. Describe anomalies and departments affected.
        3. Give a concise recommendation (e.g., approve, review, or reject).

        Example:
        > The October 2025 payroll totals $18,450 USDC for 4 employees.
        > Two anomalies were detected in the Finance department.
        > Recommend reviewing flagged payments before approval.

        Month: {summary['month']}
        Total: ${summary['total_amount']} USDC
        Employees: {summary['recipient_count']}
        Anomalies: {summary['anomaly_count']}
        Departments: {list(summary.get('department_breakdown', {}).keys())}
        Flagged items: {len(summary.get('flagged_items', []))}
        """
        
        # Initialize the model
        model = genai.GenerativeModel(settings.gemini_model)
        
        # Generate content
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=512,  # Increased to 512 tokens to avoid truncation
                )
            )
            logger.debug("Gemini API call successful", extra={"response_type": type(response).__name__})
        except Exception as api_error:
            logger.error(
                "Gemini API call failed",
                extra={"error": str(api_error), "error_type": type(api_error).__name__},
                exc_info=True
            )
            raise
        
        # Check for safety filters or blocked content
        finish_reason = None
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            # finish_reason: 1=STOP, 2=MAX_TOKENS, 3=SAFETY, 4=RECITATION, 5=OTHER
            finish_reason = getattr(candidate, 'finish_reason', None)
            if finish_reason == 3:  # SAFETY - content was filtered
                raise ValueError("Content was blocked by safety filters. Try adjusting the prompt.")
            elif finish_reason == 2:  # MAX_TOKENS - but might still have partial content
                logger.warning("Response hit max tokens limit, extracting partial content", extra={"finish_reason": finish_reason})
        
        # Extract text from response
        # Handle different response formats
        narrative = ""
        
        # Log response structure for debugging
        logger.debug(
            "Gemini API response structure",
            extra={
                "has_candidates": hasattr(response, 'candidates'),
                "candidates_count": len(response.candidates) if hasattr(response, 'candidates') and response.candidates else 0,
                "finish_reason": finish_reason
            }
        )
        
        # Extract text manually from candidates (more reliable than response.text)
        if hasattr(response, 'candidates') and response.candidates:
            text_parts = []
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        if hasattr(part, 'text'):
                            text_parts.append(part.text)
                elif hasattr(candidate, 'text'):
                    # Alternative: direct text attribute
                    text_parts.append(candidate.text)
            narrative = ' '.join(text_parts).strip() if text_parts else ""
            logger.debug("Extracted narrative from candidates", extra={"length": len(narrative), "parts_count": len(text_parts)})
        
        # Fallback: try response.text if manual extraction failed
        if not narrative:
            try:
                if hasattr(response, 'text'):
                    narrative = response.text.strip()
                    logger.debug("Extracted narrative from response.text", extra={"length": len(narrative)})
            except (ValueError, AttributeError) as e:
                logger.debug(f"response.text access failed: {e}")
        
        # If still empty, try alternative extraction methods
        if not narrative:
            # Try accessing response directly as dict-like
            if hasattr(response, '__dict__'):
                logger.debug("Response dict keys", extra={"keys": list(response.__dict__.keys())})
            
            # Try to get text from prompt_feedback or other fields
            if hasattr(response, 'prompt_feedback'):
                logger.warning("Prompt feedback available", extra={"feedback": str(response.prompt_feedback)})
        
        if not narrative:
            # Log full response for debugging (truncated)
            response_str = str(response)[:500] if response else "None"
            logger.error(
                "Empty response from Gemini API",
                extra={
                    "response_preview": response_str,
                    "response_type": type(response).__name__
                }
            )
            raise ValueError("Empty response from Gemini API - no text content returned")
        
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

