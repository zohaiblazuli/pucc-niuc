#!/bin/bash
# Reproducible build and test script for PCC-NIUC
set -euo pipefail

echo "🔧 PCC-NIUC Reproducible Build Script"
echo "======================================"

# Check Python version
echo "📋 Checking Python version..."
python --version
echo

# Create virtual environment
echo "🏗️  Setting up virtual environment..."
if [ ! -d "venv" ]; then
    python -m venv venv
fi

# Activate virtual environment (cross-platform)
if [ -f "venv/Scripts/activate" ]; then
    # Windows
    source venv/Scripts/activate
elif [ -f "venv/bin/activate" ]; then
    # Unix/Linux/Mac
    source venv/bin/activate
else
    echo "❌ Virtual environment activation failed"
    exit 1
fi

echo "✅ Virtual environment activated"

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -e .
echo "✅ Dependencies installed"

# Run smoke tests
echo "🧪 Running smoke tests..."
python scripts/smoke_test.py
echo "✅ Smoke tests passed"

# Run full test suite
echo "🔬 Running full test suite..."
python -m pytest tests/ -v --tb=short
echo "✅ All tests passed"

# Run benchmarks
echo "📊 Running benchmarks..."
python bench/score.py --verbose
echo "✅ Benchmarks completed"

# Run demo
echo "🎯 Testing demo CLI..."
python demo/demo_cli.py --help > /dev/null
echo "✅ Demo CLI working"

echo
echo "🎉 All checks passed! PCC-NIUC is ready to go."
echo "To activate the environment: source venv/bin/activate (or venv\\Scripts\\activate on Windows)"
echo "To run demo: python demo/demo_cli.py"
echo "To run benchmarks: python bench/score.py"
echo "To run tests: python -m pytest tests/ -v"
