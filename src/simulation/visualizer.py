"""
Real-Time 2D Visualization for Wastewater Pumping Station
Shows cross-section view, pump status, and system metrics
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
import numpy as np
from datetime import datetime
from typing import Optional
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from data_loader import HSYDataLoader
from physics_simulator import TunnelSimulator, PumpCommand, SystemState


class WastewaterVisualizer:
    """
    Real-time 2D visualization of the wastewater pumping system
    Shows cross-sectional view with tunnel, pumps, and water level
    """

    def __init__(self, figsize=(16, 10)):
        """Initialize visualizer"""

        self.figsize = figsize

        # Create figure with subplots
        self.fig = plt.figure(figsize=figsize)
        self.fig.suptitle('HSY Blominmäki Wastewater Pumping Station - Real-Time Monitoring',
                         fontsize=16, fontweight='bold')

        # Create grid layout
        gs = self.fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

        # Main cross-section view (top, spanning 2 columns)
        self.ax_cross = self.fig.add_subplot(gs[0:2, :])

        # Metrics panels (bottom row)
        self.ax_level = self.fig.add_subplot(gs[2, 0])
        self.ax_flow = self.fig.add_subplot(gs[2, 1])
        self.ax_cost = self.fig.add_subplot(gs[2, 2])

        # System dimensions (in meters)
        self.tunnel_length = 100  # Visual length
        self.tunnel_height = 15   # Max level ~14m
        self.tunnel_ground = 0    # Ground level reference
        self.wwtp_level = 30      # WWTP elevation

        # Data storage for time series
        self.history_size = 100
        self.time_history = []
        self.L1_history = []
        self.F1_history = []
        self.F2_history = []
        self.cost_history = []
        self.price_history = []

        # Current state
        self.current_state = None

        # Initialize plots
        self._setup_cross_section()
        self._setup_metrics()

    def _setup_cross_section(self):
        """Setup the cross-sectional view"""

        ax = self.ax_cross
        ax.set_xlim(-10, 120)
        ax.set_ylim(-5, 40)
        ax.set_aspect('equal')
        ax.set_xlabel('Distance (m)', fontsize=10)
        ax.set_ylabel('Elevation (m)', fontsize=10)
        ax.set_title('System Cross-Section', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)

        # Draw ground
        ground = patches.Rectangle((0, -5), 120, 5,
                                   linewidth=0, facecolor='#8B7355',
                                   label='Ground')
        ax.add_patch(ground)

        # Draw tunnel structure (concrete walls)
        tunnel_bottom = patches.Rectangle((0, self.tunnel_ground),
                                         self.tunnel_length, 0.5,
                                         linewidth=2, edgecolor='black',
                                         facecolor='#696969',
                                         label='Tunnel')
        ax.add_patch(tunnel_bottom)

        # Tunnel side walls
        left_wall = patches.Rectangle((0, self.tunnel_ground), 0.5,
                                     self.tunnel_height,
                                     linewidth=2, edgecolor='black',
                                     facecolor='#696969')
        ax.add_patch(left_wall)

        right_wall = patches.Rectangle((self.tunnel_length - 0.5, self.tunnel_ground),
                                      0.5, self.tunnel_height,
                                      linewidth=2, edgecolor='black',
                                      facecolor='#696969')
        ax.add_patch(right_wall)

        # Water (will be updated)
        self.water_patch = patches.Rectangle((0.5, self.tunnel_ground + 0.5),
                                            self.tunnel_length - 1, 0,
                                            linewidth=0, facecolor='#1E90FF',
                                            alpha=0.7, label='Water')
        ax.add_patch(self.water_patch)

        # Water level line (will be updated)
        self.water_line, = ax.plot([0, self.tunnel_length], [0, 0],
                                   'b-', linewidth=2, label='Water Level')

        # Level markers
        for level in [0, 2, 4, 6, 7.2, 8, 10, 12, 14]:
            ax.axhline(y=level, color='gray', linestyle='--', alpha=0.3, linewidth=0.5)
            ax.text(-2, level, f'{level}m', fontsize=8, va='center')

        # Alarm level marker
        ax.axhline(y=7.2, color='red', linestyle='--', alpha=0.5, linewidth=1.5)
        ax.text(-2, 7.2, '7.2m ALARM', fontsize=8, va='center',
               color='red', fontweight='bold')

        # Max level marker
        ax.axhline(y=8.0, color='darkred', linestyle='-', alpha=0.7, linewidth=2)
        ax.text(-2, 8.0, '8.0m MAX', fontsize=8, va='center',
               color='darkred', fontweight='bold')

        # Draw WWTP (elevated tank)
        wwtp_x = 105
        wwtp = patches.Rectangle((wwtp_x, self.wwtp_level - 5), 10, 8,
                                 linewidth=2, edgecolor='black',
                                 facecolor='#87CEEB',
                                 label='WWTP')
        ax.add_patch(wwtp)
        ax.text(wwtp_x + 5, self.wwtp_level, 'WWTP\n30m',
               fontsize=10, ha='center', va='center', fontweight='bold')

        # Draw pumps (along the right side of tunnel)
        self.pump_patches = {}
        pump_x = self.tunnel_length + 2
        pump_y_start = 5
        pump_spacing = 3

        pump_ids = ['1.1', '1.2', '1.3', '1.4', '2.1', '2.2', '2.3', '2.4']

        for i, pump_id in enumerate(pump_ids):
            y_pos = pump_y_start + i * pump_spacing

            # Pump body (rectangle)
            pump_rect = patches.Rectangle((pump_x, y_pos), 3, 2,
                                         linewidth=2, edgecolor='black',
                                         facecolor='gray',
                                         alpha=0.5)
            ax.add_patch(pump_rect)

            # Pump label
            ax.text(pump_x + 1.5, y_pos + 1, f'P{pump_id}',
                   fontsize=8, ha='center', va='center',
                   fontweight='bold')

            # Store reference
            self.pump_patches[pump_id] = pump_rect

            # Draw pipe to WWTP (thin line)
            ax.plot([pump_x + 3, wwtp_x], [y_pos + 1, self.wwtp_level],
                   'k-', linewidth=1, alpha=0.3)

        # Inflow arrow (will be updated)
        self.inflow_arrow = ax.arrow(0, self.tunnel_height + 2, 5, -3,
                                    head_width=1, head_length=1,
                                    fc='blue', ec='blue', alpha=0.7,
                                    linewidth=2)

        # Text annotations (will be updated)
        self.level_text = ax.text(50, self.tunnel_height + 3, '',
                                 fontsize=12, ha='center',
                                 bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        self.inflow_text = ax.text(10, self.tunnel_height + 3, '',
                                  fontsize=10, ha='left',
                                  bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))

        self.outflow_text = ax.text(pump_x + 1.5, 2, '',
                                   fontsize=10, ha='center',
                                   bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))

    def _setup_metrics(self):
        """Setup metric panels"""

        # Level history
        self.ax_level.set_title('Water Level History', fontsize=10, fontweight='bold')
        self.ax_level.set_xlabel('Time Steps', fontsize=8)
        self.ax_level.set_ylabel('Level (m)', fontsize=8)
        self.ax_level.grid(True, alpha=0.3)
        self.ax_level.axhline(y=7.2, color='red', linestyle='--', alpha=0.5, label='Alarm')
        self.ax_level.axhline(y=8.0, color='darkred', linestyle='-', alpha=0.7, label='Max')
        self.level_line, = self.ax_level.plot([], [], 'b-', linewidth=2)
        self.ax_level.legend(fontsize=8)

        # Flow history
        self.ax_flow.set_title('Flow Rates', fontsize=10, fontweight='bold')
        self.ax_flow.set_xlabel('Time Steps', fontsize=8)
        self.ax_flow.set_ylabel('Flow (m³/h or m³/15min)', fontsize=8)
        self.ax_flow.grid(True, alpha=0.3)
        self.F1_line, = self.ax_flow.plot([], [], 'b-', linewidth=2, label='Inflow F1')
        self.F2_line, = self.ax_flow.plot([], [], 'g-', linewidth=2, label='Outflow F2')
        self.ax_flow.legend(fontsize=8)

        # Cost and price
        self.ax_cost.set_title('Energy Cost & Price', fontsize=10, fontweight='bold')
        self.ax_cost.set_xlabel('Time Steps', fontsize=8)
        self.ax_cost.set_ylabel('EUR', fontsize=8)
        self.ax_cost.grid(True, alpha=0.3)
        self.ax_cost_twin = self.ax_cost.twinx()
        self.ax_cost_twin.set_ylabel('EUR/kWh', fontsize=8)
        self.cost_line, = self.ax_cost.plot([], [], 'r-', linewidth=2, label='Total Cost')
        self.price_line, = self.ax_cost_twin.plot([], [], 'orange', linewidth=2,
                                                  linestyle='--', label='Price')

        # Combine legends
        lines1, labels1 = self.ax_cost.get_legend_handles_labels()
        lines2, labels2 = self.ax_cost_twin.get_legend_handles_labels()
        self.ax_cost.legend(lines1 + lines2, labels1 + labels2, fontsize=8)

    def update(self, state: SystemState):
        """Update visualization with new state"""

        self.current_state = state

        # Update water level
        L1 = state.L1
        water_height = max(0, L1 - self.tunnel_ground)

        self.water_patch.set_height(water_height)
        self.water_line.set_ydata([L1, L1])

        # Update water color based on alarm status
        if L1 > 8.0:
            self.water_patch.set_facecolor('#8B0000')  # Dark red
        elif L1 > 7.2:
            self.water_patch.set_facecolor('#FF6347')  # Tomato red
        else:
            self.water_patch.set_facecolor('#1E90FF')  # Dodger blue

        # Update pump colors based on status
        for pump_id, pump_patch in self.pump_patches.items():
            if pump_id in state.active_pumps:
                # Green if running
                pump_patch.set_facecolor('#00FF00')
                pump_patch.set_alpha(0.9)
            else:
                # Gray if off
                pump_patch.set_facecolor('gray')
                pump_patch.set_alpha(0.5)

        # Update text annotations
        self.level_text.set_text(f'L1 = {L1:.2f} m\nV = {state.V:.0f} m³')
        self.inflow_text.set_text(f'Inflow\n{state.F1:.0f} m³/15min')
        self.outflow_text.set_text(f'Outflow\n{state.F2:.0f} m³/h')

        # Update history
        self.time_history.append(len(self.time_history))
        self.L1_history.append(L1)
        self.F1_history.append(state.F1)
        self.F2_history.append(state.F2 / 4)  # Convert to m³/15min for comparison
        self.cost_history.append(state.total_energy_cost)
        self.price_history.append(state.electricity_price)

        # Keep only recent history
        if len(self.time_history) > self.history_size:
            self.time_history.pop(0)
            self.L1_history.pop(0)
            self.F1_history.pop(0)
            self.F2_history.pop(0)
            self.cost_history.pop(0)
            self.price_history.pop(0)

        # Update time series plots
        self.level_line.set_data(self.time_history, self.L1_history)
        self.F1_line.set_data(self.time_history, self.F1_history)
        self.F2_line.set_data(self.time_history, self.F2_history)
        self.cost_line.set_data(self.time_history, self.cost_history)
        self.price_line.set_data(self.time_history, self.price_history)

        # Auto-scale axes
        if len(self.time_history) > 1:
            self.ax_level.set_xlim(min(self.time_history), max(self.time_history))
            self.ax_level.set_ylim(0, max(max(self.L1_history) + 1, 8.5))

            self.ax_flow.set_xlim(min(self.time_history), max(self.time_history))
            self.ax_flow.set_ylim(0, max(max(self.F1_history), max(self.F2_history)) * 1.1)

            self.ax_cost.set_xlim(min(self.time_history), max(self.time_history))
            self.ax_cost.set_ylim(0, max(self.cost_history) * 1.1)
            self.ax_cost_twin.set_ylim(0, max(self.price_history) * 1.2)

        # Update title with timestamp
        self.fig.suptitle(
            f'HSY Blominmäki Wastewater Pumping Station - {state.timestamp.strftime("%Y-%m-%d %H:%M:%S")}',
            fontsize=16, fontweight='bold'
        )

        return [self.water_patch, self.water_line, self.level_text,
                self.inflow_text, self.outflow_text]

    def show(self):
        """Display the visualization"""
        plt.tight_layout()
        plt.show()


class SimulationVisualizer:
    """
    Runs simulation with real-time visualization
    """

    def __init__(self, simulator: TunnelSimulator, interval_ms: int = 100):
        """
        Args:
            simulator: TunnelSimulator instance
            interval_ms: Update interval in milliseconds
        """
        self.simulator = simulator
        self.interval_ms = interval_ms
        self.viz = WastewaterVisualizer()
        self.running = True

    def control_strategy(self, state: SystemState) -> list:
        """
        Define pump control strategy
        Override this method for different strategies

        Args:
            state: Current system state

        Returns:
            List of PumpCommand
        """

        # Simple baseline strategy: Run 2-3 large pumps to maintain level
        commands = []

        L1 = state.L1

        if L1 > 6.0:
            # High level - run 4 pumps
            commands = [
                PumpCommand('1.2', start=True, frequency=50.0),
                PumpCommand('1.4', start=True, frequency=50.0),
                PumpCommand('2.2', start=True, frequency=50.0),
                PumpCommand('2.3', start=True, frequency=50.0),
            ]
        elif L1 > 3.0:
            # Medium level - run 2-3 pumps
            commands = [
                PumpCommand('2.2', start=True, frequency=49.0),
                PumpCommand('2.3', start=True, frequency=49.0),
            ]
        elif L1 > 1.0:
            # Low level - run 2 pumps at lower frequency
            commands = [
                PumpCommand('2.2', start=True, frequency=48.0),
                PumpCommand('2.3', start=True, frequency=48.0),
            ]
        else:
            # Very low - run 1 pump minimum
            commands = [
                PumpCommand('2.1', start=True, frequency=47.5),
            ]

        return commands

    def step(self, frame):
        """Animation step function"""

        if not self.running:
            return []

        # Get current state
        state = self.simulator.get_state()

        # Determine control commands
        pump_commands = self.control_strategy(state)

        # Step simulator
        new_state = self.simulator.step(pump_commands)

        # Update visualization
        artists = self.viz.update(new_state)

        # Check if simulation complete
        if self.simulator.historical_index >= len(self.simulator.historical_data) - 1:
            print("\n✓ Simulation complete!")
            self.running = False

        return artists

    def run(self, max_steps: Optional[int] = None):
        """
        Run simulation with visualization

        Args:
            max_steps: Maximum number of steps (None = run all data)
        """

        print("Starting simulation visualization...")
        print("Close the window to stop.")

        # Create animation
        anim = FuncAnimation(
            self.viz.fig,
            self.step,
            interval=self.interval_ms,
            blit=False,
            repeat=False,
            frames=max_steps
        )

        # Show
        plt.show()

        # Print final stats
        final_state = self.simulator.get_state()
        print(f"\n=== Simulation Summary ===")
        print(f"Duration: {self.simulator.historical_index} timesteps")
        print(f"Final L1: {final_state.L1:.2f}m")
        print(f"Total Cost: {final_state.total_energy_cost:.2f} EUR")
        print(f"Total Energy: {final_state.total_energy_kwh:.0f} kWh")
        print(f"Total Violations: {self.simulator.total_violations}")
        print(f"Alarm Count: {self.simulator.alarm_count}")


def main():
    """Test the visualizer"""

    print("Loading data...")
    loader = HSYDataLoader()
    loader.load_all_data()

    print("Creating simulator...")
    simulator = TunnelSimulator(loader, initial_L1=2.0)

    print("Starting visualization...")
    print("This will run through the 15-day dataset with visualization")
    print("Update interval: 100ms per timestep")
    print()

    # Create visualizer with simulation
    sim_viz = SimulationVisualizer(simulator, interval_ms=100)

    # Run simulation
    sim_viz.run(max_steps=200)  # Run first 200 steps (~50 hours)


if __name__ == "__main__":
    main()
