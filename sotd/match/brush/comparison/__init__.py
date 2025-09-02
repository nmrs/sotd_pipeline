"""
Brush Comparison

This module contains comparison and framework components for brush matching.
"""

# Import comparison classes
from .framework import BrushComparisonFramework
from .system import BrushSystemComparator
from .splits_loader import BrushSplitsLoader

__all__ = [
    'BrushComparisonFramework',
    'BrushSystemComparator',
    'BrushSplitsLoader'
]
