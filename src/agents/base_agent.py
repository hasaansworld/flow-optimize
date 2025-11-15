"""
Base Agent Class for Multi-Agent System
All specialized agents inherit from this
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class AgentMessage:
    """Message passed between agents"""
    from_agent: str
    to_agent: str
    content: str
    timestamp: datetime
    data: Optional[Dict] = None


@dataclass
class SystemState:
    """Shared system state accessible by all agents"""
    timestamp: datetime
    L1: float  # Water level (m)
    V: float  # Volume (m³)
    F1: float  # Inflow (m³/15min)
    F2: float  # Total outflow (m³/h)
    electricity_price: float  # EUR/kWh
    price_scenario: str  # 'high' or 'normal'
    active_pumps: Dict[str, Dict] = field(default_factory=dict)
    total_energy_cost: float = 0.0
    total_energy_kwh: float = 0.0
    violations: List[str] = field(default_factory=list)
    messages: List[AgentMessage] = field(default_factory=list)

    # Additional context
    historical_data: Optional[Any] = None
    current_index: int = 0


@dataclass
class AgentRecommendation:
    """Recommendation from an agent"""
    agent_name: str
    timestamp: datetime
    recommendation_type: str
    priority: str  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    confidence: float  # 0-1
    reasoning: str
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'agent_name': self.agent_name,
            'timestamp': self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else str(self.timestamp),
            'recommendation_type': self.recommendation_type,
            'priority': self.priority,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'data': self.data
        }


class BaseAgent:
    """
    Base class for all specialized agents

    Each agent:
    - Has ONE specific job
    - Uses tools (ML models, optimizers, calculators)
    - Generates recommendations using LLM reasoning
    - Communicates with other agents
    """

    def __init__(self, name: str, role: str):
        """
        Initialize agent

        Args:
            name: Agent identifier (e.g., "inflow_forecasting")
            role: Agent role description
        """
        self.name = name
        self.role = role
        self.tools = {}  # Tools available to this agent
        self.history = []  # History of recommendations

    def register_tool(self, tool_name: str, tool_function):
        """Register a tool for this agent to use"""
        self.tools[tool_name] = tool_function
        print(f"  ✓ Registered tool: {tool_name}")

    def assess(self, state: SystemState) -> AgentRecommendation:
        """
        Make assessment and generate recommendation

        This is the main method each agent implements

        Args:
            state: Current system state

        Returns:
            AgentRecommendation
        """
        raise NotImplementedError("Subclasses must implement assess()")

    def send_message(self, to_agent: str, content: str, data: Optional[Dict] = None) -> AgentMessage:
        """Create a message to another agent"""
        return AgentMessage(
            from_agent=self.name,
            to_agent=to_agent,
            content=content,
            timestamp=datetime.now(),
            data=data
        )

    def _format_state_summary(self, state: SystemState) -> str:
        """Format state summary for LLM prompts"""
        return f"""
Current System State ({state.timestamp}):
- Water Level (L1): {state.L1:.2f}m (Safe range: 0-8m, Alarm: 7.2m)
- Volume (V): {state.V:.0f}m³
- Inflow (F1): {state.F1:.0f}m³/15min
- Outflow (F2): {state.F2:.0f}m³/h
- Electricity Price: {state.electricity_price:.3f} EUR/kWh ({state.price_scenario.upper()} scenario)
- Active Pumps: {len(state.active_pumps)} running
- Total Energy Cost: {state.total_energy_cost:.2f} EUR
- Active Violations: {len(state.violations)}
"""

    def _format_reasoning_prompt(self, state: SystemState, additional_context: str = "") -> str:
        """
        Create base reasoning prompt for LLM

        Args:
            state: Current system state
            additional_context: Agent-specific context

        Returns:
            Formatted prompt string
        """
        prompt = f"""
You are the **{self.name.replace('_', ' ').title()} Agent** for an autonomous wastewater pumping station control system.

Your role: {self.role}

{self._format_state_summary(state)}

{additional_context}

Your task:
1. Analyze the current situation from your specialized perspective
2. Use your tools if needed
3. Provide clear reasoning
4. Make a specific recommendation

Output your response as JSON with this structure:
{{
  "analysis": "Your detailed analysis of the situation",
  "tools_used": ["list", "of", "tools"],
  "recommendation": "Your specific recommendation",
  "priority": "LOW|MEDIUM|HIGH|CRITICAL",
  "confidence": 0.85,
  "reasoning": "Explain why you made this recommendation"
}}
"""
        return prompt

    def __repr__(self):
        return f"<Agent: {self.name}>"


class AgentRegistry:
    """Registry for managing all agents"""

    def __init__(self):
        self.agents = {}

    def register(self, agent: BaseAgent):
        """Register an agent"""
        self.agents[agent.name] = agent
        print(f"✓ Registered agent: {agent.name}")

    def get(self, name: str) -> Optional[BaseAgent]:
        """Get agent by name"""
        return self.agents.get(name)

    def get_all(self) -> List[BaseAgent]:
        """Get all registered agents"""
        return list(self.agents.values())

    def __len__(self):
        return len(self.agents)


if __name__ == "__main__":
    """Test base agent"""

    print("="*60)
    print("Base Agent Testing")
    print("="*60)
    print()

    # Create test agent
    class TestAgent(BaseAgent):
        def assess(self, state: SystemState) -> AgentRecommendation:
            return AgentRecommendation(
                agent_name=self.name,
                timestamp=datetime.now(),
                recommendation_type="test",
                priority="LOW",
                confidence=1.0,
                reasoning="Test recommendation",
                data={}
            )

    # Test
    agent = TestAgent("test_agent", "Testing agent functionality")
    print(f"Created: {agent}")

    # Register tool
    agent.register_tool("test_tool", lambda x: x * 2)
    print(f"Tools: {list(agent.tools.keys())}")

    # Test state
    state = SystemState(
        timestamp=datetime.now(),
        L1=3.5,
        V=15000,
        F1=800,
        F2=5000,
        electricity_price=5.2,
        price_scenario="normal"
    )

    # Test assessment
    recommendation = agent.assess(state)
    print(f"\nRecommendation:")
    print(json.dumps(recommendation.to_dict(), indent=2))

    # Test registry
    registry = AgentRegistry()
    registry.register(agent)
    print(f"\nRegistry size: {len(registry)}")

    print("\n✓ Base agent tests passed!")
