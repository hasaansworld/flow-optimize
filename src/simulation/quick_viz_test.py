"""
Quick visualization test - saves snapshots
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

from data_loader import HSYDataLoader
from physics_simulator import TunnelSimulator, PumpCommand
from visualizer import WastewaterVisualizer


def main():
    """Run simulation and save snapshots"""

    print("Loading data...")
    loader = HSYDataLoader()
    loader.load_all_data()

    print("Creating simulator...")
    simulator = TunnelSimulator(loader, initial_L1=2.0)

    print("Creating visualizer...")
    viz = WastewaterVisualizer(figsize=(16, 10))

    # Run for a few timesteps and save snapshots
    timesteps_to_save = [0, 10, 50, 100, 150, 200]

    for step in range(201):
        # Simple control strategy
        L1 = simulator.get_state().L1

        if L1 > 6.0:
            commands = [
                PumpCommand('1.2', start=True, frequency=50.0),
                PumpCommand('1.4', start=True, frequency=50.0),
                PumpCommand('2.2', start=True, frequency=50.0),
                PumpCommand('2.3', start=True, frequency=50.0),
            ]
        elif L1 > 3.0:
            commands = [
                PumpCommand('2.2', start=True, frequency=49.0),
                PumpCommand('2.3', start=True, frequency=49.0),
            ]
        else:
            commands = [
                PumpCommand('2.2', start=True, frequency=48.0),
            ]

        # Step simulation
        state = simulator.step(commands)

        # Update visualization
        viz.update(state)

        # Save snapshot
        if step in timesteps_to_save:
            filename = f'../../visualization_step_{step:03d}.png'
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            print(f"✓ Saved snapshot: {filename}")
            print(f"  Time: {state.timestamp.strftime('%Y-%m-%d %H:%M')}")
            print(f"  L1: {state.L1:.2f}m, F1: {state.F1:.0f}m³/15min, F2: {state.F2:.0f}m³/h")
            print(f"  Active pumps: {len(state.active_pumps)}")
            print()

    print(f"\n✓ Simulation complete!")
    print(f"Check the project root for PNG snapshots.")


if __name__ == "__main__":
    main()
