"""
Policies Module

This module defines business rules and policies for payroll processing.
It centralizes all configuration and business logic in one place.

Why centralize policies?
- Easy to update rules without changing code
- Can be loaded from database or config files
- Testable and auditable
- Clear separation of business logic from implementation

Components:
- PayrollPolicy: Main policy class
- Salary computation rules
- Anomaly detection thresholds
- Batch chunking logic
- Amount conversion utilities
"""

from decimal import Decimal
from typing import List, Dict, Any
from app.db.schema import PayrollLineDTO
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class PayrollPolicy:
    """
    Payroll Business Rules and Policies
    
    This class encapsulates all business logic for payroll processing.
    
    Attributes:
        batch_size: Maximum recipients per blockchain transaction
        usdc_decimals: USDC token decimal places
        anomaly_threshold: Threshold for flagging anomalies
        min_amount: Minimum payroll amount
        max_amount: Maximum payroll amount per employee
    
    Usage:
        policy = PayrollPolicy()
        
        # Convert human amount to blockchain integer
        amount_int = policy.to_smallest_unit(Decimal("100.50"))
        
        # Split payroll lines into chunks
        chunks = policy.chunk_by_size(lines, policy.batch_size)
    """
    
    def __init__(self):
        """
        Initialize policy with settings from configuration
        """
        # Load settings
        settings = get_settings()
        
        # ========================================
        # BATCH CONFIGURATION
        # ========================================
        # batch_size: Maximum recipients per transaction
        # Why limit? Larger batches risk gas limits and failure
        # Smaller batches are more reliable but cost more gas
        self.batch_size: int = settings.batch_size
        
        # ========================================
        # USDC CONFIGURATION
        # ========================================
        # usdc_decimals: Number of decimal places
        # Standard USDC = 6 decimals
        # 1 USDC = 1,000,000 smallest units
        self.usdc_decimals: int = settings.usdc_decimals
        
        # Calculate the multiplier for conversions
        # Example: decimals=6 → multiplier=1,000,000
        self.usdc_multiplier: int = 10 ** self.usdc_decimals
        
        # ========================================
        # ANOMALY DETECTION
        # ========================================
        # anomaly_threshold: Sensitivity (0.0 to 1.0)
        # Higher = more strict (more items flagged)
        self.anomaly_threshold: float = settings.anomaly_threshold
        
        # ========================================
        # AMOUNT LIMITS
        # ========================================
        # min_amount: Minimum payroll per employee
        # Prevents dust transactions
        self.min_amount: Decimal = Decimal("0.01")
        
        # max_amount: Maximum payroll per employee
        # Prevents data entry errors
        self.max_amount: Decimal = Decimal("1000000.00")
        
        # ========================================
        # APPROVAL TIMEOUT
        # ========================================
        # How long to wait for human approval (minutes)
        self.approval_timeout_minutes: int = settings.approval_timeout_minutes
        
        logger.info(
            "PayrollPolicy initialized",
            extra={
                "batch_size": self.batch_size,
                "usdc_decimals": self.usdc_decimals,
                "anomaly_threshold": self.anomaly_threshold
            }
        )
    
    # ========================================
    # AMOUNT CONVERSION
    # ========================================
    def to_smallest_unit(self, amount: Decimal) -> int:
        """
        Convert USDC amount to smallest unit (for blockchain)
        
        Blockchain contracts work with integers, not decimals.
        We need to convert human-readable amounts to smallest units.
        
        Args:
            amount: Human-readable USDC amount
            
        Returns:
            Integer amount in smallest units
            
        Example:
            policy = PayrollPolicy(usdc_decimals=6)
            
            # Convert 100.50 USDC to smallest units
            amount_int = policy.to_smallest_unit(Decimal("100.50"))
            print(amount_int)  # 100500000
            
            # How it works:
            # 100.50 * 10^6 = 100.50 * 1,000,000 = 100,500,000
        """
        # Multiply by 10^decimals and convert to int
        return int(amount * self.usdc_multiplier)
    
    def from_smallest_unit(self, amount_int: int) -> Decimal:
        """
        Convert smallest unit to human-readable USDC amount
        
        This is the reverse of to_smallest_unit().
        Used when reading amounts from blockchain.
        
        Args:
            amount_int: Amount in smallest units
            
        Returns:
            Human-readable USDC amount
            
        Example:
            policy = PayrollPolicy(usdc_decimals=6)
            
            # Convert 100500000 smallest units to USDC
            amount = policy.from_smallest_unit(100500000)
            print(amount)  # Decimal("100.50")
            
            # How it works:
            # 100500000 / 10^6 = 100500000 / 1,000,000 = 100.50
        """
        # Divide by 10^decimals
        return Decimal(amount_int) / Decimal(self.usdc_multiplier)
    
    # ========================================
    # VALIDATION
    # ========================================
    def validate_amount(self, amount: Decimal) -> tuple[bool, str]:
        """
        Validate payroll amount is within acceptable range
        
        Args:
            amount: Payroll amount to validate
            
        Returns:
            Tuple of (is_valid, error_message)
            
        Example:
            policy = PayrollPolicy()
            
            valid, error = policy.validate_amount(Decimal("5000.00"))
            if not valid:
                print(f"Invalid amount: {error}")
        """
        # Check minimum
        if amount < self.min_amount:
            return False, f"Amount {amount} is below minimum {self.min_amount}"
        
        # Check maximum
        if amount > self.max_amount:
            return False, f"Amount {amount} exceeds maximum {self.max_amount}"
        
        return True, ""
    
    def validate_wallet(self, wallet: str) -> tuple[bool, str]:
        """
        Validate wallet address format
        
        Args:
            wallet: Ethereum wallet address
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check 0x prefix
        if not wallet.startswith("0x"):
            return False, "Wallet must start with 0x"
        
        # Check length
        if len(wallet) != 42:
            return False, "Wallet must be 42 characters (0x + 40 hex)"
        
        # Check hex format
        try:
            int(wallet, 16)
        except ValueError:
            return False, "Wallet must contain only hex characters"
        
        return True, ""
    
    # ========================================
    # BATCH CHUNKING
    # ========================================
    def chunk_by_size(
        self,
        lines: List[PayrollLineDTO],
        chunk_size: int
    ) -> List[List[PayrollLineDTO]]:
        """
        Split payroll lines into chunks for batching
        
        Why chunk?
        - Blockchain transactions have gas limits
        - Too many recipients in one transaction can fail
        - Smaller chunks are more reliable
        
        Args:
            lines: List of payroll lines to split
            chunk_size: Maximum lines per chunk
            
        Returns:
            List of chunks (each chunk is a list of lines)
            
        Example:
            policy = PayrollPolicy()
            lines = [line1, line2, line3, ..., line150]
            
            # Split into chunks of 50
            chunks = policy.chunk_by_size(lines, 50)
            print(len(chunks))  # 3 chunks
            print(len(chunks[0]))  # 50 lines
            print(len(chunks[1]))  # 50 lines
            print(len(chunks[2]))  # 50 lines
        """
        chunks = []
        
        # Iterate through lines in steps of chunk_size
        for i in range(0, len(lines), chunk_size):
            # Slice from i to i+chunk_size
            chunk = lines[i:i + chunk_size]
            chunks.append(chunk)
        
        logger.info(
            "Chunked payroll lines",
            extra={
                "total_lines": len(lines),
                "chunk_size": chunk_size,
                "num_chunks": len(chunks)
            }
        )
        
        return chunks
    
    # ========================================
    # SALARY COMPUTATION
    # ========================================
    def compute_salary(
        self,
        employee_id: str,
        ruleset: Dict[str, Any]
    ) -> Decimal:
        """
        Compute salary for an employee based on ruleset
        
        Ruleset structure:
        {
            "base": {"emp_001": 5000, "emp_002": 6000},
            "bonus": {"emp_001": 500},
            "deduction": {"emp_002": 100},
            "tax_rate": 0.15
        }
        
        Args:
            employee_id: Employee identifier
            ruleset: Dictionary of salary rules
            
        Returns:
            Computed salary amount
            
        Example:
            policy = PayrollPolicy()
            
            ruleset = {
                "base": {"emp_123": 5000},
                "bonus": {"emp_123": 500},
                "deduction": {"emp_123": 50},
            }
            
            salary = policy.compute_salary("emp_123", ruleset)
            print(salary)  # Decimal("5450.00")
            
            # Calculation:
            # Base: 5000
            # + Bonus: 500
            # - Deduction: 50
            # = 5450
        """
        # Get base salary (required)
        base = Decimal(str(ruleset.get("base", {}).get(employee_id, 0)))
        
        # Get bonus (optional)
        bonus = Decimal(str(ruleset.get("bonus", {}).get(employee_id, 0)))
        
        # Get deductions (optional)
        deduction = Decimal(str(ruleset.get("deduction", {}).get(employee_id, 0)))
        
        # Calculate gross salary
        gross = base + bonus - deduction
        
        # Apply tax rate if specified
        tax_rate = Decimal(str(ruleset.get("tax_rate", 0)))
        if tax_rate > 0:
            tax = gross * tax_rate
            net = gross - tax
        else:
            net = gross
        
        return net
    
    # ========================================
    # ANOMALY DETECTION HELPERS
    # ========================================
    def should_flag_high_amount(
        self,
        amount: Decimal,
        historical_avg: Decimal,
        threshold_multiplier: float = 2.0
    ) -> bool:
        """
        Check if amount is unusually high compared to history
        
        Args:
            amount: Current amount to check
            historical_avg: Historical average for this employee
            threshold_multiplier: How many times higher triggers flag
            
        Returns:
            True if should be flagged
            
        Example:
            policy = PayrollPolicy()
            
            # Employee usually gets 5000, this month is 12000
            should_flag = policy.should_flag_high_amount(
                amount=Decimal("12000"),
                historical_avg=Decimal("5000"),
                threshold_multiplier=2.0
            )
            print(should_flag)  # True (12000 > 5000 * 2)
        """
        if historical_avg == 0:
            return False
        
        return amount > (historical_avg * Decimal(str(threshold_multiplier)))
    
    def should_flag_first_time(
        self,
        employee_id: str,
        historical_employees: List[str]
    ) -> bool:
        """
        Check if this is a first-time recipient
        
        Args:
            employee_id: Employee to check
            historical_employees: List of employees from past batches
            
        Returns:
            True if first-time recipient
        """
        return employee_id not in historical_employees

