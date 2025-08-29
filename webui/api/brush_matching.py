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
    bypass_correct_matches: bool = False


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
        request: Contains the brush string to analyze and bypass option

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

        # Change to the parent directory where the data files are located
        import os

        original_cwd = os.getcwd()
        os.chdir(parent_dir)

        try:
            # Use the brush matcher directly
            from sotd.match.brush_matcher import BrushMatcher

            matcher = BrushMatcher()

            def transform_brush_data(flat_data: dict) -> dict:
                """Transform flat brush data into nested handle/knot structure for React component."""
                if not flat_data:
                    return {}

                # Check if this is an automated_split result with handle/knot sections
                if "handle" in flat_data and "knot" in flat_data:
                    # This is already in the correct nested structure
                    return {
                        "brand": flat_data.get("brand"),
                        "model": flat_data.get("model"),
                        "handle": {
                            "brand": flat_data["handle"].get("brand"),
                            "model": flat_data["handle"].get("model"),
                            "source_text": flat_data["handle"].get("source_text"),
                        },
                        "knot": {
                            "brand": flat_data["knot"].get("brand"),
                            "model": flat_data["knot"].get("model"),
                            "fiber": flat_data["knot"].get("fiber"),
                            "knot_size_mm": flat_data["knot"].get("knot_size_mm"),
                            "source_text": flat_data["knot"].get("source_text"),
                        },
                    }

                # Extract handle information - use handle_maker as brand, try to extract handle model
                handle_brand = flat_data.get("handle_maker")
                handle_model = flat_data.get("handle_model")

                # Try to extract handle model from source_text if available
                source_text = flat_data.get("source_text", "")
                if not handle_model and source_text and "/" in source_text:
                    # Extract handle part before "/"
                    handle_part = source_text.split("/")[0].strip()
                    handle_model = handle_part if handle_part else None

                handle_data = {
                    "brand": handle_brand,
                    "model": handle_model,
                    "source_text": (
                        flat_data.get("_original_handle_text")
                        or (source_text.split("/")[0].strip() if "/" in source_text else "")
                    ),
                }

                # Extract knot information - use fiber and knot_size_mm from flat data
                knot_brand = flat_data.get("knot_brand") or flat_data.get("brand")
                knot_model = flat_data.get("knot_model") or flat_data.get("model")

                # Try to extract knot info from source_text if available
                knot_source_text = ""
                if source_text and "*" in source_text:
                    # Extract part after "*" as knot info
                    knot_part = source_text.split("*")[-1].strip()
                    knot_source_text = knot_part if knot_part else ""

                knot_data = {
                    "brand": knot_brand,
                    "model": knot_model,
                    "fiber": flat_data.get("fiber"),
                    "knot_size_mm": flat_data.get("knot_size_mm"),
                    "source_text": (flat_data.get("_original_knot_text") or knot_source_text),
                }

                # Create nested structure
                return {
                    "brand": flat_data.get("brand"),
                    "model": flat_data.get("model"),
                    "handle": handle_data,
                    "knot": knot_data,
                }

            if request.bypass_correct_matches:
                # If bypassing, run all strategies EXCEPT CorrectMatchesStrategy
                # Filter out CorrectMatchesStrategy to avoid running correct matches logic
                filtered_strategies = [
                    s
                    for s in matcher.strategy_orchestrator.strategies
                    if s.__class__.__name__ != "CorrectMatchesStrategy"
                ]

                # Create a temporary orchestrator with filtered strategies
                from sotd.match.brush_scoring_components.strategy_orchestrator import (
                    StrategyOrchestrator,
                )

                temp_orchestrator = StrategyOrchestrator(filtered_strategies)

                strategy_results = temp_orchestrator.run_all_strategies(request.brushString)

                # Convert to expected format
                analysis_result = {
                    "all_strategies": strategy_results,
                    "enriched_data": {},
                }
            else:
                # Use normal matching (will return early if correct match found)
                result = matcher.match(request.brushString)

                # Convert to expected format
                if result and hasattr(result, "all_strategies"):
                    analysis_result = {
                        "all_strategies": result.all_strategies,
                        "enriched_data": result.matched if result.matched else {},
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

        # Get strategies from analysis result
        strategies = analysis_result.get("all_strategies", []) or []

        # Process all strategy results
        for strategy_result in strategies:
            # The new matcher now provides full MatchResult objects with complete data
            try:
                # Extract data from the MatchResult object
                strategy_name = strategy_result.strategy or "unknown"
                match_type = strategy_result.match_type or "unknown"
                pattern = strategy_result.pattern or "unknown"
                matched_data = strategy_result.matched or {}

                # Transform flat brush data to nested structure for React component
                transformed_matched_data = transform_brush_data(matched_data)

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

                modifier_score = engine._calculate_modifiers(
                    strategy_result, request.brushString, strategy_name
                )
                total_score = base_score + modifier_score

                # Get modifier details
                modifier_details = []
                modifier_names = config.get_all_modifier_names(strategy_name)

                for modifier_name in modifier_names:
                    modifier_weight = config.get_strategy_modifier(strategy_name, modifier_name)
                    if modifier_weight:
                        modifier_details.append(
                            {
                                "name": modifier_name,
                                "weight": modifier_weight,
                                "description": f"{modifier_name} bonus",
                            }
                        )

                # Create the formatted result
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
                    matchedData=transformed_matched_data,
                )

                formatted_results.append(formatted_result)

            except Exception as e:
                # Add a fallback result for failed strategies
                fallback_result = BrushMatchResult(
                    strategy="error",
                    score=0.0,
                    matchType="error",
                    pattern="error",
                    scoreBreakdown={
                        "baseScore": 0.0,
                        "modifiers": 0.0,
                        "modifierDetails": [],
                        "total": 0.0,
                    },
                    matchedData={"error": str(e)},
                )
                formatted_results.append(fallback_result)

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
