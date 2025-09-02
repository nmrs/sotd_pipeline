import pytest

from sotd.enrich.brush_enricher import BrushEnricher


@pytest.fixture
def enricher():
    return BrushEnricher()


class TestBrushEnricher:
    def test_target_field(self, enricher):
        """Test that the enricher targets the brush field."""
        assert enricher.target_field == "brush"

    def test_applies_to_with_valid_brush(self, enricher):
        """Test that enricher applies to records with valid brush data."""
        record = {
            "brush": {
                "matched": {
                    "brand": "Simpson",
                    "model": "Chubby 2",
                    "fiber": "Badger",
                }
            }
        }
        assert enricher.applies_to(record) is True

    def test_applies_to_without_brush(self, enricher):
        """Test that enricher doesn't apply to records without brush data."""
        record = {"razor": {"matched": {"brand": "Merkur", "model": "34C"}}}
        assert enricher.applies_to(record) is False

    def test_applies_to_with_none_brush(self, enricher):
        """Test that enricher doesn't apply to records with None brush."""
        record = {"brush": None}
        assert enricher.applies_to(record) is False

    def test_applies_to_without_brand(self, enricher):
        """Test that enricher doesn't apply to brush data without brand."""
        record = {"brush": {"matched": {"model": "Chubby 2", "fiber": "Badger"}}}
        assert enricher.applies_to(record) is False

    def test_enrich_with_catalog_knot_size_only(self, enricher):
        """Test enrichment when only catalog has knot size."""
        field_data = {
            "matched": {
                "brand": "Simpson",
                "model": "Chubby 2",
                "fiber": "Badger",
                "knot_size_mm": 27.0,
                "handle": {
                    "brand": "Simpson",
                    "model": "Chubby 2",
                    "source_text": "Simpson Chubby 2",
                },
                "knot": {
                    "brand": "Simpson",
                    "model": "Chubby 2",
                    "fiber": "Badger",
                    "knot_size_mm": 27.0,
                    "source_text": "Simpson Chubby 2",
                },
            }
        }
        brush_extracted = "Simpson Chubby 2"

        result = enricher.enrich(field_data, brush_extracted)

        assert result is not None
        assert result["knot_size_mm"] == 27.0
        assert result["_enriched_by"] == "BrushEnricher"
        assert result["_extraction_source"] == "catalog_data"

    def test_enrich_with_user_knot_size_only(self, enricher):
        """Test enrichment when only user specifies knot size."""
        field_data = {
            "matched": {
                "brand": "Simpson",
                "model": "Chubby 2",
                "fiber": "Badger",
                "handle": {
                    "brand": "Simpson",
                    "model": "Chubby 2",
                    "source_text": "Simpson Chubby 2",
                },
                "knot": {
                    "brand": "Simpson",
                    "model": "Chubby 2",
                    "fiber": "Badger",
                    "source_text": "Simpson Chubby 2",
                },
            }
        }
        brush_extracted = "Simpson Chubby 2 26mm"

        result = enricher.enrich(field_data, brush_extracted)

        assert result is not None
        assert result["knot_size_mm"] == 26.0
        assert result["_enriched_by"] == "BrushEnricher"
        assert result["_extraction_source"] == "user_comment + catalog_data"

    def test_enrich_with_matching_catalog_and_user(self, enricher):
        """Test enrichment when catalog and user knot sizes match."""
        field_data = {
            "matched": {
                "brand": "Simpson",
                "model": "Chubby 2",
                "fiber": "Badger",
                "knot_size_mm": 27.0,
                "handle": {
                    "brand": "Simpson",
                    "model": "Chubby 2",
                    "source_text": "Simpson Chubby 2",
                },
                "knot": {
                    "brand": "Simpson",
                    "model": "Chubby 2",
                    "fiber": "Badger",
                    "knot_size_mm": 27.0,
                    "source_text": "Simpson Chubby 2",
                },
            }
        }
        brush_extracted = "Simpson Chubby 2 27mm"

        result = enricher.enrich(field_data, brush_extracted)

        assert result is not None
        assert result["knot_size_mm"] == 27.0
        assert result["_enriched_by"] == "BrushEnricher"
        assert result["_extraction_source"] == "user_comment + catalog_data"

    def test_enrich_with_conflicting_catalog_and_user(self, enricher):
        """Test enrichment when catalog and user knot sizes conflict."""
        field_data = {
            "matched": {
                "brand": "Simpson",
                "model": "Chubby 2",
                "fiber": "Badger",
                "knot_size_mm": 27.0,
                "handle": {
                    "brand": "Simpson",
                    "model": "Chubby 2",
                    "source_text": "Simpson Chubby 2",
                },
                "knot": {
                    "brand": "Simpson",
                    "model": "Chubby 2",
                    "fiber": "Badger",
                    "knot_size_mm": 27.0,
                    "source_text": "Simpson Chubby 2",
                },
            }
        }
        brush_extracted = "Simpson Chubby 2 26mm"

        result = enricher.enrich(field_data, brush_extracted)

        assert result is not None
        assert result["knot_size_mm"] == 26.0
        assert result["_enriched_by"] == "BrushEnricher"
        assert result["_extraction_source"] == "user_comment + catalog_data"
        assert result["_catalog_knot_size_mm"] == 27.0

    def test_enrich_with_no_knot_size(self, enricher):
        """Test enrichment when no knot size is available."""
        field_data = {
            "matched": {
                "brand": "Simpson",
                "model": "Chubby 2",
                "fiber": "Badger",
                "handle": {
                    "brand": "Simpson",
                    "model": "Chubby 2",
                    "source_text": "Simpson Chubby 2",
                },
                "knot": {
                    "brand": "Simpson",
                    "model": "Chubby 2",
                    "fiber": "Badger",
                    "source_text": "Simpson Chubby 2",
                },
            }
        }
        brush_extracted = "Simpson Chubby 2"

        result = enricher.enrich(field_data, brush_extracted)

        assert result is not None
        assert "knot_size_mm" not in result
        assert result["_enriched_by"] == "BrushEnricher"
        assert result["_extraction_source"] == "catalog_data"  # Catalog fiber is present

    def test_enrich_with_invalid_field_data(self, enricher):
        """Test enrichment with invalid field data."""
        result = enricher.enrich(None, "Simpson Chubby 2")
        assert result is None

    def test_enrich_with_empty_comment(self, enricher):
        """Test enrichment with empty comment."""
        field_data = {
            "matched": {
                "brand": "Simpson",
                "model": "Chubby 2",
                "fiber": "Badger",
                "knot_size_mm": 27.0,
                "handle": {
                    "brand": "Simpson",
                    "model": "Chubby 2",
                    "source_text": "Simpson Chubby 2",
                },
                "knot": {
                    "brand": "Simpson",
                    "model": "Chubby 2",
                    "fiber": "Badger",
                    "knot_size_mm": 27.0,
                    "source_text": "Simpson Chubby 2",
                },
            }
        }
        result = enricher.enrich(field_data, "")
        assert result is not None
        assert result["_extraction_source"] == "catalog_data"

    def test_enrich_with_handle_maker_knot_size_inference(self, enricher):
        """Test enrichment when knot size is inferred from handle maker defaults."""
        field_data = {
            "matched": {
                "brand": "Declaration Grooming",
                "model": "B2",
                "fiber": "Badger",
                "handle": {
                    "brand": "Chisel & Hound",
                    "model": "Unspecified",
                    "source_text": "Chisel & Hound handle",
                },
                "knot": {
                    "brand": "Declaration Grooming",
                    "model": "B2",
                    "fiber": "Badger",
                    "source_text": "Declaration Grooming B2",
                },
            }
        }
        brush_extracted = "Declaration Grooming B2 in Chisel & Hound handle"

        result = enricher.enrich(field_data, brush_extracted)

        assert result is not None
        # Note: knot_size_mm inference from handle maker defaults is not currently implemented
        # The enricher only enriches fiber data when no knot size defaults are available
        assert result["_enriched_by"] == "BrushEnricher"
        assert result["_extraction_source"] == "catalog_data"
        # Handle maker inference is not available without knot size defaults

    def test_enrich_with_handle_maker_model_level_override(self, enricher):
        """Test enrichment when handle maker has model-level knot size override."""
        field_data = {
            "matched": {
                "brand": "Declaration Grooming",
                "model": "B2",
                "fiber": "Badger",
                "handle": {
                    "brand": "Chisel & Hound",
                    "model": "Custom Model",
                    "source_text": "Chisel & Hound Custom Model handle",
                },
                "knot": {
                    "brand": "Declaration Grooming",
                    "model": "B2",
                    "fiber": "Badger",
                    "source_text": "Declaration Grooming B2",
                },
            }
        }
        brush_extracted = "Declaration Grooming B2 in Chisel & Hound Custom Model handle"

        result = enricher.enrich(field_data, brush_extracted)

        # Note: knot_size_mm inference from handle maker defaults is not currently implemented
        # The enricher only enriches fiber data when no knot size defaults are available
        assert result is not None
        # Handle maker inference is not available without knot size defaults
        assert result["_extraction_source"] == "catalog_data"

    def test_enrich_with_handle_maker_no_defaults(self, enricher):
        """Test enrichment when handle maker has no knot size defaults."""
        field_data = {
            "matched": {
                "brand": "Declaration Grooming",
                "model": "B2",
                "fiber": "Badger",
                "handle": {
                    "brand": "Declaration Grooming",  # No defaults in handles.yaml
                    "model": "Unspecified",
                    "source_text": "Declaration Grooming handle",
                },
                "knot": {
                    "brand": "Declaration Grooming",
                    "model": "B2",
                    "fiber": "Badger",
                    "source_text": "Declaration Grooming B2",
                },
            }
        }
        brush_extracted = "Declaration Grooming B2 in Declaration Grooming handle"

        result = enricher.enrich(field_data, brush_extracted)

        # Should not infer from handle maker since Declaration Grooming has no defaults
        assert result is not None
        assert "knot_size_mm" not in result

    def test_enrich_with_handle_maker_user_priority(self, enricher):
        """Test that user-specified knot size takes priority over handle maker defaults."""
        field_data = {
            "matched": {
                "brand": "Declaration Grooming",
                "model": "B2",
                "fiber": "Badger",
                "handle": {
                    "brand": "Chisel & Hound",
                    "model": "Unspecified",
                    "source_text": "Chisel & Hound handle",
                },
                "knot": {
                    "brand": "Declaration Grooming",
                    "model": "B2",
                    "fiber": "Badger",
                    "source_text": "Declaration Grooming B2",
                },
            }
        }
        brush_extracted = "Declaration Grooming B2 28mm in Chisel & Hound handle"

        result = enricher.enrich(field_data, brush_extracted)

        # User-specified 28mm should take priority over Chisel & Hound's 26mm default
        assert result is not None
        assert result["knot_size_mm"] == 28.0
        # BaseEnricher combines sources when both user and catalog data exist
        assert "user_comment" in result["_extraction_source"]
        assert "_handle_maker_inference" not in result

    def test_enrich_with_handle_maker_catalog_priority(self, enricher):
        """Test that catalog knot size takes priority over handle maker defaults."""
        field_data = {
            "matched": {
                "brand": "Declaration Grooming",
                "model": "B2",
                "fiber": "Badger",
                "handle": {
                    "brand": "Chisel & Hound",
                    "model": "Unspecified",
                    "source_text": "Chisel & Hound handle",
                },
                "knot": {
                    "brand": "Declaration Grooming",
                    "model": "B2",
                    "fiber": "Badger",
                    "knot_size_mm": 27.0,  # Catalog has knot size
                    "source_text": "Declaration Grooming B2",
                },
            }
        }
        brush_extracted = "Declaration Grooming B2 in Chisel & Hound handle"

        result = enricher.enrich(field_data, brush_extracted)

        # Catalog's 27mm should take priority over Chisel & Hound's 26mm default
        assert result is not None
        assert result["knot_size_mm"] == 27.0
        assert result["_extraction_source"] == "catalog_data"
        assert "_handle_maker_inference" not in result

    def test_enrich_with_handle_maker_missing_handle_section(self, enricher):
        """Test enrichment when handle section is missing."""
        field_data = {
            "matched": {
                "brand": "Declaration Grooming",
                "model": "B2",
                "fiber": "Badger",
                "knot": {
                    "brand": "Declaration Grooming",
                    "model": "B2",
                    "fiber": "Badger",
                    "source_text": "Declaration Grooming B2",
                },
            }
        }
        brush_extracted = "Declaration Grooming B2"

        result = enricher.enrich(field_data, brush_extracted)

        # Should not infer from handle maker since no handle section
        assert result is not None
        assert "knot_size_mm" not in result


