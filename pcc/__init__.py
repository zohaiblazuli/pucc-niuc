"""
PCC-NIUC: Privacy-Preserving Computing with Non-Interactive Universal Computation

A comprehensive system for secure, auditable computation with privacy preservation
and verifiable certificates.
"""

__version__ = "0.1.0"
__author__ = "PCC-NIUC Team"
__email__ = "team@pcc-niuc.example"

# Core functionality imports
from .normalizer import normalize_text, TextNormalizer
from .checker import verify_niuc, NIUCChecker
from .certificate import create_certificate, validate_certificate_json
from .runtime_gate import process_with_block_mode, process_with_rewrite_mode, RuntimeGate

# Version info
__all__ = [
    "__version__",
    "__author__", 
    "__email__",
    # Core functions
    "normalize_text",
    "verify_niuc", 
    "create_certificate",
    "validate_certificate_json",
    "process_with_block_mode",
    "process_with_rewrite_mode",
    # Core classes
    "TextNormalizer",
    "NIUCChecker",
    "RuntimeGate",
]
