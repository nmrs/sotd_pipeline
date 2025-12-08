"""
Tests for Catalog Quality Detector

Tests the catalog completeness assessment capabilities based on Phase 4.1 research findings:
- 5-tier quality classification (complete/substantial/moderate/basic/minimal)
- Field coverage calculation for quality assessment
- Brand catalog presence detection
- Quality scoring for catalog entries
"""

from typing import Any, Dict
from unittest.mock import patch

import pytest

from sotd.match.quality.catalog_quality_detector import CatalogQualityDetector


class TestCatalogQualityDetector:
    """Test catalog quality detection capabilities."""

    @pytest.fixture
    def mock_catalog_data(self) -> Dict[str, Any]:
        """Mock catalog data with varying completeness levels."""
        return {
            "known_brushes": {
                "Zenith": {
                    "knot_fiber": "Boar",
                    "knot_size_mm": 28,
                    "handle_material": "Wood",
                    "loft_mm": 55,
                },  # Complete (4 quality fields)
                "Declaration Grooming": {
                    "knot_fiber": "Synthetic",
                    "knot_size_mm": 26,
                    "handle_material": "Resin",
                },  # Substantial (3 quality fields)
                "AP Shave Co": {
                    "knot_size_mm": 24,
                    "handle_material": "Wood",
                },  # Moderate (2 quality fields)
                "Maggard": {"knot_fiber": "Synthetic"},  # Basic (1 quality field)
                "Simpson": {},  # Minimal (0 quality fields)
            }
        }

    @pytest.fixture
    def detector(self, mock_catalog_data) -> CatalogQualityDetector:
        """Create CatalogQualityDetector with mock data."""
        with patch("sotd.match.quality.catalog_quality_detector.load_yaml_catalog") as mock_load:
            mock_load.return_value = mock_catalog_data
            return CatalogQualityDetector()

    def test_catalog_quality_detector_initialization(self, detector):
        """Test detector initializes with catalog data."""
        assert detector is not None
        assert hasattr(detector, "catalog_data")
        assert hasattr(detector, "quality_fields")

    def test_quality_field_definitions(self, detector):
        """Test quality fields are properly defined."""
        expected_quality_fields = ["knot_fiber", "knot_size_mm", "handle_material", "loft_mm"]
        assert detector.quality_fields == expected_quality_fields

    def test_assess_catalog_completeness_complete_entry(self, detector):
        """Test complete entry assessment (4+ quality fields)."""
        # Zenith has all 4 quality fields
        result = detector.assess_catalog_completeness("known_brushes", "Zenith")

        assert result["tier"] == "complete"
        assert result["quality_field_count"] == 4
        assert result["completeness_score"] == 100
        assert result["has_catalog_entry"] is True

    def test_assess_catalog_completeness_substantial_entry(self, detector):
        """Test substantial entry assessment (3 quality fields)."""
        # Declaration Grooming has 3 quality fields
        result = detector.assess_catalog_completeness("known_brushes", "Declaration Grooming")

        assert result["tier"] == "substantial"
        assert result["quality_field_count"] == 3
        assert result["completeness_score"] == 75
        assert result["has_catalog_entry"] is True

    def test_assess_catalog_completeness_moderate_entry(self, detector):
        """Test moderate entry assessment (2 quality fields)."""
        # AP Shave Co has 2 quality fields
        result = detector.assess_catalog_completeness("known_brushes", "AP Shave Co")

        assert result["tier"] == "moderate"
        assert result["quality_field_count"] == 2
        assert result["completeness_score"] == 50
        assert result["has_catalog_entry"] is True

    def test_assess_catalog_completeness_basic_entry(self, detector):
        """Test basic entry assessment (1 quality field)."""
        # Maggard has 1 quality field
        result = detector.assess_catalog_completeness("known_brushes", "Maggard")

        assert result["tier"] == "basic"
        assert result["quality_field_count"] == 1
        assert result["completeness_score"] == 25
        assert result["has_catalog_entry"] is True

    def test_assess_catalog_completeness_minimal_entry(self, detector):
        """Test minimal entry assessment (0 quality fields)."""
        # Simpson has 0 quality fields (brand/model only)
        result = detector.assess_catalog_completeness("known_brushes", "Simpson")

        assert result["tier"] == "minimal"
        assert result["quality_field_count"] == 0
        assert result["completeness_score"] == 0
        assert result["has_catalog_entry"] is True

    def test_assess_catalog_completeness_no_entry(self, detector):
        """Test assessment when no catalog entry exists."""
        result = detector.assess_catalog_completeness("known_brushes", "NonexistentBrand")

        assert result["tier"] == "no_entry"
        assert result["quality_field_count"] == 0
        assert result["completeness_score"] == 0
        assert result["has_catalog_entry"] is False

    def test_assess_catalog_completeness_no_category(self, detector):
        """Test assessment when catalog category doesn't exist."""
        result = detector.assess_catalog_completeness("nonexistent_category", "SomeBrand")

        assert result["tier"] == "no_entry"
        assert result["quality_field_count"] == 0
        assert result["completeness_score"] == 0
        assert result["has_catalog_entry"] is False

    def test_get_catalog_presence_existing_brand(self, detector):
        """Test catalog presence detection for existing brand."""
        assert detector.get_catalog_presence("known_brushes", "Zenith") is True
        assert detector.get_catalog_presence("known_brushes", "Simpson") is True

    def test_get_catalog_presence_missing_brand(self, detector):
        """Test catalog presence detection for missing brand."""
        assert detector.get_catalog_presence("known_brushes", "NonexistentBrand") is False
        assert detector.get_catalog_presence("nonexistent_category", "SomeBrand") is False

    def test_calculate_field_coverage(self, detector):
        """Test field coverage calculation across catalog."""
        coverage = detector.calculate_field_coverage()

        # Expected coverage based on mock data
        expected_coverage = {
            "knot_fiber": 3,  # Zenith, Declaration Grooming, Maggard
            "knot_size_mm": 3,  # Zenith, Declaration Grooming, AP Shave Co
            "handle_material": 3,  # Zenith, Declaration Grooming, AP Shave Co
            "loft_mm": 1,  # Zenith only
        }

        assert coverage == expected_coverage

    def test_get_quality_tier_distribution(self, detector):
        """Test quality tier distribution calculation."""
        distribution = detector.get_quality_tier_distribution()

        expected_distribution = {
            "complete": 1,  # Zenith
            "substantial": 1,  # Declaration Grooming
            "moderate": 1,  # AP Shave Co
            "basic": 1,  # Maggard
            "minimal": 1,  # Simpson
        }

        assert distribution == expected_distribution

    def test_assess_brand_catalog_quality(self, detector):
        """Test comprehensive brand quality assessment."""
        # Test complete brand
        zenith_quality = detector.assess_brand_catalog_quality("Zenith")
        assert zenith_quality["overall_tier"] == "complete"
        assert zenith_quality["best_model_score"] == 100
        assert zenith_quality["catalog_coverage"] is True

        # Test missing brand
        missing_quality = detector.assess_brand_catalog_quality("MissingBrand")
        assert missing_quality["overall_tier"] == "no_entry"
        assert missing_quality["best_model_score"] == 0
        assert missing_quality["catalog_coverage"] is False

    def test_get_catalog_modifier_points(self, detector):
        """Test catalog modifier points calculation based on Phase 4.1 spec."""
        # Based on Phase 4.1 quality metrics specification
        assert detector.get_catalog_modifier_points("complete") == 15
        assert detector.get_catalog_modifier_points("substantial") == 12
        assert detector.get_catalog_modifier_points("moderate") == 8
        assert detector.get_catalog_modifier_points("basic") == 3
        assert detector.get_catalog_modifier_points("minimal") == 0
        assert detector.get_catalog_modifier_points("no_entry") == 0

    def test_edge_cases_empty_catalog_data(self):
        """Test behavior with empty catalog data."""
        with patch("sotd.match.quality.catalog_quality_detector.load_yaml_catalog") as mock_load:
            mock_load.return_value = {}
            detector = CatalogQualityDetector()

            result = detector.assess_catalog_completeness("any_category", "any_brand")
            assert result["tier"] == "no_entry"
            assert result["has_catalog_entry"] is False

    def test_edge_cases_malformed_catalog_entry(self, detector):
        """Test behavior with malformed catalog entries."""
        # Patch catalog data to include malformed entry
        detector.catalog_data["known_brushes"]["MalformedEntry"] = "not_a_dict"

        result = detector.assess_catalog_completeness("known_brushes", "MalformedEntry")
        assert result["tier"] == "minimal"  # Treat as minimal entry
        assert result["quality_field_count"] == 0

    def test_real_catalog_integration(self):
        """Test integration with real catalog files if they exist."""
        # This test will use actual catalog files if available
        try:
            detector = CatalogQualityDetector()
            # If real catalogs exist, test basic functionality
            if detector.catalog_data:
                # Test that we can assess some real brand
                first_category = next(iter(detector.catalog_data.keys()))
                if detector.catalog_data[first_category]:
                    first_brand = next(iter(detector.catalog_data[first_category].keys()))
                    result = detector.assess_catalog_completeness(first_category, first_brand)
                    assert "tier" in result
                    assert "quality_field_count" in result
                    assert "has_catalog_entry" in result
        except FileNotFoundError as e:
            # If real catalogs don't exist or fail to load, fail with clear message
            pytest.fail(
                f"Test requires catalog files but they were not found: {e}. Create test catalog files or provide proper test fixtures to run this integration test."
            )


