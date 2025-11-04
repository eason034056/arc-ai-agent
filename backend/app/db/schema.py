"""
Pydantic Schemas

This module defines Pydantic models for:
1. Data validation (API requests/responses)
2. LangGraph agent state (immutable state between nodes)
3. DTOs (Data Transfer Objects) between layers

Why Pydantic?
- Runtime type checking and validation
- Automatic JSON serialization/deserialization
- IDE autocomplete and type hints
- Easy conversion to/from dictionaries

Difference from SQLAlchemy Models:
- SQLAlchemy = Database layer (mutable, DB-mapped)
- Pydantic = Application layer (immutable, validation)
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

from app.db.models import BatchStatus, TransactionStatus, ApprovalDecision


# ========================================
# PAYROLL LINE SCHEMAS
# ========================================

class PayrollLineDTO(BaseModel):
    """
    Payroll Line Data Transfer Object
    
    Represents a single employee's payroll entry.
    Used in the LangGraph agent state.
    
    Attributes:
        employee_id: Employee identifier
        wallet: Ethereum wallet address
        amount_usdc: Payroll amount in USDC
        flags: List of anomaly flags (e.g., ["HIGH_AMOUNT"])
        metadata: Additional context data
    
    Example:
        line = PayrollLineDTO(
            employee_id="emp_123",
            wallet="0x1234...5678",
            amount_usdc=Decimal("5000.50"),
            flags=["HIGH_AMOUNT"],
            metadata={"department": "Engineering"}
        )
    """
    
    # employee_id: Unique employee identifier
    # Could be email, employee number, UUID, etc.
    employee_id: str = Field(
        ...,  # Required field
        description="Unique employee identifier"
    )
    
    # wallet: Ethereum/Arc wallet address
    # Must be a valid address (42 characters with 0x prefix)
    wallet: str = Field(
        ...,
        description="Employee wallet address for receiving USDC",
        min_length=42,
        max_length=42
    )
    
    # amount_usdc: Payroll amount
    # Using Decimal for precise currency calculations
    # float has rounding errors!
    amount_usdc: Decimal = Field(
        default=Decimal("0"),
        description="Payroll amount in USDC",
        ge=0  # Greater than or equal to 0
    )
    
    # flags: Anomaly detection flags
    # Empty list = no anomalies detected
    # Examples: ["HIGH_AMOUNT", "FIRST_TIME", "UNUSUAL_CHANGE"]
    flags: List[str] = Field(
        default_factory=list,
        description="Anomaly detection flags"
    )
    
    # metadata: Additional context
    # Flexible dictionary for any extra data
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    
    # ========================================
    # VALIDATORS
    # ========================================
    @field_validator("wallet")
    @classmethod
    def validate_wallet(cls, v: str) -> str:
        """
        Validate wallet address format
        
        Args:
            v: Wallet address string
            
        Returns:
            Validated wallet address (lowercase)
            
        Raises:
            ValueError: If address format is invalid
        """
        # Ensure 0x prefix
        if not v.startswith("0x"):
            raise ValueError("Wallet address must start with 0x")
        
        # Ensure correct length (40 hex chars + 0x = 42 total)
        if len(v) != 42:
            raise ValueError("Wallet address must be 42 characters (0x + 40 hex)")
        
        # Ensure hex characters only
        try:
            int(v, 16)  # Try to parse as hexadecimal
        except ValueError:
            raise ValueError("Wallet address must contain only hexadecimal characters")
        
        # Return lowercase for consistency
        return v.lower()
    
    # Pydantic v2 configuration
    class Config:
        # Allow creating instances from ORM models
        # Example: PayrollLineDTO.from_orm(db_line)
        from_attributes = True
        
        # Use Decimal serialization instead of float
        json_encoders = {
            Decimal: str  # Serialize Decimal as string to preserve precision
        }


# ========================================
# AGENT STATE SCHEMA
# ========================================

class AgentState(BaseModel):
    """
    LangGraph Agent State
    
    This is the state that flows through all nodes in the LangGraph workflow.
    It's immutable - each node returns a new state with updated fields.
    
    Workflow:
        ingest → clean → compute → detect → summarize → 
        propose → approve_gate → onchain → writeback → reconcile
    
    Attributes:
        batch_id: Unique batch identifier
        month: Payroll month (YYYY-MM)
        lines: List of payroll lines
        approval: Approval decision (None until decided)
        tx_hashes: List of blockchain transaction hashes
        errors: List of error messages
        metadata: Additional workflow context
    
    Immutability:
        # DON'T do this (mutates state):
        state.lines.append(new_line)
        
        # DO this (creates new state):
        new_state = state.model_copy(
            update={"lines": state.lines + [new_line]}
        )
    """
    
    # batch_id: Unique identifier for this payroll batch
    # Usually a UUID
    batch_id: str = Field(
        ...,
        description="Unique batch identifier"
    )
    
    # month: Payroll month in YYYY-MM format
    # Example: "2025-11"
    month: str = Field(
        ...,
        description="Payroll month (YYYY-MM format)",
        pattern=r"^\d{4}-\d{2}$"  # Regex: 4 digits, dash, 2 digits
    )
    
    # lines: List of payroll lines (employees)
    # This is the main data being processed
    lines: List[PayrollLineDTO] = Field(
        default_factory=list,
        description="Payroll lines for all employees"
    )
    
    # approval: Approval decision from Slack
    # None until approve_gate node completes
    # Structure: {"decision": "APPROVE_ALL", "selected_ids": [...]}
    approval: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Approval decision from human reviewer"
    )
    
    # tx_hashes: Blockchain transaction hashes
    # Filled by onchain node
    # Multiple hashes if batch is split into chunks
    tx_hashes: List[str] = Field(
        default_factory=list,
        description="Blockchain transaction hashes"
    )
    
    # errors: Error messages collected during workflow
    # Helps with debugging and error reporting
    errors: List[str] = Field(
        default_factory=list,
        description="Error messages from workflow"
    )
    
    # metadata: Additional workflow context
    # Can store timing, metrics, intermediate results, etc.
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional workflow metadata"
    )
    
    # Pydantic v2 configuration
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: str
        }


# ========================================
# API REQUEST/RESPONSE SCHEMAS
# ========================================

class BatchCreateRequest(BaseModel):
    """
    Request to create a new payroll batch
    
    Used by: POST /admin/trigger
    """
    
    month: str = Field(
        ...,
        description="Payroll month (YYYY-MM)",
        pattern=r"^\d{4}-\d{2}$"
    )
    
    # force: If true, create batch even if one exists for this month
    force: bool = Field(
        default=False,
        description="Force create even if batch exists"
    )


class BatchResponse(BaseModel):
    """
    Payroll batch response
    
    Used by: GET /batches/{batch_id}
    """
    
    id: str
    month: str
    status: BatchStatus
    total_amount: Decimal
    line_count: int
    anomaly_count: int
    summary: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: str
        }


class BatchListResponse(BaseModel):
    """
    List of payroll batches
    
    Used by: GET /batches
    """
    
    batches: List[BatchResponse]
    total: int
    page: int
    page_size: int


class TransactionResponse(BaseModel):
    """
    Blockchain transaction response
    
    Used by: GET /transactions/{tx_id}
    """
    
    id: str
    batch_id: str
    tx_hash: str
    status: TransactionStatus
    block_number: Optional[int]
    gas_used: Optional[int]
    recipient_count: int
    total_amount: Decimal
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: str
        }


class ApprovalRequest(BaseModel):
    """
    Approval request from Slack
    
    Used by: POST /slack/actions
    """
    
    batch_id: str
    decision: ApprovalDecision
    approver: str
    selected_ids: Optional[List[str]] = None
    comment: Optional[str] = None


class ApprovalResponse(BaseModel):
    """
    Approval response
    """
    
    id: str
    batch_id: str
    decision: ApprovalDecision
    approver: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========================================
# WEBHOOK SCHEMAS
# ========================================

class ExpenseWebhookPayload(BaseModel):
    """
    Payload sent to expense system webhook
    
    After successful blockchain transactions,
    we send this data to the expense system for record-keeping.
    """
    
    batch_id: str
    month: str
    transactions: List[Dict[str, Any]]
    total_amount: Decimal
    recipient_count: int
    timestamp: datetime
    
    class Config:
        json_encoders = {
            Decimal: str
        }


# ========================================
# REPORT SCHEMAS
# ========================================

class ReconciliationReport(BaseModel):
    """
    Reconciliation report
    
    Compares expected payroll vs actual blockchain transactions.
    Used by: GET /reports/{month}/reconcile
    """
    
    month: str
    batch_id: str
    
    # Expected values (from payroll system)
    expected_total: Decimal
    expected_count: int
    
    # Actual values (from blockchain)
    actual_total: Decimal
    actual_count: int
    
    # Differences
    amount_diff: Decimal
    count_diff: int
    
    # Status
    reconciled: bool
    discrepancies: List[Dict[str, Any]]
    
    class Config:
        json_encoders = {
            Decimal: str
        }


# ========================================
# METRICS SCHEMAS
# ========================================

class MetricsSummary(BaseModel):
    """
    System metrics summary
    
    Used for monitoring dashboard
    """
    
    # Batch metrics
    total_batches: int
    batches_pending: int
    batches_completed: int
    batches_failed: int
    
    # Transaction metrics
    total_transactions: int
    total_usdc_sent: Decimal
    total_recipients: int
    
    # Success rate
    success_rate: float
    
    # Recent batches
    recent_batches: List[BatchResponse]
    
    class Config:
        json_encoders = {
            Decimal: str
        }