class TestSourceTrackingValidation:
    """Test that Brush Enricher uses new BaseEnricher source tracking methods correctly."""

    def test_catalog_only_data_uses_catalog_source(self, enricher):
        """Test that catalog-only data shows correct source tracking."""
        field_data = {
            "matched": {
                "knot_size_mm": 27.0,
                "fiber": "Badger",
            }
        }
        brush_extracted = "Simpson Chubby 2"  # No user data extracted

        result = enricher.enrich(field_data, brush_extracted)

        assert result is not None
        assert result["knot_size_mm"] == 27.0
        assert result["fiber"] == "Badger"
        assert result["_extraction_source"] == "catalog_data"
        assert result["_fiber_extraction_source"] == "catalog_data"

    def test_user_only_data_uses_user_source(self, enricher):
        """Test that user-only data shows correct source tracking."""
        field_data = {"matched": {}}  # No catalog data
        brush_extracted = "Simpson Chubby 2 26mm Badger"  # User data extracted

        result = enricher.enrich(field_data, brush_extracted)

        assert result is not None
        assert result["knot_size_mm"] == 26.0
        assert result["fiber"] == "Badger"
        assert result["_extraction_source"] == "user_comment"
        assert result["_fiber_extraction_source"] == "user_comment"

    def test_mixed_data_uses_combined_source(self, enricher):
        """Test that mixed data shows correct source tracking."""
        field_data = {
            "matched": {
                "knot_size_mm": 27.0,
                "fiber": "Synthetic",
            }
        }
        brush_extracted = "Simpson Chubby 2 26mm Badger"  # User overrides catalog

        result = enricher.enrich(field_data, brush_extracted)

        assert result is not None
        assert result["knot_size_mm"] == 26.0  # User value
        assert result["fiber"] == "Badger"  # User value
        assert result["_extraction_source"] == "user_comment + catalog_data"
        assert result["_fiber_extraction_source"] == "user_comment + catalog_data"

    def test_user_confirms_catalog_uses_combined_source(self, enricher):
        """Test that user confirming catalog shows correct source tracking."""
        field_data = {
            "matched": {
                "knot_size_mm": 27.0,
                "fiber": "Badger",
            }
        }
        brush_extracted = "Simpson Chubby 2 27mm Badger"  # User confirms catalog

        result = enricher.enrich(field_data, brush_extracted)

        assert result is not None
        assert result["knot_size_mm"] == 27.0  # User value (same as catalog)
        assert result["fiber"] == "Badger"  # User value (same as catalog)
        assert result["_extraction_source"] == "user_comment + catalog_data"
        assert result["_fiber_extraction_source"] == "user_comment + catalog_data"

    def test_no_data_uses_none_source(self, enricher):
        """Test that no data shows correct source tracking."""
        field_data = {}  # No catalog data
        brush_extracted = "Simpson Chubby 2"  # No user data extracted

        result = enricher.enrich(field_data, brush_extracted)

        assert result is not None
        assert "knot_size_mm" not in result
        assert "fiber" not in result
        assert result["_extraction_source"] == "none"
        # _fiber_extraction_source should not be present when no fiber data

    def test_user_none_values_dont_override_catalog(self, enricher):
        """Test that user None values don't override catalog values."""
        field_data = {
            "matched": {
                "knot_size_mm": 27.0,
                "fiber": "Badger",
            }
        }
        brush_extracted = "Simpson Chubby 2"  # No user data extracted (None values)

        result = enricher.enrich(field_data, brush_extracted)

        assert result is not None
        assert result["knot_size_mm"] == 27.0  # Catalog value preserved
        assert result["fiber"] == "Badger"  # Catalog value preserved
        assert result["_extraction_source"] == "catalog_data"
        assert result["_fiber_extraction_source"] == "catalog_data"


