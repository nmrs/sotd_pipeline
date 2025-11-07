"""Strategy Analysis Tool for Brush Matching Optimization.

This tool analyzes which strategies win for each test case in correct_matches directory,
providing empirical data to inform optimal weight configuration.
"""

import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple, Any
import yaml
from collections import defaultdict, Counter

from sotd.match.brush_matcher import BrushMatcher

logger = logging.getLogger(__name__)


class StrategyAnalyzer:
    """Analyzes which strategies win for each test case in correct_matches directory."""

    def __init__(self, config_path: Path, correct_matches_path: Path):
        """Initialize the strategy analyzer.

        Args:
            config_path: Path to brush_scoring_config.yaml
            correct_matches_path: Path to correct_matches directory
        """
        self.config_path = config_path
        self.correct_matches_path = correct_matches_path

        # Load configuration and test cases
        self.config = self._load_config()
        self.test_cases = self._extract_test_cases()

        # Strategy names from config
        self.strategy_names = self._get_strategy_names()

        # Analysis results
        self.analysis_results = {}
        self.strategy_wins = defaultdict(int)
        self.strategy_failures = defaultdict(int)
        self.input_type_analysis = defaultdict(lambda: defaultdict(int))

    def _load_config(self) -> dict:
        """Load the brush scoring configuration."""
        with open(self.config_path, "r") as f:
            return yaml.safe_load(f)

    def _extract_test_cases(self) -> List[Dict[str, Any]]:
        """Extract test cases from correct_matches directory."""
        correct_matches = {}
        
        # Load all field files from directory structure
        if self.correct_matches_path.is_dir():
            for field_file in self.correct_matches_path.glob("*.yaml"):
                field_name = field_file.stem
                # Skip backup and report files
                if field_file.name.endswith((".backup", ".bk")) or "duplicates_report" in field_file.name:
                    continue
                try:
                    with field_file.open("r", encoding="utf-8") as f:
                        field_data = yaml.safe_load(f)
                        if field_data:
                            correct_matches[field_name] = field_data
                except Exception as e:
                    logger.warning(f"Error loading {field_file}: {e}")
        else:
            # Legacy single file support (for backward compatibility)
            with open(self.correct_matches_path, "r") as f:
                correct_matches = yaml.safe_load(f) or {}

        test_cases = []

        # Extract brush test cases
        if "brush" in correct_matches:
            for brand, models in correct_matches["brush"].items():
                for model, inputs in models.items():
                    for input_text in inputs:
                        test_cases.append(
                            {
                                "input": input_text,
                                "expected_type": "complete",
                                "category": "brush",
                                "brand": brand,
                                "model": model,
                                "input_text": input_text,
                            }
                        )

        # Extract handle test cases
        if "handle" in correct_matches:
            for maker, models in correct_matches["handle"].items():
                for model, inputs in models.items():
                    for input_text in inputs:
                        test_cases.append(
                            {
                                "input": input_text,
                                "expected_type": "composite",
                                "category": "handle",
                                "maker": maker,
                                "model": model,
                                "input_text": input_text,
                            }
                        )

        # Extract knot test cases
        if "knot" in correct_matches:
            for brand, models in correct_matches["knot"].items():
                for model, inputs in models.items():
                    for input_text in inputs:
                        test_cases.append(
                            {
                                "input": input_text,
                                "expected_type": "composite",
                                "category": "knot",
                                "brand": brand,
                                "model": model,
                                "input_text": input_text,
                            }
                        )

        logger.info(f"Extracted {len(test_cases)} test cases from correct_matches directory")
        return test_cases

    def _get_strategy_names(self) -> List[str]:
        """Get strategy names from the configuration."""
        strategies = []

        # Base strategies
        if "brush_scoring_weights" in self.config:
            base_strategies = self.config["brush_scoring_weights"].get("base_strategies", {})
            strategies.extend(base_strategies.keys())

            # Strategy modifiers
            strategy_modifiers = self.config["brush_scoring_weights"].get("strategy_modifiers", {})
            strategies.extend(strategy_modifiers.keys())

        # Remove duplicates and sort
        strategies = sorted(list(set(strategies)))
        logger.info(f"Found {len(strategies)} strategies: {strategies}")
        return strategies

    def analyze_strategies(self) -> Dict[str, Any]:
        """Analyze which strategies win for each test case."""
        logger.info("Starting strategy analysis...")

        # Create a brush matcher that bypasses correct_matches directory
        # so we can see which strategies would win naturally
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(self.config, f)
            temp_config_path = Path(f.name)

        try:
            brush_matcher = BrushMatcher(
                brush_scoring_config_path=temp_config_path,
                correct_matches_path=self.correct_matches_path,
            )

            # Analyze each test case
            for i, test_case in enumerate(self.test_cases):
                logger.info(
                    f"Analyzing test case {i + 1}/{len(self.test_cases)}: {test_case['input']}"
                )

                try:
                    # Get the match result
                    result = brush_matcher.match(test_case["input"], bypass_correct_matches=True)

                    if result and result.matched:
                        # Extract strategy information
                        strategy_used = result.matched.get("_matched_by_strategy", "unknown")
                        pattern_used = result.matched.get("_pattern_used", "unknown")

                        # Record the win
                        self.strategy_wins[strategy_used] += 1

                        # Record input type analysis
                        input_type = test_case["expected_type"]
                        self.input_type_analysis[input_type][strategy_used] += 1

                        # Store detailed result
                        self.analysis_results[test_case["input"]] = {
                            "success": True,
                            "strategy": strategy_used,
                            "pattern": pattern_used,
                            "expected_type": test_case["expected_type"],
                            "category": test_case["category"],
                            "matched_data": result.matched,
                        }

                        logger.info(f"  ✓ {strategy_used} won with pattern: {pattern_used}")
                    else:
                        # Record failure
                        self.strategy_failures["no_match"] += 1

                        self.analysis_results[test_case["input"]] = {
                            "success": False,
                            "strategy": None,
                            "pattern": None,
                            "expected_type": test_case["expected_type"],
                            "category": test_case["category"],
                            "matched_data": None,
                        }

                        logger.info(f"  ✗ No match found")

                except Exception as e:
                    logger.error(f"Error analyzing test case '{test_case['input']}': {e}")
                    self.strategy_failures["error"] += 1

                    self.analysis_results[test_case["input"]] = {
                        "success": False,
                        "strategy": None,
                        "pattern": None,
                        "expected_type": test_case["expected_type"],
                        "category": test_case["category"],
                        "error": str(e),
                    }

        finally:
            # Clean up temporary config file
            temp_config_path.unlink(missing_ok=True)

        return self._generate_analysis_summary()

    def _generate_analysis_summary(self) -> Dict[str, Any]:
        """Generate a comprehensive analysis summary."""
        total_cases = len(self.test_cases)
        successful_cases = sum(1 for r in self.analysis_results.values() if r["success"])

        summary = {
            "overall_stats": {
                "total_test_cases": total_cases,
                "successful_matches": successful_cases,
                "success_rate": successful_cases / total_cases if total_cases > 0 else 0,
                "failed_matches": total_cases - successful_cases,
            },
            "strategy_performance": {
                "wins": dict(self.strategy_wins),
                "failures": dict(self.strategy_failures),
            },
            "input_type_analysis": dict(self.input_type_analysis),
            "detailed_results": self.analysis_results,
        }

        return summary

    def generate_recommendations(self) -> Dict[str, Any]:
        """Generate weight recommendations based on analysis."""
        if not self.analysis_results:
            return {"error": "No analysis results available. Run analyze_strategies() first."}

        recommendations = {
            "base_strategy_weights": {},
            "strategy_modifier_weights": {},
            "rationale": {},
        }

        # Analyze base strategy performance
        total_wins = sum(self.strategy_wins.values())
        if total_wins > 0:
            for strategy, wins in self.strategy_wins.items():
                win_rate = wins / total_wins

                # Convert win rate to weight (0-100 scale)
                # Higher win rate = higher weight
                weight = int(win_rate * 100)

                # Ensure minimum weight for strategies that do win
                if wins > 0:
                    weight = max(weight, 20)  # Minimum 20 for any winning strategy

                recommendations["base_strategy_weights"][strategy] = weight
                recommendations["rationale"][
                    strategy
                ] = f"Won {wins}/{total_wins} cases ({win_rate:.1%})"

        # Analyze input type preferences
        for input_type, strategy_counts in self.input_type_analysis.items():
            total_for_type = sum(strategy_counts.values())
            if total_for_type > 0:
                logger.info(f"\nInput type '{input_type}' analysis:")
                for strategy, count in strategy_counts.items():
                    percentage = count / total_for_type
                    logger.info(f"  {strategy}: {count}/{total_for_type} ({percentage:.1%})")

                    # If a strategy dominates a particular input type, boost its weight
                    if percentage > 0.7:  # 70%+ dominance
                        current_weight = recommendations["base_strategy_weights"].get(strategy, 0)
                        recommendations["base_strategy_weights"][strategy] = min(
                            current_weight + 20, 100
                        )
                        recommendations["rationale"][
                            f"{strategy}_boost"
                        ] = f"Dominates {input_type} inputs ({percentage:.1%})"

        return recommendations

    def print_analysis_report(self):
        """Print a comprehensive analysis report."""
        if not self.analysis_results:
            print("No analysis results available. Run analyze_strategies() first.")
            return

        print("=" * 80)
        print("BRUSH MATCHING STRATEGY ANALYSIS REPORT")
        print("=" * 80)

        # Overall statistics
        total_cases = len(self.test_cases)
        successful_cases = sum(1 for r in self.analysis_results.values() if r["success"])
        success_rate = successful_cases / total_cases if total_cases > 0 else 0

        print(f"\nOVERALL PERFORMANCE:")
        print(f"  Total Test Cases: {total_cases}")
        print(f"  Successful Matches: {successful_cases}")
        print(f"  Success Rate: {success_rate:.1%}")
        print(f"  Failed Matches: {total_cases - successful_cases}")

        # Strategy performance
        print(f"\nSTRATEGY PERFORMANCE:")
        total_wins = sum(self.strategy_wins.values())
        for strategy, wins in sorted(self.strategy_wins.items(), key=lambda x: x[1], reverse=True):
            win_rate = wins / total_wins if total_wins > 0 else 0
            print(f"  {strategy}: {wins} wins ({win_rate:.1%})")

        # Input type analysis
        print(f"\nINPUT TYPE ANALYSIS:")
        for input_type, strategy_counts in self.input_type_analysis.items():
            total_for_type = sum(strategy_counts.values())
            print(f"  {input_type.upper()} inputs ({total_for_type} total):")
            for strategy, count in sorted(
                strategy_counts.items(), key=lambda x: x[1], reverse=True
            ):
                percentage = count / total_for_type
                print(f"    {strategy}: {count}/{total_for_type} ({percentage:.1%})")

        # Recommendations
        recommendations = self.generate_recommendations()
        if "base_strategy_weights" in recommendations:
            print(f"\nRECOMMENDED BASE STRATEGY WEIGHTS:")
            for strategy, weight in sorted(
                recommendations["base_strategy_weights"].items(), key=lambda x: x[1], reverse=True
            ):
                rationale = recommendations["rationale"].get(strategy, "")
                print(f"  {strategy}: {weight} ({rationale})")

        print("\n" + "=" * 80)


def main():
    """Main function for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Analyze brush matching strategies")
    parser.add_argument("config_path", type=Path, help="Path to brush_scoring_config.yaml")
    parser.add_argument("correct_matches_path", type=Path, help="Path to correct_matches directory")
    parser.add_argument("--output", type=Path, help="Output file for analysis results (JSON)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Setup logging
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)

    # Run analysis
    analyzer = StrategyAnalyzer(args.config_path, args.correct_matches_path)
    results = analyzer.analyze_strategies()

    # Print report
    analyzer.print_analysis_report()

    # Save results if requested
    if args.output:
        import json

        with open(args.output, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nAnalysis results saved to: {args.output}")


if __name__ == "__main__":
    main()
