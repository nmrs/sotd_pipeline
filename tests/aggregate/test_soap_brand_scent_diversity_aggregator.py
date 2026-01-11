#!/usr/bin/env python3
"""Tests for SoapBrandScentDiversityAggregator."""

from sotd.aggregate.aggregators.users.soap_brand_scent_diversity_aggregator import (
    SoapBrandScentDiversityAggregator,
    aggregate_soap_brand_scent_diversity,
)


class TestSoapBrandScentDiversityAggregator:
    """Test SoapBrandScentDiversityAggregator functionality."""

    def test_extract_data_with_brand_and_scent_info(self):
        """Test data extraction with brand and scent information."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "matched": {"brand": "Declaration Grooming", "scent": "B2"},
                },
            },
            {
                "author": "user2",
                "soap": {
                    "matched": {"brand": "Barrister & Mann", "scent": "Seville"},
                },
            },
        ]

        aggregator = SoapBrandScentDiversityAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 2
        assert extracted[0]["brand"] == "Declaration Grooming"
        assert extracted[0]["scent"] == "B2"
        assert extracted[0]["author"] == "user1"
        assert extracted[1]["brand"] == "Barrister & Mann"
        assert extracted[1]["scent"] == "Seville"
        assert extracted[1]["author"] == "user2"

    def test_extract_data_skips_records_without_brand(self):
        """Test that records without brand are skipped."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "matched": {"scent": "B2"},
                },
            },
            {
                "author": "user2",
                "soap": {
                    "matched": {"brand": "Barrister & Mann", "scent": "Seville"},
                },
            },
        ]

        aggregator = SoapBrandScentDiversityAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 1
        assert extracted[0]["brand"] == "Barrister & Mann"
        assert extracted[0]["scent"] == "Seville"

    def test_extract_data_skips_records_without_scent(self):
        """Test that records without scent are skipped."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "matched": {"brand": "Declaration Grooming"},
                },
            },
            {
                "author": "user2",
                "soap": {
                    "matched": {"brand": "Barrister & Mann", "scent": "Seville"},
                },
            },
        ]

        aggregator = SoapBrandScentDiversityAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 1
        assert extracted[0]["brand"] == "Barrister & Mann"
        assert extracted[0]["scent"] == "Seville"

    def test_extract_data_skips_records_without_matched_soap(self):
        """Test that records without matched soap are skipped."""
        records = [
            {
                "author": "user1",
                "soap": {},
            },
            {
                "author": "user2",
                "soap": {
                    "matched": {"brand": "Barrister & Mann", "scent": "Seville"},
                },
            },
        ]

        aggregator = SoapBrandScentDiversityAggregator()
        extracted = aggregator._extract_data(records)

        assert len(extracted) == 1
        assert extracted[0]["brand"] == "Barrister & Mann"
        assert extracted[0]["scent"] == "Seville"

    def test_create_composite_name(self):
        """Test composite name creation."""
        aggregator = SoapBrandScentDiversityAggregator()

        # Mock DataFrame
        import pandas as pd

        df = pd.DataFrame(
            {
                "brand": ["Declaration Grooming", "Barrister & Mann"],
                "scent": ["B2", "Seville"],
            }
        )

        composite_names = aggregator._create_composite_name(df)

        assert composite_names.iloc[0] == "Declaration Grooming - B2"
        assert composite_names.iloc[1] == "Barrister & Mann - Seville"

    def test_aggregate_brand_scent_diversity(self):
        """Test complete aggregation of brand+scent diversity data."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "matched": {"brand": "Declaration Grooming", "scent": "B2"},
                },
            },
            {
                "author": "user1",
                "soap": {
                    "matched": {"brand": "Declaration Grooming", "scent": "B3"},
                },
            },
            {
                "author": "user1",
                "soap": {
                    "matched": {"brand": "Barrister & Mann", "scent": "Seville"},
                },
            },
            {
                "author": "user2",
                "soap": {
                    "matched": {"brand": "Declaration Grooming", "scent": "B2"},
                },
            },
        ]

        result = aggregate_soap_brand_scent_diversity(records)

        assert len(result) == 2

        # Check first result (user1 with 3 unique combinations, 3 total shaves)
        assert result[0]["rank"] == 1
        assert result[0]["user"] == "user1"
        assert result[0]["unique_combinations"] == 3
        assert result[0]["shaves"] == 3
        assert result[0]["unique_users"] == 1

        # Check second result (user2 with 1 unique combination, 1 total shave)
        assert result[1]["rank"] == 2
        assert result[1]["user"] == "user2"
        assert result[1]["unique_combinations"] == 1
        assert result[1]["shaves"] == 1
        assert result[1]["unique_users"] == 1

    def test_aggregate_empty_records(self):
        """Test aggregation with empty records."""
        result = aggregate_soap_brand_scent_diversity([])
        assert result == []

    def test_aggregate_no_brand_scent_records(self):
        """Test aggregation with no brand+scent records."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "matched": {"brand": "Declaration Grooming"},
                },
            },
        ]

        result = aggregate_soap_brand_scent_diversity(records)
        assert result == []

    def test_aggregate_single_user_multiple_combinations(self):
        """Test aggregation for single user with multiple brand+scent combinations."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "matched": {"brand": "Declaration Grooming", "scent": "B2"},
                },
            },
            {
                "author": "user1",
                "soap": {
                    "matched": {"brand": "Declaration Grooming", "scent": "B3"},
                },
            },
            {
                "author": "user1",
                "soap": {
                    "matched": {"brand": "Barrister & Mann", "scent": "Seville"},
                },
            },
            {
                "author": "user1",
                "soap": {
                    "matched": {"brand": "Noble Otter", "scent": "Lonestar"},
                },
            },
        ]

        result = aggregate_soap_brand_scent_diversity(records)

        assert len(result) == 1
        assert result[0]["rank"] == 1
        assert result[0]["user"] == "user1"
        assert result[0]["unique_combinations"] == 4
        assert result[0]["shaves"] == 4
        assert result[0]["unique_users"] == 1

    def test_aggregate_same_brand_different_scents(self):
        """Test aggregation for same brand with different scents."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "matched": {"brand": "Declaration Grooming", "scent": "B2"},
                },
            },
            {
                "author": "user1",
                "soap": {
                    "matched": {"brand": "Declaration Grooming", "scent": "B3"},
                },
            },
            {
                "author": "user1",
                "soap": {
                    "matched": {"brand": "Declaration Grooming", "scent": "B4"},
                },
            },
        ]

        result = aggregate_soap_brand_scent_diversity(records)

        assert len(result) == 1
        assert result[0]["rank"] == 1
        assert result[0]["user"] == "user1"
        assert result[0]["unique_combinations"] == 3
        assert result[0]["shaves"] == 3
        assert result[0]["unique_users"] == 1

    def test_hhi_calculation_single_soap(self):
        """Test HHI calculation for user with single soap (maximum concentration)."""
        # Example A: 32 shaves, 1 soap → HHI = 1.0, effective_soaps = 1.0
        records = []
        for _ in range(32):
            records.append(
                {
                    "author": "user1",
                    "soap": {
                        "matched": {"brand": "Declaration Grooming", "scent": "B2"},
                    },
                }
            )

        result = aggregate_soap_brand_scent_diversity(records)

        assert len(result) == 1
        assert result[0]["user"] == "user1"
        assert result[0]["shaves"] == 32
        assert result[0]["unique_combinations"] == 1
        # Single soap: p = 1, HHI = 1² = 1.0
        assert abs(result[0]["hhi"] - 1.0) < 0.0001
        # Effective soaps = 1 / HHI = 1 / 1.0 = 1.0
        assert abs(result[0]["effective_soaps"] - 1.0) < 0.01

    def test_hhi_calculation_even_distribution(self):
        """Test HHI calculation for user with even distribution across soaps."""
        # Example B: 64 shaves, 4 soaps (16 each) → HHI = 0.25, effective_soaps = 4.0
        records = []
        soaps = [
            {"brand": "Declaration Grooming", "scent": "B2"},
            {"brand": "Barrister & Mann", "scent": "Seville"},
            {"brand": "Noble Otter", "scent": "Lonestar"},
            {"brand": "Stirling Soap Co.", "scent": "Executive Man"},
        ]
        for soap in soaps:
            for _ in range(16):
                records.append(
                    {
                        "author": "user1",
                        "soap": {"matched": soap},
                    }
                )

        result = aggregate_soap_brand_scent_diversity(records)

        assert len(result) == 1
        assert result[0]["user"] == "user1"
        assert result[0]["shaves"] == 64
        assert result[0]["unique_combinations"] == 4
        # Even distribution: each p = 16/64 = 0.25, HHI = 4 * (0.25²) = 4 * 0.0625 = 0.25
        assert abs(result[0]["hhi"] - 0.25) < 0.0001
        # Effective soaps = 1 / HHI = 1 / 0.25 = 4.0
        assert abs(result[0]["effective_soaps"] - 4.0) < 0.01

    def test_hhi_calculation_concentrated(self):
        """Test HHI calculation for user with concentrated distribution."""
        # Example C: 64 shaves, 4 soaps (52/4/4/4) → HHI ≈ 0.6719, effective_soaps ≈ 1.49
        records = []
        # 52 shaves with first soap
        for _ in range(52):
            records.append(
                {
                    "author": "user1",
                    "soap": {"matched": {"brand": "Declaration Grooming", "scent": "B2"}},
                }
            )
        # 4 shaves each with other 3 soaps
        other_soaps = [
            {"brand": "Barrister & Mann", "scent": "Seville"},
            {"brand": "Noble Otter", "scent": "Lonestar"},
            {"brand": "Stirling Soap Co.", "scent": "Executive Man"},
        ]
        for soap in other_soaps:
            for _ in range(4):
                records.append(
                    {
                        "author": "user1",
                        "soap": {"matched": soap},
                    }
                )

        result = aggregate_soap_brand_scent_diversity(records)

        assert len(result) == 1
        assert result[0]["user"] == "user1"
        assert result[0]["shaves"] == 64
        assert result[0]["unique_combinations"] == 4
        # Concentrated: p's are 52/64 = 0.8125 and 4/64 = 0.0625 (three times)
        # HHI = 0.8125² + 3*(0.0625²) = 0.6602 + 3*0.0039 ≈ 0.6719
        assert abs(result[0]["hhi"] - 0.6719) < 0.0001
        # Effective soaps = 1 / HHI = 1 / 0.6719 ≈ 1.49
        assert abs(result[0]["effective_soaps"] - 1.49) < 0.01

    def test_hhi_in_aggregate_output(self):
        """Test that hhi and effective_soaps are included in aggregation output."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "matched": {"brand": "Declaration Grooming", "scent": "B2"},
                },
            },
            {
                "author": "user1",
                "soap": {
                    "matched": {"brand": "Barrister & Mann", "scent": "Seville"},
                },
            },
        ]

        result = aggregate_soap_brand_scent_diversity(records)

        assert len(result) == 1
        assert "hhi" in result[0]
        assert "effective_soaps" in result[0]
        assert isinstance(result[0]["hhi"], (int, float))
        assert isinstance(result[0]["effective_soaps"], (int, float))
        assert result[0]["hhi"] >= 0.0
        assert result[0]["hhi"] <= 1.0
        assert result[0]["effective_soaps"] >= 0.0
