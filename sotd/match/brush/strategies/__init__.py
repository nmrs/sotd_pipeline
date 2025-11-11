"""
Brush Matching Strategies

This module contains all brush matching strategies organized by type.
"""

# Import main strategy classes
from .base_brush_matching_strategy import BaseBrushMatchingStrategy
from .correct_matches_strategy import CorrectMatchesStrategy

__all__ = ["CorrectMatchesStrategy", "BaseBrushMatchingStrategy"]
