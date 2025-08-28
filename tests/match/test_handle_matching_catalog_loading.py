"""Test handle_matching field loading and hierarchical behavior in brush catalogs."""

import yaml

from sotd.match.loaders import CatalogLoader


class TestHandleMatchingCatalogLoading:
    """Test that handle_matching field is properly loaded and preserved."""

    def test_handle_matching_field_preserved_at_brand_level(self, tmp_path):
        """Test that handle_matching field is preserved at brand level."""
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
                    "B16": {
                        "patterns": ["(declaration|\\bdg\\b).*\\bb16\\b"],
                        "fiber": "Badger",
                        "knot_size_mm": 28,
                    },
                }
            },
            "other_brushes": {},
        }

        catalog_path = tmp_path / "brushes.yaml"
        with catalog_path.open("w", encoding="utf-8") as f:
            yaml.dump(catalog_data, f)

        # Create minimal handles and knots catalogs
        handles_data = {"artisan_handles": {}, "manufacturer_handles": {}, "other_handles": {}}
        knots_data = {"known_knots": {}, "other_knots": {}}
        correct_matches_data = {"brush": {}, "handle": {}, "knot": {}, "split_brush": {}}

        handles_path = tmp_path / "handles.yaml"
        knots_path = tmp_path / "knots.yaml"
        correct_matches_path = tmp_path / "correct_matches.yaml"

        with handles_path.open("w", encoding="utf-8") as f:
            yaml.dump(handles_data, f)
        with knots_path.open("w", encoding="utf-8") as f:
            yaml.dump(knots_data, f)
        with correct_matches_path.open("w", encoding="utf-8") as f:
            yaml.dump(correct_matches_data, f)

        # Load catalog and verify handle_matching is preserved
        loader = CatalogLoader()
        catalogs = {}
        catalogs["brushes"] = loader.load_catalog(catalog_path, "brushes")
        catalogs["handles"] = loader.load_catalog(handles_path, "handles")
        catalogs["knots"] = loader.load_catalog(knots_path, "knots")
        catalogs["correct_matches"] = loader.load_catalog(correct_matches_path, "correct_matches")

        # Check that handle_matching is preserved at brand level
        declaration_grooming = catalogs["brushes"]["known_brushes"]["Declaration Grooming"]
        assert declaration_grooming["handle_matching"] is True

        # Check that models inherit the brand-level setting
        assert "handle_matching" not in declaration_grooming["B15"]  # Should inherit from brand
        assert "handle_matching" not in declaration_grooming["B16"]  # Should inherit from brand

    def test_handle_matching_field_preserved_at_model_level(self, tmp_path):
        """Test that handle_matching field is preserved at model level."""
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
                        "handle_matching": True,
                        "patterns": ["(declaration|\\bdg\\b).*\\bb16\\b"],
                        "fiber": "Badger",
                        "knot_size_mm": 28,
                    },
                    "B14": {
                        "patterns": ["(declaration|\\bdg\\b).*\\bb14\\b"],
                        "fiber": "Badger",
                        "knot_size_mm": 28,
                    },
                }
            },
            "other_brushes": {},
        }

        catalog_path = tmp_path / "brushes.yaml"
        with catalog_path.open("w", encoding="utf-8") as f:
            yaml.dump(catalog_data, f)

        # Create minimal handles and knots catalogs
        handles_data = {"artisan_handles": {}, "manufacturer_handles": {}, "other_handles": {}}
        knots_data = {"known_knots": {}, "other_knots": {}}
        correct_matches_data = {"brush": {}, "handle": {}, "knot": {}, "split_brush": {}}

        handles_path = tmp_path / "handles.yaml"
        knots_path = tmp_path / "knots.yaml"
        correct_matches_path = tmp_path / "correct_matches.yaml"

        with handles_path.open("w", encoding="utf-8") as f:
            yaml.dump(handles_data, f)
        with knots_path.open("w", encoding="utf-8") as f:
            yaml.dump(knots_data, f)
        with correct_matches_path.open("w", encoding="utf-8") as f:
            yaml.dump(correct_matches_data, f)

        # Load catalog and verify handle_matching is preserved
        loader = CatalogLoader()
        catalogs = {}
        catalogs["brushes"] = loader.load_catalog(catalog_path, "brushes")
        catalogs["handles"] = loader.load_catalog(handles_path, "handles")
        catalogs["knots"] = loader.load_catalog(knots_path, "knots")
        catalogs["correct_matches"] = loader.load_catalog(correct_matches_path, "correct_matches")

        # Check that handle_matching is preserved at model level
        declaration_grooming = catalogs["brushes"]["known_brushes"]["Declaration Grooming"]
        assert declaration_grooming["B15"]["handle_matching"] is True
        assert declaration_grooming["B16"]["handle_matching"] is True
        assert "handle_matching" not in declaration_grooming["B14"]  # Should not have it

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
                    "B14": {
                        "handle_matching": False,  # Model-level override
                        "patterns": ["(declaration|\\bdg\\b).*\\bb14\\b"],
                        "fiber": "Badger",
                        "knot_size_mm": 28,
                    },
                }
            },
            "other_brushes": {},
        }

        catalog_path = tmp_path / "brushes.yaml"
        with catalog_path.open("w", encoding="utf-8") as f:
            yaml.dump(catalog_data, f)

        # Create minimal handles and knots catalogs
        handles_data = {"artisan_handles": {}, "manufacturer_handles": {}, "other_handles": {}}
        knots_data = {"known_knots": {}, "other_knots": {}}
        correct_matches_data = {"brush": {}, "handle": {}, "knot": {}, "split_brush": {}}

        handles_path = tmp_path / "handles.yaml"
        knots_path = tmp_path / "knots.yaml"
        correct_matches_path = tmp_path / "correct_matches.yaml"

        with handles_path.open("w", encoding="utf-8") as f:
            yaml.dump(handles_data, f)
        with knots_path.open("w", encoding="utf-8") as f:
            yaml.dump(knots_data, f)
        with correct_matches_path.open("w", encoding="utf-8") as f:
            yaml.dump(correct_matches_data, f)

        # Load catalog and verify hierarchical behavior
        loader = CatalogLoader()
        catalogs = {}
        catalogs["brushes"] = loader.load_catalog(catalog_path, "brushes")
        catalogs["handles"] = loader.load_catalog(handles_path, "handles")
        catalogs["knots"] = loader.load_catalog(knots_path, "knots")
        catalogs["correct_matches"] = loader.load_catalog(correct_matches_path, "correct_matches")

        # Check hierarchical behavior
        declaration_grooming = catalogs["brushes"]["known_brushes"]["Declaration Grooming"]

        # Brand-level setting should be preserved
        assert declaration_grooming["handle_matching"] is True

        # B15 should inherit brand-level setting (no model-level override)
        assert "handle_matching" not in declaration_grooming["B15"]

        # B16 and B14 should have model-level overrides
        assert declaration_grooming["B16"]["handle_matching"] is False
        assert declaration_grooming["B14"]["handle_matching"] is False

    def test_handle_matching_default_behavior(self, tmp_path):
        """Test that handle_matching defaults to False when not specified."""
        # Create test catalog without handle_matching fields
        catalog_data = {
            "known_brushes": {
                "Declaration Grooming": {
                    "B15": {
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

        catalog_path = tmp_path / "brushes.yaml"
        with catalog_path.open("w", encoding="utf-8") as f:
            yaml.dump(catalog_data, f)

        # Create minimal handles and knots catalogs
        handles_data = {"artisan_handles": {}, "manufacturer_handles": {}, "other_handles": {}}
        knots_data = {"known_knots": {}, "other_knots": {}}
        correct_matches_data = {"brush": {}, "handle": {}, "knot": {}, "split_brush": {}}

        handles_path = tmp_path / "handles.yaml"
        knots_path = tmp_path / "knots.yaml"
        correct_matches_path = tmp_path / "correct_matches.yaml"

        with handles_path.open("w", encoding="utf-8") as f:
            yaml.dump(handles_data, f)
        with knots_path.open("w", encoding="utf-8") as f:
            yaml.dump(knots_data, f)
        with correct_matches_path.open("w", encoding="utf-8") as f:
            yaml.dump(correct_matches_data, f)

        # Load catalog and verify default behavior
        loader = CatalogLoader()
        catalogs = {}
        catalogs["brushes"] = loader.load_catalog(catalog_path, "brushes")
        catalogs["handles"] = loader.load_catalog(handles_path, "handles")
        catalogs["knots"] = loader.load_catalog(knots_path, "knots")
        catalogs["correct_matches"] = loader.load_catalog(correct_matches_path, "correct_matches")

        # Check that handle_matching is not present (defaults to False)
        declaration_grooming = catalogs["brushes"]["known_brushes"]["Declaration Grooming"]
        assert "handle_matching" not in declaration_grooming
        assert "handle_matching" not in declaration_grooming["B15"]
        assert "handle_matching" not in declaration_grooming["B16"]

    def test_handle_matching_validation_boolean_values(self, tmp_path):
        """Test that handle_matching field validates boolean values."""
        # Create test catalog with invalid handle_matching values
        catalog_data = {
            "known_brushes": {
                "Declaration Grooming": {
                    "handle_matching": "not_a_boolean",  # Invalid value
                    "B15": {
                        "handle_matching": 123,  # Invalid value
                        "patterns": ["(declaration|\\bdg\\b).*\\bb15\\b"],
                        "fiber": "Badger",
                        "knot_size_mm": 28,
                    },
                }
            },
            "other_brushes": {},
        }

        catalog_path = tmp_path / "brushes.yaml"
        with catalog_path.open("w", encoding="utf-8") as f:
            yaml.dump(catalog_data, f)

        # Create minimal handles and knots catalogs
        handles_data = {"artisan_handles": {}, "manufacturer_handles": {}, "other_handles": {}}
        knots_data = {"known_knots": {}, "other_knots": {}}
        correct_matches_data = {"brush": {}, "handle": {}, "knot": {}, "split_brush": {}}

        handles_path = tmp_path / "handles.yaml"
        knots_path = tmp_path / "knots.yaml"
        correct_matches_path = tmp_path / "correct_matches.yaml"

        with handles_path.open("w", encoding="utf-8") as f:
            yaml.dump(handles_data, f)
        with knots_path.open("w", encoding="utf-8") as f:
            yaml.dump(knots_data, f)
        with correct_matches_path.open("w", encoding="utf-8") as f:
            yaml.dump(correct_matches_data, f)

        # Load catalog - should not raise error but should preserve the values as-is
        # (validation will be handled during usage, not during loading)
        loader = CatalogLoader()
        catalogs = {}
        catalogs["brushes"] = loader.load_catalog(catalog_path, "brushes")
        catalogs["handles"] = loader.load_catalog(handles_path, "handles")
        catalogs["knots"] = loader.load_catalog(knots_path, "knots")
        catalogs["correct_matches"] = loader.load_catalog(correct_matches_path, "correct_matches")

        # Check that invalid values are preserved (validation happens during usage)
        declaration_grooming = catalogs["brushes"]["known_brushes"]["Declaration Grooming"]
        assert declaration_grooming["handle_matching"] == "not_a_boolean"
        assert declaration_grooming["B15"]["handle_matching"] == 123
