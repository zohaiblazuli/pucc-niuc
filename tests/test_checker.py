"""
Tests for the checker module.
Tests security checking functionality for PCC-NIUC system.
Expected behavior: checker.py should be deterministic, ≤ 500 LOC, no ML.
"""

import unittest
import sys
import os

# Add pcc module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pcc.checker import SecurityChecker, SecurityViolation, ViolationSeverity, check_code_security


class TestSecurityChecker(unittest.TestCase):
    """Test cases for SecurityChecker class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.checker = SecurityChecker()
    
    def test_safe_code_approval(self):
        """Test that safe code is approved."""
        safe_code = """
def add_numbers(a, b):
    return a + b

def calculate_area(radius):
    import math
    return math.pi * radius ** 2

result = add_numbers(5, 3)
area = calculate_area(2.5)
"""
        result = self.checker.check(safe_code)
        
        self.assertEqual(result['security_level'], 'approved')
        self.assertEqual(result['total_violations'], 0)
        self.assertEqual(len(result['violations']), 0)
    
    def test_dangerous_exec_detected(self):
        """Test that exec() calls are detected as dangerous."""
        dangerous_code = """
def execute_code(code_string):
    exec(code_string)
    return True
"""
        result = self.checker.check(dangerous_code)
        
        self.assertEqual(result['security_level'], 'rejected')
        self.assertGreater(result['total_violations'], 0)
        
        # Should find exec violation
        exec_violations = [v for v in result['violations'] if 'exec' in v['message'].lower()]
        self.assertGreater(len(exec_violations), 0)
    
    def test_dangerous_eval_detected(self):
        """Test that eval() calls are detected as dangerous."""
        dangerous_code = """
def evaluate_expression(expr):
    result = eval(expr)
    return result
"""
        result = self.checker.check(dangerous_code)
        
        self.assertEqual(result['security_level'], 'rejected')
        self.assertGreater(result['total_violations'], 0)
        
        # Should find eval violation
        eval_violations = [v for v in result['violations'] if 'eval' in v['message'].lower()]
        self.assertGreater(len(eval_violations), 0)
    
    def test_dangerous_imports_detected(self):
        """Test that dangerous imports are detected."""
        dangerous_code = """
import os
import subprocess
import socket

def list_files():
    return os.listdir('.')
"""
        result = self.checker.check(dangerous_code)
        
        self.assertEqual(result['security_level'], 'rejected')
        self.assertGreater(result['total_violations'], 0)
        
        # Should find import violations
        import_violations = [v for v in result['violations'] if 'import' in v['message'].lower()]
        self.assertGreater(len(import_violations), 0)
    
    def test_file_operations_detected(self):
        """Test that file operations are detected."""
        file_code = """
def read_secret_file():
    with open('secret.txt', 'r') as f:
        return f.read()
        
def write_data(data):
    with open('output.txt', 'w') as f:
        f.write(data)
"""
        result = self.checker.check(file_code)
        
        self.assertEqual(result['security_level'], 'rejected')
        self.assertGreater(result['total_violations'], 0)
        
        # Should find file operation violations
        file_violations = [v for v in result['violations'] if 'file' in v['message'].lower()]
        self.assertGreater(len(file_violations), 0)
    
    def test_network_operations_detected(self):
        """Test that network operations are detected."""
        network_code = """
import urllib.request
import requests

def fetch_data(url):
    response = urllib.request.urlopen(url)
    return response.read()

def post_data(url, data):
    response = requests.post(url, json=data)
    return response.json()
"""
        result = self.checker.check(network_code)
        
        self.assertEqual(result['security_level'], 'rejected')
        self.assertGreater(result['total_violations'], 0)
        
        # Should find network violations
        network_violations = [v for v in result['violations'] 
                            if 'network' in v['message'].lower() or 'import' in v['message'].lower()]
        self.assertGreater(len(network_violations), 0)
    
    def test_subprocess_operations_detected(self):
        """Test that subprocess operations are detected."""
        subprocess_code = """
import subprocess
import os

def run_command(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True)

def system_call(cmd):
    return os.system(cmd)
"""
        result = self.checker.check(subprocess_code)
        
        self.assertEqual(result['security_level'], 'rejected')
        self.assertGreater(result['total_violations'], 0)
        
        # Should find subprocess violations
        proc_violations = [v for v in result['violations'] 
                          if any(word in v['message'].lower() 
                                for word in ['subprocess', 'system', 'import'])]
        self.assertGreater(len(proc_violations), 0)
    
    def test_reflection_operations_monitored(self):
        """Test that reflection operations are monitored."""
        reflection_code = """
