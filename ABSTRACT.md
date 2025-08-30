# Abstract

## Privacy-Preserving Computing with Non-Interactive Universal Computation: Cryptographic Enforcement Against Indirect Prompt Injection

Large Language Model applications face critical vulnerabilities from indirect prompt injection, where malicious imperatives in untrusted content bypass input filters to trigger unauthorized operations. Current mitigations rely on probabilistic detection rather than deterministic enforcement, creating gaps between threat identification and prevention. We introduce **Non-Interactive Universal Computing (NIUC)**, ensuring no imperative from untrusted channels reaches side-effectful operations.

Our system implements: (1) a deterministic checker (224 LOC) with Unicode normalization and character-level provenance tracking, (2) a runtime gate with blocking and certified-rewrite modes, and (3) cryptographic certificates for computation integrity attestation. NIUC property enforcement follows: ∀ imperative i ∈ imperatives(I), provenance(i) ⊆ trusted_chars(C).

We evaluate using **I²-Bench-Lite**, a benchmark with 48 scenarios across six attack categories, each including benign twins for false-positive assessment. Our certified-rewrite mode achieves 0.0% False Positive Rate while neutralizing 100% of attacks through imperative annotation and re-verification, with 0.2ms latency. Block mode shows 8.3% Attack Success Rate but 12.5% FPR, confirming neutralization's utility value.

Contributions include: (1) formal NIUC property definition, (2) production-ready deterministic implementation (≤500 LOC), (3) I²-Bench-Lite benchmark for reproducible evaluation, and (4) demonstration that cryptographic enforcement can replace probabilistic detection while preserving security and utility.

---

**Word Count**: 187 words (target: 150-200 words) ✅

*This abstract synthesizes key elements from docs/lit_review.md (problem statement), docs/spec-niuc.md (NIUC property definition), and results/metrics.csv (headline performance numbers) to provide a complete research summary suitable for academic publication.*
