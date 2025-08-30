"""
Scoring system for PCC-NIUC benchmarks.
Evaluates system performance against test scenarios.
"""

import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import sys
import os

# Add pcc module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pcc.normalizer import normalize_code
from pcc.imperative_grammar import validate_grammar
from pcc.checker import check_code_security
from pcc.certificate import generate_certificate
from pcc.rewrite import rewrite_code


@dataclass
class TestResult:
    """Result of a single test scenario."""
    scenario_id: str
    description: str
    category: str
    passed: bool
    expected_security_level: str
    actual_security_level: str
    expected_violations: int
    actual_violations: int
    execution_time_ms: float
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class BenchmarkReport:
    """Overall benchmark report."""
    total_scenarios: int
    passed_scenarios: int
    failed_scenarios: int
    pass_rate: float
    average_execution_time_ms: float
    results_by_category: Dict[str, Dict[str, Any]]
    detailed_results: List[TestResult]
    system_stats: Dict[str, Any]


class BenchmarkRunner:
    """Runs benchmark tests against PCC-NIUC system."""
    
    def __init__(self, scenarios_file: str = "scenarios.jsonl"):
        self.scenarios_file = Path(scenarios_file)
        self.scenarios = self._load_scenarios()
        self.results: List[TestResult] = []
    
    def _load_scenarios(self) -> List[Dict[str, Any]]:
        """Load test scenarios from JSONL file."""
        scenarios = []
        
        if not self.scenarios_file.exists():
            raise FileNotFoundError(f"Scenarios file not found: {self.scenarios_file}")
        
        with open(self.scenarios_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    scenario = json.loads(line)
                    scenarios.append(scenario)
                except json.JSONDecodeError as e:
                    print(f"Warning: Invalid JSON on line {line_num}: {e}")
        
        return scenarios
    
    def run_benchmark(self, verbose: bool = False) -> BenchmarkReport:
        """
        Run all benchmark scenarios.
        
        Args:
            verbose: Whether to print detailed progress
            
        Returns:
            Benchmark report with results
        """
        self.results = []
        
        print(f"Running benchmark with {len(self.scenarios)} scenarios...")
        
        for i, scenario in enumerate(self.scenarios):
            if verbose:
                print(f"Running scenario {i+1}/{len(self.scenarios)}: {scenario['id']}")
            
            result = self._run_scenario(scenario)
            self.results.append(result)
            
            if verbose and not result.passed:
                print(f"  FAILED: {result.error_message}")
        
        return self._generate_report()
    
    def _run_scenario(self, scenario: Dict[str, Any]) -> TestResult:
        """Run a single test scenario."""
        start_time = time.perf_counter()
        
        try:
            # Extract scenario data
            scenario_id = scenario['id']
            description = scenario['description']
            code = scenario['code']
            expected_level = scenario['expected_security_level']
            expected_violations = scenario['expected_violations']
            category = scenario.get('category', 'unknown')
            
            # Run PCC pipeline
            pipeline_result = self._run_pcc_pipeline(code)
            
            # Check results
            actual_level = pipeline_result.get('security_level', 'unknown')
            actual_violations = pipeline_result.get('total_violations', 0)
            
            # Determine if test passed
            passed = (
                self._security_levels_match(expected_level, actual_level) and
                abs(expected_violations - actual_violations) <= 1  # Allow small variance
            )
            
            execution_time = (time.perf_counter() - start_time) * 1000
            
            return TestResult(
                scenario_id=scenario_id,
                description=description,
                category=category,
                passed=passed,
                expected_security_level=expected_level,
                actual_security_level=actual_level,
                expected_violations=expected_violations,
                actual_violations=actual_violations,
                execution_time_ms=execution_time,
                details=pipeline_result
            )
        
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            
            return TestResult(
                scenario_id=scenario.get('id', 'unknown'),
                description=scenario.get('description', 'unknown'),
                category=scenario.get('category', 'error'),
                passed=False,
                expected_security_level=scenario.get('expected_security_level', 'unknown'),
                actual_security_level='error',
                expected_violations=scenario.get('expected_violations', 0),
                actual_violations=-1,
                execution_time_ms=execution_time,
                error_message=str(e)
            )
    
    def _run_pcc_pipeline(self, code: str) -> Dict[str, Any]:
        """Run the complete PCC pipeline on code."""
        results = {}
        
        # Step 1: Normalize code
        try:
            norm_result = normalize_code(code)
            results['normalization'] = norm_result
        except Exception as e:
            results['normalization'] = {'error': str(e)}
        
        # Step 2: Validate grammar
        try:
            grammar_result = validate_grammar(code)
            results['grammar'] = grammar_result
        except Exception as e:
            results['grammar'] = {'error': str(e)}
        
        # Step 3: Security check
        try:
            security_result = check_code_security(code)
            results['security'] = security_result
            results['security_level'] = security_result.get('security_level', 'unknown')
            results['total_violations'] = security_result.get('total_violations', 0)
        except Exception as e:
            results['security'] = {'error': str(e)}
            results['security_level'] = 'error'
            results['total_violations'] = -1
        
        # Step 4: Code rewriting (optional)
        try:
            rewrite_result = rewrite_code(code)
            results['rewrite'] = rewrite_result
        except Exception as e:
            results['rewrite'] = {'error': str(e)}
        
        # Step 5: Certificate generation (for approved code)
        if results.get('security_level') == 'approved':
            try:
                cert_json = generate_certificate(
                    computation_code=code,
                    input_data="test_input",
                    output_data="test_output"
                )
                results['certificate'] = json.loads(cert_json)
            except Exception as e:
                results['certificate'] = {'error': str(e)}
        
        return results
    
    def _security_levels_match(self, expected: str, actual: str) -> bool:
        """Check if security levels match (with some tolerance)."""
        # Define security level hierarchy
        level_hierarchy = {
            'approved': 0,
            'monitored': 1,
            'restricted': 2,
            'rejected': 3,
            'error': 4
        }
        
        expected_rank = level_hierarchy.get(expected, 4)
        actual_rank = level_hierarchy.get(actual, 4)
        
        # Exact match is always good
        if expected == actual:
            return True
        
        # Allow some tolerance for adjacent levels
        if abs(expected_rank - actual_rank) <= 1:
            return True
        
        return False
    
    def _generate_report(self) -> BenchmarkReport:
        """Generate comprehensive benchmark report."""
        total_scenarios = len(self.results)
        passed_scenarios = sum(1 for r in self.results if r.passed)
        failed_scenarios = total_scenarios - passed_scenarios
        pass_rate = (passed_scenarios / total_scenarios) * 100 if total_scenarios > 0 else 0
        
        avg_execution_time = sum(r.execution_time_ms for r in self.results) / total_scenarios if total_scenarios > 0 else 0
        
        # Results by category
        category_stats = {}
        for result in self.results:
            category = result.category
            if category not in category_stats:
                category_stats[category] = {
                    'total': 0,
                    'passed': 0,
                    'failed': 0,
                    'avg_time_ms': 0
                }
            
            category_stats[category]['total'] += 1
            if result.passed:
                category_stats[category]['passed'] += 1
            else:
                category_stats[category]['failed'] += 1
        
        # Calculate pass rates and average times per category
        for category, stats in category_stats.items():
            stats['pass_rate'] = (stats['passed'] / stats['total']) * 100 if stats['total'] > 0 else 0
            category_results = [r for r in self.results if r.category == category]
            stats['avg_time_ms'] = sum(r.execution_time_ms for r in category_results) / len(category_results)
        
        # System statistics
        system_stats = {
            'total_execution_time_ms': sum(r.execution_time_ms for r in self.results),
            'errors_encountered': sum(1 for r in self.results if r.error_message is not None),
            'security_level_distribution': self._get_security_level_distribution(),
            'category_distribution': {cat: stats['total'] for cat, stats in category_stats.items()}
        }
        
        return BenchmarkReport(
            total_scenarios=total_scenarios,
            passed_scenarios=passed_scenarios,
            failed_scenarios=failed_scenarios,
            pass_rate=pass_rate,
            average_execution_time_ms=avg_execution_time,
            results_by_category=category_stats,
            detailed_results=self.results,
            system_stats=system_stats
        )
    
    def _get_security_level_distribution(self) -> Dict[str, int]:
        """Get distribution of security levels in results."""
        distribution = {}
        for result in self.results:
            level = result.actual_security_level
            distribution[level] = distribution.get(level, 0) + 1
        return distribution
    
    def export_report(self, report: BenchmarkReport, output_file: str = "benchmark_report.json"):
        """Export benchmark report to JSON file."""
        report_dict = asdict(report)
        
        with open(output_file, 'w') as f:
            json.dump(report_dict, f, indent=2, default=str)
        
        print(f"Benchmark report exported to: {output_file}")
    
    def print_summary(self, report: BenchmarkReport):
        """Print benchmark summary to console."""
        print("\n" + "="*60)
        print("PCC-NIUC BENCHMARK REPORT")
        print("="*60)
        print(f"Total Scenarios: {report.total_scenarios}")
        print(f"Passed: {report.passed_scenarios}")
        print(f"Failed: {report.failed_scenarios}")
        print(f"Pass Rate: {report.pass_rate:.1f}%")
        print(f"Average Execution Time: {report.average_execution_time_ms:.2f} ms")
        
        print("\nResults by Category:")
        print("-" * 40)
        for category, stats in report.results_by_category.items():
            print(f"{category:20} {stats['passed']:3d}/{stats['total']:3d} ({stats['pass_rate']:5.1f}%)")
        
        print("\nSecurity Level Distribution:")
        print("-" * 40)
        for level, count in report.system_stats['security_level_distribution'].items():
            print(f"{level:15} {count:3d}")
        
        if report.failed_scenarios > 0:
            print("\nFailed Scenarios:")
            print("-" * 40)
            for result in report.detailed_results:
                if not result.passed:
                    print(f"  {result.scenario_id}: {result.error_message or 'Security level mismatch'}")


def main():
    """Main benchmark runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run PCC-NIUC benchmarks")
    parser.add_argument("--scenarios", default="scenarios.jsonl", help="Path to scenarios file")
    parser.add_argument("--output", default="benchmark_report.json", help="Output report file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    try:
        runner = BenchmarkRunner(args.scenarios)
        report = runner.run_benchmark(verbose=args.verbose)
        runner.print_summary(report)
        runner.export_report(report, args.output)
        
        # Exit with non-zero code if tests failed
        if report.failed_scenarios > 0:
            sys.exit(1)
    
    except Exception as e:
        print(f"Error running benchmarks: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
