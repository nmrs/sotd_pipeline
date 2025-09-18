import json
import logging
import os
from collections import defaultdict
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/soaps", tags=["soaps"])


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
    limit: Optional[int] = Query(None, ge=1, description="Maximum number of results"),
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
        # Allow override of data directory via environment variable for testing
        sotd_data_dir = os.environ.get("SOTD_DATA_DIR")
        if sotd_data_dir:
            data_dir = Path(sotd_data_dir) / "data" / "matched"
        else:
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
    limit: Optional[int] = Query(None, ge=1, description="Maximum number of results"),
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
        # Allow override of data directory via environment variable for testing
        sotd_data_dir = os.environ.get("SOTD_DATA_DIR")
        if sotd_data_dir:
            data_dir = Path(sotd_data_dir) / "data" / "matched"
        else:
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


@router.get("/neighbor-similarity")
async def get_soap_neighbor_similarity(
    months: str = Query("", description="Comma-separated months (e.g., '2025-05,2025-06')"),
    mode: str = Query(..., description="Analysis mode: brands, brand_scent, or scents"),
    similarity_threshold: float = Query(
        0.5, ge=0.0, le=1.0, description="Similarity threshold for filtering results"
    ),
    limit: Optional[int] = Query(None, ge=1, description="Maximum number of results"),
):
    """Get soap neighbor similarity analysis"""
    try:
        # Validate mode parameter
        valid_modes = ["brands", "brand_scent", "scents"]
        if mode not in valid_modes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid mode: {mode}. Must be one of: {', '.join(valid_modes)}",
            )

        # Parse months
        month_list = [m.strip() for m in months.split(",") if m.strip()]

        # Handle empty months gracefully
        if not month_list:
            return {
                "message": "No months specified",
                "results": [],
                "mode": mode,
                "total_entries": 0,
                "months_processed": [],
            }

        for month in month_list:
            if not is_valid_month(month):
                raise HTTPException(status_code=400, detail=f"Invalid month format: {month}")

        logger.info(f"🔍 Analyzing soap neighbor similarity for months: {month_list}, mode: {mode}")

        # Load data from all specified months
        all_matches = []
        # Allow override of data directory via environment variable for testing
        sotd_data_dir = os.environ.get("SOTD_DATA_DIR")
        if sotd_data_dir:
            data_dir = Path(sotd_data_dir) / "data" / "matched"
        else:
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
                            # Add the record ID as comment_id to the soap object
                            soap_data = record["soap"].copy()
                            soap_data["comment_id"] = record.get("id", record.get("comment_id", ""))
                            all_matches.append(soap_data)

            except Exception as e:
                logger.error(f"Error loading month {month}: {e}")
                continue

        if not all_matches:
            return {
                "message": "No soap matches found for the specified months",
                "results": [],
                "mode": mode,
                "total_entries": 0,
                "months_processed": month_list,
            }

        logger.info(f"Processing {len(all_matches)} total soap matches for neighbor similarity")

        # Analyze neighbor similarity
        results = analyze_soap_neighbor_similarity_web(
            all_matches, mode, similarity_threshold, limit
        )

        return {
            "message": f"Neighbor similarity analysis completed for {mode} mode",
            "mode": mode,
            "results": results,
            "total_entries": len(results),
            "months_processed": month_list,
        }

    except HTTPException:
        # Re-raise HTTPException to preserve status codes
        raise
    except Exception as e:
        logger.error(f"Error in soap neighbor similarity analysis: {e}")
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


def symmetric_similarity(text1: str, text2: str) -> float:
    """Calculate symmetric similarity between two strings.

    SequenceMatcher is inherently asymmetric, but we want symmetric similarity scores.
    This function ensures that similarity(A, B) == similarity(B, A) by taking the
    maximum of both directions.
    """
    from difflib import SequenceMatcher

    score_1_to_2 = SequenceMatcher(None, text1, text2).ratio()
    score_2_to_1 = SequenceMatcher(None, text2, text1).ratio()
    return max(score_1_to_2, score_2_to_1)


