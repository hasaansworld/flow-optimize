"""
All Specialist Agents for Multi-Agent Wastewater Control System

This file contains all 6 specialist agents:
1. Inflow Forecasting Agent (in separate file)
2. Energy Cost Agent
3. Pump Efficiency Agent
4. Water Level Safety Agent
5. Flow Smoothness Agent
6. Constraint Compliance Agent
"""

import sys
from pathlib import Path
import numpy as np
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'simulation'))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'config'))

from base_agent import BaseAgent, SystemState, AgentRecommendation
from gemini_wrapper import get_gemini_llm
from price_manager import PriceManager
from pump_models import PumpModel
from constraints import CONSTRAINTS


class EnergyCostAgent(BaseAgent):
    """
    Agent specialized in identifying energy cost arbitrage opportunities

    Tools:
    - Price pattern analyzer
    - Cheap window detector
    - Cost-benefit calculator
    - Risk assessor
    """

    def __init__(self):
        super().__init__(
            name="energy_cost",
            role="Identify electricity price arbitrage opportunities to minimize pumping costs"
        )

        self.llm = get_gemini_llm()
        self.price_manager = None  # Will be set when data is available

        # Register tools
        self.register_tool("identify_cheap_windows", self._tool_identify_cheap_windows)
        self.register_tool("calculate_arbitrage_value", self._tool_calculate_arbitrage_value)

    def _tool_identify_cheap_windows(self, state: SystemState, percentile: float = 25.0) -> List[dict]:
        """Tool: Identify cheap electricity windows"""
        if self.price_manager is None:
            return []

        windows = self.price_manager.identify_cheap_windows(
            current_index=state.current_index,
            horizon_steps=96,  # 24 hours
            percentile=percentile
        )

        return [
            {
                "start_step": w[0] - state.current_index,
                "end_step": w[1] - state.current_index,
                "duration_hours": (w[1] - w[0] + 1) * 0.25,
                "avg_price": w[2]
            }
            for w in windows
        ]

    def _tool_calculate_arbitrage_value(self, state: SystemState, cheap_windows: List[dict]) -> dict:
        """Tool: Calculate potential savings from arbitrage"""
        if not cheap_windows:
            return {"savings_potential": 0, "risk": "NONE"}

        current_price = state.electricity_price
        best_window = min(cheap_windows, key=lambda w: w['avg_price'])

        price_ratio = current_price / best_window['avg_price'] if best_window['avg_price'] > 0 else 1
        savings_potential = (current_price - best_window['avg_price']) * 1000  # Per 1000 kWh

        return {
            "savings_potential_eur_per_1000kwh": savings_potential,
            "price_ratio": price_ratio,
            "best_window_in_hours": best_window['start_step'] * 0.25,
            "risk": "LOW" if state.L1 < 5.0 else "MEDIUM" if state.L1 < 6.5 else "HIGH"
        }

    def assess(self, state: SystemState) -> AgentRecommendation:
        """Assess energy cost situation"""

        # Initialize price manager if needed
        if self.price_manager is None and state.historical_data is not None:
            self.price_manager = PriceManager(state.historical_data)
            self.price_manager.set_scenario(state.price_scenario)

        # Use tools
        cheap_windows = self._tool_identify_cheap_windows(state)
        arbitrage_info = self._tool_calculate_arbitrage_value(state, cheap_windows)

        # LLM reasoning
        prompt = self._format_reasoning_prompt(state, f"""
Energy Cost Analysis:

Current Situation:
- Current price: {state.electricity_price:.3f} EUR/kWh
- Price scenario: {state.price_scenario.upper()}
- Water level L1: {state.L1:.2f}m (flexibility for deferring pumping)

Cheap Windows Identified (next 24h):
{cheap_windows[:3] if cheap_windows else "None found"}

Arbitrage Potential:
- Price ratio: {arbitrage_info.get('price_ratio', 1):.1f}x
- Savings potential: {arbitrage_info.get('savings_potential_eur_per_1000kwh', 0):.2f} EUR/1000kWh
- Risk level: {arbitrage_info.get('risk', 'UNKNOWN')}

Your task:
1. Analyze if current price is expensive vs. forecast
2. Identify opportunities to defer pumping to cheaper periods
3. Calculate estimated savings vs. risk
4. Provide specific recommendation (PUMP_NOW, MINIMIZE_PUMPING, DEFER_TO_CHEAP_WINDOW)

Think like an energy trader who understands price volatility and temporal arbitrage.
""")

        response = self.llm.generate_structured(
            prompt,
            expected_fields=["analysis", "recommendation", "estimated_savings_eur", "risk_level", "confidence", "priority"]
        )

        # Determine priority
        if arbitrage_info.get('price_ratio', 1) > 10:
            priority = "HIGH"
        elif arbitrage_info.get('price_ratio', 1) > 5:
            priority = "MEDIUM"
        else:
            priority = "LOW"

        return AgentRecommendation(
            agent_name=self.name,
            timestamp=state.timestamp,
            recommendation_type="cost_optimization",
            priority=response.get('priority', priority),
            confidence=float(response.get('confidence', 0.80)),
            reasoning=response.get('analysis', ''),
            data={
                'current_price': state.electricity_price,
                'cheap_windows': cheap_windows,
                'arbitrage_value': arbitrage_info,
                'recommendation': response.get('recommendation', 'PUMP_NORMALLY'),
                'estimated_savings': float(response.get('estimated_savings_eur', 0))
            }
        )


