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
            }
        }
        brush_extracted = "Simpson Chubby 2"

        result = enricher.enrich(field_data["matched"], brush_extracted)

        assert result is not None
        assert result["knot_size_mm"] == 27.0
        assert result["_enriched_by"] == "BrushEnricher"
        assert result["_extraction_source"] == "catalog"

    def test_enrich_with_user_knot_size_only(self, enricher):
        """Test enrichment when only user specifies knot size."""
        field_data = {
            "matched": {
                "brand": "Simpson",
                "model": "Chubby 2",
                "fiber": "Badger",
            }
        }
        brush_extracted = "Simpson Chubby 2 26mm"

        result = enricher.enrich(field_data["matched"], brush_extracted)

        assert result is not None
        assert result["knot_size_mm"] == 26.0
        assert result["_enriched_by"] == "BrushEnricher"
        assert result["_extraction_source"] == "user_comment"

    def test_enrich_with_matching_catalog_and_user(self, enricher):
        """Test enrichment when catalog and user knot sizes match."""
        field_data = {
            "matched": {
                "brand": "Simpson",
                "model": "Chubby 2",
                "fiber": "Badger",
                "knot_size_mm": 27.0,
            }
        }
        brush_extracted = "Simpson Chubby 2 27mm"

        result = enricher.enrich(field_data["matched"], brush_extracted)

        assert result is not None
        assert result["knot_size_mm"] == 27.0
        assert result["_enriched_by"] == "BrushEnricher"
        assert result["_extraction_source"] == "user_confirmed_catalog"

    def test_enrich_with_conflicting_catalog_and_user(self, enricher):
        """Test enrichment when catalog and user knot sizes conflict."""
        field_data = {
            "matched": {
                "brand": "Simpson",
                "model": "Chubby 2",
                "fiber": "Badger",
                "knot_size_mm": 27.0,
            }
        }
        brush_extracted = "Simpson Chubby 2 24mm"

        result = enricher.enrich(field_data["matched"], brush_extracted)

        assert result is not None
        assert result["knot_size_mm"] == 24.0  # User takes precedence
        assert result["_enriched_by"] == "BrushEnricher"
        assert result["_extraction_source"] == "user_override_catalog"
        assert result["_catalog_knot_size_mm"] == 27.0

    def test_enrich_with_no_knot_size(self, enricher):
        """Test enrichment when no knot size is available."""
        field_data = {
            "matched": {
                "brand": "Simpson",
                "model": "Chubby 2",
                "fiber": "Badger",
            }
        }
        brush_extracted = "Simpson Chubby 2"

        result = enricher.enrich(field_data["matched"], brush_extracted)

        assert result is not None
        assert result["knot_size_mm"] is None
        assert result["_enriched_by"] == "BrushEnricher"
        assert result["_extraction_source"] == "none"

    def test_enrich_with_invalid_field_data(self, enricher):
        """Test enrichment with invalid field data."""
        result = enricher.enrich(None, "Some comment")
        assert result is None

        result = enricher.enrich("not a dict", "Some comment")
        assert result is None

    def test_enrich_with_empty_comment(self, enricher):
        """Test enrichment with empty comment."""
        field_data = {
            "matched": {
                "brand": "Simpson",
                "model": "Chubby 2",
                "fiber": "Badger",
                "knot_size_mm": 27.0,
            }
        }
        brush_extracted = ""
        result = enricher.enrich(field_data["matched"], brush_extracted)
        assert result is None


