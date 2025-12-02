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
    python tools/analyze_brush_matching.py --bypass-correct-matches "brush string here"
"""

import argparse
import re
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from sotd.enrich.brush_enricher import BrushEnricher
    from sotd.match.brush.config import BrushScoringConfig
    from sotd.match.brush.scoring.engine import ScoringEngine
    from sotd.match.brush_matcher import BrushMatcher
except ImportError:
    print(
        "Error: Could not import required modules. Make sure you're running from the project root."
    )
    sys.exit(1)


def analyze_brush_matching(
    brush_string: str,
    debug: bool = False,
    show_all_matches: bool = True,
    bypass_correct_matches: bool = False,
):
    """Analyze how a brush string is matched and enriched through the SOTD pipeline."""

    print(f"Testing brush string: '{brush_string}'")
    print("=" * 60)

    if bypass_correct_matches:
        print("\n🚫 BYPASSING correct_matches.yaml - Testing raw matchers only")
        print("=" * 60)

    if show_all_matches:
        # Use the scoring brush matcher to show all possible matches and scores
        print("\n🔍 Using Scoring Brush Matcher (shows ALL strategies and scores)")
        print("=" * 60)

        try:
            scoring_matcher = BrushMatcher()

            # If bypassing correct_matches, temporarily patch multiple components
            original_match_method = None
            original_legacy_methods = {}
            if bypass_correct_matches:
                # Store the original match method from correct_matches_matcher
                original_match_method = scoring_matcher.correct_matches_matcher.match

                # Create a dummy method that always returns None
                def dummy_match(value):
                    return None

                # Replace the match method temporarily
                scoring_matcher.correct_matches_matcher.match = dummy_match

                # Also patch the legacy matcher methods that wrapper strategies call
                # We need to find the legacy matcher instance used by the strategies
                if hasattr(scoring_matcher, "strategy_orchestrator") and hasattr(
                    scoring_matcher.strategy_orchestrator, "strategies"
                ):
                    for strategy in scoring_matcher.strategy_orchestrator.strategies:
                        if hasattr(strategy, "legacy_matcher"):
                            legacy_matcher = strategy.legacy_matcher

                            # Store original methods
                            if hasattr(legacy_matcher, "_match_correct_complete_brush"):
                                original_legacy_methods["_match_correct_complete_brush"] = (
                                    legacy_matcher._match_correct_complete_brush
                                )
                                legacy_matcher._match_correct_complete_brush = dummy_match

                            if hasattr(legacy_matcher, "_match_correct_split_brush"):
                                original_legacy_methods["_match_correct_split_brush"] = (
                                    legacy_matcher._match_correct_split_brush
                                )
                                legacy_matcher._match_correct_split_brush = dummy_match

                            # Also patch the correct_matches_checker.check method
                            if hasattr(legacy_matcher, "correct_matches_checker") and hasattr(
                                legacy_matcher.correct_matches_checker, "check"
                            ):
                                original_legacy_methods["correct_matches_checker.check"] = (
                                    legacy_matcher.correct_matches_checker.check
                                )
                                legacy_matcher.correct_matches_checker.check = dummy_match

                            # Only need to patch the first legacy matcher we find
                            break

                print(
                    "  📝 Temporarily patched correct_matches_matcher and legacy "
                    "matcher methods to bypass all matches"
                )

            result = scoring_matcher.match(brush_string, bypass_correct_matches=True)

            # Restore all original methods if we bypassed them
            if bypass_correct_matches:
                if original_match_method is not None:
                    scoring_matcher.correct_matches_matcher.match = original_match_method

                # Restore legacy matcher methods
                if hasattr(scoring_matcher, "strategy_orchestrator") and hasattr(
                    scoring_matcher.strategy_orchestrator, "strategies"
                ):
                    for strategy in scoring_matcher.strategy_orchestrator.strategies:
                        if hasattr(strategy, "legacy_matcher"):
                            legacy_matcher = strategy.legacy_matcher

                            # Restore original methods
                            for method_name, original_method in original_legacy_methods.items():
                                if hasattr(legacy_matcher, method_name):
                                    setattr(legacy_matcher, method_name, original_method)

                            # Only need to restore the first legacy matcher we find
                            break

            if result and hasattr(result, "all_strategies") and result.all_strategies:
                print("\n📊 ALL STRATEGY RESULTS (sorted by score)")
                print("=" * 50)

                # Sort by score (highest first)
                sorted_strategies = sorted(
                    result.all_strategies, key=lambda x: getattr(x, "score", 0) or 0, reverse=True
                )

                for i, strategy_result in enumerate(sorted_strategies, 1):
                    # Defensive programming: ensure strategy_result is valid
                    if strategy_result is None:
                        print(f"\n⚠️  #{i}: SKIPPING None strategy_result")
                        continue

                    strategy_name = getattr(strategy_result, "strategy", None)
                    if strategy_name is None:
                        raise ValueError(
                            f"Strategy result #{i} has None strategy name. "
                            "This is a bug in the scoring system."
                        )

                    score = getattr(strategy_result, "score", 0) or 0
                    match_type = getattr(strategy_result, "match_type", "Unknown")
                    pattern = getattr(strategy_result, "pattern", "Unknown")
                    matched_data = getattr(strategy_result, "matched", {}) or {}

                    # Check if this strategy actually produced valid results
                    has_valid_data = matched_data and (
                        matched_data.get("brand")
                        or matched_data.get("handle")
                        or matched_data.get("knot")
                    )

                    # Format the score display with appropriate status indicators
                    score_display = f"{score:.1f}"
                    if has_valid_data:
                        # Successful strategies get medal emojis based on score
                        if score >= 80:
                            score_emoji = "🥇"
                            status_indicator = "✅ MATCHED"
                        elif score >= 60:
                            score_emoji = "🥈"
                            status_indicator = "✅ MATCHED"
                        elif score >= 40:
                            score_emoji = "🥉"
                            status_indicator = "✅ MATCHED"
                        else:
                            score_emoji = "📊"
                            status_indicator = "✅ MATCHED"
                    else:
                        # Failed strategies get different indicators
                        if score >= 80:
                            score_emoji = "📊"
                            status_indicator = "❌ NO MATCH"
                        elif score >= 60:
                            score_emoji = "📊"
                            status_indicator = "❌ NO MATCH"
                        elif score >= 40:
                            score_emoji = "📊"
                            status_indicator = "❌ NO MATCH"
                        else:
                            score_emoji = "📊"
                            status_indicator = "❌ NO MATCH"

                    print(f"\n{score_emoji} #{i}: {strategy_name.upper()} - {status_indicator}")
                    print(f"   💯 Score: {score_display}")
                    print(f"   🎯 Match Type: {match_type}")
                    print(f"   🔍 Pattern: {pattern}")

                    # Show detailed score breakdown
                    print("   📊 SCORE BREAKDOWN")
                    print("   ─────────────────")
                    base_score = _get_base_score_for_strategy(strategy_name)
                    modifier_score = score - base_score
                    print(f"   Base Score: {base_score:.1f}")
                    print(f"   Modifiers: {modifier_score:+.1f}")
                    print(f"   Final Score: {score:.1f}")

                    # Show modifier details
                    print("\n   🔧 MODIFIER DETAILS")
                    print("   ──────────────────")
                    _show_modifier_details(strategy_name, brush_string, matched_data)

                    if matched_data:
                        # Only show component details for split strategies
                        # that actually have components
                        if strategy_name in [
                            "automated_split",
                            "full_input_component_matching",
                            "known_split",
                        ]:
                            print("\n   🧩 COMPONENT DETAILS")
                            print("   ───────────────────")

                            # Show handle component if present
                            if "handle" in matched_data and matched_data["handle"]:
                                handle = matched_data["handle"]
                                handle_score = handle.get("score", 0.0)
                                print("   🖐️  Handle Component")
                                print(f"        Score: {handle_score:.1f}")
                                print("        Breakdown:")
                                _show_component_modifier_details("handle", brush_string, handle)

                                # Show handle metadata
                                if handle.get("brand") or handle.get("model"):
                                    print("        Metadata:")
                                    if handle.get("brand"):
                                        print(f"        • brand: {handle['brand']}")
                                    if handle.get("model"):
                                        print(f"        • model: {handle['model']}")
                                    if handle.get("source_text"):
                                        print(f'        • source: "{handle["source_text"]}"')

                            # Show knot component if present
                            if "knot" in matched_data and matched_data["knot"]:
                                knot = matched_data["knot"]
                                knot_score = knot.get("score", 0.0)
                                print("\n   🧶 Knot Component")
                                print(f"        Score: {knot_score:.1f}")
                                print("        Breakdown:")
                                _show_component_modifier_details("knot", brush_string, knot)

                                # Show knot metadata
                                if knot.get("brand") or knot.get("model") or knot.get("fiber"):
                                    print("        Metadata:")
                                    if knot.get("brand"):
                                        print(f"        • brand: {knot['brand']}")
                                    if knot.get("model"):
                                        print(f"        • model: {knot['model']}")
                                    if knot.get("fiber"):
                                        print(f"        • fiber: {knot['fiber']}")
                                    if knot.get("source_text"):
                                        print(f'        • source: "{knot["source_text"]}"')

                        # Show split information if this is a split strategy
                        if strategy_name in ["automated_split", "full_input_component_matching"]:
                            print("\n   🔪 Split Information")
                            print("   ──────────────────")
                            if "handle" in matched_data and matched_data["handle"]:
                                handle_text = matched_data["handle"].get("source_text", "unknown")
                                print(f'   Handle Text: "{handle_text}"')
                            if "knot" in matched_data and matched_data["knot"]:
                                knot_text = matched_data["knot"].get("source_text", "unknown")
                                print(f'   Knot Text: "{knot_text}"')
                            if "split_priority" in matched_data:
                                print(f"   Split Priority: {matched_data['split_priority']}")
                            if "delimiter_priority" in matched_data:
                                print(
                                    f"   Delimiter Priority: {matched_data['delimiter_priority']}"
                                )
                        else:
                            # For complete brush strategies, show basic brush information
                            print("\n   🪮 BRUSH INFORMATION")
                            print("   ───────────────────")
                            if "brand" in matched_data and matched_data["brand"]:
                                print(f"   🏷️  Brand: {matched_data['brand']}")
                            if "model" in matched_data and matched_data["model"]:
                                print(f"   🏷️  Model: {matched_data['model']}")
                            if "fiber" in matched_data and matched_data["fiber"]:
                                print(f"   🧶 Fiber: {matched_data['fiber']}")
                            if "knot_size_mm" in matched_data and matched_data["knot_size_mm"]:
                                print(f"   📏 Size: {matched_data['knot_size_mm']}mm")
                            if "source_text" in matched_data and matched_data["source_text"]:
                                print(f'   📝 Source: "{matched_data["source_text"]}"')

                        # Show strategy-specific fields (only if they have meaningful values)
                        strategy_fields = []
                        if "user_intent" in matched_data and matched_data["user_intent"]:
                            strategy_fields.append(("User Intent", matched_data["user_intent"]))
                        if (
                            "_matched_by_strategy" in matched_data
                            and matched_data["_matched_by_strategy"]
                        ):
                            strategy_fields.append(
                                ("Matched By Strategy", matched_data["_matched_by_strategy"])
                            )
                        if "_pattern_used" in matched_data and matched_data["_pattern_used"]:
                            strategy_fields.append(("Pattern Used", matched_data["_pattern_used"]))

                        if strategy_fields:
                            print("        Strategy Fields:")
                            for key, value in strategy_fields:
                                print(f"        • {key}: {value}")

                        # Show other relevant fields (only if they have meaningful values)
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
                            "strategy",
                            "score",
                            "split_priority",
                            "delimiter_priority",
                            "handle_text",
                            "knot_text",
                            "handle_maker",  # These are shown in split info section
                        ]
                        other_fields = []
                        for key, value in matched_data.items():
                            if (
                                key not in excluded_keys
                                and value
                                and value != "Unknown"
                                and value != "None"
                                and not key.startswith("_")
                            ):
                                other_fields.append((key, value))

                        if other_fields:
                            print("        Other Fields:")
                            for key, value in other_fields:
                                print(f"        • {key.replace('_', ' ').title()}: {value}")
                    else:
                        print("   ❌ No match data")

                print("\n" + "=" * 60)
                print("🏆 WINNER: Best Match (Highest Score)")
                print("=" * 40)

                # Filter out results with no valid matches, just like the pipeline does
                valid_results = [
                    r
                    for r in sorted_strategies
                    if getattr(r, "matched", None)
                    and (
                        getattr(r, "matched", {}).get("brand")
                        or getattr(r, "matched", {}).get("handle")
                        or getattr(r, "matched", {}).get("knot")
                    )
                ]

                if valid_results:
                    # Use the best valid result
                    best_valid_result = valid_results[0]  # Already sorted by score
                    strategy = getattr(best_valid_result, "matched", {}).get("strategy", "Unknown")
                    score = getattr(best_valid_result, "matched", {}).get("score", "N/A")
                    print(f"  🥇 Strategy: {strategy}")
                    print(f"  💯 Score: {score}")
                    print(f"  🎯 Match Type: {getattr(best_valid_result, 'match_type', 'Unknown')}")
                    print(f"  🔍 Pattern: {getattr(best_valid_result, 'pattern', 'Unknown')}")

                    # Show detailed score breakdown for winner
                    print("  📊 SCORE BREAKDOWN")
                    print("  ─────────────────")
                    base_score = _get_base_score_for_strategy(strategy)
                    modifier_score = float(score) - base_score if score != "N/A" else 0
                    print(f"  Base Score: {base_score:.1f}")
                    print(f"  Modifiers: {modifier_score:+.1f}")
                    print(f"  Final Score: {score}")

                    # Show modifier details for winner
                    print("\n  🔧 MODIFIER DETAILS")
                    print("  ──────────────────")
                    _show_modifier_details(strategy, brush_string, best_valid_result)

                    print("\n  🧩 FINAL RESULT")
                    print("  ────────────────")

                    # Show complete brush structure clearly
                    print("     🪮 BRUSH COMPONENTS")

                    # Top-level brush info
                    print("       🏷️  TOP-LEVEL")
                    brand = getattr(best_valid_result, "matched", {}).get("brand", "None")
                    print(f"         • Brand: {brand}")
                    model = getattr(best_valid_result, "matched", {}).get("model", "None")
                    print(f"         • Model: {model}")
                    fiber = getattr(best_valid_result, "matched", {}).get("fiber", "None")
                    print(f"         • Fiber: {fiber}")
                    size = getattr(best_valid_result, "matched", {}).get("knot_size_mm", "None")
                    print(f"         • Size: {size}mm")

                    # Handle component
                    print("       🖐️  HANDLE")
                    if (
                        "handle" in getattr(best_valid_result, "matched", {})
                        and getattr(best_valid_result, "matched", {})["handle"]
                    ):
                        handle = getattr(best_valid_result, "matched", {})["handle"]
                        print(f"         • Brand: {handle.get('brand', 'None')}")
                        print(f"         • Model: {handle.get('model', 'None')}")
                        print(f"         • Material: {handle.get('material', 'None')}")
                    else:
                        print("         (No handle data)")

                    # Knot component
                    print("       🧶 KNOT")
                    if (
                        "knot" in getattr(best_valid_result, "matched", {})
                        and getattr(best_valid_result, "matched", {})["knot"]
                    ):
                        knot = getattr(best_valid_result, "matched", {})["knot"]
                        print(f"         • Brand: {knot.get('brand', 'None')}")
                        print(f"         • Model: {knot.get('model', 'None')}")
                        print(f"         • Fiber: {knot.get('fiber', 'None')}")
                        print(f"         • Size: {knot.get('knot_size_mm', 'None')}mm")
                    else:
                        print("         (No knot data)")

                    # Show other relevant fields
                    other_fields = []
                    for key, value in getattr(best_valid_result, "matched", {}).items():
                        excluded_keys = [
                            "brand",
                            "model",
                            "fiber",
                            "knot_size_mm",
                            "handle",
                            "knot",
                            "strategy",
                            "score",
                        ]
                        if key not in excluded_keys:
                            if value and value != "Unknown":
                                other_fields.append(f"{key.replace('_', ' ').title()}: {value}")

                    if other_fields:
                        print("       🔧 OTHER FIELDS:")
                        for field in other_fields:
                            print(f"         {field}")
                else:
                    print("  ❌ No valid results found (all strategies returned empty matches)")
                    print("  📊 Raw scores (including invalid results):")
                    for i, strategy_result in enumerate(sorted_strategies[:3], 1):  # Show top 3
                        strategy_name = getattr(strategy_result, "strategy", "Unknown")
                        score = getattr(strategy_result, "score", 0)
                        print(f"    #{i}: {strategy_name} - Score: {score} (No valid match)")

            else:
                print("  ❌ No matches found or no strategy results available")

        except Exception as e:
            print(f"  ❌ Error with scoring matcher: {e}")
            print("  💥 FAILING FAST - No fallback available")
            print("  🔍 This error needs to be fixed in the scoring system")
            import traceback

            print("  📋 Full error traceback:")
            traceback.print_exc()
            return

    # Test enrich phase
    print("\n" + "=" * 60)
    print("🔧 Testing enrich phase:")
    print("=" * 30)

    # Get the result from the scoring matcher
    try:
        scoring_matcher = BrushMatcher()

        # If bypassing correct_matches, temporarily clear them
        original_correct_matches = None
        if bypass_correct_matches:
            original_correct_matches = scoring_matcher.correct_matches_matcher.correct_matches
            scoring_matcher.correct_matches_matcher.correct_matches = {}

        result = scoring_matcher.match(brush_string)

        # Restore correct_matches if we bypassed them
        if bypass_correct_matches and original_correct_matches is not None:
            scoring_matcher.correct_matches_matcher.correct_matches = original_correct_matches

    except Exception as e:
        print(f"  ❌ Error with scoring matcher: {e}")
        print("  💥 FAILING FAST - Cannot test enrichment")
        return

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
    config = BrushScoringConfig()
    return config.get_base_strategy_score(strategy_name)


def _show_modifier_details(strategy_name: str, input_text: str, result):
    """Show detailed breakdown of modifiers using actual ScoringEngine."""
    try:
        # Import the actual ScoringEngine and config
        config = BrushScoringConfig()
        engine = ScoringEngine(config)

        # The result parameter can be either:
        # 1. A MatchResult object (from winner section)
        # 2. A dict (from strategy results section)
        # We need to handle both cases

        # Handle both MatchResult and dict cases
        if hasattr(result, "matched"):
            # This is a MatchResult object - use it directly
            result_obj = result
        else:
            # This is a dict - create a minimal result object
            from unittest.mock import Mock

            result_obj = Mock()
            result_obj.matched = result
            result_obj.strategy = strategy_name

        # Get the actual modifier calculation from the engine
        modifier_score = engine._calculate_modifiers(result_obj, input_text, strategy_name)

        # Show the real modifier breakdown
        print(f"     Real Modifier Total: {modifier_score:+.1f}")

        # Get individual modifier details from the engine
        modifier_names = config.get_all_modifier_names(strategy_name)
        for modifier_name in modifier_names:
            modifier_weight = config.get_strategy_modifier(strategy_name, modifier_name)
            modifier_function = getattr(engine, f"_modifier_{modifier_name}", None)
            if modifier_function and callable(modifier_function):
                # For manufacturer modifiers, we need to provide cached_results context
                # We need to get the actual cached results from the scoring process
                # Since this is a standalone analysis tool, we need to recreate the
                # scoring process to get the real cached results
                if strategy_name in ["handle_only", "knot_only"]:
                    # Since we're removing the legacy system, we'll use a simplified approach
                    # Create minimal cached results for modifier functions to work
                    engine.cached_results = {"unified_result": None}

                try:
                    modifier_value = modifier_function(input_text, result_obj, strategy_name)
                    # Ensure modifier_value is numeric for multiplication
                    if isinstance(modifier_value, (int, float)):
                        numeric_value: float = float(modifier_value)
                    elif modifier_value is None:
                        numeric_value = 0.0
                    else:
                        # Try to convert to float, default to 0.0 if conversion fails
                        try:
                            numeric_value = float(modifier_value)  # type: ignore
                        except (ValueError, TypeError):
                            numeric_value = 0.0
                    total_effect = numeric_value * modifier_weight

                    # Show just the final modifier value (clean and simple)
                    if total_effect > 0:
                        print(f"       {modifier_name}: +{total_effect:.1f}")
                    elif total_effect < 0:
                        print(f"       {modifier_name}: {total_effect:.1f}")
                    else:
                        print(f"       {modifier_name}: +0.0")
                except Exception as e:
                    print(f"       {modifier_name}: Error calculating modifier: {e}")

    except Exception as e:
        # Fallback to simplified calculation if engine fails
        print(f"     ⚠️  Using simplified modifier calculation (engine error: {e})")
        _show_simplified_modifier_details(strategy_name, input_text, result.matched)


def _show_component_modifier_details(component_type: str, input_text: str, component_data: dict):
    """Show detailed breakdown of modifiers for handle/knot components."""
    _show_simplified_component_modifier_details(component_type, input_text, component_data)


def _show_simplified_component_modifier_details(
    component_type: str, input_text: str, component_data: dict
):
    """Show simplified modifier details for handle/knot components when engine fails."""
    # Load actual config values instead of using hardcoded ones
    from sotd.match.brush.config import BrushScoringConfig

    config = BrushScoringConfig()
    if component_type == "knot":
        print("           🧶 Analyzing KNOT component...")
        # Use actual config values for knot_matching
        knot_config = config.weights.get("strategy_modifiers", {}).get("knot_matching", {})

        # fiber_match: 5.0
        if component_data.get("fiber"):
            print(f"              fiber_match: +{knot_config.get('fiber_match', 0.0):.1f}")
        else:
            print("              fiber_match: +0.0")

        # size_match: 5.0
        if component_data.get("knot_size_mm"):
            print(f"              size_match: +{knot_config.get('size_match', 0.0):.1f}")
        else:
            print("              size_match: +0.0")

        # brand_match: 5.0
        if component_data.get("brand"):
            print(f"              brand_match: +{knot_config.get('brand_match', 0.0):.1f}")
        else:
            print("              brand_match: +0.0")

        # knot_indicators: 10.0
        knot_indicators = [
            "boar",
            "badger",
            "synthetic",
            "syn",
            "nylon",
            "plissoft",
            "tuxedo",
            "cashmere",
            "mixed",
        ]
        if any(indicator in input_text.lower() for indicator in knot_indicators):
            print(f"              knot_indicators: +{knot_config.get('knot_indicators', 0.0):.1f}")
        else:
            print("              knot_indicators: +0.0")

        # priority_score: 5.0
        priority = component_data.get("priority", 0)
        if priority is not None:
            print(f"              priority_score: +{knot_config.get('priority_score', 0.0):.1f}")
        else:
            print("              priority_score: +0.0")

    elif component_type == "handle":
        print("           🖐️  Analyzing HANDLE component...")
        # Use actual config values for handle_matching
        handle_config = config.weights.get("strategy_modifiers", {}).get("handle_matching", {})

        # brand_match: 5.0
        if component_data.get("brand"):
            print(f"              brand_match: +{handle_config.get('brand_match', 0.0):.1f}")
        else:
            print("              brand_match: +0.0")

        # Check for handle indicators in text
        handle_indicators = ["wood", "resin", "metal", "turned", "custom", "artisan", "stock"]
        if any(indicator in input_text.lower() for indicator in handle_indicators):
            print(
                f"              handle_indicators: "
                f"+{handle_config.get('handle_indicators', 0.0):.1f}"
            )
        else:
            print("              handle_indicators: +0.0")

        # priority_score: 0.0 (from config)
        priority = component_data.get("priority", 0)
        if priority is not None:
            print(f"              priority_score: +{handle_config.get('priority_score', 0.0):.1f}")
        else:
            print("              priority_score: +0.0")


def _get_modifier_weights_for_strategy(strategy_name: str) -> dict:
    """Get modifier weights for a strategy from the configuration."""
    # Load configuration from the actual YAML file
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


def _show_simplified_modifier_details(strategy_name: str, input_text: str, matched_data: dict):
    """Fallback function for simplified modifier calculation when engine fails."""
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
    parser.add_argument(
        "--bypass-correct-matches",
        action="store_true",
        help="Bypass correct_matches.yaml lookup to test raw matchers only",
    )

    args = parser.parse_args()
    analyze_brush_matching(
        args.brush_string, args.debug, not args.legacy, args.bypass_correct_matches
    )


if __name__ == "__main__":
    main()
