"""
Certificate generation for PCC-NIUC system.
Implements certificate.json schema from docs/certificate-spec.md with helper functions.
"""

from typing import Dict, List, Tuple, Any, Optional
import hashlib
import json
import time
from dataclasses import dataclass
from .checker import VerificationResult


@dataclass
class CertificateData:
    """Certificate data structure matching docs/certificate-spec.md schema."""
    checker_version: str
    input_sha256: str
    output_sha256: str
    decision: str  # "pass" | "blocked" | "rewritten"
    violations: List[Tuple[int, int]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "checker_version": self.checker_version,
            "input_sha256": self.input_sha256,
            "output_sha256": self.output_sha256,
            "decision": self.decision,
            "violations": self.violations
        }
    
    def to_json(self, indent: Optional[int] = None) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, separators=(',', ':'), sort_keys=True)


class CertificateHasher:
    """Helper functions for computing certificate hashes."""
    
    @staticmethod
    def compute_input_hash(normalized_text: str) -> str:
        """
        Compute SHA-256 hash of normalized input text.
        
        Args:
            normalized_text: Text after normalization pipeline (NFKC, casefold, etc.)
            
        Returns:
            64-character lowercase hexadecimal SHA-256 hash
        """
        if not isinstance(normalized_text, str):
            raise TypeError("Input must be a string")
        return hashlib.sha256(normalized_text.encode('utf-8')).hexdigest().lower()
    
    @staticmethod
    def compute_output_hash_pass(output_text: str) -> str:
        """
        Compute SHA-256 hash for passed computation output.
        
        Args:
            output_text: Actual computation result
            
        Returns:
            SHA-256 hash of the output
        """
        if not isinstance(output_text, str):
            raise TypeError("Output must be a string")
        return hashlib.sha256(output_text.encode('utf-8')).hexdigest().lower()
    
    @staticmethod
    def compute_output_hash_blocked() -> str:
        """
        Compute SHA-256 hash for blocked computation (always empty string).
        
        Returns:
            SHA-256 hash of empty string (constant)
        """
        return hashlib.sha256(b'').hexdigest().lower()
        # Returns: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    
    @staticmethod
    def compute_output_hash_rewritten(rewritten_text: str) -> str:
        """
        Compute SHA-256 hash for rewritten computation output.
        
        Args:
            rewritten_text: Sanitized/rewritten computation result
            
        Returns:
            SHA-256 hash of the rewritten output
        """
        if not isinstance(rewritten_text, str):
            raise TypeError("Rewritten text must be a string")
        return hashlib.sha256(rewritten_text.encode('utf-8')).hexdigest().lower()


