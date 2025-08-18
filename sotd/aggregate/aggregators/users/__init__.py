"""User aggregators."""

from .user_aggregator import aggregate_users
from .soap_sample_user_aggregator import aggregate_soap_sample_users

__all__ = ["aggregate_users", "aggregate_soap_sample_users"]
