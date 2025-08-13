#!/usr/bin/env python3
"""Analysis tool to analyze brush matching and enrichment for any brush string.

This tool provides comprehensive analysis of how brush strings are processed through
the SOTD pipeline's brush matching and enrichment phases. It shows detailed scoring
breakdowns, strategy comparisons, and enrichment results to help understand and
debug the brush matching system.

Usage:
    python tools/analyze_brush_matching.py "brush string here"
    python tools/analyze_brush_matching.py --debug "brush string here"
    python tools/analyze_brush_matching.py --legacy "brush string here"
"""

import argparse
import re
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sotd.enrich.brush_enricher import BrushEnricher
from sotd.match.brush_matcher import BrushMatcher
from sotd.match.scoring_brush_matcher import BrushScoringMatcher


def analyze_brush_matching(brush_string: str, debug: bool = False, show_all_matches: bool = True):
    """Analyze how a brush string is matched and enriched through the SOTD pipeline."""

    print(f"Testing brush string: '{brush_string}'")
    print("=" * 60)

    if show_all_matches:
        # Use the scoring brush matcher to show all possible matches and scores
        print("\n🔍 Using Scoring Brush Matcher (shows ALL strategies and scores)")
        print("=" * 60)

        try:
            scoring_matcher = BrushScoringMatcher()
            result = scoring_matcher.match(brush_string)

            if result and hasattr(result, "all_strategies") and result.all_strategies:
                print("\n📊 ALL STRATEGY RESULTS (sorted by score)")
                print("=" * 50)

                # Sort by score (highest first)
                sorted_strategies = sorted(
                    result.all_strategies, key=lambda x: x.get("score", 0), reverse=True
                )

                for i, strategy_result in enumerate(sorted_strategies, 1):
                    strategy_name = strategy_result.get("strategy", "Unknown")
                    score = strategy_result.get("score", 0)
                    match_type = strategy_result.get("match_type", "Unknown")
                    pattern = strategy_result.get("pattern", "Unknown")
                    matched_data = strategy_result.get("result", {})

                    # Format the score display
                    score_display = f"{score:.1f}"
                    if score >= 80:
                        score_emoji = "🥇"
                    elif score >= 60:
                        score_emoji = "🥈"
                    elif score >= 40:
                        score_emoji = "🥉"
                    else:
                        score_emoji = "📊"

                    print(f"\n{score_emoji} #{i}: {strategy_name.upper()}")
                    print(f"   💯 Score: {score_display}")
                    print(f"   🎯 Match Type: {match_type}")
                    print(f"   🔍 Pattern: {pattern}")

                    # Show detailed score breakdown
                    print("   📊 Score Breakdown:")
                    base_score = _get_base_score_for_strategy(strategy_name)
                    modifier_score = score - base_score
                    print(f"     Base Score: {base_score:.1f}")
                    print(f"     Modifiers: {modifier_score:+.1f}")

                    # Show modifier details if there are any
                    if modifier_score != 0:
                        print("     Modifier Details:")
                        _show_modifier_details(strategy_name, brush_string, matched_data)

                    if matched_data:
                        print("   📝 Matched Data:")
                        # Show key information in a clean way
                        if "brand" in matched_data and matched_data["brand"]:
                            print(f"     🏷️  Brand: {matched_data['brand']}")
                        if "model" in matched_data and matched_data["model"]:
                            print(f"     🏷️  Model: {matched_data['model']}")
                        if "fiber" in matched_data and matched_data["fiber"]:
                            print(f"     🧶 Fiber: {matched_data['fiber']}")
                        if "knot_size_mm" in matched_data and matched_data["knot_size_mm"]:
                            print(f"     📏 Size: {matched_data['knot_size_mm']}mm")

                        # Show handle/knot structure if present
                        if "handle" in matched_data and matched_data["handle"]:
                            handle = matched_data["handle"]
                            if handle.get("brand"):
                                print(f"     🖐️  Handle: {handle['brand']}")
                                if handle.get("model"):
                                    print(f"        Model: {handle['model']}")

                        if "knot" in matched_data and matched_data["knot"]:
                            knot = matched_data["knot"]
                            if knot.get("brand"):
                                print(f"     🧶 Knot: {knot['brand']}")
                                if knot.get("model"):
                                    print(f"        Model: {knot['model']}")
                                if knot.get("fiber"):
                                    print(f"        Fiber: {knot['fiber']}")
                                if knot.get("knot_size_mm"):
                                    print(f"        Size: {knot['knot_size_mm']}mm")

                        # Show other relevant fields
                        for key, value in matched_data.items():
                            excluded_keys = [
                                "brand",
                                "model",
                                "fiber",
                                "knot_size_mm",
                                "handle",
                                "knot",
                                "_matched_by",
                                "_pattern_used",
                                "_matched_from",
                                "source_text",
                            ]
                            if key not in excluded_keys:
                                if value and value != "Unknown":
                                    print(f"     🔧 {key.replace('_', ' ').title()}: {value}")
                    else:
                        print("   ❌ No match data")

                print("\n" + "=" * 60)
                print("🏆 WINNER: Best Match (Highest Score)")
                print("=" * 40)

                if result.matched:
                    strategy = result.matched.get("strategy", "Unknown")
                    score = result.matched.get("score", "N/A")
                    print(f"  🥇 Strategy: {strategy}")
                    print(f"  💯 Score: {score}")
                    print(f"  🎯 Match Type: {result.match_type}")
                    print(f"  🔍 Pattern: {result.pattern}")

                    # Show detailed score breakdown for winner
                    print("  📊 Score Breakdown:")
                    base_score = _get_base_score_for_strategy(strategy)
                    modifier_score = float(score) - base_score if score != "N/A" else 0
                    print(f"    Base Score: {base_score:.1f}")
                    print(f"    Modifiers: {modifier_score:+.1f}")

                    if modifier_score != 0:
                        print("    Modifier Details:")
                        _show_modifier_details(strategy, brush_string, result.matched)

                    print("\n  📝 Final Result:")
                    if "brand" in result.matched and result.matched["brand"]:
                        print(f"     🏷️  Brand: {result.matched['brand']}")
                    if "model" in result.matched and result.matched["model"]:
                        print(f"     🏷️  Model: {result.matched['model']}")
                    if "fiber" in result.matched and result.matched["fiber"]:
                        print(f"     🧶 Fiber: {result.matched['fiber']}")
                    if "knot_size_mm" in result.matched and result.matched["knot_size_mm"]:
                        print(f"     📏 Size: {result.matched['knot_size_mm']}mm")

                    # Show handle/knot structure
                    if "handle" in result.matched and result.matched["handle"]:
                        handle = result.matched["handle"]
                        if handle.get("brand"):
                            print(f"     🖐️  Handle: {handle['brand']}")
                            if handle.get("model"):
                                print(f"        Model: {handle['model']}")

                    if "knot" in result.matched and result.matched["knot"]:
                        knot = result.matched["knot"]
                        if knot.get("brand"):
                            print(f"     🧶 Knot: {knot['brand']}")
                            if knot.get("model"):
                                print(f"        Model: {knot['model']}")
                            if knot.get("fiber"):
                                print(f"        Fiber: {knot['fiber']}")
                            if knot.get("knot_size_mm"):
                                print(f"        Size: {knot['knot_size_mm']}mm")
                else:
                    print("  ❌ No final result")

            else:
                print("  ❌ No matches found or no strategy results available")

        except Exception as e:
            print(f"  ❌ Error with scoring matcher: {e}")
            print("  🔄 Falling back to legacy matcher...")
            show_all_matches = False

    if not show_all_matches:
        # Use the legacy brush matcher
        print("\n🔧 Using Legacy Brush Matcher (first match wins)")
        print("-" * 40)

        # Initialize the brush matcher with debug enabled
        brush_matcher = BrushMatcher(
            catalog_path=Path("data/brushes.yaml"),
            handles_path=Path("data/handles.yaml"),
            knots_path=Path("data/knots.yaml"),
            correct_matches_path=Path("data/correct_matches.yaml"),
            debug=debug,
        )

        # Test each strategy individually
        if debug:
            print("\n🧪 Testing individual strategies:")
            print("-" * 40)

            # Test KnownBrushMatchingStrategy
            print("1. Testing KnownBrushMatchingStrategy:")
            for strategy in brush_matcher.brush_strategies:
                if strategy.__class__.__name__ == "KnownBrushMatchingStrategy":
                    try:
                        result = strategy.match(brush_string)
                        print(f"   Result: {result}")
                        if result and result.matched:
                            print(f"   Brand: {result.matched.get('brand')}")
                            print(f"   Model: {result.matched.get('model')}")
                    except Exception as e:
                        print(f"   Error: {e}")
                    break

        # Test brush matching
        result = brush_matcher.match(brush_string)

        print("\n📊 Brush matching result:")
        if result:
            print(f"  Original: {result.original}")
            print(f"  Match type: {result.match_type}")
            print(f"  Pattern: {result.pattern}")

            matched = result.matched
            if matched:
                print("  Matched data:")
                for key, value in matched.items():
                    print(f"    {key}: {value}")
            else:
                print("  No match data")
        else:
            print("  No match found (result is None)")

    # Test enrich phase
    print("\n" + "=" * 60)
    print("🔧 Testing enrich phase:")
    print("=" * 30)

    # Get the result from the appropriate matcher
    if show_all_matches:
        try:
            scoring_matcher = BrushScoringMatcher()
            result = scoring_matcher.match(brush_string)
        except Exception:
            result = None
    else:
        brush_matcher = BrushMatcher(
            catalog_path=Path("data/brushes.yaml"),
            handles_path=Path("data/handles.yaml"),
            knots_path=Path("data/knots.yaml"),
            correct_matches_path=Path("data/correct_matches.yaml"),
            debug=debug,
        )
        result = brush_matcher.match(brush_string)

    if result and result.matched:
        enricher = BrushEnricher()
        enriched = enricher.enrich(result.matched, brush_string)

        if enriched:
            print("  Enriched data:")
            for key, value in enriched.items():
                print(f"    {key}: {value}")
        else:
            print("  No enrichment possible")
    else:
        print("  Cannot test enrichment - no match data")


