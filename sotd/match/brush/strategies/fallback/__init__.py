"""
Fallback Strategies

This module contains fallback strategies for when primary matching fails.
"""

# Import fallback strategy classes
from .fiber_fallback_strategy import FiberFallbackStrategy
from .knot_size_fallback_strategy import KnotSizeFallbackStrategy

__all__ = ["FiberFallbackStrategy", "KnotSizeFallbackStrategy"]
