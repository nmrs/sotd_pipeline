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

        # Use the shared library for consistent analysis
        from sotd.match.tools.analyzers.brush_matching_analyzer_lib import analyze_brush_string

        # Change to the parent directory where the data files are located
        import os

        original_cwd = os.getcwd()
        os.chdir(parent_dir)

        try:
            # Use the shared library to get comprehensive analysis
            analysis_result = analyze_brush_string(
                request.brushString,
                debug=True,  # Enable debug output to see what's happening
                show_all_matches=True,
                bypass_correct_matches=False,
            )
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

        # Process all strategy results
        for strategy_result in analysis_result.get("all_strategies", []):
            formatted_result = BrushMatchResult(
                strategy=strategy_result.get("strategy", "unknown"),
                score=strategy_result.get("score", 0.0),
                matchType=strategy_result.get("match_type", "unknown"),
                pattern=strategy_result.get("pattern", "unknown"),
                scoreBreakdown={
                    "baseScore": strategy_result.get("base_score", 0.0),
                    "modifiers": strategy_result.get("modifier_score", 0.0),
                    "modifierDetails": [],
                    "total": strategy_result.get("score", 0.0),
                },
                matchedData=strategy_result.get("matched_data", {}),
            )
            formatted_results.append(formatted_result)

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