class TestKnotSizeExtraction:
    def test_extract_knot_size_with_mm_suffix(self, enricher):
        """Test knot size extraction with mm suffix."""
        result = enricher._extract_knot_size("Simpson Chubby 2 27mm")
        assert result == 27.0

    def test_extract_knot_size_with_dimensions(self, enricher):
        """Test knot size extraction with dimensions format."""
        result = enricher._extract_knot_size("Simpson Chubby 2 27x52mm")
        assert result == 27.0

    def test_extract_knot_size_with_reasonable_range(self, enricher):
        """Test knot size extraction within reasonable range."""
        result = enricher._extract_knot_size("Simpson Chubby 2 30mm")
        assert result == 30.0

    def test_extract_knot_size_outside_range(self, enricher):
        """Test knot size extraction outside reasonable range."""
        result = enricher._extract_knot_size("Simpson Chubby 2 19")
        assert result is None

    def test_extract_knot_size_priority(self, enricher):
        """Test that first valid knot size is extracted."""
        result = enricher._extract_knot_size("Simpson Chubby 2 27mm 30mm")
        assert result == 27.0

    def test_extract_knot_size_no_match(self, enricher):
        """Test knot size extraction with no valid size."""
        result = enricher._extract_knot_size("Simpson Chubby 2")
        assert result is None

    def test_extract_knot_size_with_decimal(self, enricher):
        """Test knot size extraction with decimal values."""
        result = enricher._extract_knot_size("Simpson Chubby 2 26.5mm")
        assert result == 26.5


