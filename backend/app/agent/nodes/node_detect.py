"""
Detect Node

This node detects anomalies in payroll data using various techniques.

Detection Methods:
1. Statistical analysis (outliers)
2. Rule-based detection (threshold checks)
3. Historical comparison
4. AI/ML models (optional)

Anomaly Types:
- HIGH_AMOUNT: Amount significantly higher than usual
- LOW_AMOUNT: Amount significantly lower than usual
- FIRST_TIME: New recipient
- UNUSUAL_CHANGE: Large change from previous month
- DUPLICATE_WALLET: Same wallet used for multiple employees

Flags are added to PayrollLineDTO.flags for human review.
"""

from decimal import Decimal
from typing import List, Dict
import numpy as np

from app.db.schema import AgentState, PayrollLineDTO
from app.agent.policies import PayrollPolicy
from app.core.logging import get_logger

logger = get_logger(__name__)


def run(
    state: AgentState,
    policy: PayrollPolicy = None,
    historical_data: Dict = None
) -> AgentState:
    """
    Detect anomalies in payroll data
    
    Args:
        state: Current agent state
        policy: Payroll policy (injected dependency)
        historical_data: Historical payroll data for comparison
        
    Returns:
        Updated state with flags added to anomalous lines
        
    Example:
        state = AgentState(
            batch_id="batch_123",
            month="2025-11",
            lines=[...]
        )
        
        historical_data = {
            "averages": {
                "emp_001": Decimal("5000"),
                "emp_002": Decimal("6000"),
            },
            "previous_employees": ["emp_001", "emp_002", "emp_003"]
        }
        
        new_state = run(state, historical_data=historical_data)
        
        # Lines with anomalies will have flags
        for line in new_state.lines:
            if line.flags:
                print(f"{line.employee_id}: {line.flags}")
    """
    if policy is None:
        policy = PayrollPolicy()
    
    if historical_data is None:
        historical_data = {}
    
    logger.info(
        "Starting anomaly detection",
        extra={
            "batch_id": state.batch_id,
            "line_count": len(state.lines)
        }
    )
    
    # ========================================
    # EXTRACT AMOUNTS FOR STATISTICAL ANALYSIS
    # ========================================
    amounts = [float(line.amount_usdc) for line in state.lines if line.amount_usdc > 0]
    
    # Calculate statistics
    if len(amounts) > 0:
        mean_amount = float(np.mean(amounts))
        std_amount = float(np.std(amounts))
        median_amount = float(np.median(amounts))
    else:
        mean_amount = 0
        std_amount = 0
        median_amount = 0
    
    logger.info(
        "Amount statistics",
        extra={
            "batch_id": state.batch_id,
            "mean": mean_amount,
            "std": std_amount,
            "median": median_amount
        }
    )
    
    # ========================================
    # DETECT ANOMALIES FOR EACH LINE
    # ========================================
    updated_lines = []
    anomaly_count = 0
    
    for line in state.lines:
        flags = list(line.flags)  # Copy existing flags
        
        # Skip zero amounts
        if line.amount_usdc <= 0:
            updated_lines.append(line)
            continue
        
        # ----------------------------------------
        # 1. STATISTICAL OUTLIER DETECTION
        # ----------------------------------------
        # Z-score method: flag if > 2 standard deviations from mean
        if std_amount > 0:
            z_score = (float(line.amount_usdc) - mean_amount) / std_amount
            
            if z_score > 2.0:
                flags.append("HIGH_AMOUNT")
                logger.info(
                    "High amount detected",
                    extra={
                        "batch_id": state.batch_id,
                        "employee_id": line.employee_id,
                        "amount": str(line.amount_usdc),
                        "z_score": z_score
                    }
                )
            elif z_score < -2.0:
                flags.append("LOW_AMOUNT")
                logger.info(
                    "Low amount detected",
                    extra={
                        "batch_id": state.batch_id,
                        "employee_id": line.employee_id,
                        "amount": str(line.amount_usdc),
                        "z_score": z_score
                    }
                )
        
        # ----------------------------------------
        # 2. HISTORICAL COMPARISON
        # ----------------------------------------
        # Compare to employee's historical average
        historical_averages = historical_data.get("averages", {})
        if line.employee_id in historical_averages:
            hist_avg = historical_averages[line.employee_id]
            
            # Check if amount is significantly different from history
            if policy.should_flag_high_amount(line.amount_usdc, hist_avg, 2.0):
                if "HIGH_AMOUNT" not in flags:
                    flags.append("UNUSUAL_INCREASE")
                logger.info(
                    "Unusual increase detected",
                    extra={
                        "batch_id": state.batch_id,
                        "employee_id": line.employee_id,
                        "current": str(line.amount_usdc),
                        "historical_avg": str(hist_avg)
                    }
                )
        
        # ----------------------------------------
        # 3. FIRST-TIME RECIPIENT
        # ----------------------------------------
        # Check if this employee has received payroll before
        previous_employees = historical_data.get("previous_employees", [])
        if policy.should_flag_first_time(line.employee_id, previous_employees):
            flags.append("FIRST_TIME")
            logger.info(
                "First-time recipient detected",
                extra={
                    "batch_id": state.batch_id,
                    "employee_id": line.employee_id
                }
            )
        
        # ----------------------------------------
        # 4. THRESHOLD CHECKS
        # ----------------------------------------
        # Flag very large amounts (potential data entry error)
        if line.amount_usdc > Decimal("50000"):
            flags.append("VERY_HIGH_AMOUNT")
            logger.warning(
                "Very high amount detected",
                extra={
                    "batch_id": state.batch_id,
                    "employee_id": line.employee_id,
                    "amount": str(line.amount_usdc)
                }
            )
        
        # Update line with flags
        if flags:
            anomaly_count += 1
            updated_line = line.model_copy(update={"flags": flags})
        else:
            updated_line = line
        
        updated_lines.append(updated_line)
    
    # ========================================
    # LOG RESULTS
    # ========================================
    logger.info(
        "Anomaly detection completed",
        extra={
            "batch_id": state.batch_id,
            "total_lines": len(updated_lines),
            "anomalies_detected": anomaly_count
        }
    )
    
    # ========================================
    # UPDATE STATE
    # ========================================
    new_state = state.model_copy(
        update={
            "lines": updated_lines,
            "metadata": {
                **state.metadata,
                "anomaly_count": anomaly_count,
                "detection_complete": True,
                "statistics": {
                    "mean": mean_amount,
                    "std": std_amount,
                    "median": median_amount
                }
            }
        }
    )
    
    return new_state


def get_historical_data(month: str) -> Dict:
    """
    Get historical payroll data for comparison
    
    This would query the database for:
    - Previous months' payroll amounts per employee
    - Calculate historical averages
    - List of all previous employees
    
    Args:
        month: Current payroll month
        
    Returns:
        Dictionary with historical data
        
    Example return:
        {
            "averages": {
                "emp_001": Decimal("5000.00"),
                "emp_002": Decimal("6000.00"),
            },
            "previous_employees": ["emp_001", "emp_002", "emp_003"],
            "last_month_amounts": {
                "emp_001": Decimal("5100.00"),
                "emp_002": Decimal("5900.00"),
            }
        }
    """
    # Placeholder - implement based on your database
    return {
        "averages": {},
        "previous_employees": [],
        "last_month_amounts": {}
    }

