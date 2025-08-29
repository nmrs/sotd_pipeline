"""Tests for the brush matching test harness."""

from unittest.mock import Mock, patch

from sotd.optimization.test_harness import BrushMatchingTestHarness


class TestBrushMatchingTestHarness:
    """Test the BrushMatchingTestHarness class."""

    def test_initialization(self):
        """Test harness initialization."""
        harness = BrushMatchingTestHarness()

        assert harness.config_path is None
        assert len(harness.synthetic_test_cases) > 0
        assert harness.validation_metrics == {}

    def test_synthetic_test_cases_creation(self):
        """Test that synthetic test cases are created correctly."""
        harness = BrushMatchingTestHarness()

        # Check that we have test cases of different types
        test_types = {case["type"] for case in harness.synthetic_test_cases}
        expected_types = {
            "complete_brush",
            "composite_brush",
            "handle_only",
            "knot_only",
            "unknown_brush",
        }
        assert test_types == expected_types

        # Check that we have test cases of different categories
        categories = {case["category"] for case in harness.synthetic_test_cases}
        expected_categories = {"known_brush", "dual_component", "single_component", "fallback"}
        assert categories == expected_categories

        # Check that we have test cases of different difficulties
        difficulties = {case["difficulty"] for case in harness.synthetic_test_cases}
        expected_difficulties = {"easy", "medium", "hard"}
        assert difficulties == expected_difficulties

    def test_validate_complete_brush_success(self):
        """Test successful complete brush validation."""
        harness = BrushMatchingTestHarness()

        test_case = {
            "type": "complete_brush",
            "expected_brand": "Simpson",
            "expected_model": "Trafalgar T3",
        }

        matched_data = {"brand": "Simpson", "model": "Trafalgar T3"}

        result = harness._validate_complete_brush(matched_data, test_case)
        assert result["success"] is True
        assert result["partial_match"] is False

    def test_validate_complete_brush_partial_match(self):
        """Test partial match in complete brush validation."""
        harness = BrushMatchingTestHarness()

        test_case = {
            "type": "complete_brush",
            "expected_brand": "Simpson",
            "expected_model": "Trafalgar T3",
        }

        matched_data = {"brand": "Simpson", "model": "Wrong Model"}

        result = harness._validate_complete_brush(matched_data, test_case)
        assert result["success"] is False
        assert result["partial_match"] is True
        assert "Partial match" in result["error"]

    def test_validate_complete_brush_failure(self):
        """Test failed complete brush validation."""
        harness = BrushMatchingTestHarness()

        test_case = {
            "type": "complete_brush",
            "expected_brand": "Simpson",
            "expected_model": "Trafalgar T3",
        }

        matched_data = {"brand": "Wrong Brand", "model": "Wrong Model"}

        result = harness._validate_complete_brush(matched_data, test_case)
        assert result["success"] is False
        assert result["partial_match"] is False
        assert "Brand/model mismatch" in result["error"]

    def test_validate_composite_brush_success(self):
        """Test successful composite brush validation."""
        harness = BrushMatchingTestHarness()

        test_case = {
            "type": "composite_brush",
            "expected_handle_brand": "Dogwood Handcrafts",
            "expected_handle_model": "Zenith",
            "expected_knot_brand": "Zenith",
            "expected_knot_model": "B2",
        }

        matched_data = {
            "handle": {"brand": "Dogwood Handcrafts", "model": "Zenith"},
            "knot": {"brand": "Zenith", "model": "B2"},
        }

        result = harness._validate_composite_brush(matched_data, test_case)
        assert result["success"] is True
        assert result["partial_match"] is False

    def test_validate_composite_brush_partial_match(self):
        """Test partial match in composite brush validation."""
        harness = BrushMatchingTestHarness()

        test_case = {
            "type": "composite_brush",
            "expected_handle_brand": "Dogwood Handcrafts",
            "expected_handle_model": "Zenith",
            "expected_knot_brand": "Zenith",
            "expected_knot_model": "B2",
        }

        matched_data = {
            "handle": {"brand": "Dogwood Handcrafts", "model": "Zenith"},
            "knot": {"brand": "Wrong Brand", "model": "Wrong Model"},
        }

        result = harness._validate_composite_brush(matched_data, test_case)
        assert result["success"] is False
        assert result["partial_match"] is True
        assert "Partial composite match" in result["error"]

    def test_validate_composite_brush_failure(self):
        """Test failed composite brush validation."""
        harness = BrushMatchingTestHarness()

        test_case = {
            "type": "composite_brush",
            "expected_handle_brand": "Dogwood Handcrafts",
            "expected_handle_model": "Zenith",
            "expected_knot_brand": "Zenith",
            "expected_knot_model": "B2",
        }

        matched_data = {
            "handle": {"brand": "Wrong Brand", "model": "Wrong Model"},
            "knot": {"brand": "Wrong Brand", "model": "Wrong Model"},
        }

        result = harness._validate_composite_brush(matched_data, test_case)
        assert result["success"] is False
        assert result["partial_match"] is False
        assert "Composite brush validation failed" in result["error"]

    def test_validate_handle_only_success(self):
        """Test successful handle-only validation."""
        harness = BrushMatchingTestHarness()

        test_case = {
            "type": "handle_only",
            "expected_handle_brand": "Dogwood Handcrafts",
            "expected_handle_model": "handle",
        }

        matched_data = {"handle": {"brand": "Dogwood Handcrafts", "model": "handle"}}

        result = harness._validate_handle_only(matched_data, test_case)
        assert result["success"] is True
        assert result["partial_match"] is False

    def test_validate_knot_only_success(self):
        """Test successful knot-only validation."""
        harness = BrushMatchingTestHarness()

        test_case = {
            "type": "knot_only",
            "expected_knot_brand": "Zenith",
            "expected_knot_model": "B2",
        }

        matched_data = {"knot": {"brand": "Zenith", "model": "B2"}}

        result = harness._validate_knot_only(matched_data, test_case)
        assert result["success"] is True
        assert result["partial_match"] is False

    def test_validate_unknown_brush(self):
        """Test unknown brush validation."""
        harness = BrushMatchingTestHarness()

        test_case = {"type": "unknown_brush", "expected_brand": None, "expected_model": None}

        # Test with no match (acceptable)
        result = harness._validate_unknown_brush({}, test_case)
        assert result["success"] is True
        assert result["partial_match"] is False

        # Test with some data (also acceptable)
        result = harness._validate_unknown_brush({"brand": "Unknown"}, test_case)
        assert result["success"] is True
        assert result["partial_match"] is False

    def test_validate_test_case_result_unknown_type(self):
        """Test validation with unknown test case type."""
        harness = BrushMatchingTestHarness()

        test_case = {"type": "unknown_type"}
        matched_data = {}

        result = harness._validate_test_case_result(matched_data, test_case)
        assert result["success"] is False
        assert result["partial_match"] is False
        assert "Unknown test case type" in result["error"]

    @patch("sotd.optimization.test_harness.BrushMatcher")
    @patch("tempfile.NamedTemporaryFile")
    @patch("yaml.dump")
    def test_test_configuration_success(self, mock_yaml_dump, mock_tempfile, mock_brush_matcher):
        """Test successful configuration testing."""
        # Mock the temporary file
        mock_temp = Mock()
        mock_temp.name = "/tmp/test_config.yaml"
        mock_tempfile.return_value.__enter__.return_value = mock_temp

        # Mock the brush matcher
        mock_matcher = Mock()
        mock_brush_matcher.return_value = mock_matcher

        # Mock successful match results
        mock_result = Mock()
        mock_result.matched = {"brand": "Simpson", "model": "Trafalgar T3"}
        mock_matcher.match.return_value = mock_result

        harness = BrushMatchingTestHarness()
        test_cases = [
            {
                "input": "Simpson Trafalgar T3",
                "type": "complete_brush",
                "expected_brand": "Simpson",
                "expected_model": "Trafalgar T3",
                "category": "known_brush",
                "difficulty": "easy",
            }
        ]

        config = {"test": "config"}

        results = harness._test_configuration(config, test_cases)

        assert results["total_tests"] == 1
        assert results["successful_matches"] == 1
        assert results["failed_matches"] == 0
        assert results["overall_success_rate"] == 1.0

    @patch("sotd.optimization.test_harness.BrushMatcher")
    @patch("tempfile.NamedTemporaryFile")
    @patch("yaml.dump")
    def test_test_configuration_failure(self, mock_yaml_dump, mock_tempfile, mock_brush_matcher):
        """Test configuration testing with failures."""
        # Mock the temporary file
        mock_temp = Mock()
        mock_temp.name = "/tmp/test_config.yaml"
        mock_tempfile.return_value.__enter__.return_value = mock_temp

        # Mock the brush matcher
        mock_matcher = Mock()
        mock_brush_matcher.return_value = mock_matcher

        # Mock failed match results
        mock_result = Mock()
        mock_result.matched = None
        mock_matcher.match.return_value = mock_result

        harness = BrushMatchingTestHarness()
        test_cases = [
            {
                "input": "Unknown Brush",
                "type": "complete_brush",
                "expected_brand": "Unknown",
                "expected_model": "Brush",
                "category": "fallback",
                "difficulty": "hard",
            }
        ]

        config = {"test": "config"}

        results = harness._test_configuration(config, test_cases)

        assert results["total_tests"] == 1
        assert results["successful_matches"] == 0
        assert results["failed_matches"] == 1
        assert results["overall_success_rate"] == 0.0

    def test_calculate_improvement_metrics(self):
        """Test improvement metrics calculation."""
        harness = BrushMatchingTestHarness()

        original_results = {
            "overall_success_rate": 0.5,
            "category_breakdown": {
                "known_brush": {"success": 2, "total": 4},
                "dual_component": {"success": 1, "total": 4},
            },
            "difficulty_breakdown": {
                "easy": {"success": 2, "total": 4},
                "hard": {"success": 1, "total": 4},
            },
            "detailed_results": [
                {"test_case": "Test 1", "success": True},
                {"test_case": "Test 2", "success": False},
            ],
        }

        optimized_results = {
            "overall_success_rate": 0.75,
            "category_breakdown": {
                "known_brush": {"success": 3, "total": 4},
                "dual_component": {"success": 3, "total": 4},
            },
            "difficulty_breakdown": {
                "easy": {"success": 3, "total": 4},
                "hard": {"success": 3, "total": 4},
            },
            "detailed_results": [
                {"test_case": "Test 1", "success": True},
                {"test_case": "Test 2", "success": True},
            ],
        }

        metrics = harness._calculate_improvement_metrics(original_results, optimized_results)

        assert metrics["overall_improvement"]["absolute"] == 0.25
        assert metrics["overall_improvement"]["relative_percent"] == 50.0
        assert "known_brush" in metrics["category_improvements"]
        assert "easy" in metrics["difficulty_improvements"]

    def test_analyze_regressions(self):
        """Test regression analysis."""
        harness = BrushMatchingTestHarness()

        original_results = {
            "detailed_results": [
                {"test_case": "Test 1", "success": True},
                {"test_case": "Test 2", "success": False},
                {"test_case": "Test 3", "success": True},
            ]
        }

        optimized_results = {
            "detailed_results": [
                {"test_case": "Test 1", "success": False, "error": "Failed"},
                {"test_case": "Test 2", "success": True},
                {"test_case": "Test 3", "success": True},
            ]
        }

        analysis = harness._analyze_regressions(original_results, optimized_results)

        assert analysis["regression_count"] == 1
        assert analysis["improvement_count"] == 1
        assert analysis["net_change"] == 0
        assert len(analysis["regressions"]) == 1
        assert len(analysis["improvements"]) == 1

    def test_generate_validation_report_no_metrics(self):
        """Test validation report generation without metrics."""
        harness = BrushMatchingTestHarness()

        report = harness.generate_validation_report()
        assert "No validation metrics available" in report

    def test_generate_validation_report_with_metrics(self):
        """Test validation report generation with metrics."""
        harness = BrushMatchingTestHarness()

        # Set up mock validation metrics
        harness.validation_metrics = {
            "improvement": {
                "overall_improvement": {
                    "original_rate": 0.5,
                    "optimized_rate": 0.75,
                    "absolute": 0.25,
                    "relative_percent": 50.0,
                },
                "category_improvements": {
                    "known_brush": {
                        "original_rate": 0.5,
                        "optimized_rate": 0.75,
                        "improvement": 0.25,
                    }
                },
                "difficulty_improvements": {
                    "easy": {"original_rate": 0.5, "optimized_rate": 0.75, "improvement": 0.25}
                },
                "regression_analysis": {
                    "regression_count": 0,
                    "improvement_count": 1,
                    "net_change": 1,
                    "regressions": [],
                    "improvements": [{"test_case": "Test 1"}],
                },
            }
        }

        report = harness.generate_validation_report()

        assert "BRUSH MATCHING OPTIMIZATION VALIDATION REPORT" in report
        assert "Original Success Rate: 50.0%" in report
        assert "Optimized Success Rate: 75.0%" in report
        assert "Absolute Improvement: 25.0%" in report
        assert "Relative Improvement: 50.0%" in report
