#!/usr/bin/env python3
"""
Ablation study for PCC-NIUC system components.
Tests system performance with different features toggled on/off.
"""

import argparse
import json
import time
import sys
import os
from pathlib import Path
from statistics import mean
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

# Add pcc module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pcc.normalizer import TextNormalizer
from pcc.imperative_grammar import ImperativeDetector
from pcc.provenance import ProvenanceBuilder, ChannelType
from pcc.checker import NIUCChecker, VerificationResult
from pcc.runtime_gate import RuntimeGate, RuntimeMode


class AblationConfig:
    """Configuration for ablation study toggles."""
    
    def __init__(self):
        # Feature toggles
        self.normalization_enabled = True
        self.imperative_mood_enabled = True
        self.request_frames_enabled = True
        self.code_fence_enabled = True
        self.char_level_provenance = True  # False = token-level
        self.rewrite_enabled = True
        
        # Configuration name for reporting
        self.name = "full_system"
    
    def copy(self) -> 'AblationConfig':
        """Create a copy of this configuration."""
        new_config = AblationConfig()
        new_config.normalization_enabled = self.normalization_enabled
        new_config.imperative_mood_enabled = self.imperative_mood_enabled
        new_config.request_frames_enabled = self.request_frames_enabled
        new_config.code_fence_enabled = self.code_fence_enabled
        new_config.char_level_provenance = self.char_level_provenance
        new_config.rewrite_enabled = self.rewrite_enabled
        new_config.name = self.name
        return new_config


class AblatedNormalizer(TextNormalizer):
    """Normalizer with optional normalization steps."""
    
    def __init__(self, config: AblationConfig):
        super().__init__()
        self.config = config
    
    def normalize(self, text: str) -> Tuple[str, Dict[str, int]]:
        """Normalize text with optional steps based on config."""
        if not self.config.normalization_enabled:
            # Skip normalization entirely
            return text, {
                'original_length': len(text),
                'nfkc_changes': 0,
                'case_changes': 0,
                'zero_width_removed': 0,
                'homoglyphs_mapped': 0,
            }
        
        # Use full normalization
        return super().normalize(text)


class AblatedImperativeDetector(ImperativeDetector):
    """Imperative detector with optional grammar groups."""
    
    def __init__(self, config: AblationConfig):
        super().__init__()
        self.config = config
        self._apply_ablation()
    
    def _apply_ablation(self):
        """Apply ablation configuration to disable specific pattern groups."""
        if not self.config.imperative_mood_enabled:
            # Disable direct imperative verbs and modals
            self.compiled_patterns['direct_verbs'] = []
            self.compiled_patterns['modals'] = []
        
        if not self.config.request_frames_enabled:
            # Disable request frame patterns
            self.compiled_patterns['requests'] = []
        
        if not self.config.code_fence_enabled:
            # Disable code fence patterns
            self.compiled_patterns['code_fences'] = []
            self.compiled_patterns['tool_calls'] = []


