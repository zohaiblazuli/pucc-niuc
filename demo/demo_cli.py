#!/usr/bin/env python3
"""
Demo CLI for PCC-NIUC system.
Interactive demonstration of privacy-preserving computation with certificates.
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Add pcc module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pcc.normalizer import normalize_code
from pcc.imperative_grammar import validate_grammar  
from pcc.provenance import create_provenance_tracker
from pcc.checker import check_code_security
from pcc.certificate import generate_certificate, validate_certificate
from pcc.runtime_gate import get_runtime_gate, RuntimePolicy
from pcc.rewrite import rewrite_code, create_safe_config


class DemoSession:
    """Interactive demo session for PCC-NIUC."""
    
    def __init__(self):
        self.session_id = "demo_session"
        self.provenance = create_provenance_tracker(self.session_id)
        self.results_history = []
    
    def run_interactive_demo(self):
        """Run interactive demo mode."""
        print("="*60)
        print("PCC-NIUC Interactive Demo")
        print("="*60)
        print("This demo shows privacy-preserving computation with certificates.")
        print("Enter Python code to see how the PCC system processes it.")
        print("Type 'help' for commands, 'quit' to exit.")
        print()
        
        while True:
            try:
                user_input = input("PCC> ").strip()
                
                if not user_input:
                    continue
                elif user_input.lower() == 'quit':
                    print("Goodbye!")
                    break
                elif user_input.lower() == 'help':
                    self._show_help()
                elif user_input.lower().startswith('load '):
                    filename = user_input[5:].strip()
                    self._load_file(filename)
                elif user_input.lower() == 'history':
                    self._show_history()
                elif user_input.lower() == 'clear':
                    self._clear_session()
                elif user_input.lower() == 'benchmark':
                    self._run_mini_benchmark()
                else:
                    # Process as code
                    self._process_code(user_input)
            
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def _show_help(self):
        """Show help information."""
        help_text = """
Available commands:
  help           - Show this help message
  quit           - Exit the demo
  load <file>    - Load and process code from file
  history        - Show processing history
  clear          - Clear session data
  benchmark      - Run mini benchmark
  
Or enter Python code directly to see how PCC processes it.

Example code to try:
  def add(a, b): return a + b
  exec("print('dangerous')")
  import os; os.listdir()
  sum(range(1000))
