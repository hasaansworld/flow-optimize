"""
FastAPI Server for Multi-Agent System
Exposes all agents as REST endpoints for n8n integration

Endpoints:
- POST /api/v1/assess/inflow - Inflow Forecasting Agent
- POST /api/v1/assess/cost - Energy Cost Agent
- POST /api/v1/assess/efficiency - Pump Efficiency Agent
- POST /api/v1/assess/safety - Water Level Safety Agent
- POST /api/v1/assess/smoothness - Flow Smoothness Agent
- POST /api/v1/assess/compliance - Constraint Compliance Agent
- POST /api/v1/synthesize - Coordinator Agent
- POST /api/v1/decision/execute - Execute pump commands
- GET /api/v1/state - Get current system state
- GET /api/v1/metrics - Get system metrics
- GET /api/v1/health - Health check
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import os

# Add project paths
sys.path.insert(0, str(Path(__file__).parent.parent / 'agents'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'simulation'))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'config'))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import pandas as pd

from base_agent import SystemState, AgentRecommendation
from specialist_agents import create_all_agents
from coordinator_agent import CoordinatorAgent
from data_loader import HSYDataLoader
from physics_simulator import PumpCommand
from pump_models import PumpModel
from constraints import CONSTRAINTS

# Import webhook router
from webhooks import router as webhook_router


# ===== Pydantic Models =====

class SystemStateRequest(BaseModel):
    """Request model for system state"""
    # Optional: If row_number is provided, read data from Excel row
    row_number: Optional[int] = Field(default=None, description="Excel row number to read data from (1-based index)")

    # System state fields (will be auto-populated if row_number is provided)
    timestamp: Optional[str] = Field(default=None)
    L1: Optional[float] = Field(default=None, description="Water level in meters")
    V: Optional[float] = Field(default=None, description="Volume in m³")
    F1: Optional[float] = Field(default=None, description="Inflow in m³/15min")
    F2: Optional[float] = Field(default=None, description="Outflow in m³/h")
    electricity_price: Optional[float] = Field(default=None, description="Price in EUR/kWh")
    price_scenario: str = Field(default="normal", description="'normal' or 'high'")
    active_pumps: Dict[str, Dict] = Field(default_factory=dict)
    current_index: int = Field(default=0, description="Historical data index")


class AgentRecommendationResponse(BaseModel):
    """Response model for agent recommendations"""
    agent_name: str
    timestamp: str
    recommendation_type: str
    priority: str
    confidence: float
    reasoning: str
    data: Dict[str, Any]


class SynthesizeRequest(BaseModel):
    """Request for coordinator synthesis"""
    state: SystemStateRequest
    recommendations: Dict[str, AgentRecommendationResponse]


class PumpCommandResponse(BaseModel):
    """Response model for pump commands with detailed metrics"""
    pump_id: str
    start: bool
    frequency: float
    flow_m3h: float = Field(default=0, description="Flow rate in m³/h")
    power_kw: float = Field(default=0, description="Power consumption in kW")
    efficiency: float = Field(default=0, description="Pump efficiency (0-1)")


class CostCalculation(BaseModel):
    """Detailed cost calculation breakdown"""
    total_power_kw: float
    energy_consumed_kwh: float
    cost_eur: float
    flow_pumped_m3: float
    specific_energy_kwh_per_m3: float


class AgentMessage(BaseModel):
    """Individual agent assessment message"""
    agent_name: str
    priority: str
    confidence: float
    recommendation_type: str
    reasoning: str
    key_data: Dict[str, Any] = Field(default_factory=dict)


class DecisionResponse(BaseModel):
    """Complete decision response with evaluation metrics"""
    timestamp: str
    pump_commands: List[PumpCommandResponse]
    coordinator_reasoning: str
    priority_applied: str
    conflicts_resolved: List[str]
    confidence: float

    # Evaluation metrics (matching run_evaluation.py output)
    cost_calculation: CostCalculation
    constraint_violations: List[Dict[str, Any]] = Field(default_factory=list)

    # Individual agent messages (NEW!)
    agent_messages: List[AgentMessage] = Field(default_factory=list)


class MetricsResponse(BaseModel):
    """System metrics response"""
    total_decisions: int
    total_energy_cost: float
    total_energy_kwh: float
    avg_water_level: float
    min_water_level: float
    max_water_level: float
    safety_violations: int
    uptime_hours: float


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    agents_loaded: int
    data_available: bool
    timestamp: str


# ===== FastAPI App =====

app = FastAPI(
    title="Multi-Agent Wastewater Control API",
    description="REST API for n8n integration with multi-agent pumping system",
    version="1.0.0"
)

# Enable CORS for n8n
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify n8n URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include webhook router
app.include_router(webhook_router)


# ===== Global State =====

class AppState:
    """Application state container"""
    def __init__(self):
        self.specialist_agents = None
        self.coordinator = None
        self.data = None
        self.loader = None
        self.pump_model = None
        self.decision_history = []
        self.metrics = {
            'total_decisions': 0,
            'total_energy_cost': 0.0,
            'total_energy_kwh': 0.0,
            'safety_violations': 0,
            'start_time': datetime.now()
        }
        self.initialized = False


app_state = AppState()


# ===== Startup/Shutdown =====

@app.on_event("startup")
async def startup_event():
    """Initialize agents and load data on startup"""
    print("🚀 Starting Multi-Agent API Server...")

    try:
        # Get model path
        script_dir = Path(__file__).parent.parent / 'agents'
        model_path = script_dir.parent / 'models' / 'inflow_lstm_model.pth'

        # Create agents
        print("📦 Loading specialist agents...")
        app_state.specialist_agents = create_all_agents(str(model_path))
        app_state.coordinator = CoordinatorAgent()
        print(f"✓ Loaded {len(app_state.specialist_agents)} specialist agents + coordinator")

        # Initialize pump model for power calculations
        print("🔧 Loading pump model...")
        app_state.pump_model = PumpModel()
        print("✓ Pump model initialized")

        # Load historical data
        print("📊 Loading historical data...")
        app_state.loader = HSYDataLoader()
        data_dict = app_state.loader.load_all_data()
        app_state.data = data_dict['operational_data']
        print(f"✓ Loaded {len(app_state.data)} timesteps of data")

        app_state.initialized = True
        print("✅ API Server ready!")

    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        import traceback
        traceback.print_exc()
        app_state.initialized = False


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("👋 Shutting down Multi-Agent API Server...")


# ===== Helper Functions =====

def populate_request_from_excel(req: SystemStateRequest) -> SystemStateRequest:
    """
    If row_number is provided, populate request fields from Excel data
    Returns the populated request
    """
    if req.row_number is None:
        # No row_number provided, use request as-is
        return req

    if app_state.data is None:
        raise HTTPException(status_code=503, detail="Historical data not loaded")

    # Convert 1-based row number to 0-based index
    row_index = req.row_number - 1

    if row_index < 0 or row_index >= len(app_state.data):
        raise HTTPException(
            status_code=400,
            detail=f"Row number {req.row_number} out of range. Valid range: 1-{len(app_state.data)}"
        )

    # Get the row from Excel data
    row = app_state.data.iloc[row_index]

    # Determine electricity price based on price_scenario
    if req.price_scenario == "high":
        electricity_price = float(row['Price_High'])
    else:
        electricity_price = float(row['Price_Normal'])

    # Create a new request with populated fields
    return SystemStateRequest(
        row_number=req.row_number,
        timestamp=str(row['Time stamp']),
        L1=float(row['L1']),
        V=float(row['V']),
        F1=float(row['F1']),
        F2=float(row['F2']),
        electricity_price=electricity_price,
        price_scenario=req.price_scenario,
        active_pumps=req.active_pumps,
        current_index=row_index
    )


def request_to_system_state(req: SystemStateRequest) -> SystemState:
    """Convert request model to SystemState"""
    return SystemState(
        timestamp=datetime.fromisoformat(req.timestamp) if isinstance(req.timestamp, str) else req.timestamp,
        L1=req.L1,
        V=req.V,
        F1=req.F1,
        F2=req.F2,
        electricity_price=req.electricity_price,
        price_scenario=req.price_scenario,
        active_pumps=req.active_pumps,
        historical_data=app_state.data,
        current_index=req.current_index
    )


def recommendation_to_response(rec: AgentRecommendation) -> AgentRecommendationResponse:
    """Convert AgentRecommendation to response model"""
    return AgentRecommendationResponse(
        agent_name=rec.agent_name,
        timestamp=rec.timestamp.isoformat() if isinstance(rec.timestamp, datetime) else str(rec.timestamp),
        recommendation_type=rec.recommendation_type,
        priority=rec.priority,
        confidence=rec.confidence,
        reasoning=rec.reasoning,
        data=rec.data
    )


def calculate_pump_metrics(pump_id: str, frequency: float, L1: float) -> tuple:
    """
    Calculate flow, power, and efficiency for a pump command
    (Matches logic from run_evaluation.py)

    Returns:
        (flow_m3h, power_kw, efficiency)
    """
    if frequency == 0:
        return 0, 0, 0

    try:
        flow, power, efficiency = app_state.pump_model.calculate_pump_performance(
            pump_id, frequency, L1
        )
        return flow, power, efficiency
    except Exception:
        # Fallback estimation if pump curve fails
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


# ===== API Endpoints =====

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    return await health_check()


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if app_state.initialized else "initializing",
        version="1.0.0",
        agents_loaded=len(app_state.specialist_agents) if app_state.specialist_agents else 0,
        data_available=app_state.data is not None,
        timestamp=datetime.now().isoformat()
    )


@app.post("/api/v1/assess/inflow", response_model=AgentRecommendationResponse)
async def assess_inflow(state_req: SystemStateRequest):
    """Inflow Forecasting Agent assessment"""
    if not app_state.initialized:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        state_req = populate_request_from_excel(state_req)
        state = request_to_system_state(state_req)
        agent = app_state.specialist_agents['inflow_forecasting']
        recommendation = agent.assess(state)
        return recommendation_to_response(recommendation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent assessment failed: {str(e)}")


@app.post("/api/v1/assess/cost", response_model=AgentRecommendationResponse)
async def assess_cost(state_req: SystemStateRequest):
    """Energy Cost Agent assessment"""
    if not app_state.initialized:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        state_req = populate_request_from_excel(state_req)
        state = request_to_system_state(state_req)
        agent = app_state.specialist_agents['energy_cost']
        recommendation = agent.assess(state)
        return recommendation_to_response(recommendation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent assessment failed: {str(e)}")


@app.post("/api/v1/assess/efficiency", response_model=AgentRecommendationResponse)
async def assess_efficiency(state_req: SystemStateRequest):
    """Pump Efficiency Agent assessment"""
    if not app_state.initialized:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        state_req = populate_request_from_excel(state_req)
        state = request_to_system_state(state_req)
        agent = app_state.specialist_agents['pump_efficiency']
        recommendation = agent.assess(state)
        return recommendation_to_response(recommendation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent assessment failed: {str(e)}")


@app.post("/api/v1/assess/safety", response_model=AgentRecommendationResponse)
async def assess_safety(state_req: SystemStateRequest):
    """Water Level Safety Agent assessment"""
    if not app_state.initialized:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        state_req = populate_request_from_excel(state_req)
        state = request_to_system_state(state_req)
        agent = app_state.specialist_agents['water_level_safety']
        recommendation = agent.assess(state)
        return recommendation_to_response(recommendation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent assessment failed: {str(e)}")


@app.post("/api/v1/assess/smoothness", response_model=AgentRecommendationResponse)
async def assess_smoothness(state_req: SystemStateRequest):
    """Flow Smoothness Agent assessment"""
    if not app_state.initialized:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        state_req = populate_request_from_excel(state_req)
        state = request_to_system_state(state_req)
        agent = app_state.specialist_agents['flow_smoothness']
        recommendation = agent.assess(state)
        return recommendation_to_response(recommendation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent assessment failed: {str(e)}")


@app.post("/api/v1/assess/compliance", response_model=AgentRecommendationResponse)
async def assess_compliance(state_req: SystemStateRequest):
    """Constraint Compliance Agent assessment"""
    if not app_state.initialized:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        state_req = populate_request_from_excel(state_req)
        state = request_to_system_state(state_req)
        agent = app_state.specialist_agents['constraint_compliance']
        recommendation = agent.assess(state)
        return recommendation_to_response(recommendation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent assessment failed: {str(e)}")


@app.post("/api/v1/assess/all", response_model=Dict[str, AgentRecommendationResponse])
async def assess_all(state_req: SystemStateRequest):
    """Run all specialist agents in parallel"""
    if not app_state.initialized:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        state_req = populate_request_from_excel(state_req)
        state = request_to_system_state(state_req)
        recommendations = {}

        for agent_name, agent in app_state.specialist_agents.items():
            rec = agent.assess(state)
            recommendations[agent_name] = recommendation_to_response(rec)

        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multi-agent assessment failed: {str(e)}")


@app.post("/api/v1/synthesize", response_model=DecisionResponse)
async def synthesize(state_req: SystemStateRequest):
    """
    Complete decision cycle: Run all agents + coordinator synthesis
    This is the main endpoint for n8n workflows

    Two usage modes:
    1. Provide row_number (e.g., {"row_number": 100}) - reads data from Excel row
    2. Provide all fields manually - uses provided values
    """
    if not app_state.initialized:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        # Populate request from Excel if row_number is provided
        state_req = populate_request_from_excel(state_req)

        state = request_to_system_state(state_req)
        print(f"State: {state}")

        # Step 1: Run all specialist agents
        recommendations = {}
        for agent_name, agent in app_state.specialist_agents.items():
            rec = agent.assess(state)
            recommendations[agent_name] = rec

        # Step 2: Coordinator synthesis
        pump_commands = app_state.coordinator.synthesize_recommendations(state, recommendations)

        # Step 3: Calculate power and flow for each pump (matching run_evaluation.py)
        enhanced_commands = []
        total_power_kw = 0
        total_flow_m3h = 0

        for cmd in pump_commands:
            flow, power, efficiency = calculate_pump_metrics(
                cmd.pump_id,
                cmd.frequency if cmd.start else 0,
                state.L1
            )

            enhanced_commands.append(PumpCommandResponse(
                pump_id=cmd.pump_id,
                start=cmd.start,
                frequency=cmd.frequency,
                flow_m3h=flow,
                power_kw=power,
                efficiency=efficiency
            ))

            if cmd.start:
                total_power_kw += power
                total_flow_m3h += flow

        # Step 4: Calculate cost for this timestep (15 min = 0.25 h)
        energy_kwh = total_power_kw * 0.25
        cost_eur = energy_kwh * state.electricity_price
        flow_m3 = total_flow_m3h * 0.25
        specific_energy = energy_kwh / flow_m3 if flow_m3 > 0 else 0

        # Step 5: Check constraint violations
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

        # Step 6: Format agent messages
        import numpy as np

        def convert_to_serializable(obj):
            """Convert numpy/pandas types to JSON-serializable types"""
            if isinstance(obj, (np.integer, np.floating)):
                return obj.item()
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, (np.bool_, bool)):
                return bool(obj)
            elif isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_to_serializable(item) for item in obj]
            return obj

        agent_messages = []
        for agent_name, rec in recommendations.items():
            # Convert all data to JSON-serializable format
            key_data = convert_to_serializable(rec.data) if rec.data else {}

            agent_messages.append(AgentMessage(
                agent_name=agent_name,
                priority=rec.priority,
                confidence=float(rec.confidence),  # Ensure float
                recommendation_type=rec.recommendation_type,
                reasoning=rec.reasoning,
                key_data=key_data
            ))

        # Step 7: Extract coordinator decision
        if app_state.coordinator.history:
            decision = app_state.coordinator.history[-1]

            # Update metrics
            app_state.metrics['total_decisions'] += 1
            app_state.metrics['total_energy_cost'] += cost_eur
            app_state.metrics['total_energy_kwh'] += energy_kwh
            app_state.metrics['safety_violations'] += len(violations)

            app_state.decision_history.append({
                'timestamp': state.timestamp.isoformat(),
                'pump_commands': [
                    {'pump_id': cmd.pump_id, 'frequency': cmd.frequency, 'run': cmd.start}
                    for cmd in pump_commands
                ],
                'reasoning': decision.reasoning,
                'cost_eur': cost_eur,
                'energy_kwh': energy_kwh
            })

            return DecisionResponse(
                timestamp=state.timestamp.isoformat(),
                pump_commands=enhanced_commands,
                coordinator_reasoning=decision.reasoning,
                priority_applied=decision.data.get('llm_response', {}).get('priority_applied', 'MEDIUM'),
                conflicts_resolved=decision.data.get('conflicts_resolved', []),
                confidence=decision.confidence,
                cost_calculation=CostCalculation(
                    total_power_kw=total_power_kw,
                    energy_consumed_kwh=energy_kwh,
                    cost_eur=cost_eur,
                    flow_pumped_m3=flow_m3,
                    specific_energy_kwh_per_m3=specific_energy
                ),
                constraint_violations=violations,
                agent_messages=agent_messages
            )
        else:
            raise HTTPException(status_code=500, detail="Coordinator failed to produce decision")

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Decision synthesis failed: {str(e)}")


@app.get("/api/v1/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get system performance metrics"""
    if not app_state.initialized:
        raise HTTPException(status_code=503, detail="Service not initialized")

    # Calculate uptime
    uptime = (datetime.now() - app_state.metrics['start_time']).total_seconds() / 3600

    # Calculate water level statistics from recent decisions
    water_levels = []
    if app_state.data is not None and len(app_state.data) > 0:
        recent_data = app_state.data.tail(100)
        water_levels = recent_data['L1'].values

    return MetricsResponse(
        total_decisions=app_state.metrics['total_decisions'],
        total_energy_cost=app_state.metrics['total_energy_cost'],
        total_energy_kwh=app_state.metrics['total_energy_kwh'],
        avg_water_level=float(water_levels.mean()) if len(water_levels) > 0 else 0.0,
        min_water_level=float(water_levels.min()) if len(water_levels) > 0 else 0.0,
        max_water_level=float(water_levels.max()) if len(water_levels) > 0 else 0.0,
        safety_violations=app_state.metrics['safety_violations'],
        uptime_hours=uptime
    )