def analyze_soap_neighbor_similarity_web(
    matches: list[dict], mode: str, similarity_threshold: float = 0.5, limit: Optional[int] = None
) -> list[dict]:
    """Analyze soap matches for neighbor similarity (web-optimized version)"""
    import logging

    logger = logging.getLogger(__name__)

    # Memory optimization: Process in chunks for very large datasets
    if len(matches) > 10000:  # If more than 10k matches, log memory usage
        logger.info(f"Processing large dataset: {len(matches)} matches")

    # Extract data based on mode with comment tracking
    entries_data = []
    for match in matches:
        # Handle both direct fields and nested matched fields
        if "matched" in match and match["matched"]:
            brand = match["matched"].get("brand", "")
            scent = match["matched"].get("scent", "")
        else:
            brand = match.get("brand", "")
            scent = match.get("scent", "")

        # Mode-specific validation
        should_include = False
        if mode == "brands" and brand:
            should_include = True
        elif mode == "brand_scent" and brand:
            # Include entries with brand (even if scent is empty) - this is what we want to analyze
            should_include = True
        elif mode == "scents" and scent:
            should_include = True

        if should_include:
            comment_id = match.get("comment_id", "")
            entry = ""
            normalized = ""

            if mode == "brands":
                entry = brand
                normalized = brand.lower().strip()
            elif mode == "brand_scent":
                entry = f"{brand} - {scent}"
                brand_lower = brand.lower().strip()
                scent_lower = scent.lower().strip()
                normalized = f"{brand_lower} - {scent_lower}"
            elif mode == "scents":
                entry = scent
                normalized = scent.lower().strip()

            if entry and normalized:  # Only add if we have valid data
                entries_data.append(
                    {
                        "entry": entry,
                        "normalized": normalized,
                        "comment_id": comment_id,
                        "original_match": match,
                    }
                )

    if not entries_data:
        return []

    # Group by normalized string (case-insensitive grouping)
    grouped_entries = {}
    for entry_data in entries_data:
        normalized = entry_data["normalized"]
        if normalized not in grouped_entries:
            grouped_entries[normalized] = {
                "entry": entry_data["entry"],
                "normalized_string": normalized,
                "comment_ids": [],
                "count": 0,
                "original_matches": [],
            }

        grouped_entries[normalized]["comment_ids"].append(entry_data["comment_id"])
        grouped_entries[normalized]["count"] += 1
        grouped_entries[normalized]["original_matches"].append(entry_data["original_match"])

    # Convert to list and sort by normalized string
    unique_entries = sorted(grouped_entries.values(), key=lambda x: x["normalized_string"])

    # First pass: calculate similarities and identify entries that meet threshold
    entries_with_similarities = []

    # Memory optimization: Process in smaller chunks for very large datasets
    chunk_size = 1000
    total_entries = len(unique_entries)

    if total_entries > 5000:
        logger.info(f"Processing {total_entries} entries in chunks of {chunk_size}")

    for i in range(len(unique_entries)):
        current = unique_entries[i]

        # Calculate similarity to entry above (if exists)
        similarity_to_above = None
        if i > 0:
            above = unique_entries[i - 1]
            above_normalized = above["normalized_string"]
            current_normalized = current["normalized_string"]
            similarity_to_above = symmetric_similarity(current_normalized, above_normalized)

        # Calculate similarity to entry below (if exists)
        similarity_to_below = None
        if i < len(unique_entries) - 1:
            below = unique_entries[i + 1]
            below_normalized = below["normalized_string"]
            current_normalized = current["normalized_string"]
            similarity_to_below = symmetric_similarity(current_normalized, below_normalized)

        # Check if this entry meets the similarity threshold with either neighbor
        meets_threshold = (
            similarity_to_above is not None and similarity_to_above >= similarity_threshold
        ) or (similarity_to_below is not None and similarity_to_below >= similarity_threshold)

        if meets_threshold:
            entries_with_similarities.append(
                {
                    "entry": current["entry"],
                    "normalized_string": current["normalized_string"],
                    "comment_ids": current["comment_ids"],
                    "count": current["count"],
                    "original_matches": current["original_matches"],
                    "original_similarity_to_above": similarity_to_above,
                    "original_similarity_to_below": similarity_to_below,
                }
            )

    # Second pass: recalculate similarities for the filtered entries only
    results = []
    for i in range(len(entries_with_similarities)):
        current = entries_with_similarities[i]

        # Calculate similarity to entry above (if exists) in the filtered dataset
        similarity_to_above = None
        if i > 0:
            above = entries_with_similarities[i - 1]
            above_normalized = above["normalized_string"]
            current_normalized = current["normalized_string"]
            similarity_to_above = symmetric_similarity(current_normalized, above_normalized)

        # Calculate similarity to entry below (if exists) in the filtered dataset
        similarity_to_below = None
        if i < len(entries_with_similarities) - 1:
            below = entries_with_similarities[i + 1]
            below_normalized = below["normalized_string"]
            current_normalized = current["normalized_string"]
            similarity_to_below = symmetric_similarity(current_normalized, below_normalized)

        # Determine pattern and normalized string from the first occurrence
        first_match = current["original_matches"][0]
        pattern = first_match.get("pattern", current["entry"])
        normalized_string = first_match.get("normalized", current["normalized_string"])

        # Extract matched data from the first occurrence for consistent display
        first_match = current["original_matches"][0]
        matched_data = None
        if "matched" in first_match and first_match["matched"]:
            matched_data = {
                "brand": first_match["matched"].get("brand", ""),  # Use "brand" consistently
                "scent": first_match["matched"].get("scent", ""),
            }

        # Get next entry for display
        next_entry = None
        if i < len(entries_with_similarities) - 1:
            next_entry = entries_with_similarities[i + 1]["entry"]

        results.append(
            {
                "entry": current["entry"],
                "similarity_to_above": similarity_to_above,
                "similarity_to_next": similarity_to_below,
                "next_entry": next_entry,
                "normalized_string": normalized_string,
                "pattern": pattern,
                "comment_ids": current["comment_ids"],
                "count": current["count"],
                "matched": matched_data,
            }
        )

    # Apply limit if specified
    if limit is not None:
        results = results[:limit]

    # Final memory cleanup and logging
    if total_entries > 5000:
        logger.info(
            f"Completed processing {total_entries} entries, returned {len(results)} results"
        )

    # Clear large intermediate data structures to free memory
    del entries_with_similarities
    del unique_entries
    del grouped_entries
    del entries_data

    return results


