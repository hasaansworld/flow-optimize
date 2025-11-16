# 🚀 Quick Start: n8n-Integrated Multi-Agent System

## 📋 Prerequisites

- Docker & Docker Compose installed
- Python 3.11+ (for local development)
- Google Gemini API key

## ⚡ 3-Minute Setup

### Step 1: Configure Environment

```bash
# Clone or navigate to project
cd flow-optimize

# Copy environment template
cp .env.example .env

# Edit .env and add your Gemini API key
nano .env  # or use your favorite editor
```

Required in `.env`:
```bash
GEMINI_API_KEY=your_actual_key_here
GEMINI_MODEL=gemini-2.5-flash
PRICE_SCENARIO=normal
```

### Step 2: Start All Services

```bash
# Make startup script executable (first time only)
chmod +x start_n8n_system.sh

# Start everything
./start_n8n_system.sh
```

This starts:
- ✅ FastAPI Agent Server (port 8000)
- ✅ n8n Workflow UI (port 5678)
- ✅ PostgreSQL Database (port 5432)
- ✅ Redis Cache (port 6379)
- ✅ Grafana Dashboard (port 3000)

### Step 3: Test the System

```bash
# Run integration tests
python test_n8n_integration.py
```

Expected output:
```
🎉 All tests passed! n8n integration is working correctly.
Total: 15/15 tests passed (100.0%)
```

## 🎯 Using n8n Workflows

### Import the Main Control Loop

1. Open n8n UI: http://localhost:5678
2. Login with `admin` / `hackathon2025`
3. Click **"Workflows" → "Import from File"**
4. Select: `n8n_workflows/main_control_loop.json`
5. Click **"Activate"** toggle in top-right

### Test Manual Execution

1. In n8n, open the imported workflow
2. Click **"Execute Workflow"** button
3. Watch the nodes execute in sequence
4. Check output at final node

### View Decision History

```bash
# Check recent decisions
curl http://localhost:8000/api/v1/decisions/history?limit=5
```

## 🧪 Testing Individual Components

### Test API Endpoints

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Get current state from historical data
curl http://localhost:8000/api/v1/state/current

# Run inflow forecasting agent
curl -X POST http://localhost:8000/api/v1/assess/inflow \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2025-01-15T10:00:00",
    "L1": 5.5,
    "V": 20000,
    "F1": 850,
    "F2": 5000,
    "electricity_price": 0.05,
    "price_scenario": "normal",
    "current_index": 500
  }'
```

### Test Webhooks

```bash
# Trigger price alert
curl -X POST http://localhost:8000/webhooks/price_alert \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2025-01-15T10:00:00",
    "new_price": 0.08,
    "old_price": 0.05,
    "change_percent": 60.0,
    "scenario": "high"
  }'

# Trigger emergency
curl -X POST http://localhost:8000/webhooks/emergency \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2025-01-15T10:00:00",
    "emergency_type": "overflow",
    "current_L1": 7.8,
    "message": "Water level approaching maximum"
  }'
```

## 📊 Monitoring

### View Live Logs

```bash
# All services
docker-compose logs -f

# Agent API only
docker-compose logs -f agent-api

# n8n only
docker-compose logs -f n8n
```

### Access Dashboards

- **API Documentation:** http://localhost:8000/docs
- **n8n Workflow UI:** http://localhost:5678
- **Grafana Dashboard:** http://localhost:3000

### Database Queries

```bash
# Connect to database
docker exec -it wastewater-postgres psql -U wastewater -d wastewater_decisions

# View recent decisions
SELECT timestamp, priority, estimated_cost, confidence
FROM decisions
ORDER BY timestamp DESC
LIMIT 10;

# Exit
\q
```

## 🛑 Stop Services

```bash
# Stop all containers (preserves data)
docker-compose stop

# Stop and remove containers (keeps volumes)
docker-compose down

# Stop and remove everything including data
docker-compose down -v
```

## 🔧 Troubleshooting

### Service won't start

```bash
# Check logs
docker-compose logs agent-api

# Restart specific service
docker-compose restart agent-api

# Rebuild if needed
docker-compose up -d --build agent-api
```

### API returns 503

```bash
# Check if agents initialized
curl http://localhost:8000/api/v1/health

# If data_available is false, check data files exist
ls -la data/
```

### n8n workflow fails

1. Check agent API is running: `curl http://localhost:8000/api/v1/health`
2. Check logs: `docker-compose logs n8n`
3. Verify workflow uses correct hostname: `http://agent-api:8000` (inside Docker network)

## 📁 Project Structure

```
flow-optimize/
├── src/
│   ├── api/
│   │   ├── agent_api.py          # FastAPI server
│   │   └── webhooks.py           # Webhook endpoints
│   ├── agents/                   # Multi-agent system
│   └── simulation/               # OPC UA simulation
├── n8n_workflows/
│   └── main_control_loop.json    # Main workflow template
├── sql/
│   └── init.sql                  # Database schema
├── docker-compose.yml            # Docker services
├── Dockerfile                # API container
├── requirements.txt              # Python dependencies
├── requirements-api.txt          # API-specific dependencies
├── start_n8n_system.sh          # Startup script
└── test_n8n_integration.py      # Integration tests
```

## 🎓 Next Steps

1. **Read full documentation:** [N8N_INTEGRATION.md](N8N_INTEGRATION.md)
2. **Create custom workflows:** Use n8n UI to build your own
3. **Connect to OPC UA:** See [README.md](README.md) for live mode
4. **Add alerting:** Configure Slack/email in n8n
5. **Optimize agents:** Tune parameters in agent code

## 💡 Example Use Cases

### 1. Scheduled Control Loop
Run agents every 15 minutes automatically (already in template)

### 2. Price-Triggered Optimization
Webhook triggers cost optimization when price drops >30%

### 3. Emergency Response
OPC UA alarm triggers immediate reassessment with CRITICAL priority

### 4. Manual Override
Operator requests recommendation via webhook, reviews before executing

## 🤝 Integration Options

### Option A: Full Docker Stack (Recommended for Demo)
```bash
./start_n8n_system.sh
# Everything runs in containers, managed by n8n
```

### Option B: Hybrid (API + Original Script)
```bash
# Terminal 1: Start API server
python src/api/agent_api.py

# Terminal 2: Run original backtest
python src/agents/run_multi_agent.py --mode backtest --steps 96
```

### Option C: Standalone (Original System)
```bash
# Run without n8n
python src/agents/run_multi_agent.py --mode backtest --steps 96
```

## 📞 Support

- **API Issues:** Check http://localhost:8000/docs
- **n8n Issues:** Check n8n execution logs in UI
- **Database Issues:** Check PostgreSQL logs

## ✅ Checklist

Before the hackathon demo:

- [ ] `.env` configured with valid Gemini API key
- [ ] All services start successfully
- [ ] Integration tests pass (15/15)
- [ ] n8n workflow imported and activated
- [ ] Can view decision history
- [ ] Dashboards accessible (Grafana)

---

**Built for Junction 2025 Hackathon** | **Valmet × HSY Challenge**
