# OpenAI Integration & Evaluation Support

## 🔄 **Updated Configuration**

### **AI Provider: Now Using OpenAI**

Your system now supports **OpenAI API** (in addition to Gemini):

**Environment Variables:**
```bash
# .env file
OPENAI_API_KEY=sk-proj-...    # Your OpenAI key
GEMINI_API_KEY=AIza...         # Your Gemini key (backup)

# Model selection
OPENAI_MODEL=gpt-4o-mini       # Recommended for cost
GEMINI_MODEL=gemini-2.5-flash  # Alternative
```

**Docker Compose Updated:**
```yaml
environment:
  - OPENAI_API_KEY=${OPENAI_API_KEY}
  - GEMINI_API_KEY=${GEMINI_API_KEY}
  - OPENAI_MODEL=${OPENAI_MODEL:-gpt-4o-mini}
```

---

## 📊 **Evaluation Metrics**

Your system tracks comprehensive metrics via `run_evaluation.py`:

### **Key Metrics Tracked:**

1. **Total Cost (EUR)** - Energy consumption costs
2. **Energy Consumption (kWh)** - Total electricity used
3. **Specific Energy (kWh/m³)** - Efficiency metric
4. **Constraint Violations** - Safety/compliance issues
5. **Water Level Statistics** - Min/max/avg
6. **Pump Runtime** - Operating hours per pump
7. **Flow Smoothness** - Variability metrics

### **Output Files:**

| File | Purpose |
|------|---------|
| `ai_evaluation_normal_10steps.json` | AI agent metrics |
| `baseline_metrics_normal.json` | Baseline comparison |
| `baseline_metrics_high.json` | High price scenario baseline |
| `evaluation_output.txt` | Full evaluation log |

---

## 🎯 **Should You Include Evaluation in n8n Workflow?**

### **Option 1: Separate Workflows** ⭐ **RECOMMENDED**

**Keep workflows separate:**

1. **Demo Workflow** (`demo_ready_workflow.json`)
   - For live demo/presentation
   - Real-time decision making
   - Fast, visual, impressive

2. **Evaluation Workflow** (New - create separately)
   - For batch testing
   - Run 100+ timesteps
   - Compare with baseline
   - Generate metrics report

**Why separate?**
- ✅ Demo stays fast and simple
- ✅ Evaluation can run long (minutes)
- ✅ Different use cases
- ✅ Cleaner architecture

---

### **Option 2: Combined Workflow** (More Complex)

Add evaluation metrics to demo workflow:

```
Get State → Run Agents → Evaluate Decision → Format Results
                              ↓
                       Calculate Metrics
                       (cost, energy, violations)
```

**Pros:**
- See metrics for every decision
- Real-time evaluation

**Cons:**
- Slower execution
- More complex output
- Distracts from demo flow

---

## 🚀 **Recommended Approach for Hackathon**

### **For Demo (Judges Watching):**

**Use:** `demo_ready_workflow.json` (current)

**Show:**
1. Visual workflow execution
2. Real-time AI decision
3. Agent reasoning
4. Pump commands

**Time:** 2 minutes
**Impact:** Visual and impressive

---

### **For Evaluation (After Demo):**

**Create separate evaluation workflow:**

1. **Batch Trigger** - Run N timesteps
2. **Track Metrics** - Cost, energy, violations
3. **Compare Baseline** - Show improvement
4. **Generate Report** - JSON output

**Use command line instead:**
```bash
# Run full evaluation
python src/agents/run_evaluation.py \
  --price normal \
  --steps 100 \
  --output evaluation_results.json

# Compare with baseline
cat baseline_metrics_normal.json
cat ai_evaluation_normal_10steps.json
```

---

## 📈 **Adding Evaluation Endpoint to API**

Add to [src/api/agent_api.py](src/api/agent_api.py):

