"""Tests for the HandleMakerAggregator."""

from sotd.aggregate.aggregators.brush_specialized.handle_maker_aggregator import (
    HandleMakerAggregator,
)


class TestHandleMakerAggregator:
    """Test the HandleMakerAggregator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.aggregator = HandleMakerAggregator()

    def test_extract_data_with_handle_subsection(self):
        """Test extraction when handle subsection is present."""
        records = [
            {
                "brush": {
                    "matched": {
                        "handle": {
                            "brand": "Chisel & Hound",
                            "model": "Morado",
                            "source_text": "Chisel & Hound Morado",
                        }
                    },
                    "enriched": {},
                },
                "author": "test_user",
            }
        ]

        result = self.aggregator._extract_data(records)

        assert len(result) == 1
        assert result[0]["handle_maker"] == "Chisel & Hound"
        assert result[0]["author"] == "test_user"

    def test_extract_data_with_complete_brush_fallback(self):
        """Test that complete brushes fall back to matched.brand when handle.brand is not present."""
        records = [
            {
                "brush": {
                    "matched": {
                        "brand": "Simpson",
                        "model": "Chubby 2",
                        "handle_maker": None,
                        "source_text": "Simpson Chubby 2",
                    },
                    "enriched": {},
                },
                "author": "test_user",
            }
        ]

        result = self.aggregator._extract_data(records)

        assert len(result) == 1
        assert result[0]["handle_maker"] == "Simpson"
        assert result[0]["author"] == "test_user"

    def test_extract_data_priority_handle_over_brand(self):
        """Test that matched.handle.brand takes priority over matched.brand."""
        records = [
            {
                "brush": {
                    "matched": {
                        "brand": "AP Shave Co",
                        "model": "G5C",
                        "handle": {
                            "brand": "Chisel & Hound",
                            "model": "Morado",
                            "source_text": "Chisel & Hound Morado",
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
        # Should use handle.brand (Chisel & Hound) not top-level brand (AP Shave Co)
        assert result[0]["handle_maker"] == "Chisel & Hound"
        assert result[0]["author"] == "test_user"

    def test_extract_data_mixed_scenarios(self):
        """Test mixed scenarios with both split and complete brushes."""
        records = [
            # Split brush with handle subsection
            {
                "brush": {
                    "matched": {
                        "brand": "AP Shave Co",
                        "handle": {"brand": "Chisel & Hound", "model": "Morado"},
                    },
                    "enriched": {},
                },
                "author": "test_user1",
            },
            # Complete brush without handle subsection
            {
                "brush": {"matched": {"brand": "Simpson", "model": "Chubby 2"}, "enriched": {}},
                "author": "test_user2",
            },
        ]

        result = self.aggregator._extract_data(records)

        assert len(result) == 2
        # First record should use handle.brand
        assert result[0]["handle_maker"] == "Chisel & Hound"
        # Second record should fall back to top-level brand
        assert result[1]["handle_maker"] == "Simpson"

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

    def test_extract_data_handle_brand_none(self):
        """Test that handle.brand = None falls back to top-level brand."""
        records = [
            {
                "brush": {
                    "matched": {
                        "brand": "Simpson",
                        "model": "Chubby 2",
                        "handle": {"brand": None, "model": "Chubby 2"},
                    },
                    "enriched": {},
                },
                "author": "test_user",
            }
        ]

        result = self.aggregator._extract_data(records)

        assert len(result) == 1
        assert result[0]["handle_maker"] == "Simpson"
