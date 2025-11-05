# """
# On-chain Node

# This node executes blockchain transactions to pay employees.

# Responsibilities:
# - Split payroll lines into chunks (gas limit safety)
# - Convert amounts to smallest units
# - Call PayrollVault.batchPayout() for each chunk
# - Wait for transaction confirmation
# - Store transaction hashes
# - Handle failures gracefully

# The PayrollVault smart contract handles the actual USDC transfers.
# """

# from typing import List
# from decimal import Decimal

# from app.db.schema import AgentState, PayrollLineDTO
# from app.agent.policies import PayrollPolicy
# from app.core.logging import get_logger

# logger = get_logger(__name__)


# def run(
#     state: AgentState,
#     onchain_service=None,
#     policy: PayrollPolicy = None
# ) -> AgentState:
#     """
#     Execute blockchain payments
    
#     Args:
#         state: Current agent state (must have approval)
#         onchain_service: Web3 service (injected dependency)
#         policy: Payroll policy (for chunking and conversion)
        
#     Returns:
#         Updated state with transaction hashes
        
#     Example:
#         state = AgentState(
#             batch_id="batch_123",
#             month="2025-11",
#             lines=[...5 employees...],
#             approval={"decision": "APPROVE_ALL"}
#         )
        
#         new_state = run(state, onchain_service)
        
#         print(new_state.tx_hashes)
#         # ["0xabc123...", "0xdef456..."]
#         # If 5 employees with batch_size=50, only 1 transaction needed
#     """
#     if policy is None:
#         policy = PayrollPolicy()
    
#     # Check approval
#     if not state.approval or state.approval.get("decision") in ["REJECT", "PENDING"]:
#         logger.error(
#             "Cannot execute onchain without approval",
#             extra={
#                 "batch_id": state.batch_id,
#                 "approval": state.approval
#             }
#         )
        
#         new_state = state.model_copy(
#             update={
#                 "errors": state.errors + ["Onchain execution requires approval"]
#             }
#         )
#         return new_state
    
#     logger.info(
#         "Starting blockchain transactions",
#         extra={
#             "batch_id": state.batch_id,
#             "line_count": len(state.lines)
#         }
#     )
    
#     # ========================================
#     # CHUNK PAYROLL LINES
#     # ========================================
#     # Split into smaller groups to avoid gas limits
#     chunks = policy.chunk_by_size(state.lines, policy.batch_size)
    
#     logger.info(
#         "Payroll lines chunked",
#         extra={
#             "batch_id": state.batch_id,
#             "total_lines": len(state.lines),
#             "num_chunks": len(chunks),
#             "chunk_size": policy.batch_size
#         }
#     )
    
#     # ========================================
#     # EXECUTE TRANSACTIONS
#     # ========================================
#     tx_hashes: List[str] = []
#     errors: List[str] = list(state.errors)
    
#     for chunk_idx, chunk in enumerate(chunks):
#         try:
#             # Extract recipients and amounts
#             recipients = [line.wallet for line in chunk]
            
#             # Convert amounts to smallest units (blockchain integers)
#             amounts = [
#                 policy.to_smallest_unit(line.amount_usdc)
#                 for line in chunk
#             ]
            
#             logger.info(
#                 f"Processing chunk {chunk_idx + 1}/{len(chunks)}",
#                 extra={
#                     "batch_id": state.batch_id,
#                     "chunk_size": len(chunk),
#                     "total_amount": str(sum(line.amount_usdc for line in chunk))
#                 }
#             )
            
#             # ----------------------------------------
#             # SEND TRANSACTION
#             # ----------------------------------------
#             if onchain_service:
#                 # Call Web3 service to execute transaction
#                 # See app/onchain/service.py for implementation
#                 tx_hash = onchain_service.batch_payout(
#                     recipients=recipients,
#                     amounts=amounts,
#                     batch_id=state.batch_id,
#                     metadata=f"{state.month} payroll chunk {chunk_idx + 1}"
#                 )
                
#                 tx_hashes.append(tx_hash)
                
#                 logger.info(
#                     "Transaction submitted",
#                     extra={
#                         "batch_id": state.batch_id,
#                         "chunk": chunk_idx + 1,
#                         "tx_hash": tx_hash,
#                         "recipient_count": len(recipients)
#                     }
#                 )
                
#             else:
#                 # No onchain service (testing mode)
#                 logger.warning(
#                     "No onchain service provided, skipping transaction",
#                     extra={
#                         "batch_id": state.batch_id,
#                         "chunk": chunk_idx + 1
#                     }
#                 )
                
