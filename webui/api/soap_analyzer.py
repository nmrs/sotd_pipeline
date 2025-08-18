from fastapi import APIRouter, Query, HTTPException
from pathlib import Path
from typing import List, Optional
import json
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/soap-analyzer", tags=["soap-analyzer"])


# Pydantic models for response
class SoapDuplicateResult:
    def __init__(self, text1: str, text2: str, similarity: float, count: int):
        self.text1 = text1
        self.text2 = text2
        self.similarity = similarity
        self.count = count


class SoapPatternSuggestion:
    def __init__(self, pattern: str, count: int, examples: List[str]):
        self.pattern = pattern
        self.count = count
        self.examples = examples


def is_valid_month(month: str) -> bool:
    """Validate month format (YYYY-MM)"""
    try:
        if len(month) != 7 or month[4] != "-":
            return False
        year = int(month[:4])
        month_num = int(month[5:])
        return 2020 <= year <= 2030 and 1 <= month_num <= 12
    except ValueError:
        return False


@router.get("/duplicates")
async def get_soap_duplicates(
    months: str = Query(..., description="Comma-separated months (e.g., '2025-05,2025-06')"),
    similarity_threshold: float = Query(
        0.8, ge=0.0, le=1.0, description="Similarity threshold for duplicates"
    ),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Maximum number of results"),
):
    """Get potential duplicate soap matches"""
    try:
        # Parse months
        month_list = [m.strip() for m in months.split(",")]
        for month in month_list:
            if not is_valid_month(month):
                raise HTTPException(status_code=400, detail=f"Invalid month format: {month}")

        logger.info(f"🔍 Analyzing soap duplicates for months: {month_list}")

        # Load data from all specified months
        all_matches = []
        data_dir = Path(__file__).parent.parent.parent / "data" / "matched"

        for month in month_list:
            month_file = data_dir / f"{month}.json"
            if not month_file.exists():
                logger.warning(f"No match data found for month: {month}")
                continue

            try:
                with open(month_file, "r") as f:
                    match_data = json.load(f)

                # Extract soap data from the data array
                if "data" in match_data and isinstance(match_data["data"], list):
                    for record in match_data["data"]:
                        if "soap" in record and record["soap"]:
                            all_matches.append(record["soap"])

            except Exception as e:
                logger.error(f"Error loading month {month}: {e}")
                continue

        if not all_matches:
            return {"message": "No soap matches found for the specified months", "results": []}

        logger.info(f"Processing {len(all_matches)} total soap matches")

        # Analyze duplicates
        results = analyze_soap_duplicates_web(all_matches, similarity_threshold, limit)

        return {
            "message": f"Found {len(results)} potential duplicates",
            "results": results,
            "total_matches": len(all_matches),
            "months_processed": month_list,
        }

    except Exception as e:
        logger.error(f"Error in soap duplicates analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pattern-suggestions")
