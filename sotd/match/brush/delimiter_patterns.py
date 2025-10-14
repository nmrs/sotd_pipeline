#!/usr/bin/env python3
"""Delimiter patterns for brush splitting and matching.

This module centralizes all delimiter pattern definitions used across the brush
matching system to ensure consistency and follow DRY principles.
"""

from typing import List


class BrushDelimiterPatterns:
    """Centralized delimiter patterns for brush splitting and matching."""
    
    # High-priority delimiters that indicate strong component separation
    # These are checked first and always trigger splitting
    HIGH_PRIORITY_DELIMITERS = [
        " w/ ",  # " w/ " (with spaces)
        " w/",   # " w/" (leading space only)
        " with ",  # " with " (with spaces)
        " in ",    # " in " (with spaces)
    ]
    
    # Medium-priority delimiters that may indicate component separation
    # These are checked after high-priority delimiters
    MEDIUM_PRIORITY_DELIMITERS = [
        " - ",  # " - " (dash with spaces)
        " + ",  # " + " (plus with spaces)
        "/",    # "/" (slash - requires special handling for Reddit references)
    ]
    
    # Regex patterns for scoring engine (word boundaries)
    HIGH_PRIORITY_REGEX_PATTERNS = [
        r"\bw/\b",    # "w/" (with word boundaries)
        r"\bwith\b",  # "with" (with word boundaries)
        r"\bin\b",    # "in" (with word boundaries)
    ]
    
    # Regex patterns for scoring engine (space boundaries)
    MEDIUM_PRIORITY_REGEX_PATTERNS = [
        r"\s/\s",  # " / " (slash with spaces)
        r"\s-\s",  # " - " (dash with spaces)
        r"\s\+\s",  # " + " (plus with spaces)
    ]
    
    # Delimiters that use smart splitting (content-based handle vs knot determination)
    SMART_SPLITTING_DELIMITERS = [
        " w/ ",  # " w/ " (with spaces)
        " w/",   # " w/" (leading space only)
        " with ",  # " with " (with spaces)
    ]
    
    # Delimiters that use positional splitting (first part = handle, second part = knot)
    POSITIONAL_SPLITTING_DELIMITERS = [
        " in ",  # " in " (knot in handle)
    ]
    
    @classmethod
    def get_high_priority_delimiters(cls) -> List[str]:
        """Get high-priority delimiter patterns."""
        return cls.HIGH_PRIORITY_DELIMITERS.copy()
    
    @classmethod
    def get_medium_priority_delimiters(cls) -> List[str]:
        """Get medium-priority delimiter patterns."""
        return cls.MEDIUM_PRIORITY_DELIMITERS.copy()
    
    @classmethod
    def get_high_priority_regex_patterns(cls) -> List[str]:
        """Get high-priority regex patterns for scoring."""
        return cls.HIGH_PRIORITY_REGEX_PATTERNS.copy()
    
    @classmethod
    def get_medium_priority_regex_patterns(cls) -> List[str]:
        """Get medium-priority regex patterns for scoring."""
        return cls.MEDIUM_PRIORITY_REGEX_PATTERNS.copy()
    
    @classmethod
    def get_smart_splitting_delimiters(cls) -> List[str]:
        """Get delimiters that use smart splitting logic."""
        return cls.SMART_SPLITTING_DELIMITERS.copy()
    
    @classmethod
    def get_positional_splitting_delimiters(cls) -> List[str]:
        """Get delimiters that use positional splitting logic."""
        return cls.POSITIONAL_SPLITTING_DELIMITERS.copy()
    
    @classmethod
    def is_smart_splitting_delimiter(cls, delimiter: str) -> bool:
        """Check if a delimiter uses smart splitting logic."""
        return delimiter in cls.SMART_SPLITTING_DELIMITERS
    
    @classmethod
    def is_positional_splitting_delimiter(cls, delimiter: str) -> bool:
        """Check if a delimiter uses positional splitting logic."""
        return delimiter in cls.POSITIONAL_SPLITTING_DELIMITERS
