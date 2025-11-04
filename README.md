# Arc Testnet Payroll AI Agent

A comprehensive AI-powered payroll automation system built with Python, LangGraph, and Web3, designed to run on Arc Testnet.

## 🎯 What This System Does

This AI agent automates the entire payroll process:
1. **Ingests** employee data from various sources
2. **Cleans** and validates the data
3. **Computes** salary amounts based on rules
4. **Detects** anomalies using AI
5. **Summarizes** the payroll batch
6. **Proposes** the batch for approval via Slack
7. **Waits** for human approval
8. **Executes** batch payments on Arc Testnet blockchain
9. **Writes back** results to expense systems
10. **Reconciles** and generates reports

## 📚 Documentation Structure

We've organized the documentation from simple to complex:

1. **[TUTORIAL-01-BASICS.md](docs/TUTORIAL-01-BASICS.md)** - Core concepts and architecture
2. **[TUTORIAL-02-SETUP.md](docs/TUTORIAL-02-SETUP.md)** - Environment setup and configuration
3. **[TUTORIAL-03-DATABASE.md](docs/TUTORIAL-03-DATABASE.md)** - Database models and schemas
4. **[TUTORIAL-04-LANGGRAPH.md](docs/TUTORIAL-04-LANGGRAPH.md)** - LangGraph AI Agent workflow
5. **[TUTORIAL-05-NODES.md](docs/TUTORIAL-05-NODES.md)** - Individual node implementations
6. **[TUTORIAL-06-SLACK.md](docs/TUTORIAL-06-SLACK.md)** - Slack integration and approvals
7. **[TUTORIAL-07-WEB3.md](docs/TUTORIAL-07-WEB3.md)** - Blockchain integration
8. **[TUTORIAL-08-API.md](docs/TUTORIAL-08-API.md)** - FastAPI endpoints
9. **[TUTORIAL-09-DEPLOYMENT.md](docs/TUTORIAL-09-DEPLOYMENT.md)** - Docker and deployment

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Node.js 18+ (for smart contracts)
- Arc Testnet RPC URL
- Slack workspace (for approvals)

### Installation

```bash
# Clone and navigate to the project
cd arc-ai-agent

# Copy environment variables
cp .env.example .env

# Edit .env with your credentials
nano .env

# Start all services with Docker
docker compose up -d --build

# Run database migrations
docker compose exec app alembic upgrade head

# Seed demo data (optional)
docker compose exec app python scripts/seed_demo.py
```

### Test the Agent

```bash
# Trigger a payroll batch for November 2025
curl -X POST "http://localhost:8080/admin/trigger?month=2025-11"
```

## 📁 Project Structure

```
arc-ai-agent/
├── app/                          # Main application code
│   ├── core/                     # Configuration, logging, utilities
│   ├── db/                       # Database models and schemas
│   ├── agent/                    # LangGraph AI Agent
│   │   ├── graph.py              # Main workflow graph
│   │   ├── policies.py           # Business rules and policies
│   │   └── nodes/                # Individual workflow nodes
│   ├── slack/                    # Slack integration
│   ├── onchain/                  # Web3 blockchain integration
│   ├── expense/                  # Expense system webhook
│   └── api/                      # FastAPI endpoints
├── docs/                         # Tutorial documentation
├── scripts/                      # Helper scripts
├── migrations/                   # Database migrations
├── abi/                          # Smart contract ABIs
├── docker-compose.yml            # Docker orchestration
├── Dockerfile                    # Application container
├── requirements.txt              # Python dependencies
└── .env.example                  # Environment template
```

## 🏗️ Architecture

```
┌─────────────────┐
│  Slack Channel  │ ← Human Approval
└────────┬────────┘
         │
    ┌────▼────────────────────────────────┐
    │      LangGraph AI Agent             │
    │  ┌──────────────────────────────┐   │
    │  │ ingest → clean → compute     │   │
    │  │   ↓                           │   │
    │  │ detect → summarize → propose │   │
    │  │   ↓                           │   │
    │  │ approve_gate (wait)          │   │
    │  │   ↓                           │   │
    │  │ onchain → writeback →        │   │
    │  │ reconcile → done             │   │
    │  └──────────────────────────────┘   │
    └────┬───────────────────┬─────────────┘
         │                   │
    ┌────▼────────┐    ┌────▼──────────┐
    │  PostgreSQL │    │  Arc Testnet  │
    │   Database  │    │  (Blockchain) │
    └─────────────┘    └───────────────┘
```

## 🔑 Key Technologies

- **LangGraph**: Orchestrates the AI workflow with state management
- **FastAPI**: Modern Python web framework for API endpoints
- **SQLAlchemy**: ORM for database operations
- **Web3.py**: Ethereum/Arc blockchain interactions
- **Slack Bolt**: Slack app integration framework
- **Docker**: Containerization and orchestration
- **Prometheus & Grafana**: Monitoring and metrics

## 📖 Learning Path

1. **Start with Tutorial 01**: Understand the basic concepts
2. **Follow Tutorial 02**: Set up your development environment
3. **Read Tutorial 03**: Learn about data models
4. **Study Tutorial 04**: Understand the LangGraph workflow
5. **Deep dive Tutorial 05**: Explore individual node implementations
6. **Continue sequentially**: Each tutorial builds on the previous ones

## 🤝 Contributing

This is a hackathon project built for Arc Testnet. Feel free to:
- Report issues
- Suggest improvements
- Submit pull requests

## 📝 License

MIT License - see LICENSE file for details

## 🆘 Support

- Check the tutorial documentation in `docs/`
- Review code comments for detailed explanations
- Refer to the original specification in `arc-payroll-unified-devdoc.md`

---

**Built with ❤️ for Arc Testnet Hackathon**
