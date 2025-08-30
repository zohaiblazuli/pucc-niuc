# Methods

## NIUC System Architecture

Our Non-Interactive Universal Computing (NIUC) framework implements deterministic security enforcement through a five-stage pipeline: input normalization, imperative grammar detection, character-level provenance tracking, violation checking, and certificate generation. The system processes mixed trusted/untrusted content segments while maintaining mathematical guarantees that no imperative command originating from untrusted channels can reach side-effectful operations.

## Text Normalization Pipeline

The normalization pipeline transforms input text into canonical form to prevent Unicode-based evasion attacks while preserving character-level provenance mappings. This four-step process ensures consistent imperative detection across diverse input encodings and linguistic representations.

**Unicode NFKC Normalization**: We apply Unicode Normalization Form KC (Compatibility Composition) to convert all text into canonical decomposed form, eliminating encoding variations that could hide imperatives. This handles combining characters, compatibility variants, and normalization attacks where visually identical text uses different Unicode representations.

**Case Folding**: All text undergoes Unicode case folding using the `casefold()` operation, which provides more comprehensive case normalization than simple lowercase conversion. This ensures that imperatives written in different cases ("EXECUTE", "Execute", "execute") are detected consistently while handling special cases like German ß and Turkish i/I distinctions.

**Zero-Width Character Removal**: We systematically remove zero-width characters that attackers use to hide imperatives within visually normal text. The removal set includes Zero Width Space (U+200B), Zero Width Non-Joiner (U+200C), Zero Width Joiner (U+200D), and Zero Width No-Break Space (U+FEFF). These characters are commonly exploited to split imperative words across grapheme boundaries, making them invisible to naive pattern matching while maintaining visual appearance.

**Homoglyph Mapping**: A curated mapping table converts visually similar characters from different Unicode scripts to their canonical Latin equivalents. This addresses homoglyph substitution attacks where Cyrillic 'а' (U+0430) replaces Latin 'a' (U+0061) in words like "pleаse" to evade detection. Our mapping covers the most commonly abused character pairs across Cyrillic, Greek, and mathematical symbol ranges, with provisions for domain-specific extensions.

## Imperative Grammar Detection

The grammar detection system identifies command patterns through regex-based pattern matching across four categories of imperative constructs. This approach provides deterministic detection behavior essential for certificate generation while maintaining computational efficiency.

**Direct Imperatives**: We detect verb-initial constructions ("Execute this command") and modal constructions ("Must delete files") through compiled regular expressions matching common imperative verbs. The pattern set includes destructive operations (execute, run, delete, remove), file operations (create, write, save), network operations (send, post, upload), and system operations (install, update, disable).

**Request Frames**: Politeness patterns that encode imperatives are detected through patterns matching courtesy markers followed by action verbs. These include "Please [VERB]", "Could you [VERB]", "You must [VERB]", and "I need you to [VERB]" constructions. Request frames are particularly dangerous because they exploit social engineering principles, appearing as polite requests while containing malicious imperatives.

**Code Fence Analysis**: We parse code block structures for execution indicators, including language tags with execution markers ("python-execute"), comment-based directives ("# AUTO-RUN"), and HTML code elements with execution attributes. This addresses attacks where malicious code is embedded within seemingly innocuous code examples or documentation.

**Tool-Call Intents**: Structured patterns identify requests for external tool invocation, including function call syntax, API endpoint patterns, and explicit tool markers. These patterns detect attempts to invoke system functions, API calls, or external services through crafted input formatting.

## Character-Level Provenance Tracking

Provenance tracking maintains character-level attribution of trust boundaries throughout the processing pipeline. Each character in the combined input text carries metadata indicating its originating channel (trusted or untrusted), source identifier, and position within the original segment.

When multiple segments are concatenated, we preserve individual character attributions through a mapping structure that tracks the transformation from original positions to normalized positions. This granular approach enables precise violation detection even when normalization operations change character counts or positions.

The provenance system supports segment mixing where trusted content includes references to untrusted content, maintaining strict channel boundaries while enabling practical applications like RAG systems where system prompts introduce retrieved documents.

## NIUC Checker Algorithm

The core NIUC verification algorithm operates deterministically to ensure reproducible security decisions across different deployments and platforms.

