"""Test to identify where rank corruption occurs in the report generation pipeline.

This test runs the full pipeline with rank tracing enabled to pinpoint exactly
where ranks get corrupted during processing.
"""

import pytest
from pathlib import Path
import json

from sotd.report.utils.rank_tracer import enable_rank_tracing, trace_ranks
from sotd.report.table_generators.cross_product_tables import HighestUseCountPerBladeTableGenerator
from sotd.report.enhanced_table_generator import EnhancedTableGenerator


class TestRankingCorruptionDetection:
    """Test to detect and identify rank corruption points."""

    def test_full_pipeline_rank_tracing(self):
        """Test the full pipeline with rank tracing to identify corruption points."""
        # Enable rank tracing
        enable_rank_tracing()
        
        # Check if real data file exists
        real_data_path = Path("data/aggregated/2025-06.json")
        if not real_data_path.exists():
            pytest.skip("Real 2025-06 aggregated data not available")

        # Load real data
        with open(real_data_path) as f:
            real_data = json.load(f)

        # Verify real data has the expected structure
        assert "data" in real_data, "Real data should have 'data' key"
        assert (
            "highest_use_count_per_blade" in real_data["data"]
        ), "Real data should have 'highest_use_count_per_blade'"

        blade_data = real_data["data"]["highest_use_count_per_blade"]
        assert len(blade_data) > 0, "Real data should have blade entries"

        # Test 1: Trace ranks in original aggregated data
        print("\n=== STEP 1: Original Aggregated Data ===")
        trace_ranks("original_aggregated_data", real_data, data_key="data")

        # Test 2: Trace ranks through table generator
        print("\n=== STEP 2: Table Generator Processing ===")
        table_generator = HighestUseCountPerBladeTableGenerator(real_data, debug=True)
        table_data = table_generator.get_table_data()

        # Test 3: Trace ranks through enhanced table processing
        print("\n=== STEP 3: Enhanced Table Processing ===")
        enhanced_generator = EnhancedTableGenerator()
        enhanced_data = enhanced_generator.generate_table(
            "highest-use-count-per-blade", table_data, {"rows": 30}
        )

        # Test 4: Verify final output
        print("\n=== STEP 4: Final Output Verification ===")
        assert len(enhanced_data) > 0, "Enhanced data should not be empty"
        
        # Check for rank corruption patterns
        ranks = [item.get("rank", "N/A") for item in enhanced_data]
        unique_ranks = set(ranks)
        
        print(f"Final data has {len(enhanced_data)} items")
        print(f"Unique ranks: {sorted(unique_ranks)}")
        print(f"First 10 ranks: {ranks[:10]}")
        
        # Check for specific corruption patterns
        if len(unique_ranks) == 1 and "N/A" not in unique_ranks:
            pytest.fail(
                f"RANK CORRUPTION DETECTED: All ranks are {list(unique_ranks)[0]}. "
                "This indicates the bug where all ranks show as the same value."
            )
        
        if "N/A" in ranks:
            pytest.fail(
                f"RANK CORRUPTION DETECTED: {ranks.count('N/A')}/{len(ranks)} items have no rank. "
                "This indicates rank data is being lost during processing."
            )
        
        # Check if ranks are sequential
        numeric_ranks = [r for r in ranks if isinstance(r, (int, float)) and r != "N/A"]
        if numeric_ranks and numeric_ranks != sorted(numeric_ranks):
            pytest.fail(
                f"RANK CORRUPTION DETECTED: Ranks are not sequential. "
                f"Expected sequential, got: {numeric_ranks[:10]}..."
            )
        
        print("✅ No rank corruption detected - all ranks preserved correctly")

    def test_rank_corruption_patterns(self):
        """Test specific rank corruption patterns to ensure detection works."""
        enable_rank_tracing()
        
        # Test data with known corruption patterns
        test_data = {
            "data": {
                "highest_use_count_per_blade": [
                    {"rank": 1, "user": "user1", "blade": "Test Blade 1", "format": "DE", "uses": 15},
                    {"rank": 1, "user": "user2", "blade": "Test Blade 2", "format": "DE", "uses": 12},  # Corrupted rank
                    {"rank": 1, "user": "user3", "blade": "Test Blade 3", "format": "DE", "uses": 10},  # Corrupted rank
                ]
            }
        }
        
        # This should detect the rank corruption
        table_generator = HighestUseCountPerBladeTableGenerator(test_data, debug=True)
        table_data = table_generator.get_table_data()
        
        # Verify the corruption is detected
        ranks = [item.get("rank") for item in table_data]
        assert len(set(ranks)) == 1, "Test data should have all ranks corrupted to same value"
        assert ranks[0] == 1, "Test data should have all ranks corrupted to 1"
        
        print("✅ Rank corruption pattern correctly detected in test data")
