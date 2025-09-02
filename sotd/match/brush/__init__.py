"""
Brush Matching Module

This module provides the complete brush matching system with organized submodules
for strategies, scoring, validation, and comparison functionality.
"""

# Import main classes for backward compatibility
from .matcher import BrushMatcher
from sotd.match.config import BrushMatcherConfig

__all__ = ['BrushMatcher', 'BrushMatcherConfig']