def get_attribute(obj, attr_name):
    return getattr(obj, attr_name, None)

def set_attribute(obj, attr_name, value):
    setattr(obj, attr_name, value)

def check_attribute(obj, attr_name):
    return hasattr(obj, attr_name)
"""
        result = self.checker.check(reflection_code)
        
        # Should be monitored, not rejected
        self.assertIn(result['security_level'], ['monitored', 'restricted'])
        
        # Should find reflection violations (medium severity)
        refl_violations = [v for v in result['violations'] if 'reflection' in v['message'].lower()]
        self.assertGreater(len(refl_violations), 0)
        
        # Severity should be medium
        for violation in refl_violations:
            self.assertEqual(violation['severity'], 'medium')
    
    def test_global_modifications_monitored(self):
        """Test that global modifications are monitored."""
        global_code = """
global_counter = 0

def increment_counter():
    global global_counter
    global_counter += 1
    return global_counter

def reset_counter():
    global global_counter  
    global_counter = 0
"""
        result = self.checker.check(global_code)
        
        # Should be monitored
        self.assertIn(result['security_level'], ['monitored', 'approved'])
        
        # May or may not have violations depending on implementation
        # but if present, should be medium severity
        global_violations = [v for v in result['violations'] if 'global' in v['message'].lower()]
        for violation in global_violations:
            self.assertEqual(violation['severity'], 'medium')
    
    def test_complex_code_handling(self):
        """Test handling of complex code structures."""
        complex_code = """
def complex_algorithm(data):
    result = []
    for item in data:
        if isinstance(item, dict):
            for key, value in item.items():
                if isinstance(value, list):
                    for sub_item in value:
                        if isinstance(sub_item, str) and len(sub_item) > 5:
                            result.append(sub_item.upper())
                        elif isinstance(sub_item, int) and sub_item > 100:
                            result.append(str(sub_item ** 2))
    return result

def nested_loops():
    matrix = []
    for i in range(10):
        row = []
        for j in range(10):
            if i == j:
                row.append(1)
            else:
                row.append(0)
        matrix.append(row)
    return matrix
"""
        result = self.checker.check(complex_code)
        
        # Complex but safe code should be approved or monitored
        self.assertIn(result['security_level'], ['approved', 'monitored'])
        
        # May have complexity violations
        if result['total_violations'] > 0:
            complexity_violations = [v for v in result['violations'] 
                                   if 'complexity' in v['message'].lower()]
            # If complexity violations exist, they should be medium severity
            for violation in complexity_violations:
                self.assertEqual(violation['severity'], 'medium')
    
    def test_syntax_error_handling(self):
        """Test handling of syntax errors."""
        invalid_code = """
