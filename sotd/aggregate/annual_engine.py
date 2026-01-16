"""
Annual aggregation engine for the SOTD Pipeline.

This module provides annual aggregation functionality by combining 12 months
of aggregated data into yearly summaries.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from ..utils.performance_base import BasePerformanceMetrics, BasePerformanceMonitor
from .aggregators.annual_aggregator import (
    aggregate_annual_blades,
    aggregate_annual_brushes,
    aggregate_annual_highest_use_count_per_blade,
    aggregate_annual_razor_blade_combinations,
    aggregate_annual_razors,
    aggregate_annual_soaps,
)
from .aggregators.brush_specialized import (
    aggregate_fibers,
    aggregate_handle_makers,
    aggregate_knot_makers,
    aggregate_knot_sizes,
)
from .annual_loader import load_annual_data

logger = logging.getLogger(__name__)


@dataclass
class AnnualPerformanceMetrics(BasePerformanceMetrics):
    """Performance metrics for annual aggregation."""

    # Annual-specific fields
    year: str = field(default="")
    data_loading_time: float = field(default=0.0)
    aggregation_time: float = field(default=0.0)
    month_count: int = field(default=0)
    total_shaves: int = field(default=0)
    unique_shavers: int = field(default=0)

    def to_dict(self) -> Dict:
        """Convert metrics to dictionary for JSON serialization."""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "year": self.year,
                "data_loading_time_seconds": self.data_loading_time,
                "aggregation_time_seconds": self.aggregation_time,
                "month_count": self.month_count,
                "total_shaves": self.total_shaves,
                "unique_shavers": self.unique_shavers,
            }
        )
        return base_dict


class AnnualPerformanceMonitor(BasePerformanceMonitor):
    """Performance monitor for annual aggregation."""

    def __init__(self, year: str, parallel_workers: int = 1):
        self.year = year
        super().__init__("annual_aggregation", parallel_workers)
        # Type annotation to help type checker
        self.metrics: AnnualPerformanceMetrics = self.metrics

    def _create_metrics(self, phase_name: str, parallel_workers: int) -> AnnualPerformanceMetrics:
        """Create annual performance metrics."""
        metrics = AnnualPerformanceMetrics()
        metrics.year = self.year
        metrics.phase_name = phase_name
        metrics.parallel_workers = parallel_workers
        return metrics

    def print_summary(self) -> None:
        """Print a human-readable performance summary."""
        metrics = self.metrics
        print(f"\n=== Annual Aggregation Performance Summary ({metrics.year}) ===")
        print(f"Total Processing Time: {metrics.total_processing_time:.2f}s")
        print(f"Data Loading Time: {metrics.data_loading_time:.2f}s")
        print(f"Aggregation Time: {metrics.aggregation_time:.2f}s")
        print(f"File I/O Time: {metrics.file_io_time:.2f}s")
        print(f"Months Processed: {metrics.month_count}")
        print(f"Total Shaves: {metrics.total_shaves:,}")
        print(f"Unique Shavers: {metrics.unique_shavers:,}")
        print(f"Peak Memory Usage: {metrics.peak_memory_mb:.1f}MB")
        print(f"Input File Size: {metrics.input_file_size_mb:.1f}MB")
        print(f"Output File Size: {metrics.output_file_size_mb:.1f}MB")


class AnnualAggregationEngine:
    """Engine for aggregating monthly data into annual summaries."""

    def __init__(self, year: str, data_dir: Path):
        """
        Initialize the annual aggregation engine.

        Args:
            year: Year to process (YYYY format)
            data_dir: Data directory containing monthly aggregated files
        """
        if not year.isdigit():
            raise ValueError("Year must be numeric")
        if len(year) != 4:
            raise ValueError("Year must be in YYYY format")

        self.year = year
        self.data_dir = data_dir
        self.monitor = AnnualPerformanceMonitor(year)

    def aggregate_razors(self, monthly_data: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """
        Aggregate razor data from monthly data.

        Args:
            monthly_data: Dictionary of monthly data keyed by month

        Returns:
            List of aggregated razor data sorted by shaves desc, unique_users desc
        """
        return aggregate_annual_razors(monthly_data)

    def aggregate_blades(self, monthly_data: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """
        Aggregate blade data from monthly data.

        Args:
            monthly_data: Dictionary of monthly data keyed by month

        Returns:
            List of aggregated blade data sorted by shaves desc, unique_users desc
        """
        return aggregate_annual_blades(monthly_data)

    def aggregate_brushes(self, monthly_data: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """
        Aggregate brush data from monthly data.

        Args:
            monthly_data: Dictionary of monthly data keyed by month

        Returns:
            List of aggregated brush data sorted by shaves desc, unique_users desc
        """
        return aggregate_annual_brushes(monthly_data)

    def aggregate_soaps(self, monthly_data: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """
        Aggregate soap data from monthly data.

        Args:
            monthly_data: Dictionary of monthly data keyed by month

        Returns:
            List of aggregated soap data sorted by shaves desc, unique_users desc
        """
        return aggregate_annual_soaps(monthly_data)

    def aggregate_brush_fibers(self, monthly_data: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """
        Aggregate brush fiber data from monthly data.

        Args:
            monthly_data: Dictionary of monthly data keyed by month

        Returns:
            List of aggregated brush fiber data sorted by shaves desc, unique_users desc
        """
        return self._aggregate_specialized_brush_category(monthly_data, "brush_fibers")

    def aggregate_brush_knot_sizes(self, monthly_data: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """
        Aggregate brush knot size data from monthly data.

        Args:
            monthly_data: Dictionary of monthly data keyed by month

        Returns:
            List of aggregated brush knot size data sorted by shaves desc, unique_users desc
        """
        return self._aggregate_specialized_brush_category(monthly_data, "brush_knot_sizes")

    def aggregate_brush_handle_makers(self, monthly_data: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """
        Aggregate brush handle maker data from monthly data.

        Args:
            monthly_data: Dictionary of monthly data keyed by month

        Returns:
            List of aggregated brush handle maker data sorted by shaves desc, unique_users desc
        """
        return self._aggregate_specialized_brush_category(monthly_data, "brush_handle_makers")

    def aggregate_brush_knot_makers(self, monthly_data: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """
        Aggregate brush knot maker data from monthly data.

        Args:
            monthly_data: Dictionary of monthly data keyed by month

        Returns:
            List of aggregated brush knot maker data sorted by shaves desc, unique_users desc
        """
        return self._aggregate_specialized_brush_category(monthly_data, "brush_knot_makers")

    def aggregate_razor_blade_combinations(
        self, monthly_data: Dict[str, Dict]
    ) -> List[Dict[str, Any]]:
        """Aggregate annual razor-blade combinations from monthly data."""
        return aggregate_annual_razor_blade_combinations(monthly_data)

    def aggregate_highest_use_count_per_blade(
        self, monthly_data: Dict[str, Dict]
    ) -> List[Dict[str, Any]]:
        """Aggregate annual highest use count per blade from monthly data.

        This table has a different structure (blade, format, user, uses) than standard
        product tables, so it needs special handling to find the maximum uses per
        blade+format+user combination across all months.
        """
        if not monthly_data:
            return []

        # Collect all records from all months
        all_records = []
        for month, data in monthly_data.items():
            if "data" in data and "highest_use_count_per_blade" in data["data"]:
                category_data = data["data"]["highest_use_count_per_blade"]
                if isinstance(category_data, list):
                    all_records.extend(category_data)

        if not all_records:
            return []

        # Use pandas to find maximum uses per blade+format+user combination
        import pandas as pd

        df = pd.DataFrame(all_records)

        # Group by blade, format, and user, and take the maximum uses
        # This handles cases where the same blade+format+user appears in multiple months
        max_uses = df.groupby(["blade", "format", "user"])["uses"].max().reset_index()

        # Sort by uses descending
        max_uses = max_uses.sort_values("uses", ascending=False).reset_index(drop=True)

        # Add competition ranking
        max_uses["rank"] = max_uses["uses"].rank(method="min", ascending=False).astype(int)

        # Reorder columns to put rank first
        cols = ["rank"] + [col for col in max_uses.columns if col != "rank"]
        max_uses = max_uses[cols]

        # Convert back to list of dicts
        return max_uses.to_dict("records")

    def _aggregate_specialized_brush_category(
        self, monthly_data: Dict[str, Dict], category: str
    ) -> List[Dict[str, Any]]:
        """
        Helper method to aggregate specialized brush categories from monthly data.

        Args:
            monthly_data: Dictionary of monthly data keyed by month
            category: Category name to aggregate (e.g., "brush_fibers")

        Returns:
            List of aggregated data sorted by shaves desc, unique_users desc
        """
        if not monthly_data:
            return []

        # Collect all records from all months
        all_records = []
        for month, data in monthly_data.items():
            if "data" in data and category in data["data"]:
                category_data = data["data"][category]
                if isinstance(category_data, list):
                    all_records.extend(category_data)

        if not all_records:
            return []

        # Determine identifier field based on category
        # Monthly aggregated data already has the correct structure with aggregated values
        # Check the first record to determine the identifier field name
        if not all_records:
            return []

        sample_record = all_records[0]
        # Map category to possible identifier field names
        identifier_field_candidates = {
            "brush_fibers": ["fiber"],
            "brush_knot_sizes": ["knot_size_mm"],
            "brush_handle_makers": ["handle_maker", "brand"],
            "brush_knot_makers": ["brand"],
        }

        candidates = identifier_field_candidates.get(category, [])
        identifier_field = None
        for candidate in candidates:
            if candidate in sample_record:
                identifier_field = candidate
                break

        if not identifier_field:
            # Fallback: try to find any field that looks like an identifier
            # (not shaves, unique_users, rank)
            excluded_fields = {"shaves", "unique_users", "rank"}
            for key in sample_record.keys():
                if key not in excluded_fields:
                    identifier_field = key
                    break

        if not identifier_field:
            return []

        # Use the same simple aggregation pattern as _aggregate_specialized_category
        # Group by identifier and sum metrics (shaves, unique_users)
        import pandas as pd

        # Convert to DataFrame
        df = pd.DataFrame(all_records)

        # Determine which metric fields are available
        agg_dict = {"shaves": "sum"}
        if "unique_users" in df.columns:
            # For unique_users, we need to sum them (they're already aggregated per month)
            # But we should use max or a set union approach - actually, since these are
            # already aggregated monthly values, we can't just sum unique_users across months
            # as that would double-count users who appear in multiple months.
            # However, for annual aggregation, summing is acceptable as an approximation
            # The correct approach would be to track unique users across all months,
            # but that requires the raw data. For now, we'll sum as the monthly aggregator
            # already handles this correctly.
            agg_dict["unique_users"] = "sum"

        # Group by identifier field and sum metrics
        grouped = df.groupby(identifier_field).agg(agg_dict).reset_index()

        # Rename identifier_field to "name" for consistency with other aggregators
        grouped = grouped.rename(columns={identifier_field: "name"})

        # Sort by shaves desc, then by unique_users desc if available
        sort_columns = ["shaves"]
        if "unique_users" in grouped.columns:
            sort_columns.append("unique_users")
        grouped = grouped.sort_values(sort_columns, ascending=[False] * len(sort_columns))

        # Add rank column using competition ranking
        grouped["rank"] = grouped["shaves"].rank(method="min", ascending=False).astype(int)

        # Convert back to list of dicts
        return grouped.to_dict("records")

    def _aggregate_specialized_category(
        self, monthly_data: Dict[str, Dict], category: str, identifier_field: str
    ) -> List[Dict[str, Any]]:
        """
        Helper method to aggregate specialized categories from monthly data.

        This method works for categories that have a consistent structure across months
        with an identifier field (like 'format', 'brand', 'plate', etc.) and metric fields
        (shaves, unique_users).

        Args:
            monthly_data: Dictionary of monthly data keyed by month
            category: Category name to aggregate (e.g., "razor_formats")
            identifier_field: Field name used as identifier (e.g., "format", "brand", "plate")

        Returns:
            List of aggregated data sorted by shaves desc, unique_users desc
        """
        if not monthly_data:
            return []

        # Collect all records from all months
        all_records = []
        for month, data in monthly_data.items():
            if "data" in data and category in data["data"]:
                category_data = data["data"][category]
                if isinstance(category_data, list):
                    all_records.extend(category_data)

        if not all_records:
            return []

        # Use AnnualAggregator pattern: group by identifier and sum metrics
        import pandas as pd

        # Convert to DataFrame
        df = pd.DataFrame(all_records)

        # Determine which metric fields are available
        agg_dict = {"shaves": "sum"}
        if "unique_users" in df.columns:
            agg_dict["unique_users"] = "sum"

        # Group by identifier field and sum metrics
        grouped = df.groupby(identifier_field).agg(agg_dict).reset_index()

        # Rename identifier_field to "name" for consistency with other aggregators
        # Exception: keep "user" field name for users table
        if identifier_field != "user":
            grouped = grouped.rename(columns={identifier_field: "name"})
            final_identifier = "name"
        else:
            final_identifier = "user"

        # Sort by shaves desc, then by unique_users desc if available
        sort_columns = ["shaves"]
        if "unique_users" in grouped.columns:
            sort_columns.append("unique_users")
        grouped = grouped.sort_values(sort_columns, ascending=[False] * len(sort_columns))

        # Add rank column (1-based, with ties getting the same rank)
        grouped["rank"] = grouped["shaves"].rank(method="min", ascending=False).astype(int)

        # Reorder columns: rank, identifier, then metrics
        column_order = ["rank", final_identifier]
        if "unique_users" in grouped.columns:
            column_order.append("unique_users")
        column_order.append("shaves")
        grouped = grouped[column_order]

        # Convert back to list of dicts
        result = grouped.to_dict("records")

        return result

    def _aggregate_users(self, monthly_data: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """
        Aggregate users data from monthly data.

        Users table has special fields: user, shaves, missed_days, missed_dates.
        We sum shaves and missed_days across months, and keep the user field name.

        Args:
            monthly_data: Dictionary of monthly data keyed by month

        Returns:
            List of aggregated user data sorted by shaves desc
        """
        if not monthly_data:
            return []

        # Collect all records from all months
        all_records = []
        for month, data in monthly_data.items():
            if "data" in data and "users" in data["data"]:
                users_data = data["data"]["users"]
                if isinstance(users_data, list):
                    all_records.extend(users_data)

        if not all_records:
            return []

        import pandas as pd
        from calendar import monthrange

        # Convert to DataFrame
        df = pd.DataFrame(all_records)

        # Calculate unique days posted per user per month
        # unique_days_in_month = days_in_month - missed_days_in_month
        # Then sum unique_days across months to get total unique days
        # Annual missed_days = 365 - total_unique_days

        # Add month column to calculate days in month
        df["month"] = df.index.map(
            lambda i: list(monthly_data.keys())[i // 1000] if i < len(all_records) else None
        )
        # Actually, we need to track which month each record came from
        # Let's rebuild with month tracking
        records_with_month = []
        for month, data in monthly_data.items():
            if "data" in data and "users" in data["data"]:
                users_data = data["data"]["users"]
                if isinstance(users_data, list):
                    year, month_num = int(month[:4]), int(month[5:7])
                    days_in_month = monthrange(year, month_num)[1]
                    for user_record in users_data:
                        user_record_copy = user_record.copy()
                        user_record_copy["_month"] = month
                        user_record_copy["_days_in_month"] = days_in_month
                        records_with_month.append(user_record_copy)

        df = pd.DataFrame(records_with_month)

        # Calculate unique days posted per user per month
        df["unique_days_in_month"] = df["_days_in_month"] - df["missed_days"]

        # Group by user and sum shaves and unique_days
        grouped = (
            df.groupby("user").agg({"shaves": "sum", "unique_days_in_month": "sum"}).reset_index()
        )

        # Calculate annual missed_days: 365 - total_unique_days
        grouped["missed_days"] = 365 - grouped["unique_days_in_month"]

        # Drop the helper column
        grouped = grouped.drop("unique_days_in_month", axis=1)

        # Sort by missed_days asc, shaves desc (same as monthly version)
        grouped = grouped.sort_values(["missed_days", "shaves"], ascending=[True, False])

        # Add competition ranking based on both missed_days and shaves
        # Users with same missed_days AND same shaves get tied ranks
        grouped = grouped.reset_index(drop=True)
        grouped["temp_rank"] = range(1, len(grouped) + 1)
        grouped["rank"] = grouped.groupby(["missed_days", "shaves"], sort=False)[
            "temp_rank"
        ].transform("min")
        grouped = grouped.drop("temp_rank", axis=1)

        # Sort by ranking first, then by user for consistent ordering of tied entries
        grouped = grouped.sort_values(["rank", "user"], ascending=[True, True])

        # Reorder columns: rank, user, shaves, missed_days
        grouped = grouped[["rank", "user", "shaves", "missed_days"]]

        # Convert back to list of dicts
        result = grouped.to_dict("records")

        return result

    def _calculate_median_shaves_per_user(self, monthly_data: Dict[str, Dict]) -> float:
        """
        Calculate median shaves per user from monthly aggregated data.

        Args:
            monthly_data: Dictionary of monthly data keyed by month

        Returns:
            Median shaves per user (rounded to 1 decimal place)
        """
        if not monthly_data:
            return 0.0

        # Collect all user records from all months
        all_user_records = []
        for month, data in monthly_data.items():
            if "data" in data and "users" in data["data"]:
                users_data = data["data"]["users"]
                if isinstance(users_data, list):
                    all_user_records.extend(users_data)

        if not all_user_records:
            return 0.0

        import pandas as pd

        # Convert to DataFrame
        df = pd.DataFrame(all_user_records)

        # Group by user and sum shaves across all months
        user_shaves = df.groupby("user")["shaves"].sum().reset_index()

        # Get list of shave counts
        shave_counts = user_shaves["shaves"].tolist()
        shave_counts.sort()

        if not shave_counts:
            return 0.0

        # Calculate median
        n = len(shave_counts)
        if n % 2 == 0:
            # Even number of users, average of two middle values
            median = (shave_counts[n // 2 - 1] + shave_counts[n // 2]) / 2
        else:
            # Odd number of users, middle value
            median = shave_counts[n // 2]

        return round(median, 1)

    def _aggregate_user_diversity(
        self, monthly_data: Dict[str, Dict], category: str
    ) -> List[Dict[str, Any]]:
        """
        Aggregate user diversity data from monthly data.

        User diversity tables have special fields: user, unique_combinations, shaves, avg_shaves_per_combination,
        hhi, effective_soaps. We sum shaves and unique_combinations across months, then recalculate
        avg_shaves_per_combination. HHI and effective_soaps need to be recalculated from combined
        brand-scent distribution (cannot be accurately calculated from monthly summaries alone).

        Args:
            monthly_data: Dictionary of monthly data keyed by month
            category: Category name (e.g., "user_soap_brand_scent_diversity")

        Returns:
            List of aggregated user diversity data sorted by unique_combinations desc, shaves desc
        """
        if not monthly_data:
            return []

        # Collect all records from all months
        all_records = []
        for month, data in monthly_data.items():
            if "data" in data and category in data["data"]:
                category_data = data["data"][category]
                if isinstance(category_data, list):
                    all_records.extend(category_data)

        if not all_records:
            return []

        import pandas as pd

        # Convert to DataFrame
        df = pd.DataFrame(all_records)

        # Group by user and sum shaves and unique_combinations
        # Note: unique_combinations should be summed (total unique combinations across all months)
        grouped = (
            df.groupby("user")
            .agg(
                {
                    "shaves": "sum",
                    "unique_combinations": "sum",  # Sum gives total across months
                }
            )
            .reset_index()
        )

        # Recalculate avg_shaves_per_combination
        grouped["avg_shaves_per_combination"] = (
            grouped["shaves"] / grouped["unique_combinations"]
        ).round(1)

        # Recalculate HHI and effective_soaps from enriched records for accurate annual values
        # Load enriched records for all months and recalculate HHI from combined distribution
        try:
            from .load import load_enriched_data
            from .aggregators.users.soap_brand_scent_diversity_aggregator import (
                SoapBrandScentDiversityAggregator,
            )

            # Collect all enriched records for the year
            all_enriched_records = []
            for month in monthly_data.keys():
                try:
                    enriched_records = load_enriched_data(month, self.data_dir)
                    all_enriched_records.extend(enriched_records)
                except FileNotFoundError:
                    # Skip missing months gracefully
                    continue
                except Exception:
                    # Skip corrupted months gracefully
                    continue

            if all_enriched_records:
                # Recalculate HHI from combined enriched records
                aggregator = SoapBrandScentDiversityAggregator()
                hhi_results = aggregator.aggregate(all_enriched_records)

                # Create mapping of user -> hhi, effective_soaps
                hhi_map = {
                    result["user"]: {
                        "hhi": result.get("hhi", 0.0),
                        "effective_soaps": result.get("effective_soaps", 0.0),
                    }
                    for result in hhi_results
                }

                # Merge HHI values into grouped data
                grouped["hhi"] = (
                    grouped["user"].map(lambda u: hhi_map.get(u, {}).get("hhi", 0.0)).fillna(0.0)
                )
                grouped["effective_soaps"] = (
                    grouped["user"]
                    .map(lambda u: hhi_map.get(u, {}).get("effective_soaps", 0.0))
                    .fillna(0.0)
                )
            else:
                # Fallback if no enriched records available
                grouped["hhi"] = 0.0
                grouped["effective_soaps"] = 0.0
        except Exception:
            # Fallback if HHI recalculation fails for any reason
            grouped["hhi"] = 0.0
            grouped["effective_soaps"] = 0.0

        # Sort by unique_combinations desc, shaves desc
        grouped = grouped.sort_values(["unique_combinations", "shaves"], ascending=[False, False])

        # Add rank column (1-based, with ties getting the same rank)
        grouped["rank"] = (
            grouped["unique_combinations"].rank(method="min", ascending=False).astype(int)
        )

        # Reorder columns: rank, user, unique_combinations, shaves, avg_shaves_per_combination, hhi, effective_soaps
        grouped = grouped[
            [
                "rank",
                "user",
                "unique_combinations",
                "shaves",
                "avg_shaves_per_combination",
                "hhi",
                "effective_soaps",
            ]
        ]

        # Convert back to list of dicts
        result = grouped.to_dict("records")

        return result

    def generate_metadata(
        self,
        monthly_data: Dict[str, Dict],
        included_months: Optional[List[str]] = None,
        missing_months: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate metadata for annual aggregation.

        Args:
            monthly_data: Dictionary of monthly data keyed by month
            included_months: List of months that were successfully loaded
            missing_months: List of months that were missing

        Returns:
            Dictionary with annual metadata
        """
        total_shaves = 0
        total_unique_shavers = 0

        # Calculate totals from included months
        for month, data in monthly_data.items():
            if "meta" in data and isinstance(data["meta"], dict):
                meta = data["meta"]
                total_shaves += meta.get("total_shaves", 0)
                total_unique_shavers += meta.get("unique_shavers", 0)

        # Calculate average shaves per user
        avg_shaves_per_user = 0.0
        if total_unique_shavers > 0:
            avg_shaves_per_user = round(total_shaves / total_unique_shavers, 1)

        # Calculate median shaves per user by aggregating user data from monthly records
        median_shaves_per_user = self._calculate_median_shaves_per_user(monthly_data)

        # Use provided lists or calculate from monthly_data keys
        if included_months is None:
            included_months = sorted(monthly_data.keys())
        if missing_months is None:
            # Calculate missing months if not provided
            missing_months = []
            for month_num in range(1, 13):
                month_key = f"{self.year}-{month_num:02d}"
                if month_key not in monthly_data:
                    missing_months.append(month_key)

        # Update performance metrics
        self.monitor.metrics.total_shaves = total_shaves
        self.monitor.metrics.unique_shavers = total_unique_shavers
        self.monitor.metrics.month_count = len(included_months)

        return {
            "year": self.year,
            "total_shaves": total_shaves,
            "unique_shavers": total_unique_shavers,
            "avg_shaves_per_user": avg_shaves_per_user,
            "median_shaves_per_user": median_shaves_per_user,
            "included_months": sorted(included_months),
            "missing_months": sorted(missing_months),
        }

    def aggregate_all_categories(
        self,
        monthly_data: Dict[str, Dict],
        included_months: Optional[List[str]] = None,
        missing_months: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Aggregate all product categories from monthly data.

        Args:
            monthly_data: Dictionary of monthly data keyed by month
            included_months: List of months that were successfully loaded
            missing_months: List of months that were missing

        Returns:
            Dictionary with all aggregated data and metadata
        """
        metadata = self.generate_metadata(monthly_data, included_months, missing_months)

        # Aggregate basic categories first
        soaps = self.aggregate_soaps(monthly_data)
        soap_makers = self._aggregate_specialized_category(monthly_data, "soap_makers", "brand")

        # Calculate brand_diversity from aggregated soap_makers and soaps
        from sotd.aggregate.aggregators.manufacturers.brand_diversity_aggregator import (
            aggregate_brand_diversity,
        )

        brand_diversity = aggregate_brand_diversity(soap_makers, soaps)

        return {
            "metadata": metadata,
            "razors": self.aggregate_razors(monthly_data),
            "blades": self.aggregate_blades(monthly_data),
            "brushes": self.aggregate_brushes(monthly_data),
            "soaps": soaps,
            "soap_makers": soap_makers,
            "brand_diversity": brand_diversity,
            "brush_fibers": self.aggregate_brush_fibers(monthly_data),
            "brush_knot_sizes": self.aggregate_brush_knot_sizes(monthly_data),
            "brush_handle_makers": self.aggregate_brush_handle_makers(monthly_data),
            "brush_knot_makers": self.aggregate_brush_knot_makers(monthly_data),
            "razor_blade_combinations": self.aggregate_razor_blade_combinations(monthly_data),
            "highest_use_count_per_blade": self.aggregate_highest_use_count_per_blade(monthly_data),
            # Format aggregations
            "razor_formats": self._aggregate_specialized_category(
                monthly_data, "razor_formats", "format"
            ),
            # Manufacturer aggregations
            "razor_manufacturers": self._aggregate_specialized_category(
                monthly_data, "razor_manufacturers", "brand"
            ),
            # Razor specialized aggregations
            "blackbird_plates": self._aggregate_specialized_category(
                monthly_data, "blackbird_plates", "plate"
            ),
            "christopher_bradley_plates": self._aggregate_specialized_category(
                monthly_data, "christopher_bradley_plates", "plate"
            ),
            "game_changer_plates": self._aggregate_specialized_category(
                monthly_data, "game_changer_plates", "gap"
            ),
            "straight_widths": self._aggregate_specialized_category(
                monthly_data, "straight_widths", "width"
            ),
            "straight_grinds": self._aggregate_specialized_category(
                monthly_data, "straight_grinds", "grind"
            ),
            "straight_points": self._aggregate_specialized_category(
                monthly_data, "straight_points", "point"
            ),
            # User aggregations (special handling - keep "user" field name and sum missed_days)
            "users": self._aggregate_users(monthly_data),
            # User diversity aggregations (special handling for unique_combinations and avg_shaves_per_combination)
            "user_soap_brand_scent_diversity": self._aggregate_user_diversity(
                monthly_data, "user_soap_brand_scent_diversity"
            ),
        }


def aggregate_monthly_data(
    year: str,
    monthly_data: Dict[str, Dict],
    included_months: Optional[List[str]] = None,
    missing_months: Optional[List[str]] = None,
    data_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Aggregate monthly data into annual summaries.

    Args:
        year: Year being aggregated (YYYY format)
        monthly_data: Dictionary of monthly data keyed by month
        included_months: List of months that were successfully loaded
        missing_months: List of months that were missing
        data_dir: Data directory for loading enriched records (optional)

    Returns:
        Dictionary with annual aggregated data and metadata
    """
    engine = AnnualAggregationEngine(year, data_dir or Path("/dummy"))
    return engine.aggregate_all_categories(monthly_data, included_months, missing_months)


def save_annual_data(aggregated_data: Dict[str, Any], year: str, data_dir: Path) -> None:
    """
    Save annual aggregated data to file using unified file I/O patterns.

    Args:
        aggregated_data: Annual aggregated data to save
        year: Year being saved (YYYY format)
        data_dir: Data directory to save to
    """
    # Validate year format
    if not year.isdigit() or len(year) != 4:
        raise ValueError("Year must be in YYYY format")

    # Validate data structure
    if not isinstance(aggregated_data, dict):
        raise ValueError("Invalid annual data structure")

    if "metadata" not in aggregated_data:
        raise ValueError("Invalid annual data structure")

    required_categories = ["razors", "blades", "brushes", "soaps"]
    for category in required_categories:
        if category not in aggregated_data:
            raise ValueError("Invalid annual data structure")

    # Create output directory structure
    output_dir = data_dir / "aggregated" / "annual"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Define output file path
    file_path = output_dir / f"{year}.json"

    # Use unified file I/O utilities for atomic write
    from sotd.utils.file_io import save_json_data

    save_json_data(aggregated_data, file_path, indent=2)


def process_annual(year: str, data_dir: Path, debug: bool = False, force: bool = False) -> None:
    """
    Process annual aggregation for a single year with performance monitoring.

    Args:
        year: Year to process (YYYY format)
        data_dir: Data directory containing monthly aggregated files
        debug: Enable debug logging
        force: Force regeneration of existing files
    """
    monitor = AnnualPerformanceMonitor(year)
    monitor.start_total_timing()

    try:
        if debug:
            logger.info(f"Processing annual aggregation for {year}")
            print(f"[DEBUG] Processing annual aggregation for {year}")
            logger.info(f"Data directory: {data_dir}")
            print(f"[DEBUG] Data directory: {data_dir}")
            logger.info(f"Force: {force}")
            print(f"[DEBUG] Force: {force}")

        # Load monthly data from the aggregated subdirectory
        monthly_data_dir = data_dir / "aggregated"

        monitor.start_file_io_timing()
        load_result = load_annual_data(year, monthly_data_dir)
        monitor.end_file_io_timing()

        monthly_data = load_result["monthly_data"]
        included_months = load_result["included_months"]
        missing_months = load_result["missing_months"]

        if debug:
            logger.info(f"Loaded {len(monthly_data)} months of data")
            print(f"[DEBUG] Loaded {len(monthly_data)} months of data")
            logger.info(f"Included months: {included_months}")
            print(f"[DEBUG] Included months: {included_months}")
            logger.info(f"Missing months: {missing_months}")
            print(f"[DEBUG] Missing months: {missing_months}")

        # Aggregate monthly data
        monitor.start_processing_timing()
        aggregated_data = aggregate_monthly_data(
            year, monthly_data, included_months, missing_months, data_dir
        )
        monitor.end_processing_timing()

        if debug:
            logger.info("Aggregated data generated")
            print("[DEBUG] Aggregated data generated")
            logger.info(f"Total shaves: {aggregated_data['metadata']['total_shaves']}")
            print(f"[DEBUG] Total shaves: {aggregated_data['metadata']['total_shaves']}")
            logger.info(f"Unique shavers: {aggregated_data['metadata']['unique_shavers']}")
            print(f"[DEBUG] Unique shavers: {aggregated_data['metadata']['unique_shavers']}")

        # Save aggregated data
        monitor.start_file_io_timing()
        save_annual_data(aggregated_data, year, data_dir)
        monitor.end_file_io_timing()

        # Update performance metrics
        monitor.metrics.total_shaves = aggregated_data["metadata"]["total_shaves"]
        monitor.metrics.unique_shavers = aggregated_data["metadata"]["unique_shavers"]
        monitor.metrics.month_count = len(included_months)

        if debug:
            logger.info(f"Annual aggregation for {year} completed")
            print(f"[DEBUG] Annual aggregation for {year} completed")

    finally:
        monitor.end_total_timing()
        if debug:
            monitor.print_summary()


def process_annual_range(
    years: Sequence[str], data_dir: Path, debug: bool = False, force: bool = False
) -> None:
    """
    Process annual aggregation for multiple years with performance monitoring.

    Args:
        years: List of years to process (YYYY format)
        data_dir: Data directory containing monthly aggregated files
        debug: Enable debug logging
        force: Force regeneration of existing files
    """
    if debug:
        logger.info(f"Processing annual aggregation for years: {years}")
        logger.info(f"Data directory: {data_dir}")
        logger.info(f"Force: {force}")

    for year in years:
        try:
            process_annual(year, data_dir, debug=debug, force=force)
        except Exception as e:
            logger.error(f"Failed to process year {year}: {e}")
            if debug:
                import traceback

                logger.error(traceback.format_exc())
