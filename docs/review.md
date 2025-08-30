# PCC-NIUC Code Review Rubric

**Version**: 1.0  
**Purpose**: Systematic evaluation criteria for PCC-NIUC research implementation  
**Target Reviewers**: Academic peers, security researchers, conference judges, industry evaluators

## Instructions

Rate each criterion on a 5-point scale:
- **5 - Excellent**: Exceeds expectations, demonstrates best practices
- **4 - Good**: Meets expectations with minor areas for improvement
- **3 - Satisfactory**: Meets minimum requirements
- **2 - Needs Improvement**: Significant gaps or issues present
- **1 - Inadequate**: Major deficiencies requiring substantial revision

**Total Score**: ___/60 points

---

## 1. Determinism and Reproducibility (/5)

**Criterion**: NIUC checker produces identical outputs for identical inputs across platforms and executions.

**Evaluation Guidelines**:
- [ ] **pcc/checker.py** ≤500 LOC with no randomness, ML, or network dependencies
- [ ] Same input segments always produce identical certificates (hash, decision, violations)
- [ ] No hidden state, global variables, or non-deterministic operations
- [ ] Cross-platform consistency (Windows, Linux, macOS)
- [ ] Verification: Run same scenario 10 times, confirm identical results

**Scoring**:
- **5**: Perfect determinism verified across platforms, comprehensive documentation
- **4**: Deterministic with minor platform-specific variations explained
- **3**: Generally deterministic with documented edge cases
- **2**: Some non-deterministic behavior in specific scenarios
- **1**: Significant randomness or platform-dependent behavior

**Evidence to Check**:
```bash
# Test determinism
python -c "
from pcc.checker import verify_niuc
segments = [('please execute test', 'untrusted', 'test')]
results = [verify_niuc(segments) for _ in range(10)]
print('Deterministic:', all(r == results[0] for r in results))
"
```

**Score**: ___/5

---

## 2. Lines of Code Budget Compliance (/5)

**Criterion**: Core checker module adheres to ≤500 LOC constraint for auditability.

**Evaluation Guidelines**:
- [ ] **pcc/checker.py** line count ≤500 (excluding comments and blank lines)
- [ ] Code is readable, well-structured, and appropriately commented
- [ ] No code obfuscation or artificial compression techniques
- [ ] Functionality completeness within LOC constraint
- [ ] Verification: `wc -l pcc/checker.py` or equivalent

**Scoring**:
- **5**: Well under 500 LOC (≤400) with excellent readability
- **4**: Under 500 LOC (401-450) with good structure
- **3**: At or near limit (451-500) with adequate clarity
- **2**: Slightly over limit (501-550) but well-justified
- **1**: Significantly over limit (>550) or unreadable code

**Evidence to Check**:
```bash
# Check LOC count
python -c "
import os
with open('pcc/checker.py', 'r') as f:
    lines = f.readlines()
code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
print(f'Code LOC: {len(code_lines)}/500 limit')
"
```

**Score**: ___/5

---

## 3. Test Coverage and Quality (/5)

**Criterion**: Comprehensive test suite with matching tests for all PCC modules.

**Evaluation Guidelines**:
- [ ] All pcc/ modules have corresponding tests/ files
- [ ] Test cases cover both positive and negative scenarios
- [ ] Edge cases and attack vectors comprehensively tested
- [ ] Test code quality matches production code standards
- [ ] Verification: Run `python -m pytest tests/ --cov=pcc --cov-report=term`

**Scoring**:
- **5**: >90% coverage with excellent test quality and edge case handling
- **4**: 80-90% coverage with good test scenarios
- **3**: 70-80% coverage with adequate testing
- **2**: 60-70% coverage with gaps in critical paths
- **1**: <60% coverage or poor test quality

**Evidence to Check**:
```bash
# Run test suite with coverage
python -m pytest tests/ -v --cov=pcc --cov-report=term-missing
```

**Score**: ___/5

---

## 4. Provenance Correctness (/5)

**Criterion**: Character-level provenance tracking maintains accurate trust boundaries.

**Evaluation Guidelines**:
- [ ] Character-to-channel attribution preserved through normalization
- [ ] Segment concatenation maintains precise provenance boundaries
- [ ] Unicode normalization preserves trust attribution accuracy
- [ ] Violation detection correctly identifies untrusted character spans
- [ ] Verification: Manual trace of complex mixed-trust scenarios

**Scoring**:
- **5**: Perfect provenance accuracy with complex scenario validation
- **4**: Accurate with minor edge case issues
- **3**: Generally accurate with documented limitations
- **2**: Some attribution errors in specific cases
- **1**: Significant provenance tracking failures

