"""Tests for correct matches validation tool."""

import pytest
from unittest.mock import Mock
from sotd.match.tools.validate_correct_matches import ValidateCorrectMatches
import yaml


class TestValidateCorrectMatches:
    """Test the ValidateCorrectMatches class."""

    def test_validator_can_be_instantiated(self):
        """Test that validator class can be instantiated."""
        validator = ValidateCorrectMatches()
        assert validator is not None
        assert hasattr(validator, "console")
        assert hasattr(validator, "catalog_cache")
        assert hasattr(validator, "correct_matches")

    def test_validator_with_custom_console(self):
        """Test validator instantiation with custom console."""
        mock_console = Mock()
        validator = ValidateCorrectMatches(console=mock_console)
        assert validator.console == mock_console

    def test_get_parser_returns_parser(self):
        """Test that get_parser returns a parser object."""
        validator = ValidateCorrectMatches()
        parser = validator.get_parser()
        assert parser is not None
        assert hasattr(parser, "add_argument")

    def test_parser_has_required_arguments(self):
        """Test that parser has all required CLI arguments."""
        validator = ValidateCorrectMatches()
        parser = validator.get_parser()

        # Get all argument names
        args = [action.dest for action in parser._actions]

        # Check for required arguments
        assert "field" in args
        assert "all_fields" in args
        assert "verbose" in args
        assert "dry_run" in args

    def test_run_method_exists(self):
        """Test that run method exists and is callable."""
        validator = ValidateCorrectMatches()
        assert hasattr(validator, "run")
        assert callable(validator.run)

    def test_run_method_accepts_args(self):
        """Test that run method accepts args parameter."""
        validator = ValidateCorrectMatches()
        mock_args = Mock()

        # Should not raise an exception (implementation will come later)
        try:
            validator.run(mock_args)
        except NotImplementedError:
            # Expected for now since we haven't implemented it yet
            pass
        except Exception as e:
            # Any other exception is unexpected
            pytest.fail(f"Unexpected exception: {e}")

    def test_imports_work_correctly(self):
        """Test that all required imports work correctly."""
        # This test ensures that the module can be imported without errors
        from sotd.match.tools.validate_correct_matches import ValidateCorrectMatches

        assert ValidateCorrectMatches is not None


