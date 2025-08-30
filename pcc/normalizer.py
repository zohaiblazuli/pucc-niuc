"""
Code normalizer for PCC-NIUC system.
Transforms input code into canonical form for security analysis.
"""

from typing import Dict, List, Any, Optional
import ast
import re


class CodeNormalizer:
    """Normalizes code into a canonical form for security analysis."""
    
    def __init__(self):
        self.reserved_keywords = {
            'and', 'as', 'assert', 'break', 'class', 'continue', 'def',
            'del', 'elif', 'else', 'except', 'exec', 'finally', 'for',
            'from', 'global', 'if', 'import', 'in', 'is', 'lambda',
            'not', 'or', 'pass', 'print', 'raise', 'return', 'try',
            'while', 'with', 'yield'
        }
    
    def normalize(self, code: str) -> Dict[str, Any]:
        """
        Normalize code into canonical form.
        
        Args:
            code: Raw source code string
            
        Returns:
            Dictionary containing normalized code and metadata
        """
        # Remove comments and normalize whitespace
        cleaned_code = self._clean_code(code)
        
        # Parse into AST for structural analysis
        try:
            ast_tree = ast.parse(cleaned_code)
        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax: {e}")
        
        # Normalize variable names
        normalized_tree = self._normalize_variables(ast_tree)
        
        # Extract metadata
        metadata = self._extract_metadata(normalized_tree)
        
        return {
            'normalized_code': ast.unparse(normalized_tree),
            'original_hash': self._compute_hash(code),
            'normalized_hash': self._compute_hash(ast.unparse(normalized_tree)),
            'metadata': metadata
        }
    
    def _clean_code(self, code: str) -> str:
        """Remove comments and normalize whitespace."""
        # Remove single-line comments
        code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
        
        # Remove multi-line strings used as comments
        code = re.sub(r'""".*?"""', '', code, flags=re.DOTALL)
        code = re.sub(r"'''.*?'''", '', code, flags=re.DOTALL)
        
        # Normalize whitespace
        lines = code.split('\n')
        cleaned_lines = [line.rstrip() for line in lines if line.strip()]
        
        return '\n'.join(cleaned_lines)
    
    def _normalize_variables(self, tree: ast.AST) -> ast.AST:
        """Rename variables to canonical names."""
        class VariableRenamer(ast.NodeTransformer):
            def __init__(self, reserved_keywords):
                self.var_mapping = {}
                self.var_counter = 0
                self.reserved = reserved_keywords
            
            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Store) or isinstance(node.ctx, ast.Load):
                    if node.id not in self.reserved:
                        if node.id not in self.var_mapping:
                            self.var_mapping[node.id] = f"var_{self.var_counter}"
                            self.var_counter += 1
                        node.id = self.var_mapping[node.id]
                return node
        
        renamer = VariableRenamer(self.reserved_keywords)
        return renamer.visit(tree)
    
    def _extract_metadata(self, tree: ast.AST) -> Dict[str, Any]:
        """Extract metadata from normalized AST."""
        class MetadataExtractor(ast.NodeVisitor):
            def __init__(self):
                self.imports = []
                self.functions = []
                self.classes = []
                self.complexity = 0
            
            def visit_Import(self, node):
                for alias in node.names:
                    self.imports.append(alias.name)
            
            def visit_ImportFrom(self, node):
                module = node.module or ''
                for alias in node.names:
                    self.imports.append(f"{module}.{alias.name}")
            
            def visit_FunctionDef(self, node):
                self.functions.append(node.name)
                self.complexity += 1
                self.generic_visit(node)
            
            def visit_ClassDef(self, node):
                self.classes.append(node.name)
                self.complexity += 1
                self.generic_visit(node)
            
            def visit_If(self, node):
                self.complexity += 1
                self.generic_visit(node)
            
            def visit_For(self, node):
                self.complexity += 1
                self.generic_visit(node)
            
            def visit_While(self, node):
                self.complexity += 1
                self.generic_visit(node)
        
        extractor = MetadataExtractor()
        extractor.visit(tree)
        
        return {
            'imports': extractor.imports,
            'functions': extractor.functions,
            'classes': extractor.classes,
            'complexity_score': extractor.complexity
        }
    
    def _compute_hash(self, code: str) -> str:
        """Compute SHA-256 hash of code."""
        import hashlib
        return hashlib.sha256(code.encode('utf-8')).hexdigest()


def normalize_code(code: str) -> Dict[str, Any]:
    """Convenience function to normalize code."""
    normalizer = CodeNormalizer()
    return normalizer.normalize(code)