@app.get("/api/v1/state/current")
async def get_current_state(index: Optional[int] = None):
    """Get current system state from historical data"""
    if not app_state.initialized or app_state.data is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        # Use provided index or latest
        idx = index if index is not None else len(app_state.data) - 1

        if idx < 0 or idx >= len(app_state.data):
            raise HTTPException(status_code=400, detail=f"Index {idx} out of range")

        row = app_state.data.iloc[idx]

        return {
            "timestamp": str(row['Time stamp']),
            "L1": float(row['L1']),
            "V": float(row['V']),
            "F1": float(row['F1']),
            "F2": float(row['F2']),
            "electricity_price_normal": float(row['Price_Normal']),
            "electricity_price_high": float(row['Price_High']),
            "current_index": idx
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get state: {str(e)}")


@app.get("/api/v1/decisions/history")
async def get_decision_history(limit: int = 100):
    """Get recent decision history"""
    if not app_state.initialized:
        raise HTTPException(status_code=503, detail="Service not initialized")

    return {
        "total_decisions": len(app_state.decision_history),
        "decisions": app_state.decision_history[-limit:]
    }


# ===== Main =====

if __name__ == "__main__":
    import uvicorn

    # Get port from environment or default to 8000
    port = int(os.getenv("API_PORT", "8000"))

    print("\n" + "="*60)
    print("Multi-Agent Wastewater Control API")
    print("="*60)
    print(f"\n🌐 Starting server on http://localhost:{port}")
    print(f"\n📚 API Docs: http://localhost:{port}/docs")
    print(f"📊 Redoc: http://localhost:{port}/redoc")
    print("\n" + "="*60 + "\n")

    uvicorn.run(
        "agent_api:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