class TestCLIInterface:
    """Test CLI interface functionality."""

    def test_cli_help_works(self):
        """Test that CLI help can be displayed."""
        validator = ValidateCorrectMatches()
        parser = validator.get_parser()

        # Should not raise an exception
        help_text = parser.format_help()
        assert help_text is not None
        assert len(help_text) > 0

    def test_cli_parses_field_flag(self):
        validator = ValidateCorrectMatches()
        parser = validator.get_parser()
        args = parser.parse_args(["--field", "razor"])
        assert args.field == "razor"
        assert not args.all_fields

    def test_cli_parses_all_fields_flag(self):
        validator = ValidateCorrectMatches()
        parser = validator.get_parser()
        args = parser.parse_args(["--all-fields"])
        assert args.all_fields
        assert args.field is None

    def test_cli_parses_verbose_flag(self):
        validator = ValidateCorrectMatches()
        parser = validator.get_parser()
        args = parser.parse_args(["--verbose"])
        assert args.verbose

    def test_cli_parses_dry_run_flag(self):
        validator = ValidateCorrectMatches()
        parser = validator.get_parser()
        args = parser.parse_args(["--dry-run"])
        assert args.dry_run

    def test_run_returns_issues_for_mismatched_entry(self, tmp_path):
        # Setup a correct_matches.yaml with a mismatched entry
        correct_matches_data = {"razor": {"Dairi": {"Kamisori": ["Dairi - Kamisori $KAMISORI"]}}}
        catalog_data = {"Other": {"Kamisori": {"patterns": ["kamisori"], "format": "Straight"}}}
        correct_matches_file = tmp_path / "correct_matches.yaml"
        catalog_file = tmp_path / "razors.yaml"
        with correct_matches_file.open("w") as f:
            yaml.dump(correct_matches_data, f)
        with catalog_file.open("w") as f:
            yaml.dump(catalog_data, f)
        # Patch the data directory
        validator = ValidateCorrectMatches()
        validator._data_dir = tmp_path  # type: ignore

        class Args:
            field = "razor"
            all_fields = False
            verbose = False
            dry_run = False

        results = validator.run(Args())
        assert "razor" in results
        issues = results["razor"]
        assert any(issue["issue_type"] == "mismatched_entry" for issue in issues)

    def test_run_returns_no_issues_for_valid_entry(self, tmp_path):
        # Setup a correct_matches.yaml with a valid entry
        correct_matches_data = {"razor": {"Other": {"Kamisori": ["Dairi - Kamisori $KAMISORI"]}}}
        catalog_data = {"Other": {"Kamisori": {"patterns": ["kamisori"], "format": "Straight"}}}
        correct_matches_file = tmp_path / "correct_matches.yaml"
        catalog_file = tmp_path / "razors.yaml"
        with correct_matches_file.open("w") as f:
            yaml.dump(correct_matches_data, f)
        with catalog_file.open("w") as f:
            yaml.dump(catalog_data, f)
        # Patch the data directory
        validator = ValidateCorrectMatches()
        validator._data_dir = tmp_path  # type: ignore

        class Args:
            field = "razor"
            all_fields = False
            verbose = False
            dry_run = False

        results = validator.run(Args())
        assert "razor" in results
        issues = results["razor"]
        assert len(issues) == 0

    def test_main_dry_run_exits_zero(self):
        validator = ValidateCorrectMatches()
        exit_code = validator.main(["--dry-run"])
        assert exit_code == 0

    def test_main_returns_zero_for_no_issues(self, tmp_path):
        # Setup a correct_matches.yaml with a valid entry
        correct_matches_data = {"razor": {"Other": {"Kamisori": ["Dairi - Kamisori $KAMISORI"]}}}
        catalog_data = {"Other": {"Kamisori": {"patterns": ["kamisori"], "format": "Straight"}}}
        correct_matches_file = tmp_path / "correct_matches.yaml"
        catalog_file = tmp_path / "razors.yaml"
        with correct_matches_file.open("w") as f:
            yaml.dump(correct_matches_data, f)
        with catalog_file.open("w") as f:
            yaml.dump(catalog_data, f)
        validator = ValidateCorrectMatches()
        validator._data_dir = tmp_path  # type: ignore
        exit_code = validator.main(["--field", "razor"])
        assert exit_code == 0

    def test_main_returns_one_for_issues(self, tmp_path):
        # Setup a correct_matches.yaml with a mismatched entry
        correct_matches_data = {"razor": {"Dairi": {"Kamisori": ["Dairi - Kamisori $KAMISORI"]}}}
        catalog_data = {"Other": {"Kamisori": {"patterns": ["kamisori"], "format": "Straight"}}}
        correct_matches_file = tmp_path / "correct_matches.yaml"
        catalog_file = tmp_path / "razors.yaml"
        with correct_matches_file.open("w") as f:
            yaml.dump(correct_matches_data, f)
        with catalog_file.open("w") as f:
            yaml.dump(catalog_data, f)
        validator = ValidateCorrectMatches()
        validator._data_dir = tmp_path  # type: ignore
        exit_code = validator.main(["--field", "razor"])
        assert exit_code == 1