class TestKnotSizeExtraction:
    def test_extract_knot_size_with_mm_suffix(self, enricher):
        """Test extraction of knot size with 'mm' suffix."""
        assert enricher._extract_knot_size("26mm brush") == 26.0
        assert enricher._extract_knot_size("27.5mm brush") == 27.5
        assert enricher._extract_knot_size("24 MM brush") == 24.0

    def test_extract_knot_size_with_dimensions(self, enricher):
        """Test extraction of knot size from dimension format."""
        assert enricher._extract_knot_size("27x50 brush") == 27.0
        assert enricher._extract_knot_size("28.5x50 brush") == 28.5
        assert enricher._extract_knot_size("26×50 brush") == 26.0  # Unicode ×

    def test_extract_knot_size_with_reasonable_range(self, enricher):
        """Test extraction of knot size in reasonable range (20-35mm)."""
        assert enricher._extract_knot_size("24 brush") == 24.0
        assert enricher._extract_knot_size("30 brush") == 30.0
        assert enricher._extract_knot_size("35 brush") == 35.0

    def test_extract_knot_size_outside_range(self, enricher):
        """Test that sizes outside reasonable range are not extracted."""
        assert enricher._extract_knot_size("19 brush") is None
        assert enricher._extract_knot_size("36 brush") is None
        assert enricher._extract_knot_size("100 brush") is None

    def test_extract_knot_size_priority(self, enricher):
        """Test that mm suffix takes priority over dimension format."""
        # Should prefer "26mm" over "27x50"
        assert enricher._extract_knot_size("26mm 27x50 brush") == 26.0

    def test_extract_knot_size_no_match(self, enricher):
        """Test extraction when no knot size is found."""
        assert enricher._extract_knot_size("Great brush") is None
        assert enricher._extract_knot_size("") is None
        assert enricher._extract_knot_size(None) is None

    def test_extract_knot_size_with_decimal(self, enricher):
        """Test extraction of decimal knot sizes."""
        assert enricher._extract_knot_size("26.5 brush") == 26.5
        assert enricher._extract_knot_size("27.5mm brush") == 27.5
        assert enricher._extract_knot_size("28.5x50 brush") == 28.5


class TestRealWorldExamples:
    def test_simpson_chubby_example(self, enricher):
        """Test with real Simpson Chubby example."""
        field_data = {
            "matched": {
                "brand": "Simpson",
                "model": "Chubby 2",
                "fiber": "Badger",
                "knot_size_mm": 27.0,  # From catalog
            }
        }
        brush_extracted = "Simpson Chubby 2 26mm"

        result = enricher.enrich(field_data["matched"], brush_extracted)

        assert result is not None
        assert result["knot_size_mm"] == 26.0  # User override
        assert result["_extraction_source"] == "user_override_catalog"
        assert result["_catalog_knot_size_mm"] == 27.0

    def test_omega_boar_example(self, enricher):
        """Test with real Omega boar example."""
        field_data = {
            "matched": {
                "brand": "Omega",
                "model": "10048",
                "fiber": "Boar",
                "knot_size_mm": 28.0,  # From catalog
            }
        }
        brush_extracted = "Omega 10048 28mm"

        result = enricher.enrich(field_data["matched"], brush_extracted)

        assert result is not None
        assert result["knot_size_mm"] == 28.0  # User confirms catalog
        assert result["_extraction_source"] == "user_confirmed_catalog"

    def test_custom_handle_example(self, enricher):
        """Test with custom handle example."""
        field_data = {
            "matched": {
                "brand": "Declaration Grooming",
                "model": "B3",
                "fiber": "Badger",
                # No catalog knot size
            }
        }
        brush_extracted = "Declaration Grooming B3 26mm"

        result = enricher.enrich(field_data["matched"], brush_extracted)

        assert result is not None
        assert result["knot_size_mm"] == 26.0
        assert result["_extraction_source"] == "user_comment"


