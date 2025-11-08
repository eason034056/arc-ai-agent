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
import uuid
from decimal import Decimal

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
from app.db.connection import SessionLocal
from app.db.models import PayrollBatch, PayrollLine, BatchStatus
from datetime import datetime

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


def save_payroll_results_to_db(state: AgentState) -> None:
    """
    Save payroll results to database after workflow completion.
    
    This function persists:
    - PayrollBatch: total_amount, line_count, anomaly_count, summary
    - PayrollLine: All employee payroll lines (employee_id, wallet, amount, flags)
    
    Args:
        state: Final AgentState from workflow
        
    Raises:
        Exception: If database save fails
    """
    db = SessionLocal()
    try:
        # Calculate totals
        total_amount = Decimal("0")
        anomaly_count = 0
        
        for line in state.lines:
            if hasattr(line, 'amount_usdc'):
                total_amount += Decimal(str(line.amount_usdc))
            elif isinstance(line, dict):
                total_amount += Decimal(str(line.get("amount_usdc", 0)))
            
            # Count anomalies (lines with flags)
            if hasattr(line, 'flags') and line.flags:
                anomaly_count += 1
            elif isinstance(line, dict) and line.get("flags"):
                anomaly_count += 1
        
        # Get summary from metadata
        summary = state.metadata.get("summary")
        
        # Check if batch already exists
        existing_batch = db.query(PayrollBatch).filter_by(id=state.batch_id).first()
        
        if existing_batch:
            # Update existing batch
            existing_batch.total_amount = total_amount
            existing_batch.line_count = len(state.lines)
            existing_batch.anomaly_count = anomaly_count
            existing_batch.summary = summary
            existing_batch.updated_at = datetime.utcnow()
            logger.info("Updated existing PayrollBatch", extra={"batch_id": state.batch_id})
        else:
            # Create new batch
            batch = PayrollBatch(
                id=state.batch_id,
                month=state.month,
                status=BatchStatus.PENDING_APPROVAL,
                total_amount=total_amount,
                line_count=len(state.lines),
                anomaly_count=anomaly_count,
                summary=summary,
            )
            db.add(batch)
            logger.info("Created new PayrollBatch", extra={"batch_id": state.batch_id})
        
        # Save payroll lines
        for line in state.lines:
            # Extract line data
            if hasattr(line, 'employee_id'):
                employee_id = line.employee_id
                wallet = line.wallet
                amount_usdc = Decimal(str(line.amount_usdc))
                flags = line.flags or []
            elif isinstance(line, dict):
                employee_id = line.get("employee_id")
                wallet = line.get("wallet")
                amount_usdc = Decimal(str(line.get("amount_usdc", 0)))
                flags = line.get("flags", [])
            else:
                logger.warning(f"Skipping invalid line format: {type(line)}")
                continue
            
            # Check if line already exists
            existing_line = db.query(PayrollLine).filter_by(
                batch_id=state.batch_id,
                employee_id=employee_id
            ).first()
            
            if not existing_line:
                payroll_line = PayrollLine(
                    id=str(uuid.uuid4()),
                    batch_id=state.batch_id,
                    employee_id=employee_id,
                    wallet=wallet,
                    amount_usdc=amount_usdc,
                    flags=flags if isinstance(flags, list) else [],
                )
                db.add(payroll_line)
        
        db.commit()
        logger.info(
            "✅ Payroll results saved to database",
            extra={
                "batch_id": state.batch_id,
                "lines_saved": len(state.lines),
                "total_amount": str(total_amount),
                "anomaly_count": anomaly_count,
            }
        )
        
    except Exception as e:
        db.rollback()
        logger.error(
            "❌ Failed to save payroll results to database",
            extra={"batch_id": state.batch_id, "error": str(e)},
            exc_info=True
        )
        raise
    finally:
        db.close()


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
        
        # ✅ Step 1: Save results to database after workflow completes
        try:
            save_payroll_results_to_db(final_state)
        except Exception as db_error:
            logger.error(
                "Failed to save payroll results to database",
                extra={"batch_id": batch_id, "error": str(db_error)},
                exc_info=True
            )
            # Don't fail the workflow if DB save fails, but log the error
        
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