class TestCatalogLoading:
    """Test catalog loading infrastructure in ValidateCorrectMatches."""

    def setup_method(self):
        self.validator = ValidateCorrectMatches()

    def test_load_catalog_success(self, tmp_path):
        """Test successful catalog loading."""
        field = "razor"
        catalog_data = {"Test Brand": {"Test Model": {"patterns": ["test"]}}}
        catalog_file = tmp_path / f"{field}s.yaml"

        with catalog_file.open("w") as f:
            yaml.dump(catalog_data, f)

        # Patch the data directory to tmp_path
        self.validator._data_dir = tmp_path  # type: ignore
        loaded = self.validator._load_catalog(field)  # type: ignore
        assert loaded == catalog_data

    def test_load_catalog_missing_file(self, tmp_path):
        """Test catalog loading with missing file."""
        # Patch the data directory to tmp_path
        self.validator._data_dir = tmp_path  # type: ignore
        with pytest.raises(FileNotFoundError):
            self.validator._load_catalog("razor")  # type: ignore

    def test_load_catalog_invalid_yaml(self, tmp_path):
        """Test catalog loading with invalid YAML."""
        catalog_file = tmp_path / "razors.yaml"

        with catalog_file.open("w") as f:
            f.write("invalid: yaml: content: [")

        # Patch the data directory to tmp_path
        self.validator._data_dir = tmp_path  # type: ignore
        with pytest.raises(ValueError):
            self.validator._load_catalog("razor")  # type: ignore

    def test_load_catalog_invalid_structure(self, tmp_path):
        """Test catalog loading with invalid structure."""
        catalog_data = "not a dict"
        catalog_file = tmp_path / "razors.yaml"

        with catalog_file.open("w") as f:
            yaml.dump(catalog_data, f)

        # Patch the data directory to tmp_path
        self.validator._data_dir = tmp_path  # type: ignore
        with pytest.raises(ValueError):
            self.validator._load_catalog("razor")  # type: ignore

    def test_load_catalog_unknown_field(self, tmp_path):
        """Test catalog loading with unknown field."""
        # Patch the data directory to tmp_path
        self.validator._data_dir = tmp_path  # type: ignore
        with pytest.raises(ValueError):
            self.validator._load_catalog("unknown_field")  # type: ignore

    def test_load_catalog_with_real_data(self, tmp_path):
        """Test catalog loading with realistic data."""
        catalog_data = {
            "Karve": {
                "Christopher Bradley": {"patterns": ["karve.*cb", "cb.*karve"], "format": "DE"}
            }
        }
        catalog_file = tmp_path / "razors.yaml"

        with catalog_file.open("w") as f:
            yaml.dump(catalog_data, f)

        # Patch the data directory to tmp_path
        self.validator._data_dir = tmp_path  # type: ignore
        loaded = self.validator._load_catalog("razor")  # type: ignore
        assert loaded == catalog_data


class TestCorrectMatchesLoading:
    """Test correct matches loading infrastructure in ValidateCorrectMatches."""

    def setup_method(self):
        self.validator = ValidateCorrectMatches()

    def test_load_correct_matches_success(self, tmp_path):
        """Test successful correct matches loading."""
        correct_matches_data = {
            "razor": {"Karve": {"Christopher Bradley": ["Karve CB", "CB Karve"]}}
        }
        correct_matches_file = tmp_path / "correct_matches.yaml"

        with correct_matches_file.open("w") as f:
            yaml.dump(correct_matches_data, f)

        # Patch the data directory to tmp_path
        self.validator._data_dir = tmp_path  # type: ignore
        loaded = self.validator._load_correct_matches()  # type: ignore
        assert loaded == correct_matches_data

    def test_load_correct_matches_missing_file(self, tmp_path):
        """Test correct matches loading with missing file."""
        # Patch the data directory to tmp_path
        self.validator._data_dir = tmp_path  # type: ignore
        with pytest.raises(FileNotFoundError):
            self.validator._load_correct_matches()  # type: ignore

    def test_load_correct_matches_invalid_yaml(self, tmp_path):
        """Test correct matches loading with invalid YAML."""
        correct_matches_file = tmp_path / "correct_matches.yaml"

        with correct_matches_file.open("w") as f:
            f.write("invalid: yaml: content: [")

        # Patch the data directory to tmp_path
        self.validator._data_dir = tmp_path  # type: ignore
        with pytest.raises(ValueError):
            self.validator._load_correct_matches()  # type: ignore

    def test_load_correct_matches_invalid_structure(self, tmp_path):
        """Test correct matches loading with invalid structure."""
        correct_matches_data = "not a dict"
        correct_matches_file = tmp_path / "correct_matches.yaml"

        with correct_matches_file.open("w") as f:
            yaml.dump(correct_matches_data, f)

        # Patch the data directory to tmp_path
        self.validator._data_dir = tmp_path  # type: ignore
        with pytest.raises(ValueError):
            self.validator._load_correct_matches()  # type: ignore

    def test_load_correct_matches_empty_file(self, tmp_path):
        """Test correct matches loading with empty file."""
        correct_matches_file = tmp_path / "correct_matches.yaml"
        correct_matches_file.touch()

        # Patch the data directory to tmp_path
        self.validator._data_dir = tmp_path  # type: ignore
        with pytest.raises(ValueError):
            self.validator._load_correct_matches()  # type: ignore

    def test_load_correct_matches_with_real_data(self, tmp_path):
        """Test correct matches loading with realistic data."""
        correct_matches_data = {
            "razor": {"Karve": {"Christopher Bradley": ["Karve CB", "CB Karve"]}},
            "brush": {"Simpson": {"Chubby 2": ["Simpson Chubby 2", "Chubby 2"]}},
        }
        correct_matches_file = tmp_path / "correct_matches.yaml"

        with correct_matches_file.open("w") as f:
            yaml.dump(correct_matches_data, f)

        # Patch the data directory to tmp_path
        self.validator._data_dir = tmp_path  # type: ignore
        loaded = self.validator._load_correct_matches()  # type: ignore
        assert loaded == correct_matches_data