class TestFiberExtraction:
    def test_extract_fiber_badger(self, enricher):
        """Test extraction of badger fiber types."""
        field_data = {"matched": {"brand": "Test", "model": "Test"}}
        assert enricher.enrich(field_data["matched"], "badger brush")["fiber"] == "Badger"
        assert enricher.enrich(field_data["matched"], "silvertip brush")["fiber"] == "Badger"
        assert enricher.enrich(field_data["matched"], "2 band brush")["fiber"] == "Badger"
        assert enricher.enrich(field_data["matched"], "shd brush")["fiber"] == "Badger"

    def test_extract_fiber_boar(self, enricher):
        """Test extraction of boar fiber types."""
        field_data = {"matched": {"brand": "Test", "model": "Test"}}
        assert enricher.enrich(field_data["matched"], "boar brush")["fiber"] == "Boar"
        assert enricher.enrich(field_data["matched"], "shoat brush")["fiber"] == "Boar"

    def test_extract_fiber_synthetic(self, enricher):
        """Test extraction of synthetic fiber types."""
        field_data = {"matched": {"brand": "Test", "model": "Test"}}
        assert enricher.enrich(field_data["matched"], "synthetic brush")["fiber"] == "Synthetic"
        assert enricher.enrich(field_data["matched"], "tuxedo brush")["fiber"] == "Synthetic"
        assert enricher.enrich(field_data["matched"], "cashmere brush")["fiber"] == "Synthetic"
        assert enricher.enrich(field_data["matched"], "quartermoon brush")["fiber"] == "Synthetic"

    def test_extract_fiber_mixed(self, enricher):
        """Test extraction of mixed fiber types."""
        field_data = {"matched": {"brand": "Test", "model": "Test"}}
        assert (
            enricher.enrich(field_data["matched"], "mixed badger boar")["fiber"]
            == "Mixed Badger/Boar"
        )
        assert (
            enricher.enrich(field_data["matched"], "hybrid brush")["fiber"] == "Mixed Badger/Boar"
        )

    def test_extract_fiber_horse(self, enricher):
        """Test extraction of horse fiber types."""
        field_data = {"matched": {"brand": "Test", "model": "Test"}}
        assert enricher.enrich(field_data["matched"], "horse brush")["fiber"] == "Horse"
        assert enricher.enrich(field_data["matched"], "horsehair brush")["fiber"] == "Horse"

    def test_extract_fiber_no_match(self, enricher):
        """Test extraction when no fiber is found."""
        field_data = {"matched": {"brand": "Test", "model": "Test"}}
        result = enricher.enrich(field_data["matched"], "Great brush")
        assert result["fiber"] is None
        # Empty string should return None from enricher
        result = enricher.enrich(field_data["matched"], "")
        assert result is None


class TestFiberConflictResolution:
    def test_fiber_user_confirms_catalog(self, enricher):
        """Test when user fiber matches catalog fiber."""
        field_data = {
            "matched": {
                "brand": "Simpson",
                "model": "Chubby 2",
                "fiber": "Badger",  # From catalog
            }
        }
        brush_extracted = "Simpson Chubby 2 badger"

        result = enricher.enrich(field_data["matched"], brush_extracted)

        assert result is not None
        assert result["fiber"] == "Badger"
        assert result["_fiber_extraction_source"] == "user_confirmed_catalog"

    def test_fiber_user_overrides_catalog(self, enricher):
        """Test when user fiber conflicts with catalog fiber."""
        field_data = {
            "matched": {
                "brand": "Simpson",
                "model": "Chubby 2",
                "fiber": "Badger",  # From catalog
            }
        }
        brush_extracted = "Simpson Chubby 2 synthetic"

        result = enricher.enrich(field_data["matched"], brush_extracted)

        assert result is not None
        assert result["fiber"] == "Synthetic"  # User takes precedence
        assert result["_fiber_extraction_source"] == "user_override_catalog"
        assert result["_catalog_fiber"] == "Badger"

    def test_fiber_user_only(self, enricher):
        """Test when only user specifies fiber."""
        field_data = {
            "matched": {
                "brand": "Elite",
                "model": "Badger",
                # No catalog fiber
            }
        }
        brush_extracted = "Elite Badger synthetic"

        result = enricher.enrich(field_data["matched"], brush_extracted)

        assert result is not None
        assert result["fiber"] == "Synthetic"
        assert result["_fiber_extraction_source"] == "user_comment"

    def test_fiber_catalog_only(self, enricher):
        """Test when only catalog has fiber."""
        field_data = {
            "matched": {
                "brand": "Simpson",
                "model": "Chubby 2",
                "fiber": "Badger",  # From catalog
            }
        }
        brush_extracted = "Simpson Chubby 2"

        result = enricher.enrich(field_data["matched"], brush_extracted)

        assert result is not None
        assert result["fiber"] == "Badger"
        # No _fiber_extraction_source since no user fiber was extracted


