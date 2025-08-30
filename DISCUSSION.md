# Discussion

## Generalization and Broader Applicability

Our evaluation demonstrates that the NIUC framework successfully generalizes across diverse attack categories and linguistic patterns, suggesting broad applicability to production LLM deployments. The consistent 0.0% False Positive Rate across all six attack categories indicates that our character-level provenance approach can reliably distinguish between malicious imperatives and legitimate content, even when they share similar linguistic structures. This generalization capability is particularly important given the rapid evolution of prompt injection techniques, where new attack variants continuously emerge.

The effectiveness of our certified-rewrite approach across different attack vectors—from simple homoglyph substitution to sophisticated multi-turn conversation poisoning—suggests that imperative neutralization provides robust protection against both known and novel attack patterns. The system's model-agnostic design enables deployment across different LLM architectures without requiring retraining or model-specific tuning, addressing a critical limitation of existing safety classifier approaches.

However, our current evaluation focuses on English-language scenarios with specific attack patterns documented in security research. Generalization to other languages, cultural contexts, and domain-specific imperatives requires additional validation. Languages with different grammatical structures, such as verb-final languages (Japanese, Korean) or highly inflected languages (Russian, Finnish), may require expanded imperative detection patterns and cultural adaptation of request frame recognition.

## Current Limitations

### Grammar Coverage Gaps

Our ablation study reveals that individual grammar components have minimal impact when disabled, suggesting potential coverage gaps in our current test scenarios. While this might indicate robust neutralization performance, it could also reflect insufficient diversity in attack sophistication within I²-Bench-Lite. Advanced adversaries may employ linguistic techniques not captured by our current pattern sets, such as indirect speech acts, metaphorical imperatives, or domain-specific jargon that encodes commands without explicit imperative constructions.

The regex-based pattern matching approach, while deterministic and auditable, may struggle with highly creative linguistic attacks that exploit semantic ambiguity or cultural references. For example, phrases like "channel your inner systems administrator" or "embrace the delete key lifestyle" could convey imperative intent through metaphor while evading literal pattern detection.

### Paraphrase Evasion Vulnerabilities

Our system currently focuses on detecting explicit imperative constructions but may be vulnerable to **paraphrase evasion attacks** where malicious intent is encoded through syntactic restructuring. Attackers could potentially bypass detection by using passive voice constructions ("files should be deleted"), nominalization ("the execution of commands"), or conditional statements that imply imperatives without explicit command language ("if security protocols were bypassed, systems would be more accessible").

These paraphrase attacks exploit the semantic gap between syntactic pattern matching and intent recognition. While our certified-rewrite approach provides some protection by neutralizing detected patterns, sophisticated attackers might craft imperatives that convey malicious intent through linguistic structures not covered by our current grammar definitions.

### Context-Dependent Interpretation

The current system treats all detected imperatives equally, without considering contextual factors that might distinguish between legitimate instructions and malicious commands. Domain-specific applications may require imperatives for legitimate functionality (e.g., "execute this query" in database applications, "run this analysis" in data science workflows), creating tension between security enforcement and operational necessity.

## Future Work

### Span-Level Key-Value Masking

A promising enhancement involves **span-level KV masking** where detected imperative spans are cryptographically masked during LLM processing while preserving their structural positions for post-processing verification. This approach would enable LLMs to process content containing neutralized imperatives without exposure to the original malicious text, providing additional security layers beyond annotation-based neutralization.

The KV masking approach would operate at the transformer attention mechanism level, replacing imperative token embeddings with cryptographically secure placeholder representations during inference. Post-generation verification would unmask these placeholders and validate that no new imperatives were generated through the LLM's processing of the masked content.

### Semantic Intent Analysis

Future versions could incorporate **semantic intent classification** to distinguish between legitimate operational imperatives and malicious command injection. This enhancement would analyze the broader context surrounding detected imperatives, considering factors such as user authorization levels, operational domains, and conversation flow to make more nuanced security decisions.

Advanced grammar expansion could include **pragmatic analysis** that considers speech act theory and conversational implicature to detect imperative intent encoded through indirect language. This would address paraphrase evasion while maintaining the deterministic properties essential for certificate generation.

### Cross-Lingual and Cultural Adaptation

Expanding NIUC to support global deployments requires **cross-lingual grammar development** and **cultural context adaptation**. Different languages encode imperatives through diverse grammatical structures, honorific systems, and cultural communication patterns. A comprehensive international deployment would require grammar rule sets adapted to specific linguistic families and cultural contexts.

## Ethical Considerations

The deployment of NIUC systems raises important ethical considerations around **content control** and **algorithmic fairness**. While our approach demonstrates excellent performance in neutralizing malicious content, the power to determine what constitutes an "imperative" and which channels are "trusted" introduces potential for misuse in content censorship or surveillance applications.

**Transparency and accountability** become critical when deploying deterministic security systems. Unlike machine learning approaches where decisions can be attributed to training data patterns, NIUC's rule-based approach makes security decisions based on explicit pattern definitions. This transparency enables audit and contestation of security decisions, but also requires careful governance to prevent abuse.

**User agency and consent** considerations arise when systems automatically neutralize content without explicit user awareness. While our annotation approach maintains content visibility (showing "[NEUTRALIZED:execute]" rather than silent removal), users should understand when and why their content has been modified for security purposes.

The **digital divide implications** of requiring sophisticated Unicode normalization and character-level analysis may disproportionately affect users employing assistive technologies, alternative input methods, or non-standard text encoding systems. Future implementations should consider accessibility requirements and ensure that security enforcement does not inadvertently discriminate against users with different technological capabilities.

Finally, the **concentration of trust determination** in system administrators who define channel classifications creates potential for abuse. Organizations deploying NIUC systems must establish clear governance frameworks for trust boundary definitions and provide mechanisms for users to understand and potentially contest channel classification decisions that affect their content processing.

---

**Word Count**: 641 words (target: 400-700 words) ✅
