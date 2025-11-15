"""
System Constraints and Boundaries
Updated with correct challenge specifications
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class SystemConstraints:
    """
    Operational constraints for HSY Blominmäki pumping station
    Based on official challenge specifications
    """

    # Water level constraints (meters)
    L1_MIN: float = 0.0  # Minimum water level
    L1_MAX: float = 8.0  # Maximum water level (hard limit)
    L1_ALARM: float = 7.2  # Alarm threshold
    L1_EMPTY: float = 0.5  # Emptying target level

    # Pump frequency constraints (Hz)
    FREQ_MIN: float = 47.8  # Minimum operating frequency (CORRECTED from 47.5!)
    FREQ_NOMINAL: float = 50.0  # Nominal frequency
    # Note: Can run below 47.8 Hz ONLY briefly during ramp up/down

    # Flow constraints (m³/h)
    F2_MAX: float = 16000.0  # Maximum total pumped flow (= 5 large pumps)

    # Runtime constraints
    MIN_RUNTIME_HOURS: float = 2.0  # Minimum pump runtime if started

    # Operational constraints
    MIN_ACTIVE_PUMPS: int = 1  # At least 1 pump must ALWAYS be running
    MAX_LARGE_PUMPS: int = 5  # Max 5 large pumps simultaneously (to stay under F2_MAX)

    # Daily emptying constraint
    DAILY_EMPTYING_REQUIRED: bool = True
    EMPTYING_FREQUENCY_HOURS: float = 24.0  # Once every 24 hours
    EMPTYING_ONLY_DRY_WEATHER: bool = True  # Only during dry weather!

    # Pump specifications
    LARGE_PUMP_RATED_FLOW: float = 3330.0  # m³/h at 50 Hz
    SMALL_PUMP_RATED_FLOW: float = 1670.0  # m³/h at 50 Hz
    LARGE_PUMP_RATED_POWER: float = 400.0  # kW at 50 Hz
    SMALL_PUMP_RATED_POWER: float = 250.0  # kW at 50 Hz

    # System configuration
    NUM_LARGE_PUMPS: int = 6  # Pumps 1.1, 1.2, 1.4, 2.2, 2.3, 2.4
    NUM_SMALL_PUMPS: int = 2  # Pumps 1.3, 2.1
    TOTAL_PUMPS: int = 8

    # Elevation constants
    L2_WWTP: float = 30.0  # WWTP elevation (constant)

    # Dry weather threshold (for emptying constraint)
    DRY_WEATHER_INFLOW_THRESHOLD: float = 1000.0  # m³/15min - if below, consider "dry"

    def is_dry_weather(self, inflow_F1: float) -> bool:
        """
        Determine if current conditions are "dry weather"
        Used for daily emptying constraint

        Args:
            inflow_F1: Current inflow in m³/15min

        Returns:
            True if dry weather conditions
        """
        return inflow_F1 < self.DRY_WEATHER_INFLOW_THRESHOLD

    def validate_frequency(self, frequency: float, allow_ramp: bool = False) -> bool:
        """
        Check if frequency is valid

        Args:
            frequency: Operating frequency in Hz
            allow_ramp: If True, allow below 47.8 Hz (for ramp up/down)

        Returns:
            True if valid
        """
        if allow_ramp:
            return 0 <= frequency <= self.FREQ_NOMINAL
        else:
            return self.FREQ_MIN <= frequency <= self.FREQ_NOMINAL

    def validate_total_flow(self, total_F2: float) -> bool:
        """Check if total pumped flow is within limits"""
        return total_F2 <= self.F2_MAX

    def validate_water_level(self, L1: float) -> tuple[bool, str]:
        """
        Validate water level and return status

        Returns:
            (is_valid, status_message)
        """
        if L1 < self.L1_MIN:
            return False, f"CRITICAL: L1={L1:.2f}m below minimum {self.L1_MIN}m"
        elif L1 > self.L1_MAX:
            return False, f"CRITICAL: L1={L1:.2f}m exceeds maximum {self.L1_MAX}m"
        elif L1 > self.L1_ALARM:
            return True, f"WARNING: L1={L1:.2f}m exceeds alarm threshold {self.L1_ALARM}m"
        else:
            return True, "OK"

    def get_pump_config(self) -> Dict[str, str]:
        """Get pump type assignments"""
        return {
            '1.1': 'large',
            '1.2': 'large',
            '1.3': 'small',  # Never used in historical data
            '1.4': 'large',
            '2.1': 'small',
            '2.2': 'large',
            '2.3': 'large',
            '2.4': 'large'
        }


# Global instance
CONSTRAINTS = SystemConstraints()


if __name__ == "__main__":
    """Test constraints"""

    print("=== System Constraints ===\n")

    c = CONSTRAINTS

    print(f"Water Level Limits:")
    print(f"  Min: {c.L1_MIN}m")
    print(f"  Alarm: {c.L1_ALARM}m")
    print(f"  Max: {c.L1_MAX}m")
    print(f"  Empty target: {c.L1_EMPTY}m")

    print(f"\nFrequency Limits:")
    print(f"  Min operating: {c.FREQ_MIN} Hz (CORRECTED!)")
    print(f"  Nominal: {c.FREQ_NOMINAL} Hz")
    print(f"  Note: Can go below {c.FREQ_MIN} Hz only during ramp up/down")

    print(f"\nFlow Limits:")
    print(f"  Max total pumped flow (F2): {c.F2_MAX} m³/h")
    print(f"  = {c.F2_MAX / c.LARGE_PUMP_RATED_FLOW:.1f} large pumps")

    print(f"\nOperational Rules:")
    print(f"  Min active pumps: {c.MIN_ACTIVE_PUMPS} (ALWAYS!)")
    print(f"  Min runtime: {c.MIN_RUNTIME_HOURS}h")
    print(f"  Daily emptying: {c.DAILY_EMPTYING_REQUIRED}")
    print(f"  Only during dry weather: {c.EMPTYING_ONLY_DRY_WEATHER}")

    print(f"\nPump Configuration:")
    print(f"  Large pumps: {c.NUM_LARGE_PUMPS} × {c.LARGE_PUMP_RATED_POWER}kW, {c.LARGE_PUMP_RATED_FLOW}m³/h")
    print(f"  Small pumps: {c.NUM_SMALL_PUMPS} × {c.SMALL_PUMP_RATED_POWER}kW, {c.SMALL_PUMP_RATED_FLOW}m³/h")

    # Test validation
    print(f"\n=== Testing Validations ===")

    # Frequency validation
    print(f"\nFrequency tests:")
    print(f"  47.0 Hz (ramping): {c.validate_frequency(47.0, allow_ramp=True)}")
    print(f"  47.0 Hz (normal): {c.validate_frequency(47.0, allow_ramp=False)}")
    print(f"  47.8 Hz: {c.validate_frequency(47.8, allow_ramp=False)}")
    print(f"  50.0 Hz: {c.validate_frequency(50.0, allow_ramp=False)}")

    # Water level validation
    print(f"\nWater level tests:")
    for L1 in [1.0, 5.0, 7.5, 8.5]:
        valid, msg = c.validate_water_level(L1)
        print(f"  L1={L1}m: {msg}")

    # Dry weather test
    print(f"\nDry weather tests:")
    for F1 in [500, 800, 1200, 2000]:
        is_dry = c.is_dry_weather(F1)
        print(f"  F1={F1}m³/15min: {'DRY' if is_dry else 'WET'}")

    # Flow validation
    print(f"\nFlow validation:")
    print(f"  F2=10,000 m³/h: {c.validate_total_flow(10000)}")
    print(f"  F2=16,000 m³/h: {c.validate_total_flow(16000)}")
    print(f"  F2=18,000 m³/h: {c.validate_total_flow(18000)}")
