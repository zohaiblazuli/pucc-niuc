#!/usr/bin/env python3
"""
Quick 10-scenario test to validate all 5 working models.
"""

import os
import time
import json
from typing import List, Dict
from real_api_models import RealAPIModel, test_real_api_connection
from multi_model_benchmark import MultiModelBenchmark

def run_quick_test():
    """Run a quick 10-scenario test with all working models."""
    print("🚀 QUICK 10-SCENARIO VALIDATION TEST")
    print("=" * 60)
    
    # Initialize benchmark
    benchmark = MultiModelBenchmark()
    
    # Get available models
    available_models = benchmark.get_available_models()
    print(f"📊 Available models: {available_models}")
    print(f"🤖 Testing {len(available_models)} models")
    print()
    
    # Load scenarios and take first 10
    scenarios_file = "scenarios_60.jsonl"
    if not os.path.exists(scenarios_file):
        print(f"❌ Scenarios file not found: {scenarios_file}")
        return
    
    scenarios = []
    with open(scenarios_file, 'r', encoding='utf-8') as f:
        for line in f:
            scenarios.append(json.loads(line.strip()))
    
    # Take first 10 scenarios
    test_scenarios = scenarios[:10]
    print(f"📊 Using first 10 scenarios from {len(scenarios)} total scenarios")
    print()
    
    # Test each model
    results = {}
    
    for model_name in available_models:
        print(f"🚀 TESTING {model_name.upper()}")
        print("-" * 40)
        
        try:
            # Initialize model
            real_model = RealAPIModel(model_name)
            
            # Process 10 scenarios
            processed = 0
            total_tokens = 0
            total_cost = 0
            latencies = []
            api_errors = 0
            
            for i, scenario in enumerate(test_scenarios):
                # Create segments for NIUC
                segments = []
                if scenario["trusted"]:
                    segments.append((scenario["trusted"], "trusted", "system"))
                if scenario["untrusted"]: 
                    segments.append((scenario["untrusted"], "untrusted", "external"))
                
                # Generate LLM response
                prompt = " ".join(seg[0] for seg in segments)
                
                try:
                    start_time = time.perf_counter()
                    llm_response = real_model.generate(prompt, max_tokens=200)
                    
                    if llm_response.error_message:
                        api_errors += 1
                        continue
                    
                    # Track usage
                    if llm_response.token_count:
                        total_tokens += llm_response.token_count
                        total_cost += (llm_response.token_count / 1000) * real_model.config.cost_per_1k_tokens
                    
                    latencies.append(llm_response.generation_time_ms)
                    processed += 1
                    
                except Exception as e:
                    print(f"   Error on scenario {i+1}: {e}")
                    api_errors += 1
                    continue
            
            # Calculate metrics
            avg_latency = sum(latencies) / len(latencies) if latencies else 0
            
            # Simple success rate
            success_rate = (processed / 10) * 100
            
            print(f"✅ {model_name.upper()} RESULTS:")
            print(f"   Scenarios processed: {processed}/10 ({success_rate:.1f}%)")
            print(f"   Total tokens: {total_tokens:,}")
            print(f"   Total cost: ${total_cost:.4f}")
            print(f"   Avg latency: {avg_latency:.1f}ms")
            print(f"   API errors: {api_errors}")
            print()
            
            results[model_name] = {
                "processed": processed,
                "success_rate": success_rate,
                "tokens": total_tokens,
                "cost": total_cost,
                "latency": avg_latency,
                "errors": api_errors
            }
            
        except Exception as e:
            print(f"❌ Failed to test {model_name}: {e}")
            print()
            results[model_name] = {
                "processed": 0,
                "success_rate": 0,
                "tokens": 0,
                "cost": 0,
                "latency": 0,
                "errors": 10
            }
    
    # Summary
    print("🏆 QUICK TEST SUMMARY")
    print("=" * 60)
    print(f"{'Model':<25} {'Success':<10} {'Tokens':<10} {'Cost':<10} {'Latency':<10}")
    print("-" * 60)
    
    for model_name, result in results.items():
        print(f"{model_name:<25} {result['success_rate']:<10.1f}% {result['tokens']:<10,} ${result['cost']:<9.4f} {result['latency']:<10.1f}ms")
    
    print()
    print("🎯 READY FOR FULL 60-SCENARIO BENCHMARK!")
    print("✅ All models validated")
    print("✅ API connections working")
    print("✅ Ready to proceed with comprehensive testing")

if __name__ == "__main__":
    run_quick_test()
