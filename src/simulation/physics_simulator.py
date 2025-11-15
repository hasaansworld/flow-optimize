"""
Physics Simulator for Wastewater Tunnel System
Simulates water level, volume, and pump dynamics
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from dataclasses import dataclass, field

from data_loader import HSYDataLoader
from pump_models import PumpModel, PumpController


@dataclass
class SystemState:
    """Current state of the wastewater system"""
    timestamp: datetime
    L1: float  # Water level (m)
    V: float  # Volume (m³)
    F1: float  # Inflow (m³/15min)
    F2: float  # Total outflow (m³/h)
    electricity_price: float  # EUR/kWh
    active_pumps: Dict[str, Dict] = field(default_factory=dict)
    total_energy_cost: float = 0.0
    total_energy_kwh: float = 0.0
    violations: List[str] = field(default_factory=list)


@dataclass
class PumpCommand:
    """Command to control a pump"""
    pump_id: str
    start: bool  # True to start/keep running, False to stop
    frequency: float = 50.0  # Hz (47.5-50)


class TunnelSimulator:
    """
    Simulates the tunnel water dynamics and pump operations

    Physics:
    - dV/dt = F1 - F2 (mass balance)
    - V(t+1) = V(t) + ΔV
    - L1 = f(V) from lookup table
    - F2 = Σ pump_flows
    """

    def __init__(
        self,
        data_loader: HSYDataLoader,
        initial_L1: float = 2.0,
        time_step_minutes: int = 15,
        use_historical_inflow: bool = True
    ):
        """
        Initialize simulator

        Args:
            data_loader: Loaded HSY data
            initial_L1: Starting water level (m)
            time_step_minutes: Simulation time step
            use_historical_inflow: If True, use actual historical data; if False, use forecasts
        """

        self.data_loader = data_loader
        self.pump_model = PumpModel()
        self.pump_controller = PumpController()

        self.time_step_minutes = time_step_minutes
        self.time_step_seconds = time_step_minutes * 60
        self.time_step_hours = time_step_minutes / 60.0

        self.use_historical_inflow = use_historical_inflow

        # Load historical data
        self.historical_data = data_loader.main_data
        self.historical_index = 0

        # Initialize state
        self.current_time = self.historical_data['Time stamp'].iloc[0]
        initial_V = data_loader.level_to_volume(initial_L1)

        self.state = SystemState(
            timestamp=self.current_time,
            L1=initial_L1,
            V=initial_V,
            F1=0.0,
            F2=0.0,
            electricity_price=0.0,
            active_pumps={},
            total_energy_cost=0.0,
            total_energy_kwh=0.0,
            violations=[]
        )

        # Constraints
        self.L1_MIN = 0.0  # m
        self.L1_MAX = 8.0  # m
        self.L1_ALARM = 7.2  # m
        self.MIN_FREQUENCY = 47.5  # Hz
        self.MAX_FREQUENCY = 50.0  # Hz
        self.MIN_RUNTIME_HOURS = 2.0

        # Statistics
        self.total_violations = 0
        self.alarm_count = 0

        print(f"✓ Tunnel Simulator initialized at {self.current_time}")
        print(f"  Initial L1: {initial_L1:.2f}m, V: {initial_V:.0f}m³")

    def get_inflow(self) -> float:
        """
        Get inflow for current timestep

        Returns:
            Inflow in m³/15min
        """

        if self.use_historical_inflow and self.historical_index < len(self.historical_data):
            # Use actual historical data
            F1 = self.historical_data['F1'].iloc[self.historical_index]
        else:
            # Fallback to average pattern (could be replaced with forecast)
            hour = self.current_time.hour
            # Simple daily pattern
            if 6 <= hour < 9:  # Morning peak
                F1 = 700
            elif 18 <= hour < 21:  # Evening peak
                F1 = 650
            elif 22 <= hour or hour < 6:  # Night
                F1 = 300
            else:  # Day
                F1 = 500

        return F1

    def get_electricity_price(self) -> float:
        """
        Get electricity price for current timestep

        Returns:
            Price in EUR/kWh
        """

        if self.historical_index < len(self.historical_data):
            # Use normal price scenario from historical data
            price = self.historical_data['Price_Normal'].iloc[self.historical_index]
        else:
            # Fallback to average price
            price = 0.30

        return price

    def step(self, pump_commands: List[PumpCommand]) -> SystemState:
        """
        Advance simulation by one time step

        Args:
            pump_commands: List of pump control commands

        Returns:
            Updated system state
        """

        # Get inflow and price for this timestep
        F1 = self.get_inflow()
        price = self.get_electricity_price()

        # Calculate outflow from pump commands
        F2_total = 0.0
        total_power = 0.0
        active_pumps = {}

        for cmd in pump_commands:
            if cmd.start:
                # Calculate pump performance
                flow_m3h, power_kw, efficiency = self.pump_model.calculate_pump_performance(
                    cmd.pump_id,
                    cmd.frequency,
                    self.state.L1
                )

                F2_total += flow_m3h
                total_power += power_kw

                active_pumps[cmd.pump_id] = {
                    'running': True,
                    'frequency': cmd.frequency,
                    'flow_m3h': flow_m3h,
                    'power_kw': power_kw,
                    'efficiency': efficiency
                }

                # Update controller state
                self.pump_controller.update_pump_state(
                    cmd.pump_id,
                    True,
                    cmd.frequency,
                    self.current_time.timestamp()
                )
            else:
                # Pump off
                self.pump_controller.update_pump_state(
                    cmd.pump_id,
                    False,
                    50.0,
                    self.current_time.timestamp()
                )

        # Physics: Mass balance
        # F1 is in m³/15min, F2 is in m³/h
        # ΔV = F1 - F2 * (timestep in hours)
        delta_V = F1 - (F2_total * self.time_step_hours)

        # Update volume and level
        new_V = self.state.V + delta_V
        new_L1 = self.data_loader.volume_to_level(new_V)

        # Calculate energy cost for this timestep
        energy_kwh = total_power * self.time_step_hours
        energy_cost = energy_kwh * price

        # Check constraints
        violations = []
        if new_L1 > self.L1_MAX:
            violations.append(f"CRITICAL: L1={new_L1:.2f}m exceeds maximum {self.L1_MAX}m")
            self.total_violations += 1
        elif new_L1 > self.L1_ALARM:
            violations.append(f"WARNING: L1={new_L1:.2f}m exceeds alarm threshold {self.L1_ALARM}m")
            self.alarm_count += 1
        if new_L1 < self.L1_MIN:
            violations.append(f"WARNING: L1={new_L1:.2f}m below minimum {self.L1_MIN}m")
            self.total_violations += 1

        # Update state
        self.state = SystemState(
            timestamp=self.current_time,
            L1=new_L1,
            V=new_V,
            F1=F1,
            F2=F2_total,
            electricity_price=price,
            active_pumps=active_pumps,
            total_energy_cost=self.state.total_energy_cost + energy_cost,
            total_energy_kwh=self.state.total_energy_kwh + energy_kwh,
            violations=violations
        )

        # Advance time
        self.current_time += timedelta(minutes=self.time_step_minutes)
        self.historical_index += 1

        return self.state

    def get_state(self) -> SystemState:
        """Get current state"""
        return self.state

    def reset(self, initial_L1: float = 2.0):
        """Reset simulator to initial state"""
        self.current_time = self.historical_data['Time stamp'].iloc[0]
        self.historical_index = 0

        initial_V = self.data_loader.level_to_volume(initial_L1)

        self.state = SystemState(
            timestamp=self.current_time,
            L1=initial_L1,
            V=initial_V,
            F1=0.0,
            F2=0.0,
            electricity_price=0.0,
            active_pumps={},
            total_energy_cost=0.0,
            total_energy_kwh=0.0,
            violations=[]
        )

        self.total_violations = 0
        self.alarm_count = 0

        self.pump_controller = PumpController()

        print(f"✓ Simulator reset to {self.current_time}")


if __name__ == "__main__":
    # Test the simulator
    print("=== Testing Tunnel Simulator ===\n")

    # Load data
    loader = HSYDataLoader()
    loader.load_all_data()

    # Create simulator
    sim = TunnelSimulator(loader, initial_L1=2.0)

    print("\n=== Running 24-hour simulation (96 timesteps) ===\n")

    # Simple control strategy: maintain 2 large pumps running
    results = []

    for i in range(96):  # 24 hours * 4 timesteps/hour
        # Simple fixed control: Run pumps 2.2 and 2.3 at 50 Hz
        commands = [
            PumpCommand('2.2', start=True, frequency=50.0),
            PumpCommand('2.3', start=True, frequency=50.0),
        ]

        state = sim.step(commands)

        results.append({
            'timestamp': state.timestamp,
            'L1': state.L1,
            'V': state.V,
            'F1': state.F1,
            'F2': state.F2,
            'price': state.electricity_price,
            'cost': state.total_energy_cost,
            'active_pumps': len(state.active_pumps),
            'violations': len(state.violations)
        })

        # Print every 4 hours
        if i % 16 == 0:
            print(f"t={i*15:3d}min: L1={state.L1:.2f}m, V={state.V:6.0f}m³, F1={state.F1:4.0f}m³/15min, "
                  f"F2={state.F2:4.0f}m³/h, Cost={state.total_energy_cost:.2f}EUR")

    # Convert to dataframe
    df = pd.DataFrame(results)

    print(f"\n=== 24-Hour Summary ===")
    print(f"Final L1: {df['L1'].iloc[-1]:.2f}m (started at {df['L1'].iloc[0]:.2f}m)")
    print(f"L1 range: {df['L1'].min():.2f}m - {df['L1'].max():.2f}m")
    print(f"Total energy cost: {df['cost'].iloc[-1]:.2f} EUR")
    print(f"Total violations: {df['violations'].sum()}")
    print(f"Avg price: {df['price'].mean():.3f} EUR/kWh")
    print(f"Avg F2: {df['F2'].mean():.0f} m³/h")

    print("\n✓ Simulator test completed successfully!")