class TestCustomKnotDetection:
    def test_custom_knot_fiber_mismatch(self, enricher):
        """Test custom knot detection when fiber differs from catalog."""
        field_data = {
            "matched": {
                "brand": "Simpson",
                "model": "Chubby 2",
                "knot": {
                    "brand": "Simpson",
                    "model": "Chubby 2",
                    "fiber": "Badger",  # Catalog default
                    "knot_size_mm": 27.0,
                },
            }
        }
        brush_extracted = "Simpson Chubby 2 28mm Boar"  # User says Boar, catalog says Badger

        result = enricher.enrich(field_data["matched"], brush_extracted)

        assert result is not None
        assert result["_custom_knot"] is True
        assert "fiber_mismatch:Badger->Boar" in result["_custom_knot_reason"]
        assert "size_mismatch:27.0->28.0" in result["_custom_knot_reason"]
        assert result["fiber"] == "Boar"  # User fiber takes precedence
        assert result["knot_size_mm"] == 28.0  # User size takes precedence

    def test_custom_knot_size_mismatch(self, enricher):
        """Test custom knot detection when size differs from catalog."""
        field_data = {
            "matched": {
                "brand": "Simpson",
                "model": "Chubby 2",
                "knot": {
                    "brand": "Simpson",
                    "model": "Chubby 2",
                    "fiber": "Badger",
                    "knot_size_mm": 27.0,  # Catalog default
                },
            }
        }
        brush_extracted = "Simpson Chubby 2 24mm"  # User says 24mm, catalog says 27mm

        result = enricher.enrich(field_data["matched"], brush_extracted)

        assert result is not None
        assert result["_custom_knot"] is True
        assert "size_mismatch:27.0->24.0" in result["_custom_knot_reason"]
        assert result["knot_size_mm"] == 24.0  # User size takes precedence

    def test_custom_knot_both_mismatch(self, enricher):
        """Test custom knot detection when both fiber and size differ from catalog."""
        field_data = {
            "matched": {
                "brand": "Simpson",
                "model": "Chubby 2",
                "knot": {
                    "brand": "Simpson",
                    "model": "Chubby 2",
                    "fiber": "Badger",  # Catalog default
                    "knot_size_mm": 27.0,  # Catalog default
                },
            }
        }
        brush_extracted = "Simpson Chubby 2 24mm Synthetic"  # User says Synthetic 24mm

        result = enricher.enrich(field_data["matched"], brush_extracted)

        assert result is not None
        assert result["_custom_knot"] is True
        assert "fiber_mismatch:Badger->Synthetic" in result["_custom_knot_reason"]
        assert "size_mismatch:27.0->24.0" in result["_custom_knot_reason"]
        assert result["fiber"] == "Synthetic"
        assert result["knot_size_mm"] == 24.0

    def test_no_custom_knot_when_matching(self, enricher):
        """Test that custom knot is not detected when user data matches catalog."""
        field_data = {
            "matched": {
                "brand": "Simpson",
                "model": "Chubby 2",
                "knot": {
                    "brand": "Simpson",
                    "model": "Chubby 2",
                    "fiber": "Badger",
                    "knot_size_mm": 27.0,
                },
            }
        }
        brush_extracted = "Simpson Chubby 2 27mm Badger"  # User confirms catalog

        result = enricher.enrich(field_data["matched"], brush_extracted)

        assert result is not None
        assert result.get("_custom_knot") is None  # No custom knot detected
        assert result.get("_modify_brush_structure") is None
        assert result["fiber"] == "Badger"
        assert result["knot_size_mm"] == 27.0


class TestCombinedKnotSizeAndFiber:
    def test_both_knot_size_and_fiber_conflicts(self, enricher):
        """Test handling both knot size and fiber conflicts."""
        field_data = {
            "matched": {
                "brand": "Simpson",
                "model": "Chubby 2",
                "fiber": "Badger",  # From catalog
                "knot_size_mm": 27.0,  # From catalog
            }
        }
        brush_extracted = "Simpson Chubby 2 24mm synthetic"

        result = enricher.enrich(field_data["matched"], brush_extracted)

        assert result is not None
        # Knot size conflict
        assert result["knot_size_mm"] == 24.0
        assert result["_extraction_source"] == "user_override_catalog"
        assert result["_catalog_knot_size_mm"] == 27.0
        # Fiber conflict
        assert result["fiber"] == "Synthetic"
        assert result["_fiber_extraction_source"] == "user_override_catalog"
        assert result["_catalog_fiber"] == "Badger"
