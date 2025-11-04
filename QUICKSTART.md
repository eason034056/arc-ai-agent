# Quick Start Guide

Get the Arc Payroll AI Agent running in under 10 minutes!

## Prerequisites

- Docker & Docker Compose installed
- Git installed
- Basic command line knowledge

## Step-by-Step Setup

### 1. Clone or Navigate to Project

```bash
cd "/Users/wuyusen/Desktop/Arc Hackathon/arc-ai-agent"
```

### 2. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit with your values
nano .env
```

**Minimum required values:**
```env
DATABASE_URL=postgresql+psycopg2://user:pass@postgres:5432/arc_payroll
SLACK_BOT_TOKEN=xoxb-your-token-here
SLACK_SIGNING_SECRET=your-secret-here
ARC_RPC_URL=https://your-arc-testnet-rpc
PRIVATE_KEY=0xyour-private-key
PAYROLL_CONTRACT_ADDRESS=0xyour-contract-address
```

### 3. Start Services

```bash
# Start all services (app, database, redis, monitoring)
docker compose up -d --build
```

Wait for services to start (~30 seconds). Check with:
```bash
docker compose ps
```

You should see:
- ✅ arc-payroll-app (running)
- ✅ arc-payroll-postgres (healthy)
- ✅ arc-payroll-redis (healthy)
- ✅ arc-payroll-prometheus (running)
- ✅ arc-payroll-grafana (running)

### 4. Initialize Database

```bash
# Run database migrations
docker compose exec app alembic upgrade head

# (Optional) Seed demo data
docker compose exec app python scripts/seed_demo.py
```

### 5. Test the System

#### Option A: Via API (Simple)

```bash
# Trigger a payroll batch for November 2025
curl -X POST "http://localhost:8080/admin/trigger?month=2025-11"
```

#### Option B: Via Python Script

```bash
docker compose exec app python -c "
from app.agent.graph import run_payroll_workflow
from app.agent.policies import PayrollPolicy

result = run_payroll_workflow(
    batch_id='test_001',
    month='2025-11',
    policy=PayrollPolicy()
)

print(f'Status: {result.metadata.get(\"final_status\")}')
print(f'Lines: {len(result.lines)}')
print(f'Tx Hashes: {len(result.tx_hashes)}')
"
```

### 6. Access Services

- **API Documentation**: http://localhost:8080/docs
- **Grafana Dashboard**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

## What Just Happened?

You ran a complete payroll workflow:

1. ✅ Ingested employee data
2. ✅ Cleaned and validated
3. ✅ Computed salaries
4. ✅ Detected anomalies
5. ✅ Generated summary
6. ⏸️ Waiting for approval (Slack button)
7. (After approval) Blockchain transactions
8. (After approval) Writeback & reconciliation

## Next Steps

### Configure Slack Integration

1. **Create Slack App**: https://api.slack.com/apps
2. **Add Bot Token Scopes**:
   - `chat:write`
   - `commands`
   - `im:write`
3. **Enable Interactive Components**
4. **Set Request URL**: `https://your-domain.com/slack/events`
5. **Copy tokens to `.env`**

### Deploy Smart Contract

```bash
cd ../contracts  # If you have a contracts directory

# Install dependencies
npm install

# Configure .env with:
# - ARC_RPC_URL
# - PRIVATE_KEY
# - USDC_ADDRESS
# - ADMIN_ADDRESS

# Deploy
npx hardhat run scripts/deploy.ts --network arcTestnet
```

### Add Real Employee Data

Edit `app/agent/nodes/node_ingest.py` to load from your data source:

```python
# Option 1: From database
def load_from_database(month):
    # Your database query here
    pass

# Option 2: From CSV
def load_from_csv(file_path):
    # Your CSV loading logic here
    pass
```

### Configure Monitoring

1. Open Grafana: http://localhost:3000
2. Add Prometheus data source:
   - URL: `http://prometheus:9090`
   - Save & Test
3. Import dashboard (or create custom)

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker compose logs app

# Restart services
docker compose down
docker compose up -d --build
```

### Database Connection Error

```bash
# Ensure PostgreSQL is healthy
docker compose ps postgres

# Check database logs
docker compose logs postgres

# Try manual connection
docker compose exec postgres psql -U user -d arc_payroll
```

### Import Errors

```bash
# Reinstall dependencies
docker compose exec app pip install -r requirements.txt

# Rebuild container
docker compose up -d --build
```

### Slack Not Working

- Check `SLACK_BOT_TOKEN` starts with `xoxb-`
- Verify bot is installed to workspace
- Check Request URL is configured correctly
- Review Slack app logs in API dashboard

## Common Commands

```bash
# View logs
docker compose logs -f app

# Stop services
docker compose down

# Restart a service
docker compose restart app

# Execute command in container
docker compose exec app python -c "print('Hello')"

# Access PostgreSQL
docker compose exec postgres psql -U user -d arc_payroll

# Run database migrations
docker compose exec app alembic upgrade head

# Create new migration
docker compose exec app alembic revision --autogenerate -m "description"
```

## Development Mode

For development with auto-reload:

```bash
# Edit docker-compose.yml, add to app service:
command: uvicorn app.api.main:app --host 0.0.0.0 --port 8080 --reload

# Or run outside Docker:
pip install -r requirements.txt
uvicorn app.api.main:app --reload
```

## Need Help?

1. **Check Documentation**: Read the tutorials in `docs/`
2. **Review Code Comments**: Every function is documented
3. **Check Logs**: `docker compose logs app`
4. **Test Individual Nodes**: See `app/agent/nodes/` for examples

## What's Next?

- **[Tutorial 01: Basics](docs/TUTORIAL-01-BASICS.md)** - Understand the system
- **[Tutorial 02: Setup](docs/TUTORIAL-02-SETUP.md)** - Detailed setup
- **[Tutorial 03: Database](docs/TUTORIAL-03-DATABASE.md)** - Data models
- **[Tutorial 04: LangGraph](docs/TUTORIAL-04-LANGGRAPH.md)** - Workflow deep dive

**You're all set!** 🚀

