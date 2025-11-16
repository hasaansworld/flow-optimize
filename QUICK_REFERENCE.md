# 🚀 Quick Reference - n8n Workflow with Full Metrics

## ✅ **What's Done**

Your n8n workflow now outputs **complete evaluation metrics** matching [run_evaluation.py](src/agents/run_evaluation.py).

---

## 🎯 **Quick Test**

### **1. Test API:**
```bash
curl http://localhost:8000/api/v1/health
```

### **2. Test Full Decision:**
```bash
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
  }' | python3 -m json.tool
```

### **3. Test n8n Workflow:**
1. Open http://localhost:5678
2. Login: `admin` / `hackathon2025`
3. Import `n8n_workflows/demo_ready_workflow.json`
4. Click "Test workflow"
5. View "Format Decision Summary" output

---

## 📊 **New Metrics Available**

| Metric | Example Value | Where to See |
|--------|---------------|--------------|
| **flow_m3h** | 3183.48 m³/h | pump_commands[].flow_m3h |
| **power_kw** | 349.49 kW | pump_commands[].power_kw |
| **efficiency** | 0.846 (84.6%) | pump_commands[].efficiency |
| **total_power_kw** | 349.49 kW | cost_calculation.total_power_kw |
| **energy_consumed_kwh** | 87.37 kWh | cost_calculation.energy_consumed_kwh |
| **cost_eur** | €12.23 | cost_calculation.cost_eur |
| **specific_energy** | 0.1098 kWh/m³ | cost_calculation.specific_energy_kwh_per_m3 |
| **violations** | 0 | constraint_violations.length |

---

## 🎬 **Demo Script (90 seconds)**

### **[0-10s] Introduction:**
*"Our system uses 7 AI agents to optimize wastewater pumping. Let me show you a live decision..."*

### **[10-20s] Run Workflow:**
- Open n8n
- Click "Test workflow"
- Watch nodes execute

### **[20-40s] Show Decision:**
- Click "Format Decision Summary" node
- Read metrics:
  - "1 pump active"
  - "349 kW power"
  - "€12.23 cost per 15 minutes"
  - "3,183 m³/hour flow"
  - "Zero violations - perfectly safe"

### **[40-60s] Show Reasoning:**
- Point to "reasoning" field
- "The coordinator used OpenAI to synthesize 7 specialist recommendations"

### **[60-90s] Highlight Value:**
- "Same metrics as our evaluation system"
- "Real-time cost optimization"
- "Explainable AI - see every agent's reasoning"
- "Production-ready for HSY"

---

## 🆚 **Before vs After**

### **BEFORE:**
```json
{
  "pump_commands": [{"pump_id": "P1L", "start": true, "frequency": 47.8}],
  "estimated_flow_m3h": 0,  // ❌ No data
  "estimated_cost_eur_per_hour": 0  // ❌ No data
}
```

### **AFTER:**
```json
{
  "pump_commands": [{
    "pump_id": "P1L",
    "flow_m3h": 3183.48,     // ✅ Real
    "power_kw": 349.49,      // ✅ Real
    "efficiency": 0.846      // ✅ Real
  }],
  "cost_calculation": {
    "cost_eur": 12.23,       // ✅ Real
    "specific_energy": 0.11  // ✅ Real
  }
}
```

---

## 📁 **Key Files**

| File | Purpose |
|------|---------|
| [src/api/agent_api.py](src/api/agent_api.py) | Enhanced API with pump metrics |
| [n8n_workflows/demo_ready_workflow.json](n8n_workflows/demo_ready_workflow.json) | Updated workflow |
| [CHANGES_SUMMARY.md](CHANGES_SUMMARY.md) | Complete technical summary |
| [N8N_WORKFLOW_OUTPUT_EXAMPLE.md](N8N_WORKFLOW_OUTPUT_EXAMPLE.md) | Example output |

---

## 🔧 **Troubleshooting**

### **Issue: API not responding**
```bash
docker-compose restart agent-api
docker logs wastewater-agent-api --tail 50
```

### **Issue: Workflow fails**
1. Check API health: `curl http://localhost:8000/api/v1/health`
2. Check container logs: `docker-compose logs agent-api`
3. Verify URL in workflow: `http://agent-api:8000` (NOT localhost)

### **Issue: Missing metrics in n8n**
1. Re-import workflow: `n8n_workflows/demo_ready_workflow.json`
2. Restart n8n: `docker-compose restart n8n`

---

## ✅ **Pre-Demo Checklist**

- [ ] All services running: `docker-compose ps`
- [ ] API healthy: `curl localhost:8000/api/v1/health`
- [ ] n8n accessible: http://localhost:5678
- [ ] Workflow imported and tested
- [ ] Can see full metrics in output
- [ ] Know 90-second demo script
- [ ] Have [N8N_WORKFLOW_OUTPUT_EXAMPLE.md](N8N_WORKFLOW_OUTPUT_EXAMPLE.md) open as backup

---

## 🎉 **You're Ready!**

**Your system now:**
- ✅ Shows full evaluation metrics in n8n
- ✅ Matches run_evaluation.py output
- ✅ Calculates real costs in EUR
- ✅ Monitors safety constraints
- ✅ Provides explainable AI reasoning
- ✅ Is production-ready for HSY

**Good luck at Junction 2025!** 🏆
