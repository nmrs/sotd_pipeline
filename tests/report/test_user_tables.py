"""Tests for Top Shavers table generation using the universal TableGenerator."""

from sotd.report.table_generators.table_generator import TableGenerator


class TestTopShaversTableGenerator:
    def test_empty_data(self):
        generator = TableGenerator({}, debug=False)
        data = generator.generate_table("top-shavers")
        assert data == []

    def test_missing_required_fields(self):
        sample_data = {
            "users": [
                {"user": "user1"},  # Missing shaves and missed_days
                {"shaves": 10, "missed_days": 2},  # Missing user
                {"user": "user2", "shaves": 8, "missed_days": 1},  # Valid
            ]
        }
        generator = TableGenerator(sample_data, debug=False)
        data = generator.generate_table("top-shavers")
        assert len(data) == 1
        assert data[0]["user_display"] == "u/user2"
        assert data[0]["user"] == "user2"
        assert data[0]["shaves"] == 8
        assert data[0]["missed_days"] == 1

    def test_valid_data(self):
        sample_data = {
            "users": [
                {"user": "user1", "shaves": 15, "missed_days": 2, "rank": 1},
                {"user": "user2", "shaves": 12, "missed_days": 1, "rank": 2}]
        }
        generator = TableGenerator(sample_data, debug=False)
        data = generator.generate_table("specific-table")
        assert len(data) == 2
        assert data[0]["user_display"] == "u/user1"
        assert data[1]["user_display"] == "u/user2"
        assert data[0]["user"] == "user1"
        assert data[1]["user"] == "user2"
        assert data[0]["rank"] == 1
        assert data[1]["rank"] == 2

    def test_tie_breaking_at_20th(self):
        # 18 users with unique shaves, 2 with same shaves/missed_days as 20th
        users = [
            {"user": f"user{i}", "shaves": 40 - i, "missed_days": i, "rank": i + 1}
            for i in range(18)
        ]
        # 19th and 20th have same shaves/missed_days
        users += [
            {"user": "user19", "shaves": 21, "missed_days": 2, "rank": 19},
            {"user": "user20", "shaves": 21, "missed_days": 2, "rank": 20},
            {
                "user": "user21",
                "shaves": 21,
                "missed_days": 2,
                "rank": 21},  # Should be included
        ]
        sample_data = {"users": users}
        generator = TableGenerator(sample_data, debug=False)
        data = generator.generate_table("specific-table")
        # All 21 should be included due to tie at 20th
        assert len(data) == 21
        assert any(u["user_display"] == "u/user21" for u in data)

    def test_table_title_and_columns(self):
        generator = TableGenerator({}, debug=False)
        assert generator.get_table_title() == "Top Shavers"
        config = generator.get_column_config()
        assert "user_display" in config
        assert "shaves" in config
        assert "missed_days" in config

    def test_delta_column_logic(self):
        # Current and previous data for delta calculation
        current_data = {
            "users": [
                {"user": "user1", "shaves": 10, "missed_days": 1, "rank": 1},
                {"user": "user2", "shaves": 8, "missed_days": 2, "rank": 2}]
        }
        previous_data = {
            "previous month": (
                {"month": "2024-12"},  # metadata
                {  # data
                    "users": [
                        {"user": "user1", "shaves": 8, "missed_days": 2, "rank": 2},
                        {"user": "user2", "shaves": 10, "missed_days": 1, "rank": 1}]},
            )
        }
        generator = TableGenerator(current_data, debug=False)
        # Simulate delta calculation via base class (handled in generate_table)
        table_md = generator.generate_table(
            max_rows=20,
            include_delta=True,
            comparison_data=previous_data,
        )
        assert "Δ vs previous month" in table_md
        # The delta calculation should work with the u/ prefix since we use the original
        # username for matching
        assert "↑" in table_md or "↓" in table_md or "=" in table_md
