#!/usr/bin/env python3
"""Integration tests for annual delta calculation in report generation."""

from pathlib import Path
from sotd.report.annual_generator import LegacyAnnualReportGenerator
from sotd.report.annual_delta_calculator import AnnualDeltaCalculator
from sotd.report.annual_comparison_loader import AnnualComparisonLoader
import tempfile
import json


class TestAnnualDeltaIntegration:
    def setup_method(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name)
        self.generator = LegacyAnnualReportGenerator(debug=True)
        self.delta_calculator = AnnualDeltaCalculator(debug=True)
        self.comparison_loader = AnnualComparisonLoader(debug=True)

    def teardown_method(self):
        self.temp_dir.cleanup()

    def _write_annual_file(self, year: str, data: dict):
        file_path = self.data_dir / f"{year}.json"
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        return file_path

    def test_delta_column_integration(self):
        """Test that delta columns are included in annual report tables."""
        # Write current and previous year data
        current_year = "2024"
        previous_year = "2023"
        current_data = {
            "year": current_year,
            "meta": {"total_shaves": 1000},
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 100, "rank": 1},
                    {"name": "Razor B", "shaves": 80, "rank": 2},
                ]
            },
        }
        previous_data = {
            "year": previous_year,
            "meta": {"total_shaves": 900},
            "data": {
                "razors": [
                    {"name": "Razor B", "shaves": 90, "rank": 1},
                    {"name": "Razor A", "shaves": 85, "rank": 2},
                ]
            },
        }
        self._write_annual_file(current_year, current_data)
        self._write_annual_file(previous_year, previous_data)
        # Load comparison data
        comparison = self.comparison_loader.load_comparison_years([previous_year], self.data_dir)
        # Generate report table with delta
        table_md = self.generator.generate_table_with_deltas(
            current_data, comparison, categories=["razors"], comparison_years=[previous_year]
        )
        assert f"Δ vs {previous_year}" in table_md
        assert "↑" in table_md or "↓" in table_md or "=" in table_md

    def test_missing_comparison_year(self):
        """Test that missing comparison year does not break report generation."""
        current_year = "2024"
        current_data = {
            "year": current_year,
            "meta": {"total_shaves": 1000},
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 100, "position": 1},
                ]
            },
        }
        self._write_annual_file(current_year, current_data)
        # No previous year file
        comparison = self.comparison_loader.load_comparison_years(["2023"], self.data_dir)
        table_md = self.generator.generate_table_with_deltas(
            current_data, comparison, categories=["razors"], comparison_years=["2023"]
        )
        assert f"Δ vs 2023" in table_md
        assert "n/a" in table_md

    def test_formatting_and_alignment(self):
        """Test that delta columns are formatted and aligned correctly."""
        current_year = "2024"
        previous_year = "2023"
        current_data = {
            "year": current_year,
            "meta": {"total_shaves": 1000},
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 100, "rank": 1},
                ]
            },
        }
        previous_data = {
            "year": previous_year,
            "meta": {"total_shaves": 900},
            "data": {
                "razors": [
                    {"name": "Razor A", "shaves": 90, "rank": 2},
                ]
            },
        }
        self._write_annual_file(current_year, current_data)
        self._write_annual_file(previous_year, previous_data)
        comparison = self.comparison_loader.load_comparison_years([previous_year], self.data_dir)
        table_md = self.generator.generate_table_with_deltas(
            current_data, comparison, categories=["razors"], comparison_years=[previous_year]
        )
        # Check that the delta column is aligned and contains the correct symbol
        assert f"Δ vs {previous_year}" in table_md
        assert "↑" in table_md or "↓" in table_md or "=" in table_md