def _get_base_score_for_strategy(strategy_name: str) -> float:
    """Get the base score for a strategy from the configuration."""
    # Load configuration from the actual YAML file
    from sotd.match.brush_scoring_config import BrushScoringConfig

    config = BrushScoringConfig()
    return config.get_base_strategy_score(strategy_name)


def _show_modifier_details(strategy_name: str, input_text: str, matched_data: dict):
    """Show detailed breakdown of modifiers applied to a strategy."""
    # Get modifier weights from configuration
    modifier_weights = _get_modifier_weights_for_strategy(strategy_name)

    for modifier_name, weight in modifier_weights.items():
        if weight != 0:  # Only show active modifiers
            modifier_value = _calculate_modifier_value(
                modifier_name, input_text, matched_data, strategy_name
            )
            total_effect = modifier_value * weight
            if total_effect != 0:
                print(
                    f"       {modifier_name}: {modifier_value:.1f} × {weight:+.1f} = "
                    f"{total_effect:+.1f}"
                )


def _get_modifier_weights_for_strategy(strategy_name: str) -> dict:
    """Get modifier weights for a strategy from the configuration."""
    # Load configuration from the actual YAML file
    from sotd.match.brush_scoring_config import BrushScoringConfig

    config = BrushScoringConfig()
    return config.weights.get("strategy_modifiers", {}).get(strategy_name, {})


