"""
Coordinator Agent - Synthesizes specialist recommendations into pump commands

This is the "brain" of the multi-agent system. It:
1. Collects recommendations from all 6 specialist agents
2. Resolves conflicts using priority hierarchy
3. Synthesizes final pump commands
4. Ensures safety and compliance always win
"""

import sys
from pathlib import Path
from typing import Dict, List
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'simulation'))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'config'))

from base_agent import BaseAgent, SystemState, AgentRecommendation
from gemini_wrapper import get_gemini_llm
from pump_models import PumpModel
from physics_simulator import PumpCommand
from constraints import CONSTRAINTS


class CoordinatorAgent(BaseAgent):
    """
    Coordinator Agent - Master decision maker

    Priority Hierarchy:
    1. CRITICAL: Safety (water level)
    2. CRITICAL: Compliance (hard constraints)
    3. HIGH: Cost optimization
    4. MEDIUM: Efficiency, Smoothness
    5. LOW: Inflow forecasting context

    Decision Process:
    1. Safety agent has veto power (L1 too high → emergency pumping)
    2. Compliance agent has veto power (violations → block action)
    3. Cost agent suggests when to pump (cheap vs expensive)
    4. Efficiency agent suggests how to pump (which combination)
    5. Smoothness agent suggests gradual transitions
    6. Inflow agent provides context (storm coming, dry weather)
    """

    def __init__(self):
        super().__init__(
            name="coordinator",
            role="Synthesize all specialist recommendations into optimal pump commands"
        )

        self.llm = get_gemini_llm()
        self.pump_model = PumpModel()

    def synthesize_recommendations(
        self,
        state: SystemState,
        recommendations: Dict[str, AgentRecommendation]
    ) -> List[PumpCommand]:
        """
        Synthesize all agent recommendations into pump commands

        Args:
            state: Current system state
            recommendations: Dict of agent_name → recommendation

        Returns:
            List of PumpCommand objects
        """

        # Extract key information from each agent
        inflow_rec = recommendations.get('inflow_forecasting')
        cost_rec = recommendations.get('energy_cost')
        efficiency_rec = recommendations.get('pump_efficiency')
        safety_rec = recommendations.get('water_level_safety')
        smoothness_rec = recommendations.get('flow_smoothness')
        compliance_rec = recommendations.get('constraint_compliance')

        # Build comprehensive context for LLM
        context = self._build_synthesis_context(
            state,
            inflow_rec,
            cost_rec,
            efficiency_rec,
            safety_rec,
            smoothness_rec,
            compliance_rec
        )

        # LLM synthesis prompt
        prompt = f"""
You are the Coordinator Agent for a multi-agent wastewater pumping system.
Your job is to synthesize recommendations from 6 specialist agents into a final pumping decision.

PRIORITY HIERARCHY (STRICT):
1. Safety ALWAYS wins (prevent overflow)
2. Compliance ALWAYS enforced (hard constraints)
3. Cost optimization (when safe)
4. Efficiency and smoothness (when affordable)

{context}

YOUR TASK:
1. Review all agent recommendations
2. Identify conflicts and trade-offs
3. Apply priority hierarchy to resolve conflicts
4. Generate final pump commands

DECISION FORMAT:
Return a JSON with:
{{
  "final_decision": "DESCRIPTION",
  "reasoning": "WHY this decision (reference agent inputs)",
  "pump_commands": [
    {{"pump_id": "P1L", "frequency_hz": 50.0, "run": true}},
    {{"pump_id": "P2L", "frequency_hz": 0.0, "run": false}}
  ],
  "estimated_flow_m3h": 8000,
  "cost_per_hour_eur": 25.0,
  "priority_applied": "SAFETY / COST / EFFICIENCY",
  "conflicts_resolved": ["description of conflicts"],
  "confidence": 0.85
}}

RULES:
- If safety says EMERGENCY, ignore cost and pump at max capacity
- If compliance says VETO, do NOT proceed with that action
- At least 1 pump ALWAYS running
- Prefer gradual changes (smoothness)
- During cheap electricity + low level, pump more (temporal arbitrage)
- During expensive electricity + safe level, pump minimum

Think step-by-step and explain your reasoning clearly.
"""

        # Get LLM decision
        response = self.llm.generate(prompt, json_mode=True)

        # Parse pump commands from response
        pump_commands = self._parse_pump_commands(response, state)

        # Store decision in history
        decision_rec = AgentRecommendation(
            agent_name=self.name,
            timestamp=state.timestamp,
            recommendation_type="final_decision",
            priority=response.get('priority_applied', 'MEDIUM'),
            confidence=float(response.get('confidence', 0.80)),
            reasoning=response.get('reasoning', ''),
            data={
                'pump_commands': [
                    {
                        'pump_id': cmd.pump_id,
                        'frequency': cmd.frequency,
                        'run': cmd.start
                    }
                    for cmd in pump_commands
                ],
                'estimated_flow': response.get('estimated_flow_m3h', 0),
                'estimated_cost': response.get('cost_per_hour_eur', 0),
                'conflicts_resolved': response.get('conflicts_resolved', []),
                'llm_response': response
            }
        )

        self.history.append(decision_rec)

        return pump_commands

    def _build_synthesis_context(
        self,
        state: SystemState,
        inflow_rec: AgentRecommendation,
        cost_rec: AgentRecommendation,
        efficiency_rec: AgentRecommendation,
        safety_rec: AgentRecommendation,
        smoothness_rec: AgentRecommendation,
        compliance_rec: AgentRecommendation
    ) -> str:
        """Build comprehensive context from all agent recommendations"""

        context = f"""
=== CURRENT SYSTEM STATE ===
Time: {state.timestamp}
Water Level L1: {state.L1:.2f}m (Alarm: {CONSTRAINTS.L1_ALARM}m, Max: {CONSTRAINTS.L1_MAX}m)
Current Inflow F1: {state.F1:.0f} m³/15min
Current Outflow F2: {state.F2:.0f} m³/h
Electricity Price: {state.electricity_price:.3f} EUR/kWh
Active Pumps: {len(state.active_pumps)}

=== AGENT 1: INFLOW FORECASTING ===
Priority: {inflow_rec.priority if inflow_rec else 'N/A'}
Key Insights:
"""
        if inflow_rec:
            data = inflow_rec.data
            context += f"""- Storm detected: {data.get('storm_detected', False)}
- Peak inflow: {data.get('peak_inflow', 0):.0f} m³/15min in {data.get('peak_in_hours', 0):.1f}h
- Dry weather: {data.get('is_dry_weather', False)}
- Weather status: {data.get('weather_status', 'NORMAL')}
Reasoning: {inflow_rec.reasoning[:200]}...
"""

        context += f"""
=== AGENT 2: ENERGY COST ===
Priority: {cost_rec.priority if cost_rec else 'N/A'}
Key Insights:
"""
        if cost_rec:
            data = cost_rec.data
            arb = data.get('arbitrage_value', {})
            context += f"""- Current price: {data.get('current_price', 0):.3f} EUR/kWh
- Price ratio vs. best window: {arb.get('price_ratio', 1):.1f}x
- Savings potential: {arb.get('savings_potential_eur_per_1000kwh', 0):.0f} EUR/1000kWh
- Recommendation: {data.get('recommendation', 'NORMAL')}
- Risk level: {arb.get('risk', 'UNKNOWN')}
Reasoning: {cost_rec.reasoning[:200]}...
"""

        context += f"""
=== AGENT 3: PUMP EFFICIENCY ===
Priority: {efficiency_rec.priority if efficiency_rec else 'N/A'}
Key Insights:
"""
        if efficiency_rec:
            data = efficiency_rec.data
            combo = data.get('recommended_combination', {}) or {}
            context += f"""- Recommended pumps: {combo.get('pumps', []) if combo else 'N/A'}
- Expected efficiency: {data.get('expected_efficiency', 0):.1%}
- Total flow: {combo.get('total_flow', 0) if combo else 0:.0f} m³/h
- Total power: {combo.get('total_power', 0) if combo else 0:.0f} kW
Reasoning: {efficiency_rec.reasoning[:200] if efficiency_rec.reasoning else 'N/A'}...
"""

        context += f"""
=== AGENT 4: WATER LEVEL SAFETY ===
Priority: {safety_rec.priority if safety_rec else 'N/A'}
⚠️ SAFETY HAS VETO POWER ⚠️
Key Insights:
"""
        if safety_rec:
            data = safety_rec.data
            context += f"""- Risk level: {data.get('risk_level', 'UNKNOWN')}
- Status: {data.get('status', 'UNKNOWN')}
- Required action: {data.get('required_action', 'MAINTAIN')}
- Time to alarm: {data.get('trajectory', {}).get('hours_to_alarm', 999):.1f}h
- VETO cost optimization: {data.get('veto_cost_optimization', False)}
Reasoning: {safety_rec.reasoning[:200]}...
"""

        context += f"""
=== AGENT 5: FLOW SMOOTHNESS ===
Priority: {smoothness_rec.priority if smoothness_rec else 'N/A'}
Key Insights:
"""
        if smoothness_rec:
            data = smoothness_rec.data
            metrics = data.get('variability_metrics', {})
            context += f"""- Max recent change: {metrics.get('max_change_m3h', 0):.0f} m³/h
- Status: {data.get('status', 'UNKNOWN')}
- Allow immediate change: {data.get('allow_immediate_change', True)}
- Staged plan needed: {data.get('staged_plan_needed', False)}
Reasoning: {smoothness_rec.reasoning[:200]}...
"""

        context += f"""
=== AGENT 6: CONSTRAINT COMPLIANCE ===
Priority: {compliance_rec.priority if compliance_rec else 'N/A'}
⚠️ COMPLIANCE HAS VETO POWER ⚠️
Key Insights:
"""
        if compliance_rec:
            data = compliance_rec.data
            context += f"""- Compliance status: {data.get('compliance_status', 'UNKNOWN')}
- Violations found: {len(data.get('all_violations', []))}
- VETO required: {data.get('veto_required', False)}
- Emptying status: {data.get('emptying_check', {}).get('status', 'UNKNOWN')}
Reasoning: {compliance_rec.reasoning[:200]}...
"""

        context += "\n=== END OF AGENT RECOMMENDATIONS ===\n"

        return context

    def _parse_pump_commands(self, llm_response: dict, state: SystemState) -> List[PumpCommand]:
        """Parse LLM response into PumpCommand objects"""

        commands = []

        # Get pump commands from LLM response
        pump_cmds = llm_response.get('pump_commands', [])

        if not pump_cmds:
            # Fallback: keep current configuration
            for pump_id in self.pump_model.get_all_pump_ids():
                if pump_id in state.active_pumps:
                    commands.append(PumpCommand(pump_id=pump_id, start=True, frequency=50.0))
                else:
                    commands.append(PumpCommand(pump_id=pump_id, start=False, frequency=0.0))
        else:
            # Parse LLM commands
            specified_pumps = set()

            for cmd in pump_cmds:
                pump_id = cmd.get('pump_id', '')
                frequency = float(cmd.get('frequency_hz', 0))
                run = cmd.get('run', frequency > 0)

                if pump_id:
                    commands.append(PumpCommand(
                        pump_id=pump_id,
                        start=run,
                        frequency=frequency if run else 0.0
                    ))
                    specified_pumps.add(pump_id)

            # Add commands for unspecified pumps (set to off)
            for pump_id in self.pump_model.get_all_pump_ids():
                if pump_id not in specified_pumps:
                    commands.append(PumpCommand(pump_id=pump_id, start=False, frequency=0.0))

        # Validate: at least 1 pump running
        active_count = sum(1 for cmd in commands if cmd.start)
        if active_count == 0:
            # Emergency: turn on one large pump at minimum frequency
            commands[0] = PumpCommand(pump_id='P1L', start=True, frequency=CONSTRAINTS.FREQ_MIN)
            print(f"⚠️ Coordinator: No pumps active, emergency start P1L")

        return commands


