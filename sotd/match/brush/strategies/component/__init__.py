"""
Component Strategies

This module contains strategies for matching individual brush components.
"""

# Import component strategy classes
from .handle_component_strategy import HandleComponentStrategy
from .knot_component_strategy import KnotComponentStrategy

__all__ = [
    'HandleComponentStrategy',
    'KnotComponentStrategy'
]
