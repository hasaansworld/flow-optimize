# n8n Integration Guide

## 🎯 Overview

This guide explains how to use **n8n** (workflow automation) to orchestrate your multi-agent wastewater pumping system.

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│            n8n Workflows                │
│  (Visual workflow orchestration)        │
│  - Schedule-based triggers              │
│  - Webhook triggers                     │
│  - Error handling                       │
│  - Monitoring & alerting                │
└─────────────┬───────────────────────────┘
              │
              ↓ HTTP API Calls
┌─────────────────────────────────────────┐
│        FastAPI Server (Port 8000)       │
│  - Agent endpoints                      │
│  - Webhook receivers                    │
│  - State management                     │
└─────────────┬───────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────┐
│      Multi-Agent System (Python)        │
│  - 6 Specialist Agents                  │
│  - 1 Coordinator Agent                  │
│  - LSTM Forecasting                     │
│  - Gemini LLM Reasoning                 │
└─────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Start All Services

```bash
# Make sure .env is configured
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Start all services with Docker Compose
docker-compose up -d

# Check status
docker-compose ps
```

**Services running:**
- FastAPI Agent Server: http://localhost:8000
- n8n Workflow UI: http://localhost:5678 (admin/hackathon2025)
- PostgreSQL Database: localhost:5432
- Redis Cache: localhost:6379
- Grafana Dashboard: http://localhost:3000 (admin/hackathon2025)

### 2. Access n8n UI

1. Open http://localhost:5678
2. Login with credentials from `.env` (default: admin/hackathon2025)
3. Import workflow from `n8n_workflows/main_control_loop.json`

### 3. Test the API

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Get current state
curl http://localhost:8000/api/v1/state/current

# Run full decision cycle
curl -X POST http://localhost:8000/api/v1/synthesize \
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

## 📡 API Endpoints

### Agent Assessment Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/assess/inflow` | POST | Inflow Forecasting Agent |
| `/api/v1/assess/cost` | POST | Energy Cost Agent |
| `/api/v1/assess/efficiency` | POST | Pump Efficiency Agent |
| `/api/v1/assess/safety` | POST | Water Level Safety Agent |
| `/api/v1/assess/smoothness` | POST | Flow Smoothness Agent |
| `/api/v1/assess/compliance` | POST | Constraint Compliance Agent |
| `/api/v1/assess/all` | POST | Run all agents in parallel |

### Decision Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/synthesize` | POST | Complete decision cycle (all agents + coordinator) |
| `/api/v1/state/current` | GET | Get current system state |
| `/api/v1/metrics` | GET | Get system metrics |
| `/api/v1/decisions/history` | GET | Get decision history |

### Webhook Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/webhooks/price_alert` | POST | Electricity price change trigger |
| `/webhooks/opcua_event` | POST | OPC UA server event trigger |
| `/webhooks/emergency` | POST | Emergency override trigger |
| `/webhooks/manual_decision` | POST | Manual decision request |

## 🔄 n8n Workflows

### Main Control Loop

**File:** `n8n_workflows/main_control_loop.json`

**Workflow:**
1. **Schedule Trigger** - Every 15 minutes
2. **Get Current State** - Fetch system state from API
3. **Run Multi-Agent Decision** - Call `/api/v1/synthesize`
4. **Check Priority** - If CRITICAL, send alert
5. **Log to Database** - Store decision in PostgreSQL
6. **Format Response** - Return structured result

**How to import:**
1. Open n8n UI (http://localhost:5678)
2. Click "Import from File"
3. Select `n8n_workflows/main_control_loop.json`
4. Activate the workflow

### Creating Custom Workflows

Example: Price Alert Workflow

```json
{
  "nodes": [
    {
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "webhookId": "price-alert"
    },
    {
      "name": "HTTP Request",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://agent-api:8000/webhooks/price_alert",
        "method": "POST"
      }
    }
  ]
}
```

## 🎨 Visual Workflow Examples

### Example 1: Scheduled Control Loop

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Schedule   │───▶│  Get State   │───▶│   Synthesize │
│  Every 15min │    │  (HTTP GET)  │    │  (HTTP POST) │
└──────────────┘    └──────────────┘    └──────┬───────┘
                                               │
                                               ▼
                    ┌──────────────┐    ┌──────────────┐
                    │ Log Decision │◀───│ Check Alert  │
                    │  (Postgres)  │    │  (IF Node)   │
                    └──────────────┘    └──────────────┘
```

### Example 2: Emergency Response

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Webhook    │───▶│ Emergency    │───▶│   Reassess   │
│ OPC UA Event │    │   Filter     │    │  All Agents  │
└──────────────┘    └──────────────┘    └──────┬───────┘
                                               │
                                               ▼
                    ┌──────────────┐    ┌──────────────┐
                    │ Send Slack   │◀───│   Execute    │
                    │    Alert     │    │   Commands   │
                    └──────────────┘    └──────────────┘
```

## 🧪 Testing

### Run Local API Server

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-api.txt

# Run the API server
python src/api/agent_api.py
```

### Test Individual Agents

```bash
# Test inflow agent
curl -X POST http://localhost:8000/api/v1/assess/inflow \
  -H "Content-Type: application/json" \
  -d @test_state.json

# Test all agents
curl -X POST http://localhost:8000/api/v1/assess/all \
  -H "Content-Type: application/json" \
  -d @test_state.json
```

### Test Webhooks

```bash
# Price alert webhook
curl -X POST http://localhost:8000/webhooks/price_alert \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2025-01-15T10:00:00",
    "new_price": 0.08,
    "old_price": 0.05,
    "change_percent": 60.0,
    "scenario": "high"
  }'