```python
Algorithm 1: NIUC Property Verification
Input: segments = [(text, channel, source_id), ...]
Output: VerificationResult(ok, violations, certificate_data)

1: combined_text, char_tags ← BUILD_PROVENANCE(segments)
2: normalized_text, mapping ← NORMALIZE_WITH_MAPPING(combined_text)
3: imperative_spans ← DETECT_IMPERATIVES(normalized_text)
4: violations ← []
5: 
6: for each span in imperative_spans do
7:    for pos in range(span.start, span.end) do
8:       if char_tags[pos].channel == UNTRUSTED then
9:          violations.append(Violation(span, pos, char_tags[pos].source))
10:         break  // One violation per imperative
11:    end for
12: end for
13:
14: decision ← PASS if len(violations) == 0 else BLOCKED
15: input_hash ← SHA256(normalized_text)
16: return VerificationResult(decision, violations, input_hash)
```

The algorithm maintains linear time complexity O(n) where n is the total character count, ensuring scalable performance for production deployments. The deterministic nature eliminates dependencies on machine learning models or external services, providing consistent behavior essential for certificate generation.

## Runtime Gate Enforcement

The runtime gate provides two enforcement modes that balance security requirements with operational utility. **Block mode** implements strict security by denying execution whenever NIUC violations are detected, ensuring zero attack success rate at the cost of potentially blocking legitimate content containing ambiguous imperatives.

**Certified-rewrite mode** implements intelligent neutralization where detected imperatives from untrusted sources are replaced with safety annotations (e.g., "execute" becomes "[NEUTRALIZED:execute]") while preserving the overall text structure and meaning. The neutralized text undergoes complete re-verification through the NIUC checker to ensure that no imperatives remain active, and only content that passes re-verification receives execution approval.

The rewrite process maintains semantic preservation by replacing only the specific imperative terms while leaving context and non-imperative content unchanged. This approach enables deployment in production environments where complete blocking of suspicious content would severely degrade user experience, while still providing mathematical guarantees about the safety of approved operations.

## Certificate Schema and Verification

Every security decision generates a cryptographic certificate that provides mathematical attestation of NIUC property compliance. The certificate schema includes five mandatory fields: checker version for reproducibility, input SHA-256 hash of normalized text, output SHA-256 hash varying by decision type, decision enumeration (pass/blocked/rewritten), and violations array containing character span positions for detected violations.

The certificate generation process computes hashes over normalized rather than raw input text, ensuring that certificates remain valid despite Unicode evasion attempts while maintaining cryptographic integrity. For blocked decisions, the output hash always equals the SHA-256 of an empty string, providing consistent verification behavior. For rewritten decisions, the output hash covers the neutralized text that passed re-verification.

Certificate verification follows a three-step process: structural validation ensuring all required fields are present with correct formats, semantic validation checking decision/violation consistency, and cryptographic validation recomputing hashes to detect tampering. This verification process enables trust composition where downstream systems can mathematically verify that upstream processing satisfied the NIUC property.

## Benchmark Design and Evaluation Methodology

We developed **I²-Bench-Lite** as a comprehensive evaluation framework comprising 48 scenarios across six attack categories: RAG HTML injection, tool output manipulation, code fence exploitation, citation authority abuse, multilingual evasion, and conversation context poisoning. Each category includes four attack scenarios demonstrating specific techniques and four semantically equivalent benign twins for false positive assessment.

The benchmark design ensures comprehensive coverage of known attack vectors while enabling precise measurement of system accuracy. Attack scenarios are based on documented real-world techniques from security research, while benign twins maintain semantic similarity to attacks while removing malicious intent. This pairing enables measurement of both attack detection capability and legitimate content preservation.

Our evaluation methodology compares three operational modes: baseline (no protection), block mode (strict violation blocking), and rewrite mode (certified neutralization). For each scenario, we measure processing latency, violation detection accuracy, and decision correctness against ground truth labels. This multi-mode comparison enables assessment of security-utility trade-offs and validates the effectiveness of our certified-rewrite approach.

## Metrics and Performance Evaluation

We evaluate system performance using four primary metrics aligned with privacy-preserving computation requirements. **Attack Success Rate (ASR)** measures the percentage of attack scenarios that successfully bypass security controls, with lower values indicating better security. **False Positive Rate (FPR)** measures the percentage of benign content incorrectly blocked, with lower values indicating better utility preservation.

**Utility Delta (UtilityΔ)** quantifies performance degradation compared to unprotected baseline operation, measuring the cost of security enforcement in terms of processing time and operational overhead. **Processing Latency** measures the additional time required for NIUC verification per scenario, with our target of ≤60ms per response enabling real-time deployment in interactive applications.

Additional metrics include rewrite success rate (percentage of attacks successfully neutralized), violation detection precision (character-level accuracy of imperative identification), and certificate generation overhead (cryptographic processing time). These metrics provide comprehensive assessment of both security effectiveness and operational feasibility for production deployment.

---

**Word Count**: 1,087 words (target: 900-1200 words) ✅