async def get_soap_pattern_suggestions(
    months: str = Query(..., description="Comma-separated months (e.g., '2025-05,2025-06')"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Maximum number of results"),
):
    """Get soap pattern suggestions"""
    try:
        # Parse months
        month_list = [m.strip() for m in months.split(",")]
        for month in month_list:
            if not is_valid_month(month):
                raise HTTPException(status_code=400, detail=f"Invalid month format: {month}")

        logger.info(f"🔍 Analyzing soap patterns for months: {month_list}")

        # Load data from all specified months
        all_matches = []
        data_dir = Path(__file__).parent.parent.parent / "data" / "matched"

        for month in month_list:
            month_file = data_dir / f"{month}.json"
            if not month_file.exists():
                logger.warning(f"No match data found for month: {month}")
                continue

            try:
                with open(month_file, "r") as f:
                    match_data = json.load(f)

                # Extract soap data from the data array
                if "data" in match_data and isinstance(match_data["data"], list):
                    for record in match_data["data"]:
                        if "soap" in record and record["soap"]:
                            all_matches.append(record["soap"])

            except Exception as e:
                logger.error(f"Error loading month {month}: {e}")
                continue

        if not all_matches:
            return {"message": "No soap matches found for the specified months", "results": []}

        logger.info(f"Processing {len(all_matches)} total soap matches for patterns")

        # Analyze patterns
        results = analyze_soap_patterns_web(all_matches, limit)

        return {
            "message": f"Found {len(results)} pattern suggestions",
            "results": results,
            "total_matches": len(all_matches),
            "months_processed": month_list,
        }

    except Exception as e:
        logger.error(f"Error in soap pattern analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def analyze_soap_duplicates_web(
    matches: List[dict], similarity_threshold: float = 0.9, limit: Optional[int] = None
) -> List[dict]:
    """Analyze soap matches for potential duplicates (web-optimized version)"""
    from difflib import SequenceMatcher

    # Group by maker first, then by scent for efficiency
    maker_groups = defaultdict(list)
    for match in matches:
        # Handle both direct fields and nested matched fields
        if "matched" in match and match["matched"]:
            maker = match["matched"].get("maker", "").lower()
            scent = match["matched"].get("scent", "").lower()
        else:
            maker = match.get("maker", "").lower()
            scent = match.get("scent", "").lower()

        if maker and scent:  # Only add if both fields exist
            maker_groups[maker].append(scent)

    results = []
    shown = 0
    limit_reached = False

    # Compare within maker groups
    for maker1, scents1 in maker_groups.items():
        if limit_reached:
            break

        for maker2, scents2 in maker_groups.items():
            if limit_reached:
                break

            # Skip same maker comparisons
            if maker1 == maker2:
                continue

            # Calculate maker similarity once
            maker_similarity = SequenceMatcher(None, maker1, maker2).ratio()

            # Only proceed if makers are similar enough
            if maker_similarity < similarity_threshold * 0.8:
                continue

            # Compare scents within similar makers
            for scent1 in scents1:
                if limit_reached:
                    break

                for scent2 in scents2:
                    if limit_reached:
                        break

                    # Calculate overall similarity
                    scent_similarity = SequenceMatcher(None, scent1, scent2).ratio()
                    overall_similarity = (maker_similarity + scent_similarity) / 2

                    if overall_similarity >= similarity_threshold:
                        # Count occurrences
                        count1 = sum(
                            1
                            for m in matches
                            if (
                                (
                                    m.get("matched")
                                    and m["matched"].get("maker", "").lower() == maker1
                                    and m["matched"].get("scent", "").lower() == scent1
                                )
                                or (
                                    m.get("maker", "").lower() == maker1
                                    and m.get("scent", "").lower() == scent1
                                )
                            )
                        )
                        count2 = sum(
                            1
                            for m in matches
                            if (
                                (
                                    m.get("matched")
                                    and m["matched"].get("maker", "").lower() == maker2
                                    and m["matched"].get("scent", "").lower() == scent2
                                )
                                or (
                                    m.get("maker", "").lower() == maker2
                                    and m.get("scent", "").lower() == scent2
                                )
                            )
                        )
                        total_count = count1 + count2

                        result = {
                            "text1": f"{maker1.title()} {scent1.title()}",
                            "text2": f"{maker2.title()} {scent2.title()}",
                            "similarity": round(overall_similarity, 3),
                            "count": total_count,
                            "maker1": maker1.title(),
                            "scent1": scent1.title(),
                            "maker2": maker2.title(),
                            "scent2": scent2.title(),
                        }

                        results.append(result)
                        shown += 1

                        if limit is not None and shown >= limit:
                            limit_reached = True
                            break

    # Sort by similarity (highest first) and count
    results.sort(key=lambda x: (x["similarity"], x["count"]), reverse=True)

    return results


def analyze_soap_patterns_web(matches: List[dict], limit: Optional[int] = None) -> List[dict]:
    """Analyze soap patterns for suggestions (web-optimized version)"""
    # Count patterns
    pattern_counts = defaultdict(int)
    pattern_examples = defaultdict(list)

    for match in matches:
        # Handle both direct fields and nested matched fields
        if "matched" in match and match["matched"]:
            maker = match["matched"].get("maker", "").lower()
            scent = match["matched"].get("scent", "").lower()
        else:
            maker = match.get("maker", "").lower()
            scent = match.get("scent", "").lower()

        if maker and scent:
            pattern = f"{maker} {scent}"
            pattern_counts[pattern] += 1

            # Keep up to 3 examples
            if len(pattern_examples[pattern]) < 3:
                original = match.get("original", "")
                if original:
                    pattern_examples[pattern].append(original)

    # Convert to results
    results = []
    for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
        if limit and len(results) >= limit:
            break

        result = {
            "pattern": pattern.title(),
            "count": count,
            "examples": pattern_examples[pattern][:3],
        }
        results.append(result)

    return results
