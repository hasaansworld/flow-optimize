# 🎨 Frontend UI Integration

## ✅ **What's Been Added**

A new node "**Send to Frontend UI**" has been added to the n8n workflow to push decision data to your frontend dashboard.

---

## 🔄 **Updated Workflow**

### **New Flow:**
```
Manual Trigger
    ↓
Get Current State
    ↓
Run Multi-Agent Decision
    ↓
Format Decision Summary
    ↓
Send to Frontend UI  ← NEW!
```

---

## 📊 **Data Sent to Frontend**

The workflow sends the **formatted decision summary** with all evaluation metrics:

```json
{
  "status": "Decision Complete",
  "timestamp": "2024-11-30T23:45:00",
  "priority": "MEDIUM",
  "reasoning": "Water level stable at 1.82m...",

  "pumps_active": 1,
  "total_flow_m3h": 3183.48,
  "total_power_kw": 349.49,
  "energy_kwh_per_15min": 87.37,
  "cost_eur_per_15min": 12.23,
  "specific_energy_kwh_m3": 0.1098,
  "violations": 0,
  "confidence": 0.87
}
```

---

## 🔧 **Configuration**

### **Default Settings (in workflow):**
- **URL**: `http://frontend:3001/api/decisions`
- **Method**: POST
- **Content-Type**: application/json
- **Timeout**: 10 seconds
- **Continue on Fail**: Yes (won't break workflow if frontend is down)

### **To Update URL:**

#### **Option 1: Edit in n8n UI**
1. Open n8n: http://localhost:5678
2. Open workflow: "Multi-Agent Demo - Ready to Use"
3. Click "Send to Frontend UI" node
4. Update the URL field
5. Save workflow

#### **Option 2: Edit JSON directly**
Edit [n8n_workflows/demo_ready_workflow.json](n8n_workflows/demo_ready_workflow.json:104):
```json
{
  "parameters": {
    "url": "http://your-frontend-url:port/api/endpoint"
  }
}
```

---

## 🏗️ **Frontend Setup Guide**

### **What Your Frontend Needs:**

#### **1. HTTP Endpoint to Receive Data**

**Express.js Example:**
```javascript
// server.js
const express = require('express');
const app = express();

app.use(express.json());

// Endpoint to receive decision data from n8n
app.post('/api/decisions', (req, res) => {
  const decision = req.body;

  console.log('📊 Received decision:', {
    timestamp: decision.timestamp,
    pumps_active: decision.pumps_active,
    cost: decision.cost_eur_per_15min,
    violations: decision.violations
  });

  // Store in database, update UI, emit to websocket clients, etc.
  // ... your logic here

  res.status(200).json({ success: true, message: 'Decision received' });
});

app.listen(3001, () => {
  console.log('Frontend API listening on port 3001');
});
```

**FastAPI Example (Python):**
```python
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Decision(BaseModel):
    status: str
    timestamp: str
    priority: str
    reasoning: str
    pumps_active: int
    total_flow_m3h: float
    total_power_kw: float
    energy_kwh_per_15min: float
    cost_eur_per_15min: float
    specific_energy_kwh_m3: float
    violations: int
    confidence: float

@app.post("/api/decisions")
async def receive_decision(decision: Decision):
    print(f"📊 Received decision: {decision.timestamp}")

    # Store in DB, broadcast to websocket clients, etc.
    # ... your logic here

    return {"success": True, "message": "Decision received"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)
```

#### **2. Add to Docker Compose (Optional)**

Edit [docker-compose.yml](docker-compose.yml):
```yaml
services:
  # ... existing services

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: wastewater-frontend
    ports:
      - "3001:3001"
    environment:
      - NODE_ENV=production
      - API_URL=http://agent-api:8000
    volumes:
      - ./frontend:/app
    networks:
      - wastewater-network
    depends_on:
      - agent-api
      - n8n
```

---

## 🧪 **Testing**

### **Test 1: Verify Workflow Updated**
```bash
# Check workflow includes new node
cat n8n_workflows/demo_ready_workflow.json | grep "Send to Frontend"
```

### **Test 2: Mock Frontend Endpoint**

Create a simple test server:
```bash
# Create test server
cat > /tmp/mock_frontend.py << 'EOF'
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/decisions', methods=['POST'])
def receive_decision():
    data = request.json
    print("\n" + "="*60)
    print("📊 RECEIVED DECISION FROM N8N")
    print("="*60)
    print(f"Timestamp: {data.get('timestamp')}")
    print(f"Pumps Active: {data.get('pumps_active')}")
    print(f"Power: {data.get('total_power_kw')} kW")
    print(f"Cost: €{data.get('cost_eur_per_15min')}")
    print(f"Violations: {data.get('violations')}")
    print("="*60 + "\n")
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3001)
EOF

# Run test server
python3 /tmp/mock_frontend.py
```

Then in n8n:
1. Update "Send to Frontend UI" URL to `http://host.docker.internal:3001/api/decisions`
2. Run workflow
3. Check terminal for received data

### **Test 3: Send Test Data Directly**

```bash
# Send sample decision data to your frontend
curl -X POST http://localhost:3001/api/decisions \
  -H "Content-Type: application/json" \
  -d '{
    "status": "Decision Complete",
    "timestamp": "2024-11-30T23:45:00",
    "priority": "MEDIUM",
    "reasoning": "Test decision",
    "pumps_active": 1,
    "total_flow_m3h": 3183.48,
    "total_power_kw": 349.49,
    "energy_kwh_per_15min": 87.37,
    "cost_eur_per_15min": 12.23,
    "specific_energy_kwh_m3": 0.1098,
    "violations": 0,
    "confidence": 0.87
  }'
```

---

## 📡 **Data Flow**

```
┌─────────────────────────────────────────────────────────────┐
│                     N8N WORKFLOW                            │
│                                                             │
│  1. Manual Trigger                                          │
│  2. Get Current State (from historical data)                │
│  3. Run Multi-Agent Decision (7 AI agents)                  │
│  4. Format Decision Summary (clean metrics)                 │
│  5. Send to Frontend UI ← POST with JSON                    │
│                                                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ HTTP POST
                       │ Content-Type: application/json
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                  FRONTEND API                               │
│                                                             │
│  POST /api/decisions                                        │
│                                                             │
│  Receives:                                                  │
│  - Decision timestamp                                       │
│  - Pump commands & metrics                                  │
│  - Cost calculation                                         │
│  - Safety violations                                        │
│  - AI reasoning                                             │
│                                                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Your Implementation
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              FRONTEND ACTIONS                               │
│                                                             │
│  - Store in database                                        │
│  - Update dashboard UI                                      │
│  - Broadcast via WebSocket                                  │
│  - Show real-time alerts                                    │
│  - Display charts/graphs                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎨 **Frontend Dashboard Ideas**

### **Metrics to Display:**
- **Real-time Pump Status**: Which pumps are running
- **Power Consumption**: Live kW reading
- **Cost Counter**: Running total in EUR
- **Water Level Graph**: Trend over time
- **Efficiency Metric**: kWh/m³ gauge
- **Violations Alert**: Red banner if > 0
- **AI Reasoning**: Show latest decision reasoning

### **Visualization Examples:**
```
┌─────────────────────────────────────────────────────────┐
│  Wastewater Pumping Dashboard                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  🟢 System Status: OPERATIONAL                          │
│                                                         │
│  Active Pumps: 1                                        │
│  Power: 349.49 kW                                       │
│  Cost (15min): €12.23                                   │
│  Efficiency: 0.11 kWh/m³ ⭐                             │
│  Violations: 0 ✅                                       │
│                                                         │
│  ┌─────────────────────────────────────────┐            │
│  │  Water Level (Last Hour)                │            │
│  │                                         │            │
│  │   📈 [Line chart showing L1 trend]      │            │
│  │                                         │            │
│  └─────────────────────────────────────────┘            │
│                                                         │
│  Latest AI Decision:                                    │
│  "Water level stable at 1.82m. Single large           │
│   pump operation recommended for efficiency..."        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## ⚙️ **Configuration Options**

### **In Workflow Node:**
- **URL**: Where to send data
- **Timeout**: How long to wait (default: 10s)
- **Continue on Fail**: Yes (recommended - won't break workflow if frontend is down)
- **Retry on Fail**: Can enable for reliability

### **Headers (Optional):**
Add authentication if needed:
```json
{
  "headers": {
    "Authorization": "Bearer your-token-here",
    "X-API-Key": "your-api-key"
  }
}
```

---

## 🚨 **Error Handling**

The node is configured with `continueOnFail: true`, meaning:
- ✅ Workflow continues even if frontend is unavailable
- ✅ Error is logged but not shown to user
- ✅ Decision still completes successfully

**To see errors:**
1. Open n8n workflow execution
2. Click "Send to Frontend UI" node
3. Check "Error" tab

---

## 📝 **Environment Variables**

Added to [.env.example](.env.example:40-42):
```bash
# Frontend UI Configuration
FRONTEND_URL=http://frontend:3001
FRONTEND_API_ENDPOINT=/api/decisions
```

Update your `.env`:
```bash
cp .env.example .env
# Edit FRONTEND_URL to match your frontend deployment
```

---

## 🔄 **When Frontend is Ready**

### **Step 1: Deploy Frontend**
```bash
cd frontend
docker-compose up -d
# Or: npm start, python app.py, etc.
```

### **Step 2: Update Workflow URL**
In n8n:
1. Open workflow
2. Click "Send to Frontend UI" node
3. Update URL to: `http://frontend:3001/api/decisions`
   - Docker: `http://frontend:3001/api/decisions`
   - Local: `http://localhost:3001/api/decisions`
   - Cloud: `https://your-frontend.com/api/decisions`

### **Step 3: Test**
```bash
# Run workflow in n8n
# Check frontend logs for received data
docker logs wastewater-frontend --tail 50
```

---

## 📊 **Example: React Frontend Integration**

```javascript
// React component to display decisions
import React, { useEffect, useState } from 'react';

function DecisionDashboard() {
  const [latestDecision, setLatestDecision] = useState(null);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    // Connect to your backend that receives n8n data
    const ws = new WebSocket('ws://localhost:3001/ws');

    ws.onmessage = (event) => {
      const decision = JSON.parse(event.data);
      setLatestDecision(decision);
      setHistory(prev => [decision, ...prev].slice(0, 10));
    };

    return () => ws.close();
  }, []);

  if (!latestDecision) return <div>Waiting for decisions...</div>;

  return (
    <div className="dashboard">
      <h1>AI Wastewater Control</h1>

      <div className="metrics">
        <div className="metric">
          <h3>Active Pumps</h3>
          <p className="value">{latestDecision.pumps_active}</p>
        </div>

        <div className="metric">
          <h3>Power</h3>
          <p className="value">{latestDecision.total_power_kw.toFixed(1)} kW</p>
        </div>

        <div className="metric">
          <h3>Cost (15min)</h3>
          <p className="value">€{latestDecision.cost_eur_per_15min.toFixed(2)}</p>
        </div>

        <div className="metric">
          <h3>Violations</h3>
          <p className={latestDecision.violations === 0 ? 'safe' : 'danger'}>
            {latestDecision.violations}
          </p>
        </div>
      </div>

      <div className="reasoning">
        <h3>AI Reasoning</h3>
        <p>{latestDecision.reasoning}</p>
      </div>
    </div>
  );
}

export default DecisionDashboard;
```

---

## ✅ **Summary**

**What's Ready:**
- ✅ n8n workflow sends data to frontend
- ✅ Full evaluation metrics included
- ✅ Configurable URL
- ✅ Error handling (continues on fail)
- ✅ Documentation complete

**When Frontend is Built:**
- Update URL in workflow node
- Deploy frontend with POST /api/decisions endpoint
- Test end-to-end flow

**For Now:**
- Workflow is ready to send data
- URL is placeholder: `http://frontend:3001/api/decisions`
- Change URL when frontend is deployed

---

**Your n8n workflow is ready to push data to any frontend!** 🚀
