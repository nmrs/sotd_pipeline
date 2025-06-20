"""Integration tests for report generation."""

from sotd.report.process import generate_report_content


class TestReportIntegration:
    """Integration tests for report generation."""

    def test_hardware_report_generation(self, template_file):
        """Test complete hardware report generation with sample data."""
        # Sample aggregated data
        metadata = {
            "month": "2025-01",
            "total_shaves": 1000,
            "unique_shavers": 50,
        }

        data = {
            "razors": [
                {"name": "Gillette Super Speed", "shaves": 25, "unique_users": 12},
                {"name": "Karve CB", "shaves": 18, "unique_users": 8},
            ],
            "blades": [
                {"name": "Gillette Nacet", "shaves": 30, "unique_users": 15},
                {"name": "Personna Lab Blue", "shaves": 20, "unique_users": 10},
            ],
            "brushes": [
                {"name": "Simpson Chubby 2", "shaves": 15, "unique_users": 8},
                {"name": "Declaration B15", "shaves": 12, "unique_users": 6},
            ],
            "users": [
                {"user": "user1", "shaves": 31, "missed_days": 0, "position": 1},
                {"user": "user2", "shaves": 28, "missed_days": 3, "position": 2},
            ],
        }

        # Generate report content with custom template
        report_content = generate_report_content(
            "hardware", metadata, data, template_path=str(template_file), debug=False
        )

        # Verify report structure
        assert "# Hardware Report - January 2025" in report_content
        assert "**Total Shaves:** 1,000" in report_content
        assert "**Unique Shavers:** 50" in report_content
        assert "## Notes & Caveats" in report_content
        assert "Custom template content for testing" in report_content
        assert "### Razor Statistics" in report_content
        assert "### Blade Statistics" in report_content
        assert "### Brush Statistics" in report_content
        assert "### User Statistics" in report_content

        # Verify that tables are generated (should contain actual table content)
        assert "| Razor" in report_content  # Table headers
        assert "Gillette Super Speed" in report_content
        assert "Gillette Nacet" in report_content
        assert "Simpson Chubby 2" in report_content
        assert "user1" in report_content

    def test_software_report_generation(self, template_file):
        """Test complete software report generation with sample data."""
        # Sample aggregated data
        metadata = {
            "month": "2025-01",
            "total_shaves": 500,
            "unique_shavers": 25,
        }

        data = {
            "soaps": [
                {"name": "Declaration Grooming", "shaves": 20, "unique_users": 10},
                {"name": "Stirling Soap Co", "shaves": 15, "unique_users": 8},
            ],
            "users": [
                {"user": "user1", "shaves": 31, "missed_days": 0, "position": 1},
                {"user": "user2", "shaves": 28, "missed_days": 3, "position": 2},
            ],
        }

        # Generate report content with custom template
        report_content = generate_report_content(
            "software", metadata, data, template_path=str(template_file), debug=False
        )

        # Verify report structure
        assert "# Software Report - January 2025" in report_content
        assert "**Total Shaves:** 500" in report_content
        assert "**Unique Shavers:** 25" in report_content
        assert "## Notes & Caveats" in report_content
        assert "Custom software template content" in report_content
        assert "### Soap Statistics" in report_content
        assert "### User Statistics" in report_content

        # Verify that tables are generated
        assert "| Soap" in report_content
        assert "Declaration Grooming" in report_content
        assert "Stirling Soap Co" in report_content
        assert "user1" in report_content

    def test_report_with_empty_data(self, template_file):
        """Test report generation with empty data."""
        metadata = {
            "month": "2025-01",
            "total_shaves": 0,
            "unique_shavers": 0,
        }

        data = {}

        # Should not raise exceptions
        report_content = generate_report_content(
            "hardware", metadata, data, template_path=str(template_file), debug=False
        )

        # Should still have basic structure
        assert "# Hardware Report - January 2025" in report_content
        assert "**Total Shaves:** 0" in report_content
        assert "**Unique Shavers:** 0" in report_content

        # Should handle empty data gracefully
        assert "*No data available" in report_content

    def test_report_with_delta_calculations(self, template_file):
        """Test report generation with historical data for delta calculations."""
        metadata = {
            "month": "2025-01",
            "total_shaves": 1000,
            "unique_shavers": 50,
        }

        data = {
            "razors": [
                {"name": "Gillette Super Speed", "shaves": 25, "unique_users": 12, "position": 1},
                {"name": "Karve CB", "shaves": 18, "unique_users": 8, "position": 2},
            ],
        }

        comparison_data = {
            "previous month": (
                {"month": "2024-12"},  # metadata
                {  # data
                    "razors": [
                        {"name": "Karve CB", "shaves": 20, "unique_users": 10, "position": 1},
                        {
                            "name": "Gillette Super Speed",
                            "shaves": 15,
                            "unique_users": 8,
                            "position": 2,
                        },
                    ],
                },
            )
        }

        # Generate report content with deltas
        report_content = generate_report_content(
            "hardware",
            metadata,
            data,
            comparison_data,
            template_path=str(template_file),
            debug=False,
        )

        # Should include delta column
        assert "Δ vs previous month" in report_content
