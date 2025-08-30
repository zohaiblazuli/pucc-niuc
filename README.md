# PCC-NIUC: Privacy-Preserving Computing with Non-Interactive Universal Computation

A comprehensive system for secure, auditable computation with privacy preservation and verifiable certificates.

## 🔒 Overview

PCC-NIUC provides a complete framework for privacy-preserving computation that ensures:

- **Privacy**: Sensitive data remains protected during computation
- **Security**: Code is validated against security policies before execution  
- **Verifiability**: All computations produce cryptographic certificates
- **Auditability**: Complete provenance tracking and runtime monitoring
- **Determinism**: Reproducible results without machine learning components

## 🏗️ Architecture

### Core Components

- **`pcc/normalizer.py`** - Transforms code into canonical form for analysis
- **`pcc/imperative_grammar.py`** - Defines allowed computational constructs
- **`pcc/provenance.py`** - Tracks computation lineage and data flow
- **`pcc/checker.py`** - Validates code against security policies (≤500 LOC, deterministic)
- **`pcc/certificate.py`** - Generates and validates computation certificates
- **`pcc/runtime_gate.py`** - Enforces runtime security policies
- **`pcc/rewrite.py`** - Applies security transformations to code

### Support Components

- **`bench/`** - Benchmarking system with test scenarios
- **`demo/`** - Interactive CLI demonstration
- **`tests/`** - Comprehensive test suite
- **`docs/`** - Technical documentation and specifications

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd pcc-niuc

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

### Basic Usage

```python
from pcc.checker import check_code_security
from pcc.certificate import generate_certificate

# Check code security
code = """
def safe_calculation(x, y):
    return x + y + 42
"""

result = check_code_security(code)
print(f"Security level: {result['security_level']}")
print(f"Violations: {result['total_violations']}")

# Generate certificate for approved code
if result['security_level'] == 'approved':
    cert_json = generate_certificate(
        computation_code=code,
        input_data="test_inputs",
        output_data="test_outputs"
    )
    print("Certificate generated successfully!")
```

### Interactive Demo

```bash
# Run interactive demo
python demo/demo_cli.py

# Or process a specific file
python demo/demo_cli.py -f example.py -o results.json
```

### Run Benchmarks

```bash
# Run full benchmark suite
python bench/score.py

# Run with verbose output
python bench/score.py --verbose

# Custom scenarios file
python bench/score.py --scenarios custom_scenarios.jsonl
```

## 🔧 Development

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=pcc --cov-report=html

# Run specific test file
python -m pytest tests/test_checker.py -v
```

### Code Quality

```bash
# Format code
black pcc/ bench/ demo/ tests/

# Sort imports
isort pcc/ bench/ demo/ tests/

# Type checking
mypy pcc/

# Lint code
flake8 pcc/ bench/ demo/ tests/
```

## 📋 System Requirements

- **Python**: 3.8 or higher
- **Memory**: Minimum 512MB, recommended 2GB+
- **Storage**: ~100MB for installation
- **OS**: Cross-platform (Windows, macOS, Linux)

### Dependencies

- `cryptography` - Cryptographic operations
- `psutil` - System resource monitoring
- `dataclasses-json` - JSON serialization

## 🔒 Security Model

### Threat Model

The system protects against:

- **Malicious Code Injection**: Static analysis prevents dangerous operations
- **Data Exfiltration**: Network and file access restrictions
- **Resource Exhaustion**: Runtime limits on memory, CPU, and iterations
- **Code Tampering**: Cryptographic certificates ensure integrity

### Security Levels

1. **Approved** ✅ - Safe code that can execute freely
2. **Monitored** 👀 - Code that requires runtime monitoring
3. **Restricted** ⚠️ - Code with resource limitations
4. **Rejected** ❌ - Code that violates security policies

### Certificate Schema

All approved computations produce certificates with:

- Computation hash and metadata
- Input/output data hashes (privacy-preserving)
- Cryptographic proofs of compliance
- Digital signatures from trusted authorities
- Compliance attestations

See [`docs/certificate-spec.md`](docs/certificate-spec.md) for complete schema.

## 📊 Performance

Expected performance characteristics:

- **Code Analysis**: ~1-10ms per function
- **Certificate Generation**: ~5-50ms per computation  
- **Runtime Monitoring**: <1% overhead
- **Memory Usage**: <100MB for typical workloads

Run benchmarks to measure performance on your system:

```bash
python bench/score.py
```

## 📚 Documentation

- [`docs/spec-niuc.md`](docs/spec-niuc.md) - System specification
- [`docs/threat-model.md`](docs/threat-model.md) - Security analysis
- [`docs/certificate-spec.md`](docs/certificate-spec.md) - Certificate format
- [`docs/lit_review.md`](docs/lit_review.md) - Related research

## 🧪 Example Scenarios

### Safe Computation

```python
def calculate_statistics(numbers):
    total = sum(numbers)
    count = len(numbers)
    mean = total / count if count > 0 else 0
    return {"mean": mean, "total": total, "count": count}
```

**Result**: ✅ Approved - generates certificate

### Dangerous Code

```python
import os

def read_secrets():
    return open('/etc/passwd').read()
```

**Result**: ❌ Rejected - file access violation

### Complex Computation

```python
def fibonacci_sequence(n):
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:  
        return [0, 1]
    
    sequence = [0, 1]
    for i in range(2, n):
        sequence.append(sequence[i-1] + sequence[i-2])
    return sequence
```

**Result**: 👀 Monitored - resource usage tracked

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Add tests for new functionality
4. Ensure all tests pass: `python -m pytest`
5. Follow code style guidelines
6. Submit pull request

### Development Guidelines

- Keep `checker.py` ≤ 500 lines of code
- Ensure deterministic behavior (no randomness/ML)
- All public functions must include certificates for allowed output
- Prefer small, auditable functions with no hidden state
- Update documentation and tests for all changes

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Privacy-preserving computing research community
- Secure multi-party computation protocols
- Trusted execution environment technologies
- Open source security tools and libraries

## 📞 Support

- **Issues**: Report bugs via GitHub Issues
- **Documentation**: See `docs/` directory
- **Community**: Join discussions in GitHub Discussions
- **Security**: Report security issues privately to security@pcc-niuc.example

---

**Built with ❤️ for secure, private, and verifiable computation**