class TestBasicValidationMethods:
    """Test basic validation methods in ValidateCorrectMatches."""

    def setup_method(self):
        self.validator = ValidateCorrectMatches()

    def test_check_brand_model_exists_success(self, tmp_path):
        """Test successful brand/model existence check."""
        catalog_data = {"Karve": {"Christopher Bradley": {"patterns": ["karve.*cb"]}}}
        catalog_file = tmp_path / "razors.yaml"

        with catalog_file.open("w") as f:
            yaml.dump(catalog_data, f)

        # Patch the data directory to tmp_path
        self.validator._data_dir = tmp_path  # type: ignore
        assert self.validator._check_brand_model_exists(
            "razor", "Karve", "Christopher Bradley"
        )  # type: ignore
        assert (
            self.validator._check_brand_model_exists("razor", "Karve", "NonExistent") is False
        )  # type: ignore

    def test_check_missing_entries(self, tmp_path):
        """Test missing entries detection."""
        correct_matches_data = {"razor": {"Karve": {"Christopher Bradley": ["Karve CB"]}}}
        catalog_data = {"Karve": {"Christopher Bradley": {"patterns": ["karve.*cb"]}}}

        correct_matches_file = tmp_path / "correct_matches.yaml"
        catalog_file = tmp_path / "razors.yaml"

        with correct_matches_file.open("w") as f:
            yaml.dump(correct_matches_data, f)
        with catalog_file.open("w") as f:
            yaml.dump(catalog_data, f)

        # Patch the data directory to tmp_path
        self.validator._data_dir = tmp_path  # type: ignore
        missing_entries = self.validator._check_missing_entries("razor")  # type: ignore
        assert len(missing_entries) == 0

    def test_check_field_changes(self, tmp_path):
        """Test field changes detection."""
        correct_matches_data = {"razor": {"Karve": {"Christopher Bradley": ["Karve CB"]}}}
        catalog_data = {
            "Karve": {"Christopher Bradley": {"patterns": ["karve.*cb"], "format": "DE"}}
        }

        correct_matches_file = tmp_path / "correct_matches.yaml"
        catalog_file = tmp_path / "razors.yaml"

        with correct_matches_file.open("w") as f:
            yaml.dump(correct_matches_data, f)
        with catalog_file.open("w") as f:
            yaml.dump(catalog_data, f)

        # Patch the data directory to tmp_path
        self.validator._data_dir = tmp_path  # type: ignore
        changes = self.validator._check_field_changes("razor")  # type: ignore
        assert len(changes) == 0

    def test_validate_correct_matches_structure(self, tmp_path):
        """Test correct matches structure validation."""
        correct_matches_data = {
            "razor": {"Karve": {"Christopher Bradley": ["Karve CB"]}},
            "brush": {"Simpson": {"Chubby 2": ["Simpson Chubby 2"]}},
        }

        correct_matches_file = tmp_path / "correct_matches.yaml"

        with correct_matches_file.open("w") as f:
            yaml.dump(correct_matches_data, f)

        # Patch the data directory to tmp_path
        self.validator._data_dir = tmp_path  # type: ignore
        issues = self.validator._validate_correct_matches_structure("razor")  # type: ignore
        assert len(issues) == 0

    def test_validate_field_with_empty_data(self, tmp_path):
        """Test field validation with empty data."""
        # Patch the data directory to tmp_path
        self.validator._data_dir = tmp_path  # type: ignore
        issues = self.validator._validate_field("razor")  # type: ignore
        assert len(issues) == 0

    def test_validate_field_with_valid_data(self, tmp_path):
        """Test field validation with valid data."""
        correct_matches_data = {"razor": {"Karve": {"Christopher Bradley": ["Karve CB"]}}}
        catalog_data = {"Karve": {"Christopher Bradley": {"patterns": ["karve.*cb"]}}}

        correct_matches_file = tmp_path / "correct_matches.yaml"
        catalog_file = tmp_path / "razors.yaml"

        with correct_matches_file.open("w") as f:
            yaml.dump(correct_matches_data, f)
        with catalog_file.open("w") as f:
            yaml.dump(catalog_data, f)

        # Patch the data directory to tmp_path
        self.validator._data_dir = tmp_path  # type: ignore
        issues = self.validator._validate_field("razor")  # type: ignore
        assert len(issues) == 0

    def test_check_pattern_conflicts(self, tmp_path):
        """Test pattern conflicts detection."""
        correct_matches_data = {"razor": {"Karve": {"Christopher Bradley": ["Karve CB"]}}}
        catalog_data = {"Karve": {"Christopher Bradley": {"patterns": ["karve.*cb"]}}}

        correct_matches_file = tmp_path / "correct_matches.yaml"
        catalog_file = tmp_path / "razors.yaml"

        with correct_matches_file.open("w") as f:
            yaml.dump(correct_matches_data, f)
        with catalog_file.open("w") as f:
            yaml.dump(catalog_data, f)

        # Patch the data directory to tmp_path
        self.validator._data_dir = tmp_path  # type: ignore
        conflicts = self.validator._check_pattern_conflicts("razor")  # type: ignore
        assert len(conflicts) == 0

    def test_suggest_better_matches(self, tmp_path):
        """Test better matches suggestion."""
        correct_matches_data = {"razor": {"Karve": {"Christopher Bradley": ["Karve CB"]}}}
        catalog_data = {"Karve": {"Christopher Bradley": {"patterns": ["karve.*cb"]}}}

        correct_matches_file = tmp_path / "correct_matches.yaml"
        catalog_file = tmp_path / "razors.yaml"

        with correct_matches_file.open("w") as f:
            yaml.dump(correct_matches_data, f)
        with catalog_file.open("w") as f:
            yaml.dump(catalog_data, f)

        # Patch the data directory to tmp_path
        self.validator._data_dir = tmp_path  # type: ignore
        suggestions = self.validator._suggest_better_matches("razor")  # type: ignore
        assert len(suggestions) == 0

    def test_check_pattern_conflicts_with_conflicts(self, tmp_path):
        """Test pattern conflicts detection with actual conflicts."""
        correct_matches_data = {
            "razor": {
                "Karve": {"Christopher Bradley": ["Karve CB"]},
                "Other": {"Model": ["Karve CB"]},  # Same pattern, different brand
            }
        }
        catalog_data = {
            "Karve": {"Christopher Bradley": {"patterns": ["karve.*cb"]}},
            "Other": {"Model": {"patterns": ["karve.*cb"]}},  # Conflicting pattern
        }

        correct_matches_file = tmp_path / "correct_matches.yaml"
        catalog_file = tmp_path / "razors.yaml"

        with correct_matches_file.open("w") as f:
            yaml.dump(correct_matches_data, f)
        with catalog_file.open("w") as f:
            yaml.dump(catalog_data, f)

        # Patch the data directory to tmp_path
        self.validator._data_dir = tmp_path  # type: ignore

        # Load the correct_matches data first
        self.validator.correct_matches = self.validator._load_correct_matches()

        conflicts = self.validator._check_pattern_conflicts("razor")  # type: ignore
        assert len(conflicts) > 0


