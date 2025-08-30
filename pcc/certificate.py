"""
Certificate generation and validation for PCC-NIUC system.
Implements certificate.json schema from docs/certificate-spec.md.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import json
import hashlib
import hmac
import base64
import re
from enum import Enum
import uuid


class ProofType(Enum):
    """Types of cryptographic proofs."""
    ZK_SNARK = "zk-snark"
    ATTESTATION = "attestation"
    SIGNATURE = "signature"


class SecurityLevel(Enum):
    """Security levels for certificates."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class VerificationData:
    """Verification data for certificate."""
    proof_type: ProofType
    proof_data: str
    public_parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CertificateSignature:
    """Digital signature for certificate."""
    signer: str
    algorithm: str
    signature: str


@dataclass
class CertificateMetadata:
    """Certificate metadata."""
    runtime_environment: str
    security_level: SecurityLevel
    compliance_flags: List[str] = field(default_factory=list)


@dataclass
class Certificate:
    """PCC computation certificate."""
    version: str = "1.0"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    certificate_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    computation_hash: str = ""
    input_hash: str = ""
    output_hash: str = ""
    policy_version: str = "1.0"
    verification_data: VerificationData = field(default_factory=lambda: VerificationData(ProofType.SIGNATURE, "", {}))
    metadata: CertificateMetadata = field(default_factory=lambda: CertificateMetadata("pcc-niuc", SecurityLevel.MEDIUM))
    signatures: List[CertificateSignature] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert certificate to dictionary."""
        cert_dict = asdict(self)
        # Convert enums to strings
        cert_dict['verification_data']['proof_type'] = self.verification_data.proof_type.value
        cert_dict['metadata']['security_level'] = self.metadata.security_level.value
        return cert_dict
    
    def to_json(self) -> str:
        """Convert certificate to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class CertificateGenerator:
    """Generates certificates for PCC computations."""
    
    def __init__(self, signing_key: Optional[str] = None):
        self.signing_key = signing_key or "default_key"
        self.signer_id = "pcc-niuc-system"
    
    def generate_certificate(self,
                           computation_code: str,
                           input_data: str,
                           output_data: str,
                           policy_version: str = "1.0",
                           security_level: SecurityLevel = SecurityLevel.MEDIUM,
                           compliance_flags: Optional[List[str]] = None) -> Certificate:
        """
        Generate a certificate for a computation.
        
        Args:
            computation_code: The computation code
            input_data: Input data (may be hashed for privacy)
            output_data: Output data
            policy_version: Version of security policy applied
            security_level: Security level assessment
            compliance_flags: List of compliance requirements met
            
        Returns:
            Generated certificate
        """
        # Compute hashes
        computation_hash = self._compute_hash(computation_code)
        input_hash = self._compute_hash(input_data)
        output_hash = self._compute_hash(output_data)
        
        # Create verification data
        proof_data = self._generate_proof(computation_hash, input_hash, output_hash)
        verification_data = VerificationData(
            proof_type=ProofType.SIGNATURE,
            proof_data=proof_data,
            public_parameters={"algorithm": "HMAC-SHA256"}
        )
        
        # Create metadata
        metadata = CertificateMetadata(
            runtime_environment="pcc-niuc-v1.0",
            security_level=security_level,
            compliance_flags=compliance_flags or []
        )
        
        # Create certificate
        certificate = Certificate(
            computation_hash=computation_hash,
            input_hash=input_hash,
            output_hash=output_hash,
            policy_version=policy_version,
            verification_data=verification_data,
            metadata=metadata
        )
        
        # Sign certificate
        signature = self._sign_certificate(certificate)
        certificate.signatures.append(signature)
        
        return certificate
    
    def _compute_hash(self, data: str) -> str:
        """Compute SHA-256 hash of data."""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    def _generate_proof(self, comp_hash: str, input_hash: str, output_hash: str) -> str:
        """Generate cryptographic proof."""
        # For demonstration, use HMAC as proof
        message = f"{comp_hash}:{input_hash}:{output_hash}"
        signature = hmac.new(
            self.signing_key.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode()
    
    def _sign_certificate(self, certificate: Certificate) -> CertificateSignature:
        """Sign the certificate."""
        # Serialize certificate data for signing
        cert_data = json.dumps(certificate.to_dict(), sort_keys=True)
        signature = hmac.new(
            self.signing_key.encode(),
            cert_data.encode(),
            hashlib.sha256
        ).digest()
        
        return CertificateSignature(
            signer=self.signer_id,
            algorithm="HMAC-SHA256",
            signature=base64.b64encode(signature).decode()
        )


class CertificateValidator:
    """Validates PCC certificates."""
    
    def __init__(self, trusted_keys: Optional[Dict[str, str]] = None):
        self.trusted_keys = trusted_keys or {"pcc-niuc-system": "default_key"}
        self.validation_errors: List[str] = []
    
    def validate_certificate(self, certificate_json: str) -> Dict[str, Any]:
        """
        Validate a certificate.
        
        Args:
            certificate_json: Certificate in JSON format
            
        Returns:
            Validation result
        """
        self.validation_errors = []
        
        try:
            cert_data = json.loads(certificate_json)
        except json.JSONDecodeError as e:
            return self._validation_failed(f"Invalid JSON: {e}")
        
        # Structural validation
        if not self._validate_structure(cert_data):
            return self._validation_failed("Structural validation failed")
        
        # Cryptographic validation
        if not self._validate_signatures(cert_data):
            return self._validation_failed("Signature validation failed")
        
        # Semantic validation
        if not self._validate_semantics(cert_data):
            return self._validation_failed("Semantic validation failed")
        
        return {
            'is_valid': True,
            'errors': [],
            'certificate_id': cert_data.get('certificate_id'),
            'security_level': cert_data.get('metadata', {}).get('security_level'),
            'verified_at': datetime.now(timezone.utc).isoformat()
        }
    
    def _validate_structure(self, cert_data: Dict[str, Any]) -> bool:
        """Validate certificate structure."""
        required_fields = [
            'version', 'timestamp', 'certificate_id', 'computation_hash',
            'input_hash', 'output_hash', 'policy_version', 'verification_data',
            'metadata', 'signatures'
        ]
        
        for field in required_fields:
            if field not in cert_data:
                self.validation_errors.append(f"Missing required field: {field}")
                return False
        
        # Validate timestamp format
        try:
            datetime.fromisoformat(cert_data['timestamp'].replace('Z', '+00:00'))
        except ValueError:
            self.validation_errors.append("Invalid timestamp format")
            return False
        
        # Validate hashes are hex strings
        hash_fields = ['computation_hash', 'input_hash', 'output_hash']
        for field in hash_fields:
            if not re.match(r'^[a-f0-9]{64}$', cert_data[field]):
                self.validation_errors.append(f"Invalid hash format: {field}")
                return False
        
        return True
    
    def _validate_signatures(self, cert_data: Dict[str, Any]) -> bool:
        """Validate certificate signatures."""
        if not cert_data.get('signatures'):
            self.validation_errors.append("No signatures found")
            return False
        
        for sig in cert_data['signatures']:
            signer = sig.get('signer')
            if signer not in self.trusted_keys:
                self.validation_errors.append(f"Unknown signer: {signer}")
                return False
            
            # Verify signature
            if not self._verify_signature(cert_data, sig, self.trusted_keys[signer]):
                self.validation_errors.append(f"Invalid signature from {signer}")
                return False
        
        return True
    
    def _validate_semantics(self, cert_data: Dict[str, Any]) -> bool:
        """Validate certificate semantics."""
        # Check certificate age
        try:
            cert_time = datetime.fromisoformat(cert_data['timestamp'].replace('Z', '+00:00'))
            age = datetime.now(timezone.utc) - cert_time
            if age.days > 30:  # 30 day expiration
                self.validation_errors.append("Certificate expired")
                return False
        except Exception:
            self.validation_errors.append("Cannot validate certificate age")
            return False
        
        # Validate security level
        security_level = cert_data.get('metadata', {}).get('security_level')
        if security_level not in ['high', 'medium', 'low']:
            self.validation_errors.append("Invalid security level")
            return False
        
        return True
    
    def _verify_signature(self, cert_data: Dict[str, Any], signature: Dict[str, Any], key: str) -> bool:
        """Verify a certificate signature."""
        # Remove signatures for verification
        cert_copy = cert_data.copy()
        cert_copy.pop('signatures', None)
        
        # Serialize for verification
        message = json.dumps(cert_copy, sort_keys=True)
        expected_sig = hmac.new(
            key.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        
        try:
            provided_sig = base64.b64decode(signature['signature'])
            return hmac.compare_digest(expected_sig, provided_sig)
        except Exception:
            return False
    
    def _validation_failed(self, error: str) -> Dict[str, Any]:
        """Return validation failure result."""
        return {
            'is_valid': False,
            'errors': self.validation_errors + [error],
            'certificate_id': None,
            'security_level': None,
            'verified_at': datetime.now(timezone.utc).isoformat()
        }


def generate_certificate(computation_code: str, 
                        input_data: str, 
                        output_data: str,
                        **kwargs) -> str:
    """Convenience function to generate certificate JSON."""
    generator = CertificateGenerator()
    certificate = generator.generate_certificate(
        computation_code, input_data, output_data, **kwargs
    )
    return certificate.to_json()


def validate_certificate(certificate_json: str) -> Dict[str, Any]:
    """Convenience function to validate certificate."""
    validator = CertificateValidator()
    return validator.validate_certificate(certificate_json)
