"""Tests for the observations generator."""

from sotd.report.observations import ObservationsGenerator


class TestObservationsGenerator:
    """Test the ObservationsGenerator class."""

    def test_basic_statistics(self):
        """Test basic statistics generation."""
        metadata = {
            "total_shaves": 1622,
            "unique_shavers": 110,
            "avg_shaves_per_user": 14.75,
        }
        data = {}
        generator = ObservationsGenerator(metadata, data)

        observations = generator.generate_observations()

        assert "1,622 shaves" in observations
        assert "110 unique users" in observations
        assert "14.8 shaves per user" in observations

    def test_top_performers(self):
        """Test top performers generation."""
        metadata = {"total_shaves": 100, "unique_shavers": 10}
        data = {
            "razors": [{"name": "Test Razor", "shaves": 50, "unique_users": 5}],
            "blades": [{"name": "Test Blade", "shaves": 40, "unique_users": 4}],
            "brushes": [{"name": "Test Brush", "shaves": 30, "unique_users": 3}],
        }
        generator = ObservationsGenerator(metadata, data)

        observations = generator.generate_observations()

        assert "Test Razor" in observations
        assert "Test Blade" in observations
        assert "Test Brush" in observations
        assert "50 shaves" in observations
        assert "40 shaves" in observations
        assert "30 shaves" in observations

    def test_format_insights(self):
        """Test format insights generation."""
        metadata = {"total_shaves": 100, "unique_shavers": 10}
        data = {
            "razor_formats": [
                {"name": "DE", "shaves": 60},
                {"name": "Straight", "shaves": 30},
                {"name": "GEM", "shaves": 10},
            ]
        }
        generator = ObservationsGenerator(metadata, data)

        observations = generator.generate_observations()

        assert "DE (60.0%)" in observations
        assert "Straight (30.0%)" in observations
        assert "GEM (10.0%)" in observations

    def test_user_engagement_high(self):
        """Test user engagement classification for high engagement."""
        metadata = {"total_shaves": 1500, "unique_shavers": 100}
        data = {}
        generator = ObservationsGenerator(metadata, data)

        observations = generator.generate_observations()

        assert "high" in observations
        assert "15.0 shaves" in observations

    def test_user_engagement_moderate(self):
        """Test user engagement classification for moderate engagement."""
        metadata = {"total_shaves": 1000, "unique_shavers": 100}
        data = {}
        generator = ObservationsGenerator(metadata, data)

        observations = generator.generate_observations()

        assert "moderate" in observations
        assert "10.0 shaves" in observations

    def test_user_engagement_low(self):
        """Test user engagement classification for low engagement."""
        metadata = {"total_shaves": 500, "unique_shavers": 100}
        data = {}
        generator = ObservationsGenerator(metadata, data)

        observations = generator.generate_observations()

        assert "lower" in observations
        assert "5.0 shaves" in observations

    def test_empty_data(self):
        """Test behavior with empty data."""
        metadata = {"total_shaves": 0, "unique_shavers": 0}
        data = {}
        generator = ObservationsGenerator(metadata, data)

        observations = generator.generate_observations()

        assert "0 shaves" in observations
        assert "0 unique users" in observations

    def test_missing_data_fields(self):
        """Test behavior with missing data fields."""
        metadata = {}
        data = {}
        generator = ObservationsGenerator(metadata, data)

        observations = generator.generate_observations()

        # Should handle missing fields gracefully
        assert "0 shaves" in observations
        assert "0 unique users" in observations

    def test_comparison_data_not_used_when_empty(self):
        """Test that comparison data is not used when empty."""
        metadata = {"total_shaves": 100, "unique_shavers": 10}
        data = {}
        comparison_data = {}
        generator = ObservationsGenerator(metadata, data, comparison_data)

        observations = generator.generate_observations()

        # Should not include trend analysis sections when no comparison data
        assert "Format Trends" not in observations
        assert "Manufacturer Trends" not in observations
