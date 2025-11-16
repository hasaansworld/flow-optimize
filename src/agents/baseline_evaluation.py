"""
Baseline Evaluation Script

This script evaluates a SIMPLE baseline policy and saves the results to:
  baseline_evaluation.json
at the project root.

Baseline policy:
  - At each timestep, use the historical pump frequencies from the dataset.
  - This approximates "what operators actually did" as the baseline.
"""

import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'simulation'))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'config'))

from base_agent import SystemState
from data_loader import HSYDataLoader
from physics_simulator import PumpCommand
from pump_models import PumpModel
from constraints import CONSTRAINTS


class BaselineEvaluator:
    """
    Baseline controller that simply replays historical pump frequencies.
    Uses the same closed-loop tank simulation logic as the AI evaluator.
    """

    # Map pump IDs to the corresponding column names in the data
    # Adjust these column names if your Excel headers are slightly different.
    PUMP_FREQ_COLUMNS = {
        "1.1": "Pump frequency 1.1",
        "1.2": "Pump frequency 1.2",
        "1.3": "Pump frequency 1.3",
        "1.4": "Pump frequency 1.4",
        "2.1": "Pump frequency 2.1",
        "2.2": "Pump frequency 2.2",
        "2.3": "Pump frequency 2.3",
        "2.4": "Pump frequency 2.4",
    }

    def __init__(self, price_scenario: str = "normal"):
        self.price_scenario = price_scenario

        print("\n" + "=" * 60)
        print("BASELINE EVALUATION (Historical Pump Frequencies)")
        print("=" * 60)

        # Load data
        print("\nLoading historical data...")
        self.loader = HSYDataLoader()
        data_dict = self.loader.load_all_data()
        self.data = data_dict["operational_data"]
        print(f"✓ Loaded {len(self.data)} timesteps of data")

        # Pump model
        self.pump_model = PumpModel()

        # Metrics
        self.total_cost_eur = 0.0
        self.total_energy_kwh = 0.0
        self.total_flow_m3 = 0.0
        self.constraint_violations = []
        self.predictions = []

        # Approximate tank area from historical L1/V
        try:
            V_series = self.data["V"]
            L1_series = self.data["L1"]
            dV = float(V_series.max() - V_series.min())
            dL1 = float(L1_series.max() - L1_series.min())
            self.tank_area = dV / dL1 if dL1 != 0 else 1.0
        except Exception:
            self.tank_area = 1.0

        # Simulated storage state (initialized in run)
        self.sim_V = None
        self.sim_L1 = None

    def calculate_pump_performance(self, pump_id: str, frequency: float, L1: float):
        """
        Same logic as in run_evaluation: compute flow (m³/h) and power (kW) for a pump.
        """
        if frequency <= 0.0:
            return 0.0, 0.0, 0.0

        real_pump_id = pump_id  # Here we use actual IDs 1.1, 1.2, etc.

        try:
            flow, power, efficiency = self.pump_model.calculate_pump_performance(
                real_pump_id, frequency, L1
            )
            return flow, power, efficiency
        except Exception:
            # Fallback to affinity laws with default specs
            try:
                specs = self.pump_model.get_pump_specs(real_pump_id)
            except Exception:
                if real_pump_id in ["1.1", "1.2", "1.4", "2.2", "2.3", "2.4"]:
                    specs = self.pump_model.LARGE_PUMP_SPECS
                else:
                    specs = self.pump_model.SMALL_PUMP_SPECS

            freq_ratio = frequency / 50.0
            flow_m3h = specs.rated_flow_ls * freq_ratio * 3.6
            power_kw = specs.rated_power_kw * (freq_ratio ** 3)
            efficiency = max(
                0.7, specs.rated_efficiency * max(0.95, 1.0 - abs(freq_ratio - 1.0) * 0.05)
            )
            return flow_m3h, power_kw, efficiency

    def run(self, start_index: int = 0, num_steps: int = 100) -> dict:
        """
        Run baseline evaluation.

        Uses:
          - Historical inflow F1 as exogenous input.
          - Historical pump frequencies for each pump as the control action.
          - Closed-loop mass balance to update volume/level.
        """
        print("\n" + "=" * 60)
        print("RUNNING BASELINE SIMULATION")
        print("=" * 60)
        print(f"Simulating {num_steps} timesteps ({num_steps * 0.25:.1f} hours)")
        print()

        price_col = "Price_High" if self.price_scenario == "high" else "Price_Normal"

        if start_index >= len(self.data):
            print("❌ start_index beyond data length, nothing to simulate.")
            return {
                "metadata": {
                    "timesteps_requested": num_steps,
                    "timesteps_completed": 0,
                    "duration_hours": 0.0,
                    "price_scenario": self.price_scenario,
                    "start_index": start_index,
                    "completed_successfully": False,
                },
                "metrics": {
                    "total_cost_eur": 0.0,
                    "total_energy_kwh": 0.0,
                    "total_flow_m3": 0.0,
                    "specific_energy_kwh_per_m3": 0.0,
                },
                "violations": {"count": 0, "details": []},
                "predictions": [],
            }

        # Initialize simulated storage state from the chosen start row
        first_row = self.data.iloc[start_index]
        try:
            self.sim_V = float(first_row["V"])
        except Exception:
            self.sim_V = float(first_row.get("L1", 0.0))

        try:
            self.sim_L1 = float(first_row["L1"])
        except Exception:
            self.sim_L1 = self.sim_V / self.tank_area if self.tank_area > 0 else 0.0

        for i in range(num_steps):
            idx = start_index + i
            if idx >= len(self.data):
                print("⚠️ Reached end of data")
                break

            row = self.data.iloc[idx]

            timestamp = row["Time stamp"]
            inflow_F1 = float(row["F1"])  # assume m³ per 15-min
            price = float(row[price_col])

            # Build SystemState with simulated L1/V
            state = SystemState(
                timestamp=timestamp,
                L1=self.sim_L1,
                V=self.sim_V,
                F1=inflow_F1,
                F2=0.0,  # outflow is decided by pump frequencies
                electricity_price=price,
                price_scenario=self.price_scenario,
                active_pumps={},  # not needed for baseline
                historical_data=self.data,
                current_index=idx,
            )

            # ---- Baseline policy: use historical pump frequencies ----
            pump_commands = []
            for pump_id, col_name in self.PUMP_FREQ_COLUMNS.items():
                if col_name in self.data.columns:
                    freq = float(row[col_name])
                else:
                    # If column missing, assume pump off
                    freq = 0.0

                start = freq > 0.0
                pump_commands.append(
                    PumpCommand(pump_id=pump_id, start=start, frequency=freq)
                )

            # ---- Compute flow/power/cost just like in AI evaluation ----
            enhanced_commands = []
            total_flow_m3h = 0.0
            total_power_kw = 0.0

            for cmd in pump_commands:
                eff_freq = cmd.frequency if cmd.start else 0.0
                flow, power, eff = self.calculate_pump_performance(
                    cmd.pump_id, eff_freq, state.L1
                )

                enhanced_commands.append(
                    {
                        "pump_id": cmd.pump_id,
                        "start": cmd.start,
                        "frequency_hz": cmd.frequency,
                        "flow_m3h": flow,
                        "power_kw": power,
                        "efficiency": eff,
                    }
                )

                if cmd.start:
                    total_flow_m3h += flow
                    total_power_kw += power

            # 15-min step -> 0.25 h
            energy_kwh = total_power_kw * 0.25
            cost_eur = energy_kwh * price
            flow_m3 = total_flow_m3h * 0.25
            specific_energy = energy_kwh / flow_m3 if flow_m3 > 0 else 0.0

            self.total_cost_eur += cost_eur
            self.total_energy_kwh += energy_kwh
            self.total_flow_m3 += flow_m3

            # Constraint checks on simulated level & flow
            violations = []
            if state.L1 > CONSTRAINTS.L1_MAX or state.L1 < CONSTRAINTS.L1_MIN:
                violations.append(
                    {
                        "type": "L1_OUT_OF_RANGE",
                        "value": float(state.L1),
                        "limit": f"{CONSTRAINTS.L1_MIN}-{CONSTRAINTS.L1_MAX}",
                        "timestamp": str(timestamp),
                    }
                )

            if total_flow_m3h > CONSTRAINTS.F2_MAX:
                violations.append(
                    {
                        "type": "F2_EXCEEDED",
                        "value": float(total_flow_m3h),
                        "limit": float(CONSTRAINTS.F2_MAX),
                        "timestamp": str(timestamp),
                    }
                )

            if violations:
                self.constraint_violations.extend(violations)

            # Closed-loop mass balance: update simulated storage
            pumped_m3 = flow_m3
            inflow_m3 = inflow_F1 * 0.25 # convert m³/h -> m³ per 15 min
            self.sim_V = max(0.0, float(self.sim_V) + inflow_m3 - pumped_m3)
            if self.tank_area > 0:
                self.sim_L1 = self.sim_V / self.tank_area

            # Store per-step info (optional but nice for plots)
            self.predictions.append(
                {
                    "timestamp": str(timestamp),
                    "timestep": idx,
                    "pump_commands": enhanced_commands,
                    "system_state": {
                        "L1_m": float(state.L1),
                        "V_m3": float(state.V),
                        "F1_m3_per_15min": float(state.F1),
                        "F2_total_m3h": float(total_flow_m3h),
                        "electricity_price_eur_kwh": price,
                    },
                    "cost_calculation": {
                        "total_power_kw": float(total_power_kw),
                        "energy_kwh": float(energy_kwh),
                        "cost_eur": float(cost_eur),
                        "flow_pumped_m3": float(flow_m3),
                        "specific_energy_kwh_per_m3": float(specific_energy),
                    },
                    "constraint_violations": violations,
                }
            )

            if (i + 1) % 50 == 0:
                print(
                    f"Progress: {i+1}/{num_steps} | "
                    f"Cost so far: €{self.total_cost_eur:,.2f} | "
                    f"Violations: {len(self.constraint_violations)}"
                )

        # Final summary
        actual_steps = len(self.predictions)
        specific_energy_total = (
            self.total_energy_kwh / self.total_flow_m3
            if self.total_flow_m3 > 0
            else 0.0
        )

        print("\n" + "=" * 60)
        print("BASELINE EVALUATION COMPLETE")
        print("=" * 60)
        print(f"\nTimesteps completed: {actual_steps}/{num_steps}")
        print(f"Total cost:          €{self.total_cost_eur:,.2f}")
        print(f"Total energy:        {self.total_energy_kwh:,.2f} kWh")
        print(f"Total flow pumped:   {self.total_flow_m3:,.2f} m³")
        print(f"Specific energy:     {specific_energy_total:.6f} kWh/m³")
        print(f"Constraint violations: {len(self.constraint_violations)}")

        return {
            "metadata": {
                "timesteps_requested": num_steps,
                "timesteps_completed": actual_steps,
                "duration_hours": actual_steps * 0.25,
                "price_scenario": self.price_scenario,
                "start_index": start_index,
                "completed_successfully": actual_steps == num_steps,
            },
            "metrics": {
                "total_cost_eur": self.total_cost_eur,
                "total_energy_kwh": self.total_energy_kwh,
                "total_flow_m3": self.total_flow_m3,
                "specific_energy_kwh_per_m3": specific_energy_total,
            },
            "violations": {
                "count": len(self.constraint_violations),
                "details": self.constraint_violations,
            },
            "predictions": self.predictions,
        }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Run baseline evaluation")
    parser.add_argument(
        "--price",
        choices=["normal", "high"],
        default="normal",
        help="Price scenario to use (normal/high)",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=100,
        help="Number of timesteps (15-min) to simulate",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=0,
        help="Start index in the historical dataset",
    )
    args = parser.parse_args()

    evaluator = BaselineEvaluator(price_scenario=args.price)
    results = evaluator.run(start_index=args.start, num_steps=args.steps)

    # Save baseline_evaluation.json at project root (same place run_evaluation expects it)
    root = Path(__file__).parent.parent.parent
    out_file = root / "baseline_evaluation.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Saved baseline evaluation to: {out_file}")


if __name__ == "__main__":
    main()