"""
        print(help_text)
    
    def _load_file(self, filename: str):
        """Load code from file."""
        try:
            if not os.path.exists(filename):
                print(f"File not found: {filename}")
                return
            
            with open(filename, 'r') as f:
                code = f.read()
            
            print(f"Processing code from {filename}:")
            print("-" * 40)
            print(code)
            print("-" * 40)
            self._process_code(code)
        
        except Exception as e:
            print(f"Error loading file: {e}")
    
    def _show_history(self):
        """Show processing history."""
        if not self.results_history:
            print("No processing history.")
            return
        
        print("\nProcessing History:")
        print("=" * 50)
        for i, result in enumerate(self.results_history, 1):
            print(f"{i}. Security Level: {result['security_level']}")
            print(f"   Violations: {result['violations']}")
            print(f"   Code snippet: {result['code'][:50]}...")
            print()
    
    def _clear_session(self):
        """Clear session data."""
        self.results_history.clear()
        self.provenance = create_provenance_tracker(self.session_id)
        print("Session cleared.")
    
    def _process_code(self, code: str):
        """Process code through PCC pipeline."""
        print(f"\n🔍 Processing code:")
        print("─" * 40)
        print(code)
        print("─" * 40)
        
        # Step 1: Normalization
        print("1️⃣  Normalizing code...")
        try:
            norm_result = normalize_code(code)
            print(f"   ✓ Normalized (complexity: {norm_result['metadata']['complexity_score']})")
            self.provenance.record_computation(
                "normalization", 
                [code], 
                [norm_result['normalized_code']]
            )
        except Exception as e:
            print(f"   ✗ Normalization failed: {e}")
            return
        
        # Step 2: Grammar validation
        print("2️⃣  Validating grammar...")
        try:
            grammar_result = validate_grammar(code)
            if grammar_result['is_valid']:
                print(f"   ✓ Grammar valid (security level: {grammar_result['security_level']})")
            else:
                print(f"   ⚠ Grammar issues: {len(grammar_result['violations'])} violations")
                for violation in grammar_result['violations'][:3]:  # Show first 3
                    print(f"      - {violation}")
        except Exception as e:
            print(f"   ✗ Grammar validation failed: {e}")
        
        # Step 3: Security checking
        print("3️⃣  Security analysis...")
        try:
            security_result = check_code_security(code)
            security_level = security_result['security_level']
            total_violations = security_result['total_violations']
            
            level_emoji = {
                'approved': '✅',
                'monitored': '👀', 
                'restricted': '⚠️',
                'rejected': '❌'
            }
            
            emoji = level_emoji.get(security_level, '❓')
            print(f"   {emoji} Security level: {security_level.upper()}")
            print(f"   📊 Violations: {total_violations}")
            
            if total_violations > 0:
                print("   🚨 Security violations:")
                for violation in security_result['violations'][:3]:  # Show first 3
                    print(f"      - {violation['message']} (line {violation.get('line_number', '?')})")
        
        except Exception as e:
            print(f"   ✗ Security check failed: {e}")
            security_result = {'security_level': 'error', 'total_violations': -1}
        
        # Step 4: Code rewriting (for non-rejected code)
        if security_result['security_level'] != 'rejected':
            print("4️⃣  Rewriting code...")
            try:
                rewrite_result = rewrite_code(code, create_safe_config())
                if rewrite_result['success']:
                    stats = rewrite_result['stats']
                    print(f"   🔧 Code rewritten (guards: {stats['guards_added']}, calls: {stats['calls_instrumented']})")
                else:
                    print(f"   ✗ Rewrite failed: {rewrite_result['error']}")
            except Exception as e:
                print(f"   ✗ Rewrite failed: {e}")
        
        # Step 5: Certificate generation (for approved code)
        if security_result['security_level'] == 'approved':
            print("5️⃣  Generating certificate...")
            try:
                cert_json = generate_certificate(
                    computation_code=code,
                    input_data="demo_input",
                    output_data="demo_output"
                )
                cert_data = json.loads(cert_json)
                print(f"   📜 Certificate generated: {cert_data['certificate_id'][:8]}...")
                
                # Validate certificate
                validation = validate_certificate(cert_json)
                if validation['is_valid']:
                    print("   ✅ Certificate validated successfully")
                else:
                    print("   ❌ Certificate validation failed")
            
            except Exception as e:
                print(f"   ✗ Certificate generation failed: {e}")
        
        # Record result
        result = {
            'code': code,
            'security_level': security_result['security_level'],
            'violations': security_result['total_violations']
        }
        self.results_history.append(result)
        
        print("─" * 40)
        print(f"✨ Processing complete!\n")
    
    def _run_mini_benchmark(self):
        """Run a mini benchmark with sample scenarios."""
        print("\n🏃 Running mini benchmark...")
        
        sample_scenarios = [
            ("Safe arithmetic", "def add(x, y): return x + y"),
            ("Dangerous eval", "eval('2 + 2')"),
            ("File access", "open('file.txt', 'r')"),
            ("Complex computation", "sum(i**2 for i in range(100))"),
        ]
        
        passed = 0
        total = len(sample_scenarios)
        
        for desc, code in sample_scenarios:
            try:
                security_result = check_code_security(code)
                level = security_result['security_level']
                violations = security_result['total_violations']
                
                # Simple pass/fail criteria
                if ("dangerous" in desc.lower() or "file access" in desc.lower()) and level == 'rejected':
                    status = "✅ PASS"
                    passed += 1
                elif "safe" in desc.lower() and level in ['approved', 'monitored']:
                    status = "✅ PASS"
                    passed += 1
                elif "complex" in desc.lower() and level in ['approved', 'monitored', 'restricted']:
                    status = "✅ PASS"
                    passed += 1
                else:
                    status = "❌ FAIL"
                
                print(f"  {desc:20} → {level:10} ({violations} violations) {status}")
            
            except Exception as e:
                print(f"  {desc:20} → ERROR: {e}")
        
        print(f"\nMini benchmark complete: {passed}/{total} tests passed ({passed/total*100:.0f}%)")


def run_file_demo(filename: str, output_file: Optional[str] = None):
    """Run demo on a specific file."""
    if not os.path.exists(filename):
        print(f"Error: File not found: {filename}")
        return
    
    print(f"Processing file: {filename}")
    
    with open(filename, 'r') as f:
        code = f.read()
    
    session = DemoSession()
    session._process_code(code)
    
    if output_file:
        result = session.results_history[-1] if session.results_history else {}
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Results saved to: {output_file}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="PCC-NIUC Demo CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python demo_cli.py                    # Interactive mode
  python demo_cli.py -f example.py     # Process file
  python demo_cli.py -f code.py -o result.json  # Save results
        """
    )
    
    parser.add_argument('-f', '--file', 
                       help='Process code from file instead of interactive mode')
    parser.add_argument('-o', '--output',
                       help='Output file for results (JSON format)')
    parser.add_argument('-v', '--version', action='version', version='PCC-NIUC Demo v1.0')
    
    args = parser.parse_args()
    
    try:
        if args.file:
            run_file_demo(args.file, args.output)
        else:
            session = DemoSession()
            session.run_interactive_demo()
    
    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Demo error: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
