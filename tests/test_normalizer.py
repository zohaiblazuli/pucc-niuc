"""
Tests for the normalizer module.
Tests code normalization functionality for PCC-NIUC system.
"""

import unittest
import sys
import os

# Add pcc module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pcc.normalizer import CodeNormalizer, normalize_code


class TestCodeNormalizer(unittest.TestCase):
    """Test cases for CodeNormalizer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.normalizer = CodeNormalizer()
    
    def test_basic_normalization(self):
        """Test basic code normalization."""
        code = """
def hello_world():
    # This is a comment
    x = 5
    y = 10
    return x + y
"""
        result = self.normalizer.normalize(code)
        
        self.assertIn('normalized_code', result)
        self.assertIn('original_hash', result)
        self.assertIn('normalized_hash', result)
        self.assertIn('metadata', result)
        
        # Check that comments are removed
        self.assertNotIn('#', result['normalized_code'])
        
        # Check that function name is preserved
        self.assertIn('hello_world', result['normalized_code'])
    
    def test_variable_renaming(self):
        """Test variable normalization."""
        code = """
my_var = 42
another_variable = "hello"
result = my_var + len(another_variable)
"""
        result = self.normalizer.normalize(code)
        normalized_code = result['normalized_code']
        
        # Variables should be renamed to var_0, var_1, etc.
        self.assertIn('var_0', normalized_code)
        self.assertIn('var_1', normalized_code)
        
        # Original variable names should not be present
        self.assertNotIn('my_var', normalized_code)
        self.assertNotIn('another_variable', normalized_code)
    
    def test_reserved_keywords_preserved(self):
        """Test that reserved keywords are not renamed."""
        code = """
if True:
    for i in range(10):
        if i > 5:
            break
        else:
            continue
"""
        result = self.normalizer.normalize(code)
        normalized_code = result['normalized_code']
        
        # Reserved keywords should be preserved
        keywords = ['if', 'True', 'for', 'in', 'range', 'break', 'else', 'continue']
        for keyword in keywords:
            self.assertIn(keyword, normalized_code)
    
    def test_metadata_extraction(self):
        """Test metadata extraction."""
        code = """
import math
import os

class Calculator:
    def __init__(self):
        pass
    
    def add(self, a, b):
        return a + b
    
    def complex_operation(self, x):
        if x > 0:
            for i in range(x):
                if i % 2 == 0:
                    x += i
        return x

def standalone_function():
    return "hello"
"""
        result = self.normalizer.normalize(code)
        metadata = result['metadata']
        
        # Check imports
        self.assertIn('math', metadata['imports'])
        self.assertIn('os', metadata['imports'])
        
        # Check classes
        self.assertIn('Calculator', metadata['classes'])
        
        # Check functions (including methods)
        self.assertIn('__init__', metadata['functions'])
        self.assertIn('add', metadata['functions'])
        self.assertIn('complex_operation', metadata['functions'])
        self.assertIn('standalone_function', metadata['functions'])
        
        # Complexity should be > 1 due to control structures
        self.assertGreater(metadata['complexity_score'], 1)
    
    def test_comment_removal(self):
        """Test comment removal functionality."""
        code = """
# Single line comment
def function():
    '''
    Multi-line comment
    with multiple lines
    '''
    x = 5  # Inline comment
    return x
"""
        result = self.normalizer.normalize(code)
        normalized_code = result['normalized_code']
        
        # Comments should be removed
        self.assertNotIn('#', normalized_code)
        self.assertNotIn('Single line comment', normalized_code)
        self.assertNotIn('Multi-line comment', normalized_code)
        self.assertNotIn('Inline comment', normalized_code)
    
    def test_whitespace_normalization(self):
        """Test whitespace normalization."""
        code = """
def  messy_function  (  ):
    
    
    x    =     5
    
    return    x
    
"""
        result = self.normalizer.normalize(code)
        normalized_code = result['normalized_code']
        
        # Should not contain excessive whitespace
        self.assertNotIn('    =     ', normalized_code)
        self.assertNotIn('  messy_function  ', normalized_code)
        
        # Should maintain proper Python structure
        self.assertIn('def messy_function', normalized_code)
    
    def test_syntax_error_handling(self):
        """Test handling of syntax errors."""
        invalid_code = """
