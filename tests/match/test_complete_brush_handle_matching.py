"""Test complete brush handle matching functionality."""

import yaml

from sotd.match.config import BrushMatcherConfig
from sotd.match.brush_matcher import BrushMatcher


class TestCompleteBrushHandleMatching:
    """Test the complete brush handle matching functionality."""

    def test_handle_matching_enabled_at_brand_level(self, tmp_path):
        """Test that handle matching works when enabled at brand level."""
        # Create test catalog with handle_matching at brand level
        catalog_data = {
            "known_brushes": {
                "Declaration Grooming": {
                    "handle_matching": True,
                    "B15": {
                        "patterns": ["(declaration|\\bdg\\b).*\\bb15\\b"],
                        "fiber": "Badger",
                        "knot_size_mm": 28,
                    },
                }
            },
            "other_brushes": {},
        }

        # Create handles catalog with Declaration Grooming handles
        handles_data = {
            "artisan_handles": {
                "Declaration Grooming": {
                    "Washington": {
                        "patterns": ["washington"],
                    },
                    "Jefferson": {
                        "patterns": ["jefferson"],
                    },
                }
            },
            "manufacturer_handles": {},
            "other_handles": {},
        }

        # Create minimal knots catalog
        knots_data = {"known_knots": {}, "other_knots": {}}
        correct_matches_data = {"brush": {}, "handle": {}, "knot": {}, "split_brush": {}}

        catalog_path = tmp_path / "brushes.yaml"
        handles_path = tmp_path / "handles.yaml"
        knots_path = tmp_path / "knots.yaml"
        correct_matches_path = tmp_path / "correct_matches.yaml"

        with catalog_path.open("w", encoding="utf-8") as f:
            yaml.dump(catalog_data, f)
        with handles_path.open("w", encoding="utf-8") as f:
            yaml.dump(handles_data, f)
        with knots_path.open("w", encoding="utf-8") as f:
            yaml.dump(knots_data, f)
        with correct_matches_path.open("w", encoding="utf-8") as f:
            yaml.dump(correct_matches_data, f)

        # Create brush matcher
        config = BrushMatcherConfig.create_custom(
            catalog_path=catalog_path,
            handles_path=handles_path,
            knots_path=knots_path,
            correct_matches_path=correct_matches_path,
        )
        matcher = BrushMatcher(config)

        # Test that handle matching is enabled for B15
        assert matcher._is_handle_matching_enabled("Declaration Grooming", "B15") is True

        # Test matching a brush with Washington handle
        result = matcher.match("DG B15 Washington")
        assert result is not None
        assert result.matched is not None
        assert result.matched["brand"] == "Declaration Grooming"
        assert result.matched["model"] == "B15"

        # Check that handle section was enhanced
        assert "handle" in result.matched
        assert result.matched["handle"]["brand"] == "Declaration Grooming"
        assert result.matched["handle"]["model"] == "Washington"
        assert result.matched["handle"]["_matched_by"] == "HandleMatchingStrategy"

    def test_handle_matching_enabled_at_model_level(self, tmp_path):
        """Test that handle matching works when enabled at model level."""
        # Create test catalog with handle_matching at model level
        catalog_data = {
            "known_brushes": {
                "Declaration Grooming": {
                    "B15": {
                        "handle_matching": True,
                        "patterns": ["(declaration|\\bdg\\b).*\\bb15\\b"],
                        "fiber": "Badger",
                        "knot_size_mm": 28,
                    },
                    "B16": {
                        "patterns": ["(declaration|\\bdg\\b).*\\bb16\\b"],
                        "fiber": "Badger",
                        "knot_size_mm": 28,
                    },
                }
            },
            "other_brushes": {},
        }

        # Create handles catalog with Declaration Grooming handles
        handles_data = {
            "artisan_handles": {
                "Declaration Grooming": {
                    "Washington": {
                        "patterns": ["washington"],
                    },
                    "Jefferson": {
                        "patterns": ["jefferson"],
                    },
                }
            },
            "manufacturer_handles": {},
            "other_handles": {},
        }

        # Create minimal knots catalog
        knots_data = {"known_knots": {}, "other_knots": {}}
        correct_matches_data = {"brush": {}, "handle": {}, "knot": {}, "split_brush": {}}

        catalog_path = tmp_path / "brushes.yaml"
        handles_path = tmp_path / "handles.yaml"
        knots_path = tmp_path / "knots.yaml"
        correct_matches_path = tmp_path / "correct_matches.yaml"

        with catalog_path.open("w", encoding="utf-8") as f:
            yaml.dump(catalog_data, f)
        with handles_path.open("w", encoding="utf-8") as f:
            yaml.dump(handles_data, f)
        with knots_path.open("w", encoding="utf-8") as f:
            yaml.dump(knots_data, f)
        with correct_matches_path.open("w", encoding="utf-8") as f:
            yaml.dump(correct_matches_data, f)

        # Create brush matcher
        config = BrushMatcherConfig.create_custom(
            catalog_path=catalog_path,
            handles_path=handles_path,
            knots_path=knots_path,
            correct_matches_path=correct_matches_path,
        )
        matcher = BrushMatcher(config)

        # Test that handle matching is enabled for B15 but not B16
        assert matcher._is_handle_matching_enabled("Declaration Grooming", "B15") is True
        assert matcher._is_handle_matching_enabled("Declaration Grooming", "B16") is False

        # Test matching a brush with Jefferson handle
        result = matcher.match("DG B15 Jefferson")
        assert result is not None
        assert result.matched is not None
        assert result.matched["brand"] == "Declaration Grooming"
        assert result.matched["model"] == "B15"

        # Check that handle section was enhanced
        assert "handle" in result.matched
        assert result.matched["handle"]["brand"] == "Declaration Grooming"
        assert result.matched["handle"]["model"] == "Jefferson"
        assert result.matched["handle"]["_matched_by"] == "HandleMatchingStrategy"

    def test_handle_matching_hierarchical_override(self, tmp_path):
        """Test that model-level handle_matching overrides brand-level setting."""
        # Create test catalog with brand-level handle_matching and model-level override
        catalog_data = {
            "known_brushes": {
                "Declaration Grooming": {
                    "handle_matching": True,  # Brand-level setting
                    "B15": {
                        "patterns": ["(declaration|\\bdg\\b).*\\bb15\\b"],
                        "fiber": "Badger",
                        "knot_size_mm": 28,
                    },
                    "B16": {
                        "handle_matching": False,  # Model-level override
                        "patterns": ["(declaration|\\bdg\\b).*\\bb16\\b"],
                        "fiber": "Badger",
                        "knot_size_mm": 28,
                    },
                }
            },
            "other_brushes": {},
        }

        # Create handles catalog with Declaration Grooming handles
        handles_data = {
            "artisan_handles": {
                "Declaration Grooming": {
                    "Washington": {
                        "patterns": ["washington"],
                    },
                }
            },
            "manufacturer_handles": {},
            "other_handles": {},
        }

        # Create minimal knots catalog
        knots_data = {"known_knots": {}, "other_knots": {}}
        correct_matches_data = {"brush": {}, "handle": {}, "knot": {}, "split_brush": {}}

        catalog_path = tmp_path / "brushes.yaml"
        handles_path = tmp_path / "handles.yaml"
        knots_path = tmp_path / "knots.yaml"
        correct_matches_path = tmp_path / "correct_matches.yaml"

        with catalog_path.open("w", encoding="utf-8") as f:
            yaml.dump(catalog_data, f)
        with handles_path.open("w", encoding="utf-8") as f:
            yaml.dump(handles_data, f)
        with knots_path.open("w", encoding="utf-8") as f:
            yaml.dump(knots_data, f)
        with correct_matches_path.open("w", encoding="utf-8") as f:
            yaml.dump(correct_matches_data, f)

        # Create brush matcher
        config = BrushMatcherConfig.create_custom(
            catalog_path=catalog_path,
            handles_path=handles_path,
            knots_path=knots_path,
            correct_matches_path=correct_matches_path,
        )
        matcher = BrushMatcher(config)

        # Test hierarchical behavior
        assert matcher._is_handle_matching_enabled("Declaration Grooming", "B15") is True
        assert matcher._is_handle_matching_enabled("Declaration Grooming", "B16") is False

        # Test that B15 gets handle matching but B16 doesn't
        result_b15 = matcher.match("DG B15 Washington")
        assert result_b15 is not None
        assert result_b15.matched is not None
        assert result_b15.matched["handle"]["model"] == "Washington"

        result_b16 = matcher.match("DG B16 Washington")
        assert result_b16 is not None
        assert result_b16.matched is not None
        # B16 should not have enhanced handle matching
        assert (
            result_b16.matched["handle"]["model"] is None
        )  # No handle model when handle matching disabled

    def test_handle_matching_fails_gracefully(self, tmp_path):
        """Test that handle matching fails gracefully when no patterns match."""
        # Create test catalog with handle_matching enabled
        catalog_data = {
            "known_brushes": {
                "Declaration Grooming": {
                    "handle_matching": True,
                    "B15": {
                        "patterns": ["(declaration|\\bdg\\b).*\\bb15\\b"],
                        "fiber": "Badger",
                        "knot_size_mm": 28,
                    },
                }
            },
            "other_brushes": {},
        }

        # Create handles catalog with Declaration Grooming handles
        handles_data = {
            "artisan_handles": {
                "Declaration Grooming": {
                    "Washington": {
                        "patterns": ["washington"],
                    },
                }
            },
            "manufacturer_handles": {},
            "other_handles": {},
        }

        # Create minimal knots catalog
        knots_data = {"known_knots": {}, "other_knots": {}}
        correct_matches_data = {"brush": {}, "handle": {}, "knot": {}, "split_brush": {}}

        catalog_path = tmp_path / "brushes.yaml"
        handles_path = tmp_path / "handles.yaml"
        knots_path = tmp_path / "knots.yaml"
        correct_matches_path = tmp_path / "correct_matches.yaml"

        with catalog_path.open("w", encoding="utf-8") as f:
            yaml.dump(catalog_data, f)
        with handles_path.open("w", encoding="utf-8") as f:
            yaml.dump(handles_data, f)
        with knots_path.open("w", encoding="utf-8") as f:
            yaml.dump(knots_data, f)
        with correct_matches_path.open("w", encoding="utf-8") as f:
            yaml.dump(correct_matches_data, f)

        # Create brush matcher
        config = BrushMatcherConfig.create_custom(
            catalog_path=catalog_path,
            handles_path=handles_path,
            knots_path=knots_path,
            correct_matches_path=correct_matches_path,
        )
        matcher = BrushMatcher(config)

        # Test that handle matching fails gracefully
        # The brush matcher should catch the exception and continue with other strategies
        result = matcher.match("DG B15 UnknownHandle")

        # The brush matcher should handle the exception gracefully
        # It should fall back to other strategies and find a match
        assert result is not None
        assert result.matched is not None

        # Should be a knot-only match (not a complete brush with handle matching)
        assert result.matched["brand"] is None  # Not a complete brush
        assert result.matched["model"] is None  # Not a complete brush

        # Should have knot information
        assert "knot" in result.matched
        assert result.matched["knot"]["brand"] == "Declaration Grooming"
        assert result.matched["knot"]["model"] == "B15"

    def test_handle_matching_not_applied_to_split_brushes(self, tmp_path):
        """Test that handle matching is not applied to split brushes."""
        # Create test catalog with handle_matching enabled
        catalog_data = {
            "known_brushes": {
                "Declaration Grooming": {
                    "handle_matching": True,
                    "B15": {
                        "patterns": ["(declaration|\\bdg\\b).*\\bb15\\b"],
                        "fiber": "Badger",
                        "knot_size_mm": 28,
                    },
                }
            },
            "other_brushes": {},
        }

        # Create handles catalog with Declaration Grooming handles
        handles_data = {
            "artisan_handles": {
                "Declaration Grooming": {
                    "Washington": {
                        "patterns": ["washington"],
                    },
                }
            },
            "manufacturer_handles": {},
            "other_handles": {},
        }

        # Create minimal knots catalog
        knots_data = {"known_knots": {}, "other_knots": {}}

        # Create correct matches with a split brush entry
        correct_matches_data = {
            "brush": {},
            "handle": {},
            "knot": {},
            "split_brush": {
                "DG B15 w/ C&H Zebra": {
                    "handle": "Chisel & Hound Zebra",
                    "knot": "Declaration Grooming B15",
                }
            },
        }

        catalog_path = tmp_path / "brushes.yaml"
        handles_path = tmp_path / "handles.yaml"
        knots_path = tmp_path / "knots.yaml"
        correct_matches_path = tmp_path / "correct_matches.yaml"

        with catalog_path.open("w", encoding="utf-8") as f:
            yaml.dump(catalog_data, f)
        with handles_path.open("w", encoding="utf-8") as f:
            yaml.dump(handles_data, f)
        with knots_path.open("w", encoding="utf-8") as f:
            yaml.dump(knots_data, f)
        with correct_matches_path.open("w", encoding="utf-8") as f:
            yaml.dump(correct_matches_data, f)

        # Create brush matcher
        config = BrushMatcherConfig.create_custom(
            catalog_path=catalog_path,
            handles_path=handles_path,
            knots_path=knots_path,
            correct_matches_path=correct_matches_path,
        )
        matcher = BrushMatcher(config)

        # Test that split brush matching works without handle matching enhancement
        result = matcher.match("DG B15 w/ C&H Zebra")
        assert result is not None
        assert result.matched is not None

        # Should be a split brush result, not a complete brush with handle matching
        assert result.matched["brand"] is None  # Split brush
        assert result.matched["model"] is None  # Split brush
        assert "handle" in result.matched
        assert "knot" in result.matched
