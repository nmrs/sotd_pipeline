"""
Brush Scoring System

This module contains the scoring engine and related components for brush matching.
"""

# Import main scoring classes
from .calculator import ComponentScoreCalculator
from .engine import ScoringEngine
from .matcher import CorrectMatchesMatcher
from .orchestrator import StrategyOrchestrator
from .resolver import ResultConflictResolver

__all__ = [
    "ScoringEngine",
    "StrategyOrchestrator",
    "ComponentScoreCalculator",
    "ResultConflictResolver",
    "CorrectMatchesMatcher",
]
