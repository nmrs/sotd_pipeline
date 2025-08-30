#!/usr/bin/env python3
"""Validation tool for detecting catalog drift in correct_matches.yaml."""

import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

# Add project root to Python path for direct execution
project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sotd.match.base_matcher import BaseMatcher
from sotd.match.blade_matcher import BladeMatcher
from sotd.match.brush_matcher import BrushMatcher
from sotd.match.razor_matcher import RazorMatcher
from sotd.match.soap_matcher import SoapMatcher
from sotd.match.correct_matches_updater import CorrectMatchesUpdater
from sotd.match.brush_scoring_config import BrushScoringConfig


# Compatibility layer for BrushMatcherConfig
class BrushMatcherConfig:
    def __init__(
        self, catalog_path=None, handles_path=None, knots_path=None, bypass_correct_matches=False
    ):
        self.catalog_path = catalog_path
        self.handles_path = handles_path
        self.knots_path = knots_path
        self.bypass_correct_matches = bypass_correct_matches


logger = logging.getLogger(__name__)


class ValidateCorrectMatches:
    """Validate correct_matches.yaml against current catalog patterns."""

    def __init__(self, correct_matches_path: Optional[Path] = None):
        """Initialize validation tool with all matchers."""
        print(f"🔍 INIT_DEBUG: ValidateCorrectMatches.__init__ called")
        print(f"🔍 INIT_DEBUG: correct_matches_path parameter: {correct_matches_path}")
        print(f"🔍 INIT_DEBUG: correct_matches_path type: {type(correct_matches_path)}")
        print(f"🔍 INIT_DEBUG: Current working directory: {Path.cwd()}")
        print(f"🔍 INIT_DEBUG: __file__: {__file__}")
        print(f"🔍 INIT_DEBUG: Project root: {project_root}")

        self.correct_matches_path = correct_matches_path or Path("data/correct_matches.yaml")
        print(f"🔍 INIT_DEBUG: Final correct_matches_path: {self.correct_matches_path}")
        print(f"🔍 INIT_DEBUG: Final path absolute: {self.correct_matches_path.absolute()}")
        print(f"🔍 INIT_DEBUG: Final path exists: {self.correct_matches_path.exists()}")

        self.correct_matches = self._load_correct_matches()

        # Don't initialize matchers upfront - lazy load them when needed
        self._matchers = {}

        # Initialize the updater for creating temp files
        self.updater = CorrectMatchesUpdater()

        # Performance optimization: Lazy-load normalized catalogs and validation cache
        self._normalized_catalogs = {}
        self._validation_cache = {}

        # Don't pre-compute validation structures - build them lazily when needed
        # This prevents errors during initialization for fields that aren't being validated

    @property
    def _data_dir(self):
        """Get the data directory for testing."""
        return getattr(self, "_data_dir_value", None)

    @_data_dir.setter
    def _data_dir(self, value):
        """Set the data directory and clear cache for testing."""
        self._data_dir_value = value
        if value is not None:
            self._clear_validation_cache()

    def _load_correct_matches(self) -> Dict[str, Any]:
        """Load correct_matches.yaml file."""
        print(f"🔍 LOAD_DEBUG: Starting to load correct_matches.yaml")
        print(f"🔍 LOAD_DEBUG: Self object ID: {id(self)}")
        print(f"🔍 LOAD_DEBUG: Self object type: {type(self)}")
        print(f"🔍 LOAD_DEBUG: Correct matches path: {self.correct_matches_path}")
        print(f"🔍 LOAD_DEBUG: Path type: {type(self.correct_matches_path)}")
        print(f"🔍 LOAD_DEBUG: Path absolute: {self.correct_matches_path.absolute()}")
        print(f"🔍 LOAD_DEBUG: Path exists: {self.correct_matches_path.exists()}")
        print(f"🔍 LOAD_DEBUG: Path is file: {self.correct_matches_path.is_file()}")
        print(f"🔍 LOAD_DEBUG: Path parent: {self.correct_matches_path.parent}")
        print(f"🔍 LOAD_DEBUG: Current working directory: {Path.cwd()}")
        print(f"🔍 LOAD_DEBUG: __file__: {__file__}")
        print(f"🔍 LOAD_DEBUG: Project root: {project_root}")

        if not self.correct_matches_path.exists():
            print(f"🔍 LOAD_DEBUG: File does not exist!")
            return {}

        try:
            import yaml

            print(f"🔍 LOAD_DEBUG: Opening file for reading...")
            with open(self.correct_matches_path, "r", encoding="utf-8") as f:
                print(f"🔍 LOAD_DEBUG: File opened successfully")
                data = yaml.safe_load(f)
                print(f"🔍 LOAD_DEBUG: YAML loaded, data type: {type(data)}")
                print(f"🔍 LOAD_DEBUG: Data keys: {list(data.keys()) if data else 'None'}")
                print(f"🔍 LOAD_DEBUG: Data length: {len(data) if data else 0}")
                if data and "brush" in data:
                    brush_data = data["brush"]
                    print(f"🔍 LOAD_DEBUG: Brush data type: {type(brush_data)}")
                    print(
                        f"🔍 LOAD_DEBUG: Brush data keys: {list(brush_data.keys()) if brush_data else 'None'}"
                    )
                    print(
                        f"🔍 LOAD_DEBUG: Brush data length: {len(brush_data) if brush_data else 0}"
                    )
                    if brush_data:
                        # Count total patterns in brush section
                        total_patterns = 0
                        for brand, models in brush_data.items():
                            if isinstance(models, dict):
                                for model, patterns in models.items():
                                    if isinstance(patterns, list):
                                        total_patterns += len(patterns)
                        print(f"🔍 LOAD_DEBUG: Total brush patterns: {total_patterns}")

                result = data if data else {}
                print(f"🔍 LOAD_DEBUG: Returning data with {len(result)} top-level keys")
                return result
        except Exception as e:
            print(f"🔍 LOAD_DEBUG: Error loading file: {e}")
            logger.error(f"Error loading correct_matches.yaml: {e}")
            return {}

    def _clear_field_cache(self, field: str):
        """Clear cache for a specific field only."""
        logger.info(f"Clearing cache for field: {field}")

        # Clear the specific field's catalog cache
        if hasattr(self, "_matchers") and field in self._matchers:
            del self._matchers[field]

        # Clear the specific field's YAML cache entry
        try:
            from sotd.match.loaders import _yaml_catalog_cache

            # The YAML cache uses absolute resolved paths as keys
            base_dir = self._data_dir or Path("data")
            if field == "razor":
                cache_key = str((base_dir / "razors.yaml").resolve())
            elif field == "blade":
                cache_key = str((base_dir / "blades.yaml").resolve())
            elif field == "brush":
                cache_key = str((base_dir / "brushes.yaml").resolve())
            elif field == "soap":
                cache_key = str((base_dir / "soaps.yaml").resolve())
            else:
                return

            if cache_key in _yaml_catalog_cache:
                del _yaml_catalog_cache[cache_key]
                logger.info(f"Cleared YAML cache for {cache_key}")
            else:
                logger.info(f"Cache key {cache_key} not found in YAML cache")

        except Exception as e:
            logger.warning(f"Could not clear YAML cache for field {field}: {e}")

    def _get_matcher(
        self, field: str
    ) -> Optional[BaseMatcher | BladeMatcher | BrushMatcher | RazorMatcher | SoapMatcher]:
        """Get the appropriate matcher for a field, always creating a fresh instance."""
        # Clear only this field's cache for targeted performance
        self._clear_field_cache(field)

        # Always create a fresh matcher instance to avoid caching issues
        logger.info(f"Creating fresh matcher for field: {field}")

        # Use _data_dir if set (for testing), otherwise use default data/ directory
        base_dir = self._data_dir or Path("data")

        if field == "razor":
            return RazorMatcher(catalog_path=base_dir / "razors.yaml")
        elif field == "blade":
            return BladeMatcher(catalog_path=base_dir / "blades.yaml")
        elif field == "brush":
            # For brush field, use BrushMatcher with default paths (same as working analyzer)
            # This fixes the issue where hardcoded paths were causing "None" results
            return BrushMatcher()
        elif field == "soap":
            return SoapMatcher(catalog_path=base_dir / "soaps.yaml")
        elif field in ["knot", "handle"]:
            # For brush-related fields, use BrushMatcher with default paths (same as working analyzer)
            # This fixes the issue where hardcoded paths were causing "None" results
            return BrushMatcher()

        return None

    def _clear_validation_cache(self):
        """Clear validation cache when _data_dir is set for testing."""
        self._validation_cache.clear()
        self._normalized_catalogs.clear()
        self._matchers.clear()

        # Clear individual matcher caches to ensure fresh validation
        for matcher in self._matchers.values():
            if hasattr(matcher, "clear_cache"):
                matcher.clear_cache()

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
            # Create matcher once outside the loop for performance
            blade_matcher = self._get_matcher("blade")

            for format_name, format_section in field_section.items():
                expected_structure[field][format_name] = {}

                for brand_name, brand_section in format_section.items():
                    expected_structure[field][format_name][brand_name] = {}

                    for model_name, model_section in brand_section.items():
                        expected_structure[field][format_name][brand_name][model_name] = []

                        if isinstance(model_section, list):
                            for pattern in model_section:
                                # Use context-aware matching for blades
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
            # Create matcher once outside the loop for performance
            matcher = self._get_matcher(field)

            for brand_name, brand_section in field_section.items():
                expected_structure[field][brand_name] = {}

                for model_name, model_section in brand_section.items():
                    expected_structure[field][brand_name][model_name] = []

                    if isinstance(model_section, list):
                        for pattern in model_section:
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
                            else:
                                # Fallback to original location if no matcher
                                expected_structure[field][brand_name][model_name].append(pattern)

        return expected_structure

    def _validate_catalog_existence(
        self, field: str, original: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Validate that entries in correct_matches.yaml can be matched by actual matchers."""
        print(f"🔍 _VALIDATE_CATALOG_EXISTENCE DEBUG: Starting validation for field: {field}")
        print(f"🔍 _VALIDATE_CATALOG_EXISTENCE DEBUG: Original parameter type: {type(original)}")
        print(
            f"🔍 _VALIDATE_CATALOG_EXISTENCE DEBUG: Original parameter keys: {list(original.keys()) if original else 'None'}"
        )
        print(
            f"🔍 _VALIDATE_CATALOG_EXISTENCE DEBUG: Field {field} in original: {field in original if original else False}"
        )

        issues = []

        if field not in original:
            print(
                f"🔍 _VALIDATE_CATALOG_EXISTENCE DEBUG: Field {field} not in original, returning empty issues"
            )
            return issues

        print(f"🔍 _VALIDATE_CATALOG_EXISTENCE DEBUG: Field {field} found in original")
        print(
            f"🔍 _VALIDATE_CATALOG_EXISTENCE DEBUG: Original[{field}] type: {type(original[field])}"
        )
        print(
            f"🔍 _VALIDATE_CATALOG_EXISTENCE DEBUG: Original[{field}] length: {len(original[field]) if isinstance(original[field], dict) else 'Not a dict'}"
        )

        # For blades, first check for format mismatches between correct_matches.yaml and catalog
        if field == "blade":
            format_mismatch_issues = self._validate_blade_format_consistency(original[field])
            issues.extend(format_mismatch_issues)

        # Ensure matcher is available (lazy-load if needed)
        print(f"🔍 _VALIDATE_CATALOG_EXISTENCE DEBUG: About to get matcher for field: {field}")
        matcher = self._get_matcher(field)
        print(f"🔍 _VALIDATE_CATALOG_EXISTENCE DEBUG: Matcher type: {type(matcher)}")
        print(
            f"🔍 _VALIDATE_CATALOG_EXISTENCE DEBUG: Matcher object ID: {id(matcher) if matcher else 'None'}"
        )

        if not matcher:
            logger.warning(f"No matcher available for field: {field}")
            print(
                f"🔍 _VALIDATE_CATALOG_EXISTENCE DEBUG: No matcher available, returning {len(issues)} issues"
            )
            return issues

        original_section = original[field]
        logger.info(f"Processing {field} section: {type(original_section)}")
        logger.info(
            f"Section keys: {list(original_section.keys()) if isinstance(original_section, dict) else 'Not a dict'}"
        )
        print(
            f"🔍 _VALIDATE_CATALOG_EXISTENCE DEBUG: Original section type: {type(original_section)}"
        )
        print(
            f"🔍 _VALIDATE_CATALOG_EXISTENCE DEBUG: Original section keys: {list(original_section.keys()) if isinstance(original_section, dict) else 'Not a dict'}"
        )
        print(
            f"🔍 _VALIDATE_CATALOG_EXISTENCE DEBUG: Original section length: {len(original_section) if isinstance(original_section, dict) else 'Not a dict'}"
        )

        # Debug: Check if we have the problematic entries
        if field == "brush" and "Chisel & Hound" in original_section:
            ch_hound_section = original_section["Chisel & Hound"]
            logger.info(f"Chisel & Hound section: {type(ch_hound_section)}")
            logger.info(
                f"Chisel & Hound keys: {list(ch_hound_section.keys()) if isinstance(ch_hound_section, dict) else 'Not a dict'}"
            )

            if "v26" in ch_hound_section:
                v26_patterns = original_section["Chisel & Hound"]["v26"]
                logger.info(f"v26 patterns: {v26_patterns}")
                if isinstance(v26_patterns, list):
                    for pattern in v26_patterns:
                        if "v27" in pattern.lower():
                            logger.info(f"Found v27 pattern in v26 section: {pattern}")

        if field == "blade":
            # For blades: test each individual pattern in each format
            for format_name in original_section:
                for brand_name in original_section[format_name]:
                    for model_name in original_section[format_name][brand_name]:
                        if isinstance(original_section[format_name][brand_name][model_name], list):
                            # Test each individual pattern in the list
                            for pattern in original_section[format_name][brand_name][model_name]:
                                logger.debug(
                                    f"Testing blade pattern: '{pattern}' in format '{format_name}' under '{brand_name} {model_name}'"
                                )
                                result = self._test_matcher_entry_with_format(
                                    matcher, pattern, field, format_name, brand_name, model_name
                                )
                                if result:
                                    logger.debug(f"Found issue: {result}")
                                    issues.append(result)
                        else:
                            # Fallback: test brand+model combination
                            test_text = f"{brand_name} {model_name}"
                            logger.debug(
                                f"Testing blade fallback: '{test_text}' in format '{format_name}'"
                            )
                            result = self._test_matcher_entry_with_format(
                                matcher, test_text, field, format_name, brand_name, model_name
                            )
                            if result:
                                logger.debug(f"Found issue: {result}")
                                issues.append(result)
        elif field == "brush":
            # For brushes: test each individual pattern string, not the organizational structure
            logger.info(f"Processing {field} section with {len(original_section)} brands")
            total_patterns = 0
            processed_patterns = 0
            print(
                f"🔍 _VALIDATE_CATALOG_EXISTENCE DEBUG: Processing brush section with {len(original_section)} brands"
            )
            for brand_name in original_section:
                logger.info(f"  Processing brand: {brand_name}")
                print(f"🔍 _VALIDATE_CATALOG_EXISTENCE DEBUG: Processing brand: {brand_name}")
                for version_name in original_section[brand_name]:
                    logger.info(f"    Processing version: {version_name}")
                    print(
                        f"🔍 _VALIDATE_CATALOG_EXISTENCE DEBUG: Processing version: {version_name}"
                    )
                    if isinstance(original_section[brand_name][version_name], list):
                        patterns = original_section[brand_name][version_name]
                        total_patterns += len(patterns)
                        logger.info(f"      Found {len(patterns)} patterns")
                        print(
                            f"🔍 _VALIDATE_CATALOG_EXISTENCE DEBUG: Found {len(patterns)} patterns for {brand_name} {version_name}"
                        )
                        # Test each individual pattern string
                        for pattern in patterns:
                            logger.info(f"        Testing pattern: {pattern}")
                            processed_patterns += 1
                            try:
                                result = self._test_brush_pattern(
                                    matcher, pattern, field, brand_name, version_name
                                )
                                if result:
                                    logger.info(f"        Found issue: {result}")
                                    issues.append(result)
                                else:
                                    logger.info(f"        No issue found")
                            except Exception as e:
                                logger.error(f"        Error testing pattern: {e}")
                                # Add error as an issue
                                issues.append(
                                    {
                                        "type": "validation_error",
                                        "field": field,
                                        "brand": brand_name,
                                        "version": version_name,
                                        "pattern": pattern,
                                        "message": f"Error testing pattern: {str(e)}",
                                    }
                                )
                    else:
                        # Fallback: test the version string itself
                        test_text = f"{brand_name} {version_name}"
                        total_patterns += 1
                        processed_patterns += 1
                        result = self._test_brush_pattern(
                            matcher, test_text, field, brand_name, version_name
                        )
                        if result:
                            issues.append(result)

            logger.info(
                f"Brush validation complete: processed {processed_patterns} patterns out of {total_patterns} total patterns"
            )
            logger.info(f"Found {len(issues)} issues")
        else:
            # For other fields: test each individual pattern
            logger.info(f"Processing {field} section with {len(original_section)} brands")
            for brand_name in original_section:
                logger.info(f"  Processing brand: {brand_name}")
                for model_name in original_section[brand_name]:
                    logger.info(f"    Processing model: {model_name}")
                    if isinstance(original_section[brand_name][model_name], list):
                        patterns = original_section[brand_name][model_name]
                        logger.info(f"      Found {len(patterns)} patterns")
                        # Test each individual pattern in the list
                        for pattern in patterns:
                            logger.info(f"        Testing pattern: {pattern}")
                            try:
                                result = self._test_matcher_entry(
                                    matcher, pattern, field, brand_name, model_name
                                )
                                if result:
                                    logger.info(f"        Found issue: {result}")
                                    issues.append(result)
                                else:
                                    logger.info(f"        No issue found")
                            except Exception as e:
                                logger.error(f"        Error testing pattern: {e}")
                                # Add error as an issue
                                issues.append(
                                    {
                                        "type": "validation_error",
                                        "field": field,
                                        "brand": brand_name,
                                        "model": model_name,
                                        "pattern": pattern,
                                        "message": f"Error testing pattern: {str(e)}",
                                    }
                                )
                    else:
                        # Fallback: test brand+model combination
                        test_text = f"{brand_name} {model_name}"
                        result = self._test_matcher_entry(
                            matcher, test_text, field, brand_name, model_name
                        )
                        if result:
                            issues.append(result)

        print(
            f"🔍 _VALIDATE_CATALOG_EXISTENCE DEBUG: Final result - returning {len(issues)} issues"
        )
        print(
            f"🔍 _VALIDATE_CATALOG_EXISTENCE DEBUG: First few issues: {issues[:3] if issues else 'No issues'}"
        )
        return issues

    def _validate_blade_format_consistency(
        self, blade_section: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Validate that blade formats in correct_matches.yaml match the catalog."""
        issues = []

        try:
            # Load the blade catalog
            catalog_path = (
                self._data_dir / "blades.yaml" if self._data_dir else Path("data/blades.yaml")
            )
            if not catalog_path.exists():
                logger.warning(f"Blade catalog not found at {catalog_path}")
                return issues

            with open(catalog_path, "r", encoding="utf-8") as f:
                catalog_data = yaml.safe_load(f)

            if not catalog_data:
                return issues

            # Check each format in correct_matches.yaml
            for correct_format, brands in blade_section.items():
                if not isinstance(brands, dict):
                    continue

                for brand_name, models in brands.items():
                    if not isinstance(models, dict):
                        continue

                    for model_name in models:
                        # Check if this brand/model exists in the catalog under the same format
                        catalog_format = self._find_blade_catalog_format(
                            catalog_data, brand_name, model_name
                        )

                        if catalog_format and catalog_format != correct_format:
                            # Format mismatch detected
                            issues.append(
                                {
                                    "type": "format_mismatch",
                                    "field": "blade",
                                    "format": correct_format,
                                    "brand": brand_name,
                                    "model": model_name,
                                    "catalog_format": catalog_format,
                                    "correct_match": f"{brand_name} {model_name}",
                                    "message": (
                                        f"Blade '{brand_name} {model_name}' is listed under "
                                        f"format '{correct_format}' in correct_matches.yaml but "
                                        f"found under format '{catalog_format}' in catalog"
                                    ),
                                }
                            )

        except Exception as e:
            logger.error(f"Error validating blade format consistency: {e}")

        return issues

    def _find_blade_catalog_format(
        self, catalog_data: Dict[str, Any], brand_name: str, model_name: str
    ) -> Optional[str]:
        """Find which format a blade brand/model is listed under in the catalog."""
        for format_name, format_section in catalog_data.items():
            if not isinstance(format_section, dict):
                continue

            for catalog_brand, brand_section in format_section.items():
                if not isinstance(brand_section, dict):
                    continue

                # Check if brand names match (case-insensitive)
                if catalog_brand.lower() == brand_name.lower():
                    # Check if model exists under this brand
                    for catalog_model in brand_section.keys():
                        if catalog_model.lower() == model_name.lower():
                            return format_name

        return None

    def _test_matcher_entry(
        self, matcher, test_text: str, field: str, *args
    ) -> Optional[Dict[str, Any]]:
        """Test if an entry can be matched by the actual matcher."""
        try:
            # Use the actual matcher to test the entry
            # Different matchers expect different input formats
            if field == "razor":
                # RazorMatcher expects: match(normalized_text, original_text=None)
                result = matcher.match(test_text.lower(), test_text)
            elif field == "blade":
                # BladeMatcher expects: match_with_context(normalized_text, format_name)
                # for format-aware matching
                if hasattr(matcher, "match_with_context"):
                    result = matcher.match_with_context(
                        test_text.lower(), format_name, strict_format=True
                    )
                else:
                    result = matcher.match(test_text.lower(), test_text)
            elif field == "soap":
                # SoapMatcher expects: match(normalized_text, original_text=None)
                result = matcher.match(test_text.lower(), test_text)
            elif field == "brush":
                # BrushMatcher expects: match(text_string) - NOT a dictionary
                # The matcher handles normalization internally
                result = matcher.match(test_text)
            else:
                # Default fallback
                result = matcher.match(test_text.lower(), test_text)

            if not result or not hasattr(result, "matched") or not result.matched:
                # Entry doesn't match at all - this is a validation issue
                if field == "blade" and len(args) >= 3:
                    format_name, brand_name, model_name = args[0], args[1], args[2]
                    return {
                        "type": "unmatchable_entry",
                        "field": field,
                        "format": format_name,
                        "brand": brand_name,
                        "model": model_name,
                        "pattern": test_text,
                        "message": f"Entry '{test_text}' cannot be matched by {field} matcher",
                    }
                else:
                    brand_name, model_name = args[0], args[1]
                    return {
                        "type": "unmatchable_entry",
                        "field": field,
                        "brand": brand_name,
                        "model": model_name,
                        "pattern": test_text,
                        "message": f"Entry '{test_text}' cannot be matched by {field} matcher",
                    }

            # Check if the matcher returned the expected brand/model
            if hasattr(result, "matched") and result.matched:
                matched_data = result.matched
                actual_brand = matched_data.get("brand")
                actual_model = matched_data.get("model")

                if field == "blade" and len(args) >= 3:
                    expected_format, expected_brand, expected_model = args[0], args[1], args[2]
                    if actual_brand != expected_brand or actual_model != expected_model:
                        return {
                            "type": "mismatched_result",
                            "field": field,
                            "format": expected_format,
                            "brand": expected_brand,
                            "model": expected_model,
                            "pattern": test_text,
                            "actual_brand": actual_brand or "Unknown",
                            "actual_model": actual_model or "Unknown",
                            "matched_pattern": getattr(result, "pattern", "Unknown pattern"),
                            "message": (
                                f"Entry '{test_text}' matched to '{actual_brand or 'Unknown'} {actual_model or 'Unknown'}' "
                                f"instead of expected '{expected_brand} {expected_model}'"
                            ),
                        }
                elif len(args) >= 2:
                    expected_brand, expected_model = args[0], args[1]
                    if actual_brand != expected_brand or actual_model != expected_model:
                        return {
                            "type": "mismatched_result",
                            "field": field,
                            "brand": expected_brand,
                            "model": expected_model,
                            "pattern": test_text,
                            "actual_brand": actual_brand,
                            "actual_model": actual_model,
                            "matched_pattern": getattr(result, "pattern", "Unknown pattern"),
                            "message": (
                                f"Entry '{test_text}' matched to '{actual_brand} {actual_model}' "
                                f"instead of expected '{expected_brand} {expected_model}'"
                            ),
                        }

            # Entry matches successfully and returns expected brand/model - no issue
            return None

        except Exception as e:
            # Matcher error - this indicates a problem
            logger.error(f"Error testing entry '{test_text}' with {field} matcher: {e}")
            return {
                "type": "matcher_error",
                "field": field,
                "pattern": test_text,
                "message": f"Error testing entry '{test_text}' with {field} matcher: {str(e)}",
            }

    def _test_matcher_entry_with_format(
        self, matcher, test_text: str, field: str, format_name: str, *args
    ) -> Optional[Dict[str, Any]]:
        """Test if an entry can be matched by the actual matcher with format context."""
        try:
            # Use the actual matcher to test the entry
            # Different matchers expect different input formats
            if field == "razor":
                # RazorMatcher expects: match(normalized_text, original_text=None)
                result = matcher.match(test_text.lower(), test_text)
            elif field == "blade":
                # BladeMatcher expects: match_with_context(normalized_text, format_name)
                # for format-aware matching
                if hasattr(matcher, "match_with_context"):
                    result = matcher.match_with_context(test_text.lower(), format_name)
                else:
                    result = matcher.match(test_text.lower(), test_text)
            elif field == "soap":
                # SoapMatcher expects: match(normalized_text, original_text=None)
                result = matcher.match(test_text.lower(), test_text)
            elif field == "brush":
                # BrushMatcher expects: match(text_string) - NOT a dictionary
                # The matcher handles normalization internally
                result = matcher.match(test_text)
            else:
                # Default fallback
                result = matcher.match(test_text.lower(), test_text)

            if not result:
                # Entry doesn't match at all - this is a validation issue
                if field == "blade" and len(args) >= 2:
                    brand_name, model_name = args[0], args[1]
                    return {
                        "type": "unmatchable_entry",
                        "field": field,
                        "format": format_name,
                        "brand": brand_name,
                        "model": model_name,
                        "pattern": test_text,
                        "message": f"Entry '{test_text}' cannot be matched by {field} matcher with format '{format_name}'",
                    }
                elif len(args) >= 2:
                    brand_name, model_name = args[0], args[1]
                    return {
                        "type": "unmatchable_entry",
                        "field": field,
                        "brand": brand_name,
                        "model": model_name,
                        "pattern": test_text,
                        "message": f"Entry '{test_text}' cannot be matched by {field} matcher with format '{format_name}'",
                    }

            # Check if the matcher returned the expected brand/model
            if hasattr(result, "matched") and result.matched:
                matched_data = result.matched
                actual_brand = matched_data.get("brand")
                actual_model = matched_data.get("model")

                if field == "blade" and len(args) >= 2:
                    expected_brand, expected_model = args[0], args[1]
                    if actual_brand != expected_brand or actual_model != expected_model:
                        return {
                            "type": "mismatched_result",
                            "field": field,
                            "format": format_name,
                            "brand": expected_brand,
                            "model": expected_model,
                            "pattern": test_text,
                            "actual_brand": actual_brand,
                            "actual_model": actual_model,
                            "message": f"Entry '{test_text}' matched to '{actual_brand} {actual_model}' instead of expected '{expected_brand} {expected_model}' with format '{format_name}'",
                        }
                elif len(args) >= 2:
                    expected_brand, expected_model = args[0], args[1]
                    if actual_brand != expected_brand or actual_model != expected_model:
                        return {
                            "type": "mismatched_result",
                            "field": field,
                            "brand": expected_brand,
                            "model": expected_model,
                            "pattern": test_text,
                            "actual_brand": actual_brand,
                            "actual_model": actual_model,
                            "message": f"Entry '{test_text}' matched to '{actual_brand} {expected_model}' instead of expected '{expected_brand} {expected_model}' with format '{format_name}'",
                        }

            # Entry matches successfully and returns expected brand/model - no issue
            return None

        except Exception as e:
            # Matcher error - this indicates a problem
            logger.error(
                f"Error testing entry '{test_text}' with {field} matcher with format '{format_name}': {e}"
            )
            return {
                "type": "matcher_error",
                "field": field,
                "format": format_name,
                "pattern": test_text,
                "message": f"Error testing entry '{test_text}' with {field} matcher with format '{format_name}': {str(e)}",
            }

    def _test_brush_pattern(
        self, matcher, test_text: str, field: str, brand_name: str, version_name: str
    ) -> Optional[Dict[str, Any]]:
        """Test if a brush pattern can be matched by the brush matcher."""
        print(f"🔍 DEBUG: Testing brush pattern: '{test_text}'")
        print(f"🔍 DEBUG: Expected brand: '{brand_name}', model: '{version_name}'")

        try:
            # CRITICAL: Use the same matcher instance but with bypass parameter
            # This eliminates the need to create separate matcher instances
            print(f"🔍 DEBUG: Testing with bypass parameter...")
            bypass_result = matcher.match(test_text, bypass_correct_matches=True)

            if (
                not bypass_result
                or not hasattr(bypass_result, "matched")
                or not bypass_result.matched
            ):
                print(f"🔍 DEBUG: ❌ Bypass matcher found no match")
                return {
                    "type": "catalog_pattern_no_match",
                    "pattern": test_text,
                    "message": f"Pattern '{test_text}' cannot be matched by brush matcher",
                    "details": f"Bypass matcher found no match for '{test_text}'",
                    "suggested_action": f"Pattern '{test_text}' may need to be updated or removed from correct_matches.yaml",
                    "expected_brand": brand_name,
                    "expected_model": version_name,
                    "actual_brand": None,
                    "actual_model": None,
                }

            # Extract brand and model from the bypass result
            bypass_brand = bypass_result.matched.get("brand")
            bypass_model = bypass_result.matched.get("model")

            # For brush matcher, handle the nested structure and validate brand/model
            if field == "brush":
                # Extract brand and model from the nested structure
                handle_brand = bypass_result.matched.get("handle", {}).get("brand")
                knot_brand = bypass_result.matched.get("knot", {}).get("brand")

                # Use handle brand if available, otherwise knot brand
                if handle_brand:
                    bypass_brand = handle_brand
                elif knot_brand:
                    bypass_brand = knot_brand

                # For model, try to get it from handle or knot
                handle_model = bypass_result.matched.get("handle", {}).get("model")
                knot_model = bypass_result.matched.get("knot", {}).get("model")

                if handle_model and handle_model != "Unspecified":
                    bypass_model = handle_model
                elif knot_model:
                    bypass_model = knot_model

            print(f"🔍 DEBUG: Bypass result - Brand: '{bypass_brand}', Model: '{bypass_model}'")

            # NOW validate: does the bypass result match where it's stored in correct_matches.yaml?
            if bypass_brand != brand_name:
                print(
                    f"🔍 DEBUG: ❌ BRAND MISMATCH! Bypass thinks '{bypass_brand}', stored under '{brand_name}'"
                )
                return {
                    "type": "catalog_pattern_mismatch",
                    "pattern": test_text,
                    "message": f"Pattern '{test_text}' is stored under wrong brand",
                    "details": f"Pattern mentions '{bypass_brand}' but is stored under '{brand_name}' section",
                    "suggested_action": f"Move pattern '{test_text}' from '{brand_name}' to '{bypass_brand}' section",
                    "expected_brand": brand_name,
                    "expected_model": version_name,
                    "actual_brand": bypass_brand,
                    "actual_model": bypass_model,
                }

            if bypass_model != version_name:
                print(
                    f"🔍 DEBUG: ❌ MODEL MISMATCH! Bypass thinks '{bypass_model}', stored under '{version_name}'"
                )
                return {
                    "type": "catalog_pattern_mismatch",
                    "pattern": test_text,
                    "message": f"Pattern '{test_text}' is stored under wrong model",
                    "details": f"Pattern mentions '{bypass_model}' but is stored under '{version_name}' section",
                    "suggested_action": f"Move pattern '{test_text}' from '{brand_name} {version_name}' to '{bypass_brand} {bypass_model}' section",
                    "expected_brand": brand_name,
                    "expected_model": version_name,
                    "actual_brand": bypass_brand,
                    "actual_model": bypass_model,
                }

            print(
                f"🔍 DEBUG: ✅ Pattern validation successful - stored location matches bypass result"
            )
            return None  # No issues

        except Exception as e:
            print(f"🔍 DEBUG: ❌ Exception during bypass validation: {e}")
            return {
                "type": "unmatchable_entry",
                "pattern": test_text,
                "message": f"Pattern '{test_text}' caused exception during bypass validation",
                "details": f"Exception: {e}",
                "suggested_action": f"Investigate exception in bypass validation for '{test_text}'",
                "expected_brand": brand_name,
                "expected_model": version_name,
                "actual_brand": None,
                "actual_model": None,
            }

    def _check_brush_model_mismatch(
        self, test_text: str, brand_name: str, stored_model: str, result
    ) -> Optional[Dict[str, Any]]:
        """Check if the pattern contains a model name that doesn't match where it's stored."""
        # Look for model names in the pattern text (e.g., "v27", "v26", "B13")
        import re

        # Common model name patterns
        model_patterns = [
            r"\bv\d+\b",  # v27, v26, v25, etc.
            r"\bB\d+\b",  # B13, B14, etc.
            r"\b[A-Z]\d+\b",  # Other letter+number patterns
        ]

        found_models = []
        for pattern in model_patterns:
            matches = re.findall(pattern, test_text, re.IGNORECASE)
            found_models.extend(matches)

        # Check if any found model names don't match the stored model
        for found_model in found_models:
            if found_model.lower() != stored_model.lower():
                # Get the actual matched data from the result
                actual_brand = None
                actual_model = None
                if hasattr(result, "matched") and result.matched:
                    actual_brand = result.matched.get("brand")
                    actual_model = result.matched.get("model")

                return {
                    "type": "catalog_pattern_mismatch",
                    "field": "brush",
                    "pattern": test_text,
                    "stored_brand": brand_name,
                    "stored_model": stored_model,
                    "matched_brand": actual_brand or "Unknown",
                    "matched_model": actual_model or "Unknown",
                    "message": f"Pattern '{test_text}' is stored under '{brand_name} {stored_model}' but contains model name '{found_model}'",
                    "suggested_action": f"Move from '{brand_name} {stored_model}' to '{brand_name} {found_model}' in correct_matches.yaml",
                }

        return None

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
            base_dir = self._data_dir or Path("data")

            if field == "blade":
                catalog_path = base_dir / "blades.yaml"
            elif field == "brush":
                catalog_path = base_dir / "brushes.yaml"
            elif field == "razor":
                catalog_path = base_dir / "razors.yaml"
            elif field == "soap":
                catalog_path = base_dir / "soaps.yaml"
            elif field == "handle":
                catalog_path = base_dir / "handles.yaml"
            elif field == "knot":
                catalog_path = base_dir / "knots.yaml"
            else:
                return {}

            if not catalog_path.exists():
                return {}

            import yaml

            with open(catalog_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Error loading catalog data for field {field}: {e}")
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

                    # Check patterns - SKIP for handle and knot fields since these are composite references
                    if field not in ["handle", "knot"]:
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

    def validate_field(
        self, field: str, create_expected_structure: bool = False
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Validate a specific field for catalog drift using real matchers."""
        print(f"🔍 VALIDATE_FIELD DEBUG: Starting validation for field: {field}")
        print(f"🔍 VALIDATE_FIELD DEBUG: Self object ID: {id(self)}")
        print(f"🔍 VALIDATE_FIELD DEBUG: Self object type: {type(self)}")
        print(
            f"🔍 VALIDATE_FIELD DEBUG: Correct matches keys: {list(self.correct_matches.keys()) if self.correct_matches else 'None'}"
        )
        print(
            f"🔍 VALIDATE_FIELD DEBUG: Correct matches length: {len(self.correct_matches) if self.correct_matches else 0}"
        )

        if field not in self.correct_matches:
            print(
                f"🔍 VALIDATE_FIELD DEBUG: Field {field} not found in correct_matches, returning empty"
            )
            return [], {}

        print(f"🔍 VALIDATE_FIELD DEBUG: Field {field} found in correct_matches")
        print(
            f"🔍 VALIDATE_FIELD DEBUG: Field {field} has {len(self.correct_matches[field])} entries"
        )

        logger.info(f"Validating field: {field}")

        # Clear ALL caches to force fresh validation (DRY principle)
        print(f"🔍 VALIDATE_FIELD DEBUG: About to clear caches...")
        self._clear_validation_cache()
        self._matchers.clear()

        # Debug: Log that we're clearing caches
        logger.info(f"Cleared ALL caches for field: {field}")
        logger.info(f"Matcher cache size: {len(self._matchers)}")
        logger.info(f"Validation cache size: {len(self._validation_cache)}")
        print(
            f"🔍 VALIDATE_FIELD DEBUG: After clearing - Matcher cache size: {len(self._matchers)}"
        )
        print(
            f"🔍 VALIDATE_FIELD DEBUG: After clearing - Validation cache size: {len(self._validation_cache)}"
        )

        # Use real matchers to validate entries (DRY approach)
        print(f"🔍 VALIDATE_FIELD DEBUG: About to call _validate_catalog_existence...")
        catalog_issues = self._validate_catalog_existence(field, self.correct_matches)
        print(
            f"🔍 VALIDATE_FIELD DEBUG: _validate_catalog_existence returned {len(catalog_issues)} issues"
        )
        print(
            f"🔍 VALIDATE_FIELD DEBUG: First few issues: {catalog_issues[:3] if catalog_issues else 'No issues'}"
        )

        # Create expected structure only if requested (skip for performance when not needed)
        expected_structure = {}
        if create_expected_structure:
            expected_structure = self._create_temp_correct_matches(field, self.correct_matches)
            logger.info(f"Created expected structure for {field}")
        else:
            logger.info(
                f"Skipped expected structure creation for {field} (performance optimization)"
            )

        # No need for manual structure comparison since we're using real matchers
        # The real matchers already tell us if entries can be matched or not

        print(
            f"🔍 VALIDATE_FIELD DEBUG: Returning {len(catalog_issues)} issues and {len(expected_structure)} expected structure entries"
        )
        return catalog_issues, expected_structure

    def validate_all_fields(self) -> Dict[str, List[Dict[str, Any]]]:
        """Validate all fields for catalog drift."""
        all_issues = {}

        for field in ["razor", "blade", "brush", "soap", "handle", "knot"]:
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

    def run_validation_cli(
        self, field: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        CLI interface for validation that follows DRY principles.

        This method provides the same validation logic as the API endpoint,
        ensuring consistent results between CLI and API calls.

        Args:
            field: Optional field to validate. If None, validates all fields.

        Returns:
            Tuple of (issues, expected_structure) for programmatic use
        """
        if field:
            issues, expected_structure = self.validate_field(field)
            self._report_issues(field, issues, expected_structure)
            return issues, expected_structure
        else:
            all_issues = self.validate_all_fields()
            self._report_all_issues(all_issues)
            # For CLI, return aggregated issues
            all_issues_list = []
            for field_issues in all_issues.values():
                all_issues_list.extend(field_issues)
            return all_issues_list, {}

    def validate_field_cli(self, field: str) -> List[Dict[str, Any]]:
        """
        CLI-specific field validation that returns only the issues.

        This method provides the same validation logic as validate_field()
        but is optimized for CLI usage where expected_structure is not needed.

        Args:
            field: Field to validate

        Returns:
            List of validation issues
        """
        issues, _ = self.validate_field(field)
        return issues

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
            for issue in issues:  # Show ALL issues per field - no truncation
                print(f"   • {issue['message']}")
            print()

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
        import copy
        import unicodedata

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
            # LINEAR FALLBACK: Include BOTH known_brushes AND other_brushes for validation
            # This matches how BrushMatcher actually works - it tries known_brushes first, then other_brushes
            for section_name in ["known_brushes", "other_brushes"]:
                if section_name in catalog_data:
                    for brand_name, brand_section in catalog_data[section_name].items():
                        normalized_brand = unicodedata.normalize("NFC", brand_name)
                        # If brand already exists from previous section, merge models
                        if normalized_brand not in normalized:
                            normalized[normalized_brand] = {}

                        for model_name, model_section in brand_section.items():
                            normalized_model = unicodedata.normalize("NFC", model_name)
                            normalized[normalized_brand][normalized_model] = model_section
        elif "artisan_handles" in catalog_data:  # Handle format with nested structure
            # LINEAR FALLBACK: Include ALL handle sections for validation
            # This matches how HandleMatcher actually works
            for section_name in ["artisan_handles", "manufacturer_handles", "other_handles"]:
                if section_name in catalog_data:
                    for brand_name, brand_section in catalog_data[section_name].items():
                        normalized_brand = unicodedata.normalize("NFC", brand_name)
                        # If brand already exists from previous section, merge models
                        if normalized_brand not in normalized:
                            normalized[normalized_brand] = {}

                        for model_name, model_section in brand_section.items():
                            normalized_model = unicodedata.normalize("NFC", model_name)
                            normalized[normalized_brand][normalized_model] = model_section
        elif "known_knots" in catalog_data:  # Knot format with nested structure
            # LINEAR FALLBACK: Include BOTH known_knots AND other_knots for validation
            # This matches how KnotMatcher actually works
            for section_name in ["known_knots", "other_knots"]:
                if section_name in catalog_data:
                    for brand_name, brand_section in catalog_data[section_name].items():
                        normalized_brand = unicodedata.normalize("NFC", brand_name)
                        # If brand already exists from previous section, merge models
                        if normalized_brand not in normalized:
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
            elif field == "handle":
                # Use the handle matcher component
                result = matcher.handle_matcher.match(test_input)
            elif field == "knot":
                # Use the knot matcher component
                result = matcher.knot_matcher.match(test_input)
            else:
                # For other fields (brush, razor, soap), use the standard match method
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
        "--field",
        choices=["razor", "blade", "brush", "soap", "handle", "knot"],
        help="Specific field to validate",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    validator = ValidateCorrectMatches()
    validator.run_validation(args.field)


if __name__ == "__main__":
    main()
