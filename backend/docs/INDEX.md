# Arc Payroll AI Agent - Documentation Index

Welcome! This index helps you navigate all the documentation and code in this project.

## 🚀 Quick Navigation

### New to the Project? Start Here:
1. **[README.md](README.md)** - Project overview and quick links
2. **[QUICKSTART.md](QUICKSTART.md)** - Get running in < 10 minutes
3. **[docs/TUTORIAL-01-BASICS.md](docs/TUTORIAL-01-BASICS.md)** - Understand core concepts

### Want to Understand Everything?
**[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Complete technical explanation of every component

### Need to Set Up?
**[QUICKSTART.md](QUICKSTART.md)** - Step-by-step setup instructions with Docker

## 📚 Documentation Structure

### Getting Started (Read in Order)
```
1. README.md               ← What is this project?
2. QUICKSTART.md          ← How do I run it?
3. TUTORIAL-01-BASICS.md  ← How does it work?
4. PROJECT_SUMMARY.md     ← Deep technical dive
```

### Configuration Files
```
.env.example              ← All environment variables explained
requirements.txt          ← Python dependencies with descriptions
Dockerfile               ← Container image definition
docker-compose.yml       ← Multi-service orchestration
```

### Core Application Code

#### Configuration & Utilities
```
app/core/config.py       ← Settings (loads & validates .env)
app/core/logging.py      ← Structured logging setup
```

#### Database Layer
```
app/db/connection.py     ← SQLAlchemy session management
app/db/models.py         ← Database tables (ORM models)
app/db/schema.py         ← Pydantic schemas (validation)
```

#### AI Agent (LangGraph)
```
app/agent/graph.py       ← Main workflow definition
app/agent/policies.py    ← Business rules & policies

app/agent/nodes/
  ├── node_ingest.py     ← Load employee data
  ├── node_clean.py      ← Validate & normalize
  ├── node_compute.py    ← Calculate salaries
  ├── node_detect.py     ← Anomaly detection
  ├── node_summarize.py  ← Create summary (AI)
  ├── node_propose.py    ← Send to Slack
  ├── node_approve_gate.py ← Wait for approval
  ├── node_onchain.py    ← Blockchain transactions
  ├── node_writeback.py  ← Save results
  └── node_reconcile.py  ← Final reconciliation
```

#### Integrations
```
app/slack/app.py         ← Slack Bolt app & handlers
app/onchain/service.py   ← Web3 blockchain service
```

#### API
```
app/api/main.py          ← FastAPI routes & endpoints
```

## 🎯 Common Tasks

### I want to...

#### ...understand the workflow
📖 Read: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) → Section "Complete Workflow Example"

#### ...run the system locally
📖 Read: [QUICKSTART.md](QUICKSTART.md)

#### ...modify salary calculation rules
📝 Edit: `app/agent/nodes/node_compute.py` and `app/agent/policies.py`

#### ...add a new data source (CSV, API, etc.)
📝 Edit: `app/agent/nodes/node_ingest.py`

#### ...change anomaly detection logic
📝 Edit: `app/agent/nodes/node_detect.py`

#### ...customize the Slack approval card
📝 Edit: `app/agent/nodes/node_propose.py`

#### ...add a new API endpoint
📝 Edit: `app/api/main.py`

#### ...deploy to production
📖 Read: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) → Section "Next Steps"

#### ...understand a specific function
💡 Tip: All code is heavily commented! Just open the file and read.

## 📖 Code Comment Philosophy

**Every file includes:**
- Module docstring explaining purpose
- Function docstrings with:
  - What it does
  - Arguments and return values
  - Usage examples
  - Why it works this way
- Inline comments explaining:
  - Non-obvious logic
  - Business rules
  - Technical decisions

**Example:**
```python
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
```

## 🏗️ Architecture Diagrams

### High-Level Flow
```
User triggers → API → LangGraph Agent → Slack (approval) → Blockchain → Done
```

### Data Flow
```
CSV/DB → Ingest → Clean → Compute → Detect → Summarize
                                                   ↓
Report ← Reconcile ← Writeback ← Blockchain ← Approve
```

