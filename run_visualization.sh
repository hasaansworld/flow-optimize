#!/bin/bash

# Run Visualization
# Usage: ./run_visualization.sh

echo "=============================================="
echo "HSY Wastewater - Real-Time Visualization"
echo "=============================================="
echo ""
echo "Starting 2D cross-section visualization..."
echo "Running first 200 timesteps (~50 hours of data)"
echo ""
echo "Close the window to stop the simulation."
echo ""

# Activate virtual environment
source venv/bin/activate

# Run visualization
python src/simulation/visualizer.py
