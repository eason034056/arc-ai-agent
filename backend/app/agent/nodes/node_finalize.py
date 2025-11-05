"""
Node: Finalize

This node marks the end of the payroll workflow.
It inspects previous metadata and errors to determine the final status,
and writes a clean summary back into the AgentState.
"""

from app.db.schema import AgentState
from app.core.logging import get_logger

logger = get_logger(__name__)


def run(state: AgentState) -> AgentState:
    """
    Finalize workflow status and summarize execution results.

    Args:
        state: Final state after all workflow nodes.

    Returns:
        Updated AgentState with final_status and summary metadata.
    """
    error_count = len(state.errors)
    tx_count = len(state.tx_hashes)
    
    # Calculate total execution time from all node timings
    total_time = sum([
        v for k, v in state.metadata.items()
        if k.endswith("_time") and isinstance(v, (int, float))
    ])

    # Determine final status based on errors
    if error_count == 0:
        final_status = "completed"
    elif error_count > 0 and error_count < 3:
        final_status = "completed_with_warnings"
    else:
        final_status = "failed"

    # Build final metadata
    metadata = {
        **state.metadata,
        "final_status": final_status,
        "error_count": error_count,
        "tx_count": tx_count,
        "total_time_sec": round(total_time, 3) if total_time > 0 else 0
    }

    logger.info(
        f"[Finalize] 🎯 Workflow ended with status: {final_status.upper()} "
        f"(errors={error_count}, tx={tx_count}, total_time={total_time:.2f}s)",
        extra={
            "batch_id": state.batch_id,
            "final_status": final_status,
            "error_count": error_count,
            "tx_count": tx_count
        }
    )

    return state.model_copy(update={"metadata": metadata})