class TestIssueClassificationAndPrioritization:
    """Test issue classification and prioritization methods."""

    def setup_method(self):
        self.validator = ValidateCorrectMatches()

    def test_classify_issues(self):
        """Test issue classification."""
        issues = [
            {"issue_type": "mismatched_entry", "severity": "high"},
            {"issue_type": "missing_entry", "severity": "medium"},
            {"issue_type": "pattern_conflict", "severity": "low"},
        ]

        classified = self.validator._classify_issues(issues)  # type: ignore
        assert "mismatched_entry" in classified
        assert "missing_entry" in classified
        assert "pattern_conflict" in classified
        assert len(classified["mismatched_entry"]) == 1
        assert len(classified["missing_entry"]) == 1
        assert len(classified["pattern_conflict"]) == 1

    def test_score_issues(self):
        """Test issue scoring."""
        issues = [
            {"issue_type": "mismatched_entry", "severity": "high"},
            {"issue_type": "missing_entry", "severity": "medium"},
            {"issue_type": "pattern_conflict", "severity": "low"},
        ]

        scored = self.validator._score_issues(issues)  # type: ignore
        assert len(scored) == 3
        assert all("score" in issue for issue in scored)

    def test_group_similar_issues(self):
        """Test similar issues grouping."""
        issues = [
            {"issue_type": "mismatched_entry", "brand": "Karve", "model": "CB"},
            {"issue_type": "mismatched_entry", "brand": "Karve", "model": "Overlander"},
            {"issue_type": "missing_entry", "brand": "Simpson", "model": "Chubby 2"},
        ]

        grouped = self.validator._group_similar_issues(issues)  # type: ignore
        assert "Karve" in grouped
        assert "Simpson" in grouped
        assert len(grouped["Karve"]) == 2
        assert len(grouped["Simpson"]) == 1

    def test_suggest_action_for_issue_type(self):
        """Test action suggestion for issue types."""
        actions = {
            "mismatched_entry": self.validator._suggest_action_for_issue_type(
                "mismatched_entry"
            ),  # type: ignore
            "missing_entry": self.validator._suggest_action_for_issue_type(
                "missing_entry"
            ),  # type: ignore
            "pattern_conflict": self.validator._suggest_action_for_issue_type(
                "pattern_conflict"
            ),  # type: ignore
        }

        assert all(action for action in actions.values())
        assert "update" in actions["mismatched_entry"].lower()
        assert "add" in actions["missing_entry"].lower()
        assert "resolve" in actions["pattern_conflict"].lower()

    def test_prioritize_issues(self):
        """Test issue prioritization."""
        issues = [
            {"issue_type": "mismatched_entry", "severity": "high", "score": 10},
            {"issue_type": "missing_entry", "severity": "medium", "score": 5},
            {"issue_type": "pattern_conflict", "severity": "low", "score": 1},
        ]

        prioritized = self.validator._prioritize_issues(issues)  # type: ignore
        assert len(prioritized) == 3
        # Should be sorted by score (descending)
        assert prioritized[0]["score"] >= prioritized[1]["score"]
        assert prioritized[1]["score"] >= prioritized[2]["score"]

    def test_generate_summary_statistics(self):
        """Test summary statistics generation."""
        issues = [
            {"issue_type": "mismatched_entry", "severity": "high"},
            {"issue_type": "missing_entry", "severity": "medium"},
            {"issue_type": "pattern_conflict", "severity": "low"},
        ]

        summary = self.validator._generate_summary_statistics(issues)  # type: ignore
        assert "total_issues" in summary
        assert "by_type" in summary
        assert "by_severity" in summary
        assert summary["total_issues"] == 3

    def test_create_issues_table(self):
        """Test issues table creation."""
        issues = [
            {"issue_type": "mismatched_entry", "severity": "high", "brand": "Karve"},
            {"issue_type": "missing_entry", "severity": "medium", "brand": "Simpson"},
        ]

        table = self.validator._create_issues_table(issues)  # type: ignore
        assert table is not None
        assert hasattr(table, "row_count")

    def test_get_issue_color(self):
        """Test issue color assignment."""
        colors = {
            "high": self.validator._get_issue_color({"severity": "high"}),  # type: ignore
            "medium": self.validator._get_issue_color({"severity": "medium"}),  # type: ignore
            "low": self.validator._get_issue_color({"severity": "low"}),  # type: ignore
        }

        assert all(color for color in colors.values())
        assert colors["high"] != colors["medium"]
        assert colors["medium"] != colors["low"]

    def test_generate_field_breakdown(self):
        """Test field breakdown generation."""
        issues = [
            {"issue_type": "mismatched_entry", "field": "razor", "brand": "Karve"},
            {"issue_type": "missing_entry", "field": "brush", "brand": "Simpson"},
        ]

        breakdown = self.validator._generate_field_breakdown(issues)  # type: ignore
        assert "razor" in breakdown
        assert "brush" in breakdown
        assert breakdown["razor"]["total"] == 1
        assert breakdown["brush"]["total"] == 1

    def test_display_console_report(self):
        """Test console report display."""
        issues = [
            {"issue_type": "mismatched_entry", "severity": "high", "brand": "Karve"},
            {"issue_type": "missing_entry", "severity": "medium", "brand": "Simpson"},
        ]

        summary = {"total_issues": 2, "by_type": {}, "by_severity": {}}

        # Should not raise an exception
        self.validator._display_console_report(issues, summary)  # type: ignore
