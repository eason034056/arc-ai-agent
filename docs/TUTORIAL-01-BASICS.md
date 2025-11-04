# Tutorial 01: Basic Concepts and Architecture

Welcome to the Arc Payroll AI Agent tutorial series! This document introduces the fundamental concepts and architecture of the system.

## Table of Contents
- [What is This System?](#what-is-this-system)
- [Key Technologies](#key-technologies)
- [Architecture Overview](#architecture-overview)
- [Workflow Explanation](#workflow-explanation)
- [Core Concepts](#core-concepts)
- [Next Steps](#next-steps)

## What is This System?

The Arc Payroll AI Agent is an automated payroll processing system that:

1. **Automates repetitive tasks**: No more manual payroll calculations
2. **Detects anomalies**: AI-powered detection of unusual patterns
3. **Requires human approval**: Human-in-the-loop via Slack
4. **Executes on blockchain**: Transparent, immutable payment records on Arc Testnet
5. **Handles errors gracefully**: Retry logic and comprehensive error handling

### Real-World Use Case

Imagine a company with 100 employees:

**Traditional Process:**
```
1. HR manually calculates each salary (2 hours)
2. Finance reviews for errors (1 hour)
3. Manual bank transfers or crypto sends (3 hours)
4. Manual reconciliation (1 hour)
Total: 7 hours of manual work
```

**With AI Agent:**
```
1. AI ingests employee data (30 seconds)
2. AI calculates and detects anomalies (30 seconds)
3. Human approves via Slack button click (1 minute)
4. Blockchain automatically pays all employees (2 minutes)
5. Automatic reconciliation and reporting (30 seconds)
Total: ~5 minutes of human time
```

## Key Technologies

### 1. **Python** - Programming Language
   - Why? Modern, readable, excellent AI/ML libraries
   - Version: 3.11+

### 2. **LangGraph** - AI Workflow Framework
   - What: Framework for building stateful AI agents
   - Why: Handles complex workflows with state management
   - Key Feature: Conditional branching based on AI/human decisions

### 3. **FastAPI** - Web Framework
   - What: Modern Python web framework
   - Why: Fast, automatic API documentation, async support
   - Used For: HTTP endpoints for Slack webhooks and admin API

### 4. **PostgreSQL** - Database
   - What: Relational database
   - Why: ACID compliance, reliability
   - Stores: Employee data, batch records, transactions

### 5. **Web3.py** - Blockchain Library
   - What: Python library for Ethereum/EVM chains
   - Why: Interact with Arc Testnet smart contracts
   - Used For: Sending USDC payments via PayrollVault contract

### 6. **Slack Bolt** - Slack Integration
   - What: Framework for building Slack apps
   - Why: Easy approval workflow with interactive buttons
   - Used For: Human approval step

### 7. **Docker** - Containerization
   - What: Container platform
   - Why: Consistent environment, easy deployment
   - Includes: App, PostgreSQL, Redis, Prometheus, Grafana

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    EXTERNAL SYSTEMS                          │
├─────────────────┬────────────────┬──────────────────────────┤
│  Slack Channel  │  Arc Testnet   │  Expense System (API)    │
│  (Approvals)    │  (Blockchain)  │  (Writeback)             │
└────────┬────────┴────────┬───────┴──────────┬───────────────┘
         │                 │                   │
         ▼                 ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    FASTAPI APPLICATION                       │
├─────────────────────────────────────────────────────────────┤
│  POST /admin/trigger       - Trigger payroll batch          │
│  POST /slack/commands      - Slack slash commands           │
│  POST /slack/actions       - Slack button clicks            │
│  POST /expense/webhook     - Expense system callbacks       │
│  GET  /batches/:id         - Get batch status               │
│  GET  /reports/:month      - Download reports               │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                   LANGGRAPH AI AGENT                         │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │  Ingest  │→ │  Clean   │→ │ Compute  │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
│       ↓                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │  Detect  │→ │Summarize │→ │ Propose  │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
│       ↓                                                      │
│  ┌──────────────────┐                                       │
│  │  Approve Gate    │ ← Wait for human approval             │
│  └──────────────────┘                                       │
│       ↓                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ Onchain  │→ │Writeback │→ │Reconcile │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────┬───────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATA LAYER                                │
├──────────────────┬──────────────────┬───────────────────────┤
│   PostgreSQL     │      Redis       │    Prometheus         │
│   (Persistent)   │    (Cache)       │    (Metrics)          │
└──────────────────┴──────────────────┴───────────────────────┘
```

## Workflow Explanation

Let's walk through a complete payroll run:

### Step 1: Ingest (30 seconds)
```python
# Input: Month identifier (e.g., "2025-11")
# Process: Load employee data from database or CSV
# Output: List of employees with wallet addresses
```

**What happens:**
- Query employee database
- Filter by active status
- Load wallet addresses
- Create initial payroll lines

**Example:**
```
Employee ID | Wallet Address              | Status
------------|----------------------------|--------
emp_001     | 0x1111...1111              | Active
emp_002     | 0x2222...2222              | Active
emp_003     | 0x3333...3333              | Active
```

### Step 2: Clean (10 seconds)
```python
# Input: Raw employee data
# Process: Validate and normalize
# Output: Clean, validated data
```

**What happens:**
- Validate wallet address format
- Check for duplicates
- Remove invalid entries
- Normalize to lowercase

**Example Issues Caught:**
- ❌ `0xABC` - Too short
- ❌ `0xGGGG...` - Invalid hex characters
- ❌ Duplicate wallet addresses

### Step 3: Compute (10 seconds)
```python
# Input: Clean employee list
# Process: Calculate salary amounts
# Output: Employee list with amounts
```

**What happens:**
- Apply salary rules (base + bonus - deductions)
- Calculate taxes if applicable
- Convert to USDC amounts

**Example Calculation:**
```
Employee emp_001:
  Base salary:    $5,000
  + Performance bonus: $500
  - Advance repayment: $0
  = Total: $5,500 USDC
```

### Step 4: Detect (20 seconds)
```python
# Input: Employee list with amounts
# Process: Detect anomalies using AI/statistics
# Output: Employee list with flags
```

**What happens:**
- Statistical analysis (z-score for outliers)
- Historical comparison (unusual changes)
- Rule-based checks (very high amounts)
- First-time recipient detection

**Example Flags:**
- 🚨 `HIGH_AMOUNT` - Amount >2σ from mean
- ⚠️ `FIRST_TIME` - Never received payroll before
- ⚡ `UNUSUAL_INCREASE` - 2x higher than usual

### Step 5: Summarize (10 seconds)
```python
# Input: Employee list with amounts and flags
# Process: Create human-readable summary
# Output: Summary with statistics and AI narrative
```

**What happens:**
- Calculate totals and averages
- Count anomalies
- Generate AI narrative (OpenAI GPT-4)
- Format for Slack display

**Example Summary:**
```
November 2025 Payroll
--------------------
Total: $27,500 USDC
Recipients: 5
Average: $5,500
Anomalies: 2

Flagged Items:
- emp_005: $8,000 (HIGH_AMOUNT)
- emp_004: $4,800 (FIRST_TIME)
```

### Step 6: Propose (5 seconds)
```python
# Input: Summary
# Process: Format as Slack message and send
# Output: Slack message with buttons
```

**What happens:**
- Format summary as Slack Block Kit
- Add action buttons (Approve/Reject)
- Send to approval channel
- Store message timestamp

**Slack Message:**
```
💰 November 2025 Payroll Approval

Total: $27,500 USDC
Recipients: 5
Anomalies: 2 ⚠️

Flagged Items:
• emp_005: $8,000 (HIGH_AMOUNT)
• emp_004: $4,800 (FIRST_TIME)

[✅ Approve All] [⚡ Approve Partial] [❌ Reject]
```

### Step 7: Approve Gate (Wait for human)
```python
# Input: Batch ID
# Process: Poll database for approval
# Output: Approval decision
```

**What happens:**
- Wait for human to click button in Slack
- Poll database every 5 seconds
- Timeout after 2 hours (configurable)
- Handle partial approvals

**Possible Decisions:**
1. ✅ `APPROVE_ALL` - Process all employees
2. ⚡ `APPROVE_PARTIAL` - Process selected employees only
3. ❌ `REJECT` - Cancel batch, end workflow

### Step 8: Onchain (2 minutes)
```python
# Input: Approved employee list
# Process: Execute blockchain transactions
# Output: Transaction hashes
```

**What happens:**
- Split into chunks (50 employees max per tx)
- Convert USDC amounts to smallest units
- Call `PayrollVault.batchPayout()` on Arc Testnet
- Wait for transaction confirmation
- Store transaction hashes

**Smart Contract Call:**
```solidity
// On Arc Testnet
PayrollVault.batchPayout(
    recipients: [0x1111..., 0x2222..., 0x3333...],
    amounts: [5500000000, 6000000000, 5500000000],  // 6 decimals
    batchId: "batch_123",
    meta: "November 2025 payroll"
)
```

### Step 9: Writeback (10 seconds)
```python
# Input: Transaction hashes
# Process: Send results to external systems
# Output: Success status
```

**What happens:**
- Save to internal database
- Send webhook to expense system
- Update transaction status
- Handle failures with retry

### Step 10: Reconcile (10 seconds)
```python
# Input: Expected vs actual data
# Process: Compare and generate report
# Output: Reconciliation report
```

**What happens:**
- Check blockchain transaction status
- Compare expected vs actual amounts
- Detect discrepancies
- Generate CSV report
- Mark batch as completed

**Reconciliation Report:**
```
Expected: $27,500 / 5 recipients
Actual:   $27,500 / 5 recipients
Status:   ✅ Reconciled
Success Rate: 100%
```

## Core Concepts

### 1. **Immutable State**
In LangGraph, state is immutable. Each node returns a new state:

```python
# ❌ DON'T: Mutate state
def bad_node(state):
    state.lines.append(new_line)  # Mutation!
    return state

# ✅ DO: Return new state
def good_node(state):
    new_lines = state.lines + [new_line]
    return state.model_copy(update={"lines": new_lines})
```

**Why?** Immutability makes the workflow:
- Reproducible (same input = same output)
- Debuggable (can inspect state at any point)
- Testable (pure functions)

### 2. **Dependency Injection**
Services are injected into nodes for testability:

```python
# Node accepts dependencies as parameters
def run(state, policy=None, onchain_service=None):
    if policy is None:
        policy = PayrollPolicy()  # Default
    
    # Use injected services
    if onchain_service:
        tx_hash = onchain_service.batch_payout(...)
```

**Why?** This allows:
- Unit testing with mock services
- Swapping implementations
- Running without external dependencies

### 3. **Error Handling**
Errors are collected in state, not raised:

```python
# ❌ DON'T: Raise exceptions
def bad_node(state):
    if error:
        raise Exception("Failed!")

# ✅ DO: Collect errors in state
def good_node(state):
    errors = list(state.errors)
    if error:
        errors.append("Error message")
    return state.model_copy(update={"errors": errors})
```

**Why?** This allows:
- Workflow to continue despite errors
- All errors collected in one place
- Partial success handling

### 4. **Pure Functions**
Nodes are pure functions (no side effects):

```python
# ❌ DON'T: Side effects in node
def bad_node(state):
    send_email()  # Side effect!
    return state

# ✅ DO: Side effects via injected services
def good_node(state, email_service=None):
    if email_service:
        email_service.send(...)
    return state
```

**Why?** Pure functions are:
- Testable (no external dependencies)
- Predictable (same input = same output)
- Composable (can be reused)

## Next Steps

Now that you understand the basics:

1. **[Tutorial 02: Setup](TUTORIAL-02-SETUP.md)** - Set up your development environment
2. **[Tutorial 03: Database](TUTORIAL-03-DATABASE.md)** - Learn about data models
3. **[Tutorial 04: LangGraph](TUTORIAL-04-LANGGRAPH.md)** - Deep dive into the workflow
4. **[Tutorial 05: Nodes](TUTORIAL-05-NODES.md)** - Understand each node
5. **[Tutorial 06: Slack](TUTORIAL-06-SLACK.md)** - Slack integration
6. **[Tutorial 07: Web3](TUTORIAL-07-WEB3.md)** - Blockchain integration
7. **[Tutorial 08: API](TUTORIAL-08-API.md)** - FastAPI endpoints
8. **[Tutorial 09: Deployment](TUTORIAL-09-DEPLOYMENT.md)** - Deploy to production

## Questions?

- Check the code comments (every line is explained!)
- Review the `README.md` for quick reference
- Refer back to this tutorial when concepts are unclear

**Happy Learning!** 🚀

