"""Mock Onchain Service for local dev mode.

Used to skip real blockchain interaction during development.
"""

import uuid


class MockOnchainService:
    """Simulates on-chain batch payout logic without any RPC calls."""

    def __init__(self):
        print("[MockOnchainService] Initialized (no blockchain connection).")

    def batch_payout(self, recipients, amounts, batch_id, metadata):
        """
        Simulate a payout and return a fake tx hash.
        
        Args:
            recipients: List of wallet addresses
            amounts: List of USDC amounts (in smallest units)
            batch_id: Unique batch identifier
            metadata: Additional information string (unused in mock)
            
        Returns:
            Fake transaction hash (hex string starting with 0x)
        """
        fake_tx = f"0x{uuid.uuid4().hex[:64]}"
        print(f"[MockOnchainService] Pretending to send payout for batch={batch_id} "
              f"to {len(recipients)} recipients. Metadata: {metadata}. Fake tx={fake_tx}")
        return fake_tx
