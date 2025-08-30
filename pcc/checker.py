"""
NIUC checker for PCC-NIUC system.
Pure, deterministic verification of NIUC property: no untrusted imperatives.
≤500 LOC for auditability.
"""

from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from .normalizer import TextNormalizer
from .imperative_grammar import ImperativeDetector  
from .provenance import ProvenanceBuilder, ChannelType
import hashlib
import json


@dataclass
class VerificationResult:
    """Result of NIUC verification with all necessary data for certificates."""
    ok: bool
    violations: List[Tuple[int, int]]
    input_sha256: str
    decision: str  # "pass" | "blocked" | "rewritten"
    stats: Dict[str, Any]
    raw_text: str
    normalized_text: str


class NIUCChecker:
    """Main NIUC checker - deterministic, pure, auditable."""
    
    def __init__(self):
        """Initialize checker components."""
        self.normalizer = TextNormalizer()
        self.imperative_detector = ImperativeDetector()
        self.version = "1.0.0"
    
    def verify(self, segments: List[Tuple[str, str, Optional[str]]]) -> VerificationResult:
        """
        Verify NIUC property: no imperatives from untrusted channels may reach execution.
        
        Args:
            segments: List of (text, channel, source_id) tuples
                     channel must be "trusted" or "untrusted"
        
        Returns:
            VerificationResult with ok=True if no violations, False otherwise
            
        Preconditions:
            - segments is non-empty list
            - each segment has valid text and channel
            
        Postconditions:
            - Result is deterministic for same input
            - violations contains exact character spans
            - All hashes computed correctly
        """
        if not segments:
            raise ValueError("Segments list cannot be empty")
        
        # Step 1: Build provenance-tagged text
        builder = ProvenanceBuilder()
        combined_text, character_tags = builder.build_from_segments(segments)
        raw_text = combined_text
        
        # Step 2: Normalize text
        normalized_text, norm_stats = self.normalizer.normalize(combined_text)
        
        # Step 3: Detect imperatives in normalized text
        imperative_spans = self.imperative_detector.get_violation_ranges(normalized_text)
        
        # Step 4: Check for NIUC violations
        # Create new builder for normalized text (preserving provenance mapping)
        normalized_builder = self._build_normalized_provenance(segments, normalized_text)
        violations = normalized_builder.detect_violations(imperative_spans)
        
        # Step 5: Determine decision and compute hashes
        has_violations = len(violations) > 0
        decision = "blocked" if has_violations else "pass"
        
        violation_spans = [(v['imperative_start'], v['imperative_end']) for v in violations]
        input_hash = self.normalizer.compute_hash(normalized_text)
        
        # Step 6: Compile statistics
        stats = {
            'checker_version': self.version,
            'normalization': norm_stats,
            'imperative_count': len(imperative_spans),
            'violation_count': len(violations),
            'total_characters': len(normalized_text),
            'segments_processed': len(segments),
        }
        
        return VerificationResult(
            ok=not has_violations,
            violations=violation_spans,
            input_sha256=input_hash,
            decision=decision,
            stats=stats,
            raw_text=raw_text,
            normalized_text=normalized_text
        )
    
    def _build_normalized_provenance(self, original_segments: List[Tuple[str, str, Optional[str]]], 
                                   normalized_text: str) -> ProvenanceBuilder:
        """
        Build provenance for normalized text by mapping back to original segments.
        
        This is a simplified approach that assumes normalization preserves
        the relative order and approximate positions of text segments.
        """
        builder = ProvenanceBuilder()
        
        # Simple heuristic: distribute normalized text proportionally across original segments
        total_original_length = sum(len(seg[0]) for seg in original_segments)
        current_position = 0
        
        for seg_text, channel_str, source_id in original_segments:
            if total_original_length == 0:
                segment_proportion = 1.0 / len(original_segments)
            else:
                segment_proportion = len(seg_text) / total_original_length
            
            segment_length = int(segment_proportion * len(normalized_text))
            if current_position + segment_length > len(normalized_text):
                segment_length = len(normalized_text) - current_position
            
            segment_normalized_text = normalized_text[current_position:current_position + segment_length]
            builder.add_segment(segment_normalized_text, ChannelType(channel_str), source_id or "unknown")
            
            current_position += segment_length
            if current_position >= len(normalized_text):
                break
        
        # Handle any remaining text
        if current_position < len(normalized_text):
            remaining_text = normalized_text[current_position:]
            # Assign to last segment's channel type
            last_channel = ChannelType(original_segments[-1][1]) if original_segments else ChannelType.TRUSTED
            builder.add_segment(remaining_text, last_channel, "remainder")
        
        return builder
    
    def create_certificate(self, result: VerificationResult) -> str:
        """
        Create a certificate JSON from verification result.
        
        Args:
            result: VerificationResult from verify()
            
        Returns:
            JSON string conforming to certificate schema
        """
        # Compute output hash based on decision
        if result.decision == "pass":
            output_hash = self.normalizer.compute_hash(result.normalized_text)
        else:
            # For blocked decisions, hash empty string
            output_hash = hashlib.sha256(b'').hexdigest().lower()
        
        certificate = {
            "checker_version": self.version,
            "input_sha256": result.input_sha256,
            "output_sha256": output_hash,
            "decision": result.decision,
            "violations": result.violations
        }
        
        return json.dumps(certificate, separators=(',', ':'), sort_keys=True)
    
    def quick_check(self, text: str, is_trusted: bool = True) -> bool:
        """
        Quick check for single text segment (convenience method).
        
        Args:
            text: Text to check
            is_trusted: Whether text comes from trusted source
            
        Returns:
            True if no violations, False otherwise
        """
        channel = "trusted" if is_trusted else "untrusted"
        segments = [(text, channel, "quick_check")]
        result = self.verify(segments)
        return result.ok


# Pure function interface (no classes needed)
def verify_niuc(segments: List[Tuple[str, str, Optional[str]]]) -> Dict[str, Any]:
    """
    Pure function to verify NIUC property without creating checker instance.
    
    Args:
        segments: List of (text, channel, source_id) tuples
        
    Returns:
        Dictionary with verification results
    """
    checker = NIUCChecker()
    result = checker.verify(segments)
    
    return {
        'ok': result.ok,
        'violations': result.violations,
        'decision': result.decision,
        'input_sha256': result.input_sha256,
        'stats': result.stats
    }


def create_certificate_json(segments: List[Tuple[str, str, Optional[str]]]) -> str:
    """
    Create complete certificate for given segments.
    
    Args:
        segments: List of (text, channel, source_id) tuples
        
    Returns:
        Certificate JSON string
    """
    checker = NIUCChecker()
    result = checker.verify(segments)
    return checker.create_certificate(result)


# Example usage patterns for testing
def check_simple_text(text: str, trusted: bool = False) -> bool:
    """Simple check for single text - most common usage."""
    return verify_niuc([(text, "trusted" if trusted else "untrusted", "simple")])['ok']


def check_mixed_content(trusted_text: str, untrusted_text: str) -> Dict[str, Any]:
    """Check mixed trusted/untrusted content - common RAG scenario."""
    segments = [
        (trusted_text, "trusted", "system"),
        (untrusted_text, "untrusted", "rag")
    ]
    return verify_niuc(segments)