class AblatedProvenanceBuilder(ProvenanceBuilder):
    """Provenance builder with optional token-level tracking."""
    
    def __init__(self, config: AblationConfig):
        super().__init__()
        self.config = config
    
    def build_from_segments(self, segments: List[Tuple[str, str, Optional[str]]]) -> Tuple[str, List]:
        """Build provenance with optional token-level granularity."""
        if self.config.char_level_provenance:
            # Use character-level provenance (default)
            return super().build_from_segments(segments)
        else:
            # Use token-level provenance (simplified)
            return self._build_token_level_provenance(segments)
    
    def _build_token_level_provenance(self, segments: List[Tuple[str, str, Optional[str]]]) -> Tuple[str, List]:
        """Build token-level provenance (simplified implementation)."""
        self.segments.clear()
        
        # For token-level, we'll approximate by treating words as tokens
        all_tokens = []
        token_tags = []
        
        for segment_idx, (text, channel_str, source_id) in enumerate(segments):
            channel = ChannelType(channel_str)
            
            # Split into tokens (simple whitespace splitting)
            tokens = text.split()
            
            for token in tokens:
                all_tokens.append(token)
                # Create simplified tag (one per token instead of per character)
                token_tags.append({
                    'channel': channel,
                    'source_id': source_id or f"segment_{segment_idx}",
                    'token_index': len(all_tokens) - 1
                })
        
        combined_text = ' '.join(all_tokens)
        
        # Convert back to character-level tags for compatibility
        char_tags = []
        char_pos = 0
        
        for token_idx, token in enumerate(all_tokens):
            token_tag = token_tags[token_idx]
            
            # Assign same tag to all characters in this token
            for char_idx in range(len(token)):
                char_tags.append(type('CharacterTag', (), {
                    'channel': token_tag['channel'],
                    'source_id': token_tag['source_id'],
                    'original_position': char_pos + char_idx,
                    'segment_index': token_idx
                })())
            
            char_pos += len(token)
            
            # Add space character tag if not the last token
            if token_idx < len(all_tokens) - 1:
                char_tags.append(type('CharacterTag', (), {
                    'channel': token_tag['channel'],
                    'source_id': token_tag['source_id'],
                    'original_position': char_pos,
                    'segment_index': token_idx
                })())
                char_pos += 1
        
        self.combined_text = combined_text
        self.character_tags = char_tags
        
        return combined_text, char_tags


class AblatedNIUCChecker(NIUCChecker):
    """NIUC checker with ablation configuration."""
    
    def __init__(self, config: AblationConfig):
        self.config = config
        self.normalizer = AblatedNormalizer(config)
        self.imperative_detector = AblatedImperativeDetector(config)
        self.version = f"1.0.0-ablated-{config.name}"
    
    def verify(self, segments: List[Tuple[str, str, Optional[str]]]) -> VerificationResult:
        """Verify with ablation configuration."""
        if not segments:
            raise ValueError("Segments list cannot be empty")
        
        # Step 1: Build provenance-tagged text
        builder = AblatedProvenanceBuilder(self.config)
        combined_text, character_tags = builder.build_from_segments(segments)
        raw_text = combined_text
        
        # Step 2: Normalize text (may be disabled)
        normalized_text, norm_stats = self.normalizer.normalize(combined_text)
        
        # Step 3: Detect imperatives (may have disabled pattern groups)
        imperative_spans = self.imperative_detector.get_violation_ranges(normalized_text)
        
        # Step 4: Check for NIUC violations using ablated provenance
        normalized_builder = self._build_normalized_provenance(segments, normalized_text)
        violations = normalized_builder.detect_violations(imperative_spans)
        
        # Step 5: Determine decision
        has_violations = len(violations) > 0
        decision = "blocked" if has_violations else "pass"
        
        violation_spans = [(v['imperative_start'], v['imperative_end']) for v in violations]
        input_hash = self.normalizer.compute_hash(normalized_text)
        
        # Step 6: Compile statistics
        stats = {
            'checker_version': self.version,
            'config_name': self.config.name,
            'normalization': norm_stats,
            'imperative_count': len(imperative_spans),
            'violation_count': len(violations),
            'total_characters': len(normalized_text),
            'segments_processed': len(segments),
            'ablation_features': {
                'normalization': self.config.normalization_enabled,
                'imperative_mood': self.config.imperative_mood_enabled,
                'request_frames': self.config.request_frames_enabled,
                'code_fence': self.config.code_fence_enabled,
                'char_level_provenance': self.config.char_level_provenance,
                'rewrite': self.config.rewrite_enabled
            }
        }
        
        return VerificationResult(
            ok=not has_violations,
            violations=violation_spans,
            input_sha256=input_hash,
            decision=decision,
            stats=stats,
            raw_text=raw_text,
            normalized_text=normalized_text
        )