class CertificateGenerator:
    """Generates certificates from verification results."""
    
    def __init__(self, checker_version: str = "1.0.0"):
        """
        Initialize certificate generator.
        
        Args:
            checker_version: Version of the NIUC checker
        """
        self.checker_version = checker_version
        self.hasher = CertificateHasher()
    
    def generate_certificate(self, verification_result: VerificationResult, 
                           output_text: Optional[str] = None) -> CertificateData:
        """
        Generate certificate from verification result.
        
        Args:
            verification_result: Result from NIUC checker
            output_text: Actual output text (for pass/rewritten decisions)
            
        Returns:
            CertificateData object
            
        Preconditions:
            - verification_result is valid VerificationResult
            - output_text provided if decision is "pass" or "rewritten"
            
        Postconditions:
            - Certificate matches docs/certificate-spec.md schema
            - Output hash computed correctly for decision type
        """
        # Compute output hash based on decision type
        decision = verification_result.decision
        
        if decision == "pass":
            if output_text is None:
                raise ValueError("Output text required for pass decision")
            output_hash = self.hasher.compute_output_hash_pass(output_text)
        elif decision == "blocked":
            output_hash = self.hasher.compute_output_hash_blocked()
        elif decision == "rewritten":
            if output_text is None:
                raise ValueError("Rewritten text required for rewritten decision")  
            output_hash = self.hasher.compute_output_hash_rewritten(output_text)
        else:
            raise ValueError(f"Invalid decision: {decision}")
        
        return CertificateData(
            checker_version=self.checker_version,
            input_sha256=verification_result.input_sha256,
            output_sha256=output_hash,
            decision=decision,
            violations=[[start, end] for start, end in verification_result.violations]
        )
    
    def generate_certificate_dict(self, verification_result: VerificationResult,
                                output_text: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate certificate as dictionary.
        
        Args:
            verification_result: Result from NIUC checker
            output_text: Actual output text (for pass/rewritten decisions)
            
        Returns:
            Certificate dictionary ready for JSON serialization
        """
        cert = self.generate_certificate(verification_result, output_text)
        return cert.to_dict()
    
    def generate_certificate_json(self, verification_result: VerificationResult,
                                output_text: Optional[str] = None,
                                indent: Optional[int] = None) -> str:
        """
        Generate certificate as JSON string.
        
        Args:
            verification_result: Result from NIUC checker
            output_text: Actual output text (for pass/rewritten decisions)
            indent: JSON indentation (None for compact)
            
        Returns:
            Certificate JSON string
        """
        cert = self.generate_certificate(verification_result, output_text)
        return cert.to_json(indent=indent)


class CertificateValidator:
    """Validates certificate integrity and format."""
    
    @staticmethod
    def validate_certificate_structure(cert_dict: Dict[str, Any]) -> bool:
        """
        Validate certificate has correct structure per schema.
        
        Args:
            cert_dict: Certificate dictionary to validate
            
        Returns:
            True if structure is valid, False otherwise
        """
        required_fields = ["checker_version", "input_sha256", "output_sha256", "decision", "violations"]
        
        # Check all required fields present
        if not all(field in cert_dict for field in required_fields):
            return False
        
        # Validate field types
        if not isinstance(cert_dict["checker_version"], str):
            return False
        if not isinstance(cert_dict["input_sha256"], str):
            return False  
        if not isinstance(cert_dict["output_sha256"], str):
            return False
        if cert_dict["decision"] not in ["pass", "blocked", "rewritten"]:
            return False
        if not isinstance(cert_dict["violations"], list):
            return False
        
        # Validate SHA-256 hash format (64 hex characters)
        import re
        hash_pattern = re.compile(r'^[a-f0-9]{64}$')
        if not hash_pattern.match(cert_dict["input_sha256"]):
            return False
        if not hash_pattern.match(cert_dict["output_sha256"]):
            return False
        
        # Validate violations format
        for violation in cert_dict["violations"]:
            if not isinstance(violation, list) or len(violation) != 2:
                return False
            if not isinstance(violation[0], int) or not isinstance(violation[1], int):
                return False
            if violation[0] >= violation[1] or violation[0] < 0:
                return False
        
        return True
    
    @staticmethod 
    def validate_certificate_semantics(cert_dict: Dict[str, Any]) -> bool:
        """
        Validate certificate semantic consistency.
        
        Args:
            cert_dict: Certificate dictionary to validate
            
        Returns:
            True if semantics are consistent, False otherwise
        """
        decision = cert_dict["decision"]
        violations = cert_dict["violations"]
        output_hash = cert_dict["output_sha256"]
        
        # Pass decisions must have no violations
        if decision == "pass" and len(violations) > 0:
            return False
        
        # Blocked/rewritten decisions must have violations
        if decision in ["blocked", "rewritten"] and len(violations) == 0:
            return False
        
        # Blocked decisions must hash empty string
        empty_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        if decision == "blocked" and output_hash != empty_hash:
            return False
        
        return True
    
    @classmethod
    def validate_certificate(cls, cert_dict: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Complete certificate validation.
        
        Args:
            cert_dict: Certificate dictionary to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not cls.validate_certificate_structure(cert_dict):
            return False, "Invalid certificate structure"
        
        if not cls.validate_certificate_semantics(cert_dict):
            return False, "Invalid certificate semantics"
        
        return True, None


# Convenience functions
def create_certificate(verification_result: VerificationResult, 
                      output_text: Optional[str] = None,
                      checker_version: str = "1.0.0") -> Dict[str, Any]:
    """
    Convenience function to create certificate dictionary.
    
    Args:
        verification_result: Result from NIUC checker
        output_text: Actual output text (for pass/rewritten decisions)
        checker_version: Version of the NIUC checker
        
    Returns:
        Certificate dictionary
    """
    generator = CertificateGenerator(checker_version)
    return generator.generate_certificate_dict(verification_result, output_text)


def create_certificate_json(verification_result: VerificationResult,
                           output_text: Optional[str] = None,
                           checker_version: str = "1.0.0",
                           indent: Optional[int] = 2) -> str:
    """
    Convenience function to create certificate JSON string.
    
    Args:
        verification_result: Result from NIUC checker
        output_text: Actual output text (for pass/rewritten decisions)
        checker_version: Version of the NIUC checker  
        indent: JSON indentation
        
    Returns:
        Certificate JSON string
    """
    generator = CertificateGenerator(checker_version)
    return generator.generate_certificate_json(verification_result, output_text, indent)


def validate_certificate_json(cert_json: str) -> Tuple[bool, Optional[str]]:
    """
    Validate certificate JSON string.
    
    Args:
        cert_json: Certificate JSON to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        cert_dict = json.loads(cert_json)
        return CertificateValidator.validate_certificate(cert_dict)
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"