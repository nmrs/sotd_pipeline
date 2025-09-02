"""
Specialized Strategies

This module contains specialized strategies for specific brush brands.
"""

# Import specialized strategy classes
from .omega_semogue_strategy import OmegaSemogueBrushMatchingStrategy
from .zenith_strategy import ZenithBrushMatchingStrategy

__all__ = [
    'OmegaSemogueBrushMatchingStrategy',
    'ZenithBrushMatchingStrategy'
]
