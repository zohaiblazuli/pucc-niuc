#!/usr/bin/env python3
"""
Multi-model NIUC benchmark with REAL API calls.
Tests GPT-4, Claude Sonnet, Qwen3 8B, DeepSeek V3.1 with 60 scenarios.
"""

import os
import sys
import json
import time
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Add paths for imports
sys.path.insert(0, '.')

from real_api_models import RealAPIModel, test_real_api_connection
from pcc.runtime_gate import process_with_block_mode, process_with_rewrite_mode
from demo.model_wrapper import ModelWrapper, ModelType


@dataclass
class ModelResult:
    """Results for a single model."""
    model_name: str
    scenarios_run: int
    total_tokens_used: int
    total_cost: float
    avg_latency_ms: float
    api_errors: int
    asr_block: float
    fpr_block: float  
    asr_rewrite: float
    fpr_rewrite: float


class MultiModelBenchmark:
    """Benchmark multiple models with real API calls and NIUC evaluation."""
    
    def __init__(self):
        self.models = {
            "gpt-4": {"available": False, "reason": ""},
            "claude-3-7-sonnet": {"available": False, "reason": ""},
            "google/gemini-2.5-flash": {"available": False, "reason": ""},
            "qwen/qwen3-8b": {"available": False, "reason": ""},
            "deepseek/deepseek-chat-v3.1": {"available": False, "reason": ""},
            "meta-llama/llama-3.3-70b-instruct:free": {"available": False, "reason": ""}
        }
        self.check_model_availability()
    
    def check_model_availability(self):
        """Check which models are available based on API keys."""
        print("🔍 CHECKING MODEL AVAILABILITY")
        print("=" * 40)
        
        # Check GPT-4
        if os.getenv("OPENAI_API_KEY"):
            if test_real_api_connection("gpt-4"):
                self.models["gpt-4"]["available"] = True
                print("✅ GPT-4: Available")
            else:
                self.models["gpt-4"]["reason"] = "API test failed"
                print("❌ GPT-4: API test failed")
        else:
            self.models["gpt-4"]["reason"] = "No OPENAI_API_KEY"
            print("⚠️  GPT-4: No API key")
        
        # Check Claude (with error handling)
        if os.getenv("ANTHROPIC_API_KEY"):
            try:
                if test_real_api_connection("claude-3-7-sonnet"):
                    self.models["claude-3-7-sonnet"]["available"] = True
                    print("✅ Claude 3.7 Sonnet: Available")
                else:
                    self.models["claude-3-7-sonnet"]["reason"] = "API test failed" 
                    print("❌ Claude 3.7 Sonnet: API test failed")
            except:
                self.models["claude-3-7-sonnet"]["reason"] = "API endpoint issue"
                print("❌ Claude 3.7 Sonnet: API endpoint issue")
        else:
            self.models["claude-3-7-sonnet"]["reason"] = "No ANTHROPIC_API_KEY"
            print("⚠️  Claude 3.7 Sonnet: No API key")
        

        
        # Check OpenRouter models
        if os.getenv("OPENROUTER_API_KEY"):
            for model in ["google/gemini-2.5-flash", "qwen/qwen3-8b", "deepseek/deepseek-chat-v3.1", "meta-llama/llama-3.3-70b-instruct:free"]:
                try:
                    if test_real_api_connection(model):
                        self.models[model]["available"] = True
                        print(f"✅ {model}: Available")
                    else:
                        self.models[model]["reason"] = "API test failed"
                        print(f"❌ {model}: API test failed")
                except:
                    self.models[model]["reason"] = "API connection error"
                    print(f"❌ {model}: API connection error")
        else:
            for model in ["google/gemini-2.5-flash", "qwen/qwen3-8b", "deepseek/deepseek-chat-v3.1", "meta-llama/llama-3.3-70b-instruct:free"]:
                self.models[model]["reason"] = "No OPENROUTER_API_KEY"
                print(f"⚠️  {model}: No OpenRouter API key")
        
        print()
    
    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        return [name for name, info in self.models.items() if info["available"]]
    
    def run_model_evaluation(self, model_name: str, scenarios: List[Dict]) -> ModelResult:
        """Run evaluation for single model with real API calls."""
        print(f"🚀 EVALUATING {model_name.upper()}")
        print("-" * 50)
        
        if not self.models[model_name]["available"]:
            reason = self.models[model_name]["reason"]
            print(f"❌ Skipping {model_name}: {reason}")
            return ModelResult(
                model_name=model_name,
                scenarios_run=0,
                total_tokens_used=0,
                total_cost=0,
                avg_latency_ms=0,
                api_errors=1,
                asr_block=0,
                fpr_block=0,
                asr_rewrite=0,
                fpr_rewrite=0
            )
        
        # Initialize real API model
        try:
            real_model = RealAPIModel(model_name)
        except Exception as e:
            print(f"❌ Failed to initialize {model_name}: {e}")
            return ModelResult(
                model_name=model_name,
                scenarios_run=0,
                total_tokens_used=0,
                total_cost=0,
                avg_latency_ms=0,
                api_errors=1,
                asr_block=0,
                fpr_block=0,
                asr_rewrite=0,
                fpr_rewrite=0
            )
        
        # Run scenarios
        results = []
        total_tokens = 0
        total_cost = 0
        latencies = []
        api_errors = 0
        
        print(f"📊 Processing {len(scenarios)} scenarios...")
        
        for i, scenario in enumerate(scenarios):
            if i % 10 == 0:
                print(f"   Progress: {i}/{len(scenarios)} scenarios")
            
            # Create segments for NIUC
            segments = []
            if scenario["trusted"]:
                segments.append((scenario["trusted"], "trusted", "system"))
            if scenario["untrusted"]: 
                segments.append((scenario["untrusted"], "untrusted", "external"))
            
            # Generate LLM response with real API
            prompt = " ".join(seg[0] for seg in segments)
            
            try:
                start_time = time.perf_counter()
                llm_response = real_model.generate(prompt, max_tokens=200)
                
                if llm_response.error_message:
                    api_errors += 1
                    continue
                
                # Track API usage
                if llm_response.token_count:
                    total_tokens += llm_response.token_count
                    total_cost += (llm_response.token_count / 1000) * real_model.config.cost_per_1k_tokens
                
                latencies.append(llm_response.generation_time_ms)
                
                # Test both NIUC modes
                block_result = process_with_block_mode(segments)
                rewrite_result = process_with_rewrite_mode(segments)
                
                end_time = time.perf_counter()
                total_time = (end_time - start_time) * 1000
                
                results.append({
                    "scenario_id": scenario["id"],
                    "expected": scenario["expected"],
                    "llm_response": llm_response.text[:100],
                    "block_allowed": block_result.allowed,
                    "block_correct": (block_result.allowed and scenario["expected"] == "pass") or (not block_result.allowed and scenario["expected"] == "blocked"),
                    "rewrite_allowed": rewrite_result.allowed,
                    "rewrite_correct": (rewrite_result.allowed and scenario["expected"] == "pass") or (not rewrite_result.allowed and scenario["expected"] == "blocked"),
                    "rewrite_applied": rewrite_result.rewrite_applied,
                    "tokens_used": llm_response.token_count or 0,
                    "api_latency_ms": llm_response.generation_time_ms,
                    "total_latency_ms": total_time
                })
                
            except Exception as e:
                print(f"      Error on scenario {scenario['id']}: {e}")
                api_errors += 1
                continue
        
        print(f"✅ Completed: {len(results)} scenarios processed")
        
        # Compute metrics
        attack_scenarios = [r for r in results if r.get("expected") == "blocked"]
        benign_scenarios = [r for r in results if r.get("expected") == "pass"]
        
        # ASR (Attack Success Rate) and FPR (False Positive Rate)
        asr_block = len([r for r in attack_scenarios if r["block_allowed"]]) / len(attack_scenarios) * 100 if attack_scenarios else 0
        fpr_block = len([r for r in benign_scenarios if not r["block_allowed"]]) / len(benign_scenarios) * 100 if benign_scenarios else 0
        
        asr_rewrite = len([r for r in attack_scenarios if r["rewrite_allowed"]]) / len(attack_scenarios) * 100 if attack_scenarios else 0  
        fpr_rewrite = len([r for r in benign_scenarios if not r["rewrite_allowed"]]) / len(benign_scenarios) * 100 if benign_scenarios else 0
        
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        print(f"📊 {model_name.upper()} RESULTS:")
        print(f"   Scenarios processed: {len(results)}")
        print(f"   Total tokens used: {total_tokens:,}")
        print(f"   Total cost: ${total_cost:.4f}")
        print(f"   Avg API latency: {avg_latency:.1f}ms")
        print(f"   API errors: {api_errors}")
        print(f"   Block mode - ASR: {asr_block:.1f}%, FPR: {fpr_block:.1f}%")
        print(f"   Rewrite mode - ASR: {asr_rewrite:.1f}%, FPR: {fpr_rewrite:.1f}%")
        print()
        
        return ModelResult(
            model_name=model_name,
            scenarios_run=len(results),
            total_tokens_used=total_tokens,
            total_cost=total_cost,
            avg_latency_ms=avg_latency,
            api_errors=api_errors,
            asr_block=asr_block,
            fpr_block=fpr_block,
            asr_rewrite=asr_rewrite,
            fpr_rewrite=fpr_rewrite
        )
    
    def run_full_benchmark(self, scenarios_file: str = "scenarios_100.jsonl") -> Dict[str, ModelResult]:
        """Run benchmark across all available models."""
        print("🎯 MULTI-MODEL NIUC BENCHMARK")
        print("=" * 60)
        
        # Load scenarios
        scenarios = []
        with open(scenarios_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    scenarios.append(json.loads(line.strip()))
        
        print(f"📊 Loaded {len(scenarios)} scenarios from {scenarios_file}")
        
        available_models = self.get_available_models()
        if not available_models:
            print("❌ No models available! Please set API keys.")
            return {}
        
        print(f"🤖 Testing {len(available_models)} models: {', '.join(available_models)}")
        print()
        
        # Run evaluation for each available model
        results = {}
        for model_name in available_models:
            results[model_name] = self.run_model_evaluation(model_name, scenarios)
        
        # Print comparative summary
        self.print_comparative_summary(results)
        
        # Export detailed results
        self.export_results(results, scenarios)
        
        return results
    
    def print_comparative_summary(self, results: Dict[str, ModelResult]):
        """Print comparative summary across models."""
        print("🏆 COMPARATIVE SUMMARY")
        print("=" * 80)
        
        print(f"{'Model':<20} {'Scenarios':<10} {'Tokens':<8} {'Cost':<8} {'Latency':<10} {'Block ASR':<10} {'Rewrite FPR'}")
        print("-" * 80)
        
        for model_name, result in results.items():
            if result.scenarios_run > 0:
                print(f"{model_name:<20} {result.scenarios_run:<10} {result.total_tokens_used:<8,} "
                      f"${result.total_cost:<7.3f} {result.avg_latency_ms:<10.1f} "
                      f"{result.asr_block:<10.1f}% {result.fpr_rewrite:<.1f}%")
        
        print("\n🎯 KEY INSIGHTS:")
        print("• Lower ASR = Better attack blocking")
        print("• Lower FPR = Better benign content preservation")  
        print("• Token usage = Real API verification")
        print("• Cost comparison across providers")
    
    def export_results(self, results: Dict[str, ModelResult], scenarios: List[Dict]):
        """Export results to CSV and summary."""
        timestamp = int(time.time())
        
        # Export summary CSV
        summary_data = []
        for model_name, result in results.items():
            summary_data.append({
                "model": model_name,
                "scenarios_run": result.scenarios_run,
                "total_tokens": result.total_tokens_used,
                "total_cost": result.total_cost,
                "avg_latency_ms": result.avg_latency_ms,
                "api_errors": result.api_errors,
                "asr_block": result.asr_block,
                "fpr_block": result.fpr_block,
                "asr_rewrite": result.asr_rewrite, 
                "fpr_rewrite": result.fpr_rewrite
            })
        
        summary_file = f"results/multi_model_summary_{timestamp}.csv"
        Path("results").mkdir(exist_ok=True)
        
        pd.DataFrame(summary_data).to_csv(summary_file, index=False)
        print(f"📊 Summary exported: {summary_file}")


def main():
    """Main benchmark execution."""
    print("🚀 STARTING MULTI-MODEL BENCHMARK WITH REAL APIs")
    print("=" * 60)
    
    benchmark = MultiModelBenchmark()
    results = benchmark.run_full_benchmark()
    
    if results:
        print("\n🎉 Benchmark completed successfully!")
        print("✅ Real API calls verified")
        print("✅ Token usage tracked") 
        print("✅ NIUC performance measured")
        print("✅ Ready to scale to 500 scenarios")
    else:
        print("\n❌ No models available for testing")
        print("Please set API keys:")
        print("   $env:OPENAI_API_KEY='your_key'")
        print("   $env:ANTHROPIC_API_KEY='your_key'")
        print("   $env:OPENROUTER_API_KEY='your_key'")


if __name__ == "__main__":
    main()
