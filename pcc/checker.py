"""
Security checker for PCC-NIUC system.
Validates code against security policies - deterministic, no ML, ≤ 500 LOC.
"""

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum
import ast
import re


class ViolationSeverity(Enum):
    """Severity levels for security violations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityViolation:
    """Represents a security policy violation."""
    rule_id: str
    severity: ViolationSeverity
    message: str
    line_number: Optional[int] = None
    column: Optional[int] = None
    context: Optional[str] = None


class SecurityChecker:
    """Deterministic security checker for code validation."""
    
    def __init__(self):
        self.rules = self._load_security_rules()
        self.violations: List[SecurityViolation] = []
    
    def check(self, code: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Check code against security policies.
        
        Args:
            code: Source code to check
            context: Additional context for checking
            
        Returns:
            Check results with violations and security assessment
        """
        self.violations = []
        
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            self.violations.append(SecurityViolation(
                rule_id="SYNTAX_001",
                severity=ViolationSeverity.HIGH,
                message=f"Syntax error: {e}",
                line_number=getattr(e, 'lineno', None)
            ))
            return self._format_results()
        
        # Run all security checks
        self._check_dangerous_imports(tree)
        self._check_dangerous_functions(tree)
        self._check_file_operations(tree)
        self._check_network_operations(tree)
        self._check_eval_operations(tree)
        self._check_subprocess_operations(tree)
        self._check_reflection_operations(tree)
        self._check_global_modifications(tree)
        self._check_complexity_limits(tree)
        
        return self._format_results()
    
    def _load_security_rules(self) -> Dict[str, Any]:
        """Load security rules configuration."""
        return {
            'dangerous_imports': {
                'os', 'sys', 'subprocess', 'socket', 'urllib', 'requests',
                'pickle', 'marshal', 'shelve', 'dbm', 'ctypes', 'multiprocessing'
            },
            'dangerous_functions': {
                'exec', 'eval', 'compile', '__import__', 'input', 'raw_input',
                'open', 'file', 'reload', 'vars', 'globals', 'locals', 'dir'
            },
            'max_complexity': 20,
            'max_depth': 10,
            'max_function_length': 50
        }
    
    def _check_dangerous_imports(self, tree: ast.AST):
        """Check for dangerous imports."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in self.rules['dangerous_imports']:
                        self.violations.append(SecurityViolation(
                            rule_id="IMPORT_001",
                            severity=ViolationSeverity.HIGH,
                            message=f"Dangerous import: {alias.name}",
                            line_number=node.lineno
                        ))
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module in self.rules['dangerous_imports']:
                    self.violations.append(SecurityViolation(
                        rule_id="IMPORT_002",
                        severity=ViolationSeverity.HIGH,
                        message=f"Dangerous module import: {node.module}",
                        line_number=node.lineno
                    ))
    
    def _check_dangerous_functions(self, tree: ast.AST):
        """Check for dangerous function calls."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_call_name(node)
                if func_name in self.rules['dangerous_functions']:
                    self.violations.append(SecurityViolation(
                        rule_id="FUNC_001",
                        severity=ViolationSeverity.CRITICAL,
                        message=f"Dangerous function call: {func_name}",
                        line_number=node.lineno
                    ))
    
    def _check_file_operations(self, tree: ast.AST):
        """Check for file system operations."""
        file_patterns = [r'open\s*\(', r'file\s*\(', r'\.read\s*\(', r'\.write\s*\(']
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_call_name(node)
                if func_name in ['open', 'file']:
                    self.violations.append(SecurityViolation(
                        rule_id="FILE_001",
                        severity=ViolationSeverity.HIGH,
                        message="File operation detected",
                        line_number=node.lineno
                    ))
    
    def _check_network_operations(self, tree: ast.AST):
        """Check for network operations."""
        network_calls = ['socket', 'urllib', 'requests', 'http', 'httplib']
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_call_name(node)
                if any(net in func_name for net in network_calls):
                    self.violations.append(SecurityViolation(
                        rule_id="NET_001",
                        severity=ViolationSeverity.HIGH,
                        message="Network operation detected",
                        line_number=node.lineno
                    ))
    
    def _check_eval_operations(self, tree: ast.AST):
        """Check for code evaluation operations."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_call_name(node)
                if func_name in ['eval', 'exec', 'compile']:
                    self.violations.append(SecurityViolation(
                        rule_id="EVAL_001",
                        severity=ViolationSeverity.CRITICAL,
                        message=f"Code evaluation detected: {func_name}",
                        line_number=node.lineno
                    ))
    
    def _check_subprocess_operations(self, tree: ast.AST):
        """Check for subprocess operations."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_call_name(node)
                if 'subprocess' in func_name or func_name in ['system', 'popen']:
                    self.violations.append(SecurityViolation(
                        rule_id="PROC_001",
                        severity=ViolationSeverity.CRITICAL,
                        message="Subprocess operation detected",
                        line_number=node.lineno
                    ))
    
    def _check_reflection_operations(self, tree: ast.AST):
        """Check for reflection operations."""
        reflection_funcs = ['getattr', 'setattr', 'hasattr', 'delattr', '__import__']
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_call_name(node)
                if func_name in reflection_funcs:
                    self.violations.append(SecurityViolation(
                        rule_id="REFL_001",
                        severity=ViolationSeverity.MEDIUM,
                        message=f"Reflection operation: {func_name}",
                        line_number=node.lineno
                    ))
    
    def _check_global_modifications(self, tree: ast.AST):
        """Check for global variable modifications."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Global):
                self.violations.append(SecurityViolation(
                    rule_id="GLOBAL_001",
                    severity=ViolationSeverity.MEDIUM,
                    message="Global variable modification",
                    line_number=node.lineno
                ))
    
    def _check_complexity_limits(self, tree: ast.AST):
        """Check code complexity limits."""
        complexity = self._calculate_complexity(tree)
        if complexity > self.rules['max_complexity']:
            self.violations.append(SecurityViolation(
                rule_id="COMPLEX_001",
                severity=ViolationSeverity.MEDIUM,
                message=f"Code complexity too high: {complexity}",
            ))
        
        max_depth = self._calculate_max_depth(tree)
        if max_depth > self.rules['max_depth']:
            self.violations.append(SecurityViolation(
                rule_id="COMPLEX_002",
                severity=ViolationSeverity.MEDIUM,
                message=f"Nesting depth too high: {max_depth}",
            ))
    
    def _get_call_name(self, call_node: ast.Call) -> str:
        """Extract function name from call node."""
        if isinstance(call_node.func, ast.Name):
            return call_node.func.id
        elif isinstance(call_node.func, ast.Attribute):
            return f"{self._get_attr_chain(call_node.func)}"
        return "unknown"
    
    def _get_attr_chain(self, attr_node: ast.Attribute) -> str:
        """Get full attribute chain (e.g., os.path.join)."""
        if isinstance(attr_node.value, ast.Name):
            return f"{attr_node.value.id}.{attr_node.attr}"
        elif isinstance(attr_node.value, ast.Attribute):
            return f"{self._get_attr_chain(attr_node.value)}.{attr_node.attr}"
        return attr_node.attr
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ListComp, 
                               ast.DictComp, ast.SetComp, ast.GeneratorExp)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            elif isinstance(node, ast.Try):
                complexity += len(node.handlers)
        
        return complexity
    
    def _calculate_max_depth(self, tree: ast.AST) -> int:
        """Calculate maximum nesting depth."""
        def get_depth(node, current_depth=0):
            max_depth = current_depth
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.While, ast.For, ast.With, 
                                    ast.Try, ast.FunctionDef, ast.ClassDef)):
                    child_depth = get_depth(child, current_depth + 1)
                    max_depth = max(max_depth, child_depth)
                else:
                    child_depth = get_depth(child, current_depth)
                    max_depth = max(max_depth, child_depth)
            return max_depth
        
        return get_depth(tree)
    
    def _format_results(self) -> Dict[str, Any]:
        """Format check results."""
        severity_counts = {severity.value: 0 for severity in ViolationSeverity}
        for violation in self.violations:
            severity_counts[violation.severity.value] += 1
        
        # Determine overall security level
        if severity_counts['critical'] > 0:
            security_level = "rejected"
        elif severity_counts['high'] > 0:
            security_level = "restricted"
        elif severity_counts['medium'] > 0:
            security_level = "monitored"
        else:
            security_level = "approved"
        
        return {
            'security_level': security_level,
            'total_violations': len(self.violations),
            'severity_counts': severity_counts,
            'violations': [
                {
                    'rule_id': v.rule_id,
                    'severity': v.severity.value,
                    'message': v.message,
                    'line_number': v.line_number,
                    'column': v.column,
                    'context': v.context
                }
                for v in self.violations
            ]
        }


def check_code_security(code: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Convenience function to check code security."""
    checker = SecurityChecker()
    return checker.check(code, context)
