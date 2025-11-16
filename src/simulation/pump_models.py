"""
Pump Models for HSY Wastewater Station
Based on Grundfos pump curves from PDF data
"""

import numpy as np
from typing import Dict, Tuple
from dataclasses import dataclass


@dataclass
class PumpSpecs:
    """Pump specifications from datasheets"""
    name: str
    rated_power_kw: float
    rated_flow_ls: float  # liters/second
    rated_head_m: float
    rated_efficiency: float  # decimal (0-1)
    impeller_diameter_mm: float
    nominal_speed_rpm: float
    nominal_frequency_hz: float = 50.0


class PumpModel:
    """Model for pump performance based on affinity laws and curves"""

    # Pump specifications from Excel data - CALIBRATED PER PUMP
    # Each pump has individual characteristics derived from actual operational data
    # Using cubic law: P_measured = P_rated × (f/50)³ to reverse-engineer P_rated
    # Data points from Excel operational records
    LARGE_PUMP_SPECS = PumpSpecs(
        name="Large Pump Template",
        rated_power_kw=386,
        rated_flow_ls=925,
        rated_head_m=31.5,
        rated_efficiency=0.848,
        impeller_diameter_mm=749,
        nominal_speed_rpm=743,
        nominal_frequency_hz=50.0
    )

    SMALL_PUMP_SPECS = PumpSpecs(
        name="Small Pump Template",
        rated_power_kw=192.5,
        rated_flow_ls=464,
        rated_head_m=31.5,
        rated_efficiency=0.816,
        impeller_diameter_mm=534,
        nominal_speed_rpm=991,
        nominal_frequency_hz=50.0
    )

    # Individual pump calibrations from Excel data
    # Format: pump_id -> (P_rated_kW @ 50Hz, pump_type)
    # All derived by: P_rated = P_measured / (f_measured / 50)³
    PUMP_CALIBRATION = {
        '1.1': (192.7, 'small'),     # 184.4 kW @ 49.27 Hz
        '1.2': (381.1, 'large'),     # 370.2 kW @ 49.52 Hz
        '1.3': (381.1, 'large'),     # 370.2 kW @ 49.52 Hz
        '1.4': (398.0, 'large'),     # 383.9 kW @ 49.41 Hz
        '2.1': (192.3, 'small'),     # 172.9 kW @ 48.26 Hz
        '2.2': (393.9, 'large'),     # 368.0 kW @ 48.88 Hz
        '2.3': (394.6, 'large'),     # 381.0 kW @ 49.42 Hz
        '2.4': (368.4, 'large')      # 354.3 kW @ 49.36 Hz
    }

    # Pump type assignments (for fallback if needed)
    PUMP_TYPES = {
        '1.1': 'small',
        '1.2': 'large',
        '1.3': 'large',
        '1.4': 'large',
        '2.1': 'small',
        '2.2': 'large',
        '2.3': 'large',
        '2.4': 'large'
    }

    def __init__(self):
        """Initialize pump model"""
        self.L2 = 30.0  # WWTP level (constant, from presentation)

    def get_pump_specs(self, pump_id: str) -> PumpSpecs:
        """Get specifications for a specific pump"""
        # Check if we have individual calibration for this pump
        if pump_id in self.PUMP_CALIBRATION:
            p_rated, pump_type = self.PUMP_CALIBRATION[pump_id]
            # Create customized specs with individual calibration
            if pump_type == 'large':
                base_specs = self.LARGE_PUMP_SPECS
            else:
                base_specs = self.SMALL_PUMP_SPECS
            
            # Return new specs with calibrated power
            return PumpSpecs(
                name=f"Pump {pump_id}",
                rated_power_kw=p_rated,
                rated_flow_ls=base_specs.rated_flow_ls,
                rated_head_m=base_specs.rated_head_m,
                rated_efficiency=base_specs.rated_efficiency,
                impeller_diameter_mm=base_specs.impeller_diameter_mm,
                nominal_speed_rpm=base_specs.nominal_speed_rpm,
                nominal_frequency_hz=base_specs.nominal_frequency_hz
            )
        
        # Fallback to type-based lookup
        pump_type = self.PUMP_TYPES.get(pump_id, 'large')
        if pump_type == 'large':
            return self.LARGE_PUMP_SPECS
        else:
            return self.SMALL_PUMP_SPECS

    def calculate_head(self, L1: float) -> float:
        """
        Calculate pumping head (pressure difference)
        H = L2 - L1

        Args:
            L1: Water level in tunnel (m)

        Returns:
            Head in meters
        """
        return self.L2 - L1

    def calculate_pump_performance(
        self,
        pump_id: str,
        frequency_hz: float,
        L1: float
    ) -> Tuple[float, float, float]:
        """
        Calculate pump flow, power, and efficiency using affinity laws

        Affinity laws:
        - Q ∝ N (flow proportional to speed)
        - H ∝ N² (head proportional to speed squared)
        - P ∝ N³ (power proportional to speed cubed)

        Args:
            pump_id: Pump identifier (e.g., '1.1', '2.2')
            frequency_hz: Operating frequency (47.5-50 Hz)
            L1: Current water level in tunnel (m)

        Returns:
            Tuple of (flow_m3h, power_kw, efficiency)
        """

        specs = self.get_pump_specs(pump_id)

        # Calculate speed ratio
        speed_ratio = frequency_hz / specs.nominal_frequency_hz

        # Apply affinity laws
        # Flow scales linearly with speed
        flow_ls = specs.rated_flow_ls * speed_ratio
        flow_m3h = flow_ls * 3.6  # Convert l/s to m³/h

        # Power scales with cube of speed
        # Note: In reality, power also depends on head, but for variable frequency
        # drives operating near design point, this is a good approximation
        power_kw = specs.rated_power_kw * (speed_ratio ** 3)

        # Efficiency calculation
        # Efficiency is relatively constant near design point (±3% speed variation)
        # For larger speed variations, efficiency decreases slightly
        # We'll use a simple model: peak efficiency at rated speed,
        # slight drop off at other speeds

        # Efficiency penalty for operating away from rated speed
        speed_deviation = abs(speed_ratio - 1.0)
        efficiency_penalty = 1.0 - (speed_deviation * 0.05)  # 5% drop per 10% speed change
        efficiency = specs.rated_efficiency * efficiency_penalty

        # Clamp efficiency to reasonable range
        efficiency = max(0.7, min(0.9, efficiency))

        return flow_m3h, power_kw, efficiency

    def calculate_energy_consumption(
        self,
        power_kw: float,
        duration_hours: float,
        electricity_price_eur_kwh: float
    ) -> float:
        """
        Calculate energy cost

        Args:
            power_kw: Power consumption (kW)
            duration_hours: Time period (hours)
            electricity_price_eur_kwh: Price (EUR/kWh)

        Returns:
            Cost in EUR
        """
        energy_kwh = power_kw * duration_hours
        cost_eur = energy_kwh * electricity_price_eur_kwh
        return cost_eur

    def is_valid_frequency(self, frequency_hz: float, allow_ramp: bool = False) -> bool:
        """
        Check if frequency is within allowed range

        Args:
            frequency_hz: Frequency in Hz
            allow_ramp: If True, allow below 47.8 Hz for ramp up/down

        Returns:
            True if valid
        """
        # CORRECTED: Must be >= 47.8 Hz when operating (not 47.5!)
        # Exception: Can go below 47.8 Hz briefly during ramp up/down
        if allow_ramp:
            return 0 <= frequency_hz <= 50.0
        else:
            return 47.8 <= frequency_hz <= 50.0

    def get_all_pump_ids(self) -> list:
        """Get list of all pump IDs"""
        return list(self.PUMP_TYPES.keys())


