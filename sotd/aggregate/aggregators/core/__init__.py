"""Core product aggregators."""

from .blade_aggregator import aggregate_blades
from .brush_aggregator import aggregate_brushes
from .razor_aggregator import aggregate_razors
from .soap_aggregator import aggregate_soaps


__all__ = [
    "aggregate_blades",
    "aggregate_brushes",
    "aggregate_razors",
    "aggregate_soaps",
]
