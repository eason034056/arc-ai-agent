"""
LangGraph Workflow Definition

This module defines the complete payroll automation workflow using LangGraph.

LangGraph is a framework for building stateful, multi-actor AI applications.
It allows us to define complex workflows as directed graphs where:
- Nodes = Functions that process state
- Edges = Transitions between nodes
- State = Immutable data flowing through the graph

Workflow:
    START
      ↓
    ingest (load employee data)
      ↓
    clean (validate & normalize)
      ↓
    compute (calculate salaries)
      ↓
    detect (find anomalies)
      ↓
    summarize (create summary)
      ↓
    propose (send to Slack)
      ↓
    approve_gate (wait for decision) ← Human in the loop
      ↓
    ┌─ REJECT → END
    │
    └─ APPROVE_ALL / APPROVE_PARTIAL
          ↓
        onchain (blockchain transactions)
          ↓
        writeback (save results)
          ↓
        reconcile (generate report)
          ↓
        finalize (mark completed)
          ↓
        END
"""

from typing import Callable, Dict, Any
from langgraph.graph import StateGraph, END

from app.db.schema import AgentState
from app.agent.policies import PayrollPolicy
from app.agent.nodes import (
    node_ingest,
    node_clean,
    node_compute,
    node_detect,
    node_summarize,
    node_propose,
    node_approve_gate,
    node_onchain,
    node_writeback,
    node_reconcile,
    node_finalize,
)
from app.agent.utils import safe_node
from app.core.logging import get_logger

logger = get_logger(__name__)


# ================================================================
# State conversion helper
# ================================================================
def ensure_agent_state(state) -> AgentState:
    """Ensure the state is a valid AgentState object."""
    if isinstance(state, AgentState):
        return state
    elif isinstance(state, dict):
        return AgentState(**state)
    else:
        return AgentState(**dict(state))


# ================================================================
# Graph creation
# ================================================================
def create_payroll_graph(
    policy: PayrollPolicy = None,
    ruleset: Dict[str, Any] = None,
    slack_client=None,
    onchain_service=None,
    approval_repo=None,
    webhook_client=None,
    db_repo=None,
    blockchain_client=None,
) -> StateGraph:
    """Create the payroll automation workflow graph."""
    if policy is None:
        policy = PayrollPolicy()

    logger.info("Creating payroll workflow graph")

    # ----------------------------------------
    # 1. Initialize StateGraph
    # ----------------------------------------
    graph = StateGraph(AgentState)

    # ----------------------------------------
    # 2. Define all nodes
    # ----------------------------------------
    graph.add_node("ingest", safe_node(lambda s: node_ingest.run(ensure_agent_state(s))))
    graph.add_node("clean", safe_node(lambda s: node_clean.run(ensure_agent_state(s), policy=policy)))
    graph.add_node("compute", safe_node(lambda s: node_compute.run(ensure_agent_state(s), ruleset=ruleset, policy=policy)))
    graph.add_node("detect", safe_node(lambda s: node_detect.run(ensure_agent_state(s), policy=policy)))
    graph.add_node("summarize", safe_node(lambda s: node_summarize.run(ensure_agent_state(s), use_ai=True)))
    graph.add_node("propose", safe_node(lambda s: node_propose.run(ensure_agent_state(s), slack_client=slack_client)))
    graph.add_node("approve_gate", safe_node(lambda s: node_approve_gate.run(ensure_agent_state(s), policy=policy, approval_repo=approval_repo)))
    graph.add_node("onchain", safe_node(lambda s: node_onchain.run(ensure_agent_state(s), onchain_service=onchain_service, policy=policy)))
    graph.add_node("writeback", safe_node(lambda s: node_writeback.run(ensure_agent_state(s), webhook_client=webhook_client, db_repo=db_repo)))
    graph.add_node("reconcile", safe_node(lambda s: node_reconcile.run(ensure_agent_state(s), blockchain_client=blockchain_client)))
    graph.add_node("finalize", safe_node(lambda s: node_finalize.run(ensure_agent_state(s))))

    # ----------------------------------------
    # 3. Define edges (workflow transitions)
    # ----------------------------------------
    graph.set_entry_point("ingest")

    # Main linear flow
    graph.add_edge("ingest", "clean")
    graph.add_edge("clean", "compute")
    graph.add_edge("compute", "detect")
    graph.add_edge("detect", "summarize")
    graph.add_edge("summarize", "propose")
    graph.add_edge("propose", "approve_gate")

    # ----------------------------------------
    # 4. Conditional branching after approval
    # ----------------------------------------
    def approval_router(state: AgentState) -> str:
        """Route based on approval decision."""
        if not state.approval:
            logger.warning("No approval found, routing to END", extra={"batch_id": state.batch_id})
            return "END"

        decision = state.approval.get("decision")
        logger.info(
            f"Approval decision: {decision}",
            extra={"batch_id": state.batch_id, "decision": decision},
        )

        if decision in ["APPROVE_ALL", "APPROVE_PARTIAL"]:
            return "onchain"
        return "END"

    graph.add_conditional_edges(
        "approve_gate",
        approval_router,
        {"onchain": "onchain", "END": END},
    )

    # ----------------------------------------
    # 5. Continue flow after approval
    # ----------------------------------------
    graph.add_edge("onchain", "writeback")
    graph.add_edge("writeback", "reconcile")
    graph.add_edge("reconcile", "finalize")
    graph.add_edge("finalize", END)

    logger.info(f"Graph nodes: {list(graph.nodes.keys())}")
    logger.info(f"Graph edges: {graph.edges}")
    logger.info("✅ Payroll workflow graph created successfully")

    return graph


# ================================================================
# Graph compilation and execution
# ================================================================
def compile_graph(**kwargs) -> Callable:
    """Compile the graph into an executable function."""
    graph = create_payroll_graph(**kwargs)
    return graph.compile()


def run_payroll_workflow(batch_id: str, month: str, **kwargs) -> AgentState:
    """Run the complete payroll workflow."""
    logger.info("Starting payroll workflow", extra={"batch_id": batch_id, "month": month})

    initial_state = AgentState(
        batch_id=batch_id,
        month=month,
        lines=[],
        approval=None,
        tx_hashes=[],
        errors=[],
        metadata={},
    )

    app = compile_graph(**kwargs)

    try:
        final_state = app.invoke(initial_state)

        if not isinstance(final_state, AgentState):
            final_state = AgentState(**final_state)

        logger.info(
            "Payroll workflow completed",
            extra={
                "batch_id": batch_id,
                "final_status": final_state.metadata.get("final_status"),
                "tx_count": len(final_state.tx_hashes),
                "error_count": len(final_state.errors),
            },
        )
        return final_state

    except Exception as e:
        logger.error(
            "Payroll workflow failed",
            extra={"batch_id": batch_id, "error": str(e)},
            exc_info=True,
        )
        raise


# ================================================================
# Example usage
# ================================================================
if __name__ == "__main__":
    """Manual test entry."""
    final_state = run_payroll_workflow(
        batch_id="test_batch_001",
        month="2025-11",
        policy=PayrollPolicy(),
    )

    print("\n" + "=" * 50)
    print("WORKFLOW COMPLETED")
    print("=" * 50)
    print(f"Batch ID: {final_state.batch_id}")
    print(f"Month: {final_state.month}")
    print(f"Lines processed: {len(final_state.lines)}")
    print(f"Transactions: {len(final_state.tx_hashes)}")
    print(f"Errors: {len(final_state.errors)}")
    print(f"Final status: {final_state.metadata.get('final_status', 'unknown')}")
    print("=" * 50 + "\n")