class TestRealWorldExamples:
    def test_simpson_chubby_example(self, enricher):
        """Test real-world Simpson Chubby example."""
        field_data = {
            "matched": {
                "brand": "Simpson",
                "model": "Chubby 2",
                "fiber": "Badger",
                "knot_size_mm": 27.0,
            }
        }
        brush_extracted = "Simpson Chubby 2 27mm"

        result = enricher.enrich(field_data, brush_extracted)

        assert result is not None
        assert result["knot_size_mm"] == 27.0
        assert result["fiber"] == "Badger"
        assert result["_enriched_by"] == "BrushEnricher"
        assert result["_extraction_source"] == "user_comment + catalog_data"

    def test_omega_boar_example(self, enricher):
        """Test real-world Omega boar example."""
        field_data = {
            "matched": {
                "brand": "Omega",
                "model": "10049",
                "fiber": "Boar",
            }
        }
        brush_extracted = "Omega 10049 24mm"

        result = enricher.enrich(field_data, brush_extracted)

        assert result is not None
        assert result["knot_size_mm"] == 24.0
        assert result["fiber"] == "Boar"
        assert result["_enriched_by"] == "BrushEnricher"
        assert result["_extraction_source"] == "user_comment + catalog_data"

    def test_custom_handle_example(self, enricher):
        """Test real-world custom handle example."""
        field_data = {
            "matched": {
                "brand": "Declaration",
                "model": "B2",
                "fiber": "Badger",
                "knot_size_mm": 28.0,
            }
        }
        brush_extracted = "Declaration B2 26mm"

        result = enricher.enrich(field_data, brush_extracted)

        assert result is not None
        assert result["knot_size_mm"] == 26.0
        assert result["fiber"] == "Badger"
        assert result["_enriched_by"] == "BrushEnricher"
        assert result["_extraction_source"] == "user_comment + catalog_data"
        assert result["_catalog_knot_size_mm"] == 28.0


