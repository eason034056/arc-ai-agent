"""
Agent Utilities

Provides common utilities for agent nodes, including a robust `safe_node` decorator
that ensures all LangGraph nodes execute safely, with detailed logging,
execution-time measurement, and structured metadata updates.
"""

import time
import traceback
from functools import wraps
from typing import Callable, Any

from app.db.schema import AgentState
from app.core.logging import get_logger

# ------------------------------------------------------------------------------
# Module-level constants
# ------------------------------------------------------------------------------
# ANSI color codes for colored terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

logger = get_logger(__name__)


def safe_node(node_func: Callable) -> Callable:
    """
    Decorator to execute a LangGraph node safely with structured logging.

    This decorator ensures:
      1. Each node is wrapped in try/except for robust error handling.
      2. Execution time is measured and logged.
      3. All results (success or failure) update metadata for downstream visibility.
      4. Logs are color-coded for easy visual parsing in console output.

    Args:
        node_func (Callable): The node function to be wrapped.
            Must accept an `AgentState` and return an updated `AgentState`.

    Returns:
        Callable: Wrapped node function with error handling and metadata tracking.

    Example:
        @safe_node
        def run(state: AgentState) -> AgentState:
            # Node logic here
            return new_state
    """

    @wraps(node_func)
    def wrapper(state: AgentState, *args: Any, **kwargs: Any) -> AgentState:
        """
        Wrapper that executes the node function safely and logs execution details.

        Args:
            state (AgentState): The current agent state before node execution.
            *args (Any): Additional positional arguments passed to the node.
            **kwargs (Any): Additional keyword arguments passed to the node.

        Returns:
            AgentState: Updated state after node execution (always returned,
            even if the node raised an exception).
        """
        node_name = node_func.__module__.split(".")[-1]
        start_time = time.time()

        # ----------------------------------------------------------------------
        # Step 1: Log start event
        # ----------------------------------------------------------------------
        logger.info(
            f"[Node: {node_name}] ▶️ Starting...",
            extra={"batch_id": state.batch_id, "node": node_name},
        )

        try:
            # ------------------------------------------------------------------
            # Step 2: Execute the node function
            # ------------------------------------------------------------------
            new_state = node_func(state, *args, **kwargs)
            elapsed = round(time.time() - start_time, 3)

            # ------------------------------------------------------------------
            # Step 3: Log success
            # ------------------------------------------------------------------
            logger.info(
                f"{GREEN}[Node: {node_name}] ✅ Completed successfully ({elapsed}s){RESET}",
                extra={"batch_id": state.batch_id, "node": node_name, "elapsed": elapsed},
            )

            # ------------------------------------------------------------------
            # Step 4: Update metadata with timing info
            # ------------------------------------------------------------------
            updated_metadata = {
                **(new_state.metadata or {}),
                f"{node_name}_status": "success",
                f"{node_name}_time": elapsed,
            }

            # Return updated state with timing metadata
            return new_state.model_copy(update={"metadata": updated_metadata})

        except Exception as e:  # pylint: disable=broad-except
            # ------------------------------------------------------------------
            # Step 5: Handle and log errors without breaking the workflow
            # ------------------------------------------------------------------
            elapsed = round(time.time() - start_time, 3)
            tb_str = traceback.format_exc()

            logger.error(
                f"{RED}[Node: {node_name}] ❌ Failed after {elapsed}s: {str(e)}{RESET}",
                extra={
                    "batch_id": state.batch_id,
                    "node": node_name,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "traceback": tb_str,
                },
            )

            # Append this node's error message to the cumulative error list
            errors = list(state.errors) + [f"{node_name}: {str(e)}"]

            # Merge failure metadata for downstream nodes
            updated_metadata = {
                **(state.metadata or {}),
                f"{node_name}_status": "failed",
                f"{node_name}_time": elapsed,
                f"{node_name}_error": str(e),
            }

            # Prefer partially computed state (if available)
            safe_base = locals().get("new_state", state)

            # Return a safe, consistent AgentState instance
            return safe_base.model_copy(
                update={"errors": errors, "metadata": updated_metadata}
            )

    return wrapper
