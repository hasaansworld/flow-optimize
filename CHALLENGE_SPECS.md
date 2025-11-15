# Challenge Specifications - UPDATED ✅

## Official Constraints & Boundaries

### ✅ **CORRECTED CONSTRAINTS** (From Official Communication)

#### **1. Pump Frequency** ⚠️ CORRECTED
- **Minimum**: 47.8 Hz (NOT 47.5 Hz as in some materials!)
- **Nominal**: 50.0 Hz
- **Exception**: Can run below 47.8 Hz ONLY briefly during ramp up/down
- **Reason**: Related to minimum achievable elevation and pump properties

#### **2. Maximum Pumped Flow**
- **F2_MAX**: 16,000 m³/h
- **Equivalent**: ~4.8 large pumps (5 large pumps max)
- **Constraint**: Cannot exceed this total flow

#### **3. Minimum Active Pumps** ⚠️ CRITICAL
- **At least 1 pump must be operating ALL THE TIME**
- **Cannot stop all pumps**
- **Reason**: Continuous wastewater treatment requirement

#### **4. Daily Emptying Constraint** ⚠️ MODIFIED
- **Requirement**: Tunnel must be emptied to L1 < 0.5m once every 24 hours
- **IMPORTANT**: Only during **DRY WEATHER** conditions
- **Dry Weather Definition**: When inflow F1 < 1,000 m³/15min (configurable)
- **Reason**: Prevent sediment buildup, but not safe during storms

#### **5. Water Level Limits**
- **L1_MIN**: 0.0m (minimum)
- **L1_ALARM**: 7.2m (warning threshold)
- **L1_MAX**: 8.0m (absolute maximum)
- **L1_EMPTY**: 0.5m (daily emptying target)

#### **6. Pump Runtime**
- **Minimum runtime**: 2.0 hours if started
- **Reason**: Avoid frequent starts/stops (wear, instability)

---

## Price Scenarios

### **Two Real Price Time Series**

#### **Scenario 1: "HIGH"**
- **Source**: Period of high variation and peak prices
- **Real data**: From high-volatility time slot
- **Range**: 0.055 - 99.196 EUR/kWh
- **Mean**: 40.752 EUR/kWh
- **Std Dev**: 28.780 EUR/kWh
- **Characteristics**:
  - Extreme price spikes (up to 99 EUR/kWh!)
  - 1800x variation (0.055 → 99.196)
  - Massive arbitrage opportunities
  - Challenging for cost optimization

#### **Scenario 2: "NORMAL"**
- **Source**: Contemporary everyday situation
- **Real data**: From typical operational period
- **Range**: -0.050 - 47.949 EUR/kWh (negative prices possible!)
- **Mean**: 8.817 EUR/kWh
- **Std Dev**: 10.127 EUR/kWh
- **Characteristics**:
  - More moderate variation
  - Occasional negative prices (surplus renewable energy)
  - Still significant optimization potential
  - Realistic everyday scenario

**Usage**: Select scenario based on testing needs. HIGH scenario demonstrates extreme optimization potential, NORMAL scenario shows everyday operation.

---

## Pump Performance

### **Power Calculation** (From Official Guidance)

Power intake is a function of:
1. **Pumped volume** (Q - flow rate)
2. **Lifting height** (H = L2 - L1)
3. **Pump efficiency** (η from pump curves)

**Formula**:
```
P = (ρ × g × Q × H) / (η × 3600)

Where:
  ρ = water density (1000 kg/m³)
  g = gravity (9.81 m/s²)
  Q = flow rate (m³/h)
  H = head (m)
  η = pump efficiency (decimal)
  3600 = conversion factor
```

**Simplified** (for our use):
```
P ≈ P_rated × (f / f_nom)³  # Affinity law approximation
η ≈ η_rated × efficiency_curve(Q, H)
```

**Data Source**: Use actual values from Excel data showing:
- Pumped flow per pump
- Water level L1
- Power intake per pump

---

## System Configuration

### **Pumps**

**6 Large Pumps** (1.1, 1.2, 1.4, 2.2, 2.3, 2.4):
- Rated power: 400 kW @ 50 Hz
- Rated flow: 3,330 m³/h @ 50 Hz
- Rated efficiency: ~84.8% @ optimal point
- Impeller: 749mm diameter

**2 Small Pumps** (1.3, 2.1):
- Rated power: 250 kW @ 50 Hz
- Rated flow: 1,670 m³/h @ 50 Hz
- Rated efficiency: ~81.6% @ optimal point
- Impeller: 534mm diameter

**Note**: Pump 1.3 never used in historical data

### **Tunnel Storage**

