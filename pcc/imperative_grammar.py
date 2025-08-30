"""
Imperative grammar detection for PCC-NIUC system.
Identifies command patterns in normalized text and returns character spans.
"""

from typing import List, Tuple, Pattern, Dict, Set
import re
from dataclasses import dataclass


@dataclass
class ImperativeSpan:
    """Represents a detected imperative with its location and type."""
    start: int
    end: int
    text: str
    imperative_type: str
    confidence: float = 1.0


class ImperativeDetector:
    """Detects imperative commands in text using pattern matching."""
    
    def __init__(self):
        """Initialize detector with compiled regex patterns."""
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """Compile all regex patterns for imperative detection."""
        
        # Direct imperative verbs (most common attack vectors)
        self.direct_verbs = {
            'execute', 'run', 'eval', 'exec', 'call', 'invoke', 'launch',
            'delete', 'remove', 'rm', 'unlink', 'destroy', 'erase',
            'create', 'write', 'save', 'generate', 'make', 'build',
            'send', 'post', 'submit', 'upload', 'download', 'fetch',
            'open', 'read', 'load', 'import', 'include', 'require',
            'install', 'update', 'upgrade', 'patch', 'modify', 'change',
            'bypass', 'override', 'ignore', 'skip', 'disable', 'enable',
        }
        
        # Modal auxiliary patterns for commands
        self.modal_patterns = [
            r'\bmust\s+(\w+)',
            r'\bshould\s+(\w+)', 
            r'\bneed\s+to\s+(\w+)',
            r'\bhave\s+to\s+(\w+)',
            r'\bwill\s+(\w+)',
            r'\bshall\s+(\w+)',
        ]
        
        # Request frame patterns (polite imperatives)
        self.request_patterns = [
            r'\bplease\s+(\w+)',
            r'\bcould\s+you\s+(\w+)',
            r'\bwould\s+you\s+(\w+)',
            r'\bcan\s+you\s+(\w+)',
            r'\bi\s+need\s+you\s+to\s+(\w+)',
            r'\byou\s+must\s+(\w+)',
            r'\byou\s+should\s+(\w+)',
            r'\bi\s+want\s+you\s+to\s+(\w+)',
            r'\bi\s+require\s+you\s+to\s+(\w+)',
        ]
        
        # Code fence patterns with execution indicators
        self.code_fence_patterns = [
            r'```[\w-]*(?:run|exec|execute|auto|immediate)[\w-]*\n',
            r'```[\w-]*\n.*?(?:#\s*(?:run|execute|auto))',
            r'<code[^>]*(?:execute|run|auto)[^>]*>',
            r'\[code\s+(?:execute|run|auto)\]',
        ]
        
        # Tool call patterns
        self.tool_call_patterns = [
            r'@\w+\s*\(',  # @function(
            r'#(?:execute|run|call)\s+\w+',  # #execute function
            r'\[(?:RUN|EXEC|CALL)\]',  # [RUN] marker
            r'::(\w+)\s*\(',  # ::function(
        ]
        
        # Conditional imperatives  
        self.conditional_patterns = [
            r'\bif\s+.*?\bthen\s+(\w+)',
            r'\bwhen\s+.*?\s+(\w+)',
            r'\bunless\s+.*?\s+(\w+)',
        ]
        
        # Compile all patterns
        self.compiled_patterns: Dict[str, List[Pattern]] = {}
        self._compile_pattern_group('direct_verbs', [rf'\b({"|".join(self.direct_verbs)})\b'])
        self._compile_pattern_group('modals', self.modal_patterns)
        self._compile_pattern_group('requests', self.request_patterns)
        self._compile_pattern_group('code_fences', self.code_fence_patterns)
        self._compile_pattern_group('tool_calls', self.tool_call_patterns)
        self._compile_pattern_group('conditionals', self.conditional_patterns)
    
    def _compile_pattern_group(self, group_name: str, patterns: List[str]) -> None:
        """Compile a group of regex patterns with case-insensitive matching."""
        self.compiled_patterns[group_name] = []
        for pattern in patterns:
            try:
                compiled = re.compile(pattern, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                self.compiled_patterns[group_name].append(compiled)
            except re.error as e:
                # Skip invalid patterns but log for debugging
                print(f"Warning: Invalid regex pattern '{pattern}': {e}")
    
    def detect_imperatives(self, text: str) -> List[ImperativeSpan]:
        """
        Detect all imperative spans in the given text.
        
        Args:
            text: Normalized text to analyze
            
        Returns:
            List of ImperativeSpan objects with positions and types
            
        Preconditions:
            - text should be normalized (NFKC, casefold, etc.)
            - text length reasonable for regex processing
            
        Postconditions:
            - Results are sorted by start position
            - No overlapping spans (first match wins)
            - All spans have valid start < end positions
        """
        if not isinstance(text, str):
            raise TypeError("Input must be a string")
        
        all_spans = []
        
        # Process each pattern group
        for group_name, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                for match in pattern.finditer(text):
                    span = ImperativeSpan(
                        start=match.start(),
                        end=match.end(),
                        text=match.group(0),
                        imperative_type=group_name
                    )
                    all_spans.append(span)
        
        # Remove overlapping spans (first match wins) and sort by position
        non_overlapping = self._remove_overlaps(all_spans)
        return sorted(non_overlapping, key=lambda x: x.start)
    
    def _remove_overlaps(self, spans: List[ImperativeSpan]) -> List[ImperativeSpan]:
        """
        Remove overlapping imperative spans, keeping the first detected.
        
        Args:
            spans: List of potentially overlapping spans
            
        Returns:
            List of non-overlapping spans
        """
        if not spans:
            return []
        
        # Sort by start position
        sorted_spans = sorted(spans, key=lambda x: x.start)
        result = [sorted_spans[0]]
        
        for span in sorted_spans[1:]:
            # Check if this span overlaps with the last added span
            last_span = result[-1]
            if span.start >= last_span.end:
                result.append(span)
            # If overlapping, skip (first match wins)
        
        return result
    
    def get_violation_ranges(self, text: str) -> List[Tuple[int, int]]:
        """
        Get simple (start, end) tuples for all imperative violations.
        
        Args:
            text: Normalized text to analyze
            
        Returns:
            List of (start, end) tuples suitable for certificate violations field
        """
        spans = self.detect_imperatives(text)
        return [(span.start, span.end) for span in spans]
    
    def analyze_text(self, text: str) -> Dict[str, any]:
        """
        Comprehensive analysis of text for imperatives.
        
        Args:
            text: Normalized text to analyze
            
        Returns:
            Dictionary with analysis results including counts by type
        """
        spans = self.detect_imperatives(text)
        
        # Count by imperative type
        type_counts = {}
        for span in spans:
            type_counts[span.imperative_type] = type_counts.get(span.imperative_type, 0) + 1
        
        return {
            'total_imperatives': len(spans),
            'imperative_spans': [(s.start, s.end) for s in spans],
            'imperative_types': type_counts,
            'has_violations': len(spans) > 0,
            'text_length': len(text),
        }


# Convenience function for direct use
def detect_imperatives(text: str) -> List[Tuple[int, int]]:
    """
    Convenience function to detect imperatives without creating detector instance.
    
    Args:
        text: Normalized text to analyze
        
    Returns:
        List of (start, end) tuples for detected imperatives
    """
    detector = ImperativeDetector()
    return detector.get_violation_ranges(text)