# ⚡ Quick Command Reference

## 🚀 **Starting the System**

### **Normal Start (with rebuild):**
```bash
./start_n8n_system.sh
```
- ✅ Rebuilds agent-api (installs new dependencies)
- ✅ Starts all services
- ✅ Checks health
- Use when: requirements.txt changed

### **Fast Start (skip rebuild):**
```bash
./start_n8n_system.sh --no-build
```
- ⚡ Skips rebuild
- ✅ Starts services faster
- Use when: Only Python code changed (src/)

---

## 🔄 **After Changing Files**

### **Changed Python Code (src/agents/, src/api/):**
```bash
# Just restart (no rebuild needed)
docker-compose restart agent-api

# Or use fast start
./start_n8n_system.sh --no-build
```

### **Changed requirements.txt:**
```bash
# Rebuild and restart
docker-compose build agent-api
docker-compose up -d agent-api

# Or use normal start
./start_n8n_system.sh
```

### **Changed .env:**
```bash
# Just restart
docker-compose restart agent-api

# Or restart all services
docker-compose restart
```

### **Changed docker-compose.yml:**
```bash
# Recreate containers
docker-compose up -d --force-recreate
```

---

## 📊 **Monitoring**

### **View Logs:**
```bash
# All services
docker-compose logs -f

# Agent API only
docker-compose logs -f agent-api

# Last 50 lines
docker logs wastewater-agent-api --tail 50
```

### **Check Status:**
```bash
# All containers
docker-compose ps

# Health check
curl http://localhost:8000/api/v1/health
```

---

## 🧪 **Testing**

### **Test API:**
```bash
# Health check
curl http://localhost:8000/api/v1/health

# Get decision with agent messages
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

### **Test Webhook:**
```bash
# Trigger workflow and get response
curl -X POST http://localhost:5678/webhook/wastewater-decision
```

### **Run Evaluation:**
```bash
# Using script
bash run_evaluation_with_output.sh normal 10

# Direct
source venv/bin/activate
python src/agents/run_evaluation.py --price normal --steps 10
```

---

## 🛑 **Stopping Services**

```bash
# Stop all services
docker-compose down

# Stop but keep volumes (database data)
docker-compose stop

# Stop specific service
docker-compose stop agent-api
```

---

## 🔧 **Development Workflow**

### **Typical Workflow:**

```bash
# 1. Make changes to agent code
vim src/agents/specialist_agents.py

# 2. Restart API (no rebuild needed)
docker-compose restart agent-api

# 3. Test
curl http://localhost:8000/api/v1/synthesize -X POST -d '{...}'

# 4. Check logs if needed
docker logs wastewater-agent-api --tail 30
```

### **After Adding New Package:**

```bash
# 1. Add to requirements.txt
echo "new-package==1.0.0" >> requirements.txt

# 2. Rebuild and restart
docker-compose build agent-api
docker-compose up -d agent-api

# 3. Verify
docker exec wastewater-agent-api pip list | grep new-package
```

---

## 🎯 **Quick Actions**

| Action | Command |
|--------|---------|
| **Start (with rebuild)** | `./start_n8n_system.sh` |
| **Fast start** | `./start_n8n_system.sh --no-build` |
| **Restart API** | `docker-compose restart agent-api` |
| **Rebuild API** | `docker-compose build agent-api && docker-compose up -d agent-api` |
| **View logs** | `docker-compose logs -f agent-api` |
| **Stop all** | `docker-compose down` |
| **Health check** | `curl http://localhost:8000/api/v1/health` |
| **Test webhook** | `curl -X POST http://localhost:5678/webhook/wastewater-decision` |

---

## 📁 **File Changes → Actions Needed**

| File(s) Changed | Action Required | Command |
|-----------------|-----------------|---------|
| `src/agents/*.py` | Restart only | `docker-compose restart agent-api` |
| `src/api/*.py` | Restart only | `docker-compose restart agent-api` |
| `config/*.py` | Restart only | `docker-compose restart agent-api` |
| `requirements.txt` | Rebuild | `docker-compose build agent-api && docker-compose up -d` |
| `.env` | Restart | `docker-compose restart` |
| `docker-compose.yml` | Recreate | `docker-compose up -d --force-recreate` |
| `Dockerfile` | Rebuild | `docker-compose build agent-api && docker-compose up -d` |
| `n8n_workflows/*.json` | Import in n8n | No command needed |

---

## 🆘 **Troubleshooting**

### **API not responding:**
```bash
# Check if running
docker-compose ps

# Check logs
docker logs wastewater-agent-api --tail 50

# Restart
docker-compose restart agent-api
```

### **"Module not found" error:**
```bash
# Rebuild (installs packages)
docker-compose build agent-api
docker-compose up -d agent-api
```

### **Port already in use:**
```bash
# Stop conflicting service
lsof -ti:8000 | xargs kill -9

# Or change port in docker-compose.yml
```

### **Clean start:**
```bash
# Stop everything
docker-compose down

# Remove volumes (WARNING: deletes database)
docker-compose down -v

# Rebuild and start fresh
docker-compose build
docker-compose up -d
```

---

## ✅ **Summary**

**Most Common Commands:**

```bash
# After changing agent code
docker-compose restart agent-api

# After changing requirements.txt
./start_n8n_system.sh

# View what's happening
docker-compose logs -f agent-api

# Test it works
curl http://localhost:8000/api/v1/health
curl -X POST http://localhost:5678/webhook/wastewater-decision
```

**That's it!** 🚀
