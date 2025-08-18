"""Core product aggregators."""

from .blade_aggregator import aggregate_blades
from .brush_aggregator import aggregate_brushes
from .razor_aggregator import aggregate_razors
from .soap_aggregator import aggregate_soaps
from .soap_sample_brand_aggregator import aggregate_soap_sample_brands
from .soap_sample_brand_scent_aggregator import aggregate_soap_sample_brand_scents


__all__ = [
    "aggregate_blades",
    "aggregate_brushes",
    "aggregate_razors",
    "aggregate_soaps",
    "aggregate_soap_sample_brands",
    "aggregate_soap_sample_brand_scents",
]
