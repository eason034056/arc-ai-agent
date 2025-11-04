"""
Database Models

This module defines SQLAlchemy ORM models representing database tables.

Tables:
- payroll_batches: Main payroll batch metadata
- payroll_lines: Individual payroll lines (one per employee)
- transactions: On-chain transaction records
- approvals: Approval workflow records

Why SQLAlchemy ORM?
- Type-safe Python code instead of raw SQL
- Automatic relationship handling
- Database-agnostic (works with PostgreSQL, MySQL, SQLite, etc.)
- Migration support via Alembic
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import List

from sqlalchemy import (
    Column, String, Integer, Numeric, DateTime, ForeignKey,
    JSON, Boolean, Text, Enum as SQLEnum, Index
)
from sqlalchemy.orm import relationship

from app.db.connection import Base


# ========================================
# ENUMS
# ========================================
# These enums define valid values for status columns
# Using enums prevents typos and invalid states

class BatchStatus(str, PyEnum):
    """
    Payroll Batch Status
    
    Status flow:
    DRAFT → PENDING_APPROVAL → APPROVED → PROCESSING → COMPLETED
                            ↓
                         REJECTED
    """
    DRAFT = "draft"                      # Initial state, being prepared
    PENDING_APPROVAL = "pending_approval"  # Sent to Slack, waiting for human
    APPROVED = "approved"                  # Human approved, ready to process
    REJECTED = "rejected"                  # Human rejected
    PROCESSING = "processing"              # Currently sending transactions
    COMPLETED = "completed"                # All transactions sent successfully
    FAILED = "failed"                      # Processing failed with errors


class TransactionStatus(str, PyEnum):
    """
    Blockchain Transaction Status
    
    Status flow:
    PENDING → CONFIRMED → SUCCESS
           ↓
         FAILED
    """
    PENDING = "pending"      # Submitted to blockchain, waiting for confirmation
    CONFIRMED = "confirmed"  # Included in a block
    SUCCESS = "success"      # Transaction succeeded
    FAILED = "failed"        # Transaction reverted or failed


class ApprovalDecision(str, PyEnum):
    """
    Approval Decision Types
    """
    PENDING = "pending"            # Waiting for decision
    APPROVE_ALL = "approve_all"    # Approve entire batch
    APPROVE_PARTIAL = "approve_partial"  # Approve only selected lines
    REJECT = "reject"              # Reject entire batch


# ========================================
# MODELS
# ========================================

class PayrollBatch(Base):
    """
    Payroll Batch Model
    
    Represents a single payroll run for a specific month.
    Each batch contains multiple payroll lines (one per employee).
    
    Attributes:
        id: Unique identifier (UUID)
        month: Payroll month (e.g., "2025-11")
        status: Current batch status
        total_amount: Total USDC amount for all lines
        line_count: Number of payroll lines
        anomaly_count: Number of flagged anomalies
        summary: AI-generated summary (JSON)
        created_at: When the batch was created
        updated_at: Last update timestamp
        
    Relationships:
        lines: List of PayrollLine objects
        transactions: List of Transaction objects
        approvals: List of Approval objects
    """
    
    # Table name in PostgreSQL
    __tablename__ = "payroll_batches"
    
    # ========================================
    # COLUMNS
    # ========================================
    # id: Primary key
    # String(36) is enough for UUIDs (32 hex chars + 4 hyphens)
    id = Column(String(36), primary_key=True, index=True)
    
    # month: Payroll month in YYYY-MM format
    # indexed for fast lookups by month
    month = Column(String(7), nullable=False, index=True)
    
    # status: Current batch status (enum)
    # nullable=False: Must always have a status
    # default: New batches start as DRAFT
    status = Column(
        SQLEnum(BatchStatus),
        nullable=False,
        default=BatchStatus.DRAFT,
        index=True  # Index for filtering by status
    )
    
    # total_amount: Sum of all payroll lines
    # Numeric(18, 6) = 18 total digits, 6 after decimal
    # Example: 999999999999.123456 USDC
    total_amount = Column(Numeric(18, 6), nullable=False, default=0)
    
    # line_count: Number of employees in this batch
    line_count = Column(Integer, nullable=False, default=0)
    
    # anomaly_count: Number of flagged anomalies
    anomaly_count = Column(Integer, nullable=False, default=0)
    
    # summary: AI-generated summary (stored as JSON)
    # Example: {"total": 50000, "departments": ["Eng", "Sales"], ...}
    summary = Column(JSON, nullable=True)
    
    # metadata_: Additional batch metadata (JSON)
    # Note: trailing underscore because "metadata" is a SQLAlchemy reserved word
    metadata_ = Column("metadata", JSON, nullable=True)
    
    # created_at: Timestamp when batch was created
    # default=datetime.utcnow: Automatically set on insert
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # updated_at: Timestamp of last update
    # onupdate=datetime.utcnow: Automatically update on every change
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # ========================================
    # RELATIONSHIPS
    # ========================================
    # These define connections to other tables
    # SQLAlchemy automatically handles joins
    
    # lines: One-to-many relationship
    # One batch has many payroll lines
    # back_populates: Creates a reverse "batch" attribute on PayrollLine
    # cascade: When batch is deleted, delete all its lines too
    lines = relationship(
        "PayrollLine",
        back_populates="batch",
        cascade="all, delete-orphan"
    )
    
    # transactions: One-to-many relationship
    # One batch may have multiple blockchain transactions
    transactions = relationship(
        "Transaction",
        back_populates="batch",
        cascade="all, delete-orphan"
    )
    
    # approvals: One-to-many relationship
    # Track approval history (can have multiple approval attempts)
    approvals = relationship(
        "Approval",
        back_populates="batch",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"<PayrollBatch(id={self.id}, month={self.month}, status={self.status})>"


class PayrollLine(Base):
    """
    Payroll Line Model
    
    Represents a single employee's payroll entry in a batch.
    
    Attributes:
        id: Unique identifier
        batch_id: Foreign key to PayrollBatch
        employee_id: Employee identifier
        wallet: Employee's wallet address
        amount_usdc: Payroll amount in USDC
        flags: Anomaly flags (JSON array)
        metadata_: Additional line metadata
        
    Relationships:
        batch: Parent PayrollBatch object
    """
    
    __tablename__ = "payroll_lines"
    
    # id: Primary key
    id = Column(String(36), primary_key=True, index=True)
    
    # batch_id: Foreign key to payroll_batches.id
    # ForeignKey establishes the relationship
    # nullable=False: Every line must belong to a batch
    batch_id = Column(
        String(36),
        ForeignKey("payroll_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # employee_id: Internal employee identifier
    # Could be email, employee number, etc.
    employee_id = Column(String(100), nullable=False, index=True)
    
    # wallet: Ethereum wallet address (42 chars with 0x prefix)
    # This is where USDC will be sent
    wallet = Column(String(42), nullable=False, index=True)
    
    # amount_usdc: Payroll amount
    amount_usdc = Column(Numeric(18, 6), nullable=False)
    
    # flags: Array of anomaly flags
    # Example: ["HIGH_AMOUNT", "FIRST_TIME_RECIPIENT"]
    flags = Column(JSON, nullable=True, default=list)
    
    # metadata_: Additional line metadata
    metadata_ = Column("metadata", JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # ========================================
    # RELATIONSHIPS
    # ========================================
    # batch: Many-to-one relationship
    # Many lines belong to one batch
    batch = relationship("PayrollBatch", back_populates="lines")
    
    def __repr__(self) -> str:
        return f"<PayrollLine(id={self.id}, employee_id={self.employee_id}, amount={self.amount_usdc})>"


class Transaction(Base):
    """
    Transaction Model
    
    Represents a blockchain transaction (batch payment).
    Each transaction can pay multiple recipients.
    
    Attributes:
        id: Unique identifier
        batch_id: Foreign key to PayrollBatch
        tx_hash: Blockchain transaction hash
        status: Transaction status
        block_number: Block number (when confirmed)
        gas_used: Gas consumed by transaction
        recipient_count: Number of recipients in this transaction
        total_amount: Total USDC sent
        metadata_: Additional transaction metadata
        
    Relationships:
        batch: Parent PayrollBatch object
    """
    
    __tablename__ = "transactions"
    
    id = Column(String(36), primary_key=True, index=True)
    
    # batch_id: Foreign key to batch
    batch_id = Column(
        String(36),
        ForeignKey("payroll_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # tx_hash: Blockchain transaction hash (66 chars with 0x prefix)
    # This is the unique identifier on the blockchain
    tx_hash = Column(String(66), nullable=False, unique=True, index=True)
    
    # status: Transaction status enum
    status = Column(
        SQLEnum(TransactionStatus),
        nullable=False,
        default=TransactionStatus.PENDING
    )
    
    # block_number: Which block included this transaction
    # NULL until confirmed
    block_number = Column(Integer, nullable=True)
    
    # gas_used: Gas consumed (cost of transaction)
    # Useful for accounting and cost tracking
    gas_used = Column(Integer, nullable=True)
    
    # recipient_count: How many employees were paid in this transaction
    recipient_count = Column(Integer, nullable=False)
    
    # total_amount: Total USDC sent in this transaction
    total_amount = Column(Numeric(18, 6), nullable=False)
    
    # metadata_: Additional transaction data
    # Could include gas price, nonce, error messages, etc.
    metadata_ = Column("metadata", JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # ========================================
    # RELATIONSHIPS
    # ========================================
    batch = relationship("PayrollBatch", back_populates="transactions")
    
    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, tx_hash={self.tx_hash}, status={self.status})>"


class Approval(Base):
    """
    Approval Model
    
    Tracks approval workflow for payroll batches.
    Records who approved/rejected and when.
    
    Attributes:
        id: Unique identifier
        batch_id: Foreign key to PayrollBatch
        decision: Approval decision
        approver: Who made the decision (Slack user ID)
        selected_ids: For partial approvals, which lines were approved
        comment: Optional comment from approver
        slack_ts: Slack message timestamp (for updating the message)
        
    Relationships:
        batch: Parent PayrollBatch object
    """
    
    __tablename__ = "approvals"
    
    id = Column(String(36), primary_key=True, index=True)
    
    # batch_id: Foreign key to batch
    batch_id = Column(
        String(36),
        ForeignKey("payroll_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # decision: What was decided
    decision = Column(
        SQLEnum(ApprovalDecision),
        nullable=False,
        default=ApprovalDecision.PENDING
    )
    
    # approver: Who made the decision
    # Usually a Slack user ID (e.g., "U01234567")
    approver = Column(String(100), nullable=True)
    
    # selected_ids: For partial approvals
    # Array of payroll line IDs to approve
    # Example: ["line-1", "line-2", "line-3"]
    selected_ids = Column(JSON, nullable=True)
    
    # comment: Optional comment from approver
    comment = Column(Text, nullable=True)
    
    # slack_ts: Slack message timestamp
    # Used to update the approval card in Slack
    slack_ts = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # ========================================
    # RELATIONSHIPS
    # ========================================
    batch = relationship("PayrollBatch", back_populates="approvals")
    
    def __repr__(self) -> str:
        return f"<Approval(id={self.id}, batch_id={self.batch_id}, decision={self.decision})>"


# ========================================
# INDEXES
# ========================================
# Additional indexes for common queries
# These speed up lookups but add overhead to inserts/updates

# Index for finding batches by month and status
# Common query: "Get all approved batches for November 2025"
Index(
    "ix_batch_month_status",
    PayrollBatch.month,
    PayrollBatch.status
)

# Index for finding lines by employee
# Common query: "Get payroll history for employee X"
Index(
    "ix_line_employee_batch",
    PayrollLine.employee_id,
    PayrollLine.batch_id
)

# Index for finding transactions by status
# Common query: "Get all pending transactions"
Index(
    "ix_transaction_status",
    Transaction.status
)

