# 🎯 Frontend Request-Response Integration - Quick Start

## ✅ **What's Done**

Created a **webhook-based workflow** where your frontend sends a request and gets the decision data back immediately.

---

## 🔄 **Simple Flow**

```
Frontend clicks button
    ↓
POST http://localhost:5678/webhook/wastewater-decision
    ↓
n8n runs workflow (2-5 seconds)
    ↓
Returns JSON response with decision data
    ↓
Frontend displays results
```

---

## 🚀 **Quick Start (3 Steps)**

### **Step 1: Import Workflow**
1. Open n8n: http://localhost:5678
2. Import file: `n8n_workflows/webhook_workflow.json`
3. Click "Save" and **Activate** (toggle switch)

### **Step 2: Test with curl**
```bash
curl -X POST http://localhost:5678/webhook/wastewater-decision \
  -H "Content-Type: application/json" \
  -d '{}'
```

### **Step 3: Use in Frontend**
```javascript
// React/Vue/JavaScript
const response = await fetch('http://localhost:5678/webhook/wastewater-decision', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({})
});

const decision = await response.json();
console.log('AI Decision:', decision);
```

---

## 📊 **Response You'll Get**

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

## 💻 **Frontend Code**

### **Minimal Example:**
```html
<button onclick="getDecision()">Get AI Decision</button>
<div id="result"></div>

<script>
async function getDecision() {
  const res = await fetch('http://localhost:5678/webhook/wastewater-decision', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: '{}'
  });

  const decision = await res.json();

  document.getElementById('result').innerHTML = `
    <h3>Decision</h3>
    <p>Pumps: ${decision.pumps_active}</p>
    <p>Power: ${decision.total_power_kw} kW</p>
    <p>Cost: €${decision.cost_eur_per_15min}</p>
  `;
}
</script>
```

---

## 📁 **Files**

| File | Description |
|------|-------------|
| [webhook_workflow.json](n8n_workflows/webhook_workflow.json) | n8n workflow (import this) |
| [WEBHOOK_API_GUIDE.md](WEBHOOK_API_GUIDE.md) | Complete documentation |
| [FRONTEND_REQUEST_RESPONSE.md](FRONTEND_REQUEST_RESPONSE.md) | This quick start |

---

## ⚡ **Key Features**

✅ **Synchronous**: Frontend waits for response
✅ **Fast**: 2-5 seconds response time
✅ **Complete**: All evaluation metrics included
✅ **CORS Enabled**: Works from browser
✅ **Simple**: Just POST to webhook URL

---

## 🎬 **Demo Flow**

1. User clicks "Get Decision" button
2. Frontend shows loading spinner
3. Calls webhook (takes 2-5 seconds)
4. Receives AI decision with metrics
5. Updates dashboard with results

---

## 🔗 **URLs**

**Webhook Endpoint:**
```
http://localhost:5678/webhook/wastewater-decision
```

**n8n Dashboard:**
```
http://localhost:5678
Login: admin / hackathon2025
```

---

## ✅ **Ready!**

Your frontend can now:
- ✅ Trigger AI decisions on demand
- ✅ Get instant responses with full metrics
- ✅ Display real-time results to users

**See [WEBHOOK_API_GUIDE.md](WEBHOOK_API_GUIDE.md) for complete examples in React, Vue, Python, etc.** 🚀
