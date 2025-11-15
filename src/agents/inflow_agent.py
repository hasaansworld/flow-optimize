"""
Inflow Forecasting Agent
Predicts future wastewater inflow using LSTM + LLM reasoning
"""

import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'models'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'simulation'))

from base_agent import BaseAgent, SystemState, AgentRecommendation
from gemini_wrapper import get_gemini_llm
from inflow_forecaster import InflowForecastingSystem
from datetime import datetime


class InflowForecastingAgent(BaseAgent):
    """
    Agent specialized in predicting future inflow

    Tools:
    - LSTM model for 6h and 24h forecasts
    - Storm pattern detector
    - Dry weather classifier
    - Trend analyzer

    Outputs:
    - Inflow forecast (next 6h and 24h)
    - Storm alerts
    - Dry weather status (for daily emptying)
    - Peak inflow predictions
    """

    def __init__(self, model_path: str):
        super().__init__(
            name="inflow_forecasting",
            role="Predict future wastewater inflow to enable proactive pump planning"
        )

        # Load LSTM forecaster
        self.forecaster = InflowForecastingSystem(
            lookback_steps=48,
            forecast_horizon=24
        )

        if Path(model_path).exists():
            self.forecaster.load_model(model_path)
            print(f"  ✓ Loaded LSTM model from {model_path}")
        else:
            print(f"  ⚠️  LSTM model not found at {model_path}")
            print(f"     Will train when data is available")
            self.forecaster = None

        # LLM for reasoning
        self.llm = get_gemini_llm()

        # Register tools
        self.register_tool("lstm_forecast", self._tool_lstm_forecast)
        self.register_tool("detect_storm", self._tool_detect_storm)
        self.register_tool("check_dry_weather", self._tool_check_dry_weather)

    def _tool_lstm_forecast(self, state: SystemState, horizon: int = 24) -> np.ndarray:
        """Tool: Generate LSTM forecast"""
        if self.forecaster is None or state.historical_data is None:
            # Fallback: simple persistence model
            return np.full(horizon, state.F1)

        forecast = self.forecaster.predict(
            state.historical_data,
            state.current_index,
            horizon_steps=horizon
        )
        return forecast

    def _tool_detect_storm(self, state: SystemState, forecast: np.ndarray = None) -> dict:
        """Tool: Detect if storm is predicted"""
        if forecast is None:
            forecast = self._tool_lstm_forecast(state)

        threshold = 1500.0  # m³/15min
        peak_value = np.max(forecast)
        peak_index = np.argmax(forecast)
        is_storm = peak_value > threshold

        return {
            "storm_detected": bool(is_storm),
            "peak_inflow": float(peak_value),
            "peak_time_steps_ahead": int(peak_index),
            "peak_time_hours": peak_index * 0.25
        }

    def _tool_check_dry_weather(self, state: SystemState) -> bool:
        """Tool: Check if current conditions are dry weather"""
        threshold = 1000.0  # m³/15min
        return state.F1 < threshold

    def assess(self, state: SystemState) -> AgentRecommendation:
        """
        Assess inflow situation and generate forecast

        Args:
            state: Current system state

        Returns:
            AgentRecommendation with forecast and analysis
        """

        # Use tools to gather data
        forecast_6h = self._tool_lstm_forecast(state, horizon=24)  # 6h = 24 timesteps
        forecast_24h = self._tool_lstm_forecast(state, horizon=96) if self.forecaster else forecast_6h

        storm_info = self._tool_detect_storm(state, forecast_6h)
        is_dry = self._tool_check_dry_weather(state)

        # Analyze trend
        if len(forecast_6h) >= 4:
            recent_trend = forecast_6h[:4]
            is_rising = recent_trend[-1] > recent_trend[0]
            trend_magnitude = abs(recent_trend[-1] - recent_trend[0])
        else:
            is_rising = False
            trend_magnitude = 0

        # Create LLM reasoning prompt
        prompt = self._format_reasoning_prompt(state, f"""
Inflow Analysis Data:

Current Conditions:
- Current inflow (F1): {state.F1:.0f} m³/15min
- Is dry weather: {is_dry} (threshold: <1000 m³/15min)

LSTM Forecast (next 6 hours):
- Forecast values: {forecast_6h[:8].tolist()} (showing first 8 of 24 steps)
- Trend: {"RISING" if is_rising else "FALLING"} (magnitude: {trend_magnitude:.0f} m³/15min)

Storm Detection:
- Storm detected: {storm_info['storm_detected']}
- Peak inflow: {storm_info['peak_inflow']:.0f} m³/15min
- Peak in {storm_info['peak_time_hours']:.1f} hours

Your task:
1. Interpret the LSTM forecast and current conditions
2. Assess if this is normal daily pattern or unusual event
3. Provide context for other agents (cost, pump, safety agents)
4. Warn about storms or dry weather opportunities

Think like an experienced hydrologist who understands daily flow patterns,
storm signatures, and seasonal variations.
""")

        # Get LLM reasoning
        response = self.llm.generate_structured(
            prompt,
            expected_fields=[
                "analysis",
                "forecast_summary",
                "weather_status",
                "storm_warning",
                "dry_weather_opportunity",
                "confidence",
                "priority",
                "key_insights"
            ]
        )

        # Determine priority
        if storm_info['storm_detected']:
            priority = "HIGH"
        elif is_dry:
            priority = "MEDIUM"
        else:
            priority = "LOW"

        # Create recommendation
        recommendation = AgentRecommendation(
            agent_name=self.name,
            timestamp=state.timestamp,
            recommendation_type="inflow_forecast",
            priority=response.get('priority', priority),
            confidence=float(response.get('confidence', 0.85)),
            reasoning=response.get('analysis', 'LSTM-based forecast analysis'),
            data={
                'forecast_6h': forecast_6h.tolist(),
                'forecast_24h': forecast_24h.tolist() if len(forecast_24h) > 0 else [],
                'current_inflow': state.F1,
                'storm_detected': storm_info['storm_detected'],
                'peak_inflow': storm_info['peak_inflow'],
                'peak_in_hours': storm_info['peak_time_hours'],
                'is_dry_weather': is_dry,
                'weather_status': response.get('weather_status', 'NORMAL'),
                'llm_analysis': response.get('forecast_summary', ''),
                'key_insights': response.get('key_insights', [])
            }
        )

        # Store in history
        self.history.append(recommendation)

        return recommendation