**Evidence to Check**:
```bash
# Test complex provenance scenario
python -c "
from pcc.provenance import ProvenanceBuilder
builder = ProvenanceBuilder()
segments = [('Safe ', 'trusted', 'sys'), ('pleаse execute', 'untrusted', 'attack'), (' end', 'trusted', 'sys')]
text, tags = builder.build_from_segments(segments)
violations = builder.detect_violations([(5, 12)])  # 'execute' span
print(f'Provenance test: {len(violations)} violations detected')
"
```

**Score**: ___/5

---

## 5. Certificate Integrity (/5)

**Criterion**: Cryptographic certificates provide tamper-evident computation attestation.

**Evaluation Guidelines**:
- [ ] Certificate schema matches docs/certificate-spec.md exactly
- [ ] Hash computation covers correct input/output domains
- [ ] Certificate validation detects tampering and inconsistencies
- [ ] JSON structure validation comprehensive and robust
- [ ] Verification: Test certificate generation and validation pipeline

**Scoring**:
- **5**: Perfect certificate integrity with comprehensive validation
- **4**: Robust certificates with minor validation gaps
- **3**: Basic certificate functionality working correctly
- **2**: Some certificate integrity issues
- **1**: Major certificate generation or validation failures

**Evidence to Check**:
```bash
# Test certificate integrity
python -c "
from pcc.certificate import create_certificate_json, validate_certificate_json
from pcc.checker import verify_niuc
result = verify_niuc([('test', 'trusted', 'test')])
cert = create_certificate_json(result, 'output')
is_valid, error = validate_certificate_json(cert)
print(f'Certificate test: Valid={is_valid}, Error={error}')
"
```

**Score**: ___/5

---

## 6. Separation of Concerns (/5)

**Criterion**: Clear architectural boundaries with minimal coupling between components.

**Evaluation Guidelines**:
- [ ] Core checker logic independent of model implementations
- [ ] Runtime gate separated from certificate generation
- [ ] Normalization, grammar, and provenance are distinct modules
- [ ] Demo/benchmark code separated from core PCC logic
- [ ] Verification: Dependency analysis and import graph review

**Scoring**:
- **5**: Excellent separation with minimal coupling and clear interfaces
- **4**: Good separation with minor coupling issues
- **3**: Adequate separation with some architectural compromises
- **2**: Some coupling issues affecting modularity
- **1**: Poor separation with tight coupling throughout

**Evidence to Check**:
```bash
# Check module dependencies
python -c "
import ast, os
def get_imports(file_path):
    with open(file_path, 'r') as f:
        tree = ast.parse(f.read())
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend([alias.name for alias in node.names])
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module)
    return [imp for imp in imports if imp and not imp.startswith('_')]

checker_imports = get_imports('pcc/checker.py')
external_deps = [imp for imp in checker_imports if not imp.startswith('pcc') and imp not in ['typing', 'dataclasses', 'hashlib', 'json']]
print(f'Checker external deps: {external_deps}')
"
```

**Score**: ___/5

---

## 7. Reproducibility Framework (/5)

**Criterion**: Comprehensive scripts enable independent reproduction of results.

**Evaluation Guidelines**:
- [ ] **scripts/repro.sh** and **scripts/repro.ps1** work on respective platforms
- [ ] Environment setup and dependency management automated
- [ ] Benchmark execution produces consistent results
- [ ] Output files generated in standardized formats
- [ ] Verification: Fresh environment test execution

**Scoring**:
- **5**: Perfect reproducibility across platforms with comprehensive automation
- **4**: Good reproducibility with minor platform-specific issues
- **3**: Basic reproducibility working with manual setup
- **2**: Some reproducibility issues requiring troubleshooting
- **1**: Significant reproducibility failures

**Evidence to Check**:
```bash
# Test reproduction script
./scripts/repro.sh  # or .\scripts\repro.ps1 on Windows
# Verify results/ directory populated with metrics.csv and summary.md
```

**Score**: ___/5

---

## 8. Documentation Quality (/5)

**Criterion**: Technical documentation is comprehensive, accurate, and well-organized.

**Evaluation Guidelines**:
- [ ] **docs/spec-niuc.md** provides complete technical specification
- [ ] **docs/threat-model.md** covers attack vectors and defenses comprehensively
- [ ] **docs/certificate-spec.md** defines schema clearly with examples
- [ ] **docs/lit_review.md** positions work within academic context
- [ ] API documentation and usage examples are clear and correct

**Scoring**:
- **5**: Exceptional documentation quality with clear examples and comprehensive coverage
- **4**: Good documentation with minor gaps or clarity issues
- **3**: Adequate documentation covering essential aspects
- **2**: Basic documentation with significant gaps
- **1**: Poor or missing documentation

