"""Unit tests for search index generation script."""

import json

from scripts.generate_search_index import (
    extract_products_from_category,
    extract_users_from_data,
    generate_search_index,
    merge_products,
    merge_users,
    parse_brand_model_from_name,
    process_annual_file,
    process_monthly_file,
)


class TestParseBrandModelFromName:
    """Test parsing brand and model from composite names."""

    def test_parse_brand_model_two_words(self):
        """Test parsing 'Brand Model' format."""
        brand, model = parse_brand_model_from_name("Blackland Blackbird")
        assert brand == "Blackland"
        assert model == "Blackbird"

    def test_parse_brand_model_multiple_words(self):
        """Test parsing brand with multiple words in model."""
        brand, model = parse_brand_model_from_name("Gillette Super Speed")
        assert brand == "Gillette"
        assert model == "Super Speed"

    def test_parse_single_word(self):
        """Test parsing single word (treat as brand only)."""
        brand, model = parse_brand_model_from_name("Rockwell")
        assert brand == "Rockwell"
        assert model == ""

    def test_parse_empty_string(self):
        """Test parsing empty string."""
        brand, model = parse_brand_model_from_name("")
        assert brand == ""
        assert model == ""


class TestExtractProductsFromCategory:
    """Test product extraction from category data."""

    def test_extract_razors_with_brand_model(self):
        """Test extracting razors when brand/model fields exist."""
        category_data = [
            {
                "name": "Blackland Blackbird",
                "brand": "Blackland",
                "model": "Blackbird",
                "shaves": 10,
            },
            {"name": "Gillette Tech", "brand": "Gillette", "model": "Tech", "shaves": 5},
        ]
        month = "2025-12"
        products = extract_products_from_category(category_data, "razor", month)

        assert len(products) == 2
        assert "razor:blackland:blackbird" in products
        assert products["razor:blackland:blackbird"]["type"] == "razor"
        assert products["razor:blackland:blackbird"]["brand"] == "Blackland"
        assert products["razor:blackland:blackbird"]["model"] == "Blackbird"
        assert products["razor:blackland:blackbird"]["first_seen"] == month
        assert products["razor:blackland:blackbird"]["last_seen"] == month

    def test_extract_razors_parse_from_name(self):
        """Test extracting razors when brand/model not in fields, parse from name."""
        category_data = [
            {"name": "Blackland Blackbird", "shaves": 10},
            {"name": "Gillette Tech", "shaves": 5},
        ]
        month = "2025-12"
        products = extract_products_from_category(category_data, "razor", month)

        assert len(products) == 2
        assert "razor:blackland:blackbird" in products
        assert products["razor:blackland:blackbird"]["brand"] == "Blackland"
        assert products["razor:blackland:blackbird"]["model"] == "Blackbird"

    def test_extract_soaps_with_brand_scent(self):
        """Test extracting soaps with brand and scent fields."""
        category_data = [
            {
                "name": "Stirling Soap Co. - Christmas Eve",
                "brand": "Stirling Soap Co.",
                "scent": "Christmas Eve",
                "shaves": 20,
            },
            {
                "name": "Barrister and Mann - Seville",
                "brand": "Barrister and Mann",
                "scent": "Seville",
                "shaves": 15,
            },
        ]
        month = "2025-12"
        products = extract_products_from_category(category_data, "soap", month)

        assert len(products) == 2
        assert "soap:stirling soap co.:christmas eve" in products
        assert products["soap:stirling soap co.:christmas eve"]["type"] == "soap"
        assert products["soap:stirling soap co.:christmas eve"]["brand"] == "Stirling Soap Co."
        assert products["soap:stirling soap co.:christmas eve"]["scent"] == "Christmas Eve"

    def test_extract_products_empty_category(self):
        """Test extracting from empty category."""
        category_data = []
        month = "2025-12"
        products = extract_products_from_category(category_data, "razor", month)
        assert len(products) == 0

    def test_extract_products_missing_brand(self):
        """Test extracting products when brand is missing (should skip)."""
        category_data = [
            {"name": "Some Razor", "shaves": 10},  # No brand field
        ]
        month = "2025-12"
        products = extract_products_from_category(category_data, "razor", month)
        # Should parse from name
        assert len(products) == 1
        assert "razor:some:razor" in products


class TestExtractUsersFromData:
    """Test user extraction from aggregated data."""

    def test_extract_users_from_data_section(self):
        """Test extracting users from data.users section."""
        data = {
            "data": {
                "users": [
                    {"user": "testuser1", "shaves": 10},
                    {"user": "testuser2", "shaves": 5},
                ]
            }
        }
        month = "2025-12"
        users = extract_users_from_data(data, month)

        assert len(users) == 2
        assert "testuser1" in users
        assert users["testuser1"]["username"] == "testuser1"
        assert users["testuser1"]["first_seen"] == month
        assert users["testuser1"]["last_seen"] == month

    def test_extract_users_username_field(self):
        """Test extracting users with 'username' field instead of 'user'."""
        data = {
            "data": {
                "users": [
                    {"username": "testuser1", "shaves": 10},
                ]
            }
        }
        month = "2025-12"
        users = extract_users_from_data(data, month)

        assert len(users) == 1
        assert "testuser1" in users

    def test_extract_users_empty_data(self):
        """Test extracting users from data without users section."""
        data = {"data": {}}
        month = "2025-12"
        users = extract_users_from_data(data, month)
        assert len(users) == 0


