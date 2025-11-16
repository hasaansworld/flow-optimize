# n8n Demo Guide - Simple Workflow

## 🎯 **Quick Demo Setup**

### **Step 1: Import Simple Workflow**

1. Open n8n UI: http://localhost:5678
2. Login: `admin` / `hackathon2025`
3. Click **"Import from File"**
4. Select: `n8n_workflows/simple_control_loop.json`
5. Click **"Activate"** toggle in top-right

---

## 📊 **Workflow Overview**

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Schedule   │───▶│  Get State   │───▶│  Synthesize  │
│  Every 15min │    │  (HTTP GET)  │    │  All Agents  │
└──────────────┘    └──────────────┘    └──────┬───────┘
                                               │
                                               ▼
                                        ┌──────────────┐
                                        │Check Critical│
                                        └──────┬───────┘
                                               │
                               ┌───────────────┴───────────────┐
                               ▼                               ▼
                        ┌─────────────┐              ┌──────────────┐
                        │Format ALERT │              │Format Normal │
                        │  (Critical) │              │  (Success)   │
                        └──────┬──────┘              └──────┬───────┘
                               │                            │
                               └────────────┬───────────────┘
                                            ▼
                                     ┌──────────────┐
                                     │Merge Results │
                                     └──────────────┘
```

---

## ✅ **What This Workflow Does**

### **Normal Decision (No Alert):**
```json
{
  "status": "success",
  "timestamp": "2024-11-30 23:45:00",
  "priority": "MEDIUM",
  "total_pumps_active": 2,
  "estimated_flow": 7500,
  "estimated_cost": 18.5,
  "confidence": 0.85,
  "summary": "Decision logged: 2 pumps active, flow 7500 m³/h, cost 18.5 EUR/h"
}
```

### **Critical Decision (Alert!):**
```json
{
  "alert_type": "CRITICAL",
  "timestamp": "2024-11-30 23:45:00",
  "confidence": 0.95,
  "estimated_cost": 45.2,
  "message": "🚨 CRITICAL DECISION\n\nTimestamp: 2024-11-30 23:45:00\nPriority: CRITICAL\nConfidence: 0.95\n\nReasoning:\nWater level at 7.8m approaching maximum. Safety agent triggered emergency protocol. All available pumps activated at maximum capacity to prevent overflow.\n\nEstimated Flow: 15000 m³/h\nEstimated Cost: 45.2 EUR/h\n\nActive Pumps: 5"
}
```

---

## 🧪 **Testing the Workflow**

### **Test 1: Manual Execution**

1. Click **"Execute Workflow"** button in n8n UI
2. Watch nodes light up as they execute
3. Check final output at "Merge Results" node
4. Should see decision summary

### **Test 2: View Execution History**

1. Click **"Executions"** tab in left sidebar
2. See list of all past executions
3. Click any execution to see details
4. Inspect data at each node

### **Test 3: Trigger Critical Alert**

Use webhook to force critical decision:

```bash
curl -X POST http://localhost:8000/webhooks/emergency \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2024-11-30T23:45:00",
    "emergency_type": "overflow",
    "current_L1": 7.8,
    "message": "Water level approaching maximum"
  }'
```

Then check n8n executions - should see critical alert formatted!

---

## 📺 **Demo Talking Points**

### **1. Show Visual Workflow**
"Here's our multi-agent system orchestrated visually in n8n. No code needed to modify the workflow."

### **2. Execute Manually**
*Click Execute Workflow button*
"Watch as it fetches current state, runs all 6 specialist agents plus coordinator, and makes a decision in real-time."

### **3. Show Output**
*Click on Merge Results node*
"Here we see the final decision: 2 pumps active, 7500 m³/h flow, costing 18.5 EUR/h with 85% confidence."

### **4. Show Critical Path**
*Point to branching after Check if Critical*
"If priority is CRITICAL - like overflow risk - it takes the top path and formats an alert. Otherwise, normal path."

### **5. Show Execution History**
*Click Executions tab*
"Every decision is logged automatically. We can audit any past decision and see exactly what each agent recommended."

### **6. Show Agent API**
*Open http://localhost:8000/docs in browser*
"The workflow calls our FastAPI server which runs the Python multi-agent system. All agents exposed as REST endpoints."

---

## 🎨 **Customization Examples**

### **Add Email Notification**

After "Format Critical Alert" node, add:

1. Click **"+"** button
2. Search **"Send Email"**
3. Configure:
   - **To:** your-email@example.com
   - **Subject:** `🚨 Critical: Wastewater System Alert`
   - **Message:** `={{ $json.message }}`

### **Add Database Logging**

After "Merge Results" node, add:

1. Click **"+"** button
2. Search **"Postgres"**
3. Configure connection to `postgres:5432`
4. Insert decision data

### **Add Webhook Trigger**

Instead of schedule, use webhook:

1. Replace "Schedule Every 15min" with **"Webhook"** node
2. Get webhook URL from n8n
3. External systems can trigger: `POST https://your-n8n.com/webhook/abc123`

---

## 🔍 **Debugging Tips**

### **If workflow fails:**

1. **Check node that failed**
   - Red node = error
   - Click to see error message

2. **Check API is running**
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

3. **Check Docker network**
   ```bash
   docker exec wastewater-n8n ping agent-api
   ```

4. **View container logs**
   ```bash
   docker-compose logs agent-api
   docker-compose logs n8n
   ```

### **Common Issues:**

| Issue | Fix |
|-------|-----|
| "Service refused connection" | Change URL to `http://agent-api:8000` |
| "Service not initialized" | Wait 30s for agent startup |
| "No data available" | Check `assets/` directory mounted |
| "Gemini API error" | Check `GEMINI_API_KEY` in `.env` |

---

## 📊 **Viewing Results**

### **Option 1: n8n Execution Details**
- Click on any past execution
- See input/output of each node
- Debug failed executions

### **Option 2: API Direct Call**
```bash
# Get decision history
curl http://localhost:8000/api/v1/decisions/history?limit=10

# Get system metrics
curl http://localhost:8000/api/v1/metrics
```

### **Option 3: PostgreSQL**
```bash
docker exec -it wastewater-postgres psql -U wastewater -d wastewater_decisions

SELECT timestamp, priority, estimated_cost, confidence
FROM decisions
ORDER BY timestamp DESC
LIMIT 10;
```

### **Option 4: Grafana** (if configured)
- Open http://localhost:3000
- Login: `admin` / `hackathon2025`
- View dashboards with charts

---

## 🎯 **Key Demo Messages**

✅ **Multi-Agent AI** - 6 specialist agents + 1 coordinator using Gemini LLM
✅ **Visual Orchestration** - n8n workflows instead of hard-coded Python
✅ **Event-Driven** - Responds to schedules, webhooks, manual triggers
✅ **Production-Ready** - Docker containers, health checks, logging
✅ **Easy to Extend** - Add nodes without coding
✅ **Real-Time Decision Making** - Sub-second response
✅ **Explainable AI** - See reasoning from every agent

---

## 🚀 **Next Steps After Demo**

Ideas to extend:
1. Add more triggers (OPC UA alarms, weather API)
2. Add notifications (Slack, email, SMS)
3. Add visualization (custom dashboard)
4. Add approval workflow (human-in-the-loop)
5. Add A/B testing (compare strategies)
6. Connect to real OPC UA server
7. Add machine learning optimization

---

**You're ready for the demo!** 🎉

The simple workflow shows:
- All agents working together
- Visual workflow execution
- Critical alert handling
- Decision logging

**No external services needed** - everything runs locally in Docker!

