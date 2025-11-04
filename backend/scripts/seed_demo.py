"""
Demo data seeding script
Fill demo data for testing environment
"""
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from decimal import Decimal
from app.db.connection import get_session
from app.db.models import Batch, PayrollLine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_demo_data():
    """
    Create demo data
    Includes a test batch and several payroll records
    """
    logger.info("Starting demo data seeding...")
    
    session = next(get_session())
    
    try:
        # Create demo batch
        batch = Batch(
            batch_id="demo-2025-11",
            month="2025-11",
            status="DRAFT",
            total_amount=Decimal("15000.00"),
            line_count=3
        )
        session.add(batch)
        session.flush()
        
        # Create demo payroll records
        lines = [
            PayrollLine(
                batch_id="demo-2025-11",
                employee_id="EMP001",
                wallet="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1",
                amount_usdc=Decimal("5000.00"),
                flags=[]
            ),
            PayrollLine(
                batch_id="demo-2025-11",
                employee_id="EMP002",
                wallet="0x5555763613a12D8F3e73be831DFf8598089d3dCa",
                amount_usdc=Decimal("6000.00"),
                flags=["high_performer"]
            ),
            PayrollLine(
                batch_id="demo-2025-11",
                employee_id="EMP003",
                wallet="0x1234567890123456789012345678901234567890",
                amount_usdc=Decimal("4000.00"),
                flags=["anomaly_detected"]
            ),
        ]
        
        for line in lines:
            session.add(line)
        
        session.commit()
        logger.info("Demo data seeded successfully!")
        logger.info(f"Created batch: {batch.batch_id}")
        logger.info(f"Created {len(lines)} payroll lines")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error seeding demo data: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_demo_data()