class PumpEfficiencyAgent(BaseAgent):
    """
    Agent specialized in selecting optimal pump combinations

    Tools:
    - Pump performance calculator
    - Efficiency optimizer
    - Combination generator
    """

    def __init__(self):
        super().__init__(
            name="pump_efficiency",
            role="Select optimal pump combinations for maximum energy efficiency"
        )

        self.llm = get_gemini_llm()
        self.pump_model = PumpModel()

        self.register_tool("calculate_pump_performance", self._tool_calculate_pump_performance)
        self.register_tool("find_optimal_combination", self._tool_find_optimal_combination)

    def _tool_calculate_pump_performance(self, pump_id: str, frequency: float, L1: float) -> dict:
        """Tool: Calculate performance for a specific pump"""
        flow, power, efficiency = self.pump_model.calculate_pump_performance(pump_id, frequency, L1)

        return {
            "pump_id": pump_id,
            "frequency": frequency,
            "flow_m3h": flow,
            "power_kw": power,
            "efficiency": efficiency
        }

    def _tool_find_optimal_combination(self, target_flow: float, L1: float) -> List[dict]:
        """Tool: Find best pump combinations for target flow"""
        pump_ids = self.pump_model.get_all_pump_ids()
        combinations = []

        # Try single pumps
        for pump_id in pump_ids:
            for freq in [47.8, 48.0, 49.0, 50.0]:
                flow, power, eff = self.pump_model.calculate_pump_performance(pump_id, freq, L1)
                if 0.8 * target_flow <= flow <= 1.2 * target_flow:
                    combinations.append({
                        "pumps": [pump_id],
                        "frequencies": {pump_id: freq},
                        "total_flow": flow,
                        "total_power": power,
                        "avg_efficiency": eff,
                        "match_quality": 1.0 - abs(flow - target_flow) / target_flow
                    })

        # Try pairs of pumps (most common)
        for i, pump1 in enumerate(pump_ids):
            for pump2 in pump_ids[i+1:]:
                for freq1 in [48.0, 49.0, 50.0]:
                    for freq2 in [48.0, 49.0, 50.0]:
                        flow1, power1, eff1 = self.pump_model.calculate_pump_performance(pump1, freq1, L1)
                        flow2, power2, eff2 = self.pump_model.calculate_pump_performance(pump2, freq2, L1)

                        total_flow = flow1 + flow2
                        total_power = power1 + power2

                        if total_flow <= CONSTRAINTS.F2_MAX and 0.9 * target_flow <= total_flow <= 1.1 * target_flow:
                            combinations.append({
                                "pumps": [pump1, pump2],
                                "frequencies": {pump1: freq1, pump2: freq2},
                                "total_flow": total_flow,
                                "total_power": total_power,
                                "avg_efficiency": (eff1 + eff2) / 2,
                                "match_quality": 1.0 - abs(total_flow - target_flow) / target_flow
                            })

        # Sort by efficiency and match quality
        combinations.sort(key=lambda x: (-x['avg_efficiency'], -x['match_quality']))

        return combinations[:5]  # Top 5 options

    def assess(self, state: SystemState) -> AgentRecommendation:
        """Assess pump efficiency and recommend combination"""

        # Determine target flow (simplified - would come from storage agent)
        target_flow = state.F2 if state.F2 > 0 else 5000  # m³/h

        # Find optimal combinations
        combinations = self._tool_find_optimal_combination(target_flow, state.L1)

        # LLM reasoning
        prompt = self._format_reasoning_prompt(state, f"""
Pump Efficiency Analysis:

Current Situation:
- Water level L1: {state.L1:.2f}m → Head H = {30 - state.L1:.2f}m
- Current outflow F2: {state.F2:.0f} m³/h
- Target flow: {target_flow:.0f} m³/h
- Active pumps: {len(state.active_pumps)}

Top Pump Combinations Found:
{combinations[:3] if combinations else "No valid combinations"}

Constraints:
- Frequency: ≥47.8 Hz
- Max total flow: 16,000 m³/h
- Prefer high efficiency (>80%)

Your task:
1. Evaluate the pump combinations for efficiency
2. Consider current active pumps (avoid unnecessary switching)
3. Recommend best combination balancing efficiency and operational smoothness
4. Explain trade-offs

Think like a mechanical engineer optimizing pump performance.
""")

        response = self.llm.generate_structured(
            prompt,
            expected_fields=["analysis", "recommended_combination", "expected_efficiency", "reasoning", "confidence", "priority"]
        )

        best_combo = combinations[0] if combinations else None

        return AgentRecommendation(
            agent_name=self.name,
            timestamp=state.timestamp,
            recommendation_type="pump_selection",
            priority=response.get('priority', 'MEDIUM'),
            confidence=float(response.get('confidence', 0.85)),
            reasoning=response.get('reasoning', ''),
            data={
                'target_flow': target_flow,
                'recommended_combination': best_combo,
                'alternative_combinations': combinations[1:3] if len(combinations) > 1 else [],
                'expected_efficiency': float(response.get('expected_efficiency', best_combo['avg_efficiency'] if best_combo else 0.80))
            }
        )


