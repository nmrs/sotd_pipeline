"""
Brush Matching Strategies

This module contains all brush matching strategies organized by type.
"""

# Import main strategy classes
from .correct_matches_strategy import CorrectMatchesStrategy
from .base_brush_matching_strategy import BaseBrushMatchingStrategy

__all__ = ['CorrectMatchesStrategy', 'BaseBrushMatchingStrategy']
