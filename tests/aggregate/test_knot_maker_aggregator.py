"""Tests for the KnotMakerAggregator."""

from sotd.aggregate.aggregators.brush_specialized.knot_maker_aggregator import KnotMakerAggregator


class TestKnotMakerAggregator:
    """Test the KnotMakerAggregator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.aggregator = KnotMakerAggregator()

    def test_extract_data_with_knot_subsection(self):
        """Test extraction when knot subsection is present."""
        records = [
            {
                "brush": {
                    "matched": {
                        "knot": {
                            "brand": "AP Shave Co",
                            "model": "G5C",
                            "source_text": "AP Shave Co G5C",
                        }
                    },
                    "enriched": {},
                },
                "author": "test_user",
            }
        ]

        result = self.aggregator._extract_data(records)

        assert len(result) == 1
        assert result[0]["brand"] == "AP Shave Co"
        assert result[0]["author"] == "test_user"

    def test_extract_data_with_complete_brush_fallback(self):
        """Test that complete brushes fall back to matched.brand when knot.brand is not present."""
        records = [
            {
                "brush": {
                    "matched": {
                        "brand": "Simpson",
                        "model": "Chubby 2",
                        "source_text": "Simpson Chubby 2",
                    },
                    "enriched": {},
                },
                "author": "test_user",
            }
        ]

        result = self.aggregator._extract_data(records)

        assert len(result) == 1
        assert result[0]["brand"] == "Simpson"
        assert result[0]["author"] == "test_user"

    def test_extract_data_priority_knot_over_brand(self):
        """Test that matched.knot.brand takes priority over matched.brand."""
        records = [
            {
                "brush": {
                    "matched": {
                        "brand": "Chisel & Hound",
                        "model": "Morado",
                        "knot": {
                            "brand": "AP Shave Co",
                            "model": "G5C",
                            "source_text": "AP Shave Co G5C",
                        },
                        "source_text": "Chisel & Hound / AP Shave Morado w/ G5C",
                    },
                    "enriched": {},
                },
                "author": "test_user",
            }
        ]

        result = self.aggregator._extract_data(records)

        assert len(result) == 1
        # Should use knot.brand (AP Shave Co) not top-level brand (Chisel & Hound)
        assert result[0]["brand"] == "AP Shave Co"
        assert result[0]["author"] == "test_user"

    def test_extract_data_mixed_scenarios(self):
        """Test mixed scenarios with both split and complete brushes."""
        records = [
            # Split brush with knot subsection
            {
                "brush": {
                    "matched": {
                        "brand": "Chisel & Hound",
                        "knot": {"brand": "AP Shave Co", "model": "G5C"},
                    },
                    "enriched": {},
                },
                "author": "test_user1",
            },
            # Complete brush without knot subsection
            {
                "brush": {"matched": {"brand": "Simpson", "model": "Chubby 2"}, "enriched": {}},
                "author": "test_user2",
            },
        ]

        result = self.aggregator._extract_data(records)

        assert len(result) == 2
        # First record should use knot.brand
        assert result[0]["brand"] == "AP Shave Co"
        # Second record should fall back to top-level brand
        assert result[1]["brand"] == "Simpson"

    def test_extract_data_no_brush_data(self):
        """Test handling of records without brush data."""
        records = [{"author": "test_user", "razor": {"matched": {"brand": "Gillette"}}}]

        result = self.aggregator._extract_data(records)

        assert len(result) == 0

    def test_extract_data_empty_brush(self):
        """Test handling of records with empty brush data."""
        records = [{"brush": None, "author": "test_user"}, {"brush": {}, "author": "test_user"}]

        result = self.aggregator._extract_data(records)

        assert len(result) == 0

    def test_extract_data_missing_matched(self):
        """Test handling of records with missing matched data."""
        records = [{"brush": {"enriched": {}}, "author": "test_user"}]

        result = self.aggregator._extract_data(records)

        assert len(result) == 0

    def test_extract_data_no_brand_fallback(self):
        """Test that records without any brand information are skipped."""
        records = [
            {
                "brush": {
                    "matched": {"model": "Chubby 2", "source_text": "Some brush"},
                    "enriched": {},
                },
                "author": "test_user",
            }
        ]

        result = self.aggregator._extract_data(records)

        assert len(result) == 0

    def test_extract_data_knot_brand_none(self):
        """Test that knot.brand = None falls back to top-level brand."""
        records = [
            {
                "brush": {
                    "matched": {
                        "brand": "Simpson",
                        "model": "Chubby 2",
                        "knot": {"brand": None, "model": "G5C"},
                    },
                    "enriched": {},
                },
                "author": "test_user",
            }
        ]

        result = self.aggregator._extract_data(records)

        assert len(result) == 1
        assert result[0]["brand"] == "Simpson"