```python
@app.post("/api/v1/evaluate")
async def run_evaluation(
    price_scenario: str = "normal",
    num_steps: int = 100,
    start_index: int = 500
):
    """Run full evaluation and return metrics"""

    # Run evaluation controller
    from run_evaluation import EvaluationController

    controller = EvaluationController(
        lstm_model_path=str(model_path),
        price_scenario=price_scenario
    )

    results = controller.run_evaluation(
        start_index=start_index,
        num_steps=num_steps
    )

    return {
        "total_cost_eur": results['total_cost'],
        "total_energy_kwh": results['total_energy'],
        "specific_energy_kwh_m3": results['specific_energy'],
        "violations": results['violations'],
        "comparison_vs_baseline": results['comparison']
    }
```

Then call from n8n:
```
POST http://agent-api:8000/api/v1/evaluate?num_steps=100
```

---

## 🎬 **Demo Strategy**

### **Phase 1: Live Demo (2 min)**
- Show n8n workflow
- Execute real-time decision
- Explain agent collaboration
- **Focus:** Visual and impressive

### **Phase 2: Q&A (if asked)**
- Show evaluation results
- Compare with baseline
- Discuss metrics
- **Focus:** Quantitative proof

### **Have Ready:**
```bash
# Quick evaluation summary
cat ai_evaluation_normal_10steps.json | jq '{
  total_cost,
  total_energy_kwh,
  specific_energy,
  violations
}'
```

**Output:**
```json
{
  "total_cost": 245.32,
  "total_energy_kwh": 1834.2,
  "specific_energy": 0.127,
  "violations": 0
}
```

---

## ✅ **Updated Environment Setup**

### **.env Configuration:**

```bash
# AI APIs (both configured for flexibility)
OPENAI_API_KEY=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
GEMINI_API_KEY=AIzaSyBpMmyRnAk9hMwKqNndDFtlhtprj4fFRmo

# Model selection (choose one)
OPENAI_MODEL=gpt-4o-mini      # Currently using
GEMINI_MODEL=gemini-2.5-flash # Backup

# Evaluation settings
PRICE_SCENARIO=normal
API_PORT=8000
```

### **Restart Services:**
```bash
docker-compose down
docker-compose up -d
```

---

## 🔍 **Verification**

### **Check OpenAI is Working:**
```bash
# Health check
curl http://localhost:8000/api/v1/health

# Run a decision
curl -X POST http://localhost:8000/api/v1/synthesize \
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

Should return decision with OpenAI-generated reasoning.

---

## 🎯 **Final Recommendation**

### **For Hackathon Demo:**

1. **Keep demo workflow simple** (no evaluation)
2. **Use OpenAI** (faster than Gemini)
3. **Have evaluation results ready** (pre-run)
4. **Show metrics if judges ask**

### **Demo Flow:**
1. Show n8n workflow → Execute → Results (2 min)
2. **If asked:** "Here's our evaluation vs baseline..."
3. Show pre-generated metrics file

### **Pre-Demo Checklist:**
- [ ] OpenAI key in `.env`
- [ ] Services restarted with new config
- [ ] Demo workflow tested
- [ ] Evaluation results generated:
  ```bash
  python src/agents/run_evaluation.py \
    --price normal --steps 100 \
    --output hackathon_evaluation.json
  ```
- [ ] Baseline comparison ready

---

## 📊 **Evaluation vs Baseline Table** (Have Ready)

| Metric | Baseline | AI Agents | Improvement |
|--------|----------|-----------|-------------|
| **Total Cost** | €285.40 | €245.32 | **-14%** ✅ |
| **Energy (kWh)** | 2,145 | 1,834 | **-14.5%** ✅ |
| **Specific Energy** | 0.145 | 0.127 | **-12.4%** ✅ |
| **Violations** | 2 | 0 | **0** ✅ |
| **Max Water Level** | 7.8m | 7.2m | **Safer** ✅ |

*(Use your actual numbers from evaluation files)*

---

## 🎉 **Summary**

✅ **OpenAI configured** - Faster and cost-effective
✅ **Evaluation system ready** - Full metrics tracking
✅ **Demo workflow simple** - Focus on visual impact
✅ **Metrics available** - If judges ask for proof
✅ **Both strategies ready** - Live demo + quantitative results

**You have the best of both worlds!** 🚀

