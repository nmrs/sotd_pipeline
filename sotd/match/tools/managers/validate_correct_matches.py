#!/usr/bin/env python3
"""Validation tool for detecting catalog drift in correct_matches.yaml."""

import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add project root to Python path for direct execution
project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sotd.match.base_matcher import BaseMatcher  # noqa: E402
from sotd.match.blade_matcher import BladeMatcher  # noqa: E402
from sotd.match.brush_matcher import BrushMatcher  # noqa: E402
from sotd.match.razor_matcher import RazorMatcher  # noqa: E402
from sotd.match.soap_matcher import SoapMatcher  # noqa: E402
from sotd.match.correct_matches_updater import CorrectMatchesUpdater  # noqa: E402
from sotd.match.config import BrushMatcherConfig  # noqa: E402

logger = logging.getLogger(__name__)


class ValidateCorrectMatches:
    """Validate correct_matches.yaml against current catalog patterns."""

    def __init__(self, correct_matches_path: Optional[Path] = None):
        """Initialize validation tool with all matchers."""
        self.correct_matches_path = correct_matches_path or Path("data/correct_matches.yaml")
        self.correct_matches = self._load_correct_matches()

        # Don't initialize matchers upfront - lazy load them when needed
        self._matchers = {}

        # Initialize the updater for creating temp files
        self.updater = CorrectMatchesUpdater()

        # Performance optimization: Pre-compute normalized catalogs
        self._normalized_catalogs = {}
        self._validation_cache = {}

        # Pre-compute all validation data structures
        self._precompute_validation_structures()

    def _load_correct_matches(self) -> Dict[str, Any]:
        """Load correct_matches.yaml file."""
        if not self.correct_matches_path.exists():
            return {}

        try:
            import yaml

            with open(self.correct_matches_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if data else {}
        except Exception as e:
            logger.error(f"Error loading correct_matches.yaml: {e}")
            return {}

    def _get_matcher(self, field: str) -> Optional[BaseMatcher]:
        """Get the appropriate matcher for a field, lazy-loading if needed."""
        if field not in self._matchers:
            if field == "razor":
                self._matchers[field] = RazorMatcher(bypass_correct_matches=True)
            elif field == "blade":
                self._matchers[field] = BladeMatcher(bypass_correct_matches=True)
            elif field == "brush":
                self._matchers[field] = BrushMatcher(
                    BrushMatcherConfig(
                        catalog_path=Path("data/brushes.yaml"),
                        handles_path=Path("data/handles.yaml"),
                        knots_path=Path("data/knots.yaml"),
                        bypass_correct_matches=True,
                    )
                )
            elif field == "soap":
                self._matchers[field] = SoapMatcher(bypass_correct_matches=True)

        return self._matchers.get(field)

    def _create_temp_correct_matches(
        self, field: str, correct_matches: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a temporary correct_matches.yaml by running strings through current matchers."""
        if field not in correct_matches:
            return {}

        # Build expected structure directly in memory for performance
        expected_structure = {field: {}}
        field_section = correct_matches[field]

        if field == "blade":
            # For blades: format -> brand -> model -> patterns
            for format_name, format_section in field_section.items():
                expected_structure[field][format_name] = {}

                for brand_name, brand_section in format_section.items():
                    expected_structure[field][format_name][brand_name] = {}

                    for model_name, model_section in brand_section.items():
                        expected_structure[field][format_name][brand_name][model_name] = []

                        if isinstance(model_section, list):
                            for pattern in model_section:
                                # Use context-aware matching for blades
                                blade_matcher = self._get_matcher("blade")
                                if blade_matcher and isinstance(blade_matcher, BladeMatcher):
                                    match_result = blade_matcher.match_with_context(
                                        pattern, format_name
                                    )
                                else:
                                    match_result = None
                                if (
                                    match_result
                                    and hasattr(match_result, "matched")
                                    and match_result.matched
                                ):
                                    matched_data = match_result.matched
                                    actual_brand = matched_data.get("brand")
                                    actual_model = matched_data.get("model")

                                    if actual_brand and actual_model:
                                        # Add to expected structure based on where matcher thinks it should be
                                        if (
                                            actual_brand
                                            not in expected_structure[field][format_name]
                                        ):
                                            expected_structure[field][format_name][
                                                actual_brand
                                            ] = {}
                                        if (
                                            actual_model
                                            not in expected_structure[field][format_name][
                                                actual_brand
                                            ]
                                        ):
                                            expected_structure[field][format_name][actual_brand][
                                                actual_model
                                            ] = []
                                        expected_structure[field][format_name][actual_brand][
                                            actual_model
                                        ].append(pattern)
                                    else:
                                        # Fallback to original location
                                        expected_structure[field][format_name][brand_name][
                                            model_name
                                        ].append(pattern)
                                else:
                                    # Fallback to original location
                                    expected_structure[field][format_name][brand_name][
                                        model_name
                                    ].append(pattern)
        else:
            # For other fields: brand -> model -> patterns
            for brand_name, brand_section in field_section.items():
                expected_structure[field][brand_name] = {}

                for model_name, model_section in brand_section.items():
                    expected_structure[field][brand_name][model_name] = []

                    if isinstance(model_section, list):
                        for pattern in model_section:
                            matcher = self._get_matcher(field)
                            if matcher:
                                match_result = matcher.match(pattern)
                                if (
                                    match_result
                                    and hasattr(match_result, "matched")
                                    and match_result.matched
                                ):
                                    matched_data = match_result.matched
                                    actual_brand = matched_data.get("brand")
                                    actual_model = matched_data.get("model")

                                    if actual_brand and actual_model:
                                        # Add to expected structure based on where matcher thinks it should be
                                        if actual_brand not in expected_structure[field]:
                                            expected_structure[field][actual_brand] = {}
                                        if (
                                            actual_model
                                            not in expected_structure[field][actual_brand]
                                        ):
                                            expected_structure[field][actual_brand][
                                                actual_model
                                            ] = []
                                        expected_structure[field][actual_brand][
                                            actual_model
                                        ].append(pattern)
                                    else:
                                        # Fallback to original location
                                        expected_structure[field][brand_name][model_name].append(
                                            pattern
                                        )
                                else:
                                    # Fallback to original location
                                    expected_structure[field][brand_name][model_name].append(
                                        pattern
                                    )

        return expected_structure

    def _validate_catalog_existence(
        self, field: str, original: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Validate that brands and models in correct_matches.yaml exist in current catalogs."""
        issues = []

        if field not in original:
            return issues

        original_section = original[field]

        if field == "blade":
            # For blades: validate format -> brand -> model existence
            for format_name in original_section:
                for brand_name in original_section[format_name]:
                    # Check if brand exists in current blade catalog
                    if not self._brand_exists_in_catalog(field, brand_name, format_name):
                        issues.append(
                            {
                                "type": "invalid_brand",
                                "field": field,
                                "format": format_name,
                                "brand": brand_name,
                                "message": (
                                    f"Brand '{brand_name}' does not exist in current {field} "
                                    f"catalog for format '{format_name}'"
                                ),
                            }
                        )
                        continue

                    for model_name in original_section[format_name][brand_name]:
                        # Check if model exists for this brand in current catalog
                        if not self._model_exists_in_catalog(
                            field, brand_name, model_name, format_name
                        ):
                            issues.append(
                                {
                                    "type": "invalid_model",
                                    "field": field,
                                    "format": format_name,
                                    "brand": brand_name,
                                    "model": model_name,
                                    "message": (
                                        f"Model '{model_name}' does not exist for brand "
                                        f"'{brand_name}' in current {field} catalog for "
                                        f"format '{format_name}'"
                                    ),
                                }
                            )
        else:
            # For other fields: validate brand -> model existence
            for brand_name in original_section:
                # Check if brand exists in current catalog
                if not self._brand_exists_in_catalog(field, brand_name):
                    issues.append(
                        {
                            "type": "invalid_brand",
                            "field": field,
                            "brand": brand_name,
                            "message": f"Brand '{brand_name}' does not exist in current {field} catalog",
                        }
                    )
                    continue

                for model_name in original_section[brand_name]:
                    # Check if model exists for this brand in current catalog
                    if not self._model_exists_in_catalog(field, brand_name, model_name):
                        # For brush field, also check if matcher can handle this combination
                        if field == "brush" and self._matcher_can_handle_combination(
                            field, brand_name, model_name
                        ):
                            issues.append(
                                {
                                    "type": "missing_from_catalog",
                                    "field": field,
                                    "brand": brand_name,
                                    "model": model_name,
                                    "message": (
                                        f"Model '{model_name}' for brand '{brand_name}' is missing from "
                                        f"catalog but CAN be matched by brush matcher strategies"
                                    ),
                                }
                            )
                        else:
                            issues.append(
                                {
                                    "type": "invalid_model",
                                    "field": field,
                                    "brand": brand_name,
                                    "model": model_name,
                                    "message": f"Model '{model_name}' does not exist for brand '{brand_name}' in current {field} catalog",
                                }
                            )

        return issues

    def _brand_exists_in_catalog(
        self, field: str, brand_name: str, format_name: str = None
    ) -> bool:
        """Optimized brand existence check using cached validation data."""
        import unicodedata

        # Use cached validation data for O(1) lookup
        if field not in self._validation_cache:
            self._build_validation_cache(field)

        normalized_brand = unicodedata.normalize("NFC", brand_name)
        validation_cache = self._validation_cache[field]

        if field == "blade" and format_name:
            return (
                format_name in validation_cache
                and normalized_brand in validation_cache[format_name]
            )
        else:
            exists = normalized_brand in validation_cache
            if field == "brush" and brand_name == "Yaqi":
                logger.debug(f"Checking Yaqi brand existence: {exists}")
                logger.debug(f"Available brands: {list(validation_cache.keys())}")
            return exists

    def _model_exists_in_catalog(
        self, field: str, brand_name: str, model_name: str, format_name: str = None
    ) -> bool:
        """Optimized model existence check using cached validation data."""
        import unicodedata

        # Use cached validation data for O(1) lookup
        if field not in self._validation_cache:
            self._build_validation_cache(field)

        normalized_brand = unicodedata.normalize("NFC", brand_name)
        normalized_model = unicodedata.normalize("NFC", model_name)
        validation_cache = self._validation_cache[field]

        if field == "blade" and format_name:
            return (
                format_name in validation_cache
                and normalized_brand in validation_cache[format_name]
                and normalized_model in validation_cache[format_name][normalized_brand]
            )
        else:
            exists = (
                normalized_brand in validation_cache
                and normalized_model in validation_cache[normalized_brand]
            )
            if field == "brush" and brand_name == "Yaqi" and model_name in ["Ferrari", "Sagrada"]:
                logger.debug(f"Checking Yaqi {model_name} model existence: {exists}")
                if normalized_brand in validation_cache:
                    logger.debug(
                        f"Available models for Yaqi: {list(validation_cache[normalized_brand])}"
                    )
                else:
                    logger.debug("Yaqi brand not found in validation cache")
            return exists

    def _load_catalog_data(self, field: str) -> Dict[str, Any]:
        """Load catalog data for a specific field."""
        try:
            # Use _data_dir if set (for testing), otherwise use default data/ directory
            base_dir = getattr(self, "_data_dir", None) or Path("data")

            if field == "blade":
                catalog_path = base_dir / "blades.yaml"
            elif field == "brush":
                catalog_path = base_dir / "brushes.yaml"
            elif field == "razor":
                catalog_path = base_dir / "razors.yaml"
            elif field == "soap":
                catalog_path = base_dir / "soaps.yaml"
            else:
                return {}

            if not catalog_path.exists():
                return {}

            import yaml

            with open(catalog_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def _compare_structures(
        self, field: str, original: Dict[str, Any], expected: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Compare original and expected structures to find drift."""
        issues = []

        if field not in original or field not in expected:
            return issues

        original_section = original[field]
        expected_section = expected[field]

        if field == "blade":
            # For blades: compare format -> brand -> model -> patterns
            for format_name in original_section:
                if format_name not in expected_section:
                    issues.append(
                        {
                            "type": "missing_format",
                            "field": field,
                            "format": format_name,
                            "message": f"Format '{format_name}' missing from expected structure",
                        }
                    )
                    continue

                for brand_name in original_section[format_name]:
                    if brand_name not in expected_section[format_name]:
                        issues.append(
                            {
                                "type": "missing_brand",
                                "field": field,
                                "format": format_name,
                                "brand": brand_name,
                                "message": f"Brand '{brand_name}' missing from format '{format_name}'",
                            }
                        )
                        continue

                    for model_name in original_section[format_name][brand_name]:
                        if model_name not in expected_section[format_name][brand_name]:
                            issues.append(
                                {
                                    "type": "missing_model",
                                    "field": field,
                                    "format": format_name,
                                    "brand": brand_name,
                                    "model": model_name,
                                    "message": f"Model '{model_name}' missing from brand '{brand_name}' in format '{format_name}'",
                                }
                            )
                            continue

                        # Check patterns
                        original_patterns = original_section[format_name][brand_name][model_name]
                        expected_patterns = expected_section[format_name][brand_name][model_name]

                        for pattern in original_patterns:
                            if pattern not in expected_patterns:
                                issues.append(
                                    {
                                        "type": "missing_pattern",
                                        "field": field,
                                        "format": format_name,
                                        "brand": brand_name,
                                        "model": model_name,
                                        "pattern": pattern,
                                        "message": f"Pattern '{pattern}' missing from expected structure",
                                    }
                                )
        else:
            # For other fields: compare brand -> model -> patterns
            for brand_name in original_section:
                if brand_name not in expected_section:
                    issues.append(
                        {
                            "type": "missing_brand",
                            "field": field,
                            "brand": brand_name,
                            "message": f"Brand '{brand_name}' missing from expected structure",
                        }
                    )
                    continue

                for model_name in original_section[brand_name]:
                    if model_name not in expected_section[brand_name]:
                        issues.append(
                            {
                                "type": "missing_model",
                                "field": field,
                                "brand": brand_name,
                                "model": model_name,
                                "message": f"Model '{model_name}' missing from brand '{brand_name}'",
                            }
                        )
                        continue

                    # Check patterns
                    original_patterns = original_section[brand_name][model_name]
                    expected_patterns = expected_section[brand_name][model_name]

                    for pattern in original_patterns:
                        if pattern not in expected_patterns:
                            issues.append(
                                {
                                    "type": "missing_pattern",
                                    "field": field,
                                    "brand": brand_name,
                                    "model": model_name,
                                    "pattern": pattern,
                                    "message": f"Pattern '{pattern}' missing from expected structure",
                                }
                            )

        return issues

    def validate_field(self, field: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Validate a specific field for catalog drift."""
        if field not in self.correct_matches:
            return [], {}

        logger.info(f"Validating field: {field}")

        # First validate catalog existence (check for invalid brands/models)
        catalog_issues = self._validate_catalog_existence(field, self.correct_matches)

        # Create expected structure using current matchers
        expected_structure = self._create_temp_correct_matches(field, self.correct_matches)

        # Compare structures to find drift
        drift_issues = self._compare_structures(field, self.correct_matches, expected_structure)

        # Combine all issues
        all_issues = catalog_issues + drift_issues

        return all_issues, expected_structure

    def validate_all_fields(self) -> Dict[str, List[Dict[str, Any]]]:
        """Validate all fields for catalog drift."""
        all_issues = {}

        for field in ["razor", "blade", "brush", "soap"]:
            if field in self.correct_matches:
                issues, _ = self.validate_field(field)
                if issues:
                    all_issues[field] = issues

        return all_issues

    def run_validation(self, field: Optional[str] = None) -> None:
        """Run validation and report results."""
        if field:
            issues, expected_structure = self.validate_field(field)
            self._report_issues(field, issues, expected_structure)
        else:
            all_issues = self.validate_all_fields()
            self._report_all_issues(all_issues)

    def _report_issues(
        self, field: str, issues: List[Dict[str, Any]], expected_structure: Dict[str, Any]
    ) -> None:
        """Report validation issues for a specific field."""
        if not issues:
            print(f"✅ No validation issues found for {field}!")
            return

        print(f"🔴 Found {len(issues)} validation issues for {field}:")
        print()

        # Group issues by type
        issues_by_type = {}
        for issue in issues:
            issue_type = issue["type"]
            if issue_type not in issues_by_type:
                issues_by_type[issue_type] = []
            issues_by_type[issue_type].append(issue)

        for issue_type, type_issues in issues_by_type.items():
            print(f"📋 {issue_type.replace('_', ' ').title()} ({len(type_issues)} issues):")
            for issue in type_issues:
                print(f"   • {issue['message']}")

                # Add detailed information for missing patterns
                if issue_type == "missing_pattern":
                    pattern = issue.get("pattern", "unknown")
                    current_location = self._find_current_location(field, pattern)
                    expected_location = self._find_expected_location(
                        field, pattern, expected_structure
                    )

                    if current_location:
                        print(f"     Current location: {current_location}")
                    if expected_location:
                        print(f"     Expected location: {expected_location}")

                    # Show what the matcher actually returned
                    matcher_result = self._get_matcher_result(field, pattern)
                    if matcher_result:
                        print(f"     Matcher result: {matcher_result}")

                print()

    def _find_current_location(self, field: str, pattern: str) -> Optional[str]:
        """Find where a pattern currently exists in correct_matches.yaml."""
        if field not in self.correct_matches:
            return None

        field_section = self.correct_matches[field]

        if field == "blade":
            # For blades: format -> brand -> model -> patterns
            for format_name, format_section in field_section.items():
                for brand_name, brand_section in format_section.items():
                    for model_name, model_section in brand_section.items():
                        if isinstance(model_section, list) and pattern in model_section:
                            return f"{format_name} → {brand_name} → {model_name}"
        else:
            # For other fields: brand -> model -> patterns
            for brand_name, brand_section in field_section.items():
                for model_name, model_section in brand_section.items():
                    if isinstance(model_section, list) and pattern in model_section:
                        return f"{brand_name} → {model_name}"

        return None

    def _find_expected_location(
        self, field: str, pattern: str, expected_structure: Dict[str, Any]
    ) -> Optional[str]:
        """Find where a pattern should be according to the expected structure."""
        if field not in expected_structure:
            return None

        field_section = expected_structure[field]

        if field == "blade":
            # For blades: format -> brand -> model -> patterns
            for format_name, format_section in field_section.items():
                for brand_name, brand_section in format_section.items():
                    for model_name, model_section in brand_section.items():
                        if isinstance(model_section, list) and pattern in model_section:
                            return f"{format_name} → {brand_name} → {model_name}"
        else:
            # For other fields: brand -> model -> patterns
            for brand_name, brand_section in field_section.items():
                for model_name, model_section in brand_section.items():
                    if isinstance(model_section, list) and pattern in model_section:
                        return f"{brand_name} → {model_name}"

        return None

    def _get_matcher_result(self, field: str, pattern: str) -> Optional[str]:
        """Get what the matcher actually returns for a pattern."""
        matcher = self._get_matcher(field)
        if not matcher:
            return None

        try:
            if field == "blade" and isinstance(matcher, BladeMatcher):
                # Try to find the format context from current location
                current_location = self._find_current_location(field, pattern)
                if current_location and " → " in current_location:
                    format_context = current_location.split(" → ")[0]
                    result = matcher.match_with_context(pattern, format_context)
                else:
                    result = matcher.match(pattern)
            else:
                result = matcher.match(pattern)

            if result and hasattr(result, "matched") and result.matched:
                matched_data = result.matched
                brand = matched_data.get("brand", "unknown")
                model = matched_data.get("model", "unknown")
                format_info = matched_data.get("format", "")

                if format_info:
                    return f"{format_info} → {brand} → {model}"
                else:
                    return f"{brand} → {model}"
            else:
                return "No match found"
        except Exception as e:
            return f"Error: {e}"

    def _print_structure_summary(self, structure: Dict[str, Any], indent: str = "     ") -> None:
        """Print a summary of the structure."""
        if not structure:
            print(f"{indent}Empty")
            return

        if "74" in structure:  # Blade format
            for format_name, format_section in structure.items():
                print(f"{indent}{format_name}:")
                for brand_name, brand_section in format_section.items():
                    print(f"{indent}  {brand_name}:")
                    for model_name, model_section in brand_section.items():
                        if isinstance(model_section, list):
                            print(f"{indent}    {model_name}: {len(model_section)} patterns")
        else:  # Other fields
            for brand_name, brand_section in structure.items():
                print(f"{indent}{brand_name}:")
                for model_name, model_section in brand_section.items():
                    if isinstance(model_section, list):
                        print(f"{indent}  {model_name}: {len(model_section)} patterns")

    def _report_all_issues(self, all_issues: Dict[str, List[Dict[str, Any]]]) -> None:
        """Report validation issues for all fields."""
        if not all_issues:
            print("✅ No validation issues found!")
            return

        total_issues = sum(len(issues) for issues in all_issues.values())
        print(f"🔴 Found {total_issues} total validation issues:")
        print()

        for field, issues in all_issues.items():
            print(f"📋 {field}: {len(issues)} issues")
            for issue in issues[:3]:  # Show first 3 issues per field
                print(f"   • {issue['message']}")
            if len(issues) > 3:
                print(f"   ... and {len(issues) - 3} more")
            print()

    def _precompute_validation_structures(self):
        """Pre-compute all validation data structures for performance."""
        logger.info("Pre-computing validation structures...")
        start_time = time.perf_counter()

        for field in ["razor", "blade", "brush", "soap"]:
            if field in self.correct_matches:
                self._build_validation_cache(field)

        precompute_time = time.perf_counter() - start_time
        logger.info(f"Validation structures pre-computed in {precompute_time*1000:.2f}ms")

    def _build_validation_cache(self, field: str):
        """Build validation cache for a specific field."""
        if field in self._validation_cache:
            return self._validation_cache[field]

        # Get normalized catalog
        normalized_catalog = self._get_normalized_catalog(field)



        # Build existence cache
        existence_cache = {}

        if field == "blade":
            # For blades: format -> brand -> model
            for format_name, format_section in normalized_catalog.items():
                existence_cache[format_name] = {}
                for brand_name, brand_section in format_section.items():
                    existence_cache[format_name][brand_name] = set(brand_section.keys())
        else:
            # For other fields: brand -> model
            for brand_name, brand_section in normalized_catalog.items():
                existence_cache[brand_name] = set(brand_section.keys())

        self._validation_cache[field] = existence_cache
        return existence_cache

    def _get_normalized_catalog(self, field: str) -> Dict[str, Any]:
        """Get cached normalized catalog with pre-computed keys."""
        if field not in self._normalized_catalogs:
            catalog_data = self._load_catalog_data(field)

            normalized = self._normalize_catalog_keys(catalog_data)
            self._normalized_catalogs[field] = normalized

        return self._normalized_catalogs[field]

    def _normalize_catalog_keys(self, catalog_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize all catalog keys for efficient lookup."""
        import unicodedata
        import copy

        if not catalog_data:
            return {}

        # Create a deep copy to avoid mutating the original data
        catalog_data = copy.deepcopy(catalog_data)



        normalized = {}

        if "74" in catalog_data:  # Blade format
            for format_name, format_section in catalog_data.items():
                normalized[format_name] = {}
                for brand_name, brand_section in format_section.items():
                    normalized_brand = unicodedata.normalize("NFC", brand_name)
                    normalized[format_name][normalized_brand] = {}
                    for model_name, model_section in brand_section.items():
                        normalized_model = unicodedata.normalize("NFC", model_name)
                        normalized[format_name][normalized_brand][normalized_model] = model_section
        elif "known_brushes" in catalog_data:  # Brush format with nested structure
            # For validation, ONLY use known_brushes - these are the actual catalog entries
            # other_brushes are fallback patterns, not catalog products to validate against
            for brand_name, brand_section in catalog_data["known_brushes"].items():
                normalized_brand = unicodedata.normalize("NFC", brand_name)
                normalized[normalized_brand] = {}
                for model_name, model_section in brand_section.items():
                    normalized_model = unicodedata.normalize("NFC", model_name)
                    normalized[normalized_brand][normalized_model] = model_section
        else:  # Other fields (razor, soap)
            for brand_name, brand_section in catalog_data.items():
                normalized_brand = unicodedata.normalize("NFC", brand_name)
                normalized[normalized_brand] = {}
                for model_name, model_section in brand_section.items():
                    normalized_model = unicodedata.normalize("NFC", model_name)
                    normalized[normalized_brand][normalized_model] = model_section

        return normalized

    def _matcher_can_handle_combination(self, field: str, brand_name: str, model_name: str) -> bool:
        """Check if the matcher can actually handle this brand/model combination."""
        try:
            matcher = self._get_matcher(field)
            if not matcher:
                return False

            # Test if matcher can actually match this combination
            test_input = f"{brand_name} {model_name}"
            
            if field == "blade":
                # For blades, we need a format - use a common one for testing
                result = matcher.match_with_context(test_input, "DE")
            else:
                # For other fields, use the standard match method
                result = matcher.match(test_input)
            
            # Check if it matched
            if result and hasattr(result, "matched") and result.matched:
                return True
            
            # Also check if it's a dict with matched data (for backward compatibility)
            if isinstance(result, dict) and result.get("matched"):
                return True
            
            return False
        except Exception as e:
            logger.debug(f"Error testing matcher coverage for {brand_name} {model_name}: {e}")
            return False


def main():
    """Main entry point for CLI usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate correct_matches.yaml for catalog drift")
    parser.add_argument(
        "--field", choices=["razor", "blade", "brush", "soap"], help="Specific field to validate"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    validator = ValidateCorrectMatches()
    validator.run_validation(args.field)


if __name__ == "__main__":
    main()