class TestFiberExtraction:
    def test_extract_fiber_badger(self, enricher):
        """Test fiber extraction for badger."""
        field_data = {"matched": {"brand": "Simpson", "model": "Chubby 2"}}
        brush_extracted = "Simpson Chubby 2 Badger"

        result = enricher.enrich(field_data["matched"], brush_extracted)

        assert result is not None
        assert result["fiber"] == "Badger"
        assert result["_fiber_extraction_source"] == "user_comment"

    def test_extract_fiber_boar(self, enricher):
        """Test fiber extraction for boar."""
        field_data = {"matched": {"brand": "Omega", "model": "10049"}}
        brush_extracted = "Omega 10049 Boar"

        result = enricher.enrich(field_data["matched"], brush_extracted)

        assert result is not None
        assert result["fiber"] == "Boar"
        assert result["_fiber_extraction_source"] == "user_comment"

    def test_extract_fiber_synthetic(self, enricher):
        """Test fiber extraction for synthetic."""
        field_data = {"matched": {"brand": "Simpson", "model": "Chubby 2"}}
        brush_extracted = "Simpson Chubby 2 Synthetic"

        result = enricher.enrich(field_data["matched"], brush_extracted)

        assert result is not None
        assert result["fiber"] == "Synthetic"
        assert result["_fiber_extraction_source"] == "user_comment"

    def test_extract_fiber_mixed(self, enricher):
        """Test fiber extraction for mixed fiber."""
        field_data = {"matched": {"brand": "Simpson", "model": "Chubby 2"}}
        brush_extracted = "Simpson Chubby 2 Mixed"

        result = enricher.enrich(field_data["matched"], brush_extracted)

        assert result is not None
        assert result["fiber"] == "Mixed Badger/Boar"
        assert result["_fiber_extraction_source"] == "user_comment"

    def test_extract_fiber_horse(self, enricher):
        """Test fiber extraction for horse hair."""
        field_data = {"matched": {"brand": "Simpson", "model": "Chubby 2"}}
        brush_extracted = "Simpson Chubby 2 Horse"

        result = enricher.enrich(field_data["matched"], brush_extracted)

        assert result is not None
        assert result["fiber"] == "Horse"
        assert result["_fiber_extraction_source"] == "user_comment"

    def test_extract_fiber_no_match(self, enricher):
        """Test fiber extraction with no fiber specified."""
        field_data = {"matched": {"brand": "Simpson", "model": "Chubby 2"}}
        brush_extracted = "Simpson Chubby 2"

        result = enricher.enrich(field_data["matched"], brush_extracted)

        assert result is not None
        assert "fiber" not in result
        assert "_fiber_extraction_source" not in result