class WaterLevelSafetyAgent(BaseAgent):
    """
    Agent specialized in water level safety monitoring

    Tools:
    - Level trajectory simulator
    - Risk calculator
    - Time-to-alarm calculator
    """

    def __init__(self):
        super().__init__(
            name="water_level_safety",
            role="Monitor water levels and ensure safety constraints are never violated"
        )

        self.llm = get_gemini_llm()

        self.register_tool("calculate_trajectory", self._tool_calculate_trajectory)
        self.register_tool("assess_risk", self._tool_assess_risk)

    def _tool_calculate_trajectory(self, state: SystemState, forecast_inflow: List[float], current_outflow: float, steps: int = 24) -> dict:
        """Tool: Calculate water level trajectory"""
        L1_trajectory = [state.L1]
        V_trajectory = [state.V]

        for i in range(min(steps, len(forecast_inflow))):
            F1 = forecast_inflow[i]
            F2 = current_outflow  # Assume constant for projection

            # Volume change
            dV = F1 - (F2 * 0.25)  # F1 is per 15min, F2 is per hour
            new_V = V_trajectory[-1] + dV

            # Convert to level (simplified linear approximation)
            # In reality would use volume_to_level lookup
            new_L1 = new_V / 4000  # Rough approximation

            V_trajectory.append(new_V)
            L1_trajectory.append(new_L1)

        max_L1 = max(L1_trajectory)
        steps_to_alarm = next((i for i, L in enumerate(L1_trajectory) if L > CONSTRAINTS.L1_ALARM), steps)
        steps_to_max = next((i for i, L in enumerate(L1_trajectory) if L > CONSTRAINTS.L1_MAX), steps)

        return {
            "max_level": max_L1,
            "steps_to_alarm": steps_to_alarm,
            "hours_to_alarm": steps_to_alarm * 0.25,
            "steps_to_max": steps_to_max,
            "hours_to_max": steps_to_max * 0.25
        }

    def _tool_assess_risk(self, state: SystemState, trajectory: dict) -> str:
        """Tool: Assess risk level"""
        if state.L1 > CONSTRAINTS.L1_MAX:
            return "CRITICAL"
        elif state.L1 > CONSTRAINTS.L1_ALARM:
            return "HIGH"
        elif trajectory['hours_to_alarm'] < 2:
            return "MEDIUM"
        elif trajectory['hours_to_alarm'] < 6:
            return "LOW"
        else:
            return "NONE"

    def assess(self, state: SystemState) -> AgentRecommendation:
        """Assess water level safety"""

        # Calculate trajectory (would use inflow forecast from Agent 1)
        forecast_inflow = [state.F1] * 24  # Simplified: assume constant
        trajectory = self._tool_calculate_trajectory(state, forecast_inflow, state.F2)
        risk = self._tool_assess_risk(state, trajectory)

        # LLM reasoning
        prompt = self._format_reasoning_prompt(state, f"""
Water Level Safety Analysis:

Current Situation:
- Water level L1: {state.L1:.2f}m
- Alarm threshold: {CONSTRAINTS.L1_ALARM}m
- Maximum limit: {CONSTRAINTS.L1_MAX}m
- Margin to alarm: {CONSTRAINTS.L1_ALARM - state.L1:.2f}m

Trajectory Projection:
- Max level (next 6h): {trajectory['max_level']:.2f}m
- Time to alarm: {trajectory['hours_to_alarm']:.1f} hours
- Time to max: {trajectory['hours_to_max']:.1f} hours
- Risk level: {risk}

Current pumping: {state.F2:.0f} m³/h

Your task:
1. Assess if current level is safe
2. Determine if emergency action is needed
3. Calculate required pumping capacity to maintain safety
4. Provide specific recommendation (SAFE, INCREASE_PUMPING, EMERGENCY_MAX_PUMPING)

Safety ALWAYS takes priority over cost optimization!

Think like a safety officer who never takes unnecessary risks.
""")

        response = self.llm.generate_structured(
            prompt,
            expected_fields=["analysis", "status", "required_action", "target_flow_m3h", "veto_cost_optimization", "confidence", "priority"]
        )

        # Determine priority based on risk
        if risk == "CRITICAL":
            priority = "CRITICAL"
        elif risk == "HIGH":
            priority = "HIGH"
        elif risk == "MEDIUM":
            priority = "MEDIUM"
        else:
            priority = "LOW"

        return AgentRecommendation(
            agent_name=self.name,
            timestamp=state.timestamp,
            recommendation_type="safety_assessment",
            priority=priority,
            confidence=float(response.get('confidence', 0.95)),
            reasoning=response.get('analysis', ''),
            data={
                'current_level': state.L1,
                'risk_level': risk,
                'status': response.get('status', 'SAFE'),
                'trajectory': trajectory,
                'required_action': response.get('required_action', 'MAINTAIN'),
                'veto_cost_optimization': response.get('veto_cost_optimization', False)
            }
        )


