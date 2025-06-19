#!/usr/bin/env python3
"""Base aggregation class to reduce code duplication in specialized aggregations."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import pandas as pd

from sotd.aggregate.dataframe_utils import optimize_dataframe_operations, optimized_groupby_agg
from sotd.aggregate.performance_monitor import PerformanceMonitor


class BaseAggregator(ABC):
    """
    Base class for product aggregations that provides common functionality.

    This class implements the template method pattern, allowing subclasses
    to define specific data extraction logic while inheriting common
    aggregation, validation, and error handling patterns.
    """

    def __init__(self, debug: bool = False):
        """Initialize the aggregator with debug flag."""
        self.debug = debug
        self.monitor = PerformanceMonitor(debug)

    def aggregate(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Main aggregation method that follows the template method pattern.

        Args:
            records: List of enriched comment records

        Returns:
            List of aggregation results

        Raises:
            ValueError: If records list is invalid or contains invalid data
        """
        self.monitor.start(self.get_operation_name())

        # Step 1: Validate input
        self._validate_input(records)

        if not records:
            self.monitor.end(self.get_operation_name(), 0)
            return []

        # Step 2: Extract data
        data = self._extract_data(records)

        if not data:
            if self.debug:
                print(f"[DEBUG] No valid {self.get_product_type()} data found")
            self.monitor.end(self.get_operation_name(), 0)
            return []

        # Step 3: Process data
        results = self._process_data(data)

        # Step 4: Log completion
        if self.debug:
            print(f"[DEBUG] Aggregated {len(results)} {self.get_product_type()}s")

        self.monitor.end(self.get_operation_name(), len(data))
        return results

    def _validate_input(self, records: List[Dict[str, Any]]) -> None:
        """Validate input records."""
        if not isinstance(records, list):
            raise ValueError(f"Expected list of records, got {type(records)}")

    def _extract_data(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract relevant data from records.

        Args:
            records: List of enriched comment records

        Returns:
            List of extracted data dictionaries
        """
        data = []
        invalid_records = 0

        for i, record in enumerate(records):
            if not isinstance(record, dict):
                if self.debug:
                    print(f"[DEBUG] Record {i}: Expected dict, got {type(record)}")
                invalid_records += 1
                continue

            extracted = self._extract_from_record(record, i)
            if extracted:
                data.append(extracted)
            else:
                invalid_records += 1

        if self.debug and invalid_records > 0:
            print(f"[DEBUG] Skipped {invalid_records} invalid records")

        return data

    def _process_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process extracted data using pandas aggregation.

        Args:
            data: List of extracted data dictionaries

        Returns:
            List of aggregation results
        """
        # Convert to DataFrame
        try:
            df = pd.DataFrame(data)
            df = optimize_dataframe_operations(df, self.debug)
        except (ValueError, TypeError, KeyError) as e:
            raise ValueError(
                f"Failed to create DataFrame for {self.get_product_type()} aggregation: {e}"
            )
        except ImportError as e:
            raise RuntimeError(
                f"Pandas import error during {self.get_product_type()} aggregation: {e}"
            )

        # Group and aggregate
        try:
            grouped = optimized_groupby_agg(
                df, self.get_group_column(), "user", ["count", "nunique"], self.debug
            )
        except (KeyError, ValueError) as e:
            raise ValueError(f"Failed to group {self.get_product_type()} data: {e}")
        except ImportError as e:
            raise RuntimeError(
                f"Pandas import error during {self.get_product_type()} grouping: {e}"
            )

        # Post-process results
        return self._post_process_results(grouped)

    def _post_process_results(self, grouped: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Post-process grouped results with common calculations.

        Args:
            grouped: Grouped DataFrame from pandas aggregation

        Returns:
            List of processed results
        """
        # Rename columns to standard format
        grouped.columns = [self.get_group_column(), "shaves", "unique_users"]

        # Calculate average shaves per user
        grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)

        # Sort by shaves (descending), then by unique_users (descending)
        grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])

        return list(grouped.to_dict("records"))  # type: ignore

    @abstractmethod
    def get_operation_name(self) -> str:
        """Return the operation name for monitoring."""
        pass

    @abstractmethod
    def get_product_type(self) -> str:
        """Return the product type being aggregated."""
        pass

    @abstractmethod
    def get_group_column(self) -> str:
        """Return the column name to group by."""
        pass

    @abstractmethod
    def _extract_from_record(
        self, record: Dict[str, Any], record_index: int
    ) -> Optional[Dict[str, Any]]:
        """
        Extract relevant data from a single record.

        Args:
            record: Single enriched comment record
            record_index: Index of the record for debugging

        Returns:
            Extracted data dictionary or None if invalid
        """
        pass

    def _validate_match_type(self, matched: Dict[str, Any], record_index: int) -> bool:
        """
        Validate match_type if present in matched data.

        Args:
            matched: Matched data dictionary
            record_index: Index of the record for debugging

        Returns:
            True if valid, False otherwise
        """
        if "match_type" in matched:
            match_type = matched["match_type"]
            valid_match_types = ["exact", "fuzzy", "manual", "unmatched"]
            if not isinstance(match_type, str) or match_type not in valid_match_types:
                if self.debug:
                    print(
                        f"[DEBUG] Record {record_index}: {self.get_product_type()}.match_type "
                        f"invalid: {match_type}"
                    )
                return False
        return True
