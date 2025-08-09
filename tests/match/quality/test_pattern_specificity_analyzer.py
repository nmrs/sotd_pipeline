"""
Tests for Pattern Specificity Analyzer

Tests the pattern specificity assessment capabilities based on Phase 4.1 research findings:
- 3-tier specificity classification (high/medium/low)
- Pattern complexity analysis and scoring
- Brand pattern recognition and confidence assessment
- Match pattern categorization and quality indicators
"""

import pytest

from sotd.match.quality.pattern_specificity_analyzer import PatternSpecificityAnalyzer


class TestPatternSpecificityAnalyzer:
    """Test pattern specificity analysis capabilities."""

    @pytest.fixture
    def analyzer(self) -> PatternSpecificityAnalyzer:
        """Create PatternSpecificityAnalyzer."""
        return PatternSpecificityAnalyzer()

    def test_pattern_specificity_analyzer_initialization(self, analyzer):
        """Test analyzer initializes properly."""
        assert analyzer is not None
        assert hasattr(analyzer, "specificity_levels")
        assert hasattr(analyzer, "pattern_keywords")

    def test_specificity_level_definitions(self, analyzer):
        """Test specificity levels are properly defined."""
        expected_levels = ["high", "medium", "low"]
        assert analyzer.specificity_levels == expected_levels

    def test_analyze_pattern_specificity_high_complexity(self, analyzer):
        """Test high specificity pattern analysis."""
        # High specificity: brand + model + size + material details
        high_specificity_patterns = [
            "Zenith B35 Boar 28mm x 52mm loft",
            "Declaration Grooming B15 Synthetic 26mm in Mozingo handle",
            "Simpson Trafalgar T3 Super Badger brush",
            "Omega 10049 Boar Bristle 28mm Professional",
        ]

        for pattern in high_specificity_patterns:
            result = analyzer.analyze_pattern_specificity(pattern)

            assert result["specificity_level"] == "high"
            assert result["complexity_score"] >= 70
            assert result["confidence_score"] >= 80
            # Not all high complexity patterns have size specifications
            # e.g., "Simpson Trafalgar T3 Super Badger brush" has no mm mentioned
            assert result["has_material_specification"] is True

    def test_analyze_pattern_specificity_medium_complexity(self, analyzer):
        """Test medium specificity pattern analysis."""
        # Medium specificity: brand + some details (but not fully detailed)
        medium_specificity_patterns = [
            "AP Shave Co synthetic brush",  # Brand + material only
            "Phoenix Artisan Accoutrements boar brush",  # Brand + material only
            "Maggard synthetic",  # Brand + material only
            "Stirling badger brush",  # Brand + material only
        ]

        for pattern in medium_specificity_patterns:
            result = analyzer.analyze_pattern_specificity(pattern)

            assert result["specificity_level"] == "medium"
            assert 40 <= result["complexity_score"] < 70
            assert (
                50 <= result["confidence_score"] <= 100
            )  # Confidence can be high for known brands
            assert result["has_brand_identification"] is True

    def test_analyze_pattern_specificity_low_complexity(self, analyzer):
        """Test low specificity pattern analysis."""
        # Low specificity: generic descriptions
        low_specificity_patterns = [
            "synthetic brush",
            "boar bristle",
            "badger brush 26mm",
            "unknown brush",
            "old brush",
        ]

        for pattern in low_specificity_patterns:
            result = analyzer.analyze_pattern_specificity(pattern)

            assert result["specificity_level"] == "low"
            assert result["complexity_score"] < 40
            assert result["confidence_score"] < 50
            assert result["has_brand_identification"] is False

    def test_assess_brand_specificity_known_manufacturers(self, analyzer):
        """Test brand specificity for known manufacturers."""
        manufacturer_patterns = ["Semogue 1305", "Omega 10049", "Zenith B35", "Simpson Trafalgar"]

        for pattern in manufacturer_patterns:
            result = analyzer.assess_brand_specificity(pattern)

            assert result["brand_authority"] == "manufacturer"
            assert result["brand_confidence"] >= 90
            assert result["has_model_number"] is True

    def test_assess_brand_specificity_artisan_brands(self, analyzer):
        """Test brand specificity for artisan brands."""
        artisan_patterns = [
            "Declaration Grooming B15",
            "AP Shave Co synthetic",
            "Maggard Razors 24mm",
            "Stirling Soap Co badger",
        ]

        for pattern in artisan_patterns:
            result = analyzer.assess_brand_specificity(pattern)

            assert result["brand_authority"] in ["cataloged_artisan", "emerging_artisan"]
            assert result["brand_confidence"] >= 60
            assert result["has_brand_identification"] is True

    def test_assess_brand_specificity_unknown_brands(self, analyzer):
        """Test brand specificity for unknown/generic patterns."""
        unknown_patterns = [
            "unknown brand synthetic",
            "generic boar brush",
            "random badger 26mm",
            "some old brush",
        ]

        for pattern in unknown_patterns:
            result = analyzer.assess_brand_specificity(pattern)

            assert result["brand_authority"] == "unknown"
            assert result["brand_confidence"] < 30
            assert result["has_brand_identification"] is False

    def test_calculate_pattern_complexity_score(self, analyzer):
        """Test pattern complexity scoring algorithm."""
        test_cases = [
            {
                "pattern": "Zenith B35 Boar 28mm x 52mm Professional Grade",
                "expected_min_score": 80,
                "expected_features": ["brand", "model", "material", "size", "quality_indicator"],
            },
            {
                "pattern": "AP Shave Co synthetic 26mm",
                "expected_min_score": 50,
                "expected_features": ["brand", "material", "size"],
            },
            {"pattern": "boar brush", "expected_min_score": 0, "expected_features": ["material"]},
        ]

        for case in test_cases:
            result = analyzer.calculate_pattern_complexity_score(case["pattern"])

            assert result["complexity_score"] >= case["expected_min_score"]
            for feature in case["expected_features"]:
                assert feature in result["detected_features"]

    def test_detect_specification_indicators(self, analyzer):
        """Test specification indicator detection."""
        specification_tests = [
            {
                "pattern": "Zenith B35 Boar 28mm x 52mm loft",
                "expected": {
                    "has_size_specification": True,
                    "has_material_specification": True,
                    "has_loft_specification": True,
                    "has_knot_specification": True,
                },
            },
            {
                "pattern": "synthetic brush 26mm",
                "expected": {
                    "has_size_specification": True,
                    "has_material_specification": True,
                    "has_loft_specification": False,
                    "has_knot_specification": True,  # Fixed: synthetic + size = knot specification
                },
            },
            {
                "pattern": "unknown brush",
                "expected": {
                    "has_size_specification": False,
                    "has_material_specification": False,
                    "has_loft_specification": False,
                    "has_knot_specification": False,
                },
            },
        ]

        for test in specification_tests:
            result = analyzer.detect_specification_indicators(test["pattern"])

            for key, expected_value in test["expected"].items():
                assert result[key] == expected_value

    def test_get_pattern_confidence_score(self, analyzer):
        """Test pattern confidence scoring."""
        confidence_tests = [
            {
                "pattern": "Semogue 1305 Pure Boar Bristle",
                "expected_min": 85,
                "reason": "Manufacturer with complete specs",
            },
            {
                "pattern": "Declaration Grooming B15 synthetic 26mm",
                "expected_min": 70,
                "reason": "Known artisan with good specs",
            },
            {
                "pattern": "some synthetic brush 24mm",
                "expected_max": 40,
                "reason": "Unknown brand with minimal specs",
            },
            {"pattern": "brush", "expected_max": 20, "reason": "Minimal information"},
        ]

        for test in confidence_tests:
            score = analyzer.get_pattern_confidence_score(test["pattern"])

            if "expected_min" in test:
                assert (
                    score >= test["expected_min"]
                ), f"Failed for: {test['pattern']} - {test['reason']}"
            if "expected_max" in test:
                assert (
                    score <= test["expected_max"]
                ), f"Failed for: {test['pattern']} - {test['reason']}"

    def test_categorize_pattern_type(self, analyzer):
        """Test pattern type categorization."""
        pattern_type_tests = [
            {
                "pattern": "Zenith B35 Boar 28mm x 52mm loft",
                "expected_type": "complete_specification",
                "expected_category": "manufacturer_detailed",
            },
            {
                "pattern": "Declaration Grooming synthetic brush",
                "expected_type": "partial_specification",
                "expected_category": "artisan_basic",
            },
            {
                "pattern": "boar brush 28mm",
                "expected_type": "minimal_specification",
                "expected_category": "generic_typed",
            },
            {
                "pattern": "unknown brush",
                "expected_type": "incomplete_specification",
                "expected_category": "unidentified",
            },
        ]

        for test in pattern_type_tests:
            result = analyzer.categorize_pattern_type(test["pattern"])

            assert result["pattern_type"] == test["expected_type"]
            assert result["pattern_category"] == test["expected_category"]

    def test_get_specificity_modifier_points(self, analyzer):
        """Test specificity modifier points calculation based on Phase 4.1 spec."""
        # Based on Phase 4.1 quality metrics specification
        assert analyzer.get_specificity_modifier_points("high") == 15
        assert analyzer.get_specificity_modifier_points("medium") == 10
        assert analyzer.get_specificity_modifier_points("low") == 0

    def test_calculate_comprehensive_pattern_analysis(self, analyzer):
        """Test comprehensive pattern analysis combining all factors."""
        comprehensive_tests = [
            {
                "pattern": "Zenith B35 Boar 28mm x 52mm Professional Grade",
                "expected": {
                    "specificity_level": "high",
                    "min_complexity_score": 80,
                    "min_confidence_score": 85,
                    "brand_authority": "manufacturer",
                },
            },
            {
                "pattern": "AP Shave Co synthetic brush 26mm fan",
                "expected": {
                    "specificity_level": "high",  # Fixed: this pattern has brand+material+size+knot
                    "min_complexity_score": 75,  # Updated to match high complexity requirements
                    "min_confidence_score": 80,  # Updated to match high confidence requirements
                    "brand_authority": "cataloged_artisan",
                },
            },
        ]

        for test in comprehensive_tests:
            result = analyzer.calculate_comprehensive_pattern_analysis(test["pattern"])

            assert result["specificity_level"] == test["expected"]["specificity_level"]
            assert result["complexity_score"] >= test["expected"]["min_complexity_score"]
            assert result["confidence_score"] >= test["expected"]["min_confidence_score"]
            assert (
                result["brand_analysis"]["brand_authority"] == test["expected"]["brand_authority"]
            )

    def test_edge_cases_empty_and_none_patterns(self, analyzer):
        """Test behavior with empty and None patterns."""
        edge_cases = [None, "", "   ", "\n\t"]

        for edge_case in edge_cases:
            result = analyzer.analyze_pattern_specificity(edge_case)

            assert result["specificity_level"] == "low"
            assert result["complexity_score"] == 0
            assert result["confidence_score"] == 0
            assert result["has_brand_identification"] is False

    def test_edge_cases_malformed_patterns(self, analyzer):
        """Test behavior with malformed patterns."""
        malformed_patterns = [
            "123!@#$%^&*()",
            "   random   spaces   everywhere   ",
            "UPPERCASE PATTERN ANALYSIS",
            "mixed-CaSe_WeIrD.formatting",
        ]

        for pattern in malformed_patterns:
            result = analyzer.analyze_pattern_specificity(pattern)

            # Should handle gracefully and provide valid results
            assert "specificity_level" in result
            assert "complexity_score" in result
            assert "confidence_score" in result
            assert isinstance(result["complexity_score"], (int, float))
            assert 0 <= result["complexity_score"] <= 100


