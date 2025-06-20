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
            "avg_shaves_per_user": 20.0,
        }

        data = {
            "razors": [
                {"name": "Gillette Super Speed", "shaves": 25, "unique_users": 12},
                {"name": "Karve CB", "shaves": 18, "unique_users": 8},
            ],
            "razor_manufacturers": [
                {"brand": "Gillette", "shaves": 30, "unique_users": 15},
                {"brand": "Karve", "shaves": 18, "unique_users": 8},
            ],
            "razor_formats": [
                {"format": "DE", "shaves": 45, "unique_users": 20},
                {"format": "SE", "shaves": 5, "unique_users": 3},
            ],
            "blades": [
                {"name": "Gillette Nacet", "shaves": 30, "unique_users": 15},
                {"name": "Personna Lab Blue", "shaves": 20, "unique_users": 10},
            ],
            "blade_manufacturers": [
                {"brand": "Gillette", "shaves": 35, "unique_users": 18},
                {"brand": "Personna", "shaves": 25, "unique_users": 12},
            ],
            "brushes": [
                {"name": "Simpson Chubby 2", "shaves": 15, "unique_users": 8},
                {"name": "AP Shave Co", "shaves": 12, "unique_users": 6},
            ],
            "brush_handle_makers": [
                {"handle_maker": "Simpson", "shaves": 15, "unique_users": 8},
                {"handle_maker": "AP Shave Co", "shaves": 12, "unique_users": 6},
            ],
            "brush_knot_makers": [
                {"brand": "Simpson", "shaves": 15, "unique_users": 8},
                {"brand": "AP Shave Co", "shaves": 12, "unique_users": 6},
            ],
            "brush_fibers": [
                {"fiber": "Badger", "shaves": 20, "unique_users": 10},
                {"fiber": "Synthetic", "shaves": 10, "unique_users": 5},
            ],
            "brush_knot_sizes": [
                {"knot_size": "24mm", "shaves": 15, "unique_users": 8},
                {"knot_size": "26mm", "shaves": 12, "unique_users": 6},
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
        assert "Welcome to your SOTD Hardware Report for January 2025" in report_content
        assert "Average shaves per user: 20.0" in report_content
        assert "## Notes & Caveats" in report_content
        assert "Custom template content for testing" in report_content
        assert "## Razors" in report_content
        assert "## Blades" in report_content
        assert "## Blade Manufacturers" in report_content
        assert "## Brushes" in report_content
        assert "## Top Shavers" in report_content

        # Verify that tables are generated (should contain actual table content)
        assert "| name" in report_content  # Table headers
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
            "unique_soaps": 100,
            "unique_brands": 20,
        }

        data = {
            "soaps": [
                {"name": "Declaration Grooming", "shaves": 20, "unique_users": 10},
                {"name": "Stirling Soap Co", "shaves": 15, "unique_users": 8},
            ],
            "soap_makers": [
                {"brand": "Declaration Grooming", "shaves": 20, "unique_users": 10},
                {"brand": "Stirling Soap Co", "shaves": 15, "unique_users": 8},
            ],
            "brand_diversity": [
                {"brand": "Declaration Grooming", "unique_soaps": 5},
                {"brand": "Stirling Soap Co", "unique_soaps": 3},
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
        assert "Welcome to your SOTD Lather Log for January 2025" in report_content
        assert "500 shave reports from 25 distinct shavers" in report_content
        assert "100 distinct soaps from 20 distinct brands" in report_content
        assert "## Notes & Caveats" in report_content
        assert "## Soap Makers" in report_content
        assert "## Soaps" in report_content
        assert "## Brand Diversity" in report_content
        assert "## Top Shavers" in report_content

        # Verify that tables are generated
        assert "| name" in report_content
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
