#!/usr/bin/env python3
"""Integration tests for deltas parameter in enhanced table syntax.

This test suite validates that the deltas parameter works correctly through the entire pipeline:
1. Template parsing with deltas:true
2. Parameter passing to TableGenerator
3. Delta column generation
4. Final markdown output
"""

from sotd.report.monthly_generator import MonthlyReportGenerator
from sotd.report.table_generators.table_generator import TableGenerator


class TestDeltasIntegration:
    """Test deltas parameter integration through the full pipeline."""

    def test_deltas_parameter_end_to_end(self, tmp_path):
        """Test that deltas:true parameter works end-to-end through template processing."""

        # Create a test template with deltas parameter
        template_content = """# Test Software Report

## Soap Brands with Deltas
{{tables.soap-brands|deltas:true}}

## Soap Brands without Deltas (for comparison)
{{tables.soap-brands}}
"""
        template_file = tmp_path / "software.md"
        template_file.write_text(template_content)

        # Create test data with comparison data for deltas
        metadata = {"month": "2025-06", "total_shaves": 1000}
        data = {
            "soap_brands": [
                {"rank": 1, "shaves": 100, "unique_users": 50, "brand": "Brand A"},
                {"rank": 2, "shaves": 80, "unique_users": 40, "brand": "Brand B"},
                {"rank": 3, "shaves": 60, "unique_users": 30, "brand": "Brand C"},
            ]
        }

        # Create comparison data for previous month
        comparison_data = {
            "2025-05": {
                "soap_brands": [
                    {"rank": 1, "shaves": 90, "unique_users": 45, "brand": "Brand A"},
                    {"rank": 2, "shaves": 85, "unique_users": 42, "brand": "Brand B"},
                    {"rank": 3, "shaves": 70, "unique_users": 35, "brand": "Brand C"},
                ]
            }
        }

        # Create monthly generator and table generator
        monthly_gen = MonthlyReportGenerator(
            "software", metadata, data, comparison_data=comparison_data
        )
        table_generator = TableGenerator(data, comparison_data)

        # Process the template
        result = monthly_gen._process_enhanced_table_syntax(template_content, table_generator)

        # Verify that the enhanced table was processed
        assert "{{tables.soap-brands|deltas:true}}" in result

        # Verify that delta columns are present in the output
        table_content = result["{{tables.soap-brands|deltas:true}}"]
        assert "Δ vs May 2025" in table_content

        # Verify that the basic table was also processed (should not have deltas)
        basic_table_content = result.get("{{tables.soap-brands}}", "")
        if basic_table_content:  # Basic table might not be processed if no basic syntax
            assert "Δ vs May 2025" not in basic_table_content

    def test_deltas_parameter_with_other_parameters(self, tmp_path):
        """Test that deltas parameter works with other parameters like ranks and rows."""

        template_content = """# Test Report

## Limited Soap Brands with Deltas
{{tables.soap-brands|ranks:2|deltas:true}}

## Limited Soap Brands without Deltas
{{tables.soap-brands|ranks:2}}
"""
        template_file = tmp_path / "software.md"
        template_file.write_text(template_content)

        metadata = {"month": "2025-06", "total_shaves": 1000}
        data = {
            "soap_brands": [
                {"rank": 1, "shaves": 100, "unique_users": 50, "brand": "Brand A"},
                {"rank": 2, "shaves": 80, "unique_users": 40, "brand": "Brand B"},
                {"rank": 3, "shaves": 60, "unique_users": 30, "brand": "Brand C"},
            ]
        }

        comparison_data = {
            "2025-05": {
                "soap_brands": [
                    {"rank": 1, "shaves": 90, "unique_users": 45, "brand": "Brand A"},
                    {"rank": 2, "shaves": 85, "unique_users": 42, "brand": "Brand B"},
                ]
            }
        }

        monthly_gen = MonthlyReportGenerator(
            "software", metadata, data, comparison_data=comparison_data
        )
        table_generator = TableGenerator(data, comparison_data)

        # Process the template
        result = monthly_gen._process_enhanced_table_syntax(template_content, table_generator)

        # Verify that the enhanced table with deltas was processed
        assert "{{tables.soap-brands|ranks:2|deltas:true}}" in result

        # Verify deltas table has delta columns
        deltas_table = result["{{tables.soap-brands|ranks:2|deltas:true}}"]
        assert "Δ vs May 2025" in deltas_table

        # The basic table without deltas is not processed by enhanced syntax method
        # It would be processed by the basic table generation in the main flow

    def test_deltas_parameter_boolean_conversion(self):
        """Test that deltas:true gets converted to boolean True correctly."""

        # Test the parameter parsing and conversion logic directly
        from sotd.report.table_parameter_parser import TableParameterParser

        parser = TableParameterParser()
        table_name, parameters = parser.parse_placeholder("{{tables.soap-brands|deltas:true}}")

        assert table_name == "soap-brands"
        assert parameters["deltas"] == "true"

        # Test boolean conversion
        deltas_bool = parameters.get("deltas") == "true"
        assert deltas_bool is True

        # Test false case
        table_name, parameters = parser.parse_placeholder("{{tables.soap-brands|deltas:false}}")
        deltas_bool = parameters.get("deltas") == "true"
        assert deltas_bool is False

    def test_deltas_parameter_missing_comparison_data(self, tmp_path):
        """Test that deltas parameter works gracefully when no comparison data is available."""

        template_content = """# Test Report

## Soap Brands with Deltas (No Comparison Data)
{{tables.soap-brands|deltas:true}}
"""
        template_file = tmp_path / "software.md"
        template_file.write_text(template_content)

        metadata = {"month": "2025-06", "total_shaves": 1000}
        data = {
            "soap_brands": [
                {"rank": 1, "shaves": 100, "unique_users": 50, "brand": "Brand A"},
                {"rank": 2, "shaves": 80, "unique_users": 40, "brand": "Brand B"},
            ]
        }

        # No comparison data
        monthly_gen = MonthlyReportGenerator("software", metadata, data)
        table_generator = TableGenerator(data)

        # Process the template - should not crash
        result = monthly_gen._process_enhanced_table_syntax(template_content, table_generator)

        # Should still process the table, but with n/a deltas
        assert "{{tables.soap-brands|deltas:true}}" in result
        table_content = result["{{tables.soap-brands|deltas:true}}"]

        # Should contain n/a for deltas when no comparison data
        assert "n/a" in table_content