class FlowSmoothnessAgent(BaseAgent):
    """
    Agent specialized in ensuring smooth flow transitions

    Tools:
    - Flow variability calculator
    - Staged transition planner
    - Downstream impact assessor

    Goal: Prevent shock loading to WWTP
    """

    def __init__(self):
        super().__init__(
            name="flow_smoothness",
            role="Ensure gradual flow changes to prevent shock loading downstream WWTP"
        )

        self.llm = get_gemini_llm()
        self.max_flow_change_rate = 2000  # m³/h per 15min (configurable)

        self.register_tool("calculate_flow_variability", self._tool_calculate_flow_variability)
        self.register_tool("create_staged_plan", self._tool_create_staged_plan)

    def _tool_calculate_flow_variability(self, state: SystemState, lookback_steps: int = 8) -> dict:
        """Tool: Calculate recent flow variability"""
        if state.historical_data is None or state.current_index < lookback_steps:
            return {"variability": 0, "max_change": 0, "trend": "STABLE"}

        # Get recent F2 values
        start_idx = max(0, state.current_index - lookback_steps)
        recent_F2 = state.historical_data['F2'].iloc[start_idx:state.current_index+1].values

        # Calculate variability metrics
        changes = np.diff(recent_F2)
        max_change = np.max(np.abs(changes)) if len(changes) > 0 else 0
        std_change = np.std(changes) if len(changes) > 0 else 0

        # Determine trend
        if len(recent_F2) >= 2:
            if recent_F2[-1] > recent_F2[0] * 1.1:
                trend = "RISING"
            elif recent_F2[-1] < recent_F2[0] * 0.9:
                trend = "FALLING"
            else:
                trend = "STABLE"
        else:
            trend = "STABLE"

        return {
            "max_change_m3h": float(max_change),
            "std_change_m3h": float(std_change),
            "current_flow": float(state.F2),
            "trend": trend,
            "is_smooth": max_change < self.max_flow_change_rate
        }

    def _tool_create_staged_plan(self, current_flow: float, target_flow: float, max_change_per_step: float) -> List[float]:
        """Tool: Create staged transition plan"""
        if abs(target_flow - current_flow) <= max_change_per_step:
            return [target_flow]

        # Create gradual steps
        steps = []
        flow = current_flow
        direction = 1 if target_flow > current_flow else -1

        while abs(flow - target_flow) > max_change_per_step:
            flow += direction * max_change_per_step
            steps.append(flow)

        steps.append(target_flow)
        return steps

    def assess(self, state: SystemState) -> AgentRecommendation:
        """Assess flow smoothness and provide guidance"""

        # Use tools
        variability = self._tool_calculate_flow_variability(state)

        # LLM reasoning
        prompt = self._format_reasoning_prompt(state, f"""
Flow Smoothness Analysis:

Current Situation:
- Current outflow F2: {state.F2:.0f} m³/h
- Recent flow variability: {variability['std_change_m3h']:.0f} m³/h (std dev)
- Maximum recent change: {variability['max_change_m3h']:.0f} m³/h
- Trend: {variability['trend']}
- Is smooth: {variability['is_smooth']}

Smoothness Constraints:
- Max allowed flow change: {self.max_flow_change_rate} m³/h per 15min
- Goal: Avoid sudden jumps that shock WWTP biology

Historical Context:
- Typical daily variation: 500-2000 m³/h (natural pattern is OK)
- Sudden pump starts/stops create artificial spikes (BAD)

Your task:
1. Assess if recent flow changes are acceptable
2. Evaluate if current pumping strategy is creating unnecessary variability
3. Recommend approach (ALLOW_IMMEDIATE_CHANGE, REQUIRE_GRADUAL_TRANSITION, VETO_SUDDEN_CHANGE)
4. Suggest staged transition plan if needed

Think like a wastewater treatment plant operator who values stable biological processes.
""")

        response = self.llm.generate_structured(
            prompt,
            expected_fields=["analysis", "status", "recommendation", "allow_immediate_change", "staged_plan_needed", "confidence", "priority"]
        )

        # Determine priority
        if variability['max_change_m3h'] > self.max_flow_change_rate * 1.5:
            priority = "HIGH"
        elif variability['max_change_m3h'] > self.max_flow_change_rate:
            priority = "MEDIUM"
        else:
            priority = "LOW"

        return AgentRecommendation(
            agent_name=self.name,
            timestamp=state.timestamp,
            recommendation_type="flow_smoothness",
            priority=response.get('priority', priority),
            confidence=float(response.get('confidence', 0.85)),
            reasoning=response.get('analysis', ''),
            data={
                'variability_metrics': variability,
                'status': response.get('status', 'SMOOTH'),
                'allow_immediate_change': response.get('allow_immediate_change', True),
                'staged_plan_needed': response.get('staged_plan_needed', False),
                'max_allowed_change': self.max_flow_change_rate
            }
        )


