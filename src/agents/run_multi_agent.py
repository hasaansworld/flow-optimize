"""
Multi-Agent Wastewater Pumping System
Main orchestration script

Runs the complete multi-agent system:
1. Load historical data
2. Initialize all 6 specialist agents + coordinator
3. Run decision loop every 15 minutes (simulated time)
4. Optionally connect to OPC UA for live control
"""

import sys
from pathlib import Path
import time
import asyncio
from datetime import datetime
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'simulation'))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'config'))

from base_agent import SystemState
from specialist_agents import create_all_agents
from coordinator_agent import CoordinatorAgent
from data_loader import HSYDataLoader
from physics_simulator import PumpCommand

# Optional: OPC UA client
try:
    from asyncua import Client
    OPCUA_AVAILABLE = True
except ImportError:
    OPCUA_AVAILABLE = False
    print("⚠️  asyncua not available - running in simulation mode only")


class MultiAgentController:
    """
    Multi-Agent Controller

    Orchestrates the entire decision-making process:
    1. Gather system state (from OPC UA or simulation)
    2. Run all specialist agents in parallel
    3. Coordinator synthesizes recommendations
    4. Execute pump commands (to OPC UA or simulation)
    """

    def __init__(
        self,
        lstm_model_path: str,
        price_scenario: str = 'normal',
        opcua_url: str = None
    ):
        """
        Initialize multi-agent controller

        Args:
            lstm_model_path: Path to trained LSTM model
            price_scenario: 'normal' or 'high' electricity prices
            opcua_url: Optional OPC UA server URL (e.g., 'opc.tcp://localhost:4840')
        """
        print("\n" + "="*60)
        print("MULTI-AGENT WASTEWATER PUMPING SYSTEM")
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

        # Settings
        self.price_scenario = price_scenario
        self.opcua_url = opcua_url
        self.opcua_client = None

        # Metrics tracking
        self.total_energy_cost = 0.0
        self.total_energy_kwh = 0.0
        self.decision_count = 0

        print(f"\nSettings:")
        print(f"  Price scenario: {price_scenario.upper()}")
        print(f"  OPC UA: {'Enabled - ' + opcua_url if opcua_url else 'Disabled (simulation only)'}")

    async def connect_opcua(self):
        """Connect to OPC UA server"""
        if not self.opcua_url or not OPCUA_AVAILABLE:
            return

        try:
            self.opcua_client = Client(url=self.opcua_url)
            await self.opcua_client.connect()
            print(f"✓ Connected to OPC UA server: {self.opcua_url}")
        except Exception as e:
            print(f"❌ Failed to connect to OPC UA: {e}")
            self.opcua_client = None

    async def disconnect_opcua(self):
        """Disconnect from OPC UA server"""
        if self.opcua_client:
            await self.opcua_client.disconnect()
            print("✓ Disconnected from OPC UA")

    async def read_state_from_opcua(self) -> SystemState:
        """Read current state from OPC UA server"""
        if not self.opcua_client:
            raise RuntimeError("OPC UA client not connected")

        # Read sensor nodes
        root = self.opcua_client.nodes.objects
        sensors = await root.get_child(["2:Sensors"])

        L1_node = await sensors.get_child(["2:L1"])
        V_node = await sensors.get_child(["2:V"])
        F1_node = await sensors.get_child(["2:F1"])
        F2_node = await sensors.get_child(["2:F2"])
        price_node = await sensors.get_child(["2:ElectricityPrice"])

        L1 = await L1_node.read_value()
        V = await V_node.read_value()
        F1 = await F1_node.read_value()
        F2 = await F2_node.read_value()
        price = await price_node.read_value()

        return SystemState(
            timestamp=datetime.now(),
            L1=L1,
            V=V,
            F1=F1,
            F2=F2,
            electricity_price=price,
            price_scenario=self.price_scenario,
            historical_data=self.data,
            current_index=len(self.data) - 1  # Use latest for forecasting
        )

    async def write_commands_to_opcua(self, commands: list):
        """Write pump commands to OPC UA server"""
        if not self.opcua_client:
            return

        root = self.opcua_client.nodes.objects
        control = await root.get_child(["2:Control"])

        for cmd in commands:
            try:
                pump_node = await control.get_child([f"2:{cmd.pump_id}"])
                freq_node = await pump_node.get_child(["2:Frequency"])
                await freq_node.write_value(cmd.frequency)
            except Exception as e:
                print(f"⚠️  Failed to write {cmd.pump_id} command: {e}")

    def run_decision_cycle(self, state: SystemState) -> list:
        """
        Run one complete decision cycle

        Args:
            state: Current system state

        Returns:
            List of PumpCommand objects
        """
        print(f"\n{'='*60}")
        print(f"Decision Cycle #{self.decision_count + 1}")
        print(f"Time: {state.timestamp}")
        print(f"{'='*60}")

        print(f"\nSystem State:")
        print(f"  L1: {state.L1:.2f}m")
        print(f"  F1: {state.F1:.0f} m³/15min")
        print(f"  F2: {state.F2:.0f} m³/h")
        print(f"  Price: {state.electricity_price:.3f} EUR/kWh")

        # Step 1: Run all specialist agents
        print(f"\n--- Specialist Agent Assessments ---")
        recommendations = {}

        for name, agent in self.specialist_agents.items():
            try:
                rec = agent.assess(state)
                recommendations[name] = rec
                print(f"{name:25s} | Priority: {rec.priority:8s} | Confidence: {rec.confidence:.2f}")
            except Exception as e:
                print(f"❌ {name} failed: {e}")

        # Step 2: Coordinator synthesis
        print(f"\n--- Coordinator Synthesis ---")
        pump_commands = self.coordinator.synthesize_recommendations(state, recommendations)

        # Step 3: Display final decision
        print(f"\n--- Final Pump Commands ---")
        active_pumps = [cmd for cmd in pump_commands if cmd.start]

        if active_pumps:
            for cmd in active_pumps:
                print(f"  {cmd.pump_id}: {cmd.frequency:.1f} Hz")
        else:
            print("  (No pumps active - should not happen!)")

        # Show coordinator reasoning
        if self.coordinator.history:
            decision = self.coordinator.history[-1]
            print(f"\nCoordinator Reasoning:")
            print(f"  {decision.reasoning[:150]}...")
            print(f"\n  Estimated flow: {decision.data.get('estimated_flow', 0):.0f} m³/h")
            print(f"  Estimated cost: {decision.data.get('estimated_cost', 0):.2f} EUR/h")

        self.decision_count += 1

        return pump_commands

    def run_backtest(self, start_index: int = 100, num_steps: int = 96):
        """
        Run backtest on historical data

        Args:
            start_index: Starting timestep
            num_steps: Number of 15-min timesteps to simulate
        """
        print("\n" + "="*60)
        print("BACKTEST MODE - Historical Data Simulation")
        print("="*60)
        print(f"Running {num_steps} timesteps ({num_steps * 0.25:.1f} hours)")
        print()

        results = []

        for i in range(num_steps):
            idx = start_index + i

            if idx >= len(self.data):
                print("⚠️  Reached end of data")
                break

            # Create state
            price_col = 'Price_High' if self.price_scenario == 'high' else 'Price_Normal'

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
            pump_commands = self.run_decision_cycle(state)

            # Track results
            results.append({
                'timestamp': state.timestamp,
                'L1': state.L1,
                'F1': state.F1,
                'F2': state.F2,
                'price': state.electricity_price,
                'num_pumps_active': sum(1 for cmd in pump_commands if cmd.start),
                'decision_count': self.decision_count
            })

            # Brief pause (for display)
            time.sleep(0.5)

        # Summary
        print("\n" + "="*60)
        print("BACKTEST SUMMARY")
        print("="*60)
        print(f"Total decisions: {self.decision_count}")
        print(f"Duration: {num_steps * 0.25:.1f} hours ({num_steps * 0.25 / 24:.1f} days)")

        if results:
            df_results = pd.DataFrame(results)
            print(f"\nWater Level Statistics:")
            print(f"  Min L1: {df_results['L1'].min():.2f}m")
            print(f"  Max L1: {df_results['L1'].max():.2f}m")
            print(f"  Avg L1: {df_results['L1'].mean():.2f}m")
            print(f"\nAverage pumps active: {df_results['num_pumps_active'].mean():.1f}")

        print("\n✓ Backtest complete!")

        return results

    async def run_live(self, decision_interval_seconds: float = 15.0):
        """
        Run live with OPC UA server

        Args:
            decision_interval_seconds: Time between decisions (real-time seconds)
        """
        print("\n" + "="*60)
        print("LIVE MODE - OPC UA Control")
        print("="*60)
        print(f"Decision interval: {decision_interval_seconds}s")
        print("Press Ctrl+C to stop")
        print()

        if not self.opcua_client:
            await self.connect_opcua()

        if not self.opcua_client:
            print("❌ Cannot run live mode without OPC UA connection")
            return

        try:
            while True:
                # Read state from OPC UA
                state = await self.read_state_from_opcua()

                # Run decision cycle
                pump_commands = self.run_decision_cycle(state)

                # Write commands to OPC UA
                await self.write_commands_to_opcua(pump_commands)

                # Wait for next cycle
                await asyncio.sleep(decision_interval_seconds)

        except KeyboardInterrupt:
            print("\n\n⚠️  Stopped by user")
        except Exception as e:
            print(f"\n❌ Error in live mode: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Multi-Agent Wastewater Pumping System')
    parser.add_argument('--mode', choices=['backtest', 'live'], default='backtest',
                        help='Run mode: backtest (historical data) or live (OPC UA)')
    parser.add_argument('--price', choices=['normal', 'high'], default='normal',
                        help='Electricity price scenario')
    parser.add_argument('--opcua', type=str, default=None,
                        help='OPC UA server URL (e.g., opc.tcp://localhost:4840)')
    parser.add_argument('--steps', type=int, default=96,
                        help='Number of timesteps for backtest (default: 96 = 24 hours)')
    parser.add_argument('--start', type=int, default=500,
                        help='Starting index for backtest (default: 500)')

    args = parser.parse_args()

    # Get model path
    script_dir = Path(__file__).parent
    model_path = script_dir.parent / 'models' / 'inflow_lstm_model.pth'

    # Create controller
    controller = MultiAgentController(
        lstm_model_path=str(model_path),
        price_scenario=args.price,
        opcua_url=args.opcua
    )

    # Run
    if args.mode == 'backtest':
        controller.run_backtest(start_index=args.start, num_steps=args.steps)
    else:
        # Live mode requires async
        asyncio.run(controller.run_live())


if __name__ == "__main__":
    main()