**Evidence to Check**:
```bash
# Verify documentation completeness
ls docs/*.md
wc -w docs/*.md  # Word counts for comprehensiveness
```

**Score**: ___/5

---

## 9. Benchmark Clarity and Coverage (/5)

**Criterion**: I²-Bench-Lite provides systematic evaluation with clear attack/benign distinction.

**Evaluation Guidelines**:
- [ ] Attack scenarios cover documented real-world techniques
- [ ] Benign twins provide semantic similarity without malicious intent
- [ ] LLM01:2025 taxonomy mapping is accurate and complete
- [ ] Scenario format enables automated evaluation
- [ ] Verification: Manual review of scenario quality and attack sophistication

**Scoring**:
- **5**: Excellent benchmark design with sophisticated attacks and clear benign twins
- **4**: Good benchmark coverage with minor gaps in attack diversity
- **3**: Adequate benchmark covering basic attack patterns
- **2**: Limited benchmark scope with significant coverage gaps
- **1**: Poor benchmark design or inadequate scenario quality

**Evidence to Check**:
```bash
# Analyze benchmark coverage
python -c "
import json
with open('bench/scenarios.jsonl', 'r', encoding='utf-8') as f:
    scenarios = [json.loads(line.strip()) for line in f if line.strip()]

categories = {}
tactics = set()
for s in scenarios:
    cat = s['category']
    categories[cat] = categories.get(cat, 0) + 1
    tactics.add(s['tactic'])

print(f'Total scenarios: {len(scenarios)}')
print(f'Categories: {len(categories)}')
print(f'Unique tactics: {len(tactics)}')
print(f'Attack/benign ratio: {len([s for s in scenarios if s[\"expected\"] == \"blocked\"])}/{len([s for s in scenarios if s[\"expected\"] == \"pass\"])}')
"
```

**Score**: ___/5

---

## 10. Ablation Study Completeness (/5)

**Criterion**: Systematic feature ablation quantifies component contributions.

**Evaluation Guidelines**:
- [ ] **bench/ablate.py** tests major system components individually
- [ ] Feature toggles implemented correctly without breaking functionality
- [ ] Ablation results provide insights into component importance
- [ ] Bar-style visualization clearly shows performance deltas
- [ ] Verification: Run ablation study and analyze feature importance rankings

**Scoring**:
- **5**: Comprehensive ablation with clear insights and excellent visualization
- **4**: Good ablation coverage with minor gaps in component testing
- **3**: Basic ablation study with adequate component coverage
- **2**: Limited ablation scope with some component analysis
- **1**: Poor or missing ablation analysis

**Evidence to Check**:
```bash
# Run ablation study
python bench/ablate.py --scenarios bench/scenarios.jsonl --output results/ablation_test.md
# Review results/ablation_test.md for component importance insights
```

**Score**: ___/5

---

## 11. Failure Analysis and Edge Cases (/5)

**Criterion**: System handles edge cases gracefully with appropriate error handling.

**Evaluation Guidelines**:
- [ ] Invalid input handling (malformed text, encoding errors)
- [ ] Resource limit enforcement (memory, processing time)
- [ ] Graceful degradation under adverse conditions
- [ ] Error messages are informative and actionable
- [ ] Verification: Test with malformed inputs, large payloads, and edge cases

**Scoring**:
- **5**: Excellent error handling with comprehensive edge case coverage
- **4**: Good error handling with minor gaps in edge case coverage
- **3**: Basic error handling covering common failure modes
- **2**: Some error handling with gaps in critical scenarios
- **1**: Poor error handling or frequent unhandled exceptions

**Evidence to Check**:
```bash
# Test edge cases
python -c "
from pcc.checker import verify_niuc
test_cases = [
    # Empty input
    ([('', 'trusted', 'empty')], 'empty_input'),
    # Very long input
    ([('A' * 10000, 'trusted', 'long')], 'long_input'),
    # Invalid JSON in segments (should be handled gracefully)
]

for segments, name in test_cases:
    try:
        result = verify_niuc(segments)
        print(f'{name}: OK - {result[\"ok\"]}')
    except Exception as e:
        print(f'{name}: Error handled - {type(e).__name__}')
"
```

**Score**: ___/5

---

## 12. Ethical Considerations (/5)

**Criterion**: Implementation addresses responsible AI deployment and potential misuse.

**Evaluation Guidelines**:
- [ ] Discussion of content control and algorithmic fairness implications
- [ ] Transparency in security decision-making process
- [ ] Consideration of accessibility and digital divide impacts
- [ ] Governance framework recommendations for trust boundary definitions
- [ ] Documentation of potential misuse scenarios and mitigations