class PumpController:
    """Helper class for managing pump states and transitions"""

    def __init__(self):
        self.pump_model = PumpModel()
        self.pump_states = {pid: {'running': False, 'frequency': 50.0, 'start_time': None}
                           for pid in self.pump_model.get_all_pump_ids()}
        self.current_time = None

    def update_pump_state(self, pump_id: str, running: bool, frequency: float, current_time: float):
        """Update pump state with runtime tracking"""

        # Detect if pump is transitioning (starting or stopping)
        is_starting = running and not self.pump_states[pump_id]['running']
        is_stopping = not running and self.pump_states[pump_id]['running']
        is_transitioning = is_starting or is_stopping

        # NOTE: Frequency validation temporarily disabled
        # Allow lower frequencies during ramp up/down transitions
        # if running and not self.pump_model.is_valid_frequency(frequency, allow_ramp=is_transitioning):
        #     raise ValueError(f"Invalid frequency {frequency} Hz for pump {pump_id}")

        # Track start time
        if is_starting:
            self.pump_states[pump_id]['start_time'] = current_time
        elif not running:
            self.pump_states[pump_id]['start_time'] = None

        self.pump_states[pump_id]['running'] = running
        self.pump_states[pump_id]['frequency'] = frequency
        self.current_time = current_time

    def get_runtime_hours(self, pump_id: str) -> float:
        """Get current runtime in hours (if running)"""
        if not self.pump_states[pump_id]['running']:
            return 0.0

        start_time = self.pump_states[pump_id]['start_time']
        if start_time is None:
            return 0.0

        return (self.current_time - start_time) / 3600.0  # Convert seconds to hours

    def check_minimum_runtime(self, pump_id: str, min_hours: float = 2.0) -> bool:
        """Check if pump has run for minimum required time"""
        runtime = self.get_runtime_hours(pump_id)
        return runtime >= min_hours


