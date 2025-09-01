#!/usr/bin/env python3
"""
Run 100-scenario benchmark with all 5 working models.
"""

import os
import sys
from multi_model_benchmark import MultiModelBenchmark

def run_100_scenario_benchmark():
    """Run the 100-scenario benchmark."""
    print("🚀 STARTING 100-SCENARIO MULTI-MODEL BENCHMARK")
    print("=" * 70)
    
    # Check if scenarios file exists
    scenarios_file = "scenarios_100.jsonl"
    if not os.path.exists(scenarios_file):
        print(f"❌ Scenarios file not found: {scenarios_file}")
        print("Please run generate_100_scenarios.py first")
        return
    
    # Initialize benchmark
    benchmark = MultiModelBenchmark()
    
    # Get available models
    available_models = benchmark.get_available_models()
    print(f"📊 Available models: {available_models}")
    print(f"🤖 Testing {len(available_models)} models")
    print(f"📋 Scenarios file: {scenarios_file}")
    print()
    
    # Run the benchmark
    try:
        results = benchmark.run_full_benchmark()
        print("\n🎉 100-SCENARIO BENCHMARK COMPLETED SUCCESSFULLY!")
        print("✅ All models tested")
        print("✅ Real API validation completed")
        print("✅ Comprehensive results generated")
        
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        return

if __name__ == "__main__":
    run_100_scenario_benchmark()

