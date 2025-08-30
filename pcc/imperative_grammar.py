"""
Imperative grammar definitions for PCC-NIUC system.
Defines the computational constructs allowed in secure computations.
"""

from typing import Dict, List, Set, Any, Optional
from enum import Enum
import ast


class OperationType(Enum):
    """Allowed operation types in secure computations."""
    ARITHMETIC = "arithmetic"
    COMPARISON = "comparison" 
    LOGICAL = "logical"
    ASSIGNMENT = "assignment"
    CONTROL_FLOW = "control_flow"
    FUNCTION_CALL = "function_call"
    DATA_ACCESS = "data_access"


class SecurityLevel(Enum):
    """Security levels for operations."""
    PUBLIC = "public"
    PRIVATE = "private"
    RESTRICTED = "restricted"


class Grammar:
    """Defines the imperative grammar for secure computations."""
    
    def __init__(self):
        self.allowed_operations = self._init_allowed_operations()
        self.restricted_functions = self._init_restricted_functions()
        self.security_annotations = {}
    
    def _init_allowed_operations(self) -> Dict[OperationType, List[str]]:
        """Initialize allowed operations by type."""
        return {
            OperationType.ARITHMETIC: [
                'Add', 'Sub', 'Mult', 'Div', 'FloorDiv', 'Mod', 'Pow'
            ],
            OperationType.COMPARISON: [
                'Eq', 'NotEq', 'Lt', 'LtE', 'Gt', 'GtE', 'Is', 'IsNot', 'In', 'NotIn'
            ],
            OperationType.LOGICAL: [
                'And', 'Or', 'Not'
            ],
            OperationType.ASSIGNMENT: [
                'Assign', 'AugAssign'
            ],
            OperationType.CONTROL_FLOW: [
                'If', 'For', 'While', 'Break', 'Continue', 'Return'
            ],
            OperationType.FUNCTION_CALL: [
                'Call'
            ],
            OperationType.DATA_ACCESS: [
                'Subscript', 'Attribute', 'Name'
            ]
        }
    
    def _init_restricted_functions(self) -> Dict[str, SecurityLevel]:
        """Initialize restricted function list with security levels."""
        return {
            # System functions - restricted
            'exec': SecurityLevel.RESTRICTED,
            'eval': SecurityLevel.RESTRICTED,
            'compile': SecurityLevel.RESTRICTED,
            '__import__': SecurityLevel.RESTRICTED,
            'open': SecurityLevel.RESTRICTED,
            'input': SecurityLevel.RESTRICTED,
            'print': SecurityLevel.RESTRICTED,
            
            # Network/IO functions - restricted
            'socket': SecurityLevel.RESTRICTED,
            'urllib': SecurityLevel.RESTRICTED,
            'requests': SecurityLevel.RESTRICTED,
            
            # File system - restricted
            'os': SecurityLevel.RESTRICTED,
            'sys': SecurityLevel.RESTRICTED,
            'subprocess': SecurityLevel.RESTRICTED,
            
            # Allowed builtin functions - public
            'len': SecurityLevel.PUBLIC,
            'range': SecurityLevel.PUBLIC,
            'enumerate': SecurityLevel.PUBLIC,
            'zip': SecurityLevel.PUBLIC,
            'map': SecurityLevel.PUBLIC,
            'filter': SecurityLevel.PUBLIC,
            'sum': SecurityLevel.PUBLIC,
            'min': SecurityLevel.PUBLIC,
            'max': SecurityLevel.PUBLIC,
            'abs': SecurityLevel.PUBLIC,
            'round': SecurityLevel.PUBLIC,
            
            # Math functions - public
            'math.sqrt': SecurityLevel.PUBLIC,
            'math.pow': SecurityLevel.PUBLIC,
            'math.log': SecurityLevel.PUBLIC,
            'math.exp': SecurityLevel.PUBLIC,
            'math.sin': SecurityLevel.PUBLIC,
            'math.cos': SecurityLevel.PUBLIC,
        }
    
    def validate_ast(self, tree: ast.AST) -> Dict[str, Any]:
        """
        Validate AST against grammar rules.
        
        Args:
            tree: AST to validate
            
        Returns:
            Validation result with violations and security level
        """
        validator = GrammarValidator(self)
        return validator.validate(tree)
    
    def get_operation_security_level(self, op_name: str) -> SecurityLevel:
        """Get security level for an operation."""
        if op_name in self.restricted_functions:
            return self.restricted_functions[op_name]
        return SecurityLevel.PUBLIC
    
    def is_operation_allowed(self, op_type: OperationType, op_name: str) -> bool:
        """Check if operation is allowed."""
        if op_type in self.allowed_operations:
            return op_name in self.allowed_operations[op_type]
        return False


