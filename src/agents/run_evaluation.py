"""
Run Multi-Agent System with Full Evaluation Tracking

This script runs the multi-agent system and tracks all metrics needed
for comparison with baseline:
- Total cost (EUR)
- Energy consumption (kWh)
- Specific energy (kWh/m³)
- Constraint violations
"""

import sys
from pathlib import Path
import time
import json
from datetime import datetime
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'simulation'))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'config'))

from base_agent import SystemState
from specialist_agents import create_all_agents
from coordinator_agent import CoordinatorAgent
from data_loader import HSYDataLoader
from physics_simulator import PumpCommand
from pump_models import PumpModel
from constraints import CONSTRAINTS


class EvaluationController:
    """
    Multi-Agent Controller with Full Evaluation Tracking
    """

    def __init__(
        self,
        lstm_model_path: str,
        price_scenario: str = 'normal'
    ):
        print("\n" + "="*60)
        print("MULTI-AGENT WASTEWATER SYSTEM - EVALUATION MODE")
        print("="*60)
        print()

        # Create agents
        print("Initializing agents...")
        self.specialist_agents = create_all_agents(lstm_model_path)
        self.coordinator = CoordinatorAgent()
        print(f"✓ All agents initialized ({len(self.specialist_agents)} specialists + 1 coordinator)")

        # Load historical data
        print("\nLoading historical data...")
        self.loader = HSYDataLoader()
        data_dict = self.loader.load_all_data()
        self.data = data_dict['operational_data']
        print(f"✓ Loaded {len(self.data)} timesteps of data")

        # Pump model for power calculation
        self.pump_model = PumpModel()

        # Settings
        self.price_scenario = price_scenario

        # Evaluation metrics
        self.total_cost = 0.0
        self.total_energy_kwh = 0.0
        self.total_flow_m3 = 0.0
        self.constraint_violations = []
        self.predictions = []

        # Track pump states across cycles for constraint compliance agent
        self.active_pumps = {}  # pump_id -> {'start_time': timestamp, 'frequency': float}
        self.pump_start_times = {}  # pump_id -> when it was turned on

        # Approximate tank surface area from historical L1/V data
        # This lets us convert between stored volume (V) and level (L1) in the simulator.
        try:
            V_series = self.data['V']
            L1_series = self.data['L1']
            dV = float(V_series.max() - V_series.min())
            dL1 = float(L1_series.max() - L1_series.min())
            self.tank_area = dV / dL1 if dL1 != 0 else 1.0
        except Exception:
            # Fallback: arbitrary area of 1.0 m² if we cannot compute it
            self.tank_area = 1.0

        # Simulated level/volume for closed-loop evaluation
        # These are initialized in run_evaluation based on the chosen start index.
        self.sim_L1 = None
        self.sim_V = None

        print(f"\nSettings:")
        print(f"  Price scenario: {price_scenario.upper()}")

    def calculate_pump_power(self, pump_id: str, frequency: float, L1: float) -> tuple:
        """
        Calculate flow and power for a pump command

        Returns:
            (flow_m3h, power_kw, efficiency)
        """
        if frequency == 0:
            return 0, 0, 0

        # Map legacy pump IDs to real IDs
        pump_id_map = {'P1L': '1.1', 'P2L': '2.1'}
        real_pump_id = pump_id_map.get(pump_id, pump_id)

        try:
            flow, power, efficiency = self.pump_model.calculate_pump_performance(
                real_pump_id, frequency, L1
            )
            return flow, power, efficiency
        except Exception as e:
            # Fallback: still use PumpModel specs but with simple affinity laws
            try:
                specs = self.pump_model.get_pump_specs(real_pump_id)
            except:
                # If even mapping fails, use hard specs
                if 'large' in pump_id.lower() or real_pump_id in ['1.1', '1.2', '1.4', '2.2', '2.3', '2.4']:
                    specs = self.pump_model.LARGE_PUMP_SPECS
                else:
                    specs = self.pump_model.SMALL_PUMP_SPECS

            freq_ratio = frequency / 50.0

            flow = specs.rated_flow_ls * freq_ratio * 3.6  # l/s to m³/h
            power = specs.rated_power_kw * (freq_ratio ** 3)  # Cubic law
            efficiency = max(0.7, specs.rated_efficiency * max(0.95, 1.0 - abs(freq_ratio - 1.0) * 0.05))

            return flow, power, efficiency

    def _validate_and_correct_pump_commands(self, pump_commands: list, state: SystemState) -> list:
        """
        Validate pump commands for minimum operational requirements.

        MINIMAL validation - let coordinator make smart decisions:
        - Ensure at least 1 pump is running (hard constraint)
        - Don't force additional pumps (that's coordinator's job, considering price)
        - Only warn if flow is insufficient
        """
        active_pumps = [cmd for cmd in pump_commands if cmd.start]

        # Calculate what the current commands will produce
        current_total_flow = 0
        for cmd in active_pumps:
            flow, _, _ = self.calculate_pump_power(cmd.pump_id, cmd.frequency, state.L1)
            current_total_flow += flow

        min_required_flow = state.F1 if state.F1 > 0 else 0.0  # ✅

        # HARD constraint: at least one pump must be running
        if len(active_pumps) == 0:
            print("  ⚠️ VALIDATION: No pumps active! Enabling P1L at minimum frequency")
            # Try to find existing P1L command
            found = False
            for cmd in pump_commands:
                if cmd.pump_id == 'P1L':
                    cmd.start = True
                    cmd.frequency = 47.8
                    found = True
                    break
            # If no P1L command exists, add one explicitly
            if not found:
                pump_commands.append(PumpCommand(pump_id='P1L', start=True, frequency=47.8))

            return pump_commands

        # CHECK (but don't fix): Warn if flow is insufficient
        if current_total_flow < min_required_flow:
            print(f"  ⚠️ WARNING: Flow may be insufficient - current_total_flow {current_total_flow:.0f}m³/h < inflow {min_required_flow:.0f}m³/h")
            print(f"     Coordinator should increase pump speeds or add pumps for cost savings")
        else:
            print(f"  ✓ Flow adequate: {current_total_flow:.0f}m³/h >= required {min_required_flow:.0f}m³/h")

        return pump_commands

    def run_decision_cycle(self, state: SystemState, timestep: int) -> dict:
        """
        Run one complete decision cycle with full tracking

        Returns:
            Dictionary with all evaluation data
            None if API fails (rate limit hit)
        """

        # Step 1: Run all specialist agents
        print(f"\n{'='*60}")
        print(f"TIMESTEP {timestep} - Decision Cycle {len(self.predictions) + 1}")
        print(f"{'='*60}")
        print(f"Time: {state.timestamp}")
        print(f"L1: {state.L1:.2f}m | F1: {state.F1:.0f} m³/15min | Price: €{state.electricity_price:.3f}/kWh")
        print(f"\n--- SPECIALIST AGENT ASSESSMENTS ---")

        recommendations = {}
        for name, agent in self.specialist_agents.items():
            try:
                rec = agent.assess(state)
                recommendations[name] = rec

                print(f"\n[{name}]")
                print(f"  Priority:   {rec.priority}")
                print(f"  Confidence: {rec.confidence:.2f}")
                print(f"  Type:       {rec.recommendation_type}")
                if rec.reasoning:
                    print(f"  Reasoning: {rec.reasoning[:150]}...")
                if rec.data:
                    try:
                        print(f"  Key Data: {str(rec.data)[:200]}...")
                    except Exception:
                        print("  Key Data: <unprintable>")
            except Exception as e:
                # Check if this is a rate limit error
                if "429" in str(e) or "quota" in str(e).lower() or "rate limit" in str(e).lower():
                    print(f"\n❌ API Rate Limit Hit in Specialist Agent '{name}' - Aborting evaluation")
                    return None
                print(f"⚠️ {name} failed: {e}")

        # Step 2: Coordinator synthesis
        print(f"\n--- COORDINATOR SYNTHESIS ---")
        try:
            pump_commands = self.coordinator.synthesize_recommendations(state, recommendations)

            # Print coordinator's decision
            if self.coordinator.history:
                decision = self.coordinator.history[-1]
                print(f"Coordinator Decision:")
                print(f"  Reasoning: {decision.reasoning[:200]}...")
                print(f"  Priority Applied: {decision.data.get('llm_response', {}).get('priority_applied', 'N/A')}")
                print(f"  Confidence: {decision.confidence:.2f}")
        except Exception as e:
            # Check if this is a rate limit error
            if "429" in str(e) or "quota" in str(e).lower() or "rate limit" in str(e).lower():
                print(f"\n❌ API Rate Limit Hit in Coordinator - Aborting evaluation")
                return None
            raise

        # Step 3: Validate and correct pump commands if needed
        # IMPORTANT: Ensure minimum viable flow to handle current inflow
        pump_commands = self._validate_and_correct_pump_commands(pump_commands, state)

        # Step 4: Calculate power and flow for each pump
        enhanced_commands = []
        total_power_kw = 0
        total_flow_m3h = 0

        for cmd in pump_commands:
            # Calculate power and flow for this pump
            # IMPORTANT: Use the frequency only if pump is started, otherwise 0
            pump_frequency = cmd.frequency if cmd.start else 0
            flow, power, efficiency = self.calculate_pump_power(
                cmd.pump_id,
                pump_frequency,
                state.L1
            )

            enhanced_commands.append({
                'pump_id': cmd.pump_id,
                'start': cmd.start,
                'frequency_hz': cmd.frequency,
                'flow_m3h': flow,
                'power_kw': power,
                'efficiency': efficiency
            })

            # Sum only active (started) pumps
            if cmd.start:
                total_power_kw += power
                total_flow_m3h += flow

        # Step 5: Calculate cost for this timestep
        # Energy = Power (kW) × Time (hours)
        # For 15-minute intervals: 15 min = 0.25 hours
        energy_kwh = total_power_kw * 0.25  # 15 min = 0.25 h
        cost_eur = energy_kwh * state.electricity_price
        flow_m3 = total_flow_m3h * 0.25  # Flow in 15 minutes
        specific_energy = energy_kwh / flow_m3 if flow_m3 > 0 else 0

        # Print pump commands and costs
        print(f"\n--- FINAL PUMP COMMANDS ---")
        active_pumps = [cmd for cmd in enhanced_commands if cmd['start']]
        print(f"Active Pumps: {len(active_pumps)}")
        for cmd in active_pumps:
            print(f"  {cmd['pump_id']}: {cmd['frequency_hz']:.1f} Hz -> {cmd['flow_m3h']:.1f} m³/h @ {cmd['power_kw']:.1f} kW (η={cmd['efficiency']:.1%})")
        print(f"\n💰 COST:")
        print(f"  Power: {total_power_kw:.1f} kW | Energy: {energy_kwh:.2f} kWh | Cost: €{cost_eur:.2f}")
        print(f"  Flow: {flow_m3:.0f} m³ | Specific Energy: {specific_energy:.6f} kWh/m³")

        # Step 6: Check constraints
        violations = []
        if state.L1 > CONSTRAINTS.L1_MAX or state.L1 < CONSTRAINTS.L1_MIN:
            violations.append({
                'type': 'L1_OUT_OF_RANGE',
                'value': state.L1,
                'limit': f'{CONSTRAINTS.L1_MIN}-{CONSTRAINTS.L1_MAX}'
            })

        if total_flow_m3h > CONSTRAINTS.F2_MAX:
            violations.append({
                'type': 'F2_EXCEEDED',
                'value': total_flow_m3h,
                'limit': CONSTRAINTS.F2_MAX
            })

        # Step 7: Accumulate metrics
        self.total_cost += cost_eur
        self.total_energy_kwh += energy_kwh
        self.total_flow_m3 += flow_m3
        if violations:
            self.constraint_violations.extend(violations)

        # Step 7b: UPDATE ACTIVE PUMPS STATE FOR NEXT CYCLE
        # This allows the Constraint Compliance Agent to track which pumps are running
        for cmd in pump_commands:
            if cmd.start:
                # Pump is starting or continuing
                if cmd.pump_id not in self.active_pumps:
                    # First time this pump starts - record start time
                    self.active_pumps[cmd.pump_id] = {
                        'start_time': state.timestamp,
                        'frequency': cmd.frequency
                    }
                else:
                    # Pump already running - just update frequency
                    self.active_pumps[cmd.pump_id]['frequency'] = cmd.frequency
            else:
                # Pump is stopping
                if cmd.pump_id in self.active_pumps:
                    del self.active_pumps[cmd.pump_id]

        # Step 8: Create prediction output
        prediction = {
            'timestamp': str(state.timestamp),
            'timestep': timestep,
            'decision_cycle': len(self.predictions) + 1,

            'pump_commands': enhanced_commands,

            'system_state': {
                'L1_m': float(state.L1),
                'V_m3': float(state.V),
                'F1_m3_per_15min': float(state.F1),
                'F2_total_m3h': float(total_flow_m3h),
                'electricity_price_eur_kwh': float(state.electricity_price)
            },

            'cost_calculation': {
                'total_power_kw': float(total_power_kw),
                'energy_kwh': float(energy_kwh),
                'cost_eur': float(cost_eur),
                'flow_pumped_m3': float(flow_m3),
                'specific_energy_kwh_per_m3': float(specific_energy)
            },

            'agent_assessments': {
                name: {
                    'priority': rec.priority,
                    'confidence': rec.confidence,
                    'recommendation_type': rec.recommendation_type
                }
                for name, rec in recommendations.items()
            },

            'constraint_violations': violations
        }

        self.predictions.append(prediction)

        return prediction

    def run_evaluation(self, start_index: int = 0, num_steps: int = 100):
        """
        Run evaluation over historical data in a CLOSED LOOP.

        Instead of replaying historical L1/V directly from the CSV, we:
        - Initialize simulated level/volume from the chosen start index.
        - At each timestep, use historical inflow (F1) and agent-decided pump outflow
          to update the simulated storage state.
        - Feed the simulated L1/V into the agents at the next step.

        Args:
            start_index: Starting timestep (row index in the historical dataframe)
            num_steps: Number of 15-min timesteps to simulate
        """
        print("\n" + "="*60)
        print("EVALUATION RUN")
        print("="*60)
        print(f"Simulating {num_steps} timesteps ({num_steps * 0.25:.1f} hours)")
        print()

        price_col = 'Price_High' if self.price_scenario == 'high' else 'Price_Normal'

        # Basic sanity check
        if start_index >= len(self.data):
            print("❌ start_index is beyond available data – nothing to simulate.")
            return {
                'metadata': {
                    'timesteps_requested': num_steps,
                    'timesteps_completed': 0,
                    'duration_hours': 0.0,
                    'price_scenario': self.price_scenario,
                    'start_index': start_index,
                    'completed_successfully': False,
                },
                'metrics': {
                    'total_cost_eur': 0.0,
                    'total_energy_kwh': 0.0,
                    'total_flow_m3': 0.0,
                    'specific_energy_kwh_per_m3': 0.0,
                },
                'violations': {
                    'count': 0,
                    'details': [],
                },
                'predictions': [],
            }

        # Initialise simulated storage state from the starting row
        first_row = self.data.iloc[start_index]
        try:
            self.sim_V = float(first_row['V'])
        except Exception:
            # If V is not available, fall back to using L1 as a proxy for storage
            self.sim_V = float(first_row.get('L1', 0.0))

        try:
            self.sim_L1 = float(first_row['L1'])
        except Exception:
            # If L1 is missing, derive it from volume and tank area
            self.sim_L1 = self.sim_V / self.tank_area if getattr(self, 'tank_area', 1.0) > 0 else 0.0

        # Main simulation loop
        for i in range(num_steps):
            idx = start_index + i

            if idx >= len(self.data):
                print("⚠️ Reached end of data")
                break

            row = self.data.iloc[idx]

            # Historical exogenous signals (things our policy cannot change)
            timestamp = row['Time stamp']
            inflow_F1 = float(row['F1'])   # Assumed m³ per 15-min interval
            electricity_price = float(row[price_col])

            # Build SystemState using the SIMULATED storage state
            state = SystemState(
                timestamp=timestamp,
                L1=self.sim_L1,
                V=self.sim_V,
                F1=inflow_F1,
                F2=0.0,  # Outflow is determined by our pump commands, not taken from CSV
                electricity_price=electricity_price,
                price_scenario=self.price_scenario,
                active_pumps=self.active_pumps.copy(),  # Pass previous pump states
                historical_data=self.data,
                current_index=idx,
            )

            # Run full decision cycle for this timestep
            prediction = self.run_decision_cycle(state, idx)

            # If API failed (e.g. rate limit), abort the run and keep partial results
            if prediction is None:
                print(f"\n⚠️ Stopping evaluation at timestep {i+1}/{num_steps} due to API issue")
                print(f"⚠️ Returning results for {len(self.predictions)} completed timesteps")
                break

            # --- CLOSED-LOOP STATE UPDATE ---
            # Use pump outflow from the decision cycle and historical inflow to update storage.
            try:
                # Pumped volume during this 15-min step (m³)
                pumped_m3 = float(prediction['cost_calculation']['flow_pumped_m3'])
            except Exception:
                # Fallback: if for some reason the key is missing, assume zero pumped volume
                pumped_m3 = 0.0

            # Inflow during this 15-min step (m³). F1 is already per 15-min in the dataset.
            inflow_m3 = inflow_F1 * 0.25  # ✅ convert m³/h -> m³ per 15 min

            # Mass balance: new volume = old volume + inflow − outflow
            self.sim_V = max(0.0, float(self.sim_V) + inflow_m3 - pumped_m3)

            # Convert volume back to level using the approximate tank area
            if getattr(self, 'tank_area', 1.0) > 0:
                self.sim_L1 = self.sim_V / self.tank_area

            # Progress update every 50 timesteps
            if (i + 1) % 50 == 0:
                print(
                    f"Progress: {i+1}/{num_steps} timesteps | "
                    f"Cost so far: €{self.total_cost:,.2f} | "
                    f"Violations: {len(self.constraint_violations)}"
                )

        # Final summary
        print("\n" + "="*60)
        print("EVALUATION COMPLETE")
        print("="*60)

        actual_steps = len(self.predictions)
        specific_energy = self.total_energy_kwh / self.total_flow_m3 if self.total_flow_m3 > 0 else 0.0

        print(f"\n📊 COMPLETED: {actual_steps}/{num_steps} timesteps")
        print(f"\n💰 COST METRICS")
        print(f"  Total Cost:           €{self.total_cost:,.2f}")
        print(
            f"  Cost per timestep:    €{self.total_cost/actual_steps:,.2f}"
            if actual_steps > 0
            else "  Cost per timestep:    N/A"
        )

        print(f"\n⚡ ENERGY METRICS")
        print(f"  Total Energy:         {self.total_energy_kwh:,.2f} kWh")
        print(f"  Total Flow Pumped:    {self.total_flow_m3:,.2f} m³")
        print(f"  Specific Energy:      {specific_energy:.6f} kWh/m³")

        print(f"\n🚨 CONSTRAINT COMPLIANCE")
        print(f"  Total Violations:     {len(self.constraint_violations)}")
        if len(self.constraint_violations) == 0:
            print(f"    ✅ Perfect compliance!")
        else:
            print(f"    ❌ Violations detected")
            for v in self.constraint_violations[:5]:
                print(f"      - {v}")

        return {
            'metadata': {
                'timesteps_requested': num_steps,
                'timesteps_completed': actual_steps,
                'duration_hours': actual_steps * 0.25,
                'price_scenario': self.price_scenario,
                'start_index': start_index,
                'completed_successfully': actual_steps == num_steps,
            },
            'metrics': {
                'total_cost_eur': self.total_cost,
                'total_energy_kwh': self.total_energy_kwh,
                'total_flow_m3': self.total_flow_m3,
                'specific_energy_kwh_per_m3': specific_energy,
            },
            'violations': {
                'count': len(self.constraint_violations),
                'details': self.constraint_violations,
            },
            'predictions': self.predictions,
        }