class TestMergeProducts:
    """Test merging products across months."""

    def test_merge_new_product(self):
        """Test merging a new product."""
        existing = {}
        new = {
            "razor:blackland:blackbird": {
                "type": "razor",
                "brand": "Blackland",
                "model": "Blackbird",
                "first_seen": "2025-12",
                "last_seen": "2025-12",
            }
        }
        merge_products(existing, new)
        assert len(existing) == 1
        assert "razor:blackland:blackbird" in existing

    def test_merge_existing_product_update_dates(self):
        """Test merging existing product updates first_seen/last_seen."""
        existing = {
            "razor:blackland:blackbird": {
                "type": "razor",
                "brand": "Blackland",
                "model": "Blackbird",
                "first_seen": "2025-12",
                "last_seen": "2025-12",
            }
        }
        new = {
            "razor:blackland:blackbird": {
                "type": "razor",
                "brand": "Blackland",
                "model": "Blackbird",
                "first_seen": "2026-01",
                "last_seen": "2026-01",
            }
        }
        merge_products(existing, new)
        assert existing["razor:blackland:blackbird"]["first_seen"] == "2025-12"  # Earlier
        assert existing["razor:blackland:blackbird"]["last_seen"] == "2026-01"  # Later

    def test_merge_existing_product_earlier_first_seen(self):
        """Test merging updates first_seen if new month is earlier."""
        existing = {
            "razor:blackland:blackbird": {
                "type": "razor",
                "brand": "Blackland",
                "model": "Blackbird",
                "first_seen": "2025-12",
                "last_seen": "2025-12",
            }
        }
        new = {
            "razor:blackland:blackbird": {
                "type": "razor",
                "brand": "Blackland",
                "model": "Blackbird",
                "first_seen": "2025-11",
                "last_seen": "2025-11",
            }
        }
        merge_products(existing, new)
        assert existing["razor:blackland:blackbird"]["first_seen"] == "2025-11"  # Updated
        assert existing["razor:blackland:blackbird"]["last_seen"] == "2025-12"  # Kept later


class TestMergeUsers:
    """Test merging users across months."""

    def test_merge_new_user(self):
        """Test merging a new user."""
        existing = {}
        new = {
            "testuser1": {
                "username": "testuser1",
                "first_seen": "2025-12",
                "last_seen": "2025-12",
            }
        }
        merge_users(existing, new)
        assert len(existing) == 1
        assert "testuser1" in existing

    def test_merge_existing_user_update_dates(self):
        """Test merging existing user updates first_seen/last_seen."""
        existing = {
            "testuser1": {
                "username": "testuser1",
                "first_seen": "2025-12",
                "last_seen": "2025-12",
            }
        }
        new = {
            "testuser1": {
                "username": "testuser1",
                "first_seen": "2026-01",
                "last_seen": "2026-01",
            }
        }
        merge_users(existing, new)
        assert existing["testuser1"]["first_seen"] == "2025-12"  # Earlier
        assert existing["testuser1"]["last_seen"] == "2026-01"  # Later


class TestProcessMonthlyFile:
    """Test processing monthly aggregation files."""

    def test_process_monthly_file_success(self, tmp_path):
        """Test successfully processing a monthly file."""
        data_dir = tmp_path / "data"
        aggregated_dir = data_dir / "aggregated"
        aggregated_dir.mkdir(parents=True)

        monthly_file = aggregated_dir / "2025-12.json"
        monthly_data = {
            "meta": {"month": "2025-12", "total_shaves": 100},
            "data": {
                "razors": [
                    {
                        "name": "Blackland Blackbird",
                        "brand": "Blackland",
                        "model": "Blackbird",
                        "shaves": 10,
                    }
                ],
                "blades": [
                    {"name": "Gillette Nacet", "brand": "Gillette", "model": "Nacet", "shaves": 5}
                ],
                "brushes": [
                    {"name": "Semogue 610", "brand": "Semogue", "model": "610", "shaves": 3}
                ],
                "soaps": [
                    {
                        "name": "Stirling Soap Co. - Christmas Eve",
                        "brand": "Stirling Soap Co.",
                        "scent": "Christmas Eve",
                        "shaves": 20,
                    }
                ],
                "users": [{"user": "testuser1", "shaves": 10}],
            },
        }

        with monthly_file.open("w", encoding="utf-8") as f:
            json.dump(monthly_data, f)

        products, users, month = process_monthly_file(monthly_file, data_dir)

        assert month == "2025-12"
        assert len(products) == 4  # razor, blade, brush, soap
        assert len(users) == 1

    def test_process_monthly_file_missing_file(self, tmp_path):
        """Test processing non-existent file (should handle gracefully)."""
        data_dir = tmp_path / "data"
        file_path = data_dir / "aggregated" / "2025-12.json"
        products, users, month = process_monthly_file(file_path, data_dir)
        assert len(products) == 0
        assert len(users) == 0

    def test_process_monthly_file_invalid_json(self, tmp_path):
        """Test processing invalid JSON file (should handle gracefully)."""
        data_dir = tmp_path / "data"
        aggregated_dir = data_dir / "aggregated"
        aggregated_dir.mkdir(parents=True)

        monthly_file = aggregated_dir / "2025-12.json"
        monthly_file.write_text("invalid json", encoding="utf-8")

        products, users, month = process_monthly_file(monthly_file, data_dir)
        assert len(products) == 0
        assert len(users) == 0


