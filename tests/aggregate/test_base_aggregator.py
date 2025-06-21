"""Tests for base aggregator functionality."""

from sotd.aggregate.aggregators.base_aggregator import BaseAggregator


class TestAggregator(BaseAggregator):
    """Test implementation of BaseAggregator for testing."""

    def _extract_data(self, records):
        """Extract test data from records."""
        extracted_data = []
        for record in records:
            product = record.get("test_product", {})
            matched = product.get("matched", {})

            if not matched or not matched.get("brand") or not matched.get("model"):
                continue

            brand = matched.get("brand", "").strip()
            model = matched.get("model", "").strip()
            author = record.get("author", "").strip()

            if brand and model and author:
                extracted_data.append({"brand": brand, "model": model, "author": author})

        return extracted_data

    def _create_composite_name(self, df):
        """Create composite name from brand and model."""
        return df["brand"] + " " + df["model"]


class TestAggregatorWithGrouping(BaseAggregator):
    """Test implementation with additional grouping fields."""

    def _extract_data(self, records):
        """Extract test data with additional grouping field."""
        extracted_data = []
        for record in records:
            product = record.get("test_product", {})
            matched = product.get("matched", {})

            if not matched or not matched.get("brand") or not matched.get("model"):
                continue

            brand = matched.get("brand", "").strip()
            model = matched.get("model", "").strip()
            category = matched.get("category", "").strip()
            author = record.get("author", "").strip()

            if brand and model and category and author:
                extracted_data.append(
                    {"brand": brand, "model": model, "category": category, "author": author}
                )

        return extracted_data

    def _create_composite_name(self, df):
        """Create composite name from brand and model."""
        return df["brand"] + " " + df["model"]

    def _get_group_columns(self, df):
        """Group by name and category."""
        return ["name", "category"]


