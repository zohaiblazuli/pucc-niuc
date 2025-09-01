# Methods

## NIUC Framework Design

Our Non-Interactive Universal Computing (NIUC) framework implements deterministic security enforcement through three core components:

### 1. Deterministic Checker (≤500 LOC)
- **Unicode Normalization**: Prevents homoglyph and zero-width character evasion
- **Character-Level Provenance Tracking**: Attributes each character to trusted/untrusted channels
- **Imperative Grammar Detection**: Regex-based pattern matching for command identification
- **Cryptographic Attestation**: Mathematical proofs of security properties

### 2. Runtime Gate with Dual Modes
- **Block Mode**: Prevents malicious content execution entirely
- **Certified-Rewrite Mode**: Neutralizes attacks while preserving utility through imperative annotation

### 3. NIUC Property Enforcement
```
∀ imperative i ∈ imperatives(I), provenance(i) ⊆ trusted_chars(C)
```
This ensures no imperative from untrusted channels reaches side-effectful operations.

## Comprehensive Evaluation Methodology

### Hydra-Bench-500: Comprehensive Evaluation Dataset
We designed a comprehensive 500-scenario benchmark covering:
- **17 Attack Categories**: RAG HTML injection, tool output manipulation, code fence execution, citation authority abuse, multilingual evasion, multi-turn poisoning, advanced Unicode evasion, nested code confusion, steganographic encoding, template injection, social engineering, context poisoning, advanced citation abuse, path traversal injection, command chaining, privilege escalation, time-based attacks
- **50+ Attack Techniques**: LLM01 taxonomy-based systematic coverage of documented attack vectors
- **3 Sophistication Levels**: Basic (30%), Intermediate (45%), Advanced (25%)
- **304 Attack Scenarios** (expected blocked) + **196 Benign Scenarios** (expected pass)
- **10x Scale Expansion**: Systematic expansion from foundational I²-Bench-Lite (52 → 500 scenarios)

### Universal Model Evaluation
We evaluated NIUC across 5 major LLM architectures representing the entire ecosystem:

| Model | Provider | Architecture | Context Window | Cost/1K Tokens |
|-------|----------|--------------|----------------|----------------|
| **GPT-4** | OpenAI | Transformer | 128K | $0.03 |
| **Claude 3.7 Sonnet** | Anthropic | Transformer | 200K | $0.003 |
| **Google Gemini 2.5 Flash** | Google | Transformer | 1M | $0.000075 |
| **Qwen3 8B** | Alibaba | Transformer | 32K | $0.0002 |
| **DeepSeek V3.1** | DeepSeek | Transformer | 128K | $0.0002 |

### Real API Validation
- **Production APIs**: All models tested via their official APIs
- **Token Tracking**: Comprehensive token usage and cost analysis
- **Latency Measurement**: Real-world performance assessment
- **Error Handling**: Robust API error detection and reporting

## Performance Metrics

### Security Metrics
- **Attack Success Rate (ASR)**: Percentage of attacks bypassing security
- **False Positive Rate (FPR)**: Percentage of benign content incorrectly blocked
- **Neutralization Rate**: Percentage of attacks safely neutralized in rewrite mode

### Performance Metrics
- **Processing Latency**: Time for NIUC verification and model inference
- **Token Efficiency**: Tokens consumed per scenario
- **Cost Analysis**: Total cost across all scenarios
- **API Reliability**: Error rates and availability

### Universal Effectiveness Validation
- **Model-Agnostic Security**: Identical security performance across architectures
- **Architecture Independence**: No model-specific tuning required
- **Cross-Provider Validation**: Consistent results across different API providers
