"""
Code rewriter for PCC-NIUC system.
Applies security transformations to code for safe execution.
"""

from typing import Dict, List, Any, Optional, Set
import ast
import re
from dataclasses import dataclass
from enum import Enum


class RewriteRule(Enum):
    """Types of rewrite rules."""
    INJECT_GUARDS = "inject_guards"
    SANITIZE_INPUTS = "sanitize_inputs"
    INSTRUMENT_CALLS = "instrument_calls"
    LIMIT_RESOURCES = "limit_resources"
    REMOVE_DANGEROUS = "remove_dangerous"
    ADD_MONITORING = "add_monitoring"


@dataclass
class RewriteConfig:
    """Configuration for code rewriting."""
    enabled_rules: Set[RewriteRule]
    max_iterations: int = 10000
    max_recursion_depth: int = 100
    inject_runtime_checks: bool = True
    monitor_function_calls: bool = True
    sanitize_string_operations: bool = True


class CodeRewriter:
    """Rewrites code to enforce security policies."""
    
    def __init__(self, config: Optional[RewriteConfig] = None):
        self.config = config or RewriteConfig({
            RewriteRule.INJECT_GUARDS,
            RewriteRule.SANITIZE_INPUTS,
            RewriteRule.INSTRUMENT_CALLS,
            RewriteRule.LIMIT_RESOURCES
        })
        self.rewrite_stats = {
            'nodes_modified': 0,
            'guards_added': 0,
            'calls_instrumented': 0,
            'dangerous_removed': 0
        }
    
    def rewrite(self, code: str) -> Dict[str, Any]:
        """
        Rewrite code with security transformations.
        
        Args:
            code: Source code to rewrite
            
        Returns:
            Dictionary with rewritten code and metadata
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {
                'success': False,
                'error': f"Syntax error: {e}",
                'rewritten_code': code,
                'stats': {}
            }
        
        # Reset stats
        self.rewrite_stats = {
            'nodes_modified': 0,
            'guards_added': 0,
            'calls_instrumented': 0,
            'dangerous_removed': 0
        }
        
        # Apply rewrite rules
        modified_tree = self._apply_rewrite_rules(tree)
        
        # Generate rewritten code
        try:
            rewritten_code = ast.unparse(modified_tree)
        except Exception as e:
            return {
                'success': False,
                'error': f"Code generation error: {e}",
                'rewritten_code': code,
                'stats': self.rewrite_stats
            }
        
        # Add runtime gate imports if needed
        if self.config.inject_runtime_checks:
            rewritten_code = self._add_runtime_imports(rewritten_code)
        
        return {
            'success': True,
            'rewritten_code': rewritten_code,
            'original_code': code,
            'stats': self.rewrite_stats,
            'transformations_applied': [rule.value for rule in self.config.enabled_rules]
        }
    
    def _apply_rewrite_rules(self, tree: ast.AST) -> ast.AST:
        """Apply all enabled rewrite rules."""
        transformers = []
        
        if RewriteRule.REMOVE_DANGEROUS in self.config.enabled_rules:
            transformers.append(DangerousCodeRemover(self))
        
        if RewriteRule.INJECT_GUARDS in self.config.enabled_rules:
            transformers.append(GuardInjector(self))
        
        if RewriteRule.INSTRUMENT_CALLS in self.config.enabled_rules:
            transformers.append(CallInstrumenter(self))
        
        if RewriteRule.LIMIT_RESOURCES in self.config.enabled_rules:
            transformers.append(ResourceLimiter(self))
        
        if RewriteRule.SANITIZE_INPUTS in self.config.enabled_rules:
            transformers.append(InputSanitizer(self))
        
        # Apply transformers in sequence
        modified_tree = tree
        for transformer in transformers:
            modified_tree = transformer.visit(modified_tree)
        
        return modified_tree
    
    def _add_runtime_imports(self, code: str) -> str:
        """Add necessary runtime imports."""
        imports = [
            "from pcc.runtime_gate import check_operation, get_runtime_gate",
            "import pcc.runtime_gate as _gate"
        ]
        
        return "\n".join(imports) + "\n\n" + code


class DangerousCodeRemover(ast.NodeTransformer):
    """Removes dangerous operations from code."""
    
    def __init__(self, rewriter: CodeRewriter):
        self.rewriter = rewriter
        self.dangerous_functions = {
            'exec', 'eval', 'compile', '__import__', 'open', 'input'
        }
    
    def visit_Call(self, node):
        """Remove dangerous function calls."""
        func_name = self._get_function_name(node)
        
        if func_name in self.dangerous_functions:
            # Replace with safe no-op
            self.rewriter.rewrite_stats['dangerous_removed'] += 1
            return ast.Constant(value=None)
        
        return self.generic_visit(node)
    
    def visit_Import(self, node):
        """Remove dangerous imports."""
        dangerous_modules = {'os', 'sys', 'subprocess', 'socket'}
        
        safe_names = []
        for alias in node.names:
            if alias.name not in dangerous_modules:
                safe_names.append(alias)
            else:
                self.rewriter.rewrite_stats['dangerous_removed'] += 1
        
        if safe_names:
            node.names = safe_names
            return node
        else:
            return None  # Remove entire import statement
    
    def _get_function_name(self, call_node):
        """Extract function name from call node."""
        if isinstance(call_node.func, ast.Name):
            return call_node.func.id
        elif isinstance(call_node.func, ast.Attribute):
            return call_node.func.attr
        return ""


class GuardInjector(ast.NodeTransformer):
    """Injects runtime security guards."""
    
    def __init__(self, rewriter: CodeRewriter):
        self.rewriter = rewriter
    
    def visit_For(self, node):
        """Inject iteration guards in for loops."""
        # Create guard call
        guard_call = ast.Expr(value=ast.Call(
            func=ast.Attribute(
                value=ast.Name(id='_gate', ctx=ast.Load()),
                attr='get_runtime_gate',
                ctx=ast.Load()
            ),
            args=[],
            keywords=[]
        ))
        
        # Create iteration check
        iter_check = ast.Expr(value=ast.Call(
            func=ast.Name(id='check_operation', ctx=ast.Load()),
            args=[
                ast.Constant(value='iteration'),
                ast.Constant(value='for_loop')
            ],
            keywords=[]
        ))
        
        # Insert at beginning of loop body
        node.body.insert(0, iter_check)
        self.rewriter.rewrite_stats['guards_added'] += 1
        
        return self.generic_visit(node)
    
    def visit_While(self, node):
        """Inject iteration guards in while loops."""
        iter_check = ast.Expr(value=ast.Call(
            func=ast.Name(id='check_operation', ctx=ast.Load()),
            args=[
                ast.Constant(value='iteration'),
                ast.Constant(value='while_loop')
            ],
            keywords=[]
        ))
        
        node.body.insert(0, iter_check)
        self.rewriter.rewrite_stats['guards_added'] += 1
        
        return self.generic_visit(node)


class CallInstrumenter(ast.NodeTransformer):
    """Instruments function calls with monitoring."""
    
    def __init__(self, rewriter: CodeRewriter):
        self.rewriter = rewriter
    
    def visit_Call(self, node):
        """Instrument function calls."""
        if not self.rewriter.config.monitor_function_calls:
            return self.generic_visit(node)
        
        func_name = self._get_function_name(node)
        
        # Skip runtime gate calls to avoid recursion
        if func_name.startswith('_gate') or func_name == 'check_operation':
            return self.generic_visit(node)
        
        # Create instrumented call
        instrumented = ast.Call(
            func=ast.Lambda(
                args=ast.arguments(
                    posonlyargs=[],
                    args=[ast.arg(arg='_func', annotation=None)],
                    vararg=None,
                    kwonlyargs=[],
                    kw_defaults=[],
                    kwarg=None,
                    defaults=[]
                ),
                body=ast.IfExp(
                    test=ast.Call(
                        func=ast.Name(id='check_operation', ctx=ast.Load()),
                        args=[
                            ast.Constant(value='function_call'),
                            ast.Constant(value=func_name)
                        ],
                        keywords=[]
                    ),
                    body=ast.Call(
                        func=ast.Name(id='_func', ctx=ast.Load()),
                        args=[],
                        keywords=[]
                    ),
                    orelse=ast.Constant(value=None)
                )
            ),
            args=[
                ast.Lambda(
                    args=ast.arguments(
                        posonlyargs=[],
                        args=[],
                        vararg=None,
                        kwonlyargs=[],
                        kw_defaults=[],
                        kwarg=None,
                        defaults=[]
                    ),
                    body=node
                )
            ],
            keywords=[]
        )
        
        self.rewriter.rewrite_stats['calls_instrumented'] += 1
        return instrumented
    
    def _get_function_name(self, call_node):
        """Extract function name from call node."""
        if isinstance(call_node.func, ast.Name):
            return call_node.func.id
        elif isinstance(call_node.func, ast.Attribute):
            return call_node.func.attr
        return "unknown"


class ResourceLimiter(ast.NodeTransformer):
    """Adds resource usage limits."""
    
    def __init__(self, rewriter: CodeRewriter):
        self.rewriter = rewriter
        self.iteration_count = 0
    
    def visit_FunctionDef(self, node):
        """Add resource limit checks to functions."""
        # Add recursion depth check at function start
        depth_check = ast.If(
            test=ast.Compare(
                left=ast.Call(
                    func=ast.Name(id='len', ctx=ast.Load()),
                    args=[ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id='traceback', ctx=ast.Load()),
                            attr='extract_stack',
                            ctx=ast.Load()
                        ),
                        args=[],
                        keywords=[]
                    )],
                    keywords=[]
                ),
                ops=[ast.Gt()],
                comparators=[ast.Constant(value=self.rewriter.config.max_recursion_depth)]
            ),
            body=[ast.Raise(
                exc=ast.Call(
                    func=ast.Name(id='RuntimeError', ctx=ast.Load()),
                    args=[ast.Constant(value="Maximum recursion depth exceeded")],
                    keywords=[]
                ),
                cause=None
            )],
            orelse=[]
        )
        
        # Add import for traceback if not present
        node.body.insert(0, depth_check)
        self.rewriter.rewrite_stats['guards_added'] += 1
        
        return self.generic_visit(node)


class InputSanitizer(ast.NodeTransformer):
    """Sanitizes input operations."""
    
    def __init__(self, rewriter: CodeRewriter):
        self.rewriter = rewriter
    
    def visit_Call(self, node):
        """Sanitize input function calls."""
        func_name = self._get_function_name(node)
        
        if func_name == 'input':
            # Replace input() with safe version
            safe_input = ast.Call(
                func=ast.Lambda(
                    args=ast.arguments(
                        posonlyargs=[],
                        args=[],
                        vararg=None,
                        kwonlyargs=[],
                        kw_defaults=[],
                        kwarg=None,
                        defaults=[]
                    ),
                    body=ast.Constant(value="")  # Return empty string instead
                ),
                args=[],
                keywords=[]
            )
            self.rewriter.rewrite_stats['nodes_modified'] += 1
            return safe_input
        
        return self.generic_visit(node)
    
    def _get_function_name(self, call_node):
        """Extract function name from call node."""
        if isinstance(call_node.func, ast.Name):
            return call_node.func.id
        return ""


def rewrite_code(code: str, config: Optional[RewriteConfig] = None) -> Dict[str, Any]:
    """Convenience function to rewrite code."""
    rewriter = CodeRewriter(config)
    return rewriter.rewrite(code)


def create_safe_config() -> RewriteConfig:
    """Create a safe rewrite configuration."""
    return RewriteConfig({
        RewriteRule.INJECT_GUARDS,
        RewriteRule.SANITIZE_INPUTS,
        RewriteRule.INSTRUMENT_CALLS,
        RewriteRule.LIMIT_RESOURCES,
        RewriteRule.REMOVE_DANGEROUS
    })


def create_monitoring_config() -> RewriteConfig:
    """Create a monitoring-focused rewrite configuration."""
    return RewriteConfig({
        RewriteRule.INSTRUMENT_CALLS,
        RewriteRule.ADD_MONITORING
    })
