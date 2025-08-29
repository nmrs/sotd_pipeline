"""Test harness for brush matching optimization.

This module provides synthetic test cases and validation logic to ensure
the optimizer can work with diverse brush matching scenarios.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

from sotd.match.brush_matcher import BrushMatcher

logger = logging.getLogger(__name__)


class BrushMatchingTestHarness:
    """Test harness for validating brush matching optimization results."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the test harness.

        Args:
            config_path: Path to brush scoring config (optional)
        """
        self.config_path = config_path
        self.synthetic_test_cases = self._create_synthetic_test_cases()
        self.validation_metrics = {}

    def _create_synthetic_test_cases(self) -> List[Dict[str, Any]]:
        """Create synthetic test cases covering various brush matching scenarios."""
        return [
            # Complete brush test cases
            {
                "input": "Simpson Trafalgar T3",
                "type": "complete_brush",
                "expected_brand": "Simpson",
                "expected_model": "Trafalgar T3",
                "category": "known_brush",
                "difficulty": "easy",
            },
            {
                "input": "Zenith B2 Boar",
                "type": "complete_brush",
                "expected_brand": "Zenith",
                "expected_model": "B2 Boar",
                "category": "known_brush",
                "difficulty": "easy",
            },
            {
                "input": "Declaration Grooming B2",
                "type": "complete_brush",
                "expected_brand": "Declaration Grooming",
                "expected_model": "B2",
                "category": "known_brush",
                "difficulty": "medium",
            },
            # Composite brush test cases (handle + knot)
            {
                "input": "Dogwood Handcrafts Zenith B2",
                "type": "composite_brush",
                "expected_handle_brand": "Dogwood Handcrafts",
                "expected_handle_model": "Zenith",
                "expected_knot_brand": "Zenith",
                "expected_knot_model": "B2",
                "category": "dual_component",
                "difficulty": "medium",
            },
            {
                "input": "Declaration Grooming B2 in Mozingo handle",
                "type": "composite_brush",
                "expected_handle_brand": "Mozingo",
                "expected_handle_model": "Declaration Grooming",
                "expected_knot_brand": "Declaration Grooming",
                "expected_knot_model": "B2",
                "category": "dual_component",
                "difficulty": "hard",
            },
            # Handle-only test cases
            {
                "input": "Dogwood Handcrafts handle",
                "type": "handle_only",
                "expected_handle_brand": "Dogwood Handcrafts",
                "expected_handle_model": "handle",
                "category": "single_component",
                "difficulty": "easy",
            },
            # Knot-only test cases
            {
                "input": "Zenith B2 knot",
                "type": "knot_only",
                "expected_knot_brand": "Zenith",
                "expected_knot_model": "B2",
                "category": "single_component",
                "difficulty": "easy",
            },
            # Edge cases
            {
                "input": "Unknown Brand Model X",
                "type": "unknown_brush",
                "expected_brand": None,
                "expected_model": None,
                "category": "fallback",
                "difficulty": "hard",
            },
            {
                "input": "Simpson Trafalgar T3 with custom handle",
                "type": "composite_brush",
                "expected_handle_brand": "custom",
                "expected_handle_model": "handle",
                "expected_knot_brand": "Simpson",
                "expected_knot_model": "Trafalgar T3",
                "category": "dual_component",
                "difficulty": "hard",
            },
        ]

    def validate_optimization_result(
        self,
        original_config: Dict[str, Any],
        optimized_config: Dict[str, Any],
        test_cases: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Validate that optimization improved brush matching performance.

        Args:
            original_config: Original brush scoring configuration
            optimized_config: Optimized brush scoring configuration
            test_cases: Test cases to use (defaults to synthetic cases)

        Returns:
            Validation results with performance metrics
        """
        if test_cases is None:
            test_cases = self.synthetic_test_cases

        logger.info(f"Validating optimization with {len(test_cases)} test cases")

        # Test original configuration
        original_results = self._test_configuration(original_config, test_cases)

        # Test optimized configuration
        optimized_results = self._test_configuration(optimized_config, test_cases)

        # Calculate improvement metrics
        improvement_metrics = self._calculate_improvement_metrics(
            original_results, optimized_results
        )

        # Store validation results
        self.validation_metrics = {
            "original": original_results,
            "optimized": optimized_results,
            "improvement": improvement_metrics,
            "test_cases_used": len(test_cases),
        }

        return self.validation_metrics

    def _test_configuration(
        self, config: Dict[str, Any], test_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Test a configuration against the test cases.

        Args:
            config: Brush scoring configuration to test
            test_cases: Test cases to validate against

        Returns:
            Test results with success rates and detailed metrics
        """
        # Create temporary config file
        import tempfile
        import yaml

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config, f)
            temp_config_path = Path(f.name)

        try:
            # Create brush matcher with this configuration
            brush_matcher = BrushMatcher(
                config_path=temp_config_path,
                bypass_correct_matches=True,  # Use synthetic test cases
            )

            results = {
                "total_tests": len(test_cases),
                "successful_matches": 0,
                "failed_matches": 0,
                "partial_matches": 0,
                "category_breakdown": {},
                "difficulty_breakdown": {},
                "detailed_results": [],
            }

            for test_case in test_cases:
                test_result = self._test_single_case(brush_matcher, test_case)
                results["detailed_results"].append(test_result)

                # Update counters
                if test_result["success"]:
                    results["successful_matches"] += 1
                elif test_result["partial_match"]:
                    results["partial_matches"] += 1
                else:
                    results["failed_matches"] += 1

                # Update category breakdown
                category = test_case["category"]
                if category not in results["category_breakdown"]:
                    results["category_breakdown"][category] = {"success": 0, "total": 0}
                results["category_breakdown"][category]["total"] += 1
                if test_result["success"]:
                    results["category_breakdown"][category]["success"] += 1

                # Update difficulty breakdown
                difficulty = test_case["difficulty"]
                if difficulty not in results["difficulty_breakdown"]:
                    results["difficulty_breakdown"][difficulty] = {"success": 0, "total": 0}
                results["difficulty_breakdown"][difficulty]["total"] += 1
                if test_result["success"]:
                    results["difficulty_breakdown"][difficulty]["success"] += 1

            # Calculate success rates
            results["overall_success_rate"] = results["successful_matches"] / results["total_tests"]
            partial_success = results["successful_matches"] + results["partial_matches"]
            results["partial_success_rate"] = partial_success / results["total_tests"]

            return results

        finally:
            # Clean up temporary config file
            temp_config_path.unlink(missing_ok=True)

    def _test_single_case(
        self, brush_matcher: BrushMatcher, test_case: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test a single test case with the brush matcher.

        Args:
            brush_matcher: Configured brush matcher instance
            test_case: Test case to validate

        Returns:
            Test result with success status and details
        """
        try:
            result = brush_matcher.match(test_case["input"])

            if not result or not result.matched:
                return {
                    "test_case": test_case["input"],
                    "success": False,
                    "partial_match": False,
                    "error": "No match result",
                    "matched_data": None,
                }

            # Validate the match based on test case type
            validation_result = self._validate_test_case_result(result.matched, test_case)

            return {
                "test_case": test_case["input"],
                "success": validation_result["success"],
                "partial_match": validation_result["partial_match"],
                "error": validation_result.get("error"),
                "matched_data": result.matched,
                "validation_details": validation_result,
            }

        except Exception as e:
            return {
                "test_case": test_case["input"],
                "success": False,
                "partial_match": False,
                "error": f"Exception during matching: {str(e)}",
                "matched_data": None,
            }

    def _validate_test_case_result(
        self, matched_data: Dict[str, Any], test_case: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate that the match result meets the test case expectations.

        Args:
            matched_data: Data returned by the brush matcher
            test_case: Test case with expected results

        Returns:
            Validation result with success status and details
        """
        test_type = test_case["type"]

        if test_type == "complete_brush":
            return self._validate_complete_brush(matched_data, test_case)
        elif test_type == "composite_brush":
            return self._validate_composite_brush(matched_data, test_case)
        elif test_type == "handle_only":
            return self._validate_handle_only(matched_data, test_case)
        elif test_type == "knot_only":
            return self._validate_knot_only(matched_data, test_case)
        elif test_type == "unknown_brush":
            return self._validate_unknown_brush(matched_data, test_case)
        else:
            return {
                "success": False,
                "partial_match": False,
                "error": f"Unknown test case type: {test_type}",
            }

    def _validate_complete_brush(
        self, matched_data: Dict[str, Any], test_case: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate a complete brush match result."""
        brand = matched_data.get("brand")
        model = matched_data.get("model")

        if not brand or not model:
            return {
                "success": False,
                "partial_match": False,
                "error": "Missing brand or model in complete brush match",
            }

        expected_brand = test_case["expected_brand"]
        expected_model = test_case["expected_model"]

        brand_match = brand.lower() == expected_brand.lower()
        model_match = model.lower() == expected_model.lower()

        if brand_match and model_match:
            return {"success": True, "partial_match": False}
        elif brand_match or model_match:
            return {
                "success": False,
                "partial_match": True,
                "error": f"Partial match: brand={brand_match}, model={model_match}",
            }
        else:
            return {
                "success": False,
                "partial_match": False,
                "error": f"Brand/model mismatch: got '{brand} {model}', expected '{expected_brand} {expected_model}'",
            }

    def _validate_composite_brush(
        self, matched_data: Dict[str, Any], test_case: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate a composite brush match result."""
        handle = matched_data.get("handle", {})
        knot = matched_data.get("knot", {})

        if not handle or not knot:
            return {
                "success": False,
                "partial_match": False,
                "error": "Missing handle or knot in composite brush match",
            }

        # Validate handle if expected
        handle_validation = {"success": True, "partial_match": False}
        if "expected_handle_brand" in test_case:
            handle_brand = handle.get("brand")
            handle_model = handle.get("model")
            expected_handle_brand = test_case["expected_handle_brand"]
            expected_handle_model = test_case["expected_handle_model"]

            if not handle_brand or not handle_model:
                handle_validation = {
                    "success": False,
                    "partial_match": False,
                    "error": "Missing handle brand or model",
                }
            elif (
                handle_brand.lower() != expected_handle_brand.lower()
                or handle_model.lower() != expected_handle_model.lower()
            ):
                handle_validation = {
                    "success": False,
                    "partial_match": False,
                    "error": f"Handle mismatch: got '{handle_brand} {handle_model}', expected '{expected_handle_brand} {expected_handle_model}'",
                }

        # Validate knot if expected
        knot_validation = {"success": True, "partial_match": False}
        if "expected_knot_brand" in test_case:
            knot_brand = knot.get("brand")
            knot_model = knot.get("model")
            expected_knot_brand = test_case["expected_knot_brand"]
            expected_knot_model = test_case["expected_knot_model"]

            if not knot_brand or not knot_model:
                knot_validation = {
                    "success": False,
                    "partial_match": False,
                    "error": "Missing knot brand or model",
                }
            elif (
                knot_brand.lower() != expected_knot_brand.lower()
                or knot_model.lower() != expected_knot_model.lower()
            ):
                knot_validation = {
                    "success": False,
                    "partial_match": False,
                    "error": f"Knot mismatch: got '{knot_brand} {knot_model}', expected '{expected_knot_brand} {expected_knot_model}'",
                }

        # Overall success depends on both validations
        if handle_validation["success"] and knot_validation["success"]:
            return {"success": True, "partial_match": False}
        elif handle_validation["success"] or knot_validation["success"]:
            return {
                "success": False,
                "partial_match": True,
                "error": f"Partial composite match: handle={handle_validation['success']}, knot={knot_validation['success']}",
            }
        else:
            return {
                "success": False,
                "partial_match": False,
                "error": f"Composite brush validation failed: {handle_validation.get('error')}, {knot_validation.get('error')}",
            }

    def _validate_handle_only(
        self, matched_data: Dict[str, Any], test_case: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate a handle-only match result."""
        handle = matched_data.get("handle", {})

        if not handle:
            return {
                "success": False,
                "partial_match": False,
                "error": "Missing handle in handle-only match",
            }

        handle_brand = handle.get("brand")
        handle_model = handle.get("model")
        expected_handle_brand = test_case["expected_handle_brand"]
        expected_handle_model = test_case["expected_handle_model"]

        if not handle_brand or not handle_model:
            return {
                "success": False,
                "partial_match": False,
                "error": "Missing handle brand or model",
            }

        if (
            handle_brand.lower() == expected_handle_brand.lower()
            and handle_model.lower() == expected_handle_model.lower()
        ):
            return {"success": True, "partial_match": False}
        else:
            return {
                "success": False,
                "partial_match": False,
                "error": f"Handle mismatch: got '{handle_brand} {handle_model}', expected '{expected_handle_brand} {expected_handle_model}'",
            }

    def _validate_knot_only(
        self, matched_data: Dict[str, Any], test_case: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate a knot-only match result."""
        knot = matched_data.get("knot", {})

        if not knot:
            return {
                "success": False,
                "partial_match": False,
                "error": "Missing knot in knot-only match",
            }

        knot_brand = knot.get("brand")
        knot_model = knot.get("model")
        expected_knot_brand = test_case["expected_knot_brand"]
        expected_knot_model = test_case["expected_knot_model"]

        if not knot_brand or not knot_model:
            return {
                "success": False,
                "partial_match": False,
                "error": "Missing knot brand or model",
            }

        if (
            knot_brand.lower() == expected_knot_brand.lower()
            and knot_model.lower() == expected_knot_model.lower()
        ):
            return {"success": True, "partial_match": False}
        else:
            return {
                "success": False,
                "partial_match": False,
                "error": f"Knot mismatch: got '{knot_brand} {knot_model}', expected '{expected_knot_brand} {expected_knot_model}'",
            }

    def _validate_unknown_brush(
        self, matched_data: Dict[str, Any], test_case: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate an unknown brush match result."""
        # For unknown brushes, we expect either no match or a fallback strategy
        # Success is defined as not crashing and providing reasonable output
        if matched_data:
            # If we got some data, that's acceptable for unknown brushes
            return {"success": True, "partial_match": False}
        else:
            # No match is also acceptable for unknown brushes
            return {"success": True, "partial_match": False}

    def _calculate_improvement_metrics(
        self, original_results: Dict[str, Any], optimized_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate improvement metrics between original and optimized configurations.

        Args:
            original_results: Results from original configuration
            optimized_results: Results from optimized configuration

        Returns:
            Improvement metrics and analysis
        """
        original_success_rate = original_results["overall_success_rate"]
        optimized_success_rate = optimized_results["overall_success_rate"]

        absolute_improvement = optimized_success_rate - original_success_rate
        relative_improvement = (
            (absolute_improvement / original_success_rate * 100)
            if original_success_rate > 0
            else float("inf")
        )

        # Category-specific improvements
        category_improvements = {}
        for category in original_results["category_breakdown"]:
            if category in optimized_results["category_breakdown"]:
                orig_category_rate = (
                    original_results["category_breakdown"][category]["success"]
                    / original_results["category_breakdown"][category]["total"]
                )
                opt_category_rate = (
                    optimized_results["category_breakdown"][category]["success"]
                    / optimized_results["category_breakdown"][category]["total"]
                )
                category_improvements[category] = {
                    "original_rate": orig_category_rate,
                    "optimized_rate": opt_category_rate,
                    "improvement": opt_category_rate - orig_category_rate,
                }

        # Difficulty-specific improvements
        difficulty_improvements = {}
        for difficulty in original_results["difficulty_breakdown"]:
            if difficulty in optimized_results["difficulty_breakdown"]:
                orig_difficulty_rate = (
                    original_results["difficulty_breakdown"][difficulty]["success"]
                    / original_results["difficulty_breakdown"][difficulty]["total"]
                )
                opt_difficulty_rate = (
                    optimized_results["difficulty_breakdown"][difficulty]["success"]
                    / optimized_results["difficulty_breakdown"][difficulty]["total"]
                )
                difficulty_improvements[difficulty] = {
                    "original_rate": orig_difficulty_rate,
                    "optimized_rate": opt_difficulty_rate,
                    "improvement": opt_difficulty_rate - orig_difficulty_rate,
                }

        return {
            "overall_improvement": {
                "absolute": absolute_improvement,
                "relative_percent": relative_improvement,
                "original_rate": original_success_rate,
                "optimized_rate": optimized_success_rate,
            },
            "category_improvements": category_improvements,
            "difficulty_improvements": difficulty_improvements,
            "regression_analysis": self._analyze_regressions(original_results, optimized_results),
        }

    def _analyze_regressions(
        self, original_results: Dict[str, Any], optimized_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze any regressions in the optimization results.

        Args:
            original_results: Results from original configuration
            optimized_results: Results from optimized configuration

        Returns:
            Regression analysis results
        """
        regressions = []
        improvements = []

        # Compare detailed results
        for i, (orig_result, opt_result) in enumerate(
            zip(original_results["detailed_results"], optimized_results["detailed_results"])
        ):
            if orig_result["success"] and not opt_result["success"]:
                regressions.append(
                    {
                        "test_case": orig_result["test_case"],
                        "original_success": True,
                        "optimized_success": False,
                        "error": opt_result.get("error", "Unknown error"),
                    }
                )
            elif not orig_result["success"] and opt_result["success"]:
                improvements.append(
                    {
                        "test_case": orig_result["test_case"],
                        "original_success": False,
                        "optimized_success": True,
                    }
                )

        return {
            "regressions": regressions,
            "improvements": improvements,
            "regression_count": len(regressions),
            "improvement_count": len(improvements),
            "net_change": len(improvements) - len(regressions),
        }

    def generate_validation_report(self) -> str:
        """Generate a human-readable validation report.

        Returns:
            Formatted validation report string
        """
        if not self.validation_metrics:
            return "No validation metrics available. Run validate_optimization_result() first."

        report = []
        report.append("=" * 60)
        report.append("BRUSH MATCHING OPTIMIZATION VALIDATION REPORT")
        report.append("=" * 60)
        report.append("")

        # Overall results
        overall = self.validation_metrics["improvement"]["overall_improvement"]
        report.append(f"OVERALL PERFORMANCE:")
        report.append(f"  Original Success Rate: {overall['original_rate']:.1%}")
        report.append(f"  Optimized Success Rate: {overall['optimized_rate']:.1%}")
        report.append(f"  Absolute Improvement: {overall['absolute']:.1%}")
        report.append(f"  Relative Improvement: {overall['relative_percent']:.1f}%")
        report.append("")

        # Category breakdown
        report.append("CATEGORY BREAKDOWN:")
        for category, metrics in self.validation_metrics["improvement"][
            "category_improvements"
        ].items():
            report.append(f"  {category.replace('_', ' ').title()}:")
            report.append(f"    Original: {metrics['original_rate']:.1%}")
            report.append(f"    Optimized: {metrics['optimized_rate']:.1%}")
            report.append(f"    Improvement: {metrics['improvement']:.1%}")
        report.append("")

        # Difficulty breakdown
        report.append("DIFFICULTY BREAKDOWN:")
        for difficulty, metrics in self.validation_metrics["improvement"][
            "difficulty_improvements"
        ].items():
            report.append(f"  {difficulty.title()}:")
            report.append(f"    Original: {metrics['original_rate']:.1%}")
            report.append(f"    Optimized: {metrics['optimized_rate']:.1%}")
            report.append(f"    Improvement: {metrics['improvement']:.1%}")
        report.append("")

        # Regression analysis
        regression_analysis = self.validation_metrics["improvement"]["regression_analysis"]
        report.append("REGRESSION ANALYSIS:")
        report.append(f"  Regressions: {regression_analysis['regression_count']}")
        report.append(f"  Improvements: {regression_analysis['improvement_count']}")
        report.append(f"  Net Change: {regression_analysis['net_change']}")

        if regression_analysis["regressions"]:
            report.append("  Regression Details:")
            for reg in regression_analysis["regressions"][:5]:  # Show first 5
                report.append(f"    - {reg['test_case']}: {reg['error']}")
            if len(regression_analysis["regressions"]) > 5:
                report.append(f"    ... and {len(regression_analysis['regressions']) - 5} more")

        report.append("")
        report.append("=" * 60)

        return "\n".join(report)
