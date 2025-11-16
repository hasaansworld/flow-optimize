# Multi-Agent Wastewater Pumping Optimization System

**Junction 2025 Hackathon Project** | **Challenge: Intelligent Flow Optimization** (Valmet × HSY)

## ⚠️ Important: Evaluation System Fixes (November 2025)

The evaluation system was initially claiming unrealistic **96% cost savings** due to cascading bugs. These have been fixed:

- ✅ Fixed pump power calculation (now uses real specs, not hardcoded values)
- ✅ Added pump validation layer (ensures realistic multi-pump configurations)
- ✅ Corrected cost calculation (was using constant 100 kWh per timestep)

**New realistic results: 20-30% cost savings** (achievable improvement)

→ See [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md) for details  
→ See [BEFORE_AFTER_COMPARISON.md](BEFORE_AFTER_COMPARISON.md) for metrics

---

## 🚀 Quick Start

```bash
# 1. Run the multi-agent system (backtest mode)
source venv/bin/activate
python src/agents/run_multi_agent.py --mode backtest --steps 96

# 2. (Optional) Start OPC UA simulation server
./run_simulation.sh

# 3. (Optional) Run live with OPC UA
python src/agents/run_multi_agent.py --mode live --opcua opc.tcp://localhost:4840
```

## 📋 Project Overview

This project implements a **multi-agent AI system** to optimize wastewater pumping operations, minimizing energy costs while maintaining strict safety constraints.

### System Components

- **6 Specialist AI Agents** - Each focused on one aspect (forecasting, cost, efficiency, safety, smoothness, compliance)
- **1 Coordinator Agent** - Synthesizes all recommendations using Gemini LLM
- **LSTM Neural Network** - Predicts future inflow (storms, daily patterns)
- **Google Gemini 2.5 Flash** - LLM for human-like reasoning
- **OPC UA Protocol** - Industrial-standard communication

### Key Innovation

Instead of traditional MPC or RL, this system uses **autonomous agents that think like human experts**. Agents discover emergent strategies through distributed intelligence and LLM-powered coordination.

---

## 🤖 The 7 Agents

1. **Inflow Forecasting Agent** - Predicts future wastewater inflow (LSTM + LLM)
2. **Energy Cost Agent** - Identifies price arbitrage opportunities
3. **Pump Efficiency Agent** - Selects optimal pump combinations
4. **Water Level Safety Agent** - Ensures safety constraints (VETO power)
5. **Flow Smoothness Agent** - Prevents shock loading to WWTP
6. **Constraint Compliance Agent** - Enforces all hard constraints (VETO power)
7. **Coordinator Agent** - Synthesizes all → final pump commands

**Priority Hierarchy:** Safety > Compliance > Cost > Efficiency/Smoothness

---

## 🗂️ Project Structure

```
flow-optimize/
├── src/agents/                    # Multi-agent system
│   ├── run_multi_agent.py        # 🎯 MAIN ENTRY POINT
│   ├── coordinator_agent.py      # Coordinator
│   ├── specialist_agents.py      # All 6 specialist agents
│   ├── inflow_agent.py           # Inflow forecasting
│   ├── base_agent.py             # Base class
│   └── gemini_wrapper.py         # Gemini API
│
├── src/models/                    # ML models
│   ├── inflow_forecaster.py      # LSTM implementation
│   └── inflow_lstm_model.pth     # Trained model
│
├── src/simulation/                # OPC UA simulation
│   ├── opcua_server.py           # OPC UA server
│   ├── physics_simulator.py      # Tunnel dynamics
│   ├── pump_models.py            # Pump affinity laws
│   └── opcua_visualizer.py       # Real-time visualization
│
├── config/constraints.py          # System constraints
├── .env                           # API keys & config
└── README.md                      # This file
```

---

## ⚙️ Configuration (`.env`)

```bash
# Google Gemini API Key
GEMINI_API_KEY=your_key_here

# Model (gemini-2.5-flash recommended)
GEMINI_MODEL=gemini-2.5-flash

# Price scenario
PRICE_SCENARIO=normal              # or "high"

# Agent settings
AGENT_TEMPERATURE=0.7
AGENT_MAX_TOKENS=2048
```

---

## 🎮 Usage

### Backtest Mode (Historical Data)

```bash
# Run 24 hours (96 timesteps)
python src/agents/run_multi_agent.py --mode backtest --steps 96 --start 500

# Run with HIGH price scenario
python src/agents/run_multi_agent.py --mode backtest --price high --steps 96
```

### Live Mode (OPC UA Control)

```bash
# Terminal 1: Start OPC UA server
./run_simulation.sh

# Terminal 2: Run agents
python src/agents/run_multi_agent.py --mode live --opcua opc.tcp://localhost:4840
```

---

## 📊 Results & Performance

The system successfully runs autonomous decision-making with:
- ✅ All 6 specialist agents providing recommendations
- ✅ Coordinator synthesizing with priority hierarchy
- ✅ LSTM inflow forecasting (trained on 15 days HSY data)
- ✅ Gemini 2.5 Flash LLM reasoning
- ✅ Safety and compliance enforcement
- ✅ Real-time OPC UA integration

---

## 🎯 Challenge Requirements

✅ Minimize energy costs
✅ Safety constraints (L1 ≤ 8.0m)
✅ Operational constraints (min runtime, daily emptying, frequencies)
✅ Smooth flow to WWTP (max 2000 m³/h change per 15min)
✅ Inflow forecasting (LSTM-based)
✅ OPC UA integration
✅ 2D visualization

---

## 🛠️ Key Technologies

- **PyTorch** - LSTM neural networks
- **Google Generative AI** - Gemini 2.5 Flash LLM
- **asyncua** - OPC UA protocol
- **pandas, numpy** - Data processing
- **matplotlib** - Visualization

---

## 📚 Documentation

- `CHALLENGE_SPECS.md` - Complete challenge specifications
- `MULTI_AGENT_PLAN.md` - Detailed agent architecture
- `SETUP_API.md` - Gemini API setup guide

---

## 🎉 Built for Junction 2025 Hackathon

**Challenge:** Intelligent Flow Optimization (Valmet × HSY)

**Tech Stack:** Python, PyTorch, Google Gemini, OPC UA, Multi-Agent AI
