"""
Provenance tracking for PCC-NIUC system.
Builds text with character-level trust tags from mixed trusted/untrusted segments.
"""

from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class ChannelType(Enum):
    """Types of input channels with different trust levels."""
    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"


@dataclass
class TextSegment:
    """A segment of text with its associated trust level."""
    text: str
    channel: ChannelType
    source_id: str = "unknown"
    
    def __post_init__(self):
        if not isinstance(self.text, str):
            raise TypeError("Text must be a string")
        if not isinstance(self.channel, ChannelType):
            raise TypeError("Channel must be a ChannelType enum")


@dataclass 
class CharacterTag:
    """Provenance information for a single character position."""
    channel: ChannelType
    source_id: str
    original_position: int
    segment_index: int


class ProvenanceBuilder:
    """Builds provenance-tagged text from mixed trusted/untrusted segments."""
    
    def __init__(self):
        """Initialize provenance builder."""
        self.segments: List[TextSegment] = []
        self.character_tags: List[CharacterTag] = []
        self.combined_text: str = ""
    
    def add_segment(self, text: str, channel: ChannelType, source_id: str = "unknown") -> None:
        """
        Add a text segment with its trust level.
        
        Args:
            text: Text content to add
            channel: Trust level (TRUSTED or UNTRUSTED)
            source_id: Identifier for the source of this text
            
        Preconditions:
            - text is a valid string
            - channel is a valid ChannelType
            
        Postconditions:
            - Segment is added to internal list
            - Character tags are updated
            - Combined text is rebuilt
        """
        segment = TextSegment(text, channel, source_id)
        self.segments.append(segment)
        self._rebuild_provenance()
    
    def build_from_segments(self, segments: List[Tuple[str, str, Optional[str]]]) -> Tuple[str, List[CharacterTag]]:
        """
        Build provenance-tagged text from a list of (text, channel, source_id) tuples.
        
        Args:
            segments: List of tuples where each tuple is (text, channel_name, source_id)
                     channel_name should be "trusted" or "untrusted"
                     source_id is optional and defaults to "unknown"
        
        Returns:
            Tuple of (combined_text, character_tags)
            
        Preconditions:
            - segments is a valid list
            - each segment has valid text and channel
            
        Postconditions:
            - Combined text contains all segment text concatenated
            - Each character has corresponding provenance tag
            - Character positions are correct for combined text
        """
        self.segments.clear()
        
        for i, segment_data in enumerate(segments):
            if len(segment_data) < 2:
                raise ValueError(f"Segment {i} must have at least (text, channel)")
            
            text = segment_data[0]
            channel_str = segment_data[1]
            source_id = segment_data[2] if len(segment_data) > 2 and segment_data[2] else f"segment_{i}"
            
            # Convert string to enum
            try:
                channel = ChannelType(channel_str)
            except ValueError:
                raise ValueError(f"Invalid channel type '{channel_str}'. Must be 'trusted' or 'untrusted'")
            
            segment = TextSegment(text, channel, source_id)
            self.segments.append(segment)
        
        self._rebuild_provenance()
        return self.combined_text, self.character_tags
    
    def _rebuild_provenance(self) -> None:
        """Rebuild combined text and character tags from current segments."""
        self.character_tags.clear()
        text_parts = []
        global_position = 0
        
        for segment_index, segment in enumerate(self.segments):
            text_parts.append(segment.text)
            
            # Create character tags for this segment
            for local_position, char in enumerate(segment.text):
                tag = CharacterTag(
                    channel=segment.channel,
                    source_id=segment.source_id,
                    original_position=local_position,
                    segment_index=segment_index
                )
                self.character_tags.append(tag)
                global_position += 1
        
        self.combined_text = ''.join(text_parts)
    
    def get_untrusted_positions(self) -> List[int]:
        """
        Get all character positions that originate from untrusted channels.
        
        Returns:
            List of character positions (0-indexed) that are from untrusted sources
        """
        untrusted_positions = []
        for position, tag in enumerate(self.character_tags):
            if tag.channel == ChannelType.UNTRUSTED:
                untrusted_positions.append(position)
        return untrusted_positions
    
    def check_span_trust(self, start: int, end: int) -> Dict[str, any]:
        """
        Check the trust level of characters in a given span.
        
        Args:
            start: Start position (inclusive)
            end: End position (exclusive)
            
        Returns:
            Dictionary with trust analysis of the span
            
        Preconditions:
            - 0 <= start < end <= len(combined_text)
            
        Postconditions:
            - Returns detailed trust analysis
            - Indicates if span contains any untrusted characters
        """
        if start < 0 or end > len(self.combined_text) or start >= end:
            raise ValueError(f"Invalid span [{start}, {end}) for text of length {len(self.combined_text)}")
        
        trusted_count = 0
        untrusted_count = 0
        untrusted_positions = []
        source_ids = set()
        
        for pos in range(start, end):
            if pos < len(self.character_tags):
                tag = self.character_tags[pos]
                source_ids.add(tag.source_id)
                
                if tag.channel == ChannelType.TRUSTED:
                    trusted_count += 1
                else:
                    untrusted_count += 1
                    untrusted_positions.append(pos)
        
        return {
            'span_start': start,
            'span_end': end,
            'span_text': self.combined_text[start:end],
            'total_chars': end - start,
            'trusted_chars': trusted_count,
            'untrusted_chars': untrusted_count,
            'has_untrusted': untrusted_count > 0,
            'untrusted_positions': untrusted_positions,
            'source_ids': list(source_ids),
            'is_violation': untrusted_count > 0,  # NIUC violation if any untrusted chars
        }
    
    def detect_violations(self, imperative_spans: List[Tuple[int, int]]) -> List[Dict[str, any]]:
        """
        Detect NIUC violations by checking if imperatives overlap with untrusted characters.
        
        Args:
            imperative_spans: List of (start, end) tuples for detected imperatives
            
        Returns:
            List of violation dictionaries with detailed information
            
        Postconditions:
            - Each violation includes span details and untrusted positions
            - Empty list if no violations found
        """
        violations = []
        
        for start, end in imperative_spans:
            span_analysis = self.check_span_trust(start, end)
            
            if span_analysis['has_untrusted']:
                violation = {
                    'imperative_start': start,
                    'imperative_end': end,
                    'imperative_text': span_analysis['span_text'],
                    'untrusted_positions': span_analysis['untrusted_positions'],
                    'source_ids': span_analysis['source_ids'],
                    'violation_type': 'UNTRUSTED_IMPERATIVE',
                }
                violations.append(violation)
        
        return violations
    
    def get_trust_summary(self) -> Dict[str, any]:
        """
        Get summary statistics about the trust levels in the combined text.
        
        Returns:
            Dictionary with trust statistics
        """
        trusted_count = sum(1 for tag in self.character_tags if tag.channel == ChannelType.TRUSTED)
        untrusted_count = len(self.character_tags) - trusted_count
        
        source_counts = {}
        for tag in self.character_tags:
            source_counts[tag.source_id] = source_counts.get(tag.source_id, 0) + 1
        
        return {
            'total_characters': len(self.character_tags),
            'trusted_characters': trusted_count,
            'untrusted_characters': untrusted_count,
            'trusted_percentage': (trusted_count / len(self.character_tags)) * 100 if self.character_tags else 0,
            'total_segments': len(self.segments),
            'source_breakdown': source_counts,
            'combined_text_length': len(self.combined_text),
        }


# Convenience functions for direct use

def build_provenance_text(segments: List[Tuple[str, str, Optional[str]]]) -> Tuple[str, List[CharacterTag]]:
    """
    Convenience function to build provenance text without creating a builder instance.
    
    Args:
        segments: List of (text, channel, source_id) tuples
        
    Returns:
        Tuple of (combined_text, character_tags)
    """
    builder = ProvenanceBuilder()
    return builder.build_from_segments(segments)


def check_niuc_violations(text: str, character_tags: List[CharacterTag], 
                         imperative_spans: List[Tuple[int, int]]) -> List[Dict[str, any]]:
    """
    Check for NIUC violations given text, tags, and imperative spans.
    
    Args:
        text: Combined text
        character_tags: Provenance tags for each character
        imperative_spans: List of (start, end) spans for imperatives
        
    Returns:
        List of violation dictionaries
    """
    # Create temporary builder to use violation detection
    builder = ProvenanceBuilder()
    builder.combined_text = text
    builder.character_tags = character_tags
    
    return builder.detect_violations(imperative_spans)