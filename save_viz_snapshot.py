"""
Save a single visualization snapshot
"""

import sys
from pathlib import Path

# Ensure we can import from src/simulation
sys.path.insert(0, str(Path(__file__).parent / 'src' / 'simulation'))

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

from data_loader import HSYDataLoader
from physics_simulator import TunnelSimulator, PumpCommand
from visualizer import WastewaterVisualizer


def main():
    """Run simulation and save a snapshot"""

    print("="*60)
    print("Generating Visualization Snapshot")
    print("="*60)
    print()

    print("Loading data...")
    loader = HSYDataLoader()
    loader.load_all_data()

    print("Creating simulator...")
    simulator = TunnelSimulator(loader, initial_L1=2.0)

    print("Creating visualizer...")
    viz = WastewaterVisualizer(figsize=(16, 10))

    print("\nRunning simulation for 50 timesteps...")

    for step in range(50):
        # Simple control strategy
        L1 = simulator.get_state().L1

        if L1 > 4.0:
            commands = [
                PumpCommand('2.2', start=True, frequency=50.0),
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

        if step % 10 == 0:
            print(f"  Step {step}: L1={state.L1:.2f}m, {len(state.active_pumps)} pumps active")

    # Save final snapshot
    output_path = Path(__file__).parent / 'visualization_snapshot.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')

    print(f"\n✓ Snapshot saved to: {output_path}")
    print(f"\nFinal state:")
    print(f"  Time: {state.timestamp.strftime('%Y-%m-%d %H:%M')}")
    print(f"  Water Level (L1): {state.L1:.2f}m")
    print(f"  Volume (V): {state.V:.0f}m³")
    print(f"  Inflow (F1): {state.F1:.0f}m³/15min")
    print(f"  Outflow (F2): {state.F2:.0f}m³/h")
    print(f"  Active pumps: {len(state.active_pumps)}")
    print(f"  Total cost: {state.total_energy_cost:.2f} EUR")
    print()
    print(f"✓ Open the PNG file to see the visualization!")


if __name__ == "__main__":
    main()