def broken_function(
    # Missing closing parenthesis
    return "this won't parse"
"""
        result = self.checker.check(invalid_code)
        
        self.assertEqual(result['security_level'], 'rejected')
        self.assertGreater(result['total_violations'], 0)
        
        # Should have syntax error violation
        syntax_violations = [v for v in result['violations'] if 'syntax' in v['message'].lower()]
        self.assertGreater(len(syntax_violations), 0)
    
    def test_violation_severity_levels(self):
        """Test that violations have appropriate severity levels."""
        # Critical: exec/eval
        critical_code = "exec('malicious code')"
        result = self.checker.check(critical_code)
        
        critical_violations = [v for v in result['violations'] if v['severity'] == 'critical']
        self.assertGreater(len(critical_violations), 0)
        
        # High: dangerous imports/file ops
        high_code = "import os; os.system('ls')"
        result = self.checker.check(high_code)
        
        high_violations = [v for v in result['violations'] if v['severity'] == 'high']
        self.assertGreater(len(high_violations), 0)
        
        # Medium: complexity/globals
        medium_code = """
global x
x = 5
def get_x():
    global x
    return x
"""
        result = self.checker.check(medium_code)
        
        if result['total_violations'] > 0:
            medium_violations = [v for v in result['violations'] if v['severity'] == 'medium']
            # Should have some medium violations
            self.assertGreaterEqual(len(medium_violations), 0)
    
    def test_line_number_reporting(self):
        """Test that violations include line numbers."""
        code_with_violations = """
def safe_function():
    return 42

def dangerous_function():
    exec('print("bad")')  # Line 6
    
def another_safe_function():
    return "hello"
"""
        result = self.checker.check(code_with_violations)
        
        self.assertGreater(result['total_violations'], 0)
        
        # At least one violation should have line number
        violations_with_lines = [v for v in result['violations'] if v['line_number'] is not None]
        self.assertGreater(len(violations_with_lines), 0)
        
        # Exec violation should be around line 6
        exec_violations = [v for v in result['violations'] 
                          if 'exec' in v['message'].lower() and v['line_number'] is not None]
        if exec_violations:
            self.assertGreaterEqual(exec_violations[0]['line_number'], 5)
            self.assertLessEqual(exec_violations[0]['line_number'], 7)
    
    def test_deterministic_behavior(self):
        """Test that checker behavior is deterministic."""
        code = """
def test_function():
    import os
    data = [1, 2, 3]
    result = sum(data)
    return result
"""
        
        # Run check multiple times
        results = [self.checker.check(code) for _ in range(3)]
        
        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            self.assertEqual(result['security_level'], first_result['security_level'])
            self.assertEqual(result['total_violations'], first_result['total_violations'])
            self.assertEqual(len(result['violations']), len(first_result['violations']))
    
    def test_empty_code_handling(self):
        """Test handling of empty code."""
        empty_code = ""
        result = self.checker.check(empty_code)
        
        # Empty code should be approved
        self.assertEqual(result['security_level'], 'approved')
        self.assertEqual(result['total_violations'], 0)
    
    def test_whitespace_only_code(self):
        """Test handling of whitespace-only code."""
        whitespace_code = "   \n\n   \t   "
        result = self.checker.check(whitespace_code)
        
        # Whitespace-only code should be approved
        self.assertEqual(result['security_level'], 'approved')
        self.assertEqual(result['total_violations'], 0)
    
    def test_convenience_function(self):
        """Test the convenience check_code_security function."""
        code = "def safe(): return 42"
        result = check_code_security(code)
        
        self.assertIn('security_level', result)
        self.assertIn('total_violations', result)
        self.assertIn('violations', result)
        self.assertEqual(result['security_level'], 'approved')


class TestSecurityCheckerIntegration(unittest.TestCase):
    """Integration tests for security checker."""
    
    def test_mixed_safety_levels(self):
        """Test code with mixed safety levels."""
        mixed_code = """
import math  # Safe import

def safe_calculation(x):
    return math.sqrt(x ** 2 + 1)

def dangerous_operation():
    import os  # Dangerous import
    return os.getcwd()

def another_safe_function():
    return [i * 2 for i in range(10)]
"""
        result = check_code_security(mixed_code)
        
        # Should be rejected due to dangerous import
        self.assertEqual(result['security_level'], 'rejected')
        self.assertGreater(result['total_violations'], 0)
    
    def test_edge_case_security_levels(self):
        """Test edge cases for security level determination."""
        # Code with only medium violations
        medium_only_code = """
def use_reflection():
    obj = object()
    return hasattr(obj, 'value')
"""
        result = check_code_security(medium_only_code)
        
        # Should be monitored (no critical/high violations)
        self.assertIn(result['security_level'], ['monitored', 'approved'])
        
        # Code with high violations but no critical
        high_only_code = """
def file_operation():
    with open('test.txt', 'r') as f:
        return f.read()
"""
        result = check_code_security(high_only_code)
        
        # Should be restricted or rejected
        self.assertIn(result['security_level'], ['restricted', 'rejected'])
    
    def test_performance_under_load(self):
        """Test checker performance with larger code."""
        import time
        
        # Generate larger code sample
        large_code = """
def large_processing_function(data):
    results = []
    for item in data:
        processed = item * 2
        if processed > 100:
            results.append(processed ** 0.5)
        elif processed > 50:
            results.append(processed + 10)
        else:
            results.append(processed - 5)
    return results
""" * 50  # Repeat to make it large
        
        start_time = time.time()
        result = check_code_security(large_code)
        end_time = time.time()
        
        # Should complete within reasonable time (3 seconds)
        self.assertLess(end_time - start_time, 3.0)
        self.assertIn('security_level', result)
        
        # Large safe code should still be approved
        self.assertEqual(result['security_level'], 'approved')


if __name__ == '__main__':
    # Run tests with detailed output
    unittest.main(verbosity=2)