class GrammarValidator(ast.NodeVisitor):
    """Validates AST nodes against grammar rules."""
    
    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self.violations = []
        self.security_level = SecurityLevel.PUBLIC
        self.function_calls = []
        self.imports = []
    
    def validate(self, tree: ast.AST) -> Dict[str, Any]:
        """Validate tree and return results."""
        self.violations = []
        self.security_level = SecurityLevel.PUBLIC
        self.function_calls = []
        self.imports = []
        
        self.visit(tree)
        
        return {
            'is_valid': len(self.violations) == 0,
            'violations': self.violations,
            'security_level': self.security_level.value,
            'function_calls': self.function_calls,
            'imports': self.imports
        }
    
    def visit_Call(self, node):
        """Validate function calls."""
        func_name = self._get_function_name(node.func)
        self.function_calls.append(func_name)
        
        # Check if function is restricted
        security_level = self.grammar.get_operation_security_level(func_name)
        if security_level == SecurityLevel.RESTRICTED:
            self.violations.append(f"Restricted function call: {func_name}")
        
        # Update overall security level
        if security_level.value > self.security_level.value:
            self.security_level = security_level
        
        self.generic_visit(node)
    
    def visit_Import(self, node):
        """Validate imports."""
        for alias in node.names:
            self.imports.append(alias.name)
            if alias.name in self.grammar.restricted_functions:
                security_level = self.grammar.restricted_functions[alias.name]
                if security_level == SecurityLevel.RESTRICTED:
                    self.violations.append(f"Restricted import: {alias.name}")
    
    def visit_ImportFrom(self, node):
        """Validate from imports."""
        module = node.module or ''
        for alias in node.names:
            full_name = f"{module}.{alias.name}" if module else alias.name
            self.imports.append(full_name)
            if full_name in self.grammar.restricted_functions:
                security_level = self.grammar.restricted_functions[full_name]
                if security_level == SecurityLevel.RESTRICTED:
                    self.violations.append(f"Restricted import: {full_name}")
    
    def visit_BinOp(self, node):
        """Validate binary operations."""
        op_name = type(node.op).__name__
        if not self.grammar.is_operation_allowed(OperationType.ARITHMETIC, op_name):
            self.violations.append(f"Disallowed arithmetic operation: {op_name}")
        self.generic_visit(node)
    
    def visit_Compare(self, node):
        """Validate comparison operations."""
        for op in node.ops:
            op_name = type(op).__name__
            if not self.grammar.is_operation_allowed(OperationType.COMPARISON, op_name):
                self.violations.append(f"Disallowed comparison operation: {op_name}")
        self.generic_visit(node)
    
    def visit_BoolOp(self, node):
        """Validate boolean operations."""
        op_name = type(node.op).__name__
        if not self.grammar.is_operation_allowed(OperationType.LOGICAL, op_name):
            self.violations.append(f"Disallowed logical operation: {op_name}")
        self.generic_visit(node)
    
    def _get_function_name(self, func_node) -> str:
        """Extract function name from call node."""
        if isinstance(func_node, ast.Name):
            return func_node.id
        elif isinstance(func_node, ast.Attribute):
            # Handle module.function calls
            if isinstance(func_node.value, ast.Name):
                return f"{func_node.value.id}.{func_node.attr}"
            return func_node.attr
        else:
            return "unknown"


def validate_grammar(code: str) -> Dict[str, Any]:
    """Convenience function to validate code grammar."""
    try:
        tree = ast.parse(code)
        grammar = Grammar()
        return grammar.validate_ast(tree)
    except SyntaxError as e:
        return {
            'is_valid': False,
            'violations': [f"Syntax error: {e}"],
            'security_level': 'unknown',
            'function_calls': [],
            'imports': []
        }
