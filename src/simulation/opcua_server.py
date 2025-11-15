"""
OPC UA Server for Wastewater Pumping Station Simulation
Exposes sensor data and control nodes for multi-agent system
"""

import asyncio
from asyncua import Server, ua
from datetime import datetime
from typing import Dict
import logging

from data_loader import HSYDataLoader
from physics_simulator import TunnelSimulator, PumpCommand
from pump_models import PumpModel


class WastewaterOPCUAServer:
    """
    OPC UA Server that wraps the physics simulator
    Provides industrial-standard interface for agent control
    """

    def __init__(
        self,
        endpoint: str = "opc.tcp://0.0.0.0:4840/hsy/wastewater/",
        simulation_speedup: float = 1.0
    ):
        """
        Initialize OPC UA server

        Args:
            endpoint: OPC UA endpoint URL
            simulation_speedup: Speedup factor (1.0 = real-time, 900 = 15min in 1sec)
        """

        self.endpoint = endpoint
        self.simulation_speedup = simulation_speedup

        self.server = Server()
        self.idx = None  # Namespace index

        # Simulation components
        self.data_loader = None
        self.simulator = None
        self.pump_model = PumpModel()

        # OPC UA node references
        self.sensor_nodes = {}
        self.pump_nodes = {}
        self.control_nodes = {}
        self.status_nodes = {}

        # Simulation state
        self.is_running = False

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    async def init(self):
        """Initialize OPC UA server structure"""

        self.logger.info("Initializing OPC UA Server...")

        # Server setup
        await self.server.init()
        self.server.set_endpoint(self.endpoint)
        self.server.set_server_name("HSY Blominmäki Wastewater Pumping Station")

        # Setup namespace
        uri = "http://hsy.fi/wastewater/blominmaki"
        self.idx = await self.server.register_namespace(uri)

        # Get objects node
        objects = self.server.get_objects_node()

        # Create main station object
        self.station = await objects.add_object(self.idx, "BlominmakiStation")

        # Create folder structure
        await self._create_sensor_nodes()
        await self._create_pump_nodes()
        await self._create_control_nodes()
        await self._create_status_nodes()

        self.logger.info(f"✓ OPC UA Server initialized at {self.endpoint}")
        self.logger.info(f"  Namespace: {uri}")
        self.logger.info(f"  Simulation speedup: {self.simulation_speedup}x")

    async def _create_sensor_nodes(self):
        """Create sensor data nodes (read-only)"""

        sensors_folder = await self.station.add_folder(self.idx, "Sensors")

        # Water level and volume
        self.sensor_nodes['L1'] = await sensors_folder.add_variable(
            self.idx, "WaterLevel_L1", 0.0
        )
        await self.sensor_nodes['L1'].set_writable(False)
        await self.sensor_nodes['L1'].set_attr(ua.AttributeIds.Description,
                                                ua.DataValue(ua.Variant("Water level in tunnel (m)", ua.VariantType.String)))

        self.sensor_nodes['V'] = await sensors_folder.add_variable(
            self.idx, "WaterVolume_V", 0.0
        )
        await self.sensor_nodes['V'].set_writable(False)
        await self.sensor_nodes['V'].set_attr(ua.AttributeIds.Description,
                                               ua.DataValue(ua.Variant("Water volume in tunnel (m³)", ua.VariantType.String)))

        # Flows
        self.sensor_nodes['F1'] = await sensors_folder.add_variable(
            self.idx, "Inflow_F1", 0.0
        )
        await self.sensor_nodes['F1'].set_writable(False)
        await self.sensor_nodes['F1'].set_attr(ua.AttributeIds.Description,
                                                ua.DataValue(ua.Variant("Inflow to tunnel (m³/15min)", ua.VariantType.String)))

        self.sensor_nodes['F2'] = await sensors_folder.add_variable(
            self.idx, "Outflow_F2", 0.0
        )
        await self.sensor_nodes['F2'].set_writable(False)
        await self.sensor_nodes['F2'].set_attr(ua.AttributeIds.Description,
                                                ua.DataValue(ua.Variant("Total pumped flow to WWTP (m³/h)", ua.VariantType.String)))

        # Price and time
        self.sensor_nodes['Price'] = await sensors_folder.add_variable(
            self.idx, "ElectricityPrice", 0.0
        )
        await self.sensor_nodes['Price'].set_writable(False)
        await self.sensor_nodes['Price'].set_attr(ua.AttributeIds.Description,
                                                   ua.DataValue(ua.Variant("Electricity price (EUR/kWh)", ua.VariantType.String)))

        self.sensor_nodes['Timestamp'] = await sensors_folder.add_variable(
            self.idx, "Timestamp", datetime.now()
        )
        await self.sensor_nodes['Timestamp'].set_writable(False)

        self.logger.info("✓ Created sensor nodes")

    async def _create_pump_nodes(self):
        """Create pump status nodes (read-only)"""

        pumps_folder = await self.station.add_folder(self.idx, "Pumps")

        pump_ids = self.pump_model.get_all_pump_ids()

        for pump_id in pump_ids:
            pump_name = f"Pump_{pump_id.replace('.', '_')}"
            pump_folder = await pumps_folder.add_folder(self.idx, pump_name)

            self.pump_nodes[pump_id] = {}

            # Flow
            self.pump_nodes[pump_id]['Flow'] = await pump_folder.add_variable(
                self.idx, "Flow", 0.0
            )
            await self.pump_nodes[pump_id]['Flow'].set_writable(False)

            # Power
            self.pump_nodes[pump_id]['Power'] = await pump_folder.add_variable(
                self.idx, "Power", 0.0
            )
            await self.pump_nodes[pump_id]['Power'].set_writable(False)

            # Efficiency
            self.pump_nodes[pump_id]['Efficiency'] = await pump_folder.add_variable(
                self.idx, "Efficiency", 0.0
            )
            await self.pump_nodes[pump_id]['Efficiency'].set_writable(False)

            # Frequency
            self.pump_nodes[pump_id]['Frequency'] = await pump_folder.add_variable(
                self.idx, "Frequency", 0.0
            )
            await self.pump_nodes[pump_id]['Frequency'].set_writable(False)

            # Running status
            self.pump_nodes[pump_id]['IsRunning'] = await pump_folder.add_variable(
                self.idx, "IsRunning", False
            )
            await self.pump_nodes[pump_id]['IsRunning'].set_writable(False)

        self.logger.info(f"✓ Created pump nodes for {len(pump_ids)} pumps")

    async def _create_control_nodes(self):
        """Create control command nodes (writable by agents)"""

        control_folder = await self.station.add_folder(self.idx, "Control")

        pump_ids = self.pump_model.get_all_pump_ids()

        for pump_id in pump_ids:
            pump_name = f"Pump_{pump_id.replace('.', '_')}"
            pump_control = await control_folder.add_folder(self.idx, pump_name)

            self.control_nodes[pump_id] = {}

            # Start command
            self.control_nodes[pump_id]['Start'] = await pump_control.add_variable(
                self.idx, "Start", False
            )
            await self.control_nodes[pump_id]['Start'].set_writable(True)

            # Frequency setpoint
            self.control_nodes[pump_id]['SetFrequency'] = await pump_control.add_variable(
                self.idx, "SetFrequency", 50.0
            )
            await self.control_nodes[pump_id]['SetFrequency'].set_writable(True)

        self.logger.info(f"✓ Created control nodes for {len(pump_ids)} pumps")

    async def _create_status_nodes(self):
        """Create system status nodes"""

        status_folder = await self.station.add_folder(self.idx, "Status")

        # Violations and alarms
        self.status_nodes['ConstraintsViolated'] = await status_folder.add_variable(
            self.idx, "ConstraintsViolated", False
        )
        await self.status_nodes['ConstraintsViolated'].set_writable(False)

        self.status_nodes['AlarmLevel'] = await status_folder.add_variable(
            self.idx, "AlarmLevel", False
        )
        await self.status_nodes['AlarmLevel'].set_writable(False)

        # Energy tracking
        self.status_nodes['TotalEnergyCost'] = await status_folder.add_variable(
            self.idx, "TotalEnergyCost", 0.0
        )
        await self.status_nodes['TotalEnergyCost'].set_writable(False)

        self.status_nodes['TotalEnergyKWh'] = await status_folder.add_variable(
            self.idx, "TotalEnergyKWh", 0.0
        )
        await self.status_nodes['TotalEnergyKWh'].set_writable(False)

        # Simulation control
        self.status_nodes['SimulationTime'] = await status_folder.add_variable(
            self.idx, "SimulationTime", ""
        )
        await self.status_nodes['SimulationTime'].set_writable(False)

        self.logger.info("✓ Created status nodes")

    async def load_simulation_data(self):
        """Load historical data and initialize simulator"""

        self.logger.info("Loading simulation data...")

        self.data_loader = HSYDataLoader()
        self.data_loader.load_all_data()

        self.simulator = TunnelSimulator(
            self.data_loader,
            initial_L1=2.0,
            use_historical_inflow=True
        )

        self.logger.info("✓ Simulation data loaded")

    async def update_sensor_values(self):
        """Update sensor nodes with current simulation state"""

        state = self.simulator.get_state()

        await self.sensor_nodes['L1'].write_value(state.L1)
        await self.sensor_nodes['V'].write_value(state.V)
        await self.sensor_nodes['F1'].write_value(state.F1)
        await self.sensor_nodes['F2'].write_value(state.F2)
        await self.sensor_nodes['Price'].write_value(state.electricity_price)
        await self.sensor_nodes['Timestamp'].write_value(state.timestamp)

        # Update pump states
        for pump_id in self.pump_model.get_all_pump_ids():
            if pump_id in state.active_pumps:
                pump_data = state.active_pumps[pump_id]
                await self.pump_nodes[pump_id]['Flow'].write_value(pump_data['flow_m3h'])
                await self.pump_nodes[pump_id]['Power'].write_value(pump_data['power_kw'])
                await self.pump_nodes[pump_id]['Efficiency'].write_value(pump_data['efficiency'] * 100)
                await self.pump_nodes[pump_id]['Frequency'].write_value(pump_data['frequency'])
                await self.pump_nodes[pump_id]['IsRunning'].write_value(True)
            else:
                await self.pump_nodes[pump_id]['Flow'].write_value(0.0)
                await self.pump_nodes[pump_id]['Power'].write_value(0.0)
                await self.pump_nodes[pump_id]['Efficiency'].write_value(0.0)
                await self.pump_nodes[pump_id]['Frequency'].write_value(0.0)
                await self.pump_nodes[pump_id]['IsRunning'].write_value(False)

        # Update status
        await self.status_nodes['ConstraintsViolated'].write_value(len(state.violations) > 0)
        await self.status_nodes['AlarmLevel'].write_value(state.L1 > 7.2)
        await self.status_nodes['TotalEnergyCost'].write_value(state.total_energy_cost)
        await self.status_nodes['TotalEnergyKWh'].write_value(state.total_energy_kwh)
        await self.status_nodes['SimulationTime'].write_value(state.timestamp.strftime('%Y-%m-%d %H:%M:%S'))

    async def read_pump_commands(self) -> Dict[str, PumpCommand]:
        """Read pump control commands from OPC UA nodes"""

        commands = []

        for pump_id in self.pump_model.get_all_pump_ids():
            start = await self.control_nodes[pump_id]['Start'].read_value()
            frequency = await self.control_nodes[pump_id]['SetFrequency'].read_value()

            commands.append(PumpCommand(
                pump_id=pump_id,
                start=start,
                frequency=frequency
            ))

        return commands

    async def simulation_loop(self):
        """Main simulation loop - runs every 15 minutes (scaled by speedup)"""

        self.logger.info("Starting simulation loop...")
        self.is_running = True

        step_count = 0
        real_time_per_step = (15 * 60) / self.simulation_speedup  # seconds

        while self.is_running:
            # Read pump commands from control nodes
            pump_commands = await self.read_pump_commands()

            # Step simulation
            state = self.simulator.step(pump_commands)

            # Update sensor values
            await self.update_sensor_values()

            # Log progress
            if step_count % 10 == 0:
                self.logger.info(
                    f"Step {step_count}: {state.timestamp.strftime('%Y-%m-%d %H:%M')}, "
                    f"L1={state.L1:.2f}m, F1={state.F1:.0f}m³/15min, F2={state.F2:.0f}m³/h, "
                    f"Cost={state.total_energy_cost:.2f}EUR"
                )

            step_count += 1

            # Check if simulation complete
            if step_count >= len(self.data_loader.main_data) - 1:
                self.logger.info("Simulation complete - reached end of historical data")
                self.is_running = False
                break

            # Wait for next timestep (scaled by speedup)
            await asyncio.sleep(real_time_per_step)

        self.logger.info(f"✓ Simulation finished after {step_count} steps")

    async def start(self):
        """Start the OPC UA server"""

        async with self.server:
            self.logger.info(f"✓ OPC UA Server running at {self.endpoint}")
            self.logger.info("  Waiting for agent connections...")

            # Start simulation loop
            await self.simulation_loop()


async def main():
    """Main entry point"""

    # Create server with 900x speedup (15 min = 1 second)
    server = WastewaterOPCUAServer(
        endpoint="opc.tcp://0.0.0.0:4840/hsy/wastewater/",
        simulation_speedup=900.0  # 15 min in 1 second
    )

    # Initialize
    await server.init()

    # Load data
    await server.load_simulation_data()

    # Start server and simulation
    await server.start()


if __name__ == "__main__":
    print("="*60)
    print("HSY Blominmäki Wastewater Pumping Station - OPC UA Server")
    print("="*60)
    print()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✓ Server stopped by user")
