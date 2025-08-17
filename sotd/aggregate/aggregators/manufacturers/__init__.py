"""Manufacturer-level aggregators."""

from .blade_manufacturer_aggregator import aggregate_blade_manufacturers
from .brand_diversity_aggregator import aggregate_brand_diversity
from .razor_manufacturer_aggregator import aggregate_razor_manufacturers
from .soap_maker_aggregator import aggregate_soap_makers

__all__ = [
    "aggregate_blade_manufacturers",
    "aggregate_brand_diversity",
    "aggregate_razor_manufacturers",
    "aggregate_soap_makers",
]