@router.get("/group-by-matched")
async def get_soap_group_by_matched(
    months: str = Query(..., description="Comma-separated months (e.g., '2025-05,2025-06')"),
    group_by_matched: bool = Query(True, description="Group by matched string (brand + scent)"),
    limit: Optional[int] = Query(None, ge=1, description="Maximum number of results"),
):
    """
    Group soap matches by matched string (brand + scent) to show total usage counts
    for each soap across all match types.

    When group_by_matched=True:
    - Groups results by matched string (brand + scent) instead of original string
    - Shows matched string, total count, and top 3 most common original patterns with
      individual counts
    - Includes all match types (exact, brand, alias, regex) to show complete usage
    - Helps identify which soaps are most commonly mentioned and need better patterns

    When group_by_matched=False:
    - Groups results by original string (existing behavior)
    """
    try:
        # Validate months
        month_list = [m.strip() for m in months.split(",")]
        for month in month_list:
            if not is_valid_month(month):
                raise HTTPException(
                    status_code=400, detail=f"Invalid month format: {month}. Use YYYY-MM format."
                )

        # Load soap match data for the specified months
        matches = []
        for month in month_list:
            month_file = Path(f"../data/matched/{month}.json")
            if not month_file.exists():
                logger.warning(f"Month file not found: {month_file}")
                continue

            try:
                with open(month_file, "r", encoding="utf-8") as f:
                    month_data = json.load(f)
                    # Extract soap data from the data array
                    if "data" in month_data and isinstance(month_data["data"], list):
                        for record in month_data["data"]:
                            if "soap" in record and record["soap"]:
                                matches.append(record["soap"])
            except Exception as e:
                logger.error(f"Error loading month {month}: {e}")
                continue

        if not matches:
            return {
                "groups": [],
                "total_groups": 0,
                "total_matches": 0,
                "months_processed": month_list,
                "group_by_matched": group_by_matched,
            }

        # Debug: Log match types being processed
        match_types = {}
        for match in matches:
            match_type = match.get("match_type", "unknown")
            match_types[match_type] = match_types.get(match_type, 0) + 1
        print(f"🔍 DEBUG: Processing {len(matches)} matches with types: {match_types}")
        logger.info(f"🔍 DEBUG: Processing {len(matches)} matches with types: {match_types}")

        # Group the matches
        if group_by_matched:
            groups = group_soap_matches_by_matched(matches, limit)
        else:
            groups = group_soap_matches_by_original(matches, limit)

        return {
            "groups": groups,
            "total_groups": len(groups),
            "total_matches": sum(group["total_count"] for group in groups),
            "months_processed": month_list,
            "group_by_matched": group_by_matched,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in soap group by matched analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def group_soap_matches_by_matched(matches: List[dict], limit: Optional[int] = None) -> List[dict]:
    """
    Group soap matches by matched string (brand + scent) with original pattern aggregation.

    Returns groups sorted by total count (descending) with top 3 original patterns per group.
    """
    from collections import defaultdict, Counter

    # Group by matched string (brand + scent)
    matched_groups = defaultdict(list)

    for match in matches:
        # Include all match types (exact, brand, alias, regex) to show total counts
        # This helps identify which soaps are most commonly mentioned regardless of match type

        # Extract matched data
        matched_data = match.get("matched", {})
        if not matched_data:
            continue

        brand = matched_data.get("brand", "").strip()
        scent = matched_data.get("scent", "").strip()
        match_type = match.get("match_type", "unknown")

        if not brand or not scent:
            if match_type == "alias":
                print(f"🔍 DEBUG: Skipping alias match due to missing brand/scent: {match}")
            continue

        # Create matched string key (case-insensitive for grouping)
        matched_key = f"{brand} - {scent}".lower()

        # Store normalized pattern and match type (for Group by Matched we want normalized patterns)
        normalized = match.get("normalized", "").strip()
        match_type = match.get("match_type", "unknown")

        if normalized:
            matched_groups[matched_key].append(
                {
                    "original": normalized,  # Use normalized field for pattern display
                    "match_type": match_type,
                    "count": match.get("count", 1),
                    "brand": brand,  # Store original case brand
                    "scent": scent,  # Store original case scent
                }
            )

    # Convert to result format
    results = []
    for matched_string_lower, patterns in matched_groups.items():
        # Get the proper case from the first pattern's stored brand/scent
        # This preserves the original case from the catalog data
        if patterns and "brand" in patterns[0] and "scent" in patterns[0]:
            brand = patterns[0]["brand"]  # Use original case from catalog
            scent = patterns[0]["scent"]  # Use original case from catalog
        else:
            # Fallback to title case if no stored data
            brand_lower, scent_lower = (
                matched_string_lower.split(" - ", 1)
                if " - " in matched_string_lower
                else (matched_string_lower, "")
            )
            brand = brand_lower.title()
            scent = scent_lower.title()

        # Create display version of matched_string with proper case
        matched_string = f"{brand} - {scent}"

        # Count total occurrences
        total_count = sum(pattern["count"] for pattern in patterns)

        # Count original patterns with match type information
        # Use case-insensitive grouping for original patterns to avoid duplicates like
        # "sample" vs "Sample"
        pattern_data = {}
        for pattern in patterns:
            original = pattern["original"]
            # Create a normalized key for grouping (case-insensitive)
            normalized_key = original.lower()

            if normalized_key not in pattern_data:
                pattern_data[normalized_key] = {
                    "count": 0,
                    "match_types": Counter(),
                    "original_display": original,  # Store original case for display
                }
            pattern_data[normalized_key]["count"] += pattern["count"]
            pattern_data[normalized_key]["match_types"][pattern["match_type"]] += pattern["count"]

        # Get top 3 most common original patterns
        top_patterns = sorted(pattern_data.items(), key=lambda x: x[1]["count"], reverse=True)[:3]
        remaining_count = len(pattern_data) - 3

        # Format top patterns with match type
        top_patterns_formatted = [
            {
                "original": data["original_display"],  # Use original case for display
                "count": data["count"],
                "match_type": (
                    data["match_types"].most_common(1)[0][0] if data["match_types"] else "unknown"
                ),
            }
            for pattern, data in top_patterns
        ]

        # Get all patterns for "+ n more" functionality
        all_patterns = [
            {
                "original": data["original_display"],  # Use original case for display
                "count": data["count"],
                "match_type": (
                    data["match_types"].most_common(1)[0][0] if data["match_types"] else "unknown"
                ),
            }
            for pattern, data in sorted(
                pattern_data.items(), key=lambda x: x[1]["count"], reverse=True
            )
        ]

        # Aggregate match types for this group
        match_type_counts = Counter()
        for pattern in patterns:
            match_type_counts[pattern["match_type"]] += pattern["count"]

        # Determine primary match type with priority: regex > brand > alias > exact
        # If a soap has regex matches, it should be categorized as regex regardless of other counts
        if "regex" in match_type_counts:
            primary_match_type = "regex"
        elif "brand" in match_type_counts:
            primary_match_type = "brand"
        elif "alias" in match_type_counts:
            primary_match_type = "alias"
        else:
            # If only exact matches, use exact as primary
            primary_match_type = "exact"

        # Debug: Log match type counts for groups with alias matches
        if "alias" in match_type_counts:
            print(
                f"🔍 DEBUG: Group '{matched_string}' has alias matches: "
                f"{dict(match_type_counts)} -> primary: {primary_match_type}"
            )

        # Create match type breakdown (exact + primary)
        match_type_breakdown = {
            "exact": match_type_counts.get("exact", 0),
            primary_match_type: match_type_counts.get(primary_match_type, 0),
        }

        results.append(
            {
                "matched_string": matched_string,
                "brand": brand,
                "scent": scent,
                "total_count": total_count,
                "top_patterns": top_patterns_formatted,
                "remaining_count": max(0, remaining_count),
                "all_patterns": all_patterns,
                "pattern_count": len(pattern_data),
                "match_type": primary_match_type,
                "match_type_breakdown": match_type_breakdown,
                "is_grouped": True,
            }
        )

    # Sort by total count (descending)
    results.sort(key=lambda x: x["total_count"], reverse=True)

    # Apply limit if specified
    if limit:
        results = results[:limit]

    return results


def group_soap_matches_by_original(matches: List[dict], limit: Optional[int] = None) -> List[dict]:
    """
    Group soap matches by original string (existing behavior).

    This maintains backward compatibility when group_by_matched=False.
    """
    from collections import defaultdict, Counter

    # Group by original string
    original_groups = defaultdict(list)

    for match in matches:
        original = match.get("original", "").strip()
        if not original:
            continue

        matched_data = match.get("matched", {})
        if not matched_data:
            continue

        brand = matched_data.get("brand", "").strip()
        scent = matched_data.get("scent", "").strip()

        if brand and scent:
            matched_string = f"{brand} - {scent}"
        else:
            matched_string = "Unknown"

        match_type = match.get("match_type", "unknown")
        count = match.get("count", 1)

        original_groups[original].append(
            {"matched_string": matched_string, "match_type": match_type, "count": count}
        )

    # Convert to result format
    results = []
    for original_string, matches_list in original_groups.items():
        # Count total occurrences
        total_count = sum(match["count"] for match in matches_list)

        # Count matched strings
        matched_counts = Counter()
        for match in matches_list:
            matched_counts[match["matched_string"]] += match["count"]

        # Get top 3 most common matched strings
        top_matched = matched_counts.most_common(3)
        remaining_count = len(matched_counts) - 3

        # Format top matched strings
        top_matched_formatted = [
            {"matched_string": matched_string, "count": count}
            for matched_string, count in top_matched
        ]

        # Get all matched strings for "+ n more" functionality
        all_matched = [
            {"matched_string": matched_string, "count": count}
            for matched_string, count in matched_counts.most_common()
        ]

        results.append(
            {
                "original_string": original_string,
                "total_count": total_count,
                "top_matched": top_matched_formatted,
                "remaining_count": max(0, remaining_count),
                "all_matched": all_matched,
                "matched_count": len(matched_counts),
            }
        )

    # Sort by total count (descending)
    results.sort(key=lambda x: x["total_count"], reverse=True)

    # Apply limit if specified
    if limit:
        results = results[:limit]

    return results
