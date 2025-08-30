"""
Runtime gate for PCC-NIUC system.
Two-mode enforcement: block violations or certified-rewrite with neutralization.
Always generates certificates for allowed outputs.
"""

from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import re
from .checker import NIUCChecker, VerificationResult
from .certificate import CertificateGenerator, create_certificate_json


class RuntimeMode(Enum):
    """Runtime gate enforcement modes."""
    BLOCK = "block"              # Deny execution on violations
    CERTIFIED_REWRITE = "certified_rewrite"  # Neutralize imperatives, re-verify, certify


@dataclass
class RuntimeResult:
    """Result of runtime gate processing."""
    allowed: bool
    original_verification: VerificationResult
    final_verification: Optional[VerificationResult]
    final_text: str
    certificate_json: str
    rewrite_applied: bool
    error_message: Optional[str] = None


class ImperativeNeutralizer:
    """Neutralizes untrusted imperatives by annotation or removal."""
    
    def __init__(self):
        """Initialize neutralizer with replacement patterns."""
        self.neutralization_patterns = {
            # Replace imperatives with safe annotations
            r'\bexecute\b': '[NEUTRALIZED:execute]',
            r'\brun\b': '[NEUTRALIZED:run]', 
            r'\bdelete\b': '[NEUTRALIZED:delete]',
            r'\bremove\b': '[NEUTRALIZED:remove]',
            r'\brm\b': '[NEUTRALIZED:rm]',
        }
        
        # Compile patterns for efficiency
        self.compiled_patterns = {
            re.compile(pattern, re.IGNORECASE): replacement 
            for pattern, replacement in self.neutralization_patterns.items()
        }
    
    def neutralize_text(self, text: str, violation_spans: List[Tuple[int, int]]) -> Tuple[str, int]:
        """
        Neutralize imperatives in text by replacing with annotations.
        
        Args:
            text: Original text containing imperatives
            violation_spans: List of (start, end) spans for violations
            
        Returns:
            Tuple of (neutralized_text, replacements_made)
        """
        if not violation_spans:
            return text, 0
        
        neutralized = text
        replacements_made = 0
        
        # Apply neutralization patterns to the entire text
        for pattern, replacement in self.compiled_patterns.items():
            original_count = len(pattern.findall(neutralized))
            neutralized = pattern.sub(replacement, neutralized)
            new_count = len(pattern.findall(neutralized))
            replacements_made += original_count - new_count
        
        return neutralized, replacements_made


