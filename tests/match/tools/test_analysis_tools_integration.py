#!/usr/bin/env python3
"""Integration tests for analysis tools."""

import json
from io import StringIO
import sys
from unittest.mock import patch
import collections

from sotd.match.tools.utils.analysis_base import AnalysisTool
from sotd.match.tools.utils.cli_utils import BaseAnalysisCLI
from sotd.cli_utils.base_parser import BaseCLIParser
from sotd.match.tools.analyzers.unmatched_analyzer import UnmatchedAnalyzer
from sotd.match.tools.analyzers.field_analyzer import FieldAnalyzer
from sotd.match.tools.legacy.analyze_matched_enhanced import EnhancedAnalyzer


class TestAnalysisToolsIntegration:
    """Integration tests for refactored analysis tools."""

    def test_unmatched_analyzer_integration(self, tmp_path):
        """Test UnmatchedAnalyzer integration with real data."""
        # Create test data
        out_dir = tmp_path / "data" / "matched"
        out_dir.mkdir(parents=True)

        test_data = {
            "data": [
                {"razor": "Unknown Razor"},
                {"razor": {"original": "Another Unknown", "matched": None}},
                {"razor": {"original": "Known Razor", "matched": {"brand": "Known"}}},
            ]
        }

        test_file = out_dir / "2025-01.json"
        test_file.write_text(json.dumps(test_data))

        # Test analyzer
        analyzer = UnmatchedAnalyzer()
        args = type(
            "Args",
            (),
            {
                "month": "2025-01",
                "out_dir": str(tmp_path / "data"),
                "field": "razor",
                "limit": 10,
                "debug": False,
            },
        )()

        # Capture output
        output = StringIO()
        sys_stdout = sys.stdout
        try:
            sys.stdout = output
            analyzer.run(args)
        finally:
            sys.stdout = sys_stdout

        result = output.getvalue()

        # Verify results
        assert "Unknown Razor" in result
        assert "Another Unknown" in result
        assert "Known Razor" not in result  # Should not appear as unmatched

    def test_field_analyzer_integration(self, tmp_path):
        """Test FieldAnalyzer integration with real data."""
        # Create test data
        out_dir = tmp_path / "data" / "matched"
        out_dir.mkdir(parents=True)

        test_data = {
            "data": [
                {
                    "razor": {
                        "original": "Gillette Tech",
                        "matched": {"manufacturer": "Gillette", "model": "Tech"},
                        "match_type": "exact",
                    }
                },
                {
                    "razor": {
                        "original": "Merkur 34C",
                        "matched": {"manufacturer": "Merkur", "model": "34C"},
                        "match_type": "exact",
                    }
                },
            ]
        }

        test_file = out_dir / "2025-01.json"
        test_file.write_text(json.dumps(test_data))

        # Test analyzer
        analyzer = FieldAnalyzer()
        args = type(
            "Args",
            (),
            {
                "month": "2025-01",
                "out_dir": str(tmp_path / "data"),
                "field": "razor",
                "limit": 10,
                "debug": False,
                "pattern": None,
                "show_details": False,
                "show_patterns": False,
                "show_opportunities": False,
                "show_mismatches": False,
                "show_examples": None,
                "mismatch_limit": 20,
                "example_limit": 15,
            },
        )()

        # Capture output
        output = StringIO()
        sys_stdout = sys.stdout
        try:
            sys.stdout = output
            analyzer.run(args)
        finally:
            sys.stdout = sys_stdout

        result = output.getvalue()

        # Verify results
        assert "Gillette Tech" in result
        assert "Merkur 34C" in result

    def test_analysis_base_functionality(self):
        """Test AnalysisTool base class functionality."""

        class TestAnalyzer(AnalysisTool):
            def get_parser(self):
                parser = BaseCLIParser(description="Test analyzer")
                BaseAnalysisCLI.add_common_arguments(parser)
                return parser

            def run(self, args):
                pass

        analyzer = TestAnalyzer()
        parser = analyzer.get_parser()

        # Test that parser has expected arguments
        assert any(arg.dest == "limit" for arg in parser._actions)
        assert any(arg.dest == "field" for arg in parser._actions)

    def test_base_analysis_cli_functionality(self):
        """Test BaseAnalysisCLI functionality."""
        parser = BaseCLIParser(description="Test parser")
        BaseAnalysisCLI.add_common_arguments(parser)
        BaseAnalysisCLI.add_pattern_arguments(parser)

        # Test that parser has expected arguments
        assert any(arg.dest == "limit" for arg in parser._actions)
        assert any(arg.dest == "field" for arg in parser._actions)
        assert any(arg.dest == "pattern" for arg in parser._actions)
        assert any(arg.dest == "show_details" for arg in parser._actions)

    def test_enhanced_analyzer_integration(self, tmp_path):
        """Test EnhancedAnalyzer integration."""
        # Create test data
        out_dir = tmp_path / "data" / "matched"
        out_dir.mkdir(parents=True)

        test_data = {
            "data": [
                {
                    "brush": {
                        "original": "Simpson Chubby 2",
                        "matched": {"brand": "Simpson", "model": "Chubby 2", "confidence": 0.9},
                        "match_type": "exact",
                    }
                }
            ]
        }

        test_file = out_dir / "2025-01.json"
        test_file.write_text(json.dumps(test_data))

        # Test analyzer
        analyzer = EnhancedAnalyzer()
        args = type(
            "Args",
            (),
            {
                "month": "2025-01",
                "out_dir": str(tmp_path / "data"),
                "field": "brush",
                "show_details": True,
                "debug": False,
                "show_examples": None,
                "example_limit": 15,
                "show_patterns": False,
                "show_opportunities": False,
                "show_mismatches": False,
                "mismatch_limit": 20,
            },
        )()

        # Mock the data loading functions to avoid complex dependencies
        with patch(
            "sotd.match.tools.legacy.analyze_matched_enhanced.load_analysis_data"
        ) as mock_load:
            mock_load.return_value = test_data["data"]

            with patch(
                "sotd.match.tools.legacy.analyze_matched_enhanced.extract_field_data"
            ) as mock_extract:
                mock_extract.return_value = ([test_data["data"][0]["brush"]], ["exact"], [0.9])

                with patch(
                    "sotd.match.tools.legacy.analyze_matched_enhanced.calculate_summary_statistics"
                ) as mock_stats:
                    mock_stats.return_value = {
                        "total_matches": 1,
                        "match_type_counts": collections.Counter({"exact": 1}),
                        "avg_confidence": 0.9,
                        "potential_mismatches": 0,
                    }

                    # Capture output
                    output = StringIO()
                    sys_stdout = sys.stdout
                    try:
                        sys.stdout = output
                        analyzer.run(args)
                    finally:
                        sys.stdout = sys_stdout

                    # Verify that the analyzer ran without errors
                    assert mock_load.called
                    assert mock_extract.called
                    assert mock_stats.called
