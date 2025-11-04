"""
Compute Node

This node computes payroll amounts based on business rules.

Responsibilities:
- Calculate salary for each employee
- Apply bonuses and deductions
- Apply tax rules
- Update amount_usdc field in each PayrollLineDTO

Business Rules:
- Base salary (from employee table or ruleset)
- Performance bonus
- One-time adjustments
- Deductions (advances, etc.)
- Tax withholding
"""

from decimal import Decimal
from typing import Dict, Any

from app.db.schema import AgentState, PayrollLineDTO
from app.agent.policies import PayrollPolicy
from app.core.logging import get_logger

logger = get_logger(__name__)


def run(
    state: AgentState,
    ruleset: Dict[str, Any] = None,
    policy: PayrollPolicy = None
) -> AgentState:
    """
    Compute payroll amounts
    
    Args:
        state: Current agent state
        ruleset: Salary rules dictionary
        policy: Payroll policy (injected dependency)
        
    Returns:
        Updated state with computed amounts
        
    Example ruleset:
        {
            "base": {
                "emp_001": 5000,
                "emp_002": 6000,
                "emp_003": 5500
            },
            "bonus": {
                "emp_001": 500,  # Performance bonus
                "emp_003": 200
            },
            "deduction": {
                "emp_002": 100   # Advance repayment
            },
            "tax_rate": 0.0  # If applicable
        }
    
    Example:
        state = AgentState(
            batch_id="batch_123",
            month="2025-11",
            lines=[
                PayrollLineDTO(employee_id="emp_001", ...),
                PayrollLineDTO(employee_id="emp_002", ...),
            ]
        )
        
        ruleset = {
            "base": {"emp_001": 5000, "emp_002": 6000},
            "bonus": {"emp_001": 500}
        }
        
        new_state = run(state, ruleset)
        print(new_state.lines[0].amount_usdc)  # Decimal("5500")
        print(new_state.lines[1].amount_usdc)  # Decimal("6000")
    """
    if policy is None:
        policy = PayrollPolicy()
    
    if ruleset is None:
        # Default ruleset for demo
        ruleset = get_demo_ruleset()
    
    logger.info(
        "Starting amount computation",
        extra={
            "batch_id": state.batch_id,
            "line_count": len(state.lines)
        }
    )
    
    # ========================================
    # COMPUTE AMOUNT FOR EACH LINE
    # ========================================
    updated_lines = []
    errors = list(state.errors)
    
    for line in state.lines:
        # Compute salary using policy
        try:
            amount = policy.compute_salary(line.employee_id, ruleset)
            
            # Validate amount
            is_valid, error_msg = policy.validate_amount(amount)
            if not is_valid:
                logger.warning(
                    "Invalid computed amount",
                    extra={
                        "batch_id": state.batch_id,
                        "employee_id": line.employee_id,
                        "amount": str(amount),
                        "error": error_msg
                    }
                )
                errors.append(
                    f"Employee {line.employee_id}: {error_msg}"
                )
                # Set to 0 to skip this line
                amount = Decimal("0")
            
            # Update line with computed amount
            updated_line = line.model_copy(
                update={"amount_usdc": amount}
            )
            updated_lines.append(updated_line)
            
            logger.debug(
                "Computed amount for employee",
                extra={
                    "batch_id": state.batch_id,
                    "employee_id": line.employee_id,
                    "amount": str(amount)
                }
            )
            
        except Exception as e:
            logger.error(
                "Error computing amount",
                extra={
                    "batch_id": state.batch_id,
                    "employee_id": line.employee_id,
                    "error": str(e)
                },
                exc_info=True
            )
            errors.append(
                f"Employee {line.employee_id}: Computation error - {str(e)}"
            )
            # Keep line with 0 amount
            updated_lines.append(line)
    
    # ========================================
    # CALCULATE TOTALS
    # ========================================
    total_amount = sum(line.amount_usdc for line in updated_lines)
    
    logger.info(
        "Amount computation completed",
        extra={
            "batch_id": state.batch_id,
            "line_count": len(updated_lines),
            "total_amount": str(total_amount)
        }
    )
    
    # ========================================
    # UPDATE STATE
    # ========================================
    new_state = state.model_copy(
        update={
            "lines": updated_lines,
            "errors": errors,
            "metadata": {
                **state.metadata,
                "total_amount": str(total_amount),
                "computation_complete": True
            }
        }
    )
    
    return new_state


def get_demo_ruleset() -> Dict[str, Any]:
    """
    Get demo salary ruleset
    
    In production, this would come from:
    - Database (employee salary table)
    - HR system API
    - Configuration file
    - Admin UI
    
    Returns:
        Dictionary of salary rules
    """
    return {
        "base": {
            "emp_001": 5000,
            "emp_002": 6000,
            "emp_003": 5500,
            "emp_004": 4800,
            "emp_005": 7000,
        },
        "bonus": {
            "emp_001": 500,   # Good performance
            "emp_003": 200,
            "emp_005": 1000,  # Exceptional performance
        },
        "deduction": {
            "emp_002": 100,   # Advance repayment
        },
        "tax_rate": 0.0,  # No tax for demo (handle externally)
    }


def load_ruleset_from_database(month: str) -> Dict[str, Any]:
    """
    Load salary ruleset from database
    
    This is a placeholder for production implementation.
    
    Example query:
        SELECT 
            employee_id,
            base_salary,
            bonus_amount,
            deduction_amount
        FROM employee_salaries
        WHERE effective_month = :month
    
    Args:
        month: Payroll month (YYYY-MM)
        
    Returns:
        Ruleset dictionary
    """
    # Placeholder
    raise NotImplementedError("Implement database loading logic")