- **Volume range**: 350 - 225,850 m³
- **Level range**: 0.0 - 14.1m
- **Operational range**: 0.0 - 8.0m
- **Function**: Hydraulic battery for temporal energy arbitrage

### **Elevations**

- **L1**: Water level in tunnel (variable, 0-8m operational)
- **L2**: WWTP intake level (constant, 30m)
- **H**: Pumping head = L2 - L1 (varies with L1)

---

## Optimization Objectives

### **Primary Goal**
**Minimize total energy cost** over the evaluation period

### **Subject to Constraints**
1. ✅ L1 always in range [0, 8]m
2. ✅ No alarms (L1 > 7.2m)
3. ✅ At least 1 pump always running
4. ✅ Pump frequencies ≥ 47.8 Hz (except during ramps)
5. ✅ Total flow F2 ≤ 16,000 m³/h
6. ✅ Pump runtime ≥ 2h if started
7. ✅ Daily emptying (L1 < 0.5m) during dry weather
8. ✅ Smooth flow changes (avoid sudden jumps)

### **Secondary Goals**
- Maximize pump efficiency (operate near optimal points)
- Minimize flow variability (smooth F2 changes)
- Minimize pump start/stop cycles
- Exploit price arbitrage opportunities

---

## Challenge Metrics

### **Performance Evaluation**

**Cost Savings**:
```
Savings % = (Baseline_Cost - Optimized_Cost) / Baseline_Cost × 100%
```

**Target**: 30-35% energy cost reduction

**Constraint Compliance**:
- **Violations**: 0 (zero tolerance for hard constraints)
- **Alarms**: Minimize events where L1 > 7.2m

**Operational Quality**:
- **Flow smoothness**: Low standard deviation of F2
- **Pump efficiency**: Average η > 82%
- **Uptime**: System operational 100% of time

---

## Data Available

### **Historical Data**
- **Period**: 15 days (2024-11-15 to 2024-11-30)
- **Records**: 1,536 timesteps
- **Interval**: 15 minutes
- **Columns**:
  - Time stamp
  - Water level L1 (m)
  - Volume V (m³)
  - Inflow F1 (m³/15min)
  - Outflow F2 (m³/h)
  - Pump flows (8 pumps, m³/h)
  - Pump efficiencies (8 pumps, %)
  - Pump frequencies (8 pumps, Hz)
  - Electricity price HIGH (EUR/kWh)
  - Electricity price NORMAL (EUR/kWh)

### **Pump Curves** (PDFs)
- Flow vs Head
- Efficiency vs Flow
- Power vs Flow
- For both large and small pumps

### **Volume-Level Map** (Excel)
- Lookup table: Volume ↔ Level
- 142 data points
- Non-linear relationship

---

## Multi-Agent AI Requirements

### **Core Challenge**
> "Can multiple autonomous agents, each with their own goals and data streams, discover pumping strategies no human operator could design?"

### **Agent Requirements**

**Autonomy**:
- Each agent makes independent assessments
- Uses LLM-based reasoning (human-like thinking)
- Has specialized expertise in one domain

**Coordination**:
- Agents communicate and negotiate
- Coordinator synthesizes recommendations
- Emergent strategies from collaboration

**Intelligence**:
- Forecasting (LSTM, pattern recognition)
- Optimization (MPC, RL)
- Reasoning (LLM, constraint satisfaction)

---

## Expected Innovations

### **Emergent Strategies** (Examples)

**1. Temporal Arbitrage**:
- Pre-empty tunnel before cheap electricity windows
- Use storage as "energy battery"
- Defer non-critical pumping during expensive periods

**2. Storm Pre-positioning**:
- Create capacity before predicted storm
- Skip expensive mid-storm windows if safe
- Staged pump activation (not all at once)

**3. Dynamic Efficiency Optimization**:
- Switch pump combinations as H changes
- Operate pumps at peak efficiency points
- Coordinate frequencies for minimal total power

**4. Predictive Daily Emptying**:
- Time emptying for cheapest electricity
- Only during dry weather (check forecast)
- Combine with other operational needs

---

## Success Criteria

### **Must Have** ✅
1. Zero constraint violations
2. >20% cost savings vs baseline
3. Working multi-agent system with OPC UA
4. Real-time visualization showing agent decisions
5. Explainable AI (natural language reasoning)

### **Should Have** ✅
6. >30% cost savings
7. Storm handling demonstration
8. Price arbitrage demonstration
9. LSTM inflow forecasting
10. RL policy optimization

### **Nice to Have** ⭐
11. >35% cost savings
12. 5+ emergent strategies discovered
13. Generic framework (applicable to other plants)
14. Live demo with agent communication visualization

---

**Last Updated**: 2025-11-15
**Status**: Constraints verified and simulation updated ✅
**Next**: Build multi-agent AI system 🚀
