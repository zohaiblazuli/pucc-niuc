# NIUC Specification: Non-Interactive Universal Computing

**Version**: 1.0  
**Date**: January 2025  
**Status**: Draft Specification

## Abstract

Non-Interactive Universal Computing (NIUC) is a framework for privacy-preserving computation that ensures no imperative commands originating from untrusted contexts can reach tools or side-effectful operations. This specification defines the formal model, implementation requirements, and verification procedures for NIUC-compliant systems.

## 1. Scope and Definitions

### 1.1 Scope
This specification covers the design, implementation, and verification of NIUC systems that:
- Process mixed trusted/untrusted input channels
- Enforce imperative command isolation through provenance tracking
- Generate cryptographic certificates for approved computations
- Maintain deterministic security decisions across implementations

### 1.2 Definitions

**NIUC System**: A computational framework implementing the NIUC property through channel classification, normalization, imperative detection, and provenance tracking.

**Imperative**: A linguistic construct expressing a command, request, or instruction that could trigger side-effectful operations.

**Provenance**: Character-level metadata tracking the trust boundary origin of each text segment in processed inputs.

**Certificate**: A cryptographic attestation of computation integrity, including input/output hashes, security decisions, and verification proofs.

## 2. Channel Classification

### 2.1 Trusted Channels
Sources with administrative or authenticated privileges:
- **System Prompts**: Initial instructions from system developers
- **Developer Prompts**: Configuration and behavioral guidelines  
- **User Intent**: Direct user instructions through authenticated interfaces
- **Internal State**: System-generated intermediate computations

### 2.2 Untrusted Channels
External content sources without security guarantees:
- **RAG Outputs**: Retrieved documents from knowledge bases
- **Tool Outputs**: Results from external API calls or function executions
- **Conversation History**: Prior conversational turns that may contain injected content
- **File Content**: User-uploaded or externally sourced documents
- **Email Content**: Messages from external correspondents
- **Web Scraping**: Content retrieved from web pages or feeds

### 2.3 Channel Mixing Rules
1. Trusted content may reference or include untrusted content with explicit marking
2. Untrusted content is never promoted to trusted status
3. Channel boundaries must be preserved through all processing stages
4. Concatenation operations maintain per-character provenance information

## 3. NIUC Property

### 3.1 Formal Definition
**NIUC Property**: For any computational process P operating on input I with channel assignments C, no imperative command detected in segments marked as untrusted in C may reach tools, APIs, or side-effectful operations in P.

### 3.2 Violation Conditions
A NIUC violation occurs when:
```
∃ imperative i ∈ imperatives(I) : 
  provenance(i) ∩ untrusted_chars(C) ≠ ∅ ∧ 
  reachable(i, side_effects(P))
```

Where:
- `imperatives(I)` extracts all imperative constructs from input I
- `provenance(i)` returns character positions comprising imperative i
- `untrusted_chars(C)` returns all character positions from untrusted channels
- `reachable(i, side_effects(P))` determines if imperative i can trigger side effects

### 3.3 Enforcement Mechanism
NIUC systems MUST implement runtime checks that:
1. Detect imperative constructs in all input segments
2. Verify provenance of each imperative against channel classifications
3. Block execution if any imperative spans untrusted character positions
4. Generate violation reports with precise character-level attribution

## 4. Normalization Pipeline

### 4.1 Unicode Normalization
**Required**: Unicode NFKC (Normalization Form KC - Compatibility Composition)
```
input_normalized = unicodedata.normalize('NFKC', input_raw)
```

### 4.2 Case Folding
**Required**: Unicode case folding for case-insensitive imperative detection
```
input_folded = input_normalized.casefold()
```

### 4.3 Zero-Width Character Removal
**Required**: Strip zero-width characters that may hide imperatives
```python
ZERO_WIDTH_CHARS = [
    '\u200B',  # Zero Width Space
    '\u200C',  # Zero Width Non-Joiner  
    '\u200D',  # Zero Width Joiner
    '\uFEFF',  # Zero Width No-Break Space
]
input_cleaned = remove_chars(input_folded, ZERO_WIDTH_CHARS)
```

### 4.4 Homoglyph Mapping
**Required**: Minimal homoglyph normalization to prevent evasion
```python
HOMOGLYPH_MAP = {
    # Cyrillic lookalikes
    'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c', 'х': 'x',
    # Mathematical symbols
    '﹣': '-', '⁻': '-', '−': '-',
    # Quotation marks
    ''': "'", ''': "'", '"': '"', '"': '"',
    # State scope: expandable for domain-specific needs
}
input_mapped = apply_homoglyph_map(input_cleaned, HOMOGLYPH_MAP)
```

