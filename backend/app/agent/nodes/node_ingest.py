"""
Ingest Node

This node ingests payroll data from various sources.
It's the entry point of the LangGraph workflow.

Responsibilities:
- Load employee data from database or CSV
- Create initial PayrollLineDTO objects
- Add to AgentState

Data Sources (examples):
- PostgreSQL database (employee master table)
- CSV file upload
- REST API from HR system
- Google Sheets via API
"""

from typing import List
import uuid
from decimal import Decimal

from app.db.schema import AgentState, PayrollLineDTO
from app.core.logging import get_logger

logger = get_logger(__name__)


def run(state: AgentState) -> AgentState:
    """
    Ingest payroll data
    
    This is a simplified implementation that creates demo data.
    In production, you would:
    - Query employee database
    - Load from CSV file
    - Call HR system API
    - etc.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with lines populated
        
    Example:
        state = AgentState(
            batch_id="batch_123",
            month="2025-11",
            lines=[]
        )
        
        new_state = run(state)
        print(len(new_state.lines))  # e.g., 10 employees
    """
    try:
        logger.info(
            "Starting data ingestion",
            extra={
                "batch_id": state.batch_id,
                "month": state.month
            }
        )
        
        # ========================================
        # DEMO DATA
        # ========================================
        # In production, replace this with actual data loading
        # Example: lines = load_from_database(state.month)
        
        # Use Hardhat's default test accounts for local testing
        # These addresses have ETH funded by default in local Hardhat node
        demo_employees = [
            {
                "employee_id": "emp_001",
                "wallet": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",  # Hardhat Account #1
                "name": "Alice Smith"
            },
            {
                "employee_id": "emp_002",
                "wallet": "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",  # Hardhat Account #2
                "name": "Bob Johnson"
            },
            {
                "employee_id": "emp_003",
                "wallet": "0x90F79bf6EB2c4f870365E785982E1f101E93b906",  # Hardhat Account #3
                "name": "Carol Williams"
            },
            {
                "employee_id": "emp_004",
                "wallet": "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65",  # Hardhat Account #4
                "name": "David Brown"
            },
            {
                "employee_id": "emp_005",
                "wallet": "0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc",  # Hardhat Account #5
                "name": "Eve Davis"
            },
        ]
        
        # Create PayrollLineDTO objects
        # amount_usdc is initially 0 (will be computed in compute node)
        lines: List[PayrollLineDTO] = []
        
        for emp in demo_employees:
            line = PayrollLineDTO(
                employee_id=emp["employee_id"],
                wallet=emp["wallet"],
                amount_usdc=Decimal("0"),  # Will be computed later
                flags=[],
                metadata={"name": emp["name"]}
            )
            lines.append(line)
        
        logger.info(
            "Data ingestion completed",
            extra={
                "batch_id": state.batch_id,
                "line_count": len(lines)
            }
        )
        
        # ========================================
        # UPDATE STATE
        # ========================================
        # Create new state with updated lines
        # state.model_copy() creates a shallow copy with specified fields updated
        new_state = state.model_copy(
            update={"lines": lines}
        )
        
        return new_state
        
    except Exception as e:
        logger.error(
            "[Error in node_ingest]",
            extra={
                "batch_id": state.batch_id,
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        # Return state with error, don't break workflow
        errors = list(state.errors) + [f"ingest: {str(e)}"]
        return state.model_copy(update={"errors": errors})


def load_from_database(month: str) -> List[PayrollLineDTO]:
    """
    Load payroll data from database
    
    This is a placeholder for production implementation.
    You would:
    1. Query employee table
    2. Join with employment records
    3. Filter by active status
    4. Create PayrollLineDTO objects
    
    Args:
        month: Payroll month (YYYY-MM)
        
    Returns:
        List of payroll lines
        
    Example SQL query:
        SELECT 
            e.id as employee_id,
            e.wallet_address as wallet,
            e.base_salary,
            b.bonus_amount,
            d.deduction_amount
        FROM employees e
        LEFT JOIN bonuses b ON e.id = b.employee_id AND b.month = :month
        LEFT JOIN deductions d ON e.id = d.employee_id AND d.month = :month
        WHERE e.status = 'active'
    """
    # Placeholder - implement based on your database schema
    raise NotImplementedError("Implement database loading logic")


def load_from_csv(file_path: str) -> List[PayrollLineDTO]:
    """
    Load payroll data from CSV file
    
    Expected CSV format:
        employee_id,wallet,base_salary,bonus,deduction
        emp_001,0x1111...,5000,500,0
        emp_002,0x2222...,6000,0,100
    
    Args:
        file_path: Path to CSV file
        
    Returns:
        List of payroll lines
        
    Example:
        lines = load_from_csv("payroll_2025_11.csv")
    """
    import pandas as pd
    
    # Read CSV
    df = pd.read_csv(file_path)
    
    # Validate required columns
    required_cols = ["employee_id", "wallet"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Create PayrollLineDTO objects
    lines = []
    for _, row in df.iterrows():
        line = PayrollLineDTO(
            employee_id=row["employee_id"],
            wallet=row["wallet"],
            amount_usdc=Decimal("0"),  # Will be computed
            flags=[],
            metadata=row.to_dict()
        )
        lines.append(line)
    
    logger.info(f"Loaded {len(lines)} lines from CSV: {file_path}")
    return lines

