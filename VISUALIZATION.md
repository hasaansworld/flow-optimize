# 🎨 Visualization Guide

## Real-Time 2D Cross-Section View

The project includes a comprehensive 2D visualization that shows the wastewater pumping system in action.

### Features

#### **Cross-Sectional View**
- **Tunnel**: Gray concrete structure showing the storage tunnel
- **Water Level**: Animated blue water with dynamic height
- **Water Color Coding**:
  - 🔵 Blue: Normal operation (L1 < 7.2m)
  - 🔴 Red: Alarm level (7.2m < L1 < 8.0m)
  - 🔴 Dark Red: Critical (L1 > 8.0m)
- **Level Markers**: Reference lines at key levels (0, 2, 4, 6, 7.2m alarm, 8.0m max)

#### **Pump Visualization**
- **8 Pumps** displayed on the right side (P1.1-1.4, P2.1-2.4)
- **Status Indicators**:
  - 🟢 Green: Pump running
  - ⚫ Gray: Pump off
- **Pipes**: Lines showing connection to WWTP

#### **WWTP Tank**
- Elevated tank at 30m showing wastewater treatment plant
- Receives pumped water from all active pumps

#### **Real-Time Metrics**
Three time-series panels showing:

1. **Water Level History**
   - Blue line: Current water level (L1)
   - Red dashed line: 7.2m alarm threshold
   - Dark red line: 8.0m maximum limit

2. **Flow Rates**
   - Blue line: Inflow (F1) - water entering tunnel
   - Green line: Outflow (F2/4) - water pumped to WWTP
   - Shows balance between inflow and pumping

3. **Energy Cost & Price**
   - Red line: Total accumulated energy cost (EUR)
   - Orange dashed line: Current electricity price (EUR/kWh)
   - Shows cost optimization opportunities

### Running the Visualization

#### **Option 1: Standalone Simulation**

Run simulation with built-in control strategy:

```bash
./run_visualization.sh
```

Or directly:

```bash
source venv/bin/activate
python src/simulation/visualizer.py
```

**What happens:**
- Loads 15 days of historical HSY data
- Runs physics simulation with simple control strategy
- Updates visualization every 100ms (100ms = 1 timestep = 15 minutes simulated)
- Shows first 200 timesteps (~50 hours of operation)

#### **Option 2: OPC UA Connected Visualization**

View real-time data from OPC UA server (for multi-agent testing):

**Terminal 1** - Start OPC UA server:
```bash
./run_simulation.sh
```

**Terminal 2** - Start connected visualizer:
```bash
source venv/bin/activate
python src/simulation/opcua_visualizer.py
```

**What happens:**
- Connects to OPC UA server at `opc.tcp://localhost:4840/hsy/wastewater/`
- Reads sensor data and pump states every 0.5 seconds
- Displays what the multi-agent system is doing
- Shows agent control decisions in real-time

### Visualization Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  HSY Blominmäki Wastewater Pumping Station - 2024-11-15 14:30  │
├─────────────────────────────────────────────────────────────────┤
│                    System Cross-Section                         │
│                                                                 │
│  Inflow →         ┌────────────────────────┐      ┌─────┐      │
│   850 m³/15min    │~~~~~~~~~~~~~~~~~~~~~~~~│  ╔═══╡WWTP │      │
│                   │~~~ Water L1=4.2m ~~~~~│  ║   │ 30m │      │
│                   │████████████████████████│  ║   └─────┘      │
│  ─────────────────┴────────────────────────┴──╝───────────      │
│   0m  2m  4m  6m  7.2m  8m                 Pumps (8x)          │
│                                            P1.1 🟢              │
│  L1 = 4.20m                                P1.2 ⚫              │
│  V = 45,230m³                              P1.3 ⚫              │
│                                            P1.4 🟢              │
│                                            P2.1 ⚫              │
│                                            P2.2 🟢              │
│                                            P2.3 🟢              │
│                             Outflow →      P2.4 ⚫              │
│                            8,500 m³/h                           │
├──────────────────┬──────────────────────┬──────────────────────┤
│ Water Level      │ Flow Rates           │ Energy Cost & Price  │
│                  │                      │                      │
│  8m ┄┄┄┄┄┄       │  3000 ┐              │  500 EUR ┐          │
│  7.2m ═════      │       │ F1 Inflow    │          │ Cost     │
│       /‾‾‾\      │  2000 │ F2 Outflow   │  300     │          │
│  4m  /     \     │  1000 │              │  100     │ Price    │
│  2m /       ‾‾   │     0 └──────────    │    0 └────────      │
│     └────────    │       Time           │          Time        │
└──────────────────┴──────────────────────┴──────────────────────┘
```

### Customizing the Control Strategy

Edit `visualizer.py` to change pump control logic:

```python
def control_strategy(self, state: SystemState) -> list:
    """Define your control strategy here"""

    L1 = state.L1

    if L1 > 6.0:
        # High level - run 4 pumps
        commands = [
            PumpCommand('1.2', start=True, frequency=50.0),
            PumpCommand('1.4', start=True, frequency=50.0),
            PumpCommand('2.2', start=True, frequency=50.0),
            PumpCommand('2.3', start=True, frequency=50.0),
        ]
    # ... more logic

    return commands
```

This is where the multi-agent system will plug in later!

### Performance

**System Requirements:**
- ✅ MacBook Pro (any M1/M2/M3 or Intel)
- ✅ No GPU needed
- ✅ ~7% CPU usage
- ✅ ~700 MB RAM
- ✅ Smooth 60 FPS animation

**Update Rates:**
- Standalone mode: 100ms per timestep (10 timesteps/second)
- OPC UA mode: 500ms per update (2 updates/second)
- Configurable via `interval_ms` parameter

### Interpreting the Visualization

**Normal Operation:**
- Water level oscillating between 1-4m (blue water)
- 2-3 pumps active (green)
- Inflow and outflow roughly balanced
- Steady cost accumulation

**Storm Event:**
- Inflow (F1) spikes rapidly
- Water level rising quickly
- More pumps activate (more green)
- Outflow (F2) increases to compensate

**Price Arbitrage:**
- Cost line flattens during high prices (minimal pumping)
- Multiple pumps activate during cheap periods
- Water level allowed to rise temporarily (within safe limits)

**Constraint Violation:**
- Water turns red (L1 > 7.2m alarm)
- Water turns dark red (L1 > 8.0m critical)
- All pumps should activate (emergency response)

### Tips

- **Pause simulation**: Close the window, modify code, re-run
- **Speed up**: Reduce `interval_ms` in `SimulationVisualizer`
- **Longer run**: Increase `max_steps` parameter
- **Full dataset**: Set `max_steps=None` to run all 1,536 timesteps

### Next Steps

Once multi-agent system is built:
1. Agents will write commands to OPC UA server
2. Use `opcua_visualizer.py` to see agent decisions in real-time
3. Compare agent strategies vs. baseline visually
4. Demo emergent behaviors with live animation

---

**See it in action**: `./run_visualization.sh` 🚀
