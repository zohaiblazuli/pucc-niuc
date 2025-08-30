# PCC-NIUC Development Rules

## Scope
- `pcc/**` - Core PCC modules
- `bench/**` - Benchmarking system
- `tests/**` - Test suite
- `docs/**` - Documentation

## Description
PCC/NIUC runtime with proof-carrying certificates; tests-first development; reproducible benchmarks.

## Core Development Rules

### 1. Security & Determinism Requirements
- **`pcc/checker.py` MUST be deterministic, pure, and ≤500 LOC**
  - No network calls, file I/O, or machine learning
  - Same input always produces identical output
  - All randomness must be seeded or eliminated
  - Pure functions only - no side effects or global state

### 2. Certificate Generation Requirements  
- **Any "allow" decision MUST emit a `certificate.json` per specification**
  - Follow schema defined in `docs/certificate-spec.md`
  - Include computation hash, input/output hashes, and cryptographic proofs
  - Certificate must be re-verified after any code rewriting
  - All approved computations require verifiable certificates

### 3. Test-Driven Development
- **Any change in `pcc/**` MUST add/adjust matching tests in `tests/**`**
  - New functions require corresponding test functions
  - Modified functions require updated test cases
  - Test coverage must remain comprehensive
  - Expected behavior must be documented in test docstrings

### 4. Attack Research Documentation
- **Any `bench/**` change MUST update the "Related Attacks" table**
  - Add or update row in `docs/lit_review.md` "Related Attacks" table
  - Include proper academic citation
  - Describe attack vector and mitigation strategy
  - Link to corresponding benchmark scenario

### 5. Multi-File Change Planning
- **Composer MUST show a plan before multi-file edits**
  - List all files to be modified
  - Describe changes for each file
  - Specify test cases that will be added/modified
  - Explain integration between components
  - Get confirmation before proceeding

### 6. Code Quality Standards
- **Small, auditable functions with no hidden state**
  - Functions should be ≤50 lines when possible
  - Clear, descriptive function names
  - Single responsibility principle
  - No global variables or hidden dependencies
  
- **Comprehensive docstrings with pre/post-conditions**
  ```python
  def example_function(param: Type) -> ReturnType:
      """
      Brief description of function purpose.
      
      Args:
          param: Description of parameter
          
      Returns:
          Description of return value
          
      Preconditions:
          - param must be non-null
          - param must satisfy specific constraints
          
      Postconditions:
          - Return value satisfies output constraints
          - No side effects occur
          
      Raises:
          ExceptionType: When specific error conditions occur
      """
  ```

## Implementation Guidelines

### Security Analysis (`pcc/checker.py`)
- Use only deterministic algorithms
- Implement static analysis without external dependencies
- Maintain complexity counters and resource limits
- Return consistent violation reports
- No caching that could introduce non-determinism

### Certificate Management (`pcc/certificate.py`)
- Generate certificates for all approved operations
- Validate certificate schemas strictly
- Include sufficient metadata for audit trails
- Support certificate verification workflows
- Maintain cryptographic integrity

### Testing Strategy (`tests/**`)
- Unit tests for individual functions
- Integration tests for component interactions  
- Security tests for edge cases and attacks
- Performance tests for resource limits
- Determinism tests (same input → same output)

### Benchmarking (`bench/**`)
- Reproducible test scenarios
- Clear pass/fail criteria
- Performance metrics tracking
- Attack scenario documentation
- Literature references for related work

### Documentation (`docs/**`)
- Keep specifications up-to-date
- Document threat model thoroughly
- Maintain literature review with citations
- Provide clear implementation guidance
- Include security considerations

## Enforcement Notes

- These rules are automatically enforced by Cursor IDE
- Code reviews should verify compliance
- CI/CD pipelines should validate rule adherence
- Any rule violations should be addressed before merging
- Rules may be updated as project evolves

## Examples

### ✅ Good Practice
```python
def validate_computation_hash(code: str) -> ValidationResult:
    """
    Validate computation code hash for certificate generation.
    
    Preconditions:
        - code is valid Python syntax
        - code length < 10KB
        
    Postconditions:
        - Returns deterministic validation result
        - No side effects or state changes
    """
    # Implementation...
```

### ❌ Bad Practice  
```python
import requests  # Violates determinism rule
global_cache = {}  # Hidden state violation

def check_code(code):  # Missing docstring and types
    # Non-deterministic behavior
    result = requests.get('http://validator.com')
    global_cache[code] = result  # Side effects
```

---

*This file is automatically processed by Cursor Rules engine.*