def compare_with_baseline(ai_results: dict, baseline_results: dict) -> dict:
    """
    Compare AI system performance with baseline and print results

    Args:
        ai_results: Results from run_evaluation
        baseline_results: Loaded from baseline_evaluation.json
    """
    print("\n" + "="*60)
    print("COMPARISON WITH BASELINE")
    print("="*60)

    # Extract AI metrics
    ai_cost = ai_results['metrics']['total_cost_eur']
    ai_energy = ai_results['metrics']['total_energy_kwh']
    ai_flow = ai_results['metrics']['total_flow_m3']
    ai_specific = ai_results['metrics']['specific_energy_kwh_per_m3']
    ai_timesteps = ai_results['metadata']['timesteps_completed']

    # Extract baseline metrics
    baseline_cost = baseline_results['metrics']['total_cost_eur']
    baseline_energy = baseline_results['metrics']['total_energy_kwh']
    baseline_flow = baseline_results['metrics']['total_flow_m3']
    baseline_specific = baseline_results['metrics']['specific_energy_kwh_per_m3']
    baseline_timesteps = baseline_results['metadata']['timesteps_completed']

    # Normalize baseline metrics to same number of timesteps (if different)
    if baseline_timesteps > 0 and ai_timesteps > 0:
        duration_ratio = ai_timesteps / baseline_timesteps
        baseline_cost_scaled = baseline_cost * duration_ratio
        baseline_energy_scaled = baseline_energy * duration_ratio
        baseline_flow_scaled = baseline_flow * duration_ratio
    else:
        baseline_cost_scaled = baseline_cost
        baseline_energy_scaled = baseline_energy
        baseline_flow_scaled = baseline_flow

    cost_savings = baseline_cost_scaled - ai_cost
    cost_improvement = (cost_savings / baseline_cost_scaled * 100) if baseline_cost_scaled > 0 else 0

    energy_savings = baseline_energy_scaled - ai_energy
    energy_improvement = (energy_savings / baseline_energy_scaled * 100) if baseline_energy_scaled > 0 else 0

    specific_improvement = ((baseline_specific - ai_specific) / baseline_specific * 100) if baseline_specific > 0 else 0

    print(f"\n📊 RESULTS ({ai_timesteps} timesteps completed)")
    if not ai_results['metadata']['completed_successfully']:
        print(f"⚠️  Partial results - API rate limit hit at {ai_timesteps}/{ai_results['metadata']['timesteps_requested']} timesteps")
    print(f"\n{'Metric':<30} {'Baseline':<20} {'AI System':<20} {'Improvement':<15}")
    print(f"{'-'*85}")
    print(f"{'Total Cost (EUR)':<30} €{baseline_cost_scaled:>18,.2f} €{ai_cost:>18,.2f} {cost_improvement:>13.1f}%")
    print(f"{'Total Energy (kWh)':<30} {baseline_energy_scaled:>18,.2f} {ai_energy:>18,.2f} {energy_improvement:>13.1f}%")
    print(f"{'Specific Energy (kWh/m³)':<30} {baseline_specific:>18.6f} {ai_specific:>18.6f} {specific_improvement:>13.1f}%")

    print(f"\n💰 SAVINGS")
    print(f"  Cost Savings:         €{cost_savings:,.2f}")
    print(f"  Energy Savings:       {energy_savings:,.2f} kWh")

    if cost_improvement > 0:
        print(f"\n✅ AI system is {cost_improvement:.1f}% BETTER than baseline!")
    else:
        print(f"\n❌ AI system is {abs(cost_improvement):.1f}% WORSE than baseline")

    return {
        'baseline': {
            'cost': baseline_cost_scaled,
            'energy': baseline_energy_scaled,
            'specific_energy': baseline_specific
        },
        'ai': {
            'cost': ai_cost,
            'energy': ai_energy,
            'specific_energy': ai_specific
        },
        'improvement': {
            'cost_savings_eur': cost_savings,
            'cost_improvement_pct': cost_improvement,
            'energy_savings_kwh': energy_savings,
            'energy_improvement_pct': energy_improvement,
            'specific_energy_improvement_pct': specific_improvement
        }
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Run Multi-Agent Evaluation")
    parser.add_argument(
        "--price",
        choices=["normal", "high"],
        default="normal",
        help="Price scenario (normal or high)",
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
    parser.add_argument(
        "--lstm-model",
        type=str,
        default=str(Path(__file__).parent.parent / "models" / "lstm_inflow_model.pth"),
        help="Path to LSTM inflow forecasting model",
    )
    args = parser.parse_args()

    controller = EvaluationController(
        lstm_model_path=args.lstm_model,
        price_scenario=args.price,
    )

    results = controller.run_evaluation(
        start_index=args.start,
        num_steps=args.steps,
    )

    # Save AI evaluation results
    results_file = Path(__file__).parent.parent.parent / f"ai_evaluation_{args.price}_{args.steps}steps.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Saved AI evaluation results to: {results_file}")

    # Try to load baseline results for comparison
    baseline_file = Path(__file__).parent.parent.parent / "baseline_evaluation.json"
    if baseline_file.exists():
        with open(baseline_file, "r") as f:
            baseline_results = json.load(f)
        comparison = compare_with_baseline(results, baseline_results)

        # Save comparison
        comparison_file = Path(__file__).parent.parent.parent / f'comparison_{args.price}_{args.steps}steps.json'
        with open(comparison_file, 'w') as f:
            json.dump(comparison, f, indent=2)
        print(f"💾 Saved comparison to: {comparison_file}")
    else:
        print(f"\n⚠️ Baseline file not found: {baseline_file}")

    print("\n✓ Evaluation complete!")


if __name__ == "__main__":
    main()
