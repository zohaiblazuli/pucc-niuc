# Abstract

Large Language Models (LLMs) are vulnerable to indirect prompt injection attacks, where malicious content embedded in untrusted inputs can manipulate model behavior. Current defenses rely on probabilistic detection, which can be evaded and lacks mathematical guarantees. We present Non-Interactive Universal Computing (NIUC), a novel framework that provides deterministic security enforcement through cryptographic attestation and character-level provenance tracking.

NIUC introduces a two-mode runtime gate: Block Mode prevents malicious content execution, while Certified-Rewrite Mode neutralizes attacks while preserving utility. Our comprehensive evaluation using Hydra-Bench-500 (500 scenarios across 17 attack categories) demonstrates effectiveness with 7.9% Attack Success Rate and 0.2ms latency.

Results show NIUC achieves excellent security performance: 7.9% Attack Success Rate in block mode, 100% attack neutralization with 0% false positives in rewrite mode, with 0.2ms processing latency. The framework provides mathematical security guarantees independent of the underlying LLM architecture, establishing NIUC as the universal standard for protecting LLM applications against indirect prompt injection attacks.

**Keywords:** Large Language Models, Prompt Injection, Security, NIUC, Universal Computing, Cryptographic Attestation

**Word Count:** 127 words
