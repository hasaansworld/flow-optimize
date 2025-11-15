"""
Test OPC UA Client
Connects to the simulation server and tests reading/writing
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'simulation'))

from asyncua import Client
import logging


class TestClient:
    """Simple OPC UA client for testing"""

    def __init__(self, url="opc.tcp://localhost:4840/hsy/wastewater/"):
        self.client = Client(url=url)
        self.logger = logging.getLogger(__name__)

    async def connect(self):
        """Connect to OPC UA server"""
        await self.client.connect()
        self.logger.info(f"✓ Connected to {self.client.server_url}")

    async def disconnect(self):
        """Disconnect from server"""
        await self.client.disconnect()
        self.logger.info("✓ Disconnected")

    async def test_read_sensors(self):
        """Test reading sensor values"""

        self.logger.info("\n=== Testing Sensor Reads ===")

        # Get namespace index
        nsidx = await self.client.get_namespace_index("http://hsy.fi/wastewater/blominmaki")

        # Read sensor values
        sensors = {
            'Water Level': f'ns={nsidx};i=2',  # These IDs will vary, use browse instead
            'Water Volume': f'ns={nsidx};i=3',
        }

        # Alternatively, browse the tree
        root = self.client.get_root_node()
        objects = await root.get_child(["0:Objects"])
        station = await objects.get_child([f"{nsidx}:BlominmakiStation"])
        sensors_folder = await station.get_child([f"{nsidx}:Sensors"])

        # Get all children
        sensor_nodes = await sensors_folder.get_children()

        print("\nAvailable sensors:")
        for node in sensor_nodes:
            name = await node.read_browse_name()
            value = await node.read_value()
            print(f"  {name.Name}: {value}")

    async def test_write_controls(self):
        """Test writing pump control commands"""

        self.logger.info("\n=== Testing Control Writes ===")

        # Get namespace index
        nsidx = await self.client.get_namespace_index("http://hsy.fi/wastewater/blominmaki")

        # Navigate to control nodes
        root = self.client.get_root_node()
        objects = await root.get_child(["0:Objects"])
        station = await objects.get_child([f"{nsidx}:BlominmakiStation"])
        control_folder = await station.get_child([f"{nsidx}:Control"])

        # Get pump control folder
        pump_control = await control_folder.get_child([f"{nsidx}:Pump_2_2"])

        # Read current values
        start_node = await pump_control.get_child([f"{nsidx}:Start"])
        freq_node = await pump_control.get_child([f"{nsidx}:SetFrequency"])

        current_start = await start_node.read_value()
        current_freq = await freq_node.read_value()

        print(f"\nPump 2.2 current state:")
        print(f"  Start: {current_start}")
        print(f"  Frequency: {current_freq} Hz")

        # Write new values
        print("\nWriting new values...")
        await start_node.write_value(True)
        await freq_node.write_value(48.5)

        # Read back
        new_start = await start_node.read_value()
        new_freq = await freq_node.read_value()

        print(f"Pump 2.2 new state:")
        print(f"  Start: {new_start}")
        print(f"  Frequency: {new_freq} Hz")

        # Wait a bit
        print("\nWaiting 3 seconds for simulation to update...")
        await asyncio.sleep(3)

        # Read pump status
        pumps_folder = await station.get_child([f"{nsidx}:Pumps"])
        pump_status = await pumps_folder.get_child([f"{nsidx}:Pump_2_2"])

        flow_node = await pump_status.get_child([f"{nsidx}:Flow"])
        power_node = await pump_status.get_child([f"{nsidx}:Power"])
        eff_node = await pump_status.get_child([f"{nsidx}:Efficiency"])

        flow = await flow_node.read_value()
        power = await power_node.read_value()
        eff = await eff_node.read_value()

        print(f"\nPump 2.2 performance:")
        print(f"  Flow: {flow:.0f} m³/h")
        print(f"  Power: {power:.1f} kW")
        print(f"  Efficiency: {eff:.1f}%")

    async def monitor_system(self, duration_seconds=30):
        """Monitor system for a period of time"""

        self.logger.info(f"\n=== Monitoring System for {duration_seconds} seconds ===")

        # Get namespace index
        nsidx = await self.client.get_namespace_index("http://hsy.fi/wastewater/blominmaki")

        # Navigate to nodes
        root = self.client.get_root_node()
        objects = await root.get_child(["0:Objects"])
        station = await objects.get_child([f"{nsidx}:BlominmakiStation"])
        sensors_folder = await station.get_child([f"{nsidx}:Sensors"])
        status_folder = await station.get_child([f"{nsidx}:Status"])

        # Get sensor nodes
        L1_node = await sensors_folder.get_child([f"{nsidx}:WaterLevel_L1"])
        F1_node = await sensors_folder.get_child([f"{nsidx}:Inflow_F1"])
        F2_node = await sensors_folder.get_child([f"{nsidx}:Outflow_F2"])
        price_node = await sensors_folder.get_child([f"{nsidx}:ElectricityPrice"])

        # Get status nodes
        cost_node = await status_folder.get_child([f"{nsidx}:TotalEnergyCost"])
        time_node = await status_folder.get_child([f"{nsidx}:SimulationTime"])

        # Monitor loop
        start_time = asyncio.get_event_loop().time()
        while (asyncio.get_event_loop().time() - start_time) < duration_seconds:
            L1 = await L1_node.read_value()
            F1 = await F1_node.read_value()
            F2 = await F2_node.read_value()
            price = await price_node.read_value()
            cost = await cost_node.read_value()
            sim_time = await time_node.read_value()

            print(f"[{sim_time}] L1={L1:.2f}m, F1={F1:.0f}m³/15min, F2={F2:.0f}m³/h, "
                  f"Price={price:.3f}EUR/kWh, Cost={cost:.2f}EUR")

            await asyncio.sleep(2)


async def main():
    """Run tests"""

    logging.basicConfig(level=logging.INFO)

    client = TestClient()

    try:
        # Connect
        await client.connect()

        # Test reading sensors
        await client.test_read_sensors()

        # Test writing controls
        await client.test_write_controls()

        # Monitor for a bit
        await client.monitor_system(duration_seconds=30)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Disconnect
        await client.disconnect()


if __name__ == "__main__":
    print("="*60)
    print("OPC UA Test Client")
    print("="*60)
    print("\nMake sure the OPC UA server is running first!")
    print("Start it with: python src/simulation/opcua_server.py")
    print()

    asyncio.run(main())
