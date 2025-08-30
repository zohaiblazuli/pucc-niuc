#!/bin/bash
# Reproducible benchmarking script for PCC-NIUC I²-Bench-Lite
# Compares baseline (no gate) vs block vs rewrite modes
set -euo pipefail

echo "🔒 PCC-NIUC I²-Bench-Lite Reproducible Evaluation"
echo "=================================================="
echo "This script runs comprehensive benchmarks comparing:"
echo "  • Baseline (no gate) - unprotected model responses"
echo "  • Block mode - strict violation blocking"  
echo "  • Rewrite mode - neutralization with re-verification"
echo

# Configuration
SCENARIOS_FILE="bench/scenarios.jsonl"
RESULTS_DIR="results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S" 2>/dev/null || python -c "import time; print(time.strftime('%Y%m%d_%H%M%S'))")
MODEL_TYPE=${MODEL_TYPE:-"mock"}  # Can be overridden with env var

echo "📋 Configuration:"
echo "  Model type: $MODEL_TYPE"
echo "  Scenarios: $SCENARIOS_FILE" 
echo "  Results dir: $RESULTS_DIR"
echo "  Timestamp: $TIMESTAMP"
echo

# Check Python and environment
echo "🔧 Environment Check:"
python --version
echo "  Python: ✅"

# Clean previous results
echo "🧹 Cleaning previous results..."
rm -rf "$RESULTS_DIR" 2>/dev/null || true
mkdir -p "$RESULTS_DIR"
echo "  Results directory: ✅"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -e . > /dev/null 2>&1 || echo "  Warning: pip install had issues"
echo "  Dependencies: ✅"

# Verify scenarios file
if [ ! -f "$SCENARIOS_FILE" ]; then
    echo "❌ Scenarios file not found: $SCENARIOS_FILE"
    exit 1
fi
echo "  Scenarios file: ✅"
echo

# Run the Python evaluation script
echo "🧪 Running I²-Bench-Lite Comprehensive Evaluation..."
echo "=================================================="

python scripts/run_benchmarks.py --model "$MODEL_TYPE" --scenarios "$SCENARIOS_FILE" --results-dir "$RESULTS_DIR" --timestamp "$TIMESTAMP"

echo
echo "🎯 Evaluation complete! Check $RESULTS_DIR/ directory for outputs."
echo "📊 Key files generated:"
echo "  • $RESULTS_DIR/metrics_${TIMESTAMP}.csv - Detailed scenario results"
echo "  • $RESULTS_DIR/summary_${TIMESTAMP}.md - Executive summary with tables"
echo
echo "💡 To run with different model:"
echo "  MODEL_TYPE=api ./scripts/repro.sh"
echo "  MODEL_TYPE=local ./scripts/repro.sh"
echo
echo "🔍 Next steps:"
echo "  • Review $RESULTS_DIR/summary_*.md for research insights"
echo "  • Analyze $RESULTS_DIR/metrics_*.csv for detailed breakdown"
echo "  • Compare performance across different model types"
