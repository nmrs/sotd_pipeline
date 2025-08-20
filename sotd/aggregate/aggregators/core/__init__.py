"""Core product aggregators."""

from .blade_aggregator import aggregate_blades
from .blade_usage_distribution_aggregator import aggregate_blade_usage_distribution
from .brush_aggregator import aggregate_brushes
from .razor_aggregator import aggregate_razors
from .sample_usage_metrics_aggregator import aggregate_sample_usage_metrics
from .soap_aggregator import aggregate_soaps
from .soap_sample_brand_aggregator import aggregate_soap_sample_brands
from .soap_sample_brand_scent_aggregator import aggregate_soap_sample_brand_scents

__all__ = [
    "aggregate_blades",
    "aggregate_blade_usage_distribution",
    "aggregate_brushes",
    "aggregate_razors",
    "aggregate_sample_usage_metrics",
    "aggregate_soaps",
    "aggregate_soap_sample_brands",
    "aggregate_soap_sample_brand_scents",
]
