#!/usr/bin/env python3
"""Tests for the annual report generator."""

import json
from pathlib import Path

import pytest

from sotd.report import annual_generator


class TestAnnualReportGenerator:
    def test_generate_annual_report_valid(self, tmp_path: Path):
        """Test generating a valid annual report from data and template."""
        # Create test annual data
        test_data = {
            "metadata": {
                "year": "2024",
                "total_shaves": 1200,
                "unique_shavers": 100,
                "included_months": 12,
                "missing_months": 0,
            },
            "razors": [
                {"name": "Rockwell 6C", "shaves": 200, "unique_users": 80, "position": 1},
                {"name": "Merkur 34C", "shaves": 150, "unique_users": 60, "position": 2},
            ],
            "blades": [
                {
                    "name": "Astra Superior Platinum",
                    "shaves": 250,
                    "unique_users": 90,
                    "position": 1,
                },
                {"name": "Feather Hi-Stainless", "shaves": 200, "unique_users": 85, "position": 2},
            ],
            "brushes": [
                {"name": "Simpson Chubby 2", "shaves": 100, "unique_users": 40, "position": 1},
                {"name": "Omega 10049", "shaves": 80, "unique_users": 35, "position": 2},
            ],
            "soaps": [
                {
                    "name": "Barrister and Mann Seville",
                    "shaves": 120,
                    "unique_users": 50,
                    "position": 1,
                },
                {
                    "name": "Stirling Executive Man",
                    "shaves": 100,
                    "unique_users": 45,
                    "position": 2,
                },
            ],
        }

        # Create test annual data file
        annual_data_file = tmp_path / "aggregated" / "annual" / "2024.json"
        annual_data_file.parent.mkdir(parents=True)
        with open(annual_data_file, "w") as f:
            json.dump(test_data, f)

        # Generate annual hardware report
        result = annual_generator.generate_annual_report(
            report_type="hardware",
            year="2024",
            data_dir=tmp_path,
            debug=False,
        )

        # Verify the report was generated
        assert result is not None
        assert "Welcome to your Annual SOTD Hardware Report for 2024" in result
        assert "1,200 shave reports from 100 distinct shavers during 2024" in result
        assert "Data includes 12 months of the year" in result
        assert "Rockwell 6C" in result
        assert "Astra Superior Platinum" in result

    def test_generate_annual_report_missing_data(self, tmp_path: Path):
        """Test error handling when annual data is missing."""
        # Do not create the annual data file
        with pytest.raises(FileNotFoundError):
            annual_generator.generate_annual_report(
                report_type="hardware",
                year="2024",
                data_dir=tmp_path,
                debug=False,
            )

    def test_generate_annual_report_invalid_template(self, tmp_path: Path):
        """Test error handling for invalid/malformed template."""
        # Remove/rename the template file so the template is missing
        # Use a custom template path that does not contain annual_hardware
        import yaml

        # Create a template file with only monthly templates
        template_content = {"hardware": {"report_template": "Monthly hardware report"}}
        template_file = tmp_path / "test_templates.yaml"
        with open(template_file, "w") as f:
            yaml.dump(template_content, f)

        # Create valid annual data file
        test_data = {
            "metadata": {
                "year": "2024",
                "total_shaves": 1200,
                "unique_shavers": 100,
                "included_months": 12,
                "missing_months": 0,
            },
            "razors": [],
            "blades": [],
            "brushes": [],
            "soaps": [],
        }
        annual_data_file = tmp_path / "aggregated" / "annual" / "2024.json"
        annual_data_file.parent.mkdir(parents=True)
        with open(annual_data_file, "w") as f:
            json.dump(test_data, f)

        # Should raise KeyError for missing annual_hardware template
        with pytest.raises(KeyError, match="Template 'annual_hardware' not found"):
            annual_generator.generate_annual_report(
                report_type="hardware",
                year="2024",
                data_dir=tmp_path,
                debug=False,
                template_path=str(template_file),
            )

    def test_generate_annual_report_with_extra_fields(self, tmp_path: Path):
        """Test that extra fields in data/template do not break report generation."""
        # Create test annual data with extra fields
        test_data = {
            "metadata": {
                "year": "2024",
                "total_shaves": 1200,
                "unique_shavers": 100,
                "included_months": 12,
                "missing_months": 0,
                "extra_metadata_field": "should be ignored",
            },
            "razors": [
                {"name": "Rockwell 6C", "shaves": 200, "unique_users": 80, "position": 1},
            ],
            "blades": [
                {
                    "name": "Astra Superior Platinum",
                    "shaves": 250,
                    "unique_users": 90,
                    "position": 1,
                },
            ],
            "brushes": [
                {"name": "Simpson Chubby 2", "shaves": 100, "unique_users": 40, "position": 1},
            ],
            "soaps": [
                {
                    "name": "Barrister and Mann Seville",
                    "shaves": 120,
                    "unique_users": 50,
                    "position": 1,
                },
            ],
            "extra_category": [
                {"name": "Extra Product", "shaves": 50, "unique_users": 20, "position": 1},
            ],
        }

        # Create test annual data file
        annual_data_file = tmp_path / "aggregated" / "annual" / "2024.json"
        annual_data_file.parent.mkdir(parents=True)
        with open(annual_data_file, "w") as f:
            json.dump(test_data, f)

        # Create template with extra fields
        import yaml

        template_content = {
            "annual_hardware": {
                "report_template": (
                    "Welcome to your Annual SOTD Hardware Report for {{year}}\n\n"
                    "* {{total_shaves}} shave reports from {{unique_shavers}} "
                    "distinct shavers during {{year}}.\n\n"
                    "## Razors\n\n{{tables.razors}}\n\n"
                    "## Extra Section\n\nThis is an extra section that should be included."
                ),
                "extra_template_field": "should be ignored",
            }
        }
        template_file = tmp_path / "test_templates.yaml"
        with open(template_file, "w") as f:
            yaml.dump(template_content, f)

        # Generate annual hardware report
        result = annual_generator.generate_annual_report(
            report_type="hardware",
            year="2024",
            data_dir=tmp_path,
            debug=False,
            template_path=str(template_file),
        )

        # Verify the report was generated correctly despite extra fields
        assert result is not None
        assert "Welcome to your Annual SOTD Hardware Report for 2024" in result
        assert "1,200 shave reports from 100 distinct shavers during 2024" in result
        assert "Rockwell 6C" in result
        assert "Extra Section" in result  # Extra template content should be included
        # Extra fields should not cause errors or appear in output
        assert "extra_metadata_field" not in result
        assert "extra_category" not in result
        assert "extra_template_field" not in result

    def test_generate_annual_report_performance(self, tmp_path: Path):
        """Test performance with large annual data sets."""
        # Create large dataset with many products
        large_razors = [
            {"name": f"Razor {i}", "shaves": 100 + i, "unique_users": 50 + i, "position": i}
            for i in range(1, 101)
        ]
        large_blades = [
            {"name": f"Blade {i}", "shaves": 200 + i, "unique_users": 100 + i, "position": i}
            for i in range(1, 101)
        ]
        large_brushes = [
            {"name": f"Brush {i}", "shaves": 50 + i, "unique_users": 25 + i, "position": i}
            for i in range(1, 101)
        ]
        large_soaps = [
            {"name": f"Soap {i}", "shaves": 75 + i, "unique_users": 40 + i, "position": i}
            for i in range(1, 101)
        ]

        test_data = {
            "metadata": {
                "year": "2024",
                "total_shaves": 50000,
                "unique_shavers": 1000,
                "included_months": [f"2024-{i:02d}" for i in range(1, 13)],
                "missing_months": [],
            },
            "razors": large_razors,
            "blades": large_blades,
            "brushes": large_brushes,
            "soaps": large_soaps,
        }

        # Create test annual data file
        annual_data_file = tmp_path / "aggregated" / "annual" / "2024.json"
        annual_data_file.parent.mkdir(parents=True)
        with open(annual_data_file, "w") as f:
            json.dump(test_data, f)

        # Generate annual hardware report and measure performance
        import time

        start_time = time.time()

        result = annual_generator.generate_annual_report(
            report_type="hardware",
            year="2024",
            data_dir=tmp_path,
            debug=False,
        )

        end_time = time.time()
        generation_time = end_time - start_time

        # Verify the report was generated correctly
        assert result is not None
        assert "Welcome to your Annual SOTD Hardware Report for 2024" in result
        assert "50,000 shave reports from 1000 distinct shavers during 2024" in result
        assert "Razor 1" in result
        assert "Blade 1" in result
        assert "Brush 1" in result

        # Performance assertion: should complete in under 5 seconds
        assert (
            generation_time < 5.0
        ), f"Report generation took {generation_time:.2f}s, expected under 5s"

    def test_generate_annual_report_integration(self, tmp_path: Path):
        """Test integration with loader and template processor."""
        # Create test annual data with realistic structure
        test_data = {
            "metadata": {
                "year": "2024",
                "total_shaves": 15000,
                "unique_shavers": 500,
                "included_months": [
                    "2024-01",
                    "2024-02",
                    "2024-03",
                    "2024-04",
                    "2024-05",
                    "2024-06",
                ],
                "missing_months": [
                    "2024-07",
                    "2024-08",
                    "2024-09",
                    "2024-10",
                    "2024-11",
                    "2024-12",
                ],
            },
            "razors": [
                {"name": "Rockwell 6C", "shaves": 1200, "unique_users": 300, "position": 1},
                {"name": "Merkur 34C", "shaves": 800, "unique_users": 250, "position": 2},
                {"name": "Gillette Super Speed", "shaves": 600, "unique_users": 200, "position": 3},
            ],
            "blades": [
                {
                    "name": "Astra Superior Platinum",
                    "shaves": 2000,
                    "unique_users": 400,
                    "position": 1,
                },
                {
                    "name": "Feather Hi-Stainless",
                    "shaves": 1500,
                    "unique_users": 350,
                    "position": 2,
                },
                {
                    "name": "Gillette Silver Blue",
                    "shaves": 1000,
                    "unique_users": 300,
                    "position": 3,
                },
            ],
            "brushes": [
                {"name": "Simpson Chubby 2", "shaves": 500, "unique_users": 150, "position": 1},
                {"name": "Omega 10049", "shaves": 400, "unique_users": 120, "position": 2},
                {"name": "Yaqi Sagrada Familia", "shaves": 300, "unique_users": 100, "position": 3},
            ],
            "soaps": [
                {
                    "name": "Barrister and Mann Seville",
                    "shaves": 800,
                    "unique_users": 200,
                    "position": 1,
                },
                {
                    "name": "Stirling Executive Man",
                    "shaves": 600,
                    "unique_users": 180,
                    "position": 2,
                },
                {
                    "name": "Declaration Grooming Original",
                    "shaves": 400,
                    "unique_users": 120,
                    "position": 3,
                },
            ],
        }

        # Create test annual data file
        annual_data_file = tmp_path / "aggregated" / "annual" / "2024.json"
        annual_data_file.parent.mkdir(parents=True)
        with open(annual_data_file, "w") as f:
            json.dump(test_data, f)

        # Create custom template to test template processor integration
        import yaml

        template_content = {
            "annual_hardware": {
                "report_template": (
                    "# Annual SOTD Hardware Report for {{year}}\n\n"
                    "## Overview\n\n"
                    "* {{total_shaves}} shave reports from {{unique_shavers}} "
                    "distinct shavers during {{year}}.\n"
                    "* Data includes {{included_months}} months of the year.\n"
                    "* Missing data for {{missing_months}} months.\n\n"
                    "## Top Razors\n\n"
                    "{{tables.razors}}\n\n"
                    "## Top Blades\n\n"
                    "{{tables.blades}}\n\n"
                    "## Top Brushes\n\n"
                    "{{tables.brushes}}\n\n"
                    "## Summary\n\n"
                    "This report covers {{included_months}} months of {{year}} "
                    "with {{total_shaves}} total shaves."
                )
            }
        }
        template_file = tmp_path / "test_templates.yaml"
        with open(template_file, "w") as f:
            yaml.dump(template_content, f)

        # Generate annual hardware report with integration testing
        result = annual_generator.generate_annual_report(
            report_type="hardware",
            year="2024",
            data_dir=tmp_path,
            debug=True,  # Enable debug to test logging integration
            template_path=str(template_file),
        )

        # Verify complete integration workflow
        assert result is not None
        assert "# Annual SOTD Hardware Report for 2024" in result
        assert "15,000 shave reports from 500 distinct shavers during 2024" in result
        assert "Data includes 6 months of the year" in result
        assert "Missing data for 6 months" in result

        # Verify table generation integration
        assert "## Top Razors" in result
        assert "Rockwell 6C" in result
        assert "Merkur 34C" in result
        assert "Gillette Super Speed" in result

        assert "## Top Blades" in result
        assert "Astra Superior Platinum" in result
        assert "Feather Hi-Stainless" in result
        assert "Gillette Silver Blue" in result

        assert "## Top Brushes" in result
        assert "Simpson Chubby 2" in result
        assert "Omega 10049" in result
        assert "Yaqi Sagrada Familia" in result

        # Verify summary section
        assert "This report covers 6 months of 2024 with 15,000 total shaves" in result

        # Verify data loading integration (metadata values)
        assert "500" in result  # unique_shavers
        assert "6" in result  # included_months count
        assert "6" in result  # missing_months count

        # Verify template processor integration (variable substitution)
        assert "{{year}}" not in result  # Template variables should be substituted
        assert "{{total_shaves}}" not in result
        assert "{{unique_shavers}}" not in result
