"""End-to-end tests for enhanced report templating system.

This test suite validates the complete enhanced templating workflow:
1. Template parsing with enhanced syntax
2. Parameter validation and processing
3. Data filtering and limiting
4. Report generation with enhanced tables
5. Backward compatibility with existing templates
"""

from sotd.report.process import generate_report_content


class TestEnhancedReportGeneration:
    """Test complete enhanced report generation workflow."""

    def test_basic_table_generation_backward_compatibility(self, tmp_path):
        """Test that basic table generation still works unchanged."""
        # Create a simple template with basic syntax
        template_content = """# Test Report

## Razors
{{tables.razors}}

## Blades  
{{tables.blades}}
"""
        template_file = tmp_path / "hardware.md"
        template_file.write_text(template_content)

        # Sample data with required rank column
        metadata = {"month": "2025-01", "total_shaves": 100}
        data = {
            "razors": [
                {"rank": 1, "name": "Test Razor 1", "shaves": 10, "unique_users": 5},
                {"rank": 2, "name": "Test Razor 2", "shaves": 8, "unique_users": 3},
            ],
            "blades": [
                {"rank": 1, "name": "Test Blade 1", "shaves": 15, "unique_users": 8},
                {"rank": 2, "name": "Test Blade 2", "shaves": 12, "unique_users": 6},
            ],
        }

        # Generate report
        report_content = generate_report_content(
            "hardware", metadata, data, template_path=str(tmp_path), debug=False
        )

        # Verify basic functionality still works
        assert "# Test Report" in report_content
        assert "## Razors" in report_content
        assert "## Blades" in report_content
        # Tables should be generated (content will vary based on actual generators)
        assert "Test Razor" in report_content or "|" in report_content

    def test_enhanced_table_with_shaves_limit(self, tmp_path):
        """Test enhanced table with shaves limit parameter."""
        template_content = """# Test Report

## Top Razors (5+ shaves)
{{tables.razors|shaves:5}}

## Top Blades (10+ shaves)
{{tables.blades|shaves:10}}
"""
        template_file = tmp_path / "hardware.md"
        template_file.write_text(template_content)

        # Sample data with varying shave counts and required rank column
        metadata = {"month": "2025-01", "total_shaves": 100}
        data = {
            "razors": [
                {"rank": 1, "name": "High Use Razor", "shaves": 15, "unique_users": 8},
                {"rank": 2, "name": "Medium Use Razor", "shaves": 8, "unique_users": 4},
                {"rank": 3, "name": "Low Use Razor", "shaves": 3, "unique_users": 2},
            ],
            "blades": [
                {"rank": 1, "name": "High Use Blade", "shaves": 20, "unique_users": 10},
                {"rank": 2, "name": "Medium Use Blade", "shaves": 12, "unique_users": 6},
                {"rank": 3, "name": "Low Use Blade", "shaves": 5, "unique_users": 3},
            ],
        }

        # Generate report
        report_content = generate_report_content(
            "hardware", metadata, data, template_path=str(tmp_path), debug=False
        )

        # Verify enhanced functionality works
        assert "# Test Report" in report_content
        assert "## Top Razors (5+ shaves)" in report_content
        assert "## Top Blades (10+ shaves)" in report_content

        # Verify that low-use items are filtered out
        assert "High Use Razor" in report_content
        assert "Medium Use Razor" in report_content
        assert "Low Use Razor" not in report_content  # Below 5 shaves threshold

        assert "High Use Blade" in report_content
        assert "Medium Use Blade" in report_content
        assert "Low Use Blade" not in report_content  # Below 10 shaves threshold

    def test_enhanced_table_with_rows_limit(self, tmp_path):
        """Test enhanced table with rows limit parameter."""
        template_content = """# Test Report

## Top 2 Razors
{{tables.razors|rows:2}}

## Top 1 Blade
{{tables.blades|rows:1}}
"""
        template_file = tmp_path / "hardware.md"
        template_file.write_text(template_content)

        # Sample data
        metadata = {"month": "2025-01", "total_shaves": 100}
        data = {
            "razors": [
                {"rank": 1, "name": "Razor 1", "shaves": 20, "unique_users": 10},
                {"rank": 2, "name": "Razor 2", "shaves": 15, "unique_users": 8},
                {"rank": 3, "name": "Razor 3", "shaves": 10, "unique_users": 5},
            ],
            "blades": [
                {"rank": 1, "name": "Blade 1", "shaves": 25, "unique_users": 12},
                {"rank": 2, "name": "Blade 2", "shaves": 18, "unique_users": 9},
                {"rank": 3, "name": "Blade 3", "shaves": 12, "unique_users": 6},
            ],
        }

        # Generate report
        report_content = generate_report_content(
            "hardware", metadata, data, template_path=str(tmp_path), debug=False
        )

        # Verify row limits are applied
        assert "# Test Report" in report_content
        assert "## Top 2 Razors" in report_content
        assert "## Top 1 Blade" in report_content

        # Count table rows (should be limited)
        lines = report_content.split("\n")
        razor_section = False
        blade_section = False
        razor_rows = 0
        blade_rows = 0

        for line in lines:
            if "## Top 2 Razors" in line:
                razor_section = True
                blade_section = False
            elif "## Top 1 Blade" in line:
                razor_section = False
                blade_section = True
            elif razor_section and "|" in line and "---" not in line:
                # Skip header row (contains "Rank" and "Razor"/"Blade")
                if "Rank" not in line:
                    razor_rows += 1
            elif blade_section and "|" in line and "---" not in line:
                # Skip header row (contains "Rank" and "Razor"/"Blade")
                if "Rank" not in line:
                    blade_rows += 1

        # Should have limited data rows (excluding header row)
        assert razor_rows <= 2
        assert blade_rows <= 1

    def test_enhanced_table_with_combined_limits(self, tmp_path):
        """Test enhanced table with multiple parameter types."""
        template_content = """# Test Report

## Top Razors (5+ shaves, max 2 rows)
{{tables.razors|shaves:5|rows:2}}

## Top Blades (10+ shaves, max 1 row)
{{tables.blades|shaves:10|rows:1}}
"""
        template_file = tmp_path / "hardware.md"
        template_file.write_text(template_content)

        # Sample data
        metadata = {"month": "2025-01", "total_shaves": 100}
        data = {
            "razors": [
                {"rank": 1, "name": "High Use Razor", "shaves": 15, "unique_users": 8},
                {"rank": 2, "name": "Medium Use Razor", "shaves": 8, "unique_users": 4},
                {"rank": 3, "name": "Low Use Razor", "shaves": 3, "unique_users": 2},
            ],
            "blades": [
                {"rank": 1, "name": "High Use Blade", "shaves": 20, "unique_users": 10},
                {"rank": 2, "name": "Medium Use Blade", "shaves": 12, "unique_users": 6},
                {"rank": 3, "name": "Low Use Blade", "shaves": 5, "unique_users": 3},
            ],
        }

        # Generate report
        report_content = generate_report_content(
            "hardware", metadata, data, template_path=str(tmp_path), debug=False
        )

        # Verify combined limits work
        assert "# Test Report" in report_content
        assert "## Top Razors (5+ shaves, max 2 rows)" in report_content
        assert "## Top Blades (10+ shaves, max 1 row)" in report_content

        # Verify filtering and row limits are both applied
        assert "High Use Razor" in report_content
        assert "Medium Use Razor" in report_content
        assert "Low Use Razor" not in report_content  # Below shaves threshold

        assert "High Use Blade" in report_content
        assert "Medium Use Blade" not in report_content  # Row limit exceeded
        assert "Low Use Blade" not in report_content  # Below shaves threshold

    def test_enhanced_table_with_unique_users_limit(self, tmp_path):
        """Test enhanced table with unique_users limit parameter."""
        template_content = """# Test Report

## Popular Razors (3+ unique users)
{{tables.razors|unique_users:3}}

## Popular Blades (5+ unique users)
{{tables.blades|unique_users:5}}
"""
        template_file = tmp_path / "hardware.md"
        template_file.write_text(template_content)

        # Sample data
        metadata = {"month": "2025-01", "total_shaves": 100}
        data = {
            "razors": [
                {"rank": 1, "name": "Popular Razor", "shaves": 20, "unique_users": 8},
                {"rank": 2, "name": "Medium Razor", "shaves": 15, "unique_users": 4},
                {"rank": 3, "name": "Unpopular Razor", "shaves": 10, "unique_users": 2},
            ],
            "blades": [
                {"rank": 1, "name": "Popular Blade", "shaves": 25, "unique_users": 12},
                {"rank": 2, "name": "Medium Blade", "shaves": 18, "unique_users": 6},
                {"rank": 3, "name": "Unpopular Blade", "shaves": 12, "unique_users": 3},
            ],
        }

        # Generate report
        report_content = generate_report_content(
            "hardware", metadata, data, template_path=str(tmp_path), debug=False
        )

        # Verify unique_users filtering works
        assert "# Test Report" in report_content
        assert "## Popular Razors (3+ unique users)" in report_content
        assert "## Popular Blades (5+ unique users)" in report_content

        # Verify filtering by unique_users
        assert "Popular Razor" in report_content
        assert "Medium Razor" in report_content
        assert "Unpopular Razor" not in report_content  # Below unique_users threshold

        assert "Popular Blade" in report_content
        assert "Medium Blade" in report_content
        assert "Unpopular Blade" not in report_content  # Below unique_users threshold

    def test_enhanced_table_with_ranks_limit(self, tmp_path):
        """Test enhanced table with ranks limit parameter."""
        template_content = """# Test Report

## Top 2 Rank Razors
{{tables.razors|ranks:2}}

## Top 1 Rank Blade
{{tables.blades|ranks:1}}
"""
        template_file = tmp_path / "hardware.md"
        template_file.write_text(template_content)

        # Sample data with ranks
        metadata = {"month": "2025-01", "total_shaves": 100}
        data = {
            "razors": [
                {"rank": 1, "name": "Top Razor", "shaves": 20, "unique_users": 10},
                {"rank": 2, "name": "Second Razor", "shaves": 15, "unique_users": 8},
                {"rank": 3, "name": "Third Razor", "shaves": 10, "unique_users": 5},
            ],
            "blades": [
                {"rank": 1, "name": "Top Blade", "shaves": 25, "unique_users": 12},
                {"rank": 2, "name": "Second Blade", "shaves": 18, "unique_users": 9},
                {"rank": 3, "name": "Third Blade", "shaves": 12, "unique_users": 6},
            ],
        }

        # Generate report
        report_content = generate_report_content(
            "hardware", metadata, data, template_path=str(tmp_path), debug=False
        )

        # Verify rank limits are applied
        assert "# Test Report" in report_content
        assert "## Top 2 Rank Razors" in report_content
        assert "## Top 1 Rank Blade" in report_content

        # Verify only top ranks are included
        assert "Top Razor" in report_content
        assert "Second Razor" in report_content
        assert "Third Razor" not in report_content  # Rank 3 exceeds limit

        assert "Top Blade" in report_content
        assert "Second Blade" not in report_content  # Rank 2 exceeds limit
        assert "Third Blade" not in report_content  # Rank 3 exceeds limit

    def test_enhanced_table_mixed_with_basic_tables(self, tmp_path):
        """Test mixing enhanced and basic table syntax in the same template."""
        template_content = """# Test Report

## Basic Razors Table
{{tables.razors}}

## Enhanced Blades Table (5+ shaves)
{{tables.blades|shaves:5}}

## Basic Brushes Table
{{tables.brushes}}
"""
        template_file = tmp_path / "hardware.md"
        template_file.write_text(template_content)

        # Sample data
        metadata = {"month": "2025-01", "total_shaves": 100}
        data = {
            "razors": [
                {"name": "Razor 1", "shaves": 10, "unique_users": 5},
                {"name": "Razor 2", "shaves": 8, "unique_users": 4},
            ],
            "blades": [
                {"name": "High Use Blade", "shaves": 15, "unique_users": 8},
                {"name": "Medium Use Blade", "shaves": 8, "unique_users": 4},
                {"name": "Low Use Blade", "shaves": 3, "unique_users": 2},
            ],
            "brushes": [
                {"name": "Brush 1", "shaves": 12, "unique_users": 6},
                {"name": "Brush 2", "shaves": 9, "unique_users": 4},
            ],
        }

        # Generate report
        report_content = generate_report_content(
            "hardware", metadata, data, template_path=str(tmp_path), debug=False
        )

        # Verify both enhanced and basic tables work
        assert "# Test Report" in report_content
        assert "## Basic Razors Table" in report_content
        assert "## Enhanced Blades Table (5+ shaves)" in report_content
        assert "## Basic Brushes Table" in report_content

        # Verify enhanced filtering works
        assert "High Use Blade" in report_content
        assert "Medium Use Blade" in report_content
        assert "Low Use Blade" not in report_content  # Below shaves threshold

        # Verify basic tables still work
        assert "Razor 1" in report_content or "|" in report_content
        assert "Brush 1" in report_content or "|" in report_content

    def test_enhanced_table_error_handling(self, tmp_path):
        """Test error handling for invalid enhanced table syntax."""
        template_content = """# Test Report

## Invalid Syntax (should fall back to basic)
{{tables.razors|invalid_param:value}}

## Valid Enhanced Table
{{tables.blades|shaves:5}}

## Basic Table
{{tables.brushes}}
"""
        template_file = tmp_path / "hardware.md"
        template_file.write_text(template_content)

        # Sample data
        metadata = {"month": "2025-01", "total_shaves": 100}
        data = {
            "razors": [{"name": "Razor 1", "shaves": 10, "unique_users": 5}],
            "blades": [
                {"name": "High Use Blade", "shaves": 15, "unique_users": 8},
                {"name": "Low Use Blade", "shaves": 3, "unique_users": 2},
            ],
            "brushes": [{"name": "Brush 1", "shaves": 12, "unique_users": 6}],
        }

        # Generate report - should not crash
        report_content = generate_report_content(
            "hardware", metadata, data, template_path=str(tmp_path), debug=False
        )

        # Verify error handling works gracefully
        assert "# Test Report" in report_content
        assert "## Invalid Syntax (should fall back to basic)" in report_content
        assert "## Valid Enhanced Table" in report_content
        assert "## Basic Table" in report_content

        # Invalid syntax should fall back to basic table generation
        # Valid enhanced syntax should work
        assert "High Use Blade" in report_content
        assert "Low Use Blade" not in report_content  # Below shaves threshold

        # Basic tables should still work
        assert "Razor 1" in report_content or "|" in report_content
        assert "Brush 1" in report_content or "|" in report_content

    def test_enhanced_table_empty_data_handling(self, tmp_path):
        """Test enhanced table handling with empty or minimal data."""
        template_content = """# Test Report

## Razors with High Threshold (should be empty)
{{tables.razors|shaves:100}}

## Blades with Row Limit (should respect limit)
{{tables.blades|rows:5}}
"""
        template_file = tmp_path / "hardware.md"
        template_file.write_text(template_content)

        # Sample data with low values
        metadata = {"month": "2025-01", "total_shaves": 100}
        data = {
            "razors": [{"name": "Low Use Razor", "shaves": 5, "unique_users": 2}],
            "blades": [
                {"name": "Blade 1", "shaves": 10, "unique_users": 5},
                {"name": "Blade 2", "shaves": 8, "unique_users": 4},
            ],
        }

        # Generate report
        report_content = generate_report_content(
            "hardware", metadata, data, template_path=str(tmp_path), debug=False
        )

        # Verify empty data handling
        assert "# Test Report" in report_content
        assert "## Razors with High Threshold (should be empty)" in report_content
        assert "## Blades with Row Limit (should respect limit)" in report_content

        # High threshold should result in no razors
        assert "Low Use Razor" not in report_content

        # Row limit should be respected for blades
        assert "Blade 1" in report_content
        assert "Blade 2" in report_content

    def test_enhanced_table_tie_handling(self, tmp_path):
        """Test enhanced table tie handling with row limits."""
        template_content = """# Test Report

## Top 2 Razors (respecting ties)
{{tables.razors|rows:2}}
"""
        template_file = tmp_path / "hardware.md"
        template_file.write_text(template_content)

        # Sample data with ties
        metadata = {"month": "2025-01", "total_shaves": 100}
        data = {
            "razors": [
                {"rank": 1, "name": "Top Razor", "shaves": 20, "unique_users": 10},
                {"rank": 2, "name": "Tied Razor A", "shaves": 15, "unique_users": 8},
                {"rank": 2, "name": "Tied Razor B", "shaves": 15, "unique_users": 8},
                {"rank": 4, "name": "Fourth Razor", "shaves": 10, "unique_users": 5},
            ]
        }

        # Generate report
        report_content = generate_report_content(
            "hardware", metadata, data, template_path=str(tmp_path), debug=False
        )

        # Verify tie handling works
        assert "# Test Report" in report_content
        assert "## Top 2 Razors (respecting ties)" in report_content

        # Should include top rank and tied items (respecting ties)
        assert "Top Razor" in report_content
        assert "Tied Razor A" in report_content
        assert "Tied Razor B" in report_content
        assert "Fourth Razor" not in report_content  # Exceeds row limit

    def test_enhanced_table_software_tables(self, tmp_path):
        """Test enhanced table functionality with software tables."""
        template_content = """# Software Report

## Popular Soaps (10+ shaves)
{{tables.soaps|shaves:10}}

## Top Soap Makers (5+ unique users)
{{tables.soap-makers|unique_users:5}}

## Brand Diversity (max 3 rows)
{{tables.brand-diversity|rows:3}}
"""
        template_file = tmp_path / "software.md"
        template_file.write_text(template_content)

        # Sample software data
        metadata = {"month": "2025-01", "total_shaves": 100}
        data = {
            "soaps": [
                {"rank": 1, "name": "Popular Soap", "shaves": 20, "unique_users": 10},
                {"rank": 2, "name": "Medium Soap", "shaves": 8, "unique_users": 4},
                {"rank": 3, "name": "Unpopular Soap", "shaves": 3, "unique_users": 2},
            ],
            "soap_makers": [
                {"rank": 1, "brand": "Popular Brand", "shaves": 25, "unique_users": 8},
                {"rank": 2, "brand": "Medium Brand", "shaves": 15, "unique_users": 6},
                {"rank": 3, "brand": "Small Brand", "shaves": 10, "unique_users": 3},
            ],
            "brand_diversity": [
                {"rank": 1, "brand": "Brand A", "unique_soaps": 5},
                {"rank": 2, "brand": "Brand B", "unique_soaps": 4},
                {"rank": 3, "brand": "Brand C", "unique_soaps": 3},
                {"rank": 4, "brand": "Brand D", "unique_soaps": 2},
            ],
        }

        # Generate report
        report_content = generate_report_content(
            "software", metadata, data, template_path=str(tmp_path), debug=False
        )

        # Verify software table enhanced functionality
        assert "# Software Report" in report_content
        assert "## Popular Soaps (10+ shaves)" in report_content
        assert "## Top Soap Makers (5+ unique users)" in report_content
        assert "## Brand Diversity (max 3 rows)" in report_content

        # Verify filtering works
        assert "Popular Soap" in report_content
        assert "Medium Soap" not in report_content  # Below shaves threshold
        assert "Unpopular Soap" not in report_content  # Below shaves threshold

        # Verify unique_users filtering
        assert "Popular Brand" in report_content
        assert "Medium Brand" in report_content
        assert "Small Brand" not in report_content  # Below unique_users threshold

        # Verify row limits - check Brand Diversity section specifically
        brand_diversity_section = ""
        if "## Brand Diversity" in report_content:
            brand_diversity_section = report_content.split("## Brand Diversity")[1].split("##")[0]
        assert "Brand A" in brand_diversity_section
        assert "Brand B" in brand_diversity_section
        assert "Brand C" in brand_diversity_section
        assert "Brand D" not in brand_diversity_section  # Exceeds row limit

    def test_enhanced_table_user_tables(self, tmp_path):
        """Test enhanced table functionality with user tables."""
        template_content = """# User Report

## Top Shavers (20+ shaves, max 2 rows)
{{tables.users|shaves:20|rows:2}}
"""
        template_file = tmp_path / "hardware.md"
        template_file.write_text(template_content)

        # Sample user data with required rank column
        metadata = {"month": "2025-01", "total_shaves": 100}
        data = {
            "users": [
                {"rank": 1, "user": "user1", "shaves": 31, "missed_days": 0, "position": 1},
                {"rank": 2, "user": "user2", "shaves": 28, "missed_days": 3, "position": 2},
                {"rank": 3, "user": "user3", "shaves": 25, "missed_days": 6, "position": 3},
                {"rank": 4, "user": "user4", "shaves": 15, "missed_days": 16, "position": 4},
            ]
        }

        # Generate report
        report_content = generate_report_content(
            "hardware", metadata, data, template_path=str(tmp_path), debug=False
        )

        # Verify user table enhanced functionality
        assert "# User Report" in report_content
        assert "## Top Shavers (20+ shaves, max 2 rows)" in report_content

        # Verify filtering and row limits work
        assert "user1" in report_content
        assert "user2" in report_content
        assert "user3" not in report_content  # Below shaves threshold (20)
        assert "user4" not in report_content  # Below shaves threshold (20)

    def test_enhanced_table_specialized_tables(self, tmp_path):
        """Test enhanced table functionality with specialized tables."""
        template_content = """# Specialized Report

## Blackbird Plates (5+ shaves)
{{tables.blackbird-plates|shaves:5}}

## Game Changer Plates (max 2 rows)
{{tables.game-changer-plates|rows:2}}
"""
        template_file = tmp_path / "hardware.md"
        template_file.write_text(template_content)

        # Sample specialized data
        metadata = {"month": "2025-01", "total_shaves": 100}
        data = {
            "blackbird_plates": [
                {"rank": 1, "plate": "OC", "shaves": 10, "unique_users": 5},
                {"rank": 2, "plate": "SB", "shaves": 3, "unique_users": 2},
            ],
            "game_changer_plates": [
                {"rank": 1, "gap": "0.84-P", "shaves": 15, "unique_users": 8},
                {"rank": 2, "gap": "0.68-P", "shaves": 12, "unique_users": 6},
                {"rank": 3, "gap": "0.76-P", "shaves": 10, "unique_users": 5},
            ],
        }

        # Generate report
        report_content = generate_report_content(
            "hardware", metadata, data, template_path=str(tmp_path), debug=False
        )

        # Verify specialized table enhanced functionality
        assert "# Specialized Report" in report_content
        assert "## Blackbird Plates (5+ shaves)" in report_content
        assert "## Game Changer Plates (max 2 rows)" in report_content

        # Verify filtering works
        assert "OC" in report_content
        assert "SB" not in report_content  # Below shaves threshold

        # Verify row limits work
        assert "0.84-P" in report_content
        assert "0.68-P" in report_content
        assert "0.76-P" not in report_content  # Exceeds row limit

    def test_enhanced_table_cross_product_tables(self, tmp_path):
        """Test enhanced table functionality with cross-product tables."""
        template_content = """# Cross-Product Report

## Razor-Blade Combinations (10+ shaves)
{{tables.razor-blade-combinations|shaves:10}}

## Highest Use Count Per Blade (max 3 rows)
{{tables.highest-use-count-per-blade|rows:3}}
"""
        template_file = tmp_path / "hardware.md"
        template_file.write_text(template_content)

        # Sample cross-product data
        metadata = {"month": "2025-01", "total_shaves": 100}
        data = {
            "razor_blade_combinations": [
                {"rank": 1, "name": "Razor A + Blade X", "shaves": 15, "unique_users": 8},
                {"rank": 2, "name": "Razor B + Blade Y", "shaves": 8, "unique_users": 4},
                {"rank": 3, "name": "Razor C + Blade Z", "shaves": 3, "unique_users": 2},
            ],
            "highest_use_count_per_blade": [
                {"rank": 1, "blade": "Blade A", "uses": 20, "user": "User1"},
                {"rank": 2, "blade": "Blade B", "uses": 18, "user": "User2"},
                {"rank": 3, "blade": "Blade C", "uses": 15, "user": "User3"},
                {"rank": 4, "blade": "Blade D", "uses": 12, "user": "User4"},
            ],
        }

        # Generate report
        report_content = generate_report_content(
            "hardware", metadata, data, template_path=str(tmp_path), debug=False
        )

        # Verify cross-product table enhanced functionality
        assert "# Cross-Product Report" in report_content
        assert "## Razor-Blade Combinations (10+ shaves)" in report_content
        assert "## Highest Use Count Per Blade (max 3 rows)" in report_content

        # Verify filtering works (10+ shaves threshold)
        assert "Razor A + Blade X" in report_content  # 15 shaves - above threshold
        assert "Razor B + Blade Y" not in report_content  # 8 shaves - below threshold
        assert "Razor C + Blade Z" not in report_content  # 3 shaves - below threshold

        # Verify row limits work
        assert "Blade A" in report_content
        assert "Blade B" in report_content
        assert "Blade C" in report_content
        assert "Blade D" not in report_content  # Exceeds row limit

    def test_enhanced_table_debug_mode(self, tmp_path):
        """Test enhanced table functionality with debug mode enabled."""
        template_content = """# Debug Report

## Debug Razors (5+ shaves)
{{tables.razors|shaves:5}}
"""
        template_file = tmp_path / "hardware.md"
        template_file.write_text(template_content)

        # Sample data
        metadata = {"month": "2025-01", "total_shaves": 100}
        data = {
            "razors": [
                {"name": "High Use Razor", "shaves": 15, "unique_users": 8},
                {"name": "Low Use Razor", "shaves": 3, "unique_users": 2},
            ]
        }

        # Generate report with debug enabled
        report_content = generate_report_content(
            "hardware", metadata, data, template_path=str(tmp_path), debug=True
        )

        # Verify debug mode works with enhanced tables
        assert "# Debug Report" in report_content
        assert "## Debug Razors (5+ shaves)" in report_content

        # Verify enhanced functionality still works in debug mode
        assert "High Use Razor" in report_content
        assert "Low Use Razor" not in report_content  # Below shaves threshold

    def test_enhanced_table_performance_with_large_data(self, tmp_path):
        """Test enhanced table performance with larger datasets."""
        template_content = """# Performance Report

## Large Razors Table (10+ shaves, max 50 rows)
{{tables.razors|shaves:10|rows:50}}
"""
        template_file = tmp_path / "hardware.md"
        template_file.write_text(template_content)

        # Generate larger dataset
        metadata = {"month": "2025-01", "total_shaves": 1000}
        data = {
            "razors": [
                {
                    "rank": i + 1,
                    "name": f"Razor {i}, rank: 1",
                    "shaves": 20 - (i % 10),  # Varying shave counts
                    "unique_users": 10 - (i % 5),  # Varying user counts
                }
                for i in range(100)  # 100 razors
            ]
        }

        # Generate report - should complete in reasonable time
        import time

        start_time = time.time()

        report_content = generate_report_content(
            "hardware", metadata, data, template_path=str(tmp_path), debug=False
        )

        end_time = time.time()
        generation_time = end_time - start_time

        # Verify performance is acceptable (< 5 seconds for 100 items)
        expected_msg = f"Report generation took {generation_time:.2f}s, expected < 5s"
        assert generation_time < 5.0, expected_msg

        # Verify enhanced functionality works with large data
        assert "# Performance Report" in report_content
        assert "## Large Razors Table (10+ shaves, max 50 rows)" in report_content

        # Should have filtered and limited data
        assert "Razor 0" in report_content  # High shave count
        assert "Razor 99" not in report_content  # Low shave count (below threshold)

    def test_enhanced_table_edge_cases(self, tmp_path):
        """Test enhanced table functionality with edge cases."""
        template_content = """# Edge Case Report

## Single Item Table (should work)
{{tables.razors|shaves:1}}

## Empty Result Table (high threshold)
{{tables.blades|shaves:1000}}

## Zero Limit Table (should be empty)
{{tables.brushes|rows:0}}
"""
        template_file = tmp_path / "hardware.md"
        template_file.write_text(template_content)

        # Sample data with edge cases
        metadata = {"month": "2025-01", "total_shaves": 100}
        data = {
            "razors": [{"name": "Single Razor", "shaves": 5, "unique_users": 2}],
            "blades": [{"name": "Low Use Blade", "shaves": 3, "unique_users": 1}],
            "brushes": [{"name": "Test Brush", "shaves": 10, "unique_users": 5}],
        }

        # Generate report
        report_content = generate_report_content(
            "hardware", metadata, data, template_path=str(tmp_path), debug=False
        )

        # Verify edge case handling
        assert "# Edge Case Report" in report_content
        assert "## Single Item Table (should work)" in report_content
        assert "## Empty Result Table (high threshold)" in report_content
        assert "## Zero Limit Table (should be empty)" in report_content

        # Single item should work
        assert "Single Razor" in report_content

        # High threshold should result in empty table
        assert "Low Use Blade" not in report_content

        # Zero limit should result in empty table
        assert "Test Brush" not in report_content

    def test_enhanced_table_parameter_combinations(self, tmp_path):
        """Test various parameter combinations and their interactions."""
        template_content = """# Parameter Test Report

## Test 1: Shaves + Rows
{{tables.razors|shaves:5|rows:3}}

## Test 2: Unique Users + Ranks
{{tables.blades|unique_users:3|ranks:2}}

## Test 3: Single Numeric Limit + Other Parameters
{{tables.brushes|shaves:10|rows:5|ranks:3}}
"""
        template_file = tmp_path / "hardware.md"
        template_file.write_text(template_content)

        # Sample data
        metadata = {"month": "2025-01", "total_shaves": 100}
        data = {
            "razors": [
                {"rank": 1, "name": "Razor 1", "shaves": 20, "unique_users": 10},
                {"rank": 2, "name": "Razor 2", "shaves": 15, "unique_users": 8},
                {"rank": 3, "name": "Razor 3", "shaves": 10, "unique_users": 5},
                {"rank": 4, "name": "Razor 4", "shaves": 3, "unique_users": 2},
            ],
            "blades": [
                {"rank": 1, "name": "Blade 1", "shaves": 18, "unique_users": 8},
                {"rank": 2, "name": "Blade 2", "shaves": 15, "unique_users": 6},
                {"rank": 3, "name": "Blade 3", "shaves": 12, "unique_users": 3},
                {"rank": 4, "name": "Blade 4", "shaves": 8, "unique_users": 2},
            ],
            "brushes": [
                {"rank": 1, "name": "Brush 1", "shaves": 25, "unique_users": 8},
                {"rank": 2, "name": "Brush 2", "shaves": 20, "unique_users": 6},
                {"rank": 3, "name": "Brush 3", "shaves": 15, "unique_users": 4},
                {"rank": 4, "name": "Brush 4", "shaves": 8, "unique_users": 2},
            ],
        }

        # Generate report
        report_content = generate_report_content(
            "hardware", metadata, data, template_path=str(tmp_path), debug=False
        )

        # Verify parameter combinations work
        assert "# Parameter Test Report" in report_content
        assert "## Test 1: Shaves + Rows" in report_content
        assert "## Test 2: Unique Users + Ranks" in report_content
        assert "## Test 3: Single Numeric Limit + Other Parameters" in report_content

        # Test 1: Should filter by shaves and limit rows
        assert "Razor 1" in report_content
        assert "Razor 2" in report_content
        assert "Razor 3" in report_content
        assert "Razor 4" not in report_content  # Below shaves threshold

        # Test 2: Should filter by unique_users and limit ranks
        assert "Blade 1" in report_content
        assert "Blade 2" in report_content
        assert "Blade 3" not in report_content  # Below unique_users threshold
        assert "Blade 4" not in report_content  # Below unique_users threshold

        # Test 3: Should apply single numeric limit + other parameters
        assert "Brush 1" in report_content
        assert "Brush 2" in report_content
        assert "Brush 3" in report_content
        assert "Brush 4" not in report_content  # Below shaves threshold
