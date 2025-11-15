"""
OPC UA Connected Visualizer
Connects to running OPC UA server and visualizes in real-time
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from asyncua import Client
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from visualizer import WastewaterVisualizer
from physics_simulator import SystemState
from datetime import datetime


class OPCUAVisualizer:
    """
    Connects to OPC UA server and displays real-time visualization
    """

    def __init__(self, url="opc.tcp://localhost:4840/hsy/wastewater/"):
        self.url = url
        self.client = Client(url=url)
        self.viz = WastewaterVisualizer()
        self.running = True
        self.nsidx = None

        # Node references
        self.nodes = {}

    async def connect(self):
        """Connect to OPC UA server"""
        await self.client.connect()
        print(f"✓ Connected to OPC UA server: {self.url}")

        # Get namespace index
        self.nsidx = await self.client.get_namespace_index("http://hsy.fi/wastewater/blominmaki")

        # Get node references
        await self._get_node_references()

    async def _get_node_references(self):
        """Get references to OPC UA nodes"""

        root = self.client.get_root_node()
        objects = await root.get_child(["0:Objects"])
        station = await objects.get_child([f"{self.nsidx}:BlominmakiStation"])

        # Sensors
        sensors_folder = await station.get_child([f"{self.nsidx}:Sensors"])
        self.nodes['L1'] = await sensors_folder.get_child([f"{self.nsidx}:WaterLevel_L1"])
        self.nodes['V'] = await sensors_folder.get_child([f"{self.nsidx}:WaterVolume_V"])
        self.nodes['F1'] = await sensors_folder.get_child([f"{self.nsidx}:Inflow_F1"])
        self.nodes['F2'] = await sensors_folder.get_child([f"{self.nsidx}:Outflow_F2"])
        self.nodes['Price'] = await sensors_folder.get_child([f"{self.nsidx}:ElectricityPrice"])
        self.nodes['Timestamp'] = await sensors_folder.get_child([f"{self.nsidx}:Timestamp"])

        # Status
        status_folder = await station.get_child([f"{self.nsidx}:Status"])
        self.nodes['TotalCost'] = await status_folder.get_child([f"{self.nsidx}:TotalEnergyCost"])
        self.nodes['TotalEnergy'] = await status_folder.get_child([f"{self.nsidx}:TotalEnergyKWh"])

        # Pumps
        pumps_folder = await station.get_child([f"{self.nsidx}:Pumps"])
        pump_ids = ['1_1', '1_2', '1_3', '1_4', '2_1', '2_2', '2_3', '2_4']

        self.nodes['pumps'] = {}
        for pump_id in pump_ids:
            pump_folder = await pumps_folder.get_child([f"{self.nsidx}:Pump_{pump_id}"])
            self.nodes['pumps'][pump_id] = {
                'running': await pump_folder.get_child([f"{self.nsidx}:IsRunning"]),
                'flow': await pump_folder.get_child([f"{self.nsidx}:Flow"]),
                'power': await pump_folder.get_child([f"{self.nsidx}:Power"]),
                'efficiency': await pump_folder.get_child([f"{self.nsidx}:Efficiency"]),
                'frequency': await pump_folder.get_child([f"{self.nsidx}:Frequency"]),
            }

        print("✓ Got all node references")

    async def read_state(self) -> SystemState:
        """Read current state from OPC UA server"""

        # Read sensor values
        L1 = await self.nodes['L1'].read_value()
        V = await self.nodes['V'].read_value()
        F1 = await self.nodes['F1'].read_value()
        F2 = await self.nodes['F2'].read_value()
        price = await self.nodes['Price'].read_value()
        timestamp = await self.nodes['Timestamp'].read_value()
        total_cost = await self.nodes['TotalCost'].read_value()
        total_energy = await self.nodes['TotalEnergy'].read_value()

        # Read pump states
        active_pumps = {}
        for pump_id_underscore, pump_nodes in self.nodes['pumps'].items():
            is_running = await pump_nodes['running'].read_value()

            if is_running:
                pump_id = pump_id_underscore.replace('_', '.')
                active_pumps[pump_id] = {
                    'running': True,
                    'flow_m3h': await pump_nodes['flow'].read_value(),
                    'power_kw': await pump_nodes['power'].read_value(),
                    'efficiency': await pump_nodes['efficiency'].read_value() / 100.0,
                    'frequency': await pump_nodes['frequency'].read_value()
                }

        # Create state object
        state = SystemState(
            timestamp=timestamp if isinstance(timestamp, datetime) else datetime.now(),
            L1=L1,
            V=V,
            F1=F1,
            F2=F2,
            electricity_price=price,
            active_pumps=active_pumps,
            total_energy_cost=total_cost,
            total_energy_kwh=total_energy,
            violations=[]
        )

        return state

    async def update_loop(self):
        """Async update loop"""

        while self.running:
            try:
                # Read state from OPC UA
                state = await self.read_state()

                # Update visualization
                self.viz.update(state)

                # Redraw
                self.viz.fig.canvas.draw_idle()
                self.viz.fig.canvas.flush_events()

                # Wait a bit
                await asyncio.sleep(0.5)  # Update twice per second

            except Exception as e:
                print(f"Error in update loop: {e}")
                self.running = False
                break

    async def disconnect(self):
        """Disconnect from server"""
        await self.client.disconnect()
        print("✓ Disconnected from OPC UA server")

    async def run(self):
        """Run the visualizer"""

        try:
            await self.connect()

            # Show visualization in non-blocking mode
            plt.ion()
            plt.show()

            # Run update loop
            await self.update_loop()

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

        finally:
            await self.disconnect()


async def main():
    """Main entry point"""

    print("="*60)
    print("OPC UA Real-Time Visualizer")
    print("="*60)
    print()
    print("Connecting to OPC UA server...")
    print("Make sure the server is running: python src/simulation/opcua_server.py")
    print()

    visualizer = OPCUAVisualizer()

    try:
        await visualizer.run()
    except KeyboardInterrupt:
        print("\n✓ Stopped by user")


if __name__ == "__main__":
    asyncio.run(main())