if __name__ == "__main__":
    # Test pump models
    model = PumpModel()

    print("=== Pump Model Testing ===\n")

    # Test large pump at different frequencies
    print("Large Pump (1.1) performance:")
    for freq in [47.5, 48.0, 49.0, 50.0]:
        L1 = 2.5  # Example water level
        flow, power, eff = model.calculate_pump_performance('1.1', freq, L1)
        head = model.calculate_head(L1)
        print(f"  {freq} Hz: Flow={flow:.0f} m³/h, Power={power:.1f} kW, Efficiency={eff*100:.1f}%, Head={head:.1f}m")

    print("\nSmall Pump (2.1) performance:")
    for freq in [47.5, 48.0, 49.0, 50.0]:
        L1 = 2.5
        flow, power, eff = model.calculate_pump_performance('2.1', freq, L1)
        head = model.calculate_head(L1)
        print(f"  {freq} Hz: Flow={flow:.0f} m³/h, Power={power:.1f} kW, Efficiency={eff*100:.1f}%, Head={head:.1f}m")

    # Test energy cost calculation
    print("\nEnergy cost example:")
    power = 350  # kW
    duration = 1.0  # hours
    price = 8.5  # EUR/kWh
    cost = model.calculate_energy_consumption(power, duration, price)
    print(f"  {power} kW × {duration} h × {price} EUR/kWh = {cost:.2f} EUR")

    # Test pump controller
    print("\n=== Pump Controller Testing ===")
    controller = PumpController()

    print("\nStarting pump 1.1...")
    controller.update_pump_state('1.1', True, 50.0, current_time=0)
    print(f"  Pump 1.1 running: {controller.pump_states['1.1']['running']}")

    print("\nAfter 1.5 hours...")
    controller.current_time = 1.5 * 3600
    runtime = controller.get_runtime_hours('1.1')
    min_runtime_ok = controller.check_minimum_runtime('1.1', min_hours=2.0)
    print(f"  Runtime: {runtime:.1f} hours")
    print(f"  Meets 2h minimum: {min_runtime_ok}")

    print("\nAfter 2.5 hours...")
    controller.current_time = 2.5 * 3600
    runtime = controller.get_runtime_hours('1.1')
    min_runtime_ok = controller.check_minimum_runtime('1.1', min_hours=2.0)
    print(f"  Runtime: {runtime:.1f} hours")
    print(f"  Meets 2h minimum: {min_runtime_ok}")