class ConstraintComplianceAgent(BaseAgent):
    """
    Agent specialized in enforcing operational constraints

    Tools:
    - Pump runtime tracker
    - Daily emptying checker
    - Constraint validator
    - Violation detector

    Critical constraints:
    - Min pump runtime: 2 hours
    - Daily emptying during dry weather
    - Frequency limits: 47.8-50 Hz
    - Min 1 pump always running
    - Max total flow: 16,000 m³/h
    """

    def __init__(self):
        super().__init__(
            name="constraint_compliance",
            role="Enforce all operational constraints and prevent violations"
        )

        self.llm = get_gemini_llm()
        self.pump_runtime_tracker = {}  # Track when each pump started

        self.register_tool("check_pump_runtimes", self._tool_check_pump_runtimes)
        self.register_tool("check_daily_emptying", self._tool_check_daily_emptying)
        self.register_tool("validate_frequencies", self._tool_validate_frequencies)

    def _tool_check_pump_runtimes(self, state: SystemState, proposed_pumps: List[str]) -> dict:
        """Tool: Check if pump runtime constraints are satisfied"""
        violations = []
        warnings = []

        # Check current active pumps
        for pump_id in state.active_pumps:
            if pump_id not in proposed_pumps:
                # Pump is being stopped - check if it ran for at least 2h
                if pump_id in self.pump_runtime_tracker:
                    start_time = self.pump_runtime_tracker[pump_id]
                    runtime_hours = (state.timestamp - start_time).total_seconds() / 3600

                    if runtime_hours < 2.0:
                        violations.append({
                            "pump": pump_id,
                            "runtime_hours": runtime_hours,
                            "required": 2.0,
                            "type": "MIN_RUNTIME_VIOLATION"
                        })

        # Check if at least 1 pump will be running
        if len(proposed_pumps) == 0:
            violations.append({
                "type": "NO_PUMPS_RUNNING",
                "message": "At least 1 pump must always be running"
            })

        return {
            "violations": violations,
            "warnings": warnings,
            "is_compliant": len(violations) == 0
        }

    def _tool_check_daily_emptying(self, state: SystemState) -> dict:
        """Tool: Check if daily emptying requirement is being met"""
        # Check if it's dry weather (F1 < 1000 m³/15min)
        is_dry_weather = state.F1 < 1000.0

        # Check if we're low enough (L1 < 0.5m)
        is_emptied = state.L1 < 0.5

        # Check time of day (prefer early morning for emptying)
        hour = state.timestamp.hour
        is_good_time = 2 <= hour <= 6  # 2 AM - 6 AM

        # Determine status
        if is_emptied:
            status = "EMPTIED"
            action_needed = False
        elif is_dry_weather and is_good_time:
            status = "OPPORTUNITY_TO_EMPTY"
            action_needed = True
        elif is_dry_weather:
            status = "DRY_WEATHER_BUT_WRONG_TIME"
            action_needed = False
        else:
            status = "WET_WEATHER_CANNOT_EMPTY"
            action_needed = False

        return {
            "status": status,
            "is_dry_weather": is_dry_weather,
            "current_level": state.L1,
            "is_emptied": is_emptied,
            "is_good_time": is_good_time,
            "action_needed": action_needed
        }

    def _tool_validate_frequencies(self, proposed_frequencies: Dict[str, float]) -> dict:
        """Tool: Validate proposed pump frequencies"""
        violations = []

        for pump_id, freq in proposed_frequencies.items():
            if freq > 0:  # If pump is running
                if freq < CONSTRAINTS.FREQ_MIN:
                    violations.append({
                        "pump": pump_id,
                        "frequency": freq,
                        "min_allowed": CONSTRAINTS.FREQ_MIN,
                        "type": "FREQUENCY_TOO_LOW"
                    })
                elif freq > CONSTRAINTS.FREQ_NOMINAL:
                    violations.append({
                        "pump": pump_id,
                        "frequency": freq,
                        "max_allowed": CONSTRAINTS.FREQ_NOMINAL,
                        "type": "FREQUENCY_TOO_HIGH"
                    })

        return {
            "violations": violations,
            "is_compliant": len(violations) == 0
        }

    def assess(self, state: SystemState) -> AgentRecommendation:
        """Assess constraint compliance"""

        # Get currently active pumps from state tracking
        # state.active_pumps is a dict: {pump_id: {'start_time': timestamp, 'frequency': float}}
        proposed_pumps = list(state.active_pumps.keys()) if state.active_pumps else []
        
        # If no active pumps (shouldn't happen), this will be caught as violation
        # Build frequency dict for validation
        proposed_frequencies = {
            pump_id: state.active_pumps[pump_id].get('frequency', 50.0) 
            for pump_id in proposed_pumps
        }

        # Use tools
        runtime_check = self._tool_check_pump_runtimes(state, proposed_pumps)
        emptying_check = self._tool_check_daily_emptying(state)
        frequency_check = self._tool_validate_frequencies(proposed_frequencies)

        # Collect all violations
        all_violations = (
            runtime_check['violations'] +
            frequency_check['violations']
        )

        # Format active pump info for LLM
        active_pump_info = ""
        if proposed_pumps:
            active_pump_info = "\nActive Pumps Running:\n"
            for pump_id in proposed_pumps:
                pump_info = state.active_pumps[pump_id]
                start_time = pump_info['start_time']
                freq = pump_info['frequency']
                runtime_hours = (state.timestamp - start_time).total_seconds() / 3600
                active_pump_info += f"  - {pump_id}: {freq:.1f} Hz (running {runtime_hours:.1f}h)\n"
        else:
            active_pump_info = "\n⚠️ NO PUMPS CURRENTLY ACTIVE ⚠️\n"

        # LLM reasoning
        prompt = self._format_reasoning_prompt(state, f"""
Constraint Compliance Analysis:

Current Situation:
- Active pumps: {len(proposed_pumps)}
{active_pump_info}
- Water level L1: {state.L1:.2f}m
- Current inflow F1: {state.F1:.0f} m³/15min

Constraint Checks:

1. Pump Runtime Compliance:
   - Violations: {len(runtime_check['violations'])}
   - Details: {runtime_check['violations'][:2] if runtime_check['violations'] else 'All OK'}

2. Daily Emptying Status:
   - Status: {emptying_check['status']}
   - Dry weather: {emptying_check['is_dry_weather']}
   - Current level: {emptying_check['current_level']:.2f}m
   - Action needed: {emptying_check['action_needed']}

3. Frequency Compliance:
   - Violations: {len(frequency_check['violations'])}
   - Details: {frequency_check['violations']}

Critical Constraints (MUST enforce):
- Min pump runtime: 2 hours before stopping
- Daily emptying: L1 < 0.5m during dry weather (F1 < 1000)
- Frequency: 47.8-50 Hz when running
- At least 1 pump ALWAYS running
- Max total flow: 16,000 m³/h

Your task:
1. Identify any constraint violations or risks
2. Determine if current state is safe
3. Warn if constraints are violated
4. Always report actual active pump status

These are HARD constraints - they CANNOT be violated for any reason!

Think like a compliance officer who enforces safety rules absolutely.
""")

        response = self.llm.generate_structured(
            prompt,
            expected_fields=["analysis", "compliance_status", "violations_found", "veto_required", "recommended_actions", "confidence", "priority"]
        )

        # Determine priority based on violations
        if len(all_violations) > 0:
            priority = "CRITICAL"
        elif len(proposed_pumps) == 0:
            priority = "CRITICAL"  # No pumps running is always critical
        elif emptying_check['action_needed']:
            priority = "HIGH"
        else:
            priority = "LOW"

        return AgentRecommendation(
            agent_name=self.name,
            timestamp=state.timestamp,
            recommendation_type="constraint_compliance",
            priority=priority,
            confidence=float(response.get('confidence', 0.98)),  # Very high - these are hard rules
            reasoning=response.get('analysis', ''),
            data={
                'compliance_status': response.get('compliance_status', 'COMPLIANT'),
                'active_pumps': proposed_pumps,
                'active_pump_details': state.active_pumps,
                'runtime_check': runtime_check,
                'emptying_check': emptying_check,
                'frequency_check': frequency_check,
                'all_violations': all_violations,
                'veto_required': response.get('veto_required', len(all_violations) > 0),
                'recommended_actions': response.get('recommended_actions', [])
            }
        )