def _calculate_modifier_value(
    modifier_name: str, input_text: str, matched_data: dict, strategy_name: str
) -> float:
    """Calculate the value of a specific modifier for debugging purposes."""
    # Simplified modifier calculations for debugging
    if modifier_name == "multiple_brands":
        # Check actual matched result for multiple brands
        if strategy_name == "unified":
            handle = matched_data.get("handle", {})
            knot = matched_data.get("knot", {})

            handle_brand = handle.get("brand") if handle else None
            knot_brand = knot.get("brand") if knot else None

            brands_found = set()
            if handle_brand:
                brands_found.add(handle_brand)
            if knot_brand:
                brands_found.add(knot_brand)

            return 1.0 if len(brands_found) > 1 else 0.0
        return 0.0

    elif modifier_name == "dual_component":
        if strategy_name == "unified":
            handle = matched_data.get("handle", {})
            knot = matched_data.get("knot", {})
            return 1.0 if handle and knot else 0.0
        return 0.0

    elif modifier_name == "fiber_words":
        fiber_patterns = [
            r"\bbadger\b",
            r"\bboar\b",
            r"\bsynthetic\b",
            r"\bsyn\b",
            r"\bnylon\b",
            r"\bplissoft\b",
            r"\btuxedo\b",
            r"\bcashmere\b",
            r"\bmixed\b",
            r"\btimberwolf\b",
        ]
        for pattern in fiber_patterns:
            if re.search(pattern, input_text.lower()):
                return 1.0
        return 0.0

    elif modifier_name == "size_specification":
        size_patterns = [r"\b\d+mm\b", r"\b\d+\s*mm\b", r"\b\d+x\d+\b", r"\b\d+\s*x\s*\d+\b"]
        for pattern in size_patterns:
            if re.search(pattern, input_text.lower()):
                return 1.0
        return 0.0

    elif modifier_name == "high_confidence":
        high_confidence_delimiters = [r"\s+w/\s+", r"\s+with\s+", r"\s+in\s+"]
        for delimiter in high_confidence_delimiters:
            if re.search(delimiter, input_text.lower()):
                return 1.0
        return 0.0

    elif modifier_name == "delimiter_confidence":
        high_confidence_delimiters = [r"\s+w/\s+", r"\s+with\s+", r"\s+in\s+"]
        for delimiter in high_confidence_delimiters:
            if re.search(delimiter, input_text.lower()):
                return 1.0
        return 0.0

    elif modifier_name == "handle_indicators":
        # Check for handle-specific indicators in the input text
        handle_indicators = [
            r"\bhandle\b",
            r"\bwood\b",
            r"\bresin\b",
            r"\bacrylic\b",
            r"\bmetal\b",
            r"\bbrass\b",
            r"\baluminum\b",
            r"\bsteel\b",
            r"\btitanium\b",
            r"\bebonite\b",
            r"\bivory\b",
            r"\bhorn\b",
            r"\bbone\b",
            r"\bstone\b",
            r"\bmarble\b",
            r"\bgranite\b",
        ]
        for pattern in handle_indicators:
            if re.search(pattern, input_text.lower()):
                return 1.0
        return 0.0

    elif modifier_name == "knot_indicators":
        # Check for knot-specific indicators in the input text
        knot_indicators = [
            r"\bbadger\b",
            r"\bboar\b",
            r"\bsynthetic\b",
            r"\bsyn\b",
            r"\bnylon\b",
            r"\bplissoft\b",
            r"\btuxedo\b",
            r"\bcashmere\b",
            r"\bmixed\b",
            r"\btimberwolf\b",
            r"\b26mm\b",
            r"\b28mm\b",
            r"\b30mm\b",
            r"\b24mm\b",
            r"\b22mm\b",
        ]
        for pattern in knot_indicators:
            if re.search(pattern, input_text.lower()):
                return 1.0
        return 0.0

    return 0.0


def main():
    parser = argparse.ArgumentParser(
        description="Analyze brush matching and enrichment through the SOTD pipeline"
    )
    parser.add_argument(
        "brush_string",
        nargs="?",
        default="AKA Brushworx manchurian $COMPOSITE",
        help="Brush string to test (default: AKA Brushworx manchurian $COMPOSITE)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output",
    )
    parser.add_argument(
        "--legacy",
        action="store_true",
        help="Use legacy brush matcher (first match wins) instead of scoring system",
    )

    args = parser.parse_args()
    analyze_brush_matching(args.brush_string, args.debug, not args.legacy)


if __name__ == "__main__":
    main()