class TestCatalogQualityDetectorPerformance:
    """Test performance characteristics of catalog quality detection."""

    @pytest.fixture
    def large_catalog_data(self) -> Dict[str, Any]:
        """Create large mock catalog for performance testing."""
        catalog = {"large_category": {}}

        # Create 1000 mock entries with varying quality
        for i in range(1000):
            brand_name = f"Brand_{i}"
            quality_fields = i % 5  # 0-4 quality fields

            entry = {}
            if quality_fields >= 1:
                entry["knot_fiber"] = "Synthetic"
            if quality_fields >= 2:
                entry["knot_size_mm"] = 24
            if quality_fields >= 3:
                entry["handle_material"] = "Wood"
            if quality_fields >= 4:
                entry["loft_mm"] = 50

            catalog["large_category"][brand_name] = entry

        return catalog

    def test_performance_large_catalog_assessment(self, large_catalog_data):
        """Test performance with large catalog data."""
        import time

        with patch("sotd.match.quality.catalog_quality_detector.load_yaml_catalog") as mock_load:
            mock_load.return_value = large_catalog_data
            detector = CatalogQualityDetector()

            # Time catalog assessment operations
            start_time = time.time()

            # Assess 100 random brands
            for i in range(0, 100, 10):
                brand_name = f"Brand_{i}"
                detector.assess_catalog_completeness("large_category", brand_name)

            end_time = time.time()
            processing_time = end_time - start_time

            # Should complete 100 assessments in reasonable time
            assert processing_time < 1.0  # Less than 1 second

            # Calculate field coverage (more expensive operation)
            start_time = time.time()
            detector.calculate_field_coverage()
            end_time = time.time()
            coverage_time = end_time - start_time

            # Field coverage should also be reasonably fast
            assert coverage_time < 2.0  # Less than 2 seconds

    def test_memory_usage_reasonable(self, large_catalog_data):
        """Test that memory usage remains reasonable with large catalogs."""
        import sys

        with patch("sotd.match.quality.catalog_quality_detector.load_yaml_catalog") as mock_load:
            mock_load.return_value = large_catalog_data

            # Measure approximate memory usage
            initial_size = sys.getsizeof(large_catalog_data)

            detector = CatalogQualityDetector()
            detector_size = sys.getsizeof(detector.catalog_data)

            # Detector shouldn't significantly increase memory usage
            assert detector_size <= initial_size * 1.5  # No more than 50% overhead