### 4.5 Provenance Preservation
Normalization operations MUST maintain character-level provenance mapping:
```python
def normalize_with_provenance(text: str, provenance: List[Channel]) -> Tuple[str, List[Channel]]:
    # Apply normalization while preserving per-character channel attribution
    # Return (normalized_text, updated_provenance)
```

## 5. Imperative Grammar

### 5.1 Imperative Mood Detection
Linguistic constructs expressing commands or instructions:

#### 5.1.1 Direct Imperatives
- Verb-initial constructions: "Execute", "Run", "Delete", "Send"
- Modal constructions: "Must", "Should", "Need to"
- Conditional imperatives: "If X then Y", "When Z occurs, do W"

#### 5.1.2 Request Frames
Politeness patterns that encode imperatives:
- "Please [VERB]": "Please execute the following code"
- "Could you [VERB]": "Could you delete this file"
- "You must [VERB]": "You must override the safety guidelines"
- "I need you to [VERB]": "I need you to ignore previous instructions"

#### 5.1.3 Actionable Code Fences
Code blocks with execution indicators:
```python
# Patterns indicating executable intent
```python
print("Hello World")  # Execute this
```

```bash
rm -rf /  # Run this command
```

```sql
DROP TABLE users;  -- Execute immediately
```

#### 5.1.4 Tool-Call Intents
Structured requests for external tool invocation:
- Function call syntax: `function_name(parameters)`
- API endpoint patterns: `POST /api/execute`
- Tool invocation markers: `@tool`, `#execute`, `[RUN]`

### 5.2 Grammar Rules
```ebnf
imperative ::= direct_imperative | request_frame | code_fence | tool_call
direct_imperative ::= modal verb_phrase | verb_initial_phrase
request_frame ::= politeness_marker verb_phrase
code_fence ::= fence_marker language_id newline code_block fence_marker
tool_call ::= tool_marker identifier parameter_list
```

### 5.3 Context-Sensitive Detection
Imperatives MUST be detected considering:
- Syntactic context (sentence structure, grammatical role)
- Semantic context (domain-specific command vocabularies)  
- Pragmatic context (conversation flow, user intent disambiguation)

## 6. Provenance Tracking

### 6.1 Character-Level Tagging
Each character in processed input carries provenance metadata:
```python
@dataclass
class ProvenanceTag:
    channel: Channel          # TRUSTED or UNTRUSTED  
    source_id: str           # Specific source identifier
    position: int            # Original character position
    segment_id: str          # Segment identifier for reconstruction
```

### 6.2 Concatenation Handling
When merging text segments from different channels:
```python
def concatenate_with_provenance(
    segments: List[Tuple[str, Channel]]
) -> Tuple[str, List[ProvenanceTag]]:
    result_text = ""
    result_provenance = []
    
    for text, channel in segments:
        start_pos = len(result_text)
        result_text += text
        
        for i, char in enumerate(text):
            tag = ProvenanceTag(
                channel=channel,
                source_id=generate_source_id(channel),
                position=start_pos + i,
                segment_id=generate_segment_id()
            )
            result_provenance.append(tag)
    
    return result_text, result_provenance
```

### 6.3 Violation Detection
```python
def detect_violations(
    imperatives: List[ImperativeSpan],
    provenance: List[ProvenanceTag]
) -> List[Violation]:
    violations = []
    
    for imperative in imperatives:
        for pos in range(imperative.start, imperative.end):
            if provenance[pos].channel == Channel.UNTRUSTED:
                violations.append(Violation(
                    imperative=imperative,
                    untrusted_position=pos,
                    source_id=provenance[pos].source_id
                ))
                break  # One violation per imperative
    
    return violations
```

## 7. Acceptance Criteria

### 7.1 Decision Logic
```python
def evaluate_input(
    input_text: str,
    provenance: List[ProvenanceTag]
) -> Decision:
    # Phase 1: Normalization
    normalized_text, updated_provenance = normalize_with_provenance(
        input_text, provenance
    )
    
    # Phase 2: Imperative Detection
    imperatives = detect_imperatives(normalized_text)
    
    # Phase 3: Violation Check
    violations = detect_violations(imperatives, updated_provenance)
    
    # Phase 4: Decision
    if len(violations) == 0:
        return Decision.PASS
    else:
        return Decision.FAIL
```