if __name__ == "__main__":
    """Test Coordinator Agent"""

    print("="*60)
    print("Coordinator Agent - Testing")
    print("="*60)
    print()

    from data_loader import HSYDataLoader
    from specialist_agents import create_all_agents

    # Load data
    loader = HSYDataLoader()
    data_dict = loader.load_all_data()
    data = data_dict['operational_data']

    # Create all agents
    model_path = Path(__file__).parent.parent / 'models' / 'inflow_lstm_model.pth'
    specialist_agents = create_all_agents(str(model_path))

    # Create coordinator
    coordinator = CoordinatorAgent()

    # Create test state
    test_index = 800
    state = SystemState(
        timestamp=data['Time stamp'].iloc[test_index],
        L1=data['L1'].iloc[test_index],
        V=data['V'].iloc[test_index],
        F1=data['F1'].iloc[test_index],
        F2=data['F2'].iloc[test_index],
        electricity_price=data['Price_High'].iloc[test_index],
        price_scenario='high',
        historical_data=data,
        current_index=test_index
    )

    print(f"Test State:")
    print(f"  Time: {state.timestamp}")
    print(f"  L1: {state.L1:.2f}m")
    print(f"  F1: {state.F1:.0f} m³/15min")
    print(f"  F2: {state.F2:.0f} m³/h")
    print(f"  Price: {state.electricity_price:.3f} EUR/kWh")

    # Get recommendations from all specialists
    print("\n" + "="*60)
    print("Gathering Specialist Recommendations...")
    print("="*60)

    recommendations = {}
    for name, agent in specialist_agents.items():
        print(f"\nAgent: {name}")
        rec = agent.assess(state)
        recommendations[name] = rec
        print(f"  Priority: {rec.priority}, Confidence: {rec.confidence:.2f}")

    # Synthesize with coordinator
    print("\n" + "="*60)
    print("Coordinator Synthesis...")
    print("="*60)

    pump_commands = coordinator.synthesize_recommendations(state, recommendations)

    print(f"\nFinal Pump Commands:")
    for cmd in pump_commands:
        if cmd.start:
            print(f"  {cmd.pump_id}: {cmd.frequency:.1f} Hz")

    # Show coordinator reasoning
    if coordinator.history:
        decision = coordinator.history[-1]
        print(f"\nCoordinator Reasoning:")
        print(decision.reasoning)
        print(f"\nEstimated Flow: {decision.data.get('estimated_flow', 0):.0f} m³/h")
        print(f"Estimated Cost: {decision.data.get('estimated_cost', 0):.2f} EUR/h")

    print("\n✓ Coordinator test complete!")
