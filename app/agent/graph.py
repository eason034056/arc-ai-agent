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
        END

Key Features:
- Type-safe state management (Pydantic)
- Conditional branching based on approval
- Pure functional nodes (testable)
- Dependency injection for services
- Error handling and recovery
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
)
from app.core.logging import get_logger

logger = get_logger(__name__)


def create_payroll_graph(
    policy: PayrollPolicy = None,
    ruleset: Dict[str, Any] = None,
    slack_client = None,
    onchain_service = None,
    approval_repo = None,
    webhook_client = None,
    db_repo = None,
    blockchain_client = None
) -> StateGraph:
    """
    Create the payroll automation workflow graph
    
    This function creates a LangGraph StateGraph with all nodes and edges defined.
    Services are injected as dependencies for testability.
    
    Args:
        policy: Payroll policy (business rules)
        ruleset: Salary computation rules
        slack_client: Slack Bolt client
        onchain_service: Web3 service for blockchain
        approval_repo: Repository for approval data
        webhook_client: HTTP client for webhooks
        db_repo: Database repository
        blockchain_client: Web3 client for reading blockchain
        
    Returns:
        Compiled StateGraph ready for execution
        
    Usage:
        # Create graph with dependencies
        graph = create_payroll_graph(
            policy=PayrollPolicy(),
            slack_client=slack_app.client,
            onchain_service=OnchainService(),
            ...
        )
        
        # Execute workflow
        initial_state = AgentState(
            batch_id="batch_123",
            month="2025-11",
            lines=[]
        )
        
        final_state = graph.invoke(initial_state)
        print(final_state.metadata["reconciliation_report"])
    """
    if policy is None:
        policy = PayrollPolicy()
    
    logger.info("Creating payroll workflow graph")
    
    # ========================================
    # CREATE GRAPH
    # ========================================
    # StateGraph takes the state schema as a type parameter
    # All nodes must accept and return this state type
    graph = StateGraph(AgentState)
    
    # ========================================
    # DEFINE NODES
    # ========================================
    # Each node is a function that processes the state
    # We wrap each node to inject dependencies
    
    # Node 1: Ingest
    # Load employee data from data sources
    graph.add_node(
        "ingest",
        lambda state: node_ingest.run(state)
    )
    
    # Node 2: Clean
    # Validate and normalize data
    graph.add_node(
        "clean",
        lambda state: node_clean.run(state, policy=policy)
    )
    
    # Node 3: Compute
    # Calculate salary amounts
    graph.add_node(
        "compute",
        lambda state: node_compute.run(state, ruleset=ruleset, policy=policy)
    )
    
    # Node 4: Detect
    # Detect anomalies
    graph.add_node(
        "detect",
        lambda state: node_detect.run(state, policy=policy)
    )
    
    # Node 5: Summarize
    # Create human-readable summary
    graph.add_node(
        "summarize",
        lambda state: node_summarize.run(state, use_ai=True)
    )
    
    # Node 6: Propose
    # Send approval request to Slack
    graph.add_node(
        "propose",
        lambda state: node_propose.run(state, slack_client=slack_client)
    )
    
    # Node 7: Approve Gate
    # Wait for human approval (blocking)
    graph.add_node(
        "approve_gate",
        lambda state: node_approve_gate.run(
            state,
            policy=policy,
            approval_repo=approval_repo
        )
    )
    
    # Node 8: Onchain
    # Execute blockchain transactions
    graph.add_node(
        "onchain",
        lambda state: node_onchain.run(
            state,
            onchain_service=onchain_service,
            policy=policy
        )
    )
    
    # Node 9: Writeback
    # Write results to external systems
    graph.add_node(
        "writeback",
        lambda state: node_writeback.run(
            state,
            webhook_client=webhook_client,
            db_repo=db_repo
        )
    )
    
    # Node 10: Reconcile
    # Final reconciliation and reporting
    graph.add_node(
        "reconcile",
        lambda state: node_reconcile.run(
            state,
            blockchain_client=blockchain_client
        )
    )
    
    # ========================================
    # DEFINE EDGES (Linear Flow)
    # ========================================
    # add_edge(from, to) creates a transition
    # The workflow follows this path:
    
    # Set entry point (first node)
    graph.set_entry_point("ingest")
    
    # Linear edges
    graph.add_edge("ingest", "clean")
    graph.add_edge("clean", "compute")
    graph.add_edge("compute", "detect")
    graph.add_edge("detect", "summarize")
    graph.add_edge("summarize", "propose")
    graph.add_edge("propose", "approve_gate")
    
    # ========================================
    # CONDITIONAL EDGES (Branching)
    # ========================================
    # After approve_gate, the workflow branches based on the decision
    
    def approval_router(state: AgentState) -> str:
        """
        Route based on approval decision
        
        This function determines the next node based on approval.
        
        Args:
            state: Current agent state
            
        Returns:
            Next node name or END
        """
        if not state.approval:
            logger.warning(
                "No approval found, routing to END",
                extra={"batch_id": state.batch_id}
            )
            return "END"
        
        decision = state.approval.get("decision")
        
        logger.info(
            f"Approval decision: {decision}",
            extra={
                "batch_id": state.batch_id,
                "decision": decision
            }
        )
        
        # Route based on decision
        if decision in ["APPROVE_ALL", "APPROVE_PARTIAL"]:
            return "onchain"
        else:
            # REJECT or unknown
            return "END"
    
    # Add conditional edges from approve_gate
    graph.add_conditional_edges(
        "approve_gate",
        approval_router,
        {
            "onchain": "onchain",
            "END": END
        }
    )
    
    # Continue linear flow after onchain
    graph.add_edge("onchain", "writeback")
    graph.add_edge("writeback", "reconcile")
    graph.add_edge("reconcile", END)
    
    logger.info("Payroll workflow graph created successfully")
    
    return graph


