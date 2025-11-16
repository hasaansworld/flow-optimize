# 🎯 Hackathon Demo - Quick Setup

## ⚡ **5-Minute Setup**

### **Step 1: Start Services**
```bash
cd /Users/saimakhtar/Work/flow-optimize

# Start all Docker containers
docker-compose up -d

# Wait 30 seconds for initialization
sleep 30

# Verify API is ready
curl http://localhost:8000/api/v1/health
```

### **Step 2: Import Workflow**
1. Open n8n: http://localhost:5678
2. Login: `admin` / `hackathon2025`
3. Click **"+ Add workflow"**
4. Click **"⋮"** menu → **"Import from File"**
5. Select: **`n8n_workflows/demo_ready_workflow.json`**
6. Workflow loads ✅

### **Step 3: Test It**
1. Click **"Test workflow"** button (top right)
2. Watch nodes execute (they'll light up green)
3. Click **"Format Decision Summary"** node
4. See the output! 🎉

---

## 📊 **What You'll See**

### **Output Format:**
```json
{
  "status": "Decision Complete",
  "timestamp": "2024-11-30 23:45:00",
  "priority": "MEDIUM",
  "reasoning": "Water level stable at 1.82m. Cost optimization suggests minimal pumping during current price period (13.607 EUR/kWh). Efficiency agent recommends 2-pump configuration...",
  "pumps_active": 2,
  "flow_m3h": 6980.35,
  "cost_eur_h": 18.45,
  "confidence": 0.87
}
```

---

## 🎬 **Demo Script (2 Minutes)**

### **1. Show the System** (30 sec)
"We built a multi-agent AI system for wastewater pumping optimization. Instead of traditional control methods, we use 7 autonomous AI agents that collaborate using Google Gemini LLM."

### **2. Show n8n Workflow** (30 sec)
*Open n8n*
"Here's the workflow orchestration in n8n. Four simple steps:
1. Get current system state from historical data
2. Call our multi-agent API
3. All 7 agents run in parallel and coordinator synthesizes
4. We get the final decision with reasoning"

### **3. Execute Live** (30 sec)
*Click Test Workflow*
"Let me run this live... watch the nodes execute... and here's the decision!"

*Click on Format Decision Summary node*

"The system decided to run 2 pumps at 6,980 m³/h, costing 18.45 EUR/hour. Confidence is 87%."

### **4. Show the Reasoning** (30 sec)
*Point to reasoning field*
"Here's the AI reasoning: Water level is stable, current electricity price is moderate, so it recommends cost-optimized pumping with 2 pumps. The coordinator considered inputs from:
- Inflow forecasting agent (LSTM neural network)
- Energy cost agent (price pattern analysis)
- Pump efficiency agent (optimal combinations)
- Safety agent (water level monitoring)
- Flow smoothness agent (prevent shock loading)
- Compliance agent (enforce constraints)"

---

## 🔧 **Troubleshooting**

### **Issue: Workflow fails**

**Check 1: Is API running?**
```bash
curl http://localhost:8000/api/v1/health
# Should return: {"status": "healthy", "agents_loaded": 6}
```

**Check 2: Are containers running?**
```bash
docker-compose ps
# Should show 4 containers: agent-api, n8n, postgres, grafana
```

**Check 3: View logs**
```bash
docker-compose logs agent-api | tail -50
# Should show: "✅ API Server ready!"
```

### **Issue: "Service refused connection"**

**Fix:** URL must be `http://agent-api:8000` (NOT localhost)

In workflow, check "Run Multi-Agent Decision" node:
- ✅ Correct: `http://agent-api:8000/api/v1/synthesize`
- ❌ Wrong: `http://localhost:8000/api/v1/synthesize`

---

## 📱 **Quick Reference**

| Service | URL | Credentials |
|---------|-----|-------------|
| **n8n UI** | http://localhost:5678 | admin / hackathon2025 |
| **API Docs** | http://localhost:8000/docs | None |
| **Grafana** | http://localhost:3000 | admin / hackathon2025 |
| **Postgres** | localhost:5432 | wastewater / hackathon2025 |

---

## 🎯 **Key Demo Points**

✅ **Multi-Agent AI** - 6 specialists + 1 coordinator
✅ **LLM-Powered** - Google Gemini 2.5 Flash for reasoning
✅ **LSTM Forecasting** - Neural network predicts inflow
✅ **Visual Orchestration** - n8n workflow instead of code
✅ **Real-Time Decisions** - Sub-second response
✅ **Explainable** - See reasoning from every agent
✅ **Production-Ready** - Docker, APIs, monitoring

---

## 🚀 **Advanced Demo (Optional)**

### **Show Individual Agents**

Call agents directly via API:

```bash
# Inflow forecasting agent
curl -X POST http://localhost:8000/api/v1/assess/inflow \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2024-11-30T23:45:00",
    "L1": 1.82,
    "V": 5405,
    "F1": 1708,
    "F2": 6980,
    "electricity_price": 0.14,
    "price_scenario": "normal",
    "current_index": 1535
  }'
```

### **Show Webhook Triggers**

Trigger emergency:
```bash
curl -X POST http://localhost:8000/webhooks/emergency \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2024-11-30T23:45:00",
    "emergency_type": "overflow",
    "current_L1": 7.8,
    "message": "Water level critical"
  }'
```

### **Show Database**

```bash
docker exec -it wastewater-postgres psql -U wastewater -d wastewater_decisions

# View decisions
SELECT timestamp, priority, estimated_cost
FROM decisions
ORDER BY timestamp DESC
LIMIT 5;
```

---

## ✅ **Pre-Demo Checklist**

Before the hackathon presentation:

- [ ] All services running (`docker-compose ps`)
- [ ] API health check passes (`curl localhost:8000/api/v1/health`)
- [ ] n8n accessible (http://localhost:5678)
- [ ] Workflow imported and tested
- [ ] Know the 2-minute demo script
- [ ] Have backup: API docs open (http://localhost:8000/docs)
- [ ] Optional: Grafana dashboard configured

---

## 🎉 **You're Ready!**

The demo workflow is:
- ✅ Zero external dependencies
- ✅ Works 100% offline
- ✅ No Slack/email setup needed
- ✅ Clean, simple output
- ✅ Easy to understand
- ✅ Impressive to judges

**Total demo time: 2 minutes**
**Setup time: 5 minutes**
**Impact: Maximum!** 🏆

Good luck at Junction 2025! 🚀