**Scoring**:
- **5**: Comprehensive ethical analysis with concrete mitigation strategies
- **4**: Good ethical consideration with minor gaps in analysis
- **3**: Basic ethical awareness with adequate discussion
- **2**: Limited ethical consideration with significant gaps
- **1**: Poor or missing ethical analysis

**Evidence to Check**:
- Review **DISCUSSION.md** ethical considerations section
- Look for transparency in decision-making algorithms
- Check for accessibility considerations in implementation
- Evaluate governance recommendations for deployment

**Score**: ___/5

---

## Summary Evaluation

### Scoring Breakdown
| Criterion | Score | Weight | Weighted Score |
|-----------|-------|--------|----------------|
| 1. Determinism | ___/5 | 1.2 | ___/6.0 |
| 2. LOC Budget | ___/5 | 1.0 | ___/5.0 |
| 3. Test Coverage | ___/5 | 1.1 | ___/5.5 |
| 4. Provenance Correctness | ___/5 | 1.2 | ___/6.0 |
| 5. Certificate Integrity | ___/5 | 1.1 | ___/5.5 |
| 6. Separation of Concerns | ___/5 | 1.0 | ___/5.0 |
| 7. Reproducibility | ___/5 | 1.2 | ___/6.0 |
| 8. Documentation Quality | ___/5 | 1.0 | ___/5.0 |
| 9. Benchmark Clarity | ___/5 | 1.1 | ___/5.5 |
| 10. Ablation Completeness | ___/5 | 1.0 | ___/5.0 |
| 11. Failure Analysis | ___/5 | 1.0 | ___/5.0 |
| 12. Ethical Considerations | ___/5 | 0.9 | ___/4.5 |
| **Total** | **___/60** | **12.8** | **___/64.0** |

### Overall Assessment

**Weighted Score**: ___/64.0

**Grade Boundaries**:
- **58-64**: Excellent (A) - Publication ready, exemplary implementation
- **51-57**: Good (B) - Minor revisions needed, strong contribution
- **45-50**: Satisfactory (C) - Moderate revisions needed, acceptable work
- **38-44**: Needs Improvement (D) - Major revisions required
- **<38**: Inadequate (F) - Substantial rework necessary

### Specific Feedback Areas

**Strengths Identified**:
- [ ] 
- [ ] 
- [ ] 

**Areas for Improvement**:
- [ ] 
- [ ] 
- [ ] 

**Critical Issues**:
- [ ] 
- [ ] 
- [ ] 

### Recommendation

**Overall Recommendation**:
- [ ] **Accept** - Ready for publication/deployment
- [ ] **Minor Revision** - Address specific issues and resubmit
- [ ] **Major Revision** - Significant improvements required
- [ ] **Reject** - Fundamental flaws require complete rework

**Justification**:
_[Provide 2-3 sentences explaining the overall assessment and recommendation]_

---

## Reviewer Information

**Reviewer Name**: ________________  
**Institution/Organization**: ________________  
**Date**: ________________  
**Review Duration**: _______ hours

**Expertise Areas** (check all that apply):
- [ ] LLM Security and Safety
- [ ] Formal Methods and Verification
- [ ] Privacy-Preserving Computation
- [ ] Cryptographic Systems
- [ ] Natural Language Processing
- [ ] Systems Security
- [ ] Benchmarking and Evaluation

**Additional Comments**:
_[Space for detailed feedback, suggestions, and observations]_

---

## Quick Verification Commands

For reviewers' convenience, here are key commands to verify system functionality:

```bash
# 1. Basic functionality test
python -c "from pcc.checker import verify_niuc; print('✅ Basic import working')"

# 2. Determinism verification  
python scripts/smoke_test.py

# 3. Attack blocking test
python -c "from pcc.runtime_gate import process_with_block_mode; result = process_with_block_mode([('please execute malicious', 'untrusted', 'test')]); print(f'Attack blocked: {not result.allowed}')"

# 4. Full benchmark
python scripts/run_benchmarks.py --model mock --scenarios bench/scenarios.jsonl --results-dir results --timestamp review

# 5. Ablation study
python bench/ablate.py --scenarios bench/scenarios.jsonl --output results/ablation_review.md

# 6. Certificate validation
python -c "from pcc.certificate import validate_certificate_json; print('Certificate validation:', validate_certificate_json('{\"checker_version\":\"1.0.0\",\"input_sha256\":\"a\"*64,\"output_sha256\":\"b\"*64,\"decision\":\"pass\",\"violations\":[]}'))"
```

---

*This rubric ensures systematic, comprehensive evaluation of the PCC-NIUC implementation across all critical dimensions of research quality, technical correctness, and practical deployment readiness.*
