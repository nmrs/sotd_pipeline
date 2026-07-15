#!/usr/bin/env python3
"""Shared rules for whether soap usage counts as a distinct catalog scent."""

from typing import Any, Dict, Optional


def is_mashup_soap(soap: Optional[Dict[str, Any]]) -> bool:
    """Return True when enrich marked the soap as a mashup."""
    if not soap or not isinstance(soap, dict):
        return False
    enriched = soap.get("enriched") or {}
    return enriched.get("is_mashup") is True


def counts_as_distinct_soap_scent(soap: Optional[Dict[str, Any]]) -> bool:
    """Return True when soap usage should count toward distinct soap/scent metrics.

    Mashups and catalog non-countable scents are excluded. Mashup-specific
    aggregators key off is_mashup only; this helper is for scent-level metrics.
    """
    if not soap or not isinstance(soap, dict):
        return False
    if is_mashup_soap(soap):
        return False

    matched = soap.get("matched")
    if not matched or not isinstance(matched, dict):
        return False

    if not matched.get("countable", True):
        return False

    return True
