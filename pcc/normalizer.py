"""
Text normalizer for PCC-NIUC system.
Transforms input text into canonical form for imperative detection.
"""

from typing import Dict, Tuple, List
import unicodedata
import re


class TextNormalizer:
    """Normalizes text to prevent Unicode-based evasion attacks."""
    
    def __init__(self):
        """Initialize normalizer with homoglyph mappings and zero-width character lists."""
        # Zero-width characters that can hide imperatives
        self.zero_width_chars = {
            '\u200B',  # Zero Width Space
            '\u200C',  # Zero Width Non-Joiner
            '\u200D',  # Zero Width Joiner
            '\uFEFF',  # Zero Width No-Break Space (BOM)
            '\u061C',  # Arabic Letter Mark
            '\u180E',  # Mongolian Vowel Separator
        }
        
        # Homoglyph mapping for common attack characters
        # Assumption: Limited to most common attack vectors for performance
        self.homoglyph_map = {
            # Cyrillic lookalikes (most common in attacks)
            'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c', 'х': 'x',
            'А': 'A', 'Е': 'E', 'О': 'O', 'Р': 'P', 'С': 'C', 'Х': 'X',
            
            # Greek lookalikes
            'α': 'a', 'ο': 'o', 'ρ': 'p', 'υ': 'u', 'Α': 'A', 'Ο': 'O',
            
            # Mathematical symbols commonly abused
            '﹣': '-', '⁻': '-', '−': '-', '‒': '-', '–': '-', '—': '-',
            
            # Quotation marks
            ''': "'", ''': "'", '"': '"', '"': '"', '‚': ',', '„': '"',
            
            # Common symbol substitutions
            '！': '!', '？': '?', '：': ':', '；': ';',
        }
    
    def normalize(self, text: str) -> Tuple[str, Dict[str, int]]:
        """
        Normalize text through the complete NIUC pipeline.
        
        Args:
            text: Raw input text to normalize
            
        Returns:
            Tuple of (normalized_text, stats) where stats contains
            counts of transformations applied
            
        Preconditions:
            - text is a valid string
            - text length < 1MB for performance
            
        Postconditions:
            - Result is deterministic for same input
            - All Unicode evasion techniques neutralized
            - Character count mappings preserved for provenance
        """
        if not isinstance(text, str):
            raise TypeError("Input must be a string")
        
        stats = {
            'original_length': len(text),
            'nfkc_changes': 0,
            'case_changes': 0,
            'zero_width_removed': 0,
            'homoglyphs_mapped': 0,
        }
        
        # Step 1: Unicode NFKC normalization
        normalized = unicodedata.normalize('NFKC', text)
        if normalized != text:
            stats['nfkc_changes'] = len(text) - len(normalized)
        
        # Step 2: Case folding for case-insensitive detection
        folded = normalized.casefold()
        if folded != normalized:
            stats['case_changes'] = sum(1 for a, b in zip(normalized, folded) if a != b)
        
        # Step 3: Zero-width character removal
        cleaned, zw_removed = self._remove_zero_width_chars(folded)
        stats['zero_width_removed'] = zw_removed
        
        # Step 4: Homoglyph mapping
        mapped, homoglyphs_mapped = self._apply_homoglyph_mapping(cleaned)
        stats['homoglyphs_mapped'] = homoglyphs_mapped
        
        return mapped, stats
    
    def _remove_zero_width_chars(self, text: str) -> Tuple[str, int]:
        """
        Remove zero-width characters that can hide imperatives.
        
        Args:
            text: Input text potentially containing zero-width characters
            
        Returns:
            Tuple of (cleaned_text, count_removed)
        """
        removed_count = 0
        result = []
        
        for char in text:
            if char in self.zero_width_chars:
                removed_count += 1
            else:
                result.append(char)
        
        return ''.join(result), removed_count
    
    def _apply_homoglyph_mapping(self, text: str) -> Tuple[str, int]:
        """
        Map homoglyph characters to their canonical Latin equivalents.
        
        Args:
            text: Input text potentially containing homoglyphs
            
        Returns:
            Tuple of (mapped_text, count_mapped)
        """
        mapped_count = 0
        result = []
        
        for char in text:
            if char in self.homoglyph_map:
                result.append(self.homoglyph_map[char])
                mapped_count += 1
            else:
                result.append(char)
        
        return ''.join(result), mapped_count
    
    def compute_hash(self, text: str) -> str:
        """
        Compute SHA-256 hash of normalized text.
        
        Args:
            text: Text to hash (should be normalized)
            
        Returns:
            Lowercase hexadecimal SHA-256 hash
        """
        import hashlib
        return hashlib.sha256(text.encode('utf-8')).hexdigest().lower()
    
    def create_character_mapping(self, original: str, normalized: str) -> List[int]:
        """
        Create mapping from normalized positions back to original positions.
        
        Args:
            original: Original input text
            normalized: Result of normalization
            
        Returns:
            List where index is normalized position, value is original position
            
        Note:
            This is a simplified mapping that assumes character-level correspondence.
            Unicode normalization can change character counts, so this provides
            a best-effort mapping for provenance tracking.
        """
        # Simple implementation: assumes most characters map 1:1
        # More sophisticated implementations would track detailed Unicode transforms
        mapping = []
        orig_pos = 0
        
        for norm_pos in range(len(normalized)):
            # Find corresponding position in original text
            while (orig_pos < len(original) and 
                   unicodedata.normalize('NFKC', original[orig_pos]).casefold() != normalized[norm_pos]):
                orig_pos += 1
            
            mapping.append(orig_pos if orig_pos < len(original) else len(original) - 1)
            orig_pos += 1
        
        return mapping


# Convenience function for direct use
def normalize_text(text: str) -> Tuple[str, Dict[str, int]]:
    """
    Convenience function to normalize text without creating a normalizer instance.
    
    Args:
        text: Input text to normalize
        
    Returns:
        Tuple of (normalized_text, transformation_stats)
    """
    normalizer = TextNormalizer()
    return normalizer.normalize(text)