#!/bin/bash

# Run OPC UA Simulation Server
# Usage: ./run_simulation.sh

echo "=============================================="
echo "HSY Wastewater Pumping - OPC UA Simulation"
echo "=============================================="
echo ""

# Activate virtual environment
source venv/bin/activate

# Run server
python src/simulation/opcua_server.py