class TestPatternSpecificityAnalyzerPerformance:
    """Test performance characteristics of pattern specificity analysis."""

    @pytest.fixture
    def analyzer(self) -> PatternSpecificityAnalyzer:
        """Create PatternSpecificityAnalyzer."""
        return PatternSpecificityAnalyzer()

    def test_performance_large_pattern_batch(self, analyzer):
        """Test performance with large batch of patterns."""
        import time

        # Create 1000 test patterns
        test_patterns = [
            f"Brand_{i} Model_{i % 10} {['Boar', 'Badger', 'Synthetic'][i % 3]} {20 + i % 10}mm"
            for i in range(1000)
        ]

        start_time = time.time()

        for pattern in test_patterns:
            analyzer.analyze_pattern_specificity(pattern)

        end_time = time.time()
        processing_time = end_time - start_time

        # Should process 1000 patterns in reasonable time
        assert processing_time < 2.0  # Less than 2 seconds

        # Calculate patterns per second
        patterns_per_second = len(test_patterns) / processing_time
        assert patterns_per_second > 500  # At least 500 patterns per second

    def test_memory_usage_reasonable(self, analyzer):
        """Test that memory usage remains reasonable with pattern analysis."""
        import sys

        # Measure approximate memory usage
        initial_size = sys.getsizeof(analyzer)

        # Process many patterns
        for i in range(100):
            pattern = f"Test Pattern {i} with various specifications 28mm Boar"
            analyzer.analyze_pattern_specificity(pattern)

        final_size = sys.getsizeof(analyzer)

        # Memory usage shouldn't grow significantly
        assert final_size <= initial_size * 1.5  # No more than 50% growth

    def test_consistent_results_repeated_analysis(self, analyzer):
        """Test that repeated analysis of same pattern gives consistent results."""
        test_pattern = "Zenith B35 Boar 28mm Professional Grade"

        # Analyze same pattern multiple times
        results = []
        for _ in range(10):
            result = analyzer.analyze_pattern_specificity(test_pattern)
            results.append(result)

        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result["specificity_level"] == first_result["specificity_level"]
            assert result["complexity_score"] == first_result["complexity_score"]
            assert result["confidence_score"] == first_result["confidence_score"]
