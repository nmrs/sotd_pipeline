#!/usr/bin/env python3
"""Table size limiter for enhanced report templates."""

from typing import Any, Dict, List


class TableSizeLimiter:
    """Applies table size limits with smart tie handling."""

    def apply_size_limits(
        self, data: List[Dict[str, Any]], parameters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply size limits to the data.

        Args:
            data: List of data records
            parameters: Dictionary of size limit parameters

        Returns:
            Data with size limits applied
        """
        if not parameters:
            return data

        if not data:
            return data

        # Apply rank limit first (more restrictive)
        if "ranks" in parameters:
            data = self.apply_rank_limit(data, parameters["ranks"])

        # Apply row limit
        if "rows" in parameters:
            data = self.apply_row_limit(data, parameters["rows"])

        return data

    def apply_row_limit(self, data: List[Dict[str, Any]], max_rows: int) -> List[Dict[str, Any]]:
        """Apply row limit with smart tie handling.

        Args:
            data: List of data records
            max_rows: Maximum number of rows

        Returns:
            Data with row limit applied
        """
        if not data or max_rows <= 0:
            return []

        if len(data) <= max_rows:
            return data

        # Find the cutoff point that respects ties
        cutoff_rank = data[max_rows - 1]["rank"]

        # Check if including the tie would exceed the limit
        tie_count = 0
        for item in data:
            if item["rank"] == cutoff_rank:
                tie_count += 1

        # If including the tie would exceed the limit by more than 50%, stop before it
        if tie_count > 1:
            # Count how many items we would have if we included the tie
            items_up_to_cutoff = 0
            for item in data:
                if item["rank"] <= cutoff_rank:
                    items_up_to_cutoff += 1
                else:
                    break

            # Allow ties if they don't exceed the limit by more than 50%
            max_allowed = max_rows + (max_rows // 2)
            if items_up_to_cutoff > max_allowed:
                # Find the rank before the tie
                for i in range(max_rows - 1, -1, -1):
                    if data[i]["rank"] < cutoff_rank:
                        cutoff_rank = data[i]["rank"]
                        break

        # Include all items up to and including the cutoff rank
        result = []
        for item in data:
            if item["rank"] <= cutoff_rank:
                result.append(item)
            else:
                break

        return result

    def apply_rank_limit(self, data: List[Dict[str, Any]], max_ranks: int) -> List[Dict[str, Any]]:
        """Apply rank limit with smart tie handling.

        Args:
            data: List of data records
            max_ranks: Maximum number of ranks

        Returns:
            Data with rank limit applied
        """
        if not data or max_ranks <= 0:
            return []

        # Find the highest rank in the data
        max_rank_in_data = max(item["rank"] for item in data)

        # If the highest rank is already within the limit, return all data
        if max_rank_in_data <= max_ranks:
            return data

        # Find the cutoff rank - include all items with rank <= max_ranks
        cutoff_rank = max_ranks

        # Include all items up to and including the cutoff rank
        result = []
        for item in data:
            if item["rank"] <= cutoff_rank:
                result.append(item)
            else:
                break

        return result