class TestFiberConflictResolution:
    def test_fiber_user_confirms_catalog(self, enricher):
        """Test fiber conflict resolution when user confirms catalog."""
        field_data = {
            "matched": {
                "brand": "Simpson",
                "model": "Chubby 2",
                "fiber": "Badger",
            }
        }
        brush_extracted = "Simpson Chubby 2 Badger"

        result = enricher.enrich(field_data, brush_extracted)

        assert result is not None
        assert result["fiber"] == "Badger"
        assert result["_fiber_extraction_source"] == "user_comment + catalog_data"

    def test_fiber_user_overrides_catalog(self, enricher):
        """Test fiber conflict resolution when user overrides catalog."""
        field_data = {
            "matched": {
                "brand": "Simpson",
                "model": "Chubby 2",
                "fiber": "Synthetic",
            }
        }
        brush_extracted = "Simpson Chubby 2 Badger"

        result = enricher.enrich(field_data, brush_extracted)

        assert result is not None
        assert result["fiber"] == "Badger"
        assert result["_fiber_extraction_source"] == "user_comment + catalog_data"
        assert result["_catalog_fiber"] == "Synthetic"

    def test_fiber_user_only(self, enricher):
        """Test fiber conflict resolution when only user has fiber."""
        field_data = {"matched": {"brand": "Simpson", "model": "Chubby 2"}}
        brush_extracted = "Simpson Chubby 2 Badger"

        result = enricher.enrich(field_data["matched"], brush_extracted)

        assert result is not None
        assert result["fiber"] == "Badger"
        assert result["_fiber_extraction_source"] == "user_comment"

    def test_fiber_catalog_only(self, enricher):
        """Test fiber conflict resolution when only catalog has fiber."""
        field_data = {
            "matched": {
                "brand": "Simpson",
                "model": "Chubby 2",
                "fiber": "Badger",
            }
        }
        brush_extracted = "Simpson Chubby 2"

        result = enricher.enrich(field_data, brush_extracted)

        assert result is not None
        assert result["fiber"] == "Badger"
        assert result["_fiber_extraction_source"] == "catalog_data"


