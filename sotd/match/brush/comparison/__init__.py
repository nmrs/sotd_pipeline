"""
Brush Comparison

This module contains comparison and framework components for brush matching.
"""

# Import comparison classes
from .framework import BrushComparisonFramework
from .splits_loader import BrushSplitsLoader
from .system import BrushSystemComparator

__all__ = ["BrushComparisonFramework", "BrushSystemComparator", "BrushSplitsLoader"]