class TestProcessAnnualFile:
    """Test processing annual aggregation files."""

    def test_process_annual_file_success(self, tmp_path):
        """Test successfully processing an annual file."""
        data_dir = tmp_path / "data"
        aggregated_dir = data_dir / "aggregated"
        annual_dir = aggregated_dir / "annual"
        annual_dir.mkdir(parents=True)

        annual_file = annual_dir / "2025.json"
        annual_data = {
            "metadata": {
                "year": "2025",
                "included_months": ["2025-01", "2025-02", "2025-03"],
            },
            "razors": [
                {
                    "name": "Blackland Blackbird",
                    "brand": "Blackland",
                    "model": "Blackbird",
                    "shaves": 100,
                }
            ],
            "users": [{"user": "testuser1", "shaves": 50}],
        }

        with annual_file.open("w", encoding="utf-8") as f:
            json.dump(annual_data, f)

        products, users, months = process_annual_file(annual_file, data_dir)

        assert len(products) == 1
        assert len(users) == 1
        assert "2025-01" in months
        assert "2025-02" in months
        assert "2025-03" in months


class TestGenerateSearchIndex:
    """Test full search index generation."""

    def test_generate_search_index_success(self, tmp_path):
        """Test successfully generating search index."""
        data_dir = tmp_path / "data"
        aggregated_dir = data_dir / "aggregated"
        aggregated_dir.mkdir(parents=True)

        # Create monthly file
        monthly_file = aggregated_dir / "2025-12.json"
        monthly_data = {
            "meta": {"month": "2025-12"},
            "data": {
                "razors": [
                    {
                        "name": "Blackland Blackbird",
                        "brand": "Blackland",
                        "model": "Blackbird",
                        "shaves": 10,
                    }
                ],
                "soaps": [
                    {
                        "name": "Stirling Soap Co. - Christmas Eve",
                        "brand": "Stirling Soap Co.",
                        "scent": "Christmas Eve",
                        "shaves": 20,
                    }
                ],
                "users": [{"user": "testuser1", "shaves": 10}],
            },
        }
        with monthly_file.open("w", encoding="utf-8") as f:
            json.dump(monthly_data, f)

        # Create another monthly file
        monthly_file2 = aggregated_dir / "2026-01.json"
        monthly_data2 = {
            "meta": {"month": "2026-01"},
            "data": {
                "razors": [
                    {
                        "name": "Blackland Blackbird",
                        "brand": "Blackland",
                        "model": "Blackbird",
                        "shaves": 5,
                    }
                ],
                "users": [{"user": "testuser1", "shaves": 5}],
            },
        }
        with monthly_file2.open("w", encoding="utf-8") as f:
            json.dump(monthly_data2, f)

        output_path = data_dir / "search_index.json"
        success = generate_search_index(data_dir, output_path)

        assert success is True
        assert output_path.exists()

        with output_path.open("r", encoding="utf-8") as f:
            index = json.load(f)

        assert "products" in index
        assert "users" in index
        assert "available_months" in index
        assert "available_years" in index
        assert "generated_at" in index

        # Check products
        products = index["products"]
        assert len(products) >= 1
        razor = next(
            (p for p in products if p["type"] == "razor" and p["brand"] == "Blackland"), None
        )
        assert razor is not None
        assert razor["first_seen"] == "2025-12"
        assert razor["last_seen"] == "2026-01"  # Updated from later month

        # Check users
        users = index["users"]
        assert len(users) >= 1
        user = next((u for u in users if u["username"] == "testuser1"), None)
        assert user is not None
        assert user["first_seen"] == "2025-12"
        assert user["last_seen"] == "2026-01"  # Updated from later month

        # Check months and years
        assert "2025-12" in index["available_months"]
        assert "2026-01" in index["available_months"]
        assert "2025" in index["available_years"]
        assert "2026" in index["available_years"]

    def test_generate_search_index_missing_directory(self, tmp_path):
        """Test generating index when aggregated directory doesn't exist."""
        data_dir = tmp_path / "data"
        output_path = data_dir / "search_index.json"
        success = generate_search_index(data_dir, output_path)
        assert success is False
