#!/bin/bash
# Run evaluation with output to both console and file

# Default parameters
PRICE_SCENARIO=${1:-normal}
NUM_STEPS=${2:-10}
START_INDEX=${3:-500}

# Output file
OUTPUT_FILE="evaluation_output_${PRICE_SCENARIO}_${NUM_STEPS}steps.txt"

echo "============================================================"
echo "Running Multi-Agent Evaluation"
echo "============================================================"
echo "Price Scenario: $PRICE_SCENARIO"
echo "Number of Steps: $NUM_STEPS"
echo "Start Index: $START_INDEX"
echo "Output File: $OUTPUT_FILE"
echo ""
echo "Starting evaluation... (output will be shown below and saved to file)"
echo "============================================================"
echo ""

# Activate virtual environment and run
source venv/bin/activate
python -u src/agents/run_evaluation.py \
    --price "$PRICE_SCENARIO" \
    --steps "$NUM_STEPS" \
    --start "$START_INDEX" \
    2>&1 | tee "$OUTPUT_FILE"

# Check exit status
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "✅ Evaluation completed successfully!"
    echo "📁 Full output saved to: $OUTPUT_FILE"
    echo "============================================================"
else
    echo ""
    echo "============================================================"
    echo "❌ Evaluation failed with exit code ${PIPESTATUS[0]}"
    echo "============================================================"
fi
