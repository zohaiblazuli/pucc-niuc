"""
PCC-NIUC: Privacy-Preserving Computing with Non-Interactive Universal Computation

A comprehensive system for secure, auditable computation with privacy preservation
and verifiable certificates.
"""

__version__ = "0.1.0"
__author__ = "PCC-NIUC Team"
__email__ = "team@pcc-niuc.example"

# Core functionality imports
from .normalizer import normalize_code, CodeNormalizer
from .checker import check_code_security, SecurityChecker
from .certificate import generate_certificate, validate_certificate
from .runtime_gate import check_operation, get_runtime_gate

# Version info
__all__ = [
    "__version__",
    "__author__", 
    "__email__",
    # Core functions
    "normalize_code",
    "check_code_security", 
    "generate_certificate",
    "validate_certificate",
    "check_operation",
    # Core classes
    "CodeNormalizer",
    "SecurityChecker",
    "get_runtime_gate",
]
