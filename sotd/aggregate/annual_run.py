"""
Annual aggregation integration module.

This module wires together the annual aggregation components to provide
a complete end-to-end workflow for annual data processing.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from ..utils.performance_base import BasePerformanceMetrics, BasePerformanceMonitor
from .annual_engine import process_annual, process_annual_range

logger = logging.getLogger(__name__)


@dataclass
class AnnualRunMetrics(BasePerformanceMetrics):
    """Performance metrics for annual run integration."""

    # Annual run specific fields
    year: str = field(default="")
    years_processed: int = field(default=0)
    years_failed: int = field(default=0)
    validation_passed: bool = field(default=False)
    validation_errors: int = field(default=0)

    def to_dict(self) -> Dict:
        """Convert metrics to dictionary for JSON serialization."""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "year": self.year,
                "years_processed": self.years_processed,
                "years_failed": self.years_failed,
                "validation_passed": self.validation_passed,
                "validation_errors": self.validation_errors,
            }
        )
        return base_dict


class AnnualRunPerformanceMonitor(BasePerformanceMonitor):
    """Performance monitor for annual run integration."""

    def __init__(self, year: str, parallel_workers: int = 1):
        self.year = year
        super().__init__("annual_run", parallel_workers)
        # Type annotation to help type checker
        self.metrics: AnnualRunMetrics = self.metrics

    def _create_metrics(self, phase_name: str, parallel_workers: int) -> AnnualRunMetrics:
        """Create annual run performance metrics."""
        metrics = AnnualRunMetrics()
        metrics.year = self.year
        metrics.phase_name = phase_name
        metrics.parallel_workers = parallel_workers
        return metrics

    def print_summary(self) -> None:
        """Print a human-readable performance summary."""
        metrics = self.metrics
        logger.info(f"\n=== Annual Run Performance Summary ({metrics.year}) ===")
        logger.info(f"Total Processing Time: {metrics.total_processing_time:.2f}s")
        logger.info(f"Years Processed: {metrics.years_processed}")
        logger.info(f"Years Failed: {metrics.years_failed}")
        logger.info(f"Validation Passed: {metrics.validation_passed}")
        logger.info(f"Validation Errors: {metrics.validation_errors}")
        logger.info(f"Peak Memory Usage: {metrics.peak_memory_mb:.1f}MB")


def run_annual_aggregation(
    year: str, data_dir: Path, debug: bool = False, force: bool = False, verbose: bool = False
) -> bool:
    """
    Run complete annual aggregation workflow with performance monitoring.

    Args:
        year: Year to process (YYYY format)
        data_dir: Data directory containing monthly aggregated files
        debug: Enable debug logging
        force: Force regeneration of existing files
        verbose: Enable verbose output

    Returns:
        True if successful, False otherwise
    """
    monitor = AnnualRunPerformanceMonitor(year)
    monitor.start_total_timing()

    try:
        if verbose:
            logger.info(f"Starting annual aggregation for year {year}")
            logger.info(f"Data directory: {data_dir}")
            logger.info(f"Force mode: {force}")
            logger.info(f"Debug mode: {debug}")

        # Process annual aggregation
        monitor.start_processing_timing()
        process_annual(year, data_dir, debug=debug, force=force)
        monitor.end_processing_timing()

        # Update metrics
        monitor.metrics.years_processed = 1

        if verbose:
            logger.info(f"Annual aggregation for year {year} completed successfully")

        return True

    except Exception as e:
        logger.error(f"Annual aggregation failed for year {year}: {e}")
        monitor.metrics.years_failed = 1
        if debug:
            import traceback

            logger.error(traceback.format_exc())
        return False

    finally:
        monitor.end_total_timing()
        if debug:
            monitor.print_summary()


def run_annual_range_aggregation(
    start_year: str,
    end_year: str,
    data_dir: Path,
    debug: bool = False,
    force: bool = False,
    verbose: bool = False,
) -> bool:
    """
    Run annual aggregation for a range of years with performance monitoring.

    Args:
        start_year: Start year (YYYY format)
        end_year: End year (YYYY format)
        data_dir: Data directory containing monthly aggregated files
        debug: Enable debug logging
        force: Force regeneration of existing files
        verbose: Enable verbose output

    Returns:
        True if all years successful, False if any failed
    """
    # Use the first year for monitoring
    monitor = AnnualRunPerformanceMonitor(start_year)
    monitor.start_total_timing()

    # Initialize years variable
    years = []

    try:
        if verbose:
            logger.info(f"Starting annual aggregation for range {start_year}-{end_year}")
            logger.info(f"Data directory: {data_dir}")
            logger.info(f"Force mode: {force}")
            logger.info(f"Debug mode: {debug}")

        # Generate list of years
        years = [str(year) for year in range(int(start_year), int(end_year) + 1)]

        # Process annual aggregation for range
        monitor.start_processing_timing()
        process_annual_range(years, data_dir, debug=debug, force=force)
        monitor.end_processing_timing()

        # Update metrics
        monitor.metrics.years_processed = len(years)

        if verbose:
            logger.info(
                f"Annual aggregation for range {start_year}-{end_year} completed successfully"
            )

        return True

    except Exception as e:
        logger.error(f"Annual range aggregation failed for {start_year}-{end_year}: {e}")
        monitor.metrics.years_failed = len(years)
        if debug:
            import traceback

            logger.error(traceback.format_exc())
        return False

    finally:
        monitor.end_total_timing()
        if debug:
            monitor.print_summary()


def validate_annual_data(year: str, data_dir: Path) -> dict:
    """
    Validate annual aggregated data for a year using unified patterns.

    Args:
        year: Year to validate (YYYY format)
        data_dir: Data directory containing annual aggregated files

    Returns:
        Dictionary with validation results
    """
    validation_result = {
        "year": year,
        "valid": False,
        "errors": [],
        "warnings": [],
        "file_exists": False,
        "data_structure_valid": False,
        "metadata_valid": False,
        "product_data_valid": False,
    }

    try:
        # Check if annual file exists
        annual_file = data_dir / "aggregated" / "annual" / f"{year}.json"
        validation_result["file_exists"] = annual_file.exists()

        if not annual_file.exists():
            validation_result["errors"].append(f"Annual file not found: {annual_file}")
            return validation_result

        # Load and validate data structure using unified file I/O
        from sotd.utils.file_io import load_json_data

        annual_data = load_json_data(annual_file)

        # Validate basic structure
        required_keys = ["metadata", "razors", "blades", "brushes", "soaps"]
        missing_keys = [key for key in required_keys if key not in annual_data]

        if missing_keys:
            validation_result["errors"].append(f"Missing required keys: {missing_keys}")
        else:
            validation_result["data_structure_valid"] = True

        # Validate metadata
        metadata = annual_data.get("metadata", {})
        required_metadata_keys = [
            "year",
            "total_shaves",
            "unique_shavers",
            "included_months",
            "missing_months",
        ]
        missing_metadata_keys = [key for key in required_metadata_keys if key not in metadata]

        if missing_metadata_keys:
            validation_result["errors"].append(f"Missing metadata keys: {missing_metadata_keys}")
        else:
            validation_result["metadata_valid"] = True

            # Validate metadata values
            if metadata["year"] != year:
                validation_result["errors"].append(
                    f"Year mismatch: expected {year}, got {metadata['year']}"
                )

            if not isinstance(metadata["total_shaves"], int):
                validation_result["errors"].append("total_shaves must be integer")

            if not isinstance(metadata["unique_shavers"], int):
                validation_result["errors"].append("unique_shavers must be integer")

        # Validate product data
        product_types = ["razors", "blades", "brushes", "soaps"]
        product_errors = []

        for product_type in product_types:
            products = annual_data.get(product_type, [])
            if not isinstance(products, list):
                product_errors.append(f"{product_type} must be a list")
                continue

            for i, product in enumerate(products):
                if not isinstance(product, dict):
                    product_errors.append(f"{product_type}[{i}] must be a dictionary")
                    continue

                required_product_keys = ["name", "shaves", "unique_users"]
                missing_product_keys = [key for key in required_product_keys if key not in product]

                if missing_product_keys:
                    product_errors.append(
                        f"{product_type}[{i}] missing keys: {missing_product_keys}"
                    )

                if "shaves" in product and not isinstance(product["shaves"], int):
                    product_errors.append(f"{product_type}[{i}] shaves must be integer")

                if "unique_users" in product and not isinstance(product["unique_users"], int):
                    product_errors.append(f"{product_type}[{i}] unique_users must be integer")

        if product_errors:
            validation_result["errors"].extend(product_errors)
        else:
            validation_result["product_data_valid"] = True

        # Check for warnings
        if metadata.get("missing_months"):
            validation_result["warnings"].append(f"Missing months: {metadata['missing_months']}")

        if metadata.get("total_shaves", 0) == 0:
            validation_result["warnings"].append("No shaves recorded for this year")

        # Overall validation result
        validation_result["valid"] = len(validation_result["errors"]) == 0

    except Exception as e:
        validation_result["errors"].append(f"Validation failed: {e}")

    return validation_result


def get_annual_summary(year: str, data_dir: Path) -> Optional[dict]:
    """
    Get summary information for annual aggregated data using unified patterns.

    Args:
        year: Year to get summary for (YYYY format)
        data_dir: Data directory containing annual aggregated files

    Returns:
        Dictionary with summary information, or None if not found
    """
    try:
        annual_file = data_dir / "aggregated" / "annual" / f"{year}.json"

        if not annual_file.exists():
            return None

        # Use unified file I/O patterns
        from sotd.utils.file_io import get_file_size_mb, load_json_data

        annual_data = load_json_data(annual_file)

        metadata = annual_data.get("metadata", {})

        summary = {
            "year": year,
            "file_path": str(annual_file),
            "file_size_mb": get_file_size_mb(annual_file),
            "total_shaves": metadata.get("total_shaves", 0),
            "unique_shavers": metadata.get("unique_shavers", 0),
            "included_months": metadata.get("included_months", []),
            "missing_months": metadata.get("missing_months", []),
            "product_counts": {
                "razors": len(annual_data.get("razors", [])),
                "blades": len(annual_data.get("blades", [])),
                "brushes": len(annual_data.get("brushes", [])),
                "soaps": len(annual_data.get("soaps", [])),
            },
        }

        return summary

    except Exception as e:
        logger.error(f"Failed to get annual summary for {year}: {e}")
        return None


def list_available_annual_years(data_dir: Path) -> list:
    """
    List all available annual aggregated years using unified patterns.

    Args:
        data_dir: Data directory containing annual aggregated files

    Returns:
        List of available years (sorted)
    """
    try:
        annual_dir = data_dir / "aggregated" / "annual"

        if not annual_dir.exists():
            return []

        years = []
        for file_path in annual_dir.glob("*.json"):
            year = file_path.stem
            if year.isdigit() and len(year) == 4:
                years.append(year)

        return sorted(years)

    except Exception as e:
        logger.error(f"Failed to list available annual years: {e}")
        return []
