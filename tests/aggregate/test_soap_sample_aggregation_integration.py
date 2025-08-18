#!/usr/bin/env python3
"""Integration tests for soap sample aggregation in the aggregate phase."""

from sotd.aggregate.processor import aggregate_all


class TestSoapSampleAggregationIntegration:
    """Test that soap sample aggregation integrates correctly with the aggregate phase."""

    def test_soap_sample_aggregation_in_processor(self):
        """Test that soap sample aggregation is included in aggregate_all output."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "matched": {"maker": "B&M", "scent": "Seville"},
                    "enriched": {"sample_type": "sample"},
                },
            },
            {
                "author": "user2",
                "soap": {
                    "matched": {"maker": "B&M", "scent": "Seville"},
                    "enriched": {"sample_type": "sample"},
                },
            },
            {
                "author": "user1",
                "soap": {
                    "matched": {"maker": "Declaration Grooming", "scent": "Persephone"},
                    "enriched": {"sample_type": "tester"},
                },
            },
            {
                "author": "user3",
                "soap": {
                    "matched": {"maker": "Stirling", "scent": "Bay Rum"},
                    # No enriched section - regular soap
                },
            },
        ]

        result = aggregate_all(records, "2025-08", debug=False)

        # Check that soap_samples is included in the output
        assert "soap_samples" in result["data"], "soap_samples should be in aggregate output"
        
        soap_samples = result["data"]["soap_samples"]
        assert len(soap_samples) == 2, f"Expected 2 soap sample entries, got {len(soap_samples)}"
        
        # Check that the sample data is correctly aggregated
        sample_names = [entry["name"] for entry in soap_samples]
        assert "sample - B&M - Seville" in sample_names, (
            "B&M Seville sample should be aggregated"
        )
        assert "tester - Declaration Grooming - Persephone" in sample_names, (
            "Declaration Grooming tester should be aggregated"
        )
        
        # Check that regular soaps are not included
        assert "Stirling - Bay Rum" not in sample_names, (
            "Regular soaps should not be in sample aggregation"
        )

    def test_soap_sample_aggregation_with_regular_soaps(self):
        """Test that regular soap aggregation still works alongside sample aggregation."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "matched": {"maker": "B&M", "scent": "Seville"},
                    "enriched": {"sample_type": "sample"},
                },
            },
            {
                "author": "user2",
                "soap": {
                    "matched": {"maker": "B&M", "scent": "Seville"},
                    # No enriched section - regular soap
                },
            },
        ]

        result = aggregate_all(records, "2025-08", debug=False)

        # Check that both aggregations work
        assert "soaps" in result["data"], "Regular soap aggregation should work"
        assert "soap_samples" in result["data"], "Soap sample aggregation should work"
        
        # Regular soaps should include both entries (sample and regular)
        soaps = result["data"]["soaps"]
        assert len(soaps) == 1, "Regular soap aggregation should include all soaps"
        assert soaps[0]["name"] == "B&M - Seville", "Regular soap name should be correct"
        assert soaps[0]["shaves"] == 2, "Regular soap should count both shaves"
        
        # Sample aggregation should only include the sample
        soap_samples = result["data"]["soap_samples"]
        assert len(soap_samples) == 1, "Sample aggregation should only include samples"
        assert soap_samples[0]["name"] == "sample - B&M - Seville", "Sample name should be correct"
        assert soap_samples[0]["shaves"] == 1, "Sample should only count sample shaves"

    def test_soap_sample_aggregation_empty_data(self):
        """Test that soap sample aggregation handles empty data gracefully."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "matched": {"maker": "B&M", "scent": "Seville"},
                    # No enriched section - no samples
                },
            },
        ]

        result = aggregate_all(records, "2025-08", debug=False)

        # Soap samples should be empty but present
        assert "soap_samples" in result["data"], "soap_samples should be present even when empty"
        assert result["data"]["soap_samples"] == [], "soap_samples should be empty list when no samples"
        
        # Regular soap aggregation should still work
        assert "soaps" in result["data"], "Regular soap aggregation should work"
        assert len(result["data"]["soaps"]) == 1, "Regular soap should be aggregated"

    def test_soap_sample_aggregation_metadata_included(self):
        """Test that soap sample aggregation includes proper metadata."""
        records = [
            {
                "author": "user1",
                "soap": {
                    "matched": {"maker": "B&M", "scent": "Seville"},
                    "enriched": {"sample_type": "sample"},
                },
            },
        ]

        result = aggregate_all(records, "2025-08", debug=False)

        # Check metadata structure
        assert "meta" in result, "Result should include metadata"
        meta = result["meta"]
        assert "month" in meta, "Metadata should include month"
        assert meta["month"] == "2025-08", "Month should match input"
        
        # Check data structure
        assert "data" in result, "Result should include data section"
        data = result["data"]
        assert "soap_samples" in data, "Data should include soap_samples"
        
        # Check soap sample entry structure
        soap_samples = data["soap_samples"]
        assert len(soap_samples) == 1, "Should have one soap sample entry"
        
        entry = soap_samples[0]
        required_fields = ["position", "name", "shaves", "unique_users"]
        for field in required_fields:
            assert field in entry, f"Soap sample entry should have {field} field"
        
        # Check that position is 1-based
        assert entry["position"] == 1, "Position should be 1-based ranking"