# Emergency webhook
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

### View Metrics

```bash
# System metrics
curl http://localhost:8000/api/v1/metrics

# Decision history
curl http://localhost:8000/api/v1/decisions/history?limit=10
```

### Database Queries

```sql
-- Connect to PostgreSQL
docker exec -it wastewater-postgres psql -U wastewater -d wastewater_decisions

-- View recent decisions
SELECT timestamp, priority, estimated_cost, confidence
FROM decisions
ORDER BY timestamp DESC
LIMIT 10;

-- Agent performance
SELECT * FROM agent_performance;

-- Hourly decision summary
SELECT * FROM decision_performance
ORDER BY hour DESC
LIMIT 24;
```

### Grafana Dashboards

1. Open http://localhost:3000
2. Login (admin/hackathon2025)
3. Import dashboard from `grafana/dashboards/`
4. View real-time metrics:
   - Decision count
   - Water level trends
   - Energy cost
   - Agent confidence

## 🔧 Configuration

### Environment Variables

```bash
# .env file
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
PRICE_SCENARIO=normal
API_PORT=8000

# n8n
N8N_USER=admin
N8N_PASSWORD=hackathon2025

# Database
POSTGRES_USER=wastewater
POSTGRES_PASSWORD=hackathon2025
POSTGRES_DB=wastewater_decisions

# Grafana
GRAFANA_USER=admin
GRAFANA_PASSWORD=hackathon2025
```

## 🎯 Use Cases

### 1. Scheduled Optimization
- **Trigger:** Cron schedule (every 15 minutes)
- **Action:** Run full decision cycle
- **Output:** Pump commands logged to database

### 2. Price Alert Response
- **Trigger:** Webhook from electricity price API
- **Action:** Reassess cost optimization
- **Output:** Adjust pumping strategy if beneficial

### 3. Emergency Override
- **Trigger:** OPC UA alarm or manual webhook
- **Action:** Emergency reassessment with CRITICAL priority
- **Output:** Immediate pump commands + Slack alert

### 4. Human-in-the-Loop
- **Trigger:** Manual webhook from operator
- **Action:** Generate recommendation for review
- **Output:** Decision logged for operator approval

## 🚨 Error Handling

n8n provides built-in error handling:

1. **Retry Logic** - Automatic retries on API failures
2. **Error Branches** - Different paths for success/failure
3. **Alerting** - Send notifications on errors
4. **Logging** - All executions logged in n8n

Example error handling node:

```json
{
  "name": "Error Handler",
  "type": "n8n-nodes-base.errorTrigger",
  "parameters": {
    "errorMessage": "Agent API failed"
  }
}
```

## 📚 Resources

- **API Documentation:** http://localhost:8000/docs (FastAPI Swagger UI)
- **n8n Documentation:** https://docs.n8n.io/
- **Project README:** [README.md](README.md)
- **Multi-Agent Plan:** [MULTI_AGENT_PLAN.md](MULTI_AGENT_PLAN.md)

## 🤝 Integration with Existing System

The n8n integration works alongside your existing system:

```bash
# Option 1: Run via Docker (n8n orchestrated)
docker-compose up -d

# Option 2: Run original Python script (no n8n)
python src/agents/run_multi_agent.py --mode backtest --steps 96

# Option 3: Hybrid (API server + original script)
# Terminal 1: Start API
python src/api/agent_api.py

# Terminal 2: Run backtest
python src/agents/run_multi_agent.py --mode backtest
```

## 🎉 Benefits of n8n Integration

✅ **Visual Debugging** - See exactly where decisions fail
✅ **Flexible Routing** - Add conditional logic easily
✅ **External Integrations** - Connect to Slack, email, databases
✅ **Error Recovery** - Automatic retries and fallbacks
✅ **Monitoring** - Built-in execution history
✅ **Scalability** - Easy to add more agents or workflows
✅ **Collaboration** - Non-coders can modify workflows

---

**Built for Junction 2025 Hackathon** | **Valmet × HSY Challenge**