def compile_graph(**kwargs) -> Callable:
    """
    Compile the graph into an executable function
    
    Args:
        **kwargs: Dependencies to inject (passed to create_payroll_graph)
        
    Returns:
        Compiled graph function that can be invoked
        
    Usage:
        app = compile_graph(
            policy=PayrollPolicy(),
            slack_client=slack_app.client,
            ...
        )
        
        # Execute
        result = app.invoke(initial_state)
    """
    graph = create_payroll_graph(**kwargs)
    return graph.compile()


# ========================================
# CONVENIENCE FUNCTIONS
# ========================================

def run_payroll_workflow(
    batch_id: str,
    month: str,
    **kwargs
) -> AgentState:
    """
    Run complete payroll workflow
    
    This is a high-level convenience function that:
    1. Creates initial state
    2. Compiles graph
    3. Executes workflow
    4. Returns final state
    
    Args:
        batch_id: Unique batch identifier
        month: Payroll month (YYYY-MM)
        **kwargs: Dependencies for graph creation
        
    Returns:
        Final agent state after workflow completion
        
    Usage:
        final_state = run_payroll_workflow(
            batch_id="batch_123",
            month="2025-11",
            policy=PayrollPolicy(),
            slack_client=slack_app.client,
            onchain_service=OnchainService(),
            ...
        )
        
        print(final_state.metadata["final_status"])
    """
    logger.info(
        "Starting payroll workflow",
        extra={
            "batch_id": batch_id,
            "month": month
        }
    )
    
    # Create initial state
    initial_state = AgentState(
        batch_id=batch_id,
        month=month,
        lines=[],
        approval=None,
        tx_hashes=[],
        errors=[],
        metadata={}
    )
    
    # Compile graph
    app = compile_graph(**kwargs)
    
    # Execute workflow
    try:
        final_state = app.invoke(initial_state)
        
        logger.info(
            "Payroll workflow completed",
            extra={
                "batch_id": batch_id,
                "final_status": final_state.metadata.get("final_status"),
                "tx_count": len(final_state.tx_hashes),
                "error_count": len(final_state.errors)
            }
        )
        
        return final_state
    
    except Exception as e:
        logger.error(
            "Payroll workflow failed",
            extra={
                "batch_id": batch_id,
                "error": str(e)
            },
            exc_info=True
        )
        raise


# ========================================
# EXAMPLE USAGE
# ========================================

if __name__ == "__main__":
    """
    Example of how to run the workflow
    
    This is for testing and demonstration.
    In production, this would be triggered by the FastAPI endpoint.
    """
    
    # Create a simple test workflow without external dependencies
    final_state = run_payroll_workflow(
        batch_id="test_batch_001",
        month="2025-11",
        policy=PayrollPolicy(),
        # Other services are None (nodes will handle gracefully)
    )
    
    print("\n" + "="*50)
    print("WORKFLOW COMPLETED")
    print("="*50)
    print(f"Batch ID: {final_state.batch_id}")
    print(f"Month: {final_state.month}")
    print(f"Lines processed: {len(final_state.lines)}")
    print(f"Transactions: {len(final_state.tx_hashes)}")
    print(f"Errors: {len(final_state.errors)}")
    print(f"Final status: {final_state.metadata.get('final_status', 'unknown')}")
    print("="*50 + "\n")

