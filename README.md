# Flow Optimize - Multi-Agent AI for Wastewater Pumping

**Intelligent Flow Optimization by Valmet x HSY - Junction 2025 Hackathon**

Multi-agent AI system that autonomously optimizes wastewater pumping energy costs while maintaining safety constraints.

## 🎯 Challenge

Build autonomous agents that discover optimal pumping strategies by coordinating across:
- Energy price fluctuations (15-min intervals)
- Inflow forecasting (storms, daily patterns)
- Pump efficiency optimization (8 pumps, variable frequency)
- Storage management (tunnel as hydraulic battery)
- Safety constraints (level limits, runtime rules)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│         Multi-Agent AI System                   │
│  (Specialized Autonomous Agents)                │
│  - Inflow Forecasting Agent                     │
│  - Cost Optimization Agent                      │
│  - Pump Efficiency Agent                        │
│  - Safety Agent                                 │
│  - Flow Smoothness Agent                        │
│  - Compliance Agent                             │
│  - Coordinator Agent                            │
└──────────────┬──────────────────────────────────┘
               │ OPC UA Protocol
               ▼
┌─────────────────────────────────────────────────┐
│      OPC UA Simulation Environment              │
│  - Physics Simulator (tunnel dynamics)          │
│  - Pump Models (efficiency curves)              │
│  - Historical Data Replay                       │
│  - Sensor & Control Nodes                       │
└─────────────────────────────────────────────────┘
```

## 📦 Project Structure

```
flow-optimize/
├── assets/                          # Historical data
│   ├── Hackathon_HSY_data.xlsx     # 15 days operational data
│   ├── Volume of tunnel vs level...xlsx
│   └── Pumppukäyrä_*.PDF           # Pump curves
├── src/
│   ├── simulation/                  # ✅ OPC UA Simulation (DONE)
│   │   ├── data_loader.py          # Load historical data
│   │   ├── pump_models.py          # Pump performance models
│   │   ├── physics_simulator.py    # Tunnel dynamics
│   │   └── opcua_server.py         # OPC UA server
│   ├── agents/                      # 🚧 Multi-Agent System (TODO)
│   │   ├── inflow_agent.py
│   │   ├── cost_agent.py
│   │   ├── efficiency_agent.py
│   │   ├── safety_agent.py
│   │   └── coordinator.py
│   └── models/                      # 🚧 ML Models (TODO)
│       ├── lstm_forecaster.py
│       └── ppo_policy.py
├── tests/
│   └── test_opcua_client.py        # Test OPC UA connection
└── venv/                            # Python environment
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Already set up with venv
source venv/bin/activate

# Packages installed:
# - asyncua (OPC UA)
# - pandas, numpy (data)
# - scipy, matplotlib (analysis)
# - openpyxl (Excel)
```

### 2. Run OPC UA Simulation Server

```bash
# Start the server (900x speedup: 15 min = 1 second)
python src/simulation/opcua_server.py

