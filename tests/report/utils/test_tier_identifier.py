"""Tests for TierIdentifier utility class."""

from sotd.report.utils.tier_identifier import TierIdentifier


class TestTierIdentifier:
    """Test TierIdentifier utility class."""

    def test_identify_tiers_basic(self):
        """Test basic tier identification with sequential ranks."""
        data = [
            {"name": "Razor A", "rank": 1},
            {"name": "Razor B", "rank": 2},
            {"name": "Razor C", "rank": 3},
            {"name": "Razor D", "rank": 4},
        ]

        identifier = TierIdentifier()
        tiers = identifier.identify_tiers(data)

        # Should have 4 tiers
        assert len(tiers) == 4
        assert tiers[1] == ["Razor A"]
        assert tiers[2] == ["Razor B"]
        assert tiers[3] == ["Razor C"]
        assert tiers[4] == ["Razor D"]

    def test_identify_tiers_with_ties(self):
        """Test tier identification with tied items."""
        data = [
            {"name": "Razor A", "rank": 1},
            {"name": "Razor B", "rank": 2},
            {"name": "Razor C", "rank": 2},  # Tied with Razor B
            {"name": "Razor D", "rank": 3},
        ]

        identifier = TierIdentifier()
        tiers = identifier.identify_tiers(data)

        # Should have 3 tiers
        assert len(tiers) == 3
        assert tiers[1] == ["Razor A"]
        assert set(tiers[2]) == {"Razor B", "Razor C"}  # Tied items
        assert tiers[3] == ["Razor D"]

    def test_identify_tiers_complex_ties(self):
        """Test tier identification with complex tie patterns."""
        data = [
            {"name": "Razor A", "rank": 1},
            {"name": "Razor B", "rank": 2},
            {"name": "Razor C", "rank": 2},  # 2-way tie
            {"name": "Razor D", "rank": 2},  # 3-way tie
            {"name": "Razor E", "rank": 3},
            {"name": "Razor F", "rank": 3},  # 2-way tie
        ]

        identifier = TierIdentifier()
        tiers = identifier.identify_tiers(data)

        # Should have 3 tiers
        assert len(tiers) == 3
        assert tiers[1] == ["Razor A"]
        assert set(tiers[2]) == {"Razor B", "Razor C", "Razor D"}  # 3-way tie
        assert set(tiers[3]) == {"Razor E", "Razor F"}  # 2-way tie

    def test_get_tier_movement(self):
        """Test calculating movement between tiers for items."""
        current_data = [
            {"name": "Razor A", "rank": 1},
            {"name": "Razor B", "rank": 2},
            {"name": "Razor C", "rank": 2},  # Tied with Razor B
        ]

        historical_data = [
            {"name": "Razor A", "rank": 2},  # Was in Tier 2
            {"name": "Razor B", "rank": 1},  # Was in Tier 1
            {"name": "Razor C", "rank": 2},  # Still in Tier 2
        ]

        identifier = TierIdentifier()
        movement = identifier.get_tier_movement(current_data, historical_data)

        # Razor A: Tier 2 -> Tier 1 (improved by 1 tier)
        assert movement["Razor A"] == 1
        # Razor B: Tier 1 -> Tier 2 (worsened by 1 tier)
        assert movement["Razor B"] == -1
        # Razor C: Tier 2 -> Tier 2 (no change)
        assert movement["Razor C"] == 0

    def test_compare_tiers(self):
        """Test comparing tier structures between datasets."""
        current_data = [
            {"name": "Razor A", "rank": 1},
            {"name": "Razor B", "rank": 2},
            {"name": "Razor C", "rank": 2},
        ]

        historical_data = [
            {"name": "Razor A", "rank": 2},
            {"name": "Razor B", "rank": 1},
            {"name": "Razor C", "rank": 2},
        ]

        identifier = TierIdentifier()
        comparison = identifier.compare_tiers(current_data, historical_data)

        # Should show tier changes
        assert comparison["tier_changes"]["Razor A"] == (2, 1)  # (historical, current)
        assert comparison["tier_changes"]["Razor B"] == (1, 2)
        assert comparison["tier_changes"]["Razor C"] == (2, 2)

        # Should show tier structure changes
        assert comparison["tier_structure_changed"] is True

    def test_identify_tier_splits_and_merges(self):
        """Test identifying tier splits and merges."""
        current_data = [
            {"name": "Razor A", "rank": 1},  # Moved up from Tier 2
            {"name": "Razor B", "rank": 2},  # Still in Tier 2
            {"name": "Razor C", "rank": 2},  # Still in Tier 2
            {"name": "Razor D", "rank": 3},  # Moved down from Tier 2
        ]

        historical_data = [
            {"name": "Razor A", "rank": 2},  # Was in Tier 2 (tied)
            {"name": "Razor B", "rank": 2},  # Was in Tier 2 (tied)
            {"name": "Razor C", "rank": 2},  # Was in Tier 2 (tied)
            {"name": "Razor D", "rank": 2},  # Was in Tier 2 (tied)
        ]

        identifier = TierIdentifier()
        result = identifier.identify_tier_splits_and_merges(current_data, historical_data)

        # Should identify that Tier 2 split into multiple tiers
        assert result["restructured"] is True
        assert len(result["splits"]) == 1

        split = result["splits"][0]
        assert split["historical_tier"] == 2
        assert set(split["historical_items"]) == {"Razor A", "Razor B", "Razor C", "Razor D"}
        assert set(split["current_tiers"]) == {1, 2, 3}

    def test_identify_tier_merges(self):
        """Test identifying tier merges."""
        current_data = [
            {"name": "Razor A", "rank": 2},  # Now in merged Tier 2
            {"name": "Razor B", "rank": 2},  # Now in merged Tier 2
        ]

        historical_data = [
            {"name": "Razor A", "rank": 1},  # Was in Tier 1
            {"name": "Razor B", "rank": 3},  # Was in Tier 3
        ]

        identifier = TierIdentifier()
        result = identifier.identify_tier_splits_and_merges(current_data, historical_data)

        # Should identify that multiple historical tiers merged
        assert result["restructured"] is True
        assert len(result["merges"]) == 1

        merge = result["merges"][0]
        assert merge["current_tier"] == 2
        assert set(merge["current_items"]) == {"Razor A", "Razor B"}
        assert set(merge["historical_tiers"]) == {1, 3}

    def test_get_complex_tier_movement(self):
        """Test comprehensive tier movement information."""
        current_data = [
            {"name": "Razor A", "rank": 1},  # Moved up from Tier 2
            {"name": "Razor B", "rank": 2},  # Still in Tier 2
            {"name": "Razor C", "rank": 3},  # Moved down from Tier 2
        ]

        historical_data = [
            {"name": "Razor A", "rank": 2},  # Was in Tier 2 (tied)
            {"name": "Razor B", "rank": 2},  # Was in Tier 2 (tied)
            {"name": "Razor C", "rank": 2},  # Was in Tier 2 (tied)
        ]

        identifier = TierIdentifier()
        result = identifier.get_complex_tier_movement(current_data, historical_data)

        # Should include all movement information
        assert "movement" in result
        assert "tier_changes" in result
        assert "structure_changed" in result
        assert "splits" in result
        assert "merges" in result
        assert "restructured" in result

        # Should show tier structure changed
        assert result["structure_changed"] is True
        assert result["restructured"] is True

        # Should show movement details
        assert result["movement"]["Razor A"] == 1  # Improved
        assert result["movement"]["Razor B"] == 0  # No change
        assert result["movement"]["Razor C"] == -1  # Worsened

    def test_edge_cases_empty_data(self):
        """Test handling of empty data."""
        identifier = TierIdentifier()

        # Empty current data
        tiers = identifier.identify_tiers([])
        assert tiers == {}

        # Empty historical data
        movement = identifier.get_tier_movement([], [])
        assert movement == {}

    def test_edge_cases_single_item(self):
        """Test handling of single item data."""
        data = [{"name": "Razor A", "rank": 1}]

        identifier = TierIdentifier()
        tiers = identifier.identify_tiers(data)

        assert len(tiers) == 1
        assert tiers[1] == ["Razor A"]

    def test_edge_cases_all_tied(self):
        """Test handling when all items are tied."""
        data = [
            {"name": "Razor A", "rank": 1},
            {"name": "Razor B", "rank": 1},
            {"name": "Razor C", "rank": 1},
        ]

        identifier = TierIdentifier()
        tiers = identifier.identify_tiers(data)

        # Should have 1 tier with all items
        assert len(tiers) == 1
        assert set(tiers[1]) == {"Razor A", "Razor B", "Razor C"}

    def test_performance_with_large_datasets(self):
        """Test performance with large datasets."""
        # Create large dataset
        data = [
            {"name": f"Razor {i}", "rank": (i % 10) + 1} for i in range(100)  # 10 tiers, 100 items
        ]

        identifier = TierIdentifier()

        # Should complete within reasonable time
        import time

        start_time = time.time()
        tiers = identifier.identify_tiers(data)
        end_time = time.time()

        # Should complete in under 1 second
        assert end_time - start_time < 1.0

        # Should have correct tier structure
        assert len(tiers) == 10
        assert all(len(tier_items) == 10 for tier_items in tiers.values())
