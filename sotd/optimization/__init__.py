"""Optimization module for SOTD Pipeline.

This module provides tools for optimizing configuration parameters
using gradient descent and other optimization techniques.
"""

from .brush_scoring_optimizer import BrushScoringOptimizer

__all__ = ["BrushScoringOptimizer"]