#                 # Use a fake transaction hash for testing
#                 fake_tx_hash = f"0x{'0' * 64}"
#                 tx_hashes.append(fake_tx_hash)
        
#         except Exception as e:
#             error_msg = f"Chunk {chunk_idx + 1} transaction failed: {str(e)}"
#             errors.append(error_msg)
            
#             logger.error(
#                 "Transaction failed",
#                 extra={
#                     "batch_id": state.batch_id,
#                     "chunk": chunk_idx + 1,
#                     "error": str(e)
#                 },
#                 exc_info=True
#             )
            
#             # Decide whether to continue or abort
#             # For now, we continue with remaining chunks
#             # In production, you might want to abort on first failure
    
#     # ========================================
#     # LOG RESULTS
#     # ========================================
#     logger.info(
#         "Blockchain transactions completed",
#         extra={
#             "batch_id": state.batch_id,
#             "successful_transactions": len(tx_hashes),
#             "failed_transactions": len(errors) - len(state.errors),
#             "tx_hashes": tx_hashes
#         }
#     )
    
#     # ========================================
#     # UPDATE STATE
#     # ========================================
#     new_state = state.model_copy(
#         update={
#             "tx_hashes": tx_hashes,
#             "errors": errors,
#             "metadata": {
#                 **state.metadata,
#                 "onchain_complete": True,
#                 "transaction_count": len(tx_hashes)
#             }
#         }
#     )
    
#     return new_state


# def prepare_batch_payout_params(
#     chunk: List[PayrollLineDTO],
#     batch_id: str,
#     metadata: str,
#     policy: PayrollPolicy
# ) -> dict:
#     """
#     Prepare parameters for PayrollVault.batchPayout() call
    
#     Contract signature:
#         function batchPayout(
#             address[] calldata recipients,
#             uint256[] calldata amounts,
#             bytes32 batchId,
#             string calldata meta
#         )
    
#     Args:
#         chunk: List of payroll lines to pay
#         batch_id: Batch identifier
#         metadata: Additional metadata string
#         policy: Payroll policy for amount conversion
        
#     Returns:
#         Dictionary of parameters ready for Web3 call
        
#     Example:
#         params = prepare_batch_payout_params(
#             chunk=[line1, line2],
#             batch_id="batch_123",
#             metadata="November 2025 payroll",
#             policy=policy
#         )
        
#         print(params)
#         # {
#         #     "recipients": ["0x1111...", "0x2222..."],
#         #     "amounts": [5000000000, 6000000000],
#         #     "batchId": "0x6261746368...",  # bytes32
#         #     "meta": "November 2025 payroll"
#         # }
#     """
#     # Extract wallet addresses
#     recipients = [line.wallet for line in chunk]
    
#     # Convert amounts to smallest units
#     amounts = [
#         policy.to_smallest_unit(line.amount_usdc)
#         for line in chunk
#     ]
    
#     # Convert batch_id to bytes32 format
#     # Solidity bytes32 = 32 bytes
#     # We'll use the first 32 chars of batch_id, padded with zeros
#     batch_id_bytes = batch_id.encode('utf-8')[:32].ljust(32, b'\x00')
    
#     return {
#         "recipients": recipients,
#         "amounts": amounts,
#         "batchId": batch_id_bytes,
#         "meta": metadata
#     }

"""Mock version of onchain node for local development.

This node replaces the actual Web3 on-chain payout logic
to prevent connection errors when no blockchain RPC is set up.
It simply logs a fake transaction hash to continue the workflow.
"""
"""Mock version of onchain node for local development.

This replaces the actual blockchain payout logic
to allow the LangGraph workflow to complete
without connecting to any Arc Testnet RPC.
"""

from typing import Any
from app.db.schema import AgentState


def run(state: AgentState, *args: Any, **kwargs: Any) -> AgentState:
  """Skip blockchain step in development mode.

  This mock node simply appends a fake transaction hash
  and prints a message to confirm the onchain stage was reached.

  Args:
      state (AgentState): Current state of the LangGraph workflow.
      *args: Placeholder for extra dependencies.
      **kwargs: Additional optional keyword arguments.

  Returns:
      AgentState: The updated state containing mock tx_hashes.
  """
  print("[Mock Onchain] Skipping blockchain interaction.")
  mock_tx_hashes = ["0xFAKE1234567890abcdef"]
  return state.model_copy(update={"tx_hashes": mock_tx_hashes})
