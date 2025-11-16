#!/usr/bin/env bash
set -e

# Detect project root as the folder where this script lives
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Arguments (with defaults)
# 1 = price scenario (normal/high)
# 2 = number of timesteps
# 3 = start index in dataset
PRICE="${1:-normal}"
STEPS="${2:-1538}"
START="${3:-0}"

echo "Running baseline evaluation..."
echo "  Price scenario: $PRICE"
echo "  Timesteps:      $STEPS"
echo "  Start index:    $START"
echo

python src/agents/baseline_evaluation.py \
  --price "$PRICE" \
  --steps "$STEPS" \
  --start "$START"