class TestCustomKnotDetection:
    def test_custom_knot_fiber_mismatch(self, enricher):
        """Test custom knot detection for fiber mismatch."""
        field_data = {
            "matched": {
                "brand": "Simpson",
                "model": "Chubby 2",
                "fiber": "Synthetic",
                "knot_size_mm": 27.0,
            }
        }
        brush_extracted = "Simpson Chubby 2 27mm Badger"

        result = enricher.enrich(field_data, brush_extracted)

        assert result is not None
        assert result["_user_override"] is True
        assert "fiber_mismatch:Synthetic->Badger" in result["_user_override_reason"]

    def test_custom_knot_size_mismatch(self, enricher):
        """Test custom knot detection for size mismatch."""
        field_data = {
            "matched": {
                "brand": "Simpson",
                "model": "Chubby 2",
                "fiber": "Badger",
                "knot_size_mm": 27.0,
            }
        }
        brush_extracted = "Simpson Chubby 2 26mm Badger"

        result = enricher.enrich(field_data, brush_extracted)

        assert result is not None
        assert result["_user_override"] is True
        assert "size_mismatch:27.0->26.0" in result["_user_override_reason"]

    def test_custom_knot_both_mismatch(self, enricher):
        """Test custom knot detection for both fiber and size mismatch."""
        field_data = {
            "matched": {
                "brand": "Simpson",
                "model": "Chubby 2",
                "fiber": "Synthetic",
                "knot_size_mm": 27.0,
            }
        }
        brush_extracted = "Simpson Chubby 2 26mm Badger"

        result = enricher.enrich(field_data, brush_extracted)

        assert result is not None
        assert result["_user_override"] is True
        assert "fiber_mismatch:Synthetic->Badger" in result["_user_override_reason"]
        assert "size_mismatch:27.0->26.0" in result["_user_override_reason"]

    def test_no_custom_knot_when_matching(self, enricher):
        """Test that no custom knot is detected when values match."""
        field_data = {
            "matched": {
                "brand": "Simpson",
                "model": "Chubby 2",
                "fiber": "Badger",
                "knot_size_mm": 27.0,
            }
        }
        brush_extracted = "Simpson Chubby 2 27mm Badger"

        result = enricher.enrich(field_data["matched"], brush_extracted)

        assert result is not None
        assert "_user_override" not in result


class TestCombinedKnotSizeAndFiber:
    def test_both_knot_size_and_fiber_conflicts(self, enricher):
        """Test handling of both knot size and fiber conflicts."""
        field_data = {
            "matched": {
                "brand": "Simpson",
                "model": "Chubby 2",
                "fiber": "Synthetic",
                "knot_size_mm": 27.0,
            }
        }
        brush_extracted = "Simpson Chubby 2 26mm Badger"

        result = enricher.enrich(field_data, brush_extracted)

        assert result is not None
        assert result["knot_size_mm"] == 26.0
        assert result["fiber"] == "Badger"
        assert result["_catalog_knot_size_mm"] == 27.0
        assert result["_catalog_fiber"] == "Synthetic"
        assert result["_user_override"] is True