def invalid_function(
    # Missing closing parenthesis and colon
    return "invalid"
"""
        with self.assertRaises(ValueError) as context:
            self.normalizer.normalize(invalid_code)
        
        self.assertIn("Invalid Python syntax", str(context.exception))
    
    def test_hash_computation(self):
        """Test hash computation consistency."""
        code1 = "x = 5"
        code2 = "x = 5"  # Same code
        code3 = "y = 5"  # Different variable name
        
        result1 = self.normalizer.normalize(code1)
        result2 = self.normalizer.normalize(code2)
        result3 = self.normalizer.normalize(code3)
        
        # Same code should produce same normalized hash
        self.assertEqual(result1['normalized_hash'], result2['normalized_hash'])
        
        # Different code should produce same normalized hash if semantically equivalent
        # (after variable renaming)
        self.assertEqual(result1['normalized_hash'], result3['normalized_hash'])
        
        # Original hashes should be different for different code
        self.assertNotEqual(result1['original_hash'], result3['original_hash'])
    
    def test_complex_code_structures(self):
        """Test normalization of complex code structures."""
        code = """
class ComplexClass:
    def __init__(self, param1, param2):
        self.data = {param1: param2}
    
    def process_data(self):
        result = []
        for key, value in self.data.items():
            if isinstance(value, str):
                processed = [char.upper() for char in value if char.isalpha()]
                result.extend(processed)
        return result
    
    @property
    def data_size(self):
        return len(self.data)

def lambda_test():
    numbers = [1, 2, 3, 4, 5]
    filtered = list(filter(lambda x: x > 2, numbers))
    mapped = list(map(lambda x: x * 2, filtered))
    return mapped
"""
        result = self.normalizer.normalize(code)
        
        # Should not raise exceptions
        self.assertIn('normalized_code', result)
        self.assertIn('metadata', result)
        
        # Check that complex structures are preserved
        normalized = result['normalized_code']
        self.assertIn('class', normalized)
        self.assertIn('def', normalized)
        self.assertIn('lambda', normalized)
        self.assertIn('property', normalized)
    
    def test_empty_code(self):
        """Test normalization of empty code."""
        code = ""
        result = self.normalizer.normalize(code)
        
        self.assertEqual(result['normalized_code'], "")
        self.assertEqual(len(result['metadata']['imports']), 0)
        self.assertEqual(len(result['metadata']['functions']), 0)
        self.assertEqual(result['metadata']['complexity_score'], 0)
    
    def test_convenience_function(self):
        """Test the convenience normalize_code function."""
        code = "def test(): return 42"
        result = normalize_code(code)
        
        self.assertIn('normalized_code', result)
        self.assertIn('original_hash', result)
        self.assertIn('normalized_hash', result)
        self.assertIn('metadata', result)


class TestNormalizerIntegration(unittest.TestCase):
    """Integration tests for normalizer."""
    
    def test_normalization_deterministic(self):
        """Test that normalization is deterministic."""
        code = """
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
"""
        
        # Run normalization multiple times
        results = [normalize_code(code) for _ in range(3)]
        
        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            self.assertEqual(result['normalized_code'], first_result['normalized_code'])
            self.assertEqual(result['normalized_hash'], first_result['normalized_hash'])
            self.assertEqual(result['metadata'], first_result['metadata'])
    
    def test_functionally_equivalent_code(self):
        """Test that functionally equivalent code normalizes to same result."""
        code1 = """
def add_numbers(first_number, second_number):
    total = first_number + second_number
    return total
"""
        
        code2 = """
def add_numbers(x, y):
    # Different variable names but same logic
    sum_result = x + y
    return sum_result
"""
        
        result1 = normalize_code(code1)
        result2 = normalize_code(code2)
        
        # Normalized code should be identical (same variable renaming)
        self.assertEqual(result1['normalized_code'], result2['normalized_code'])
        self.assertEqual(result1['normalized_hash'], result2['normalized_hash'])
    
    def test_performance_reasonable(self):
        """Test that normalization performance is reasonable."""
        import time
        
        # Generate medium-sized code
        code = """
def large_function():
    data = []
    for i in range(100):
        if i % 2 == 0:
            data.append(i * 2)
        else:
            data.append(i + 1)
    
    processed = []
    for item in data:
        if item > 50:
            processed.append(item ** 2)
        elif item > 25:
            processed.append(item * 3)
        else:
            processed.append(item)
    
    return sum(processed)
""" * 10  # Repeat to make it larger
        
        start_time = time.time()
        result = normalize_code(code)
        end_time = time.time()
        
        # Should complete within reasonable time (2 seconds)
        self.assertLess(end_time - start_time, 2.0)
        self.assertIn('normalized_code', result)


if __name__ == '__main__':
    # Run tests with detailed output
    unittest.main(verbosity=2)