class TestBaseAggregator:
    """Test cases for BaseAggregator functionality."""

    def test_aggregate_empty_records(self):
        """Test aggregation with empty records."""
        aggregator = TestAggregator()
        result = aggregator.aggregate([])
        assert result == []

    def test_aggregate_no_valid_data(self):
        """Test aggregation with records but no valid data."""
        records = [
            {"test_product": {"matched": {}}, "author": "user1"},
            {"test_product": {"matched": {"brand": ""}}, "author": "user2"},
        ]
        aggregator = TestAggregator()
        result = aggregator.aggregate(records)
        assert result == []

    def test_aggregate_basic_functionality(self):
        """Test basic aggregation functionality."""
        records = [
            {
                "test_product": {"matched": {"brand": "Brand1", "model": "Model1"}},
                "author": "user1",
            },
            {
                "test_product": {"matched": {"brand": "Brand1", "model": "Model1"}},
                "author": "user2",
            },
            {
                "test_product": {"matched": {"brand": "Brand2", "model": "Model2"}},
                "author": "user1",
            },
        ]

        aggregator = TestAggregator()
        result = aggregator.aggregate(records)

        assert len(result) == 2

        # Check first item (Brand1 Model1 - 2 shaves, 2 users)
        assert result[0]["position"] == 1
        assert result[0]["name"] == "Brand1 Model1"
        assert result[0]["shaves"] == 2
        assert result[0]["unique_users"] == 2

        # Check second item (Brand2 Model2 - 1 shave, 1 user)
        assert result[1]["position"] == 2
        assert result[1]["name"] == "Brand2 Model2"
        assert result[1]["shaves"] == 1
        assert result[1]["unique_users"] == 1

    def test_aggregate_with_grouping(self):
        """Test aggregation with additional grouping fields."""
        records = [
            {
                "test_product": {
                    "matched": {"brand": "Brand1", "model": "Model1", "category": "Category1"}
                },
                "author": "user1",
            },
            {
                "test_product": {
                    "matched": {"brand": "Brand1", "model": "Model1", "category": "Category2"}
                },
                "author": "user2",
            },
        ]

        aggregator = TestAggregatorWithGrouping()
        result = aggregator.aggregate(records)

        assert len(result) == 2

        # Check both items have correct grouping
        assert result[0]["name"] == "Brand1 Model1"
        assert result[0]["category"] == "Category1"
        assert result[1]["name"] == "Brand1 Model1"
        assert result[1]["category"] == "Category2"

    def test_sorting_by_shaves_and_users(self):
        """Test that results are sorted by shaves desc, unique_users desc."""
        records = [
            # Brand1 Model1: 3 shaves, 1 user
            {
                "test_product": {"matched": {"brand": "Brand1", "model": "Model1"}},
                "author": "user1",
            },
            {
                "test_product": {"matched": {"brand": "Brand1", "model": "Model1"}},
                "author": "user1",
            },
            {
                "test_product": {"matched": {"brand": "Brand1", "model": "Model1"}},
                "author": "user1",
            },
            # Brand2 Model2: 2 shaves, 2 users
            {
                "test_product": {"matched": {"brand": "Brand2", "model": "Model2"}},
                "author": "user1",
            },
            {
                "test_product": {"matched": {"brand": "Brand2", "model": "Model2"}},
                "author": "user2",
            },
        ]

        aggregator = TestAggregator()
        result = aggregator.aggregate(records)

        # Brand1 Model1 should be first (more shaves)
        assert result[0]["name"] == "Brand1 Model1"
        assert result[0]["shaves"] == 3
        assert result[0]["unique_users"] == 1

        # Brand2 Model2 should be second (fewer shaves, but more unique users)
        assert result[1]["name"] == "Brand2 Model2"
        assert result[1]["shaves"] == 2
        assert result[1]["unique_users"] == 2

    def test_extract_field_utility(self):
        """Test the _extract_field utility method."""
        aggregator = TestAggregator()

        record = {"level1": {"level2": {"level3": "test_value"}}}

        # Test successful extraction
        result = aggregator._extract_field(record, ["level1", "level2", "level3"])
        assert result == "test_value"

        # Test with default value
        result = aggregator._extract_field(record, ["level1", "missing"], "default")
        assert result == "default"

        # Test with None value
        record["level1"]["level2"]["level3"] = ""  # Use empty string instead of None
        result = aggregator._extract_field(record, ["level1", "level2", "level3"], "default")
        assert result == "default"

        # Test with whitespace
        record["level1"]["level2"]["level3"] = "  test  "
        result = aggregator._extract_field(record, ["level1", "level2", "level3"])
        assert result == "test"

    def test_validate_required_fields(self):
        """Test the _validate_required_fields utility method."""
        aggregator = TestAggregator()

        data = {"field1": "value1", "field2": "value2", "field3": ""}

        # Test with all required fields present and non-empty
        assert aggregator._validate_required_fields(data, ["field1", "field2"]) is True

        # Test with missing field
        assert aggregator._validate_required_fields(data, ["field1", "field4"]) is False

        # Test with empty field
        assert aggregator._validate_required_fields(data, ["field1", "field3"]) is False

        # Test with None field
        data["field4"] = ""  # Use empty string instead of None
        assert aggregator._validate_required_fields(data, ["field1", "field4"]) is False

    def test_position_ranking(self):
        """Test that position rankings are correctly assigned."""
        records = [
            {
                "test_product": {"matched": {"brand": "Brand1", "model": "Model1"}},
                "author": "user1",
            },
            {
                "test_product": {"matched": {"brand": "Brand2", "model": "Model2"}},
                "author": "user2",
            },
            {
                "test_product": {"matched": {"brand": "Brand3", "model": "Model3"}},
                "author": "user3",
            },
        ]

        aggregator = TestAggregator()
        result = aggregator.aggregate(records)

        # Check that positions are 1-based and sequential
        for i, item in enumerate(result):
            assert item["position"] == i + 1

    def test_data_types_in_result(self):
        """Test that result data types are correct."""
        records = [
            {
                "test_product": {"matched": {"brand": "Brand1", "model": "Model1"}},
                "author": "user1",
            },
        ]

        aggregator = TestAggregator()
        result = aggregator.aggregate(records)

        assert len(result) == 1
        item = result[0]

        # Check data types
        assert isinstance(item["position"], int)
        assert isinstance(item["shaves"], int)
        assert isinstance(item["unique_users"], int)
        assert isinstance(item["name"], str)
