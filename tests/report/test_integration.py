"""Integration tests for end-to-end report generation."""

from sotd.report.process import generate_report_content


class TestReportIntegration:
    """Integration tests for complete report generation."""

    def test_hardware_report_generation(self):
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

        # Generate report content
        report_content = generate_report_content("hardware", metadata, data, debug=False)

        # Verify report structure
        assert "# Hardware Report - January 2025" in report_content
        assert "**Total Shaves:** 1,000" in report_content
        assert "**Unique Shavers:** 50" in report_content
        assert "## Observations" in report_content
        assert "## Notes & Caveats" in report_content
        assert "## Tables" in report_content

        # Verify tables are included
        assert "### Razors" in report_content
        assert "### Blades" in report_content
        assert "### Brushes" in report_content
        assert "### Top Shavers" in report_content

    def test_software_report_generation(self):
        """Test complete software report generation with sample data."""
        # Sample aggregated data
        metadata = {
            "month": "2025-01",
            "total_shaves": 1000,
            "unique_shavers": 50,
        }

        data = {
            "soaps": [
                {"name": "Declaration Grooming Sellout", "shaves": 35, "unique_users": 18},
                {"name": "Stirling Executive Man", "shaves": 25, "unique_users": 12},
            ],
            "soap_makers": [
                {"brand": "Declaration Grooming", "shaves": 70, "unique_users": 35},
                {"brand": "Stirling", "shaves": 55, "unique_users": 28},
            ],
            "users": [
                {"user": "user1", "shaves": 31, "missed_days": 0, "position": 1},
                {"user": "user2", "shaves": 28, "missed_days": 3, "position": 2},
            ],
        }

        # Generate report content
        report_content = generate_report_content("software", metadata, data, debug=False)

        # Verify report structure
        assert "# Software Report - January 2025" in report_content
        assert "**Total Shaves:** 1,000" in report_content
        assert "**Unique Shavers:** 50" in report_content
        assert "## Observations" in report_content
        assert "## Notes & Caveats" in report_content
        assert "## Tables" in report_content

        # Verify tables are included
        assert "### Soap Makers" in report_content
        assert "### Soaps" in report_content
        assert "### Brand Diversity" in report_content
        assert "### Top Shavers" in report_content

    def test_report_with_empty_data(self):
        """Test report generation with empty data."""
        metadata = {
            "month": "2025-01",
            "total_shaves": 0,
            "unique_shavers": 0,
        }

        data = {}

        # Should not raise exceptions
        report_content = generate_report_content("hardware", metadata, data, debug=False)

        # Should still have basic structure
        assert "# Hardware Report - January 2025" in report_content
        assert "**Total Shaves:** 0" in report_content
        assert "**Unique Shavers:** 0" in report_content

    def test_report_with_delta_calculations(self):
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
            "hardware", metadata, data, comparison_data, debug=False
        )

        # Should include delta column
        assert "vs Previous Month" in report_content
