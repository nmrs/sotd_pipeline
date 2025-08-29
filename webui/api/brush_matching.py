"""
API endpoint for brush matching analyzer.

This endpoint provides a web interface to the brush matching analysis tool,
allowing users to test brush strings and see detailed scoring results.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Import SOTD modules - will be handled in the function

router = APIRouter(prefix="/api/brush-matching", tags=["brush-matching"])


class BrushAnalysisRequest(BaseModel):
    brushString: str


class BrushMatchResult(BaseModel):
    strategy: str
    score: float
    matchType: str
    pattern: str
    scoreBreakdown: Dict[str, Any]
    matchedData: Dict[str, Any]


class BrushAnalysisResponse(BaseModel):
    results: List[BrushMatchResult]
    winner: BrushMatchResult
    enrichedData: Dict[str, Any] = {}


def _get_modifier_description(modifier_name: str, modifier_value: float, brush_string: str) -> str:
    """
    Helper function to generate a user-friendly description for a modifier.
    """
    if modifier_name == "knot_indicators":
        if modifier_value > 0:
            # Look for fiber words in the input
            fiber_words = [
                "badger",
                "boar",
                "synthetic",
                "syn",
                "nylon",
                "plissoft",
                "tuxedo",
                "cashmere",
                "mixed",
                "timberwolf",
            ]
            found_words = [word for word in fiber_words if word.lower() in brush_string.lower()]
            if found_words:
                return f"Fiber type detected: {', '.join(found_words)}"
            else:
                return "Knot indicators detected"
        return "Knot indicators"

    elif modifier_name == "handle_indicators":
        if modifier_value > 0:
            # Look for handle-related words
            handle_words = [
                "handle",
                "wood",
                "resin",
                "acrylic",
                "metal",
                "brass",
                "aluminum",
                "steel",
                "titanium",
                "ebonite",
                "ivory",
                "horn",
                "bone",
                "stone",
                "marble",
                "granite",
            ]
            found_words = [word for word in handle_words if word.lower() in brush_string.lower()]
            if found_words:
                return f"Handle material detected: {', '.join(found_words)}"
            else:
                return "Handle indicators detected"
        return "Handle indicators"

    elif modifier_name == "fiber_mismatch":
        return "Fiber type mismatch between input and catalog"

    elif modifier_name == "size_specification":
        if modifier_value > 0:
            # Look for size specifications
            import re

            size_patterns = [r"\b\d+mm\b", r"\b\d+\s*mm\b", r"\b\d+x\d+\b", r"\b\d+\s*x\s*\d+\b"]
            for pattern in size_patterns:
                match = re.search(pattern, brush_string.lower())
                if match:
                    return f"Size specification detected: {match.group()}"
            return "Size specification detected"
        return "Size specification"

    elif modifier_name == "multiple_brands":
        return "Multiple brands detected"

    elif modifier_name == "high_confidence":
        return "High confidence delimiter used"

    elif modifier_name == "delimiter_confidence":
        return "High confidence delimiter detected"

    elif modifier_name == "dual_component":
        return "Both handle and knot components matched"

    elif modifier_name == "handle_brand_without_knot_brand":
        return "Handle brand detected without knot brand"

    elif modifier_name == "knot_brand_without_handle_brand":
        return "Knot brand detected without handle brand"

    else:
        return f"Modifier: {modifier_name}"


@router.post("/analyze", response_model=BrushAnalysisResponse)
async def analyze_brush(request: BrushAnalysisRequest) -> BrushAnalysisResponse:
    """
    Analyze a brush string and return detailed scoring results.

    Args:
        request: Contains the brush string to analyze

    Returns:
        Detailed analysis results including all strategies and scores
    """
    try:
        # Import SOTD modules inside the function to avoid linter issues
        import sys
        from pathlib import Path

        # Add the parent directory to Python path to import SOTD modules
        parent_dir = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(parent_dir))

        # Use the BrushMatcher for consistent analysis
        from sotd.match.brush_matcher import BrushMatcher

        # Change to the parent directory where the data files are located
        import os

        original_cwd = os.getcwd()
        os.chdir(parent_dir)

        try:
            # Use the brush matcher
            matcher = BrushMatcher()
            analysis_result = matcher.match(request.brushString)

            # Convert to expected format
            if analysis_result and hasattr(analysis_result, "all_strategies"):
                # The new matcher returns a MatchResult with all_strategies
                analysis_result = {
                    "all_strategies": analysis_result.all_strategies,
                    "enriched_data": analysis_result.matched if analysis_result.matched else {},
                }
            else:
                # Fallback if no results
                analysis_result = {"all_strategies": [], "enriched_data": {}}
        finally:
            # Restore original working directory
            os.chdir(original_cwd)

        # Check for errors
        if "error" in analysis_result:
            raise HTTPException(
                status_code=500, detail=f"Analysis failed: {analysis_result['error']}"
            )

        # Format results for the API response
        formatted_results = []

        # Debug logging
        print(f"DEBUG: Processing {len(analysis_result.get('all_strategies', []))} strategies")
        for i, strategy_result in enumerate(analysis_result.get("all_strategies", [])):
            print(f"DEBUG: Strategy {i + 1}: {strategy_result.strategy}")

        # Process all strategy results
        for strategy_result in analysis_result.get("all_strategies", []):
            # The new matcher now provides full MatchResult objects with complete data
            try:
                # Extract data from the MatchResult object
                strategy_name = strategy_result.strategy or "unknown"
                match_type = strategy_result.match_type or "unknown"
                pattern = strategy_result.pattern or "unknown"
                matched_data = strategy_result.matched or {}

                print(f"DEBUG: Processing strategy: {strategy_name}")

                # Get detailed scoring breakdown using the ScoringEngine
                from sotd.match.brush_scoring_components.scoring_engine import ScoringEngine
                from sotd.match.brush_scoring_config import BrushScoringConfig

                config_path = (
                    Path(__file__).parent.parent.parent / "data" / "brush_scoring_config.yaml"
                )
                config = BrushScoringConfig(config_path=config_path)
                engine = ScoringEngine(config)

                # Calculate base score and modifiers
                base_score = engine.config.get_base_strategy_score(strategy_name)
                print(f"DEBUG: Base score for {strategy_name}: {base_score}")

                modifier_score = engine._calculate_modifiers(
                    strategy_result, request.brushString, strategy_name
                )
                total_score = base_score + modifier_score
                print(f"DEBUG: Total score for {strategy_name}: {total_score}")

                # Get modifier details
                modifier_details = []
                modifier_names = config.get_all_modifier_names(strategy_name)

                for modifier_name in modifier_names:
                    modifier_weight = config.get_strategy_modifier(strategy_name, modifier_name)
                    modifier_function = getattr(engine, f"_modifier_{modifier_name}", None)

                    if modifier_function is not None and callable(modifier_function):
                        try:
                            modifier_value = modifier_function(
                                request.brushString, strategy_result, strategy_name
                            )
                            total_effect = modifier_value * modifier_weight

                            if total_effect != 0:
                                modifier_description = _get_modifier_description(
                                    modifier_name, modifier_value, request.brushString
                                )
                                modifier_details.append(
                                    f"{modifier_description} (+{total_effect:+.0f})"
                                )
                        except Exception:
                            continue

            except Exception as e:
                # Fallback to basic scoring if detailed calculation fails
                print(
                    f"Warning: Detailed scoring failed for {strategy_result.strategy or 'unknown'}: {e}"
                )
                base_score = getattr(strategy_result, "score", 0.0)
                modifier_score = 0.0
                total_score = base_score
                modifier_details = []
                matched_data = getattr(strategy_result, "matched", {})
                strategy_name = getattr(strategy_result, "strategy", "unknown")
                match_type = getattr(strategy_result, "match_type", "unknown")
                pattern = getattr(strategy_result, "pattern", "unknown")

            formatted_result = BrushMatchResult(
                strategy=strategy_name,
                score=total_score,
                matchType=match_type,
                pattern=pattern,
                scoreBreakdown={
                    "baseScore": base_score,
                    "modifiers": modifier_score,
                    "modifierDetails": modifier_details,
                    "total": total_score,
                },
                matchedData=matched_data,
            )
            formatted_results.append(formatted_result)
            print(f"DEBUG: Added formatted result for {strategy_name}")

        print(f"DEBUG: Final formatted results count: {len(formatted_results)}")

        # If no strategies, create a basic result
        if not formatted_results:
            basic_matching = analysis_result.get("analysis_summary", {}).get("basic_matching", {})
            formatted_result = BrushMatchResult(
                strategy="basic_matcher",
                score=0.0,
                matchType=basic_matching.get("match_type", "unknown"),
                pattern=basic_matching.get("pattern", "unknown"),
                scoreBreakdown={"baseScore": 0.0, "modifiers": 0.0, "modifierDetails": []},
                matchedData=basic_matching.get("matched", {}),
            )
            formatted_results.append(formatted_result)

        # Find the winner (highest score)
        winner = max(formatted_results, key=lambda x: x.score)

        # Get enriched data
        enriched_data = analysis_result.get("enriched_data", {})

        return BrushAnalysisResponse(
            results=formatted_results, winner=winner, enrichedData=enriched_data
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "brush_matching_analyzer"}
