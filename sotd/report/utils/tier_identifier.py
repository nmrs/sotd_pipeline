"""Tier identification and movement calculation utilities."""

from typing import Any, Dict, List


class TierIdentifier:
    """Utility class for identifying and managing tiers in ranking data."""

    def identify_tiers(self, data: List[Dict[str, Any]]) -> Dict[int, List[str]]:
        """
        Identify tiers based on ranking data.

        Args:
            data: List of items with "rank" field

        Returns:
            Dictionary mapping tier numbers to lists of item names
        """
        if not data:
            return {}

        tiers: Dict[int, List[str]] = {}

        for item in data:
            rank = item.get("rank")
            name = item.get("name")

            if rank is not None and name:
                if rank not in tiers:
                    tiers[rank] = []
                tiers[rank].append(name)

        return tiers

    def get_tier_movement(
        self, current_data: List[Dict[str, Any]], historical_data: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Calculate movement between tiers for items.

        Args:
            current_data: Current ranking data
            historical_data: Historical ranking data

        Returns:
            Dictionary mapping item names to tier movement
            (positive = improved, negative = worsened)
        """
        if not current_data or not historical_data:
            return {}

        # Create name to rank mappings
        current_ranks = {
            item["name"]: item["rank"] for item in current_data if "name" in item and "rank" in item
        }
        historical_ranks = {
            item["name"]: item["rank"]
            for item in historical_data
            if "name" in item and "rank" in item
        }

        movement = {}

        # Calculate movement for items in current data
        for name, current_rank in current_ranks.items():
            if name in historical_ranks:
                historical_rank = historical_ranks[name]
                # Positive delta means improved (moved to lower rank number)
                # Negative delta means worsened (moved to higher rank number)
                movement[name] = historical_rank - current_rank
            else:
                # New item, no movement
                movement[name] = 0

        return movement

    def compare_tiers(
        self, current_data: List[Dict[str, Any]], historical_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare tier structures between current and historical data.

        Args:
            current_data: Current ranking data
            historical_data: Historical ranking data

        Returns:
            Dictionary with tier comparison information
        """
        if not current_data or not historical_data:
            return {"tier_changes": {}, "tier_structure_changed": False}

        # Create name to rank mappings
        current_ranks = {
            item["name"]: item["rank"] for item in current_data if "name" in item and "rank" in item
        }
        historical_ranks = {
            item["name"]: item["rank"]
            for item in historical_data
            if "name" in item and "rank" in item
        }

        tier_changes = {}
        tier_structure_changed = False

        # Compare tiers for items in both datasets
        for name in set(current_ranks.keys()) & set(historical_ranks.keys()):
            current_rank = current_ranks[name]
            historical_rank = historical_ranks[name]

            if current_rank != historical_rank:
                tier_structure_changed = True
                tier_changes[name] = (historical_rank, current_rank)
            else:
                tier_changes[name] = (historical_rank, current_rank)

        return {"tier_changes": tier_changes, "tier_structure_changed": tier_structure_changed}

    def identify_tier_splits_and_merges(
        self, current_data: List[Dict[str, Any]], historical_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Identify tier splits and merges between current and historical data.

        Args:
            current_data: Current ranking data
            historical_data: Historical ranking data

        Returns:
            Dictionary with tier split/merge information
        """
        if not current_data or not historical_data:
            return {"splits": [], "merges": [], "restructured": False}

        current_tiers = self.identify_tiers(current_data)
        historical_tiers = self.identify_tiers(historical_data)

        splits = []
        merges = []
        restructured = False

        # Identify splits: historical tier that became multiple current tiers
        for hist_rank, hist_items in historical_tiers.items():
            current_ranks_for_items = set()
            for item_name in hist_items:
                # Find current rank for this item
                for current_item in current_data:
                    if current_item.get("name") == item_name:
                        current_ranks_for_items.add(current_item.get("rank"))
                        break

            if len(current_ranks_for_items) > 1:
                # This historical tier split into multiple current tiers
                splits.append(
                    {
                        "historical_tier": hist_rank,
                        "historical_items": hist_items,
                        "current_tiers": list(current_ranks_for_items),
                    }
                )
                restructured = True

        # Identify merges: multiple historical tiers that became single current tier
        for current_rank, current_items in current_tiers.items():
            historical_ranks_for_items = set()
            for item_name in current_items:
                # Find historical rank for this item
                for historical_item in historical_data:
                    if historical_item.get("name") == item_name:
                        historical_ranks_for_items.add(historical_item.get("rank"))
                        break

            if len(historical_ranks_for_items) > 1:
                # Multiple historical tiers merged into this current tier
                merges.append(
                    {
                        "current_tier": current_rank,
                        "current_items": current_items,
                        "historical_tiers": list(historical_ranks_for_items),
                    }
                )
                restructured = True

        return {"splits": splits, "merges": merges, "restructured": restructured}

    def get_complex_tier_movement(
        self, current_data: List[Dict[str, Any]], historical_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get comprehensive tier movement information including splits and merges.

        Args:
            current_data: Current ranking data
            historical_data: Historical ranking data

        Returns:
            Dictionary with comprehensive tier movement information
        """
        basic_movement = self.get_tier_movement(current_data, historical_data)
        tier_comparison = self.compare_tiers(current_data, historical_data)
        splits_merges = self.identify_tier_splits_and_merges(current_data, historical_data)

        return {
            "movement": basic_movement,
            "tier_changes": tier_comparison["tier_changes"],
            "structure_changed": tier_comparison["tier_structure_changed"],
            "splits": splits_merges["splits"],
            "merges": splits_merges["merges"],
            "restructured": splits_merges["restructured"],
        }