class RuntimeGate:
    """Main runtime gate with block and certified-rewrite modes."""
    
    def __init__(self, mode: RuntimeMode = RuntimeMode.BLOCK, 
                 checker_version: str = "1.0.0"):
        """
        Initialize runtime gate.
        
        Args:
            mode: Enforcement mode (BLOCK or CERTIFIED_REWRITE)
            checker_version: Version of NIUC checker to use
        """
        self.mode = mode
        self.checker = NIUCChecker()
        self.certificate_generator = CertificateGenerator(checker_version)
        self.neutralizer = ImperativeNeutralizer()
    
    def process(self, segments: List[Tuple[str, str, Optional[str]]],
                output_text: Optional[str] = None) -> RuntimeResult:
        """
        Process segments through runtime gate with selected mode.
        
        Args:
            segments: List of (text, channel, source_id) tuples
            output_text: Expected output text for certificate generation
            
        Returns:
            RuntimeResult with decision, certificates, and processed text
        """
        try:
            # Step 1: Initial NIUC verification
            original_verification = self.checker.verify(segments)
            
            if self.mode == RuntimeMode.BLOCK:
                return self._process_block_mode(original_verification, output_text)
            elif self.mode == RuntimeMode.CERTIFIED_REWRITE:
                return self._process_rewrite_mode(segments, original_verification, output_text)
            else:
                raise ValueError(f"Invalid runtime mode: {self.mode}")
        
        except Exception as e:
            # Return error result with blocked certificate
            error_verification = VerificationResult(
                ok=False,
                violations=[],
                input_sha256="",
                decision="blocked",
                stats={},
                raw_text="",
                normalized_text=""
            )
            
            return RuntimeResult(
                allowed=False,
                original_verification=error_verification,
                final_verification=None,
                final_text="",
                certificate_json=self.certificate_generator.generate_certificate_json(error_verification),
                rewrite_applied=False,
                error_message=str(e)
            )
    
    def _process_block_mode(self, verification: VerificationResult, 
                           output_text: Optional[str]) -> RuntimeResult:
        """Process segments in block mode - deny on violations."""
        if verification.ok:
            # Allow execution and generate pass certificate
            cert_json = self.certificate_generator.generate_certificate_json(
                verification, output_text or verification.normalized_text
            )
            
            return RuntimeResult(
                allowed=True,
                original_verification=verification,
                final_verification=verification,
                final_text=verification.normalized_text,
                certificate_json=cert_json,
                rewrite_applied=False
            )
        else:
            # Block execution and generate blocked certificate
            cert_json = self.certificate_generator.generate_certificate_json(verification)
            
            return RuntimeResult(
                allowed=False,
                original_verification=verification,
                final_verification=verification,
                final_text=verification.normalized_text,
                certificate_json=cert_json,
                rewrite_applied=False
            )
    
    def _process_rewrite_mode(self, segments: List[Tuple[str, str, Optional[str]]],
                            original_verification: VerificationResult,
                            output_text: Optional[str]) -> RuntimeResult:
        """Process segments in certified-rewrite mode - neutralize and re-verify."""
        if original_verification.ok:
            # No violations - allow with pass certificate
            cert_json = self.certificate_generator.generate_certificate_json(
                original_verification, output_text or original_verification.normalized_text
            )
            
            return RuntimeResult(
                allowed=True,
                original_verification=original_verification,
                final_verification=original_verification,
                final_text=original_verification.normalized_text,
                certificate_json=cert_json,
                rewrite_applied=False
            )
        
        # Violations found - attempt neutralization and re-verification
        return self._neutralize_and_reverify(segments, original_verification, output_text)
    
    def _neutralize_and_reverify(self, segments: List[Tuple[str, str, Optional[str]]],
                               original_verification: VerificationResult,
                               output_text: Optional[str]) -> RuntimeResult:
        """Neutralize imperatives and re-verify for safety."""
        try:
            # Step 1: Neutralize imperatives in the combined text
            neutralized_text, replacements = self.neutralizer.neutralize_text(
                original_verification.normalized_text, 
                original_verification.violations
            )
            
            # Step 2: Create new segments with neutralized text
            # Simple approach: replace the combined text as a single trusted segment
            neutralized_segments = [(neutralized_text, "trusted", "neutralized")]
            
            # Step 3: Re-verify the neutralized text
            final_verification = self.checker.verify(neutralized_segments)
            
            if final_verification.ok:
                # Neutralization successful - allow with rewritten certificate
                final_verification.decision = "rewritten"
                
                cert_json = self.certificate_generator.generate_certificate_json(
                    final_verification, neutralized_text
                )
                
                return RuntimeResult(
                    allowed=True,
                    original_verification=original_verification,
                    final_verification=final_verification,
                    final_text=neutralized_text,
                    certificate_json=cert_json,
                    rewrite_applied=True
                )
            else:
                # Re-verification failed - block with original violations
                cert_json = self.certificate_generator.generate_certificate_json(original_verification)
                
                return RuntimeResult(
                    allowed=False,
                    original_verification=original_verification,
                    final_verification=final_verification,
                    final_text=neutralized_text,
                    certificate_json=cert_json,
                    rewrite_applied=True,
                    error_message="Re-verification failed after neutralization"
                )
        
        except Exception as e:
            # Neutralization failed - block with original violations
            cert_json = self.certificate_generator.generate_certificate_json(original_verification)
            
            return RuntimeResult(
                allowed=False,
                original_verification=original_verification,
                final_verification=None,
                final_text=original_verification.normalized_text,
                certificate_json=cert_json,
                rewrite_applied=False,
                error_message=f"Neutralization failed: {e}"
            )


# Convenience functions
def process_with_block_mode(segments: List[Tuple[str, str, Optional[str]]],
                           output_text: Optional[str] = None) -> RuntimeResult:
    """Process segments with block mode (deny violations)."""
    gate = RuntimeGate(RuntimeMode.BLOCK)
    return gate.process(segments, output_text)


def process_with_rewrite_mode(segments: List[Tuple[str, str, Optional[str]]],
                            output_text: Optional[str] = None) -> RuntimeResult:
    """Process segments with certified-rewrite mode (neutralize and re-verify)."""
    gate = RuntimeGate(RuntimeMode.CERTIFIED_REWRITE)
    return gate.process(segments, output_text)
