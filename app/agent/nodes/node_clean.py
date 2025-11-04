"""
Clean Node

This node validates and cleans payroll data.

Responsibilities:
- Validate wallet addresses
- Remove duplicates
- Filter invalid entries
- Normalize data format
- Add validation errors to state.errors

Why clean data?
- Prevents failed blockchain transactions
- Ensures data quality
- Catches errors early
- Saves gas costs
"""

from typing import List, Set
from decimal import Decimal

from app.db.schema import AgentState, PayrollLineDTO
from app.agent.policies import PayrollPolicy
from app.core.logging import get_logger

logger = get_logger(__name__)


def run(state: AgentState, policy: PayrollPolicy = None) -> AgentState:
    """
    Clean and validate payroll data
    
    Args:
        state: Current agent state
        policy: Payroll policy (injected dependency)
        
    Returns:
        Updated state with cleaned lines
        
    Example:
        state = AgentState(
            batch_id="batch_123",
            month="2025-11",
            lines=[line1, line2_duplicate, line3_invalid]
        )
        
        new_state = run(state)
        # Duplicates removed, invalid filtered out
        print(len(new_state.lines))  # 2 (duplicate and invalid removed)
        print(new_state.errors)  # ["Duplicate wallet: 0x...", "Invalid wallet: 0x..."]
    """
    if policy is None:
        policy = PayrollPolicy()
    
    logger.info(
        "Starting data cleaning",
        extra={
            "batch_id": state.batch_id,
            "initial_line_count": len(state.lines)
        }
    )
    
    cleaned_lines: List[PayrollLineDTO] = []
    errors: List[str] = list(state.errors)  # Copy existing errors
    
    # Track seen wallets to detect duplicates
    seen_wallets: Set[str] = set()
    
    # ========================================
    # VALIDATE AND CLEAN EACH LINE
    # ========================================
    for idx, line in enumerate(state.lines):
        line_errors: List[str] = []
        
        # ----------------------------------------
        # 1. VALIDATE WALLET ADDRESS
        # ----------------------------------------
        # Normalize wallet to lowercase for comparison
        wallet_lower = line.wallet.lower()
        
        # Check wallet format
        is_valid_wallet, wallet_error = policy.validate_wallet(wallet_lower)
        if not is_valid_wallet:
            line_errors.append(f"Line {idx}: {wallet_error}")
            logger.warning(
                "Invalid wallet address",
                extra={
                    "batch_id": state.batch_id,
                    "employee_id": line.employee_id,
                    "wallet": line.wallet,
                    "error": wallet_error
                }
            )
        
        # ----------------------------------------
        # 2. CHECK FOR DUPLICATES
        # ----------------------------------------
        # Duplicate wallets could indicate:
        # - Data entry error
        # - Attempted fraud
        # - Multiple roles for same person (valid but needs review)
        if wallet_lower in seen_wallets:
            line_errors.append(
                f"Line {idx}: Duplicate wallet {wallet_lower} "
                f"for employee {line.employee_id}"
            )
            logger.warning(
                "Duplicate wallet detected",
                extra={
                    "batch_id": state.batch_id,
                    "employee_id": line.employee_id,
                    "wallet": wallet_lower
                }
            )
        else:
            seen_wallets.add(wallet_lower)
        
        # ----------------------------------------
        # 3. VALIDATE EMPLOYEE ID
        # ----------------------------------------
        # Employee ID should not be empty
        if not line.employee_id or not line.employee_id.strip():
            line_errors.append(f"Line {idx}: Empty employee_id")
            logger.warning(
                "Empty employee_id",
                extra={
                    "batch_id": state.batch_id,
                    "wallet": wallet_lower
                }
            )
        
        # ----------------------------------------
        # 4. NORMALIZE DATA
        # ----------------------------------------
        # If line is valid, normalize and add to cleaned list
        if not line_errors:
            # Normalize wallet to lowercase
            normalized_line = line.model_copy(
                update={"wallet": wallet_lower}
            )
            cleaned_lines.append(normalized_line)
        else:
            # Add all errors for this line
            errors.extend(line_errors)
    
    # ========================================
    # LOG RESULTS
    # ========================================
    removed_count = len(state.lines) - len(cleaned_lines)
    
    logger.info(
        "Data cleaning completed",
        extra={
            "batch_id": state.batch_id,
            "initial_count": len(state.lines),
            "cleaned_count": len(cleaned_lines),
            "removed_count": removed_count,
            "error_count": len(errors) - len(state.errors)
        }
    )
    
    # If all lines were removed, add a critical error
    if len(cleaned_lines) == 0 and len(state.lines) > 0:
        errors.append("CRITICAL: All payroll lines were invalid and removed")
        logger.error(
            "All payroll lines invalid",
            extra={"batch_id": state.batch_id}
        )
    
    # ========================================
    # UPDATE STATE
    # ========================================
    new_state = state.model_copy(
        update={
            "lines": cleaned_lines,
            "errors": errors
        }
    )
    
    return new_state


def deduplicate_by_wallet(lines: List[PayrollLineDTO]) -> List[PayrollLineDTO]:
    """
    Remove duplicate wallet addresses, keeping first occurrence
    
    Args:
        lines: List of payroll lines
        
    Returns:
        Deduplicated list
        
    Example:
        lines = [
            PayrollLineDTO(employee_id="emp_1", wallet="0x1111...", ...),
            PayrollLineDTO(employee_id="emp_2", wallet="0x2222...", ...),
            PayrollLineDTO(employee_id="emp_3", wallet="0x1111...", ...),  # Duplicate
        ]
        
        deduplicated = deduplicate_by_wallet(lines)
        print(len(deduplicated))  # 2
    """
    seen: Set[str] = set()
    result: List[PayrollLineDTO] = []
    
    for line in lines:
        wallet_lower = line.wallet.lower()
        if wallet_lower not in seen:
            seen.add(wallet_lower)
            result.append(line)
    
    return result


def filter_zero_amounts(lines: List[PayrollLineDTO]) -> List[PayrollLineDTO]:
    """
    Remove lines with zero or negative amounts
    
    This is typically called after the compute node.
    
    Args:
        lines: List of payroll lines
        
    Returns:
        Filtered list
    """
    return [
        line for line in lines
        if line.amount_usdc > Decimal("0")
    ]

