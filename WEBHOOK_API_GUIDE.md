# 🎯 Webhook API - Frontend Request-Response Pattern

## ✅ **What's Built**

A **webhook-based workflow** where your frontend **triggers** the decision and **receives the response** synchronously.

---

## 🔄 **How It Works**

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (React/Vue/etc)                                   │
│                                                             │
│  User clicks "Get Decision" button                          │
│  ↓                                                          │
│  POST http://n8n:5678/webhook/wastewater-decision          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ HTTP POST Request
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  n8n Webhook Workflow                                       │
│                                                             │
│  1. Webhook Trigger (receives request)                      │
│  2. Get Current State                                       │
│  3. Run Multi-Agent Decision                                │
│  4. Format Decision Summary                                 │
│  5. Return Response to Frontend                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ HTTP Response (JSON)
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  Frontend Receives Data                                     │
│                                                             │
│  {                                                          │
│    "status": "Decision Complete",                           │
│    "pumps_active": 1,                                       │
│    "total_power_kw": 349.49,                                │
│    "cost_eur_per_15min": 12.23,                             │
│    ...                                                      │
│  }                                                          │
│                                                             │
│  ↓ Update Dashboard UI                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 **New Workflow File**

**File**: [n8n_workflows/webhook_workflow.json](n8n_workflows/webhook_workflow.json)

This is a **synchronous request-response** workflow:
- Frontend sends POST request
- n8n runs the decision workflow
- Frontend receives response with decision data

---

## 🚀 **Setup Instructions**

### **Step 1: Import Webhook Workflow**

1. Open n8n: http://localhost:5678
2. Login: `admin` / `hackathon2025`
3. Click **"+ Add workflow"**
4. Click **"⋮" menu** → **"Import from File"**
5. Select: `n8n_workflows/webhook_workflow.json`
6. Click **"Save"** (top right)
7. **Activate** the workflow (toggle switch at top)

### **Step 2: Get Webhook URL**

1. Click on **"Webhook Trigger"** node
2. Look for **"Production URL"**:
   ```
   http://localhost:5678/webhook/wastewater-decision
   ```
