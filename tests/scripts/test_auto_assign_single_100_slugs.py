"""Unit tests for auto_assign_single_100_slugs script filter logic."""

from scripts.auto_assign_single_100_slugs import _filter_single_100_results


class TestFilterSingle100Results:
    """Test _filter_single_100_results selects only single 100% match entries."""

    def test_single_100_match_included(self):
        """Entry with exactly one match at 100% confidence is included."""
        pipeline_results = [
            {
                "source_brand": "Barrister and Mann",
                "source_scent": "Seville",
                "matches": [
                    {
                        "confidence": 100,
                        "details": {"slug": "barrister-and-mann-seville-soap"},
                    }
                ],
            }
        ]
        got = _filter_single_100_results(pipeline_results)
        assert len(got) == 1
        assert got[0]["source_brand"] == "Barrister and Mann"
        assert got[0]["source_scent"] == "Seville"
        assert got[0]["matches"][0]["details"]["slug"] == "barrister-and-mann-seville-soap"

    def test_one_100_with_95_ignored(self):
        """Entry with one 100% match is included; API may also return 95% (pattern) matches, we ignore them."""
        pipeline_results = [
            {
                "source_brand": "Ariana & Evans",
                "source_scent": "Vanille Vendetta",
                "matches": [
                    {"confidence": 100, "details": {"slug": "a-e-vanille-vendetta-soap"}},
                    {"confidence": 95, "details": {"slug": "a-e-tabac-de-vanille-soap"}},
                ],
            }
        ]
        got = _filter_single_100_results(pipeline_results)
        assert len(got) == 1
        hundred_pct = [m for m in got[0]["matches"] if m.get("confidence") == 100]
        assert hundred_pct[0]["details"]["slug"] == "a-e-vanille-vendetta-soap"

    def test_two_100_matches_excluded(self):
        """Entry with two matches at 100% is excluded (ambiguous)."""
        pipeline_results = [
            {
                "source_brand": "Some Brand",
                "source_scent": "Some Scent",
                "matches": [
                    {"confidence": 100, "details": {"slug": "slug-a-soap"}},
                    {"confidence": 100, "details": {"slug": "slug-b-soap"}},
                ],
            }
        ]
        got = _filter_single_100_results(pipeline_results)
        assert len(got) == 0

    def test_single_95_match_excluded(self):
        """Entry with exactly one match at 95% confidence is excluded."""
        pipeline_results = [
            {
                "source_brand": "Some Brand",
                "source_scent": "Some Scent",
                "matches": [{"confidence": 95, "details": {"slug": "some-brand-some-scent-soap"}}],
            }
        ]
        got = _filter_single_100_results(pipeline_results)
        assert len(got) == 0

    def test_single_100_no_slug_excluded(self):
        """Entry with one 100% match but missing details.slug is excluded."""
        pipeline_results = [
            {
                "source_brand": "Brand",
                "source_scent": "Scent",
                "matches": [{"confidence": 100, "details": {}}],
            }
        ]
        got = _filter_single_100_results(pipeline_results)
        assert len(got) == 0

    def test_empty_matches_excluded(self):
        """Entry with no matches is excluded."""
        pipeline_results = [{"source_brand": "Brand", "source_scent": "Scent", "matches": []}]
        got = _filter_single_100_results(pipeline_results)
        assert len(got) == 0

    def test_mixed_results_only_single_100_included(self):
        """From mixed list, entries with exactly one 100% match are returned; we ignore non-100% matches."""
        pipeline_results = [
            {
                "source_brand": "Barrister and Mann",
                "source_scent": "Seville",
                "matches": [
                    {"confidence": 100, "details": {"slug": "barrister-and-mann-seville-soap"}}
                ],
            },
            {
                "source_brand": "Ariana & Evans",
                "source_scent": "Vanille Vendetta",
                "matches": [
                    {"confidence": 100, "details": {"slug": "a-e-vanille-vendetta-soap"}},
                    {"confidence": 95, "details": {"slug": "a-e-other-soap"}},
                ],
            },
            {
                "source_brand": "Other Brand",
                "source_scent": "Other Scent",
                "matches": [{"confidence": 95, "details": {"slug": "other-soap"}}],
            },
        ]
        got = _filter_single_100_results(pipeline_results)
        assert len(got) == 2
        brands = {r["source_brand"] for r in got}
        assert "Barrister and Mann" in brands
        assert "Ariana & Evans" in brands