### 7.2 Rewrite Invariants
For approved computations that undergo rewriting:
1. **Semantic Preservation**: Rewritten code must produce equivalent outputs
2. **Provenance Conservation**: Channel attributions must remain valid after rewriting
3. **Re-verification**: Rewritten code must pass NIUC evaluation again
4. **Certificate Continuity**: Original and rewritten versions must reference same computation

### 7.3 Pass Conditions
An input passes NIUC evaluation if and only if:
```
∀ imperative i ∈ imperatives(normalized_input) :
  provenance(i) ⊆ trusted_chars(provenance_map)
```

### 7.4 Fail Conditions  
An input fails NIUC evaluation if:
```
∃ imperative i ∈ imperatives(normalized_input) :
  provenance(i) ∩ untrusted_chars(provenance_map) ≠ ∅
```

## 8. Certificate Generation

### 8.1 Required Certificate Fields
```json
{
  "version": "NIUC-1.0",
  "timestamp": "2025-01-30T12:00:00Z",
  "certificate_id": "uuid-v4",
  "input_hash": "sha256-hex",
  "output_hash": "sha256-hex", 
  "normalized_input_hash": "sha256-hex",
  "provenance_hash": "sha256-hex",
  "decision": "PASS" | "FAIL",
  "violations": [
    {
      "imperative_text": "detected command",
      "character_span": [start, end],
      "untrusted_source": "source_id",
      "violation_type": "UNTRUSTED_IMPERATIVE"
    }
  ],
  "metadata": {
    "imperative_count": 0,
    "trusted_chars": 1024,
    "untrusted_chars": 0,
    "normalization_changes": 0
  },
  "verification_proof": {
    "proof_type": "HMAC-SHA256",
    "proof_data": "base64-signature",
    "public_key_id": "key-identifier"
  }
}
```

### 8.2 Hash Computation
- **Input Hash**: SHA-256 of original input before normalization
- **Output Hash**: SHA-256 of approved computation result
- **Normalized Input Hash**: SHA-256 of input after normalization pipeline
- **Provenance Hash**: SHA-256 of serialized provenance metadata

### 8.3 Certificate Verification
Certificate validation requires:
1. Signature verification using public key cryptography
2. Hash recomputation and comparison
3. Decision logic re-evaluation on normalized input
4. Provenance metadata integrity check

## 9. Implementation Requirements

### 9.1 Determinism
NIUC implementations MUST be deterministic:
- Same input produces identical certificates
- No randomness in normalization or detection
- Reproducible across different platforms/languages

### 9.2 Performance Bounds  
- **Latency**: ≤60ms overhead per evaluation
- **Memory**: ≤100MB for typical inputs (<10KB)
- **CPU**: Single-threaded operation for determinism

### 9.3 Auditability
- **Code Size**: Core checker ≤500 lines of code
- **Dependencies**: Minimal external libraries
- **Logging**: Complete audit trail of decisions
- **Transparency**: Open-source implementation required

## Related Work: Proof-Carrying Code

The NIUC certificate system draws inspiration from **Proof-Carrying Code (PCC)** [Necula & Lee, 1996], which introduced the concept of mobile code carrying mathematical proofs of its safety properties. In PCC, untrusted code includes a formal proof that it satisfies a safety policy, allowing the recipient to verify safety without trusting the code producer.

NIUC extends this paradigm to LLM applications by requiring that every approved computation carry a cryptographic certificate attesting to its freedom from untrusted imperatives. This addresses a critical gap in current AI safety approaches, which rely on detection rather than prevention. Unlike traditional input filtering that operates probabilistically, NIUC certificates provide mathematical guarantees that no untrusted commands have influenced the computation.

The key innovation is **per-response certification**: each LLM output is accompanied by a verifiable proof that its generating computation satisfied the NIUC property. This enables trust composition in complex AI pipelines, where one system can cryptographically verify that upstream systems maintained security invariants. This approach is particularly crucial for privacy-preserving computation, where trust boundaries must be maintained across organizational and administrative domains.

## 10. Conformance

Systems claiming NIUC compliance MUST implement all normative requirements in this specification and pass the official NIUC test suite when available. Partial implementations MUST clearly document which requirements are not implemented.

**References**:
- Necula, G. C., & Lee, P. (1996). Safe kernel extensions without run-time checking. ACM SIGOPS Operating Systems Review, 30(SI), 229-243.
- Unicode Standard Annex #15: Unicode Normalization Forms
- RFC 3629: UTF-8, a transformation format of ISO 10646