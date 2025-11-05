"""Mock Onchain Service for local dev mode.

Used to skip real blockchain interaction during development.
"""

import uuid


class MockOnchainService:
    """Simulates on-chain batch payout logic without any RPC calls."""

    def __init__(self):
        print("[MockOnchainService] Initialized (no blockchain connection).")

    def batch_payout(self, recipients, amounts, batch_id, meta):
        """Simulate a payout and return a fake tx hash."""
        fake_tx = f"0x{uuid.uuid4().hex[:64]}"
        print(f"[MockOnchainService] Pretending to send payout for batch={batch_id} "
              f"to {len(recipients)} recipients. Fake tx={fake_tx}")
        return fake_tx
