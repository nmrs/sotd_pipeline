"""Test complete brush catalog loading and matching."""

from sotd.match.brush_matcher import BrushMatcher


class TestCompleteBrushCatalog:
    """Test that complete brush makers are properly loaded and matched."""

    def test_declaration_grooming_in_catalog(self):
        """Test that Declaration Grooming is properly loaded from brushes.yaml."""
        matcher = BrushMatcher()
        # Check that Declaration Grooming is in the catalog
        assert "Declaration Grooming" in matcher.catalog_data["known_brushes"]
        # Test matching a Declaration Grooming brush
        result = matcher.match("B15")
        assert result["matched"]["brand"] == "Declaration Grooming"
        assert result["matched"]["model"] == "B15"

    def test_chisel_and_hound_in_catalog(self):
        """Test that Chisel & Hound is properly loaded from brushes.yaml."""
        matcher = BrushMatcher()
        # Check that Chisel & Hound is in the catalog
        assert "Chisel & Hound" in matcher.catalog_data["known_brushes"]
        # Test matching a Chisel & Hound brush with version
        result = matcher.match("C&H v21")
        assert result["matched"]["brand"] == "Chisel & Hound"
        assert result["matched"]["model"] == "v21"

    def test_catalog_loading_handles_new_entries(self):
        """Test that catalog loading can handle new complete brush entries."""
        matcher = BrushMatcher()
        # Verify that the catalog data is loaded and has the expected structure
        assert isinstance(matcher.catalog_data, dict)
        assert len(matcher.catalog_data) > 0

        # Check that complete brush makers have the expected structure
        for brand in ["Declaration Grooming", "Chisel & Hound"]:
            if brand in matcher.catalog_data["known_brushes"]:
                brand_data = matcher.catalog_data["known_brushes"][brand]
                assert isinstance(brand_data, dict)
                # Should have fiber and knot_size_mm at brand level, and models with patterns
                assert "fiber" in brand_data
                assert "knot_size_mm" in brand_data
                # Check that at least one model has patterns
                has_model_with_patterns = False
                for model_data in brand_data.values():
                    if isinstance(model_data, dict) and "patterns" in model_data:
                        has_model_with_patterns = True
                        break
                assert (
                    has_model_with_patterns
                ), f"Brand {brand} should have at least one model with patterns"

    def test_complete_brush_patterns_match_correctly(self):
        """Test that complete brush patterns match correctly."""
        matcher = BrushMatcher()

        # Test Declaration Grooming patterns
        test_cases = [
            ("B15", "Declaration Grooming", "B15"),
            ("B3", "Declaration Grooming", "B3"),
            ("B10", "Declaration Grooming", "B10"),
        ]

        for input_text, expected_brand, expected_model in test_cases:
            result = matcher.match(input_text)
            assert result["matched"]["brand"] == expected_brand
            assert result["matched"]["model"] == expected_model

    def test_chisel_and_hound_batch_patterns(self):
        """Test that Chisel & Hound batch patterns work correctly."""
        matcher = BrushMatcher()

        # Test Chisel & Hound version patterns
        test_cases = [
            ("C&H v21", "Chisel & Hound", "v21"),
            ("Chisel & Hound v15", "Chisel & Hound", "v15"),
            ("CH v20", "Chisel & Hound", "v20"),
        ]

        for input_text, expected_brand, expected_model in test_cases:
            result = matcher.match(input_text)
            assert result["matched"]["brand"] == expected_brand
            assert result["matched"]["model"] == expected_model
