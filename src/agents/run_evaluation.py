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
        
        # Minimum required: handle current inflow rate (convert F1 from m³/15min to m³/h)
        min_required_flow = state.F1 * 4 if state.F1 > 0 else 1000  # F1 is per 15 min
        
        # ONLY enforce: At least 1 pump must be running
        if len(active_pumps) == 0:
            print(f"  ⚠️ VALIDATION: No pumps active! Enabling P1L at minimum frequency")
            for cmd in pump_commands:
                if cmd.pump_id == 'P1L':
                    cmd.start = True
                    cmd.frequency = 47.8  # Minimum operating frequency
                    break
            return pump_commands
        
        # CHECK (but don't fix): Warn if flow is insufficient
        if current_total_flow < min_required_flow:
            print(f"  ⚠️ WARNING: Flow may be insufficient - current {current_total_flow:.0f}m³/h < inflow {min_required_flow:.0f}m³/h")
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
                print(f"\n{name.upper()}:")
                print(f"  Priority: {rec.priority} | Confidence: {rec.confidence:.2f}")
                print(f"  Type: {rec.recommendation_type}")
                print(f"  Reasoning: {rec.reasoning[:150]}...")
                if rec.data:
                    print(f"  Key Data: {str(rec.data)[:200]}...")
            except Exception as e:
                # Check if this is a rate limit error
                if "429" in str(e) or "quota" in str(e).lower() or "rate" in str(e).lower():
                    print(f"\n❌ API Rate Limit Hit - Aborting evaluation")
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
            if "429" in str(e) or "quota" in str(e).lower() or "rate" in str(e).lower():
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
            print(f"  {cmd['pump_id']}: {cmd['frequency_hz']:.1f} Hz → {cmd['flow_m3h']:.0f} m³/h @ {cmd['power_kw']:.1f} kW (η={cmd['efficiency']:.1%})")
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
                active_pumps=self.active_pumps.copy(),  # Pass previous pump states
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
    Compare AI results with baseline for the SAME timesteps

    This calculates baseline metrics for the exact same timesteps that the AI
    evaluation ran on, ensuring an apples-to-apples comparison.
    """
    print("\n" + "="*60)
    print("COMPARISON: AI vs BASELINE")
    print("="*60)

    # Load historical data to calculate baseline for same timesteps
    loader = HSYDataLoader()
    data_dict = loader.load_all_data()
    data = data_dict['operational_data']

    # Get AI evaluation parameters
    ai_timesteps = ai_results['metadata']['timesteps_completed']
    start_index = ai_results['metadata']['start_index']
    price_scenario = ai_results['metadata']['price_scenario']
    price_col = 'Price_High' if price_scenario == 'high' else 'Price_Normal'

    print(f"\n📊 Calculating baseline for SAME timesteps as AI evaluation:")
    print(f"  Start index: {start_index}")
    print(f"  Timesteps: {ai_timesteps}")
    print(f"  Price scenario: {price_scenario}")

    # Calculate baseline metrics for the SAME timesteps
    pump_power_cols = [
        'Pump efficiency 1.1', 'Pump efficiency 1.2', 'Pump efficiency 1.3', 'Pump efficiency 1.4',
        'Pump efficiency 2.1', 'Pump efficiency 2.2', 'Pump efficiency 2.3', 'Pump efficiency 2.4'
    ]

    baseline_cost = 0.0
    baseline_energy = 0.0
    baseline_flow = 0.0

    # Process the SAME timesteps as AI evaluation
    for i in range(ai_timesteps):
        idx = start_index + i
        if idx >= len(data):
            break

        row = data.iloc[idx]

        # Sum power from all pumps
        total_power_kw = 0
        for col in pump_power_cols:
            power = row[col]
            if pd.notna(power) and power > 0:
                total_power_kw += power

        # Energy consumed (kW × 0.25h = kWh)
        energy_kwh = total_power_kw * 0.25

        # Cost for this timestep
        price = row[price_col]
        if pd.isna(price):
            price = 0.0
        cost_eur = energy_kwh * price

        # Flow pumped (m³/h × 0.25h = m³)
        F2 = row['F2']
        if pd.isna(F2):
            F2 = 0.0
        flow_m3 = F2 * 0.25

        # Accumulate
        baseline_cost += cost_eur
        baseline_energy += energy_kwh
        baseline_flow += flow_m3

    baseline_specific = baseline_energy / baseline_flow if baseline_flow > 0 else 0

    # Get AI metrics
    ai_cost = ai_results['metrics']['total_cost_eur']
    ai_energy = ai_results['metrics']['total_energy_kwh']
    ai_flow = ai_results['metrics']['total_flow_m3']
    ai_specific = ai_results['metrics']['specific_energy_kwh_per_m3']

    # Calculate improvements (no scaling needed - direct comparison!)
    cost_savings = baseline_cost - ai_cost
    cost_improvement = (cost_savings / baseline_cost * 100) if baseline_cost > 0 else 0

    energy_savings = baseline_energy - ai_energy
    energy_improvement = (energy_savings / baseline_energy * 100) if baseline_energy > 0 else 0

    specific_improvement = ((baseline_specific - ai_specific) / baseline_specific * 100) if baseline_specific > 0 else 0

    print(f"\n📊 RESULTS ({ai_timesteps} timesteps)")
    if not ai_results['metadata']['completed_successfully']:
        print(f"⚠️  Partial results - API rate limit hit at {ai_timesteps}/{ai_results['metadata']['timesteps_requested']} timesteps")
    print(f"\n{'Metric':<30} {'Baseline':<20} {'AI System':<20} {'Improvement':<15}")
    print(f"{'-'*85}")
    print(f"{'Total Cost (EUR)':<30} €{baseline_cost:>18,.2f} €{ai_cost:>18,.2f} {cost_improvement:>13.1f}%")
    print(f"{'Total Energy (kWh)':<30} {baseline_energy:>18,.2f} {ai_energy:>18,.2f} {energy_improvement:>13.1f}%")
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
            'cost': baseline_cost,
            'energy': baseline_energy,
            'flow': baseline_flow,
            'specific_energy': baseline_specific
        },
        'ai': {
            'cost': ai_cost,
            'energy': ai_energy,
            'flow': ai_flow,
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