class AblationStudy:
    """Runs ablation study across different system configurations."""
    
    def __init__(self):
        self.configurations = self._create_ablation_configurations()
    
    def _create_ablation_configurations(self) -> Dict[str, AblationConfig]:
        """Create all ablation configurations to test."""
        configs = {}
        
        # Full system (baseline for comparison)
        full_config = AblationConfig()
        full_config.name = "full_system"
        configs["full_system"] = full_config
        
        # (a) No normalization
        no_norm_config = full_config.copy()
        no_norm_config.normalization_enabled = False
        no_norm_config.name = "no_normalization"
        configs["no_normalization"] = no_norm_config
        
        # (b) Remove grammar groups - imperative mood
        no_imperative_config = full_config.copy()
        no_imperative_config.imperative_mood_enabled = False
        no_imperative_config.name = "no_imperative_mood"
        configs["no_imperative_mood"] = no_imperative_config
        
        # (b) Remove grammar groups - request frames
        no_requests_config = full_config.copy()
        no_requests_config.request_frames_enabled = False
        no_requests_config.name = "no_request_frames"
        configs["no_request_frames"] = no_requests_config
        
        # (b) Remove grammar groups - code fence
        no_code_fence_config = full_config.copy()
        no_code_fence_config.code_fence_enabled = False
        no_code_fence_config.name = "no_code_fence"
        configs["no_code_fence"] = no_code_fence_config
        
        # (c) Token-level provenance
        token_provenance_config = full_config.copy()
        token_provenance_config.char_level_provenance = False
        token_provenance_config.name = "token_level_provenance"
        configs["token_level_provenance"] = token_provenance_config
        
        # (d) Rewrite off (block only)
        no_rewrite_config = full_config.copy()
        no_rewrite_config.rewrite_enabled = False
        no_rewrite_config.name = "no_rewrite"
        configs["no_rewrite"] = no_rewrite_config
        
        # Combined ablations for more extreme testing
        minimal_config = AblationConfig()
        minimal_config.normalization_enabled = False
        minimal_config.imperative_mood_enabled = False
        minimal_config.request_frames_enabled = True  # Keep basic request detection
        minimal_config.code_fence_enabled = False
        minimal_config.char_level_provenance = False
        minimal_config.rewrite_enabled = False
        minimal_config.name = "minimal_system"
        configs["minimal_system"] = minimal_config
        
        return configs
    
    def run_ablation_study(self, scenarios: List[Dict[str, Any]], verbose: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Run ablation study across all configurations.
        
        Args:
            scenarios: List of scenario dictionaries
            verbose: Whether to print detailed progress
            
        Returns:
            Dictionary mapping config names to results
        """
        print(f"🔬 Starting ablation study with {len(scenarios)} scenarios...")
        print(f"📊 Testing {len(self.configurations)} configurations...")
        
        all_results = {}
        
        for config_name, config in self.configurations.items():
            if verbose:
                print(f"\n🧪 Testing configuration: {config_name}")
                self._print_config_details(config)
            else:
                print(f"\n🧪 Testing {config_name}...")
            
            config_results = self._run_configuration(scenarios, config)
            all_results[config_name] = config_results
            
            # Compute quick metrics
            metrics = self._compute_metrics(config_results)
            print(f"   ✅ ASR: {metrics['asr']:.1f}% | FPR: {metrics['fpr']:.1f}% | Latency: {metrics['avg_latency_ms']:.1f}ms")
        
        return all_results
    
    def _print_config_details(self, config: AblationConfig):
        """Print detailed configuration for verbose mode."""
        print(f"   Features enabled:")
        print(f"   - Normalization: {'✅' if config.normalization_enabled else '❌'}")
        print(f"   - Imperative mood: {'✅' if config.imperative_mood_enabled else '❌'}")
        print(f"   - Request frames: {'✅' if config.request_frames_enabled else '❌'}")
        print(f"   - Code fence: {'✅' if config.code_fence_enabled else '❌'}")
        print(f"   - Char-level provenance: {'✅' if config.char_level_provenance else '❌'}")
        print(f"   - Rewrite mode: {'✅' if config.rewrite_enabled else '❌'}")
    
    def _run_configuration(self, scenarios: List[Dict[str, Any]], config: AblationConfig) -> List[Dict[str, Any]]:
        """Run scenarios with specific ablation configuration."""
        checker = AblatedNIUCChecker(config)
        results = []
        
        for scenario in scenarios:
            segments = [
                (scenario['trusted'], 'trusted', 'trusted_input'),
                (scenario['untrusted'], 'untrusted', 'untrusted_input')
            ]
            
            start_time = time.perf_counter()
            
            try:
                # Run verification
                verification = checker.verify(segments)
                
                # Determine mode to test
                if config.rewrite_enabled:
                    # Test rewrite mode (primary mode for ablation)
                    gate = RuntimeGate(RuntimeMode.CERTIFIED_REWRITE)
                    gate.checker = checker  # Use ablated checker
                    gate_result = gate.process(segments)
                    
                    actual_decision = 'pass' if gate_result.allowed else 'blocked'
                    rewrite_applied = gate_result.rewrite_applied
                else:
                    # Test block mode only (rewrite disabled)
                    actual_decision = 'pass' if verification.ok else 'blocked'
                    rewrite_applied = False
                
                end_time = time.perf_counter()
                latency_ms = (end_time - start_time) * 1000
                
                results.append({
                    'scenario_id': scenario['id'],
                    'category': scenario['category'],
                    'tactic': scenario['tactic'],
                    'expected': scenario['expected'],
                    'actual': actual_decision,
                    'correct': (actual_decision == scenario['expected']),
                    'violations': len(verification.violations),
                    'latency_ms': round(latency_ms, 2),
                    'rewrite_applied': rewrite_applied,
                    'config_name': config.name
                })
            
            except Exception as e:
                end_time = time.perf_counter()
                latency_ms = (end_time - start_time) * 1000
                
                results.append({
                    'scenario_id': scenario['id'],
                    'category': scenario['category'],
                    'tactic': scenario['tactic'],
                    'expected': scenario['expected'],
                    'actual': 'error',
                    'correct': False,
                    'violations': 0,
                    'latency_ms': round(latency_ms, 2),
                    'rewrite_applied': False,
                    'config_name': config.name,
                    'error': str(e)
                })
        
        return results
    
    def _compute_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Compute metrics for a configuration."""
        attack_results = [r for r in results if r['expected'] == 'blocked']
        benign_results = [r for r in results if r['expected'] == 'pass']
        
        # ASR: Attack Success Rate
        successful_attacks = sum(1 for r in attack_results if r['actual'] == 'pass')
        asr = (successful_attacks / len(attack_results)) * 100 if attack_results else 0
        
        # FPR: False Positive Rate
        blocked_benign = sum(1 for r in benign_results if r['actual'] == 'blocked')
        fpr = (blocked_benign / len(benign_results)) * 100 if benign_results else 0
        
        # Accuracy
        correct_results = sum(1 for r in results if r['correct'])
        accuracy = (correct_results / len(results)) * 100 if results else 0
        
        # Latency
        latencies = [r['latency_ms'] for r in results if r['latency_ms'] > 0]
        avg_latency = mean(latencies) if latencies else 0
        
        return {
            'asr': round(asr, 1),
            'fpr': round(fpr, 1),
            'accuracy': round(accuracy, 1),
            'avg_latency_ms': round(avg_latency, 1),
            'total_scenarios': len(results),
            'attack_scenarios': len(attack_results),
            'benign_scenarios': len(benign_results)
        }
    
    def export_ablation_report(self, all_results: Dict[str, List[Dict]], output_file: str = "ablation_report.md"):
        """Export ablation study results as Markdown with bar charts."""
        
        # Compute metrics for all configurations
        all_metrics = {}
        for config_name, results in all_results.items():
            all_metrics[config_name] = self._compute_metrics(results)
        
        # Get baseline (full system) metrics for delta computation
        baseline_metrics = all_metrics.get('full_system', {})
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# PCC-NIUC Ablation Study Results\n\n")
            f.write(f"**Study Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Total Scenarios**: {baseline_metrics.get('total_scenarios', 0)}\n")
            f.write(f"**Configurations Tested**: {len(self.configurations)}\n\n")
            
            f.write("## Configuration Overview\n\n")
            f.write("| Configuration | Normalization | Imperative Mood | Request Frames | Code Fence | Char Provenance | Rewrite |\n")
            f.write("|---------------|---------------|-----------------|----------------|------------|-----------------|----------|\n")
            
            for config_name, config in self.configurations.items():
                f.write(f"| {config_name} | {'✅' if config.normalization_enabled else '❌'} | {'✅' if config.imperative_mood_enabled else '❌'} | {'✅' if config.request_frames_enabled else '❌'} | {'✅' if config.code_fence_enabled else '❌'} | {'✅' if config.char_level_provenance else '❌'} | {'✅' if config.rewrite_enabled else '❌'} |\n")
            
            f.write("\n## Performance Metrics\n\n")
            f.write("| Configuration | ASR (%) | FPR (%) | Accuracy (%) | Latency (ms) |\n")
            f.write("|---------------|---------|---------|--------------|-------------|\n")
            
            for config_name in ['full_system', 'no_normalization', 'no_imperative_mood', 'no_request_frames', 'no_code_fence', 'token_level_provenance', 'no_rewrite', 'minimal_system']:
                if config_name in all_metrics:
                    m = all_metrics[config_name]
                    f.write(f"| **{config_name}** | {m['asr']} | {m['fpr']} | {m['accuracy']} | {m['avg_latency_ms']} |\n")
            
            # Delta analysis vs full system
            f.write("\n## Delta Analysis (vs Full System)\n\n")
            
            if baseline_metrics:
                f.write("### ASR Delta (Attack Success Rate Change)\n")
                f.write("```\n")
                for config_name, metrics in all_metrics.items():
                    if config_name != 'full_system':
                        delta = metrics['asr'] - baseline_metrics['asr']
                        bar_length = int(abs(delta) / 10) if abs(delta) < 100 else 10
                        bar_char = '█' if delta > 0 else '▌'
                        bar = bar_char * bar_length
                        f.write(f"{config_name:20} {delta:+6.1f}% {'':5} {bar}\n")
                f.write("```\n\n")
                
                f.write("### FPR Delta (False Positive Rate Change)\n")
                f.write("```\n")
                for config_name, metrics in all_metrics.items():
                    if config_name != 'full_system':
                        delta = metrics['fpr'] - baseline_metrics['fpr']
                        bar_length = int(abs(delta) / 5) if abs(delta) < 50 else 10
                        bar_char = '█' if delta > 0 else '▌'
                        bar = bar_char * bar_length
                        f.write(f"{config_name:20} {delta:+6.1f}% {'':5} {bar}\n")
                f.write("```\n\n")
                
                f.write("### Latency Delta (Processing Time Change)\n")
                f.write("```\n")
                for config_name, metrics in all_metrics.items():
                    if config_name != 'full_system':
                        delta = metrics['avg_latency_ms'] - baseline_metrics['avg_latency_ms']
                        bar_length = int(abs(delta) / 2) if abs(delta) < 20 else 10
                        bar_char = '█' if delta > 0 else '▌'
                        bar = bar_char * bar_length
                        f.write(f"{config_name:20} {delta:+6.1f}ms {'':4} {bar}\n")
                f.write("```\n\n")
            
            # Feature importance analysis
            f.write("## Feature Importance Analysis\n\n")
            
            if baseline_metrics:
                feature_impacts = []
                
                for config_name, metrics in all_metrics.items():
                    if config_name != 'full_system':
                        asr_impact = metrics['asr'] - baseline_metrics['asr']
                        fpr_impact = metrics['fpr'] - baseline_metrics['fpr']
                        latency_impact = metrics['avg_latency_ms'] - baseline_metrics['avg_latency_ms']
                        
                        # Calculate overall security impact (higher ASR + higher FPR = worse)
                        security_impact = asr_impact + fpr_impact
                        
                        feature_impacts.append({
                            'config': config_name,
                            'asr_impact': asr_impact,
                            'fpr_impact': fpr_impact,
                            'latency_impact': latency_impact,
                            'security_impact': security_impact
                        })
                
                # Sort by security impact (most important features have highest impact when removed)
                feature_impacts.sort(key=lambda x: x['security_impact'], reverse=True)
                
                f.write("**Most Critical Features** (ranked by security impact when disabled):\n\n")
                for i, impact in enumerate(feature_impacts[:5], 1):
                    f.write(f"{i}. **{impact['config'].replace('_', ' ').title()}**\n")
                    f.write(f"   - ASR impact: {impact['asr_impact']:+.1f}%\n")
                    f.write(f"   - FPR impact: {impact['fpr_impact']:+.1f}%\n")
                    f.write(f"   - Security degradation: {impact['security_impact']:+.1f}%\n\n")
            
            f.write("## Recommendations\n\n")
            f.write("Based on ablation study results:\n\n")
            
            # Add specific recommendations based on results
            if 'no_normalization' in all_metrics:
                no_norm_asr = all_metrics['no_normalization']['asr']
                if no_norm_asr > baseline_metrics.get('asr', 0) + 10:
                    f.write("- **Unicode normalization is critical** - removing it significantly increases attack success rate\n")
            
            if 'no_request_frames' in all_metrics:
                no_req_asr = all_metrics['no_request_frames']['asr']
                if no_req_asr > baseline_metrics.get('asr', 0) + 5:
                    f.write("- **Request frame detection is important** - polite attack patterns are common\n")
            
            if 'token_level_provenance' in all_metrics:
                token_fpr = all_metrics['token_level_provenance']['fpr']
                if token_fpr > baseline_metrics.get('fpr', 0) + 2:
                    f.write("- **Character-level provenance provides better precision** than token-level\n")
            
            f.write("\n---\n")
            f.write(f"*Generated by PCC-NIUC ablation study on {time.strftime('%Y-%m-%d %H:%M:%S')}*\n")
        
        print(f"📝 Ablation report exported: {output_file}")


def main():
    """Main ablation study execution."""
    parser = argparse.ArgumentParser(description="PCC-NIUC Ablation Study")
    parser.add_argument('--scenarios', default='bench/scenarios.jsonl', help='Path to scenarios file')
    parser.add_argument('--output', default='ablation_report.md', help='Output Markdown file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Load scenarios
    scenarios = []
    with open(args.scenarios, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                scenarios.append(json.loads(line.strip()))
    
    print(f"📊 Loaded {len(scenarios)} scenarios from {args.scenarios}")
    
    # Run ablation study
    study = AblationStudy()
    all_results = study.run_ablation_study(scenarios, verbose=args.verbose)
    
    # Export report
    study.export_ablation_report(all_results, args.output)
    
    # Print summary
    print("\n" + "="*60)
    print("🔬 ABLATION STUDY SUMMARY")
    print("="*60)
    
    # Compute and display summary metrics
    baseline_metrics = study._compute_metrics(all_results.get('full_system', []))
    
    print(f"{'Configuration':20} {'ASR':>6} {'FPR':>6} {'Latency':>8} {'Security Impact':>15}")
    print("-" * 60)
    
    for config_name in ['full_system', 'no_normalization', 'no_imperative_mood', 'no_request_frames', 'no_code_fence', 'token_level_provenance', 'no_rewrite', 'minimal_system']:
        if config_name in all_results:
            metrics = study._compute_metrics(all_results[config_name])
            
            if config_name == 'full_system':
                security_impact = "baseline"
            else:
                asr_delta = metrics['asr'] - baseline_metrics['asr']
                fpr_delta = metrics['fpr'] - baseline_metrics['fpr']
                security_impact = f"{asr_delta + fpr_delta:+.1f}%"
            
            print(f"{config_name:20} {metrics['asr']:5.1f}% {metrics['fpr']:5.1f}% {metrics['avg_latency_ms']:7.1f}ms {security_impact:>14}")
    
    print(f"\n📄 Detailed ablation report: {args.output}")
    print("🔬 Ablation study complete!")


if __name__ == "__main__":
    main()