# Server will run at: opc.tcp://localhost:4840/hsy/wastewater/
```

### 3. Test with OPC UA Client

```bash
# In another terminal
source venv/bin/activate
python tests/test_opcua_client.py
```

## 📊 OPC UA Interface

### Sensor Nodes (Read-Only)

```
ns=2;s=Sensors/WaterLevel_L1       # Water level (m)
ns=2;s=Sensors/WaterVolume_V       # Volume (m³)
ns=2;s=Sensors/Inflow_F1           # Inflow (m³/15min)
ns=2;s=Sensors/Outflow_F2          # Total outflow (m³/h)
ns=2;s=Sensors/ElectricityPrice    # Price (EUR/kWh)
ns=2;s=Sensors/Timestamp           # Current time
```

### Pump Nodes (Read-Only Status)

For each pump (1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4):

```
ns=2;s=Pumps/Pump_X_Y/Flow         # Current flow (m³/h)
ns=2;s=Pumps/Pump_X_Y/Power        # Power consumption (kW)
ns=2;s=Pumps/Pump_X_Y/Efficiency   # Efficiency (%)
ns=2;s=Pumps/Pump_X_Y/Frequency    # Frequency (Hz)
ns=2;s=Pumps/Pump_X_Y/IsRunning    # Status (bool)
```

### Control Nodes (Writable by Agents)

```
ns=2;s=Control/Pump_X_Y/Start         # Start/Stop (bool)
ns=2;s=Control/Pump_X_Y/SetFrequency  # Frequency (47.5-50 Hz)
```

### Status Nodes

```
ns=2;s=Status/ConstraintsViolated  # Any violations (bool)
ns=2;s=Status/AlarmLevel           # L1 > 7.2m (bool)
ns=2;s=Status/TotalEnergyCost      # Total cost (EUR)
ns=2;s=Status/TotalEnergyKWh       # Total energy (kWh)
```

## 🔧 System Specifications

### Pumps
- **6 Large Pumps** (1.1, 1.2, 1.4, 2.2, 2.3, 2.4): 400 kW rated, 3,330 m³/h @ 50Hz
- **2 Small Pumps** (1.3, 2.1): 250 kW rated, 1,670 m³/h @ 50Hz
- Operating frequency: 47.5-50 Hz (variable frequency drive)
- Efficiency: ~82-85% at optimal operating point

### Tunnel Storage
- Volume range: 350 - 225,850 m³
- Level range: 0.0 - 14.1 m
- Alarm threshold: 7.2 m
- Maximum: 8.0 m

### Constraints
- Water level: 0-8 m (alarm at 7.2 m)
- Pump runtime: ≥2 hours if started
- Daily emptying: L1 < 0.5m once per day
- Pumps cannot all stop
- Smooth outflow preferred

### Data
- Period: 15 days (2024-11-15 to 2024-11-30)
- Timestep: 15 minutes (1,536 records)
- Inflow range: 30 - 3,213 m³/15min (storm events)
- Price range: 0.055 - 99.196 EUR/kWh (high volatility!)

## 🧪 Testing

### Test Data Loader

```bash
python src/simulation/data_loader.py
```

### Test Pump Models

```bash
python src/simulation/pump_models.py
```

### Test Physics Simulator

```bash
cd src/simulation
python physics_simulator.py
```

### Test OPC UA Server

```bash
# Terminal 1: Start server
python src/simulation/opcua_server.py

# Terminal 2: Run client
python tests/test_opcua_client.py
```

## 📈 Expected Performance

### Baseline (Current Operations)
- Average cost: ~100%
- Constraint violations: 15/day
- Flow smoothness: High variability

### Target (Multi-Agent AI)
- Energy savings: 30-35%
- Violations: 0
- Flow smoothness: Improved
- Emergent strategies: 5-10 discovered

## 🎯 Next Steps

### Phase 1: ML Models ✅ Foundation Complete
- [x] Data loader
- [x] Pump models with affinity laws
- [x] Physics simulator
- [x] OPC UA server
- [ ] LSTM inflow forecasting
- [ ] PPO reinforcement learning policy

### Phase 2: Multi-Agent System
- [ ] Inflow Forecasting Agent
- [ ] Cost Optimization Agent
- [ ] Pump Efficiency Agent
- [ ] Safety Agent
- [ ] Flow Smoothness Agent
- [ ] Compliance Agent
- [ ] Coordinator Agent
- [ ] LangGraph integration

### Phase 3: Integration & Testing
- [ ] End-to-end testing
- [ ] Backtesting on 15-day dataset
- [ ] Scenario testing (storms, price spikes)
- [ ] Performance benchmarking

### Phase 4: Visualization
- [ ] Real-time dashboard
- [ ] Cross-sectional view (tunnel, pumps)
- [ ] Agent communication visualization
- [ ] Performance metrics

## 🛠️ Technology Stack

- **Python 3.13**
- **OPC UA**: asyncua
- **Data**: pandas, numpy
- **ML**: PyTorch (LSTM), Stable-Baselines3 (PPO)
- **Agents**: LangChain, LangGraph, Anthropic Claude API
- **Viz**: Matplotlib, Streamlit

## 💻 Hardware Requirements

✅ **Runs on MacBook Pro without GPU**
- CPU usage: ~7%
- RAM: ~700 MB
- M1/M2/M3: Perfect performance
- Intel Mac: Works fine

## 📝 License

Hackathon Project - Junction 2025

---

**Status**: ✅ Simulation Environment Complete | 🚧 Multi-Agent System In Progress
