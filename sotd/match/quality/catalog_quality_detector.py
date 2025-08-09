"""
Catalog Quality Detector

Assesses catalog completeness and quality for brush matches based on Phase 4.1 research findings.
Implements 5-tier quality classification and catalog presence detection.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional


def load_yaml_catalog(file_path: Path) -> Dict[str, Any]:
    """Load YAML catalog file."""
    if not file_path.exists():
        return {}

    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


class CatalogQualityDetector:
    """
    Detects and assesses catalog quality for brush matching.

    Based on Phase 4.1 research findings:
    - 5-tier quality classification (complete/substantial/moderate/basic/minimal)
    - Quality field coverage assessment
    - Catalog presence detection
    - Quality scoring modifiers
    """

    def __init__(self, catalog_files: Optional[List[Path]] = None):
        """Initialize catalog quality detector."""
        # Define quality fields based on Phase 4.1 research
        self.quality_fields = ["knot_fiber", "knot_size_mm", "handle_material", "loft_mm"]

        # Load catalog data
        if catalog_files is None:
            catalog_files = [
                Path("data/brushes.yaml"),
                Path("data/knots.yaml"),
                Path("data/handles.yaml"),
            ]

        self.catalog_data = {}
        for catalog_file in catalog_files:
            if catalog_file.exists():
                catalog_data = load_yaml_catalog(catalog_file)
                if catalog_data:
                    self.catalog_data.update(catalog_data)

    def assess_catalog_completeness(self, category: str, brand: str) -> Dict[str, Any]:
        """
        Assess catalog completeness for a brand.

        Returns:
            Dict with tier, quality_field_count, completeness_score, has_catalog_entry
        """
        # Check if category and brand exist in catalog
        if category not in self.catalog_data:
            return {
                "tier": "no_entry",
                "quality_field_count": 0,
                "completeness_score": 0,
                "has_catalog_entry": False,
            }

        if brand not in self.catalog_data[category]:
            return {
                "tier": "no_entry",
                "quality_field_count": 0,
                "completeness_score": 0,
                "has_catalog_entry": False,
            }

        # Get brand entry data
        brand_data = self.catalog_data[category][brand]

        # Handle malformed entries (not a dict)
        if not isinstance(brand_data, dict):
            return {
                "tier": "minimal",
                "quality_field_count": 0,
                "completeness_score": 0,
                "has_catalog_entry": True,
            }

        # Count quality fields present
        quality_field_count = sum(1 for field in self.quality_fields if brand_data.get(field))

        # Determine tier based on quality field count
        if quality_field_count >= 4:
            tier = "complete"
            completeness_score = 100
        elif quality_field_count == 3:
            tier = "substantial"
            completeness_score = 75
        elif quality_field_count == 2:
            tier = "moderate"
            completeness_score = 50
        elif quality_field_count == 1:
            tier = "basic"
            completeness_score = 25
        else:
            tier = "minimal"
            completeness_score = 0

        return {
            "tier": tier,
            "quality_field_count": quality_field_count,
            "completeness_score": completeness_score,
            "has_catalog_entry": True,
        }

    def get_catalog_presence(self, category: str, brand: str) -> bool:
        """Check if brand has catalog presence."""
        return category in self.catalog_data and brand in self.catalog_data[category]

    def calculate_field_coverage(self) -> Dict[str, int]:
        """Calculate field coverage across entire catalog."""
        coverage = {field: 0 for field in self.quality_fields}

        for category_data in self.catalog_data.values():
            if isinstance(category_data, dict):
                for brand_data in category_data.values():
                    if isinstance(brand_data, dict):
                        for field in self.quality_fields:
                            if brand_data.get(field):
                                coverage[field] += 1

        return coverage

    def get_quality_tier_distribution(self) -> Dict[str, int]:
        """Get distribution of quality tiers across catalog."""
        distribution = {"complete": 0, "substantial": 0, "moderate": 0, "basic": 0, "minimal": 0}

        for category_name, category_data in self.catalog_data.items():
            if isinstance(category_data, dict):
                for brand_name in category_data.keys():
                    assessment = self.assess_catalog_completeness(category_name, brand_name)
                    tier = assessment["tier"]
                    if tier in distribution:
                        distribution[tier] += 1

        return distribution

    def assess_brand_catalog_quality(self, brand: str) -> Dict[str, Any]:
        """Assess overall brand quality across all catalog entries."""
        best_score = 0
        best_tier = "no_entry"
        has_catalog_entry = False

        # Search across all categories for this brand
        for category_name, category_data in self.catalog_data.items():
            if isinstance(category_data, dict) and brand in category_data:
                has_catalog_entry = True
                assessment = self.assess_catalog_completeness(category_name, brand)
                score = assessment["completeness_score"]
                if score > best_score:
                    best_score = score
                    best_tier = assessment["tier"]

        return {
            "overall_tier": best_tier,
            "best_model_score": best_score,
            "catalog_coverage": has_catalog_entry,
        }

    def get_catalog_modifier_points(self, tier: str) -> int:
        """Get catalog modifier points based on quality tier."""
        # Based on Phase 4.1 quality metrics specification
        modifier_points = {
            "complete": 15,
            "substantial": 12,
            "moderate": 8,
            "basic": 3,
            "minimal": 0,
            "no_entry": 0,
        }

        return modifier_points.get(tier, 0)
