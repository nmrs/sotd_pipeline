"""
Brush Scoring System

This module contains the scoring engine and related components for brush matching.
"""

# Import main scoring classes
from .engine import ScoringEngine
from .orchestrator import StrategyOrchestrator
from .calculator import ComponentScoreCalculator
from .resolver import ResultConflictResolver
from .matcher import CorrectMatchesMatcher

__all__ = [
    "ScoringEngine",
    "StrategyOrchestrator",
    "ComponentScoreCalculator",
    "ResultConflictResolver",
    "CorrectMatchesMatcher",
]
