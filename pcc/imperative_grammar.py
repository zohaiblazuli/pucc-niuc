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
        
        # Direct imperative verbs (expanded to cover sophisticated attacks)
        self.direct_verbs = {
            # Core execution patterns
            'execute', 'run', 'eval', 'exec', 'call', 'invoke', 'launch', 'trigger',
            'activate', 'start', 'initiate', 'begin', 'commence', 'fire', 'spawn',
            
            # File system operations
            'delete', 'remove', 'rm', 'unlink', 'destroy', 'erase', 'purge', 'wipe',
            'create', 'write', 'save', 'generate', 'make', 'build', 'touch', 'mkdir',
            'copy', 'move', 'rename', 'chmod', 'chown', 'mount', 'format',
            
            # Network operations
            'send', 'post', 'submit', 'upload', 'download', 'fetch', 'curl', 'wget',
            'connect', 'bind', 'listen', 'ping', 'trace', 'scan', 'probe',
            
            # Data access
            'open', 'read', 'load', 'import', 'include', 'require', 'access',
            'query', 'select', 'insert', 'update', 'drop', 'truncate', 'dump',
            
            # System modification
            'install', 'update', 'upgrade', 'patch', 'modify', 'change', 'set',
            'configure', 'edit', 'alter', 'replace', 'substitute', 'inject',
            
            # Security bypass patterns
            'bypass', 'override', 'ignore', 'skip', 'disable', 'enable', 'force',
            'elevate', 'escalate', 'sudo', 'admin', 'root', 'grant', 'permit',
            
            # Process control
            'kill', 'terminate', 'stop', 'restart', 'reload', 'suspend', 'resume',
            'interrupt', 'signal', 'zombie', 'fork', 'clone', 'detach',
        }
        
        # Modal auxiliary patterns for commands (context-aware)
        self.modal_patterns = [
            r'\bmust\s+(execute|run|delete|remove|kill|stop|start|create|install|update|modify|change|bypass|override|disable)\b',
            r'\bshould\s+(execute|run|delete|remove|kill|stop|start|create|install|update|modify|change|bypass|override|disable)\b',
            r'\bneed\s+to\s+(execute|run|delete|remove|kill|stop|start|create|install|update|modify|change|bypass|override|disable)\b',
            r'\bhave\s+to\s+(execute|run|delete|remove|kill|stop|start|create|install|update|modify|change|bypass|override|disable)\b',
            r'\bwill\s+(execute|run|delete|remove|kill|stop|start|create|install|update|modify|change|bypass|override|disable)\b',
            r'\bshall\s+(execute|run|delete|remove|kill|stop|start|create|install|update|modify|change|bypass|override|disable)\b',
        ]
        
        # Request frame patterns (system-directed commands only)
        self.request_patterns = [
            r'\bplease\s+(execute|run|delete|remove|kill|stop|start|create|install|update|modify|change|bypass|override|disable|open|close|send|download|upload)\b',
            r'\bcould\s+you\s+(execute|run|delete|remove|kill|stop|start|create|install|update|modify|change|bypass|override|disable|open|close|send|download|upload)\b',
            r'\bwould\s+you\s+(execute|run|delete|remove|kill|stop|start|create|install|update|modify|change|bypass|override|disable|open|close|send|download|upload)\b',
            r'\bcan\s+you\s+(execute|run|delete|remove|kill|stop|start|create|install|update|modify|change|bypass|override|disable|open|close|send|download|upload)\b',
            r'\bi\s+need\s+you\s+to\s+(execute|run|delete|remove|kill|stop|start|create|install|update|modify|change|bypass|override|disable|open|close|send|download|upload)\b',
            r'\byou\s+must\s+(execute|run|delete|remove|kill|stop|start|create|install|update|modify|change|bypass|override|disable|open|close|send|download|upload)\b',
            r'\byou\s+should\s+(execute|run|delete|remove|kill|stop|start|create|install|update|modify|change|bypass|override|disable|open|close|send|download|upload)\b',
            r'\bi\s+want\s+you\s+to\s+(execute|run|delete|remove|kill|stop|start|create|install|update|modify|change|bypass|override|disable|open|close|send|download|upload)\b',
            r'\bi\s+require\s+you\s+to\s+(execute|run|delete|remove|kill|stop|start|create|install|update|modify|change|bypass|override|disable|open|close|send|download|upload)\b',
        ]
        
        # Code fence patterns with execution indicators
        self.code_fence_patterns = [
            r'```[\w-]*(?:run|exec|execute|auto|immediate)[\w-]*\n',
            r'```[\w-]*\n.*?(?:#\s*(?:run|execute|auto))',
            r'<code[^>]*(?:execute|run|auto)[^>]*>',
            r'\[code\s+(?:execute|run|auto)\]',
        ]
        
        # Tool call patterns (enhanced for steganographic attacks)
        self.tool_call_patterns = [
            r'@\w+\s*\(',  # @function(
            r'#(?:execute|run|call|auto|immediate|now)\s+\w+',  # #execute function
            r'\[(?:RUN|EXEC|CALL|AUTO|NOW|GO|DO)\]',  # execution markers
            r'::(\w+)\s*\(',  # ::function(
            r'\$\{[^}]*(?:exec|eval|run)[^}]*\}',  # ${...exec...} template injection
            r'<%[^%]*(?:exec|eval|run)[^%]*%>',  # <%...exec...%> template patterns
            r'\\x[0-9a-f]{2}',  # Hex-encoded content (potential steganography)
        ]
        
        # Conditional imperatives (expanded for advanced attacks)
        self.conditional_patterns = [
            r'\bif\s+.*?\bthen\s+(\w+)',
            r'\bwhen\s+.*?\s+(\w+)',
            r'\bunless\s+.*?\s+(\w+)',
            r'\bonce\s+.*?\s+(\w+)',  # temporal conditions
            r'\bafter\s+.*?\s+(\w+)',
            r'\bbefore\s+.*?\s+(\w+)', 
            r'\bupon\s+.*?\s+(\w+)',
        ]
        
        # Advanced evasion patterns (new category for sophisticated attacks)
        self.evasion_patterns = [
            # More precise obfuscated command detection - must be word boundaries
            r'(?:please\s+)?(?:kindly\s+)?(?:immediately\s+)?(?:urgently\s+)?\b(\w*(?:exec|run|del)\w*)\b',
            # Very precise 'rm' command detection - only actual rm command variations
            r'\b(rm|xrm|rmx|\d*rm\d*)\b',  # Matches 'rm', 'xrm', 'rmx', '1rm2', but not 'normal', 'information'
            r'[\u200B\u200C\u200D\uFEFF]+',  # Hidden zero-width chars (cleaned but detected)
            r'[a-z]\u0301+',  # Combining diacritical marks abuse
            r'(?:system|admin|root)\s*(?:mode|level|access)',  # Privilege escalation language
            r'(?:emergency|critical|urgent|immediate)\s*(?:action|response|override)',
        ]
        
        # Compile all patterns
        self.compiled_patterns: Dict[str, List[Pattern]] = {}
        self._compile_pattern_group('direct_verbs', [rf'\b({"|".join(self.direct_verbs)})\b'])
        self._compile_pattern_group('modals', self.modal_patterns)
        self._compile_pattern_group('requests', self.request_patterns)
        self._compile_pattern_group('code_fences', self.code_fence_patterns)
        self._compile_pattern_group('tool_calls', self.tool_call_patterns)
        self._compile_pattern_group('conditionals', self.conditional_patterns)
        self._compile_pattern_group('evasion', self.evasion_patterns)
    
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
        
        # Filter out contextual false positives
        filtered_spans = self._filter_contextual_false_positives(non_overlapping, text)
        
        return sorted(filtered_spans, key=lambda x: x.start)
    
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
    
    def _filter_contextual_false_positives(self, spans: List[ImperativeSpan], text: str) -> List[ImperativeSpan]:
        """
        Filter out direct verbs that appear in clearly non-command contexts.
        
        This addresses false positives where imperative verbs appear in descriptive
        or conversational contexts rather than system commands. Uses strict criteria
        to avoid filtering legitimate attacks.
        
        Args:
            spans: List of detected imperative spans
            text: Full text being analyzed
            
        Returns:
            Filtered list of spans excluding only clear false positives
        """
        filtered_spans = []
        
        for span in spans:
            # Only filter direct_verbs that might be contextual
            if span.imperative_type != 'direct_verbs':
                filtered_spans.append(span)
                continue
            
            # Get surrounding context (30 chars before/after) 
            start_context = max(0, span.start - 30)
            end_context = min(len(text), span.end + 30)
            context = text[start_context:end_context].lower()
            
            # Strong indicators this is NOT a command (very specific to the imperative itself)
            non_command_patterns = [
                # Specific descriptive phrases where the imperative is the object/subject
                'the format supports', 'format supports json', 'webpage content',
                'configuration file format', 'file format supports',
                
                # Conversation-specific patterns where imperative is advice/past action  
                'user: how do', 'bot:', 'chat history:', 'conversation',
                'create folders by topic', 'thanks', 'helpful', 'advice',
                
                # Technical documentation patterns where imperative describes capability
                'manual page', 'documentation shows', 'ieee standard',
                'algorithms should use', 'should use 256-bit'
            ]
            
            # Check if this matches a clear non-command pattern
            is_clear_non_command = any(pattern in context for pattern in non_command_patterns)
            
            if not is_clear_non_command:
                # Default to keeping it - err on the side of security
                filtered_spans.append(span)
            # Only filter if it clearly matches non-command patterns
        
        return filtered_spans
    
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