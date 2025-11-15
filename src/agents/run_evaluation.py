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

        try:
            flow, power, efficiency = self.pump_model.calculate_pump_performance(
                pump_id, frequency, L1
            )
            return flow, power, efficiency
        except:
            # Fallback estimation if pump curve fails
            # Simple linear approximation based on frequency
            freq_ratio = frequency / 50.0

            # Estimate based on pump type (large vs small)
            if 'L' in pump_id or pump_id in ['P1.4', 'P2.1', 'P2.2']:
                # Large pump
                flow = 3000 * freq_ratio
                power = 180 * (freq_ratio ** 3)  # Cubic law
            else:
                # Small pump
                flow = 1500 * freq_ratio
                power = 90 * (freq_ratio ** 3)

            efficiency = 0.80  # Assume reasonable efficiency
            return flow, power, efficiency

    def run_decision_cycle(self, state: SystemState, timestep: int) -> dict:
        """
        Run one complete decision cycle with full tracking

        Returns:
            Dictionary with all evaluation data
            None if API fails (rate limit hit)
        """

        # Step 1: Run all specialist agents
        recommendations = {}
        for name, agent in self.specialist_agents.items():
            try:
                rec = agent.assess(state)
                recommendations[name] = rec
            except Exception as e:
                # Check if this is a rate limit error
                if "429" in str(e) or "quota" in str(e).lower() or "rate" in str(e).lower():
                    print(f"\n❌ API Rate Limit Hit - Aborting evaluation")
                    return None
                print(f"⚠️ {name} failed: {e}")

        # Step 2: Coordinator synthesis
        try:
            pump_commands = self.coordinator.synthesize_recommendations(state, recommendations)
        except Exception as e:
            # Check if this is a rate limit error
            if "429" in str(e) or "quota" in str(e).lower() or "rate" in str(e).lower():
                print(f"\n❌ API Rate Limit Hit in Coordinator - Aborting evaluation")
                return None
            raise

        # Step 3: Calculate power and flow for each pump
        enhanced_commands = []
        total_power_kw = 0
        total_flow_m3h = 0

        for cmd in pump_commands:
            flow, power, efficiency = self.calculate_pump_power(
                cmd.pump_id,
                cmd.frequency if cmd.start else 0,
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

            if cmd.start:
                total_power_kw += power
                total_flow_m3h += flow

        # Step 4: Calculate cost for this timestep
        energy_kwh = total_power_kw * 0.25  # 15 min = 0.25 h
        cost_eur = energy_kwh * state.electricity_price
        flow_m3 = total_flow_m3h * 0.25
        specific_energy = energy_kwh / flow_m3 if flow_m3 > 0 else 0

        # Step 5: Check constraints
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

        # Step 6: Accumulate metrics
        self.total_cost += cost_eur
        self.total_energy_kwh += energy_kwh
        self.total_flow_m3 += flow_m3
        if violations:
            self.constraint_violations.extend(violations)

        # Step 7: Create prediction output
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
                'energy_consumed_kwh': float(energy_kwh),
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
        Run evaluation over historical data

        Args:
            start_index: Starting timestep
            num_steps: Number of 15-min timesteps to simulate
        """
        print("\n" + "="*60)
        print("EVALUATION RUN")
        print("="*60)
        print(f"Simulating {num_steps} timesteps ({num_steps * 0.25:.1f} hours)")
        print()

        price_col = 'Price_High' if self.price_scenario == 'high' else 'Price_Normal'

        for i in range(num_steps):
            idx = start_index + i

            if idx >= len(self.data):
                print("⚠️ Reached end of data")
                break

            # Create state from historical data
            state = SystemState(
                timestamp=self.data['Time stamp'].iloc[idx],
                L1=self.data['L1'].iloc[idx],
                V=self.data['V'].iloc[idx],
                F1=self.data['F1'].iloc[idx],
                F2=self.data['F2'].iloc[idx],
                electricity_price=self.data[price_col].iloc[idx],
                price_scenario=self.price_scenario,
                historical_data=self.data,
                current_index=idx
            )

            # Run decision cycle
            prediction = self.run_decision_cycle(state, idx)

            # Check if API failed (rate limit)
            if prediction is None:
                print(f"\n⚠️ Stopping evaluation at timestep {i+1}/{num_steps} due to API rate limit")
                print(f"⚠️ Returning results for {len(self.predictions)} completed timesteps")
                break

            # Progress update
            if (i + 1) % 50 == 0:
                print(f"Progress: {i+1}/{num_steps} timesteps | "
                      f"Cost so far: €{self.total_cost:,.2f} | "
                      f"Violations: {len(self.constraint_violations)}")

        # Final summary
        print("\n" + "="*60)
        print("EVALUATION COMPLETE")
        print("="*60)

        actual_steps = len(self.predictions)
        specific_energy = self.total_energy_kwh / self.total_flow_m3 if self.total_flow_m3 > 0 else 0

        print(f"\n📊 COMPLETED: {actual_steps}/{num_steps} timesteps")
        print(f"\n💰 COST METRICS")
        print(f"  Total Cost:           €{self.total_cost:,.2f}")
        print(f"  Cost per timestep:    €{self.total_cost/actual_steps:,.2f}" if actual_steps > 0 else "  Cost per timestep:    N/A")

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
                'completed_successfully': actual_steps == num_steps
            },
            'metrics': {
                'total_cost_eur': self.total_cost,
                'total_energy_kwh': self.total_energy_kwh,
                'total_flow_m3': self.total_flow_m3,
                'specific_energy_kwh_per_m3': specific_energy
            },
            'violations': {
                'count': len(self.constraint_violations),
                'details': self.constraint_violations
            },
            'predictions': self.predictions
        }


def compare_with_baseline(ai_results: dict, baseline_path: str):
    """
    Compare AI results with baseline
    """
    print("\n" + "="*60)
    print("COMPARISON: AI vs BASELINE")
    print("="*60)

    # Load baseline
    with open(baseline_path, 'r') as f:
        baseline = json.load(f)

    ai_cost = ai_results['metrics']['total_cost_eur']
    ai_energy = ai_results['metrics']['total_energy_kwh']
    ai_flow = ai_results['metrics']['total_flow_m3']
    ai_specific = ai_results['metrics']['specific_energy_kwh_per_m3']

    baseline_cost = baseline['baseline_metrics']['total_cost_eur']
    baseline_energy = baseline['baseline_metrics']['total_energy_kwh']
    baseline_flow = baseline['baseline_metrics']['total_flow_m3']
    baseline_specific = baseline['baseline_metrics']['specific_energy_kwh_per_m3']

    # Scale baseline to same duration
    ai_timesteps = ai_results['metadata']['timesteps_completed']
    duration_ratio = ai_timesteps / baseline['metadata']['timesteps']
    baseline_cost_scaled = baseline_cost * duration_ratio
    baseline_energy_scaled = baseline_energy * duration_ratio
    baseline_flow_scaled = baseline_flow * duration_ratio

    # Calculate improvements
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
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Multi-Agent System Evaluation')
    parser.add_argument('--price', choices=['normal', 'high'], default='normal')
    parser.add_argument('--steps', type=int, default=100,
                        help='Number of timesteps to simulate')
    parser.add_argument('--start', type=int, default=500)

    args = parser.parse_args()

    # Get model path
    script_dir = Path(__file__).parent
    model_path = script_dir.parent / 'models' / 'inflow_lstm_model.pth'

    # Create controller
    controller = EvaluationController(
        lstm_model_path=str(model_path),
        price_scenario=args.price
    )

    # Run evaluation
    results = controller.run_evaluation(
        start_index=args.start,
        num_steps=args.steps
    )

    # Save results
    output_file = Path(__file__).parent.parent.parent / f'ai_evaluation_{args.price}_{args.steps}steps.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Saved results to: {output_file}")

    # Compare with baseline
    baseline_file = Path(__file__).parent.parent.parent / f'baseline_metrics_{args.price}.json'
    if baseline_file.exists():
        comparison = compare_with_baseline(results, str(baseline_file))

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
