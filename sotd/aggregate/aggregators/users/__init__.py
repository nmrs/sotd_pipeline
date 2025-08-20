"""User aggregators."""

from .blade_diversity_aggregator import aggregate_blade_diversity
from .brush_diversity_aggregator import aggregate_brush_diversity
from .brush_fiber_user_aggregator import aggregate_brush_fiber_users
from .razor_diversity_aggregator import aggregate_razor_diversity
from .razor_format_user_aggregator import aggregate_razor_format_users
from .soap_brand_diversity_aggregator import aggregate_soap_brand_diversity
from .soap_brand_scent_diversity_aggregator import aggregate_soap_brand_scent_diversity
from .soap_sample_user_aggregator import aggregate_soap_sample_users
from .user_aggregator import aggregate_users

__all__ = [
    "aggregate_users",
    "aggregate_soap_sample_users",
    "aggregate_soap_brand_diversity",
    "aggregate_soap_brand_scent_diversity",
    "aggregate_razor_diversity",
    "aggregate_blade_diversity",
    "aggregate_brush_diversity",
    "aggregate_razor_format_users",
    "aggregate_brush_fiber_users",
]