3. Copy this URL (you'll use it in your frontend)

### **Step 3: Test the Webhook**

```bash
# Test from command line
curl -X POST http://localhost:5678/webhook/wastewater-decision \
  -H "Content-Type: application/json" \
  -d '{}' | python3 -m json.tool
```

**Expected Response:**
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

## 💻 **Frontend Integration**

### **React Example:**

```javascript
import React, { useState } from 'react';

function DecisionButton() {
  const [decision, setDecision] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const getDecision = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:5678/webhook/wastewater-decision', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({}) // Empty body (workflow gets state from API)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setDecision(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="decision-panel">
      <button onClick={getDecision} disabled={loading}>
        {loading ? 'Running AI Decision...' : 'Get New Decision'}
      </button>

      {error && <div className="error">Error: {error}</div>}

      {decision && (
        <div className="decision-result">
          <h3>AI Decision</h3>
          <div className="metrics">
            <div className="metric">
              <label>Active Pumps:</label>
              <span>{decision.pumps_active}</span>
            </div>
            <div className="metric">
              <label>Power:</label>
              <span>{decision.total_power_kw.toFixed(1)} kW</span>
            </div>
            <div className="metric">
              <label>Cost (15min):</label>
              <span>€{decision.cost_eur_per_15min.toFixed(2)}</span>
            </div>
            <div className="metric">
              <label>Violations:</label>
              <span className={decision.violations === 0 ? 'safe' : 'warning'}>
                {decision.violations}
              </span>
            </div>
          </div>
          <div className="reasoning">
            <h4>AI Reasoning:</h4>
            <p>{decision.reasoning}</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default DecisionButton;
```

### **Vue Example:**

```vue
<template>
  <div class="decision-panel">
    <button @click="getDecision" :disabled="loading">
      {{ loading ? 'Running AI Decision...' : 'Get New Decision' }}
    </button>

    <div v-if="error" class="error">Error: {{ error }}</div>

    <div v-if="decision" class="decision-result">
      <h3>AI Decision</h3>
      <div class="metrics">
        <div class="metric">
          <label>Active Pumps:</label>
          <span>{{ decision.pumps_active }}</span>
        </div>
        <div class="metric">
          <label>Power:</label>
          <span>{{ decision.total_power_kw.toFixed(1) }} kW</span>
        </div>
        <div class="metric">
          <label>Cost (15min):</label>
          <span>€{{ decision.cost_eur_per_15min.toFixed(2) }}</span>
        </div>
        <div class="metric">
          <label>Violations:</label>
          <span :class="decision.violations === 0 ? 'safe' : 'warning'">
            {{ decision.violations }}
          </span>
        </div>
      </div>
      <div class="reasoning">
        <h4>AI Reasoning:</h4>
        <p>{{ decision.reasoning }}</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      decision: null,
      loading: false,
      error: null
    };
  },
  methods: {
    async getDecision() {
      this.loading = true;
      this.error = null;

      try {
        const response = await fetch('http://localhost:5678/webhook/wastewater-decision', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({})
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        this.decision = await response.json();
      } catch (err) {
        this.error = err.message;
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>
```

### **Vanilla JavaScript:**

```javascript
async function getDecision() {
  const button = document.getElementById('decision-btn');
  const resultDiv = document.getElementById('result');

  button.disabled = true;
  button.textContent = 'Running AI Decision...';

  try {
    const response = await fetch('http://localhost:5678/webhook/wastewater-decision', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({})
    });

    const decision = await response.json();

    resultDiv.innerHTML = `
      <h3>AI Decision</h3>
      <div class="metrics">
        <p><strong>Active Pumps:</strong> ${decision.pumps_active}</p>
        <p><strong>Power:</strong> ${decision.total_power_kw.toFixed(1)} kW</p>
        <p><strong>Cost (15min):</strong> €${decision.cost_eur_per_15min.toFixed(2)}</p>
        <p><strong>Violations:</strong> ${decision.violations}</p>
      </div>
      <div class="reasoning">
        <h4>AI Reasoning:</h4>
        <p>${decision.reasoning}</p>
      </div>
    `;
  } catch (error) {
    resultDiv.innerHTML = `<p class="error">Error: ${error.message}</p>`;
  } finally {
    button.disabled = false;
    button.textContent = 'Get New Decision';
  }
}
```

### **Python (Backend):**

```python
import requests

def get_ai_decision():
    """Call n8n webhook to get AI decision"""
    url = "http://localhost:5678/webhook/wastewater-decision"

    try:
        response = requests.post(
            url,
            json={},
            timeout=30
        )
        response.raise_for_status()

        decision = response.json()

        print(f"✅ Decision received:")
        print(f"  Pumps active: {decision['pumps_active']}")
        print(f"  Power: {decision['total_power_kw']:.1f} kW")
        print(f"  Cost: €{decision['cost_eur_per_15min']:.2f}")
        print(f"  Violations: {decision['violations']}")

        return decision

    except requests.exceptions.RequestException as e:
        print(f"❌ Error calling webhook: {e}")
        return None

# Usage
decision = get_ai_decision()
```

---

## 🔧 **Configuration**

### **Webhook Settings:**

| Setting | Value | Description |
|---------|-------|-------------|
| **Path** | `wastewater-decision` | URL path for webhook |
| **Method** | POST | HTTP method |
| **Response Mode** | lastNode | Returns data from last node |
| **CORS** | Enabled | Allows frontend cross-origin requests |

### **URLs:**

**Local Development:**
```
http://localhost:5678/webhook/wastewater-decision
```

**Docker Network (from other containers):**
```
http://n8n:5678/webhook/wastewater-decision
```

**Production (when deployed):**
```
https://your-domain.com/webhook/wastewater-decision
```

---

## ⚡ **Performance**

**Response Time:**
- Get Current State: ~50ms
- Run Multi-Agent Decision: ~2-5 seconds (LLM call)
- Total: **~2-5 seconds** per request

**Tip**: Show loading spinner in frontend during this time!

---

## 🧪 **Testing**

### **Test 1: Basic Call**
```bash
curl -X POST http://localhost:5678/webhook/wastewater-decision \
  -H "Content-Type: application/json" \
  -d '{}'
```

### **Test 2: Check Response Format**
```bash
curl -X POST http://localhost:5678/webhook/wastewater-decision \
  -H "Content-Type: application/json" \
  -d '{}' | python3 -c "
import sys, json
data = json.load(sys.stdin)
print('Status:', data.get('status'))
print('Pumps:', data.get('pumps_active'))
print('Cost:', data.get('cost_eur_per_15min'))
"
```

### **Test 3: Load Testing**
```bash
# Test multiple requests
for i in {1..5}; do
  echo "Request $i:"
  curl -X POST http://localhost:5678/webhook/wastewater-decision \
    -H "Content-Type: application/json" \
    -d '{}' -w "\nTime: %{time_total}s\n\n"
  sleep 1
done
```

---

## 🔒 **Security (Optional)**

### **Add Authentication:**

If you want to secure the webhook, you can add API key validation:

1. In n8n workflow, add an "IF" node after webhook:
   ```javascript
   // Check for API key in headers
   {{ $json.headers['x-api-key'] === 'your-secret-key' }}
   ```

2. In frontend:
   ```javascript
   fetch('http://localhost:5678/webhook/wastewater-decision', {
     method: 'POST',
     headers: {
       'Content-Type': 'application/json',
       'X-API-Key': 'your-secret-key'
     }
   })
   ```

---

## 📊 **Response Schema**

```typescript
interface DecisionResponse {
  status: string;              // "Decision Complete"
  timestamp: string;           // "2024-11-30T23:45:00"
  priority: string;            // "HIGH" | "MEDIUM" | "LOW"
  reasoning: string;           // AI explanation

  // Metrics
  pumps_active: number;        // Number of pumps running
  total_flow_m3h: number;      // Total flow rate (m³/h)
  total_power_kw: number;      // Power consumption (kW)
  energy_kwh_per_15min: number; // Energy used (kWh)
  cost_eur_per_15min: number;  // Cost (EUR)
  specific_energy_kwh_m3: number; // Efficiency (kWh/m³)
  violations: number;          // Safety violations count
  confidence: number;          // 0-1 confidence score
}
```

---

## 🎨 **Frontend Dashboard Example**

```html
<!DOCTYPE html>
<html>
<head>
  <title>Wastewater AI Control</title>
  <style>
    body { font-family: Arial, sans-serif; padding: 20px; }
    .container { max-width: 800px; margin: 0 auto; }
    button { padding: 15px 30px; font-size: 16px; cursor: pointer; }
    .metrics { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin: 20px 0; }
    .metric { padding: 15px; background: #f5f5f5; border-radius: 5px; }
    .metric label { font-weight: bold; display: block; margin-bottom: 5px; }
    .metric span { font-size: 24px; color: #007bff; }
    .safe { color: green; }
    .warning { color: red; }
    .reasoning { background: #f9f9f9; padding: 15px; border-left: 4px solid #007bff; }
  </style>
</head>
<body>
  <div class="container">
    <h1>🚰 Wastewater AI Control Dashboard</h1>

    <button id="decision-btn" onclick="getDecision()">
      Get New AI Decision
    </button>

    <div id="result"></div>
  </div>

  <script>
    async function getDecision() {
      const button = document.getElementById('decision-btn');
      const resultDiv = document.getElementById('result');

      button.disabled = true;
      button.textContent = 'Running AI Decision...';
      resultDiv.innerHTML = '<p>⏳ Processing...</p>';

      try {
        const response = await fetch('http://localhost:5678/webhook/wastewater-decision', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({})
        });

        const decision = await response.json();

        resultDiv.innerHTML = `
          <h3>✅ ${decision.status}</h3>
          <p><strong>Time:</strong> ${decision.timestamp}</p>
          <p><strong>Priority:</strong> ${decision.priority}</p>

          <div class="metrics">
            <div class="metric">
              <label>Active Pumps</label>
              <span>${decision.pumps_active}</span>
            </div>
            <div class="metric">
              <label>Power (kW)</label>
              <span>${decision.total_power_kw.toFixed(1)}</span>
            </div>
            <div class="metric">
              <label>Cost (15min)</label>
              <span>€${decision.cost_eur_per_15min.toFixed(2)}</span>
            </div>
            <div class="metric">
              <label>Violations</label>
              <span class="${decision.violations === 0 ? 'safe' : 'warning'}">
                ${decision.violations}
              </span>
            </div>
          </div>

          <div class="reasoning">
            <h4>AI Reasoning:</h4>
            <p>${decision.reasoning}</p>
          </div>
        `;
      } catch (error) {
        resultDiv.innerHTML = `<p class="error">❌ Error: ${error.message}</p>`;
      } finally {
        button.disabled = false;
        button.textContent = 'Get New AI Decision';
      }
    }
  </script>
</body>
</html>
```

Save as `test_dashboard.html` and open in browser!

---

## 🚀 **Deployment**

### **For Production:**

1. **Deploy n8n** (already in docker-compose.yml)
2. **Get production webhook URL**
3. **Update frontend** to use production URL
4. **Enable HTTPS** (recommended for production)

---

## ✅ **Summary**

**What You Have:**
- ✅ Webhook-based API at `/webhook/wastewater-decision`
- ✅ Frontend triggers workflow with POST request
- ✅ Receives complete decision data in response
- ✅ CORS enabled for frontend access
- ✅ Full evaluation metrics included

**Next Steps:**
1. Import `webhook_workflow.json` to n8n
2. Activate the workflow
3. Test with curl or browser
4. Integrate with your frontend

**Your frontend can now request decisions on-demand and get instant responses!** 🎉