if __name__ == "__main__":
    """Test Inflow Forecasting Agent"""

    print("="*60)
    print("Inflow Forecasting Agent - Testing")
    print("="*60)
    print()

    from data_loader import HSYDataLoader

    # Load data
    print("Loading historical data...")
    loader = HSYDataLoader()
    data_dict = loader.load_all_data()
    data = data_dict['operational_data']

    # Create agent
    model_path = Path(__file__).parent.parent / 'models' / 'inflow_lstm_model.pth'
    agent = InflowForecastingAgent(str(model_path))

    # Create test state
    test_index = 500
    state = SystemState(
        timestamp=data['Time stamp'].iloc[test_index],
        L1=data['L1'].iloc[test_index],
        V=data['V'].iloc[test_index],
        F1=data['F1'].iloc[test_index],
        F2=data['F2'].iloc[test_index],
        electricity_price=data['Price_Normal'].iloc[test_index],
        price_scenario='normal',
        historical_data=data,
        current_index=test_index
    )

    print(f"\nTest State:")
    print(f"  Time: {state.timestamp}")
    print(f"  L1: {state.L1:.2f}m")
    print(f"  F1: {state.F1:.0f} m³/15min")
    print(f"  Price: {state.electricity_price:.3f} EUR/kWh")

    # Assess
    print("\n" + "="*60)
    print("Running Agent Assessment...")
    print("="*60)

    recommendation = agent.assess(state)

    print(f"\nAgent: {recommendation.agent_name}")
    print(f"Priority: {recommendation.priority}")
    print(f"Confidence: {recommendation.confidence:.2f}")
    print(f"\nReasoning:")
    print(recommendation.reasoning)
    print(f"\nData:")
    for key, value in recommendation.data.items():
        if isinstance(value, list) and len(value) > 10:
            print(f"  {key}: {value[:5]} ... (length: {len(value)})")
        else:
            print(f"  {key}: {value}")

    print("\n✓ Agent test complete!")
