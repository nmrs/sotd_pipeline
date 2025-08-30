#!/usr/bin/env python3
"""Shared catalog validation logic for CLI and API."""

from pathlib import Path
from typing import Dict, List, Any

import yaml
from sotd.match.brush_matcher import BrushMatcher


class CatalogValidator:
    """Shared catalog validation logic for CLI and API."""

    def __init__(self, project_root: Path):
        """Initialize the validator with project paths."""
        self.project_root = project_root
        self.correct_matches_path = project_root / "data" / "correct_matches.yaml"

        # Debug logging
        import os

        print(f"DEBUG: Current working directory: {os.getcwd()}")
        print(f"DEBUG: Project root: {project_root}")
        print(f"DEBUG: Correct matches path: {self.correct_matches_path}")

        # Initialize brush matcher with default configuration
        # The bypass_correct_matches parameter is now passed to the match method, not constructor
        self.brush_matcher = BrushMatcher()

        # Debug logging for brush matcher
        print(f"DEBUG: Brush matcher initialized: {self.brush_matcher}")
        print(
            f"DEBUG: Brush matcher config path: {getattr(self.brush_matcher, 'config_path', 'Not set')}"
        )

    def load_correct_matches(self) -> Dict[str, Any]:
        """Load correct_matches.yaml data."""
        if not self.correct_matches_path.exists():
            raise FileNotFoundError(f"correct_matches.yaml not found: {self.correct_matches_path}")

        with open(self.correct_matches_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def validate_brush_catalog(self) -> List[Dict[str, Any]]:
        """Validate brush catalog entries by testing actual matching system.

        This method tests whether the brush matching strategies (without correct_matches.yaml)
        can produce the same results as stored in correct_matches.yaml. It validates
        that our strategy system is working correctly, not just that entries exist.

        Returns:
            List of validation issues found
        """
        # Load correct_matches.yaml to get expected results
        data = self.load_correct_matches()
        brush_data = data.get("brush", {})

        issues = []

        # Process each pattern through the brush matcher WITHOUT correct_matches.yaml
        # This tests whether our strategy system can produce the expected results
        for brand, brand_data in brush_data.items():
            if isinstance(brand_data, dict):
                for model, model_data in brand_data.items():
                    if isinstance(model_data, list):
                        for pattern in model_data:
                            try:
                                # Run pattern through brush matcher WITHOUT correct_matches.yaml
                                # This tests the actual strategy system, not the cheat sheet
                                print(f"DEBUG: Testing pattern: {pattern}")  # Debug log
                                result = self.brush_matcher.match(
                                    pattern, bypass_correct_matches=True
                                )
                                print(f"DEBUG: Result: {result}")  # Debug log
                                print(
                                    f"DEBUG: Has matched: {hasattr(result, 'matched') if result else False}"
                                )  # Debug log
                                print(
                                    f"DEBUG: Matched value: {getattr(result, 'matched', None) if result else None}"
                                )  # Debug log

                                if result and hasattr(result, "matched") and result.matched:
                                    # Extract brand and model from matcher result
                                    # Handle both object and dictionary types
                                    if hasattr(result.matched, "get"):
                                        # Dictionary-like object
                                        matched_brand = result.matched.get("brand")
                                        matched_model = result.matched.get("model")
                                    else:
                                        # Object with attributes
                                        matched_brand = getattr(result.matched, "brand", None)
                                        matched_model = getattr(result.matched, "model", None)

                                    # Check if this is a composite brush (has handle/knot components)
                                    has_handle = False
                                    has_knot = False
                                    if hasattr(result.matched, "get"):
                                        # Dictionary-like object
                                        has_handle = (
                                            "handle" in result.matched
                                            and result.matched.get("handle")
                                        )
                                        has_knot = "knot" in result.matched and result.matched.get(
                                            "knot"
                                        )
                                    else:
                                        # Object with attributes
                                        has_handle = (
                                            hasattr(result.matched, "handle")
                                            and result.matched.handle
                                        )
                                        has_knot = (
                                            hasattr(result.matched, "knot") and result.matched.knot
                                        )

                                    # IMPORTANT: Only flag as composite brush if the matcher didn't return a top-level brand/model
                                    # Known brushes can have both top-level brand/model AND handle/knot components populated
                                    # This is the correct behavior for catalog-driven brushes according to the specification
                                    if (has_handle or has_knot) and (
                                        not matched_brand or not matched_model
                                    ):
                                        # This is a composite brush - check if it should be stored in handle/knot sections
                                        # Extract handle/knot information
                                        if hasattr(result.matched, "get"):
                                            # Dictionary-like object
                                            handle_data = result.matched.get("handle", {})
                                            knot_data = result.matched.get("knot", {})
                                            matched_handle_brand = (
                                                handle_data.get("brand") if handle_data else None
                                            )
                                            matched_handle_model = (
                                                handle_data.get("model") if handle_data else None
                                            )
                                            matched_knot_brand = (
                                                knot_data.get("brand") if knot_data else None
                                            )
                                            matched_knot_model = (
                                                knot_data.get("model") if knot_data else None
                                            )
                                        else:
                                            # Object with attributes
                                            matched_handle_brand = (
                                                getattr(result.matched.handle, "brand", None)
                                                if hasattr(result.matched, "handle")
                                                else None
                                            )
                                            matched_handle_model = (
                                                getattr(result.matched.handle, "model", None)
                                                if hasattr(result.matched, "handle")
                                                else None
                                            )
                                            matched_knot_brand = (
                                                getattr(result.matched.knot, "brand", None)
                                                if hasattr(result.matched, "knot")
                                                else None
                                            )
                                            matched_knot_model = (
                                                getattr(result.matched.knot, "model", None)
                                                if hasattr(result.matched, "knot")
                                                else None
                                            )

                                        # Flag if composite brush is stored in complete brush section
                                        issues.append(
                                            {
                                                "type": "composite_brush_in_wrong_section",
                                                "field": "brush",
                                                "pattern": pattern,
                                                "stored_brand": brand.strip(),
                                                "stored_model": model.strip(),
                                                "matched_handle_brand": matched_handle_brand,
                                                "matched_handle_model": matched_handle_model,
                                                "matched_knot_brand": matched_knot_brand,
                                                "matched_knot_model": matched_knot_model,
                                                "message": (
                                                    f"Pattern '{pattern}' is stored as complete brush under "
                                                    f"'{brand.strip()} {model.strip()}' but matcher returns "
                                                    f"composite brush with handle: {matched_handle_brand}/{matched_handle_model}, "
                                                    f"knot: {matched_knot_brand}/{matched_knot_model}"
                                                ),
                                                "suggested_action": (
                                                    f"Move pattern '{pattern}' from complete brush section to "
                                                    f"handle/knot sections or fix matcher to return complete brush"
                                                ),
                                            }
                                        )
                                    elif matched_brand and matched_model:
                                        # This is a complete brush - check for mismatches
                                        # Normalize for comparison
                                        stored_brand = brand.strip()
                                        stored_model = model.strip()

                                        if (
                                            matched_brand.lower() != stored_brand.lower()
                                            or matched_model.lower() != stored_model.lower()
                                        ):
                                            # Mismatch found!
                                            issues.append(
                                                {
                                                    "type": "catalog_pattern_mismatch",
                                                    "field": "brush",
                                                    "pattern": pattern,
                                                    "stored_brand": stored_brand,
                                                    "stored_model": stored_model,
                                                    "matched_brand": matched_brand,
                                                    "matched_model": matched_model,
                                                    "message": (
                                                        f"Pattern '{pattern}' is stored under "
                                                        f"'{stored_brand} {stored_model}' but matcher returns "
                                                        f"'{matched_brand} {matched_model}'"
                                                    ),
                                                    "suggested_action": (
                                                        f"Move from '{stored_brand} {stored_model}' to "
                                                        f"'{matched_brand} {matched_model}' in correct_matches.yaml"
                                                    ),
                                                }
                                            )
                                    else:
                                        # This is neither a complete brush nor a composite brush
                                        # Check if there's a basic brand mismatch
                                        if (
                                            matched_brand
                                            and matched_brand.lower() != brand.strip().lower()
                                        ):
                                            # Brand mismatch
                                            issues.append(
                                                {
                                                    "type": "catalog_pattern_mismatch",
                                                    "field": "brush",
                                                    "pattern": pattern,
                                                    "stored_brand": brand.strip(),
                                                    "stored_model": model.strip(),
                                                    "matched_brand": matched_brand,
                                                    "matched_model": matched_model,
                                                    "message": (
                                                        f"Pattern '{pattern}' is stored under "
                                                        f"'{brand.strip()}' but matcher returns brand "
                                                        f"'{matched_brand}'"
                                                    ),
                                                    "suggested_action": (
                                                        f"Check if pattern '{pattern}' should be moved to "
                                                        f"'{matched_brand}' section or if the matcher result is incorrect"
                                                    ),
                                                }
                                            )

                                        # Now check if this is a composite brush (model is null, but handle/knot components exist)
                                        # Check if this is a composite brush (model is null, but handle/knot components exist)
                                        is_composite = False
                                        if hasattr(result.matched, "get"):
                                            # Dictionary-like object
                                            is_composite = (
                                                not matched_model
                                                and "handle" in result.matched
                                                and "knot" in result.matched
                                            )
                                        else:
                                            # Object with attributes
                                            is_composite = (
                                                not matched_model
                                                and hasattr(result.matched, "handle")
                                                and hasattr(result.matched, "knot")
                                            )

                                        if is_composite:
                                            # This is a composite brush - check if it should be stored in handle/knot sections
                                            # Handle both object and dictionary types for handle/knot
                                            if hasattr(result.matched, "get"):
                                                # Dictionary-like object
                                                handle_data = result.matched.get("handle", {})
                                                knot_data = result.matched.get("knot", {})
                                                matched_handle_brand = (
                                                    handle_data.get("brand")
                                                    if handle_data
                                                    else None
                                                )
                                                matched_handle_model = (
                                                    handle_data.get("model")
                                                    if handle_data
                                                    else None
                                                )
                                                matched_knot_brand = (
                                                    knot_data.get("brand") if knot_data else None
                                                )
                                                matched_knot_model = (
                                                    knot_data.get("model") if knot_data else None
                                                )
                                            else:
                                                # Object with attributes
                                                matched_handle_brand = getattr(
                                                    result.matched.handle, "brand", None
                                                )
                                                matched_handle_model = getattr(
                                                    result.matched.handle, "model", None
                                                )
                                                matched_knot_brand = getattr(
                                                    result.matched.knot, "brand", None
                                                )
                                                matched_knot_model = getattr(
                                                    result.matched.knot, "model", None
                                                )

                                            # Flag if composite brush is stored in complete brush section
                                            issues.append(
                                                {
                                                    "type": "composite_brush_in_wrong_section",
                                                    "field": "brush",
                                                    "pattern": pattern,
                                                    "stored_brand": brand.strip(),
                                                    "stored_model": model.strip(),
                                                    "matched_handle_brand": matched_handle_brand,
                                                    "matched_handle_model": matched_handle_model,
                                                    "matched_knot_brand": matched_knot_brand,
                                                    "matched_knot_model": matched_knot_model,
                                                    "message": (
                                                        f"Pattern '{pattern}' is stored as complete brush under "
                                                        f"'{brand.strip()} {model.strip()}' but matcher returns "
                                                        f"composite brush with handle: {matched_handle_brand}/{matched_handle_model}, "
                                                        f"knot: {matched_knot_brand}/{matched_knot_model}"
                                                    ),
                                                    "suggested_action": (
                                                        f"Move pattern '{pattern}' from complete brush section to "
                                                        f"handle/knot sections or fix matcher to return complete brush"
                                                    ),
                                                }
                                            )

                                        # Now check for single component brushes (handle-only or knot-only)
                                        elif not matched_model and (
                                            (
                                                hasattr(result.matched, "handle")
                                                and (
                                                    hasattr(result.matched, "get")
                                                    and result.matched.get("handle", {}).get(
                                                        "brand"
                                                    )
                                                    or getattr(result.matched.handle, "brand", None)
                                                )
                                            )
                                            or (
                                                hasattr(result.matched, "knot")
                                                and (
                                                    hasattr(result.matched, "get")
                                                    and result.matched.get("knot", {}).get("brand")
                                                    or getattr(result.matched.knot, "brand", None)
                                                )
                                            )
                                        ):
                                            # This is a single component brush - check if it should be stored in handle/knot sections
                                            if hasattr(result.matched, "get"):
                                                # Dictionary-like object
                                                handle_data = result.matched.get("handle", {})
                                                knot_data = result.matched.get("knot", {})
                                                matched_handle_brand = (
                                                    handle_data.get("brand")
                                                    if handle_data
                                                    else None
                                                )
                                                matched_knot_brand = (
                                                    knot_data.get("brand") if knot_data else None
                                                )
                                            else:
                                                # Object with attributes
                                                matched_handle_brand = (
                                                    getattr(result.matched.handle, "brand", None)
                                                    if hasattr(result.matched, "handle")
                                                    else None
                                                )
                                                matched_knot_brand = (
                                                    getattr(result.matched.knot, "brand", None)
                                                    if hasattr(result.matched, "knot")
                                                    else None
                                                )

                                            # Determine which component is populated
                                            if matched_handle_brand and not matched_knot_brand:
                                                # Handle-only brush
                                                issues.append(
                                                    {
                                                        "type": "handle_only_brush_in_wrong_section",
                                                        "field": "brush",
                                                        "pattern": pattern,
                                                        "stored_brand": brand.strip(),
                                                        "stored_model": model.strip(),
                                                        "matched_handle_brand": matched_handle_brand,
                                                        "message": (
                                                            f"Pattern '{pattern}' is stored as complete brush under "
                                                            f"'{brand.strip()} {model.strip()}' but matcher returns "
                                                            f"handle-only brush: {matched_handle_brand}"
                                                        ),
                                                        "suggested_action": (
                                                            f"Move pattern '{pattern}' from complete brush section to "
                                                            f"handle section under {matched_handle_brand}"
                                                        ),
                                                    }
                                                )
                                            elif matched_knot_brand and not matched_handle_brand:
                                                # Knot-only brush
                                                issues.append(
                                                    {
                                                        "type": "knot_only_brush_in_wrong_section",
                                                        "field": "brush",
                                                        "pattern": pattern,
                                                        "stored_brand": brand.strip(),
                                                        "stored_model": model.strip(),
                                                        "matched_knot_brand": matched_knot_brand,
                                                        "message": (
                                                            f"Pattern '{pattern}' is stored as complete brush under "
                                                            f"'{brand.strip()} {model.strip()}' but matcher returns "
                                                            f"knot-only brush: {matched_knot_brand}"
                                                        ),
                                                        "suggested_action": (
                                                            f"Move pattern '{pattern}' from complete brush section to "
                                                            f"knot section under {matched_knot_brand}"
                                                        ),
                                                    }
                                                )

                                else:
                                    # Pattern couldn't be matched
                                    issues.append(
                                        {
                                            "type": "unmatched_pattern",
                                            "field": "brush",
                                            "pattern": pattern,
                                            "stored_brand": brand.strip(),
                                            "stored_model": model.strip(),
                                            "message": (
                                                f"Pattern '{pattern}' could not be matched by brush matcher"
                                            ),
                                            "suggested_action": (
                                                f"Check if pattern '{pattern}' is valid or if brush matcher needs updates"
                                            ),
                                        }
                                    )

                            except Exception as e:
                                # Error during matching
                                issues.append(
                                    {
                                        "type": "matching_error",
                                        "field": "brush",
                                        "pattern": pattern,
                                        "stored_brand": brand.strip(),
                                        "stored_model": model.strip(),
                                        "error": str(e),
                                        "message": (
                                            f"Error during matching of pattern '{pattern}': {e}"
                                        ),
                                        "suggested_action": (
                                            f"Investigate error with '{pattern}' - check brush matcher implementation"
                                        ),
                                    }
                                )

        return issues

    def validate_field(self, field: str) -> List[Dict[str, Any]]:
        """Validate a specific field in the catalog.

        Args:
            field: The field to validate (e.g., "brush", "blade", "razor")

        Returns:
            List of validation issues found
        """
        if field == "brush":
            return self.validate_brush_catalog()
        else:
            # For now, only brush validation is implemented
            return []

    def get_validation_summary(self, field: str) -> Dict[str, Any]:
        """Get validation summary for a specific field.

        This method is expected by the API to return a dictionary with an "issues" key.

        Args:
            field: Field to validate (e.g., "brush")

        Returns:
            Dictionary with "issues" key containing validation results
        """
        if field == "brush":
            issues = self.validate_brush_catalog()
            return {"issues": issues}
        else:
            # For other fields, return empty issues list
            # This method is primarily for brush validation
            return {"issues": []}