### Tech Stack
```
Frontend:     Slack (approval UI)
Backend:      Python + FastAPI + LangGraph
Database:     PostgreSQL + SQLAlchemy
Cache:        Redis
Blockchain:   Web3.py → Arc Testnet
Monitoring:   Prometheus + Grafana
Deployment:   Docker + Docker Compose
```

## 🔍 File Organization Explained

### Why this structure?

**`app/core/`** - Cross-cutting concerns
- Things used by multiple modules
- Configuration, logging, utilities

**`app/db/`** - Database isolation
- All database code in one place
- Easy to swap PostgreSQL for another DB

**`app/agent/`** - Business logic
- The "brain" of the application
- Pure functions for testability

**`app/agent/nodes/`** - Single responsibility
- Each node does ONE thing
- Easy to understand and modify

**`app/slack/`** - Integration isolation
- Slack-specific code separate
- Easy to add other integrations (email, SMS, etc.)

**`app/onchain/`** - Blockchain isolation
- Web3 code in one place
- Easy to support multiple chains

**`app/api/`** - HTTP interface
- Thin layer exposing functionality
- Routes → Services → Nodes

## 📊 Key Design Decisions

### 1. Immutable State (LangGraph)
**Decision:** State flows through nodes, never mutated
**Why:** Reproducible, debuggable, testable
**Example:** `state.model_copy(update={...})`

### 2. Dependency Injection
**Decision:** Services passed as parameters
**Why:** Testable without external dependencies
**Example:** `run(state, onchain_service=None)`

### 3. Error Collection (vs Exceptions)
**Decision:** Collect errors in state, don't raise
**Why:** Partial success, all errors visible
**Example:** `errors.append("Error message")`

### 4. Pure Functional Nodes
**Decision:** Nodes are pure functions
**Why:** Testable, composable, predictable
**Example:** Same input → Same output

### 5. Type Safety (Pydantic)
**Decision:** Validate everything with types
**Why:** Catch errors at boundaries
**Example:** `AgentState(BaseModel)`

## 🎓 Learning Resources

### Concepts
- **LangGraph**: https://langchain-ai.github.io/langgraph/
- **State Machines**: https://en.wikipedia.org/wiki/Finite-state_machine
- **Web3**: https://ethereum.org/en/developers/docs/

### Technologies
- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **Pydantic**: https://docs.pydantic.dev/
- **Slack Bolt**: https://slack.dev/bolt-python/
- **Web3.py**: https://web3py.readthedocs.io/

### Patterns
- **Repository Pattern**: https://martinfowler.com/eaaCatalog/repository.html
- **Dependency Injection**: https://en.wikipedia.org/wiki/Dependency_injection
- **Domain-Driven Design**: https://martinfowler.com/bliki/DomainDrivenDesign.html

## 🤝 Contributing

Want to improve this project?

1. **Find an issue**: Check code TODOs
2. **Make a change**: Follow existing patterns
3. **Add comments**: Explain your reasoning
4. **Test**: Ensure it works end-to-end

**Common improvements needed:**
- Database repository implementations
- More comprehensive tests
- Additional data sources
- Enhanced anomaly detection
- Web UI for management

## 📝 Coding Standards

### Python Style
- **PEP 8** compliance
- **Type hints** on all functions
- **Docstrings** in Google style
- **Comments** for non-obvious logic

### Naming Conventions
- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions**: `snake_case()`
- **Constants**: `UPPER_SNAKE_CASE`

### Module Organization
```python
# 1. Imports (grouped)
from typing import ...
from app.core import ...

# 2. Constants
DEFAULT_TIMEOUT = 120

# 3. Classes/Functions
class MyClass:
    ...

def my_function():
    ...

# 4. Main execution (if applicable)
if __name__ == "__main__":
    ...
```

## 🎉 You're Ready!

With this index, you can:
- ✅ Navigate the entire codebase
- ✅ Find what you need quickly
- ✅ Understand design decisions
- ✅ Make modifications confidently

**Start exploring and happy coding!** 🚀

---

**Need help?** 
- Every file has detailed comments
- Check [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) for deep dives
- Read the code - it's designed to be readable!