# Initialize function to get all agents
def create_all_agents(lstm_model_path: str) -> Dict[str, BaseAgent]:
    """
    Create all specialist agents

    Args:
        lstm_model_path: Path to LSTM model file

    Returns:
        Dictionary of agent_name → agent instance
    """
    from inflow_agent import InflowForecastingAgent

    print("Creating specialist agents...")

    agents = {
        'inflow_forecasting': InflowForecastingAgent(lstm_model_path),
        'energy_cost': EnergyCostAgent(),
        'pump_efficiency': PumpEfficiencyAgent(),
        'water_level_safety': WaterLevelSafetyAgent(),
        'flow_smoothness': FlowSmoothnessAgent(),
        'constraint_compliance': ConstraintComplianceAgent()
    }

    print(f"✓ Created {len(agents)} specialist agents")

    return agents


if __name__ == "__main__":
    """Test specialist agents"""

    print("="*60)
    print("Specialist Agents - Testing")
    print("="*60)
    print()

    from data_loader import HSYDataLoader

    # Load data
    loader = HSYDataLoader()
    data_dict = loader.load_all_data()
    data = data_dict['operational_data']

    # Create test state
    test_index = 700
    state = SystemState(
        timestamp=data['Time stamp'].iloc[test_index],
        L1=data['L1'].iloc[test_index],
        V=data['V'].iloc[test_index],
        F1=data['F1'].iloc[test_index],
        F2=data['F2'].iloc[test_index],
        electricity_price=data['Price_High'].iloc[test_index],  # Use HIGH scenario
        price_scenario='high',
        historical_data=data,
        current_index=test_index
    )

    print(f"Test State: L1={state.L1:.2f}m, F1={state.F1:.0f}, Price={state.electricity_price:.2f} EUR/kWh")

    # Test each agent
    agents_to_test = [
        ("Energy Cost", EnergyCostAgent()),
        ("Pump Efficiency", PumpEfficiencyAgent()),
        ("Water Level Safety", WaterLevelSafetyAgent())
    ]

    for name, agent in agents_to_test:
        print(f"\n{'='*60}")
        print(f"Testing: {name} Agent")
        print('='*60)

        rec = agent.assess(state)

        print(f"Priority: {rec.priority}")
        print(f"Confidence: {rec.confidence:.2f}")
        print(f"Recommendation: {rec.data.get('recommendation', rec.data.get('status', 'N/A'))}")
        print(f"Reasoning: {rec.reasoning[:200]}...")

    print("\n✓ All agent tests complete!")
