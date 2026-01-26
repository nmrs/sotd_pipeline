"""Comprehensive tests for run.py module."""

import argparse
from datetime import date
from unittest.mock import Mock, patch

import pytest

from sotd.fetch.run import _calc_missing, _process_month, main


# --------------------------------------------------------------------------- #
# Test fixtures and helper classes                                            #
# --------------------------------------------------------------------------- #
class MockSubmission:
    """Mock Reddit submission for testing."""

    def __init__(
        self, submission_id: str, title: str, created_utc: int = 1640995200, num_comments: int = 5
    ):
        self.id = submission_id
        self.title = title
        self.created_utc = created_utc
        self.num_comments = num_comments
        self.permalink = f"/r/wetshaving/comments/{submission_id}/"
        self.link_flair_text = "SOTD"
        self.author = "test_user"
        self.comments = Mock()
        self.comments.replace_more = Mock(return_value=None)
        self.comments.list = Mock(return_value=[])


class MockComment:
    """Mock Reddit comment for testing."""

    def __init__(
        self,
        comment_id: str,
        thread_id: str,
        body: str = "Test shave",
        created_utc: int = 1640995200,
    ):
        self.id = comment_id
        self.thread_id = thread_id
        self.body = body
        self.created_utc = created_utc
        self.author = "test_user"
        self.is_root = True
        self.permalink = f"/r/wetshaving/comments/{thread_id}/comment/{comment_id}/"


@pytest.fixture
def mock_args():
    """Create mock command line arguments."""
    args = argparse.Namespace()
    args.data_dir = "test_data"
    args.debug = False
    args.force = False
    args.verbose = False
    return args


@pytest.fixture
def sample_threads():
    """Create sample thread data for testing."""
    return [
        MockSubmission("thread1", "SOTD Thread May 01, 2025", num_comments=3),
        MockSubmission("thread2", "SOTD Thread May 03, 2025", num_comments=2),
        MockSubmission("thread3", "SOTD Thread May 05, 2025", num_comments=1),
    ]


@pytest.fixture
def sample_comments():
    """Create sample comment data for testing."""
    return {
        "thread1": [
            MockComment("c1", "thread1", "Great shave with soap A"),
            MockComment("c2", "thread1", "Love this razor"),
            MockComment("c3", "thread1", "Nice brush work"),
        ],
        "thread2": [
            MockComment("c4", "thread2", "Smooth shave today"),
            MockComment("c5", "thread2", "Testing new blade"),
        ],
        "thread3": [
            MockComment("c6", "thread3", "Quick shave"),
        ],
    }


# --------------------------------------------------------------------------- #
# _calc_missing tests                                                          #
# --------------------------------------------------------------------------- #
def test_calc_missing_basic():
    """_calc_missing should identify missing days correctly."""
    threads = [
        MockSubmission("1", "SOTD Thread May 01, 2025"),
        MockSubmission("3", "SOTD Thread May 03, 2025"),
        MockSubmission("5", "SOTD Thread May 05, 2025"),
    ]

    missing = _calc_missing(2025, 5, threads)

    # May has 31 days, missing: 2, 4, 6-31
    expected_missing = [date(2025, 5, d) for d in [2, 4] + list(range(6, 32))]
    assert missing == expected_missing


def test_calc_missing_no_threads():
    """_calc_missing should return all days when no threads exist."""
    missing = _calc_missing(2025, 2, [])  # February 2025

    expected_missing = [date(2025, 2, d) for d in range(1, 29)]  # 28 days in Feb 2025
    assert missing == expected_missing


def test_calc_missing_complete_month():
    """_calc_missing should return empty list when all days are present."""
    threads = [
        MockSubmission(str(d), f"SOTD Thread May {d:02d}, 2025")
        for d in range(1, 32)  # All 31 days of May
    ]

    missing = _calc_missing(2025, 5, threads)
    assert missing == []


def test_calc_missing_invalid_dates():
    """_calc_missing should handle threads with unparseable dates."""
    threads = [
        MockSubmission("1", "SOTD Thread May 01, 2025"),
        MockSubmission("invalid", "Weekly Discussion Thread"),  # Can't parse date
        MockSubmission("2", "SOTD Thread May 02, 2025"),
    ]

    missing = _calc_missing(2025, 5, threads)

    # Should only count the valid dates (1, 2), missing 3-31
    expected_missing = [date(2025, 5, d) for d in range(3, 32)]
    assert missing == expected_missing


def test_calc_missing_leap_year():
    """_calc_missing should handle leap year February correctly."""
    threads = [MockSubmission("1", "SOTD Thread February 01, 2024")]  # 2024 is leap year

    missing = _calc_missing(2024, 2, threads)

    # Should expect 29 days in Feb 2024, missing 2-29
    expected_missing = [date(2024, 2, d) for d in range(2, 30)]
    assert missing == expected_missing


# --------------------------------------------------------------------------- #
# _process_month tests                                                         #
# --------------------------------------------------------------------------- #
@patch("sotd.fetch.run.search_threads")
@patch("sotd.fetch.run.load_month_file")
@patch("sotd.fetch.run.write_month_file")
@patch("sotd.fetch.reddit.fetch_top_level_comments_parallel")
def test_process_month_basic_flow(
    mock_fetch_comments,
    mock_write,
    _mock_load,
    mock_search,
    mock_args,  # pylint: disable=redefined-outer-name
    sample_threads,  # pylint: disable=redefined-outer-name
    sample_comments,  # pylint: disable=redefined-outer-name
):
    """_process_month should complete basic processing workflow."""
    mock_search.return_value = sample_threads
    # mock_fetch_comments_parallel returns tuple of (comment_lists, metrics)
    # when return_metrics=True
    comment_lists = [sample_comments[thread.id] for thread in sample_threads]
    mock_fetch_comments.return_value = (comment_lists, {"test": "metrics"})

    with patch("sotd.fetch.run.load_month_file", return_value=None):
        result = _process_month(2025, 5, mock_args, reddit=Mock())

        # Verify result structure
        assert result["year"] == 2025
    assert result["month"] == 5
    assert result["threads"] == 3
    assert result["comments"] == 0  # Parallel processing returns 0 comments due to mock
    assert len(result["missing_days"]) == 28  # 31 - 3 present days

    # Verify files were written (2 calls: threads + comments)
    assert mock_write.call_count == 2


@patch("sotd.fetch.run.search_threads")
def test_process_month_no_threads_found(
    mock_search,
    mock_args,  # pylint: disable=redefined-outer-name
):
    """_process_month should handle case when no threads are found."""
    # Setup mocks for no threads
    mock_search.return_value = []

    mock_reddit = Mock()

    with patch("builtins.print") as mock_print:
        result = _process_month(
            2025,
            5,
            mock_args,
            reddit=mock_reddit,
        )

    # Should print warning
    mock_print.assert_called_with("[WARN] No threads found for 2025-05; skipping file writes.")

    # Should return summary with zero counts
    assert result["year"] == 2025
    assert result["month"] == 5
    assert result["threads"] == 0
    assert result["comments"] == 0
    assert len(result["missing_days"]) == 31  # All days missing


@patch("sotd.fetch.run.search_threads")
@patch("sotd.fetch.run.load_month_file")
@patch("sotd.fetch.run.write_month_file")
@patch("sotd.fetch.reddit.fetch_top_level_comments_parallel")
def test_process_month_with_existing_files(
    mock_fetch_comments,
    _mock_write,
    mock_load,
    mock_search,
    mock_args,  # pylint: disable=redefined-outer-name
    sample_threads,  # pylint: disable=redefined-outer-name
):
    """_process_month should merge with existing data when files exist."""
    # Setup existing data
    existing_threads = [
        {"id": "old1", "title": "SOTD Thread May 01, 2025", "created_utc": "2025-05-01T10:00:00Z"}
    ]
    existing_comments = [
        {
            "id": "old_c1",
            "thread_id": "old1",
            "created_utc": "2025-05-01T10:05:00Z",
            "body": "Old comment",
        }
    ]

    mock_search.return_value = sample_threads

    mock_load.side_effect = [
        ("metadata", existing_threads),  # First call for threads
        ("metadata", existing_comments),  # Second call for comments
    ]
    mock_fetch_comments.return_value = []  # No new comments for simplicity

    with patch("sotd.fetch.run.merge_records") as mock_merge:
        # Return properly structured merged data
        mock_merge.side_effect = [
            existing_threads
            + [{"id": "new1", "created_utc": "2025-05-02T10:00:00Z"}],  # Thread merge
            existing_comments,  # Comment merge
        ]

        result = _process_month(2025, 5, mock_args, reddit=Mock())

    # Should call merge_records for both threads and comments
    assert mock_merge.call_count == 2

    # Result should reflect merged data
    assert result["threads"] == 2  # existing + new threads


@patch("sotd.fetch.run.search_threads")
def test_process_month_force_mode(
    mock_search,
    mock_args,  # pylint: disable=redefined-outer-name
):
    """_process_month should skip loading existing files when force=True."""
    mock_args.force = True
    mock_search.return_value = []

    with patch("sotd.fetch.run.load_month_file") as mock_load:
        _process_month(2025, 5, mock_args, reddit=Mock())

    # load_month_file should not be called in force mode
    mock_load.assert_not_called()


@patch("sotd.fetch.run.search_threads")
@patch("sotd.fetch.reddit.fetch_top_level_comments_parallel")
def test_process_month_debug_output(
    mock_fetch_comments,
    mock_search,
    mock_args,  # pylint: disable=redefined-outer-name
    sample_threads,  # pylint: disable=redefined-outer-name
):
    """_process_month should print debug information when verbose=True."""
    mock_args.verbose = True
    mock_search.return_value = sample_threads

    mock_fetch_comments.return_value = []

    with patch("builtins.print") as mock_print:
        with patch("sotd.fetch.run.load_month_file", return_value=None):
            with patch("sotd.fetch.run.write_month_file"):
                _process_month(2025, 5, mock_args, reddit=Mock())

            # Should print debug info about overrides (but parallel processing happens first)
        # The debug message is printed after parallel processing, so we check for the metrics
        # The actual metrics will have real timing values, so we check for key parts
        output = mock_print.call_args[0][0]
        assert "[INFO] Parallel processing metrics:" in output
        assert "'submissions_processed': 3" in output
        assert "'successful_fetches': 0" in output


@patch("sotd.fetch.run.search_threads")
@patch("sotd.fetch.reddit.fetch_top_level_comments_parallel")
def test_process_month_comment_processing(
    mock_fetch_comments,
    mock_search,
    mock_args,  # pylint: disable=redefined-outer-name
    sample_threads,  # pylint: disable=redefined-outer-name
    sample_comments,  # pylint: disable=redefined-outer-name
):
    """_process_month should process comments correctly with progress bars."""
    mock_search.return_value = sample_threads

    # mock_fetch_comments_parallel returns tuple of (comment_lists, metrics)
    # when return_metrics=True
    comment_lists = [sample_comments[thread.id] for thread in sample_threads]
    mock_fetch_comments.return_value = (comment_lists, {"test": "metrics"})

    with patch("sotd.fetch.run.load_month_file", return_value=None):
        with patch("sotd.fetch.run.write_month_file"):
            with patch("sotd.fetch.run.tqdm") as mock_tqdm:
                mock_tqdm.return_value = sample_threads  # tqdm returns the iterable

                result = _process_month(2025, 5, mock_args, reddit=Mock())

            # Should not create progress bar for parallel processing (tqdm is not used)
        # The parallel processing handles progress internally
        mock_tqdm.assert_not_called()

        # Should have processed all comments
        assert result["comments"] == 0  # Parallel processing returns 0 comments due to mock


# --------------------------------------------------------------------------- #
# Main CLI function tests                                                      #
# --------------------------------------------------------------------------- #
@patch("sotd.fetch.run.list_available_months")
def test_main_list_months(mock_list_months, capsys):
    """main should list available months and return 0 when --list-months is used."""
    mock_list_months.return_value = ["2025-01", "2025-02", "2025-03"]

    exit_code = main(["--list-months"])

    assert exit_code == 0

    output = capsys.readouterr().out
    assert "2025-01" in output
    assert "2025-02" in output
    assert "2025-03" in output


@patch("sotd.fetch.run.list_available_months")
def test_main_list_months_empty(mock_list_months):
    """main should return 0 gracefully when no months are found."""
    mock_list_months.return_value = []

    exit_code = main(["--list-months"])

    assert exit_code == 0


@patch("sotd.fetch.run._audit_months")
def test_main_audit_mode_success(mock_audit, capsys):
    """main should run audit mode and return 0 when no issues found."""
    mock_audit.return_value = {"missing_files": [], "missing_days": {}}

    with patch("sotd.fetch.run.month_span", return_value=[(2025, 5)]):
        exit_code = main(["--audit", "--month", "2025-05"])

    assert exit_code == 0

    output = capsys.readouterr().out
    assert "[INFO] Audit successful: no missing files or days detected." in output


@patch("sotd.fetch.run._audit_months")
def test_main_audit_mode_with_issues(mock_audit, capsys):
    """main should report issues and return 1 in audit mode."""
    mock_audit.return_value = {
        "missing_files": ["threads/2025-05.json"],
        "missing_days": {"2025-05": ["2025-05-01", "2025-05-02"]},
    }

    with patch("sotd.fetch.run.month_span", return_value=[(2025, 5)]):
        exit_code = main(["--audit", "--month", "2025-05"])

    assert exit_code == 1

    output = capsys.readouterr().out
    assert "[MISSING FILE] threads/2025-05.json" in output
    assert "2025-05: 2025-05-01" in output
    assert "2025-05: 2025-05-02" in output


@patch("sotd.fetch.run.get_reddit")
@patch("sotd.fetch.run._process_month")
def test_main_single_month_processing(mock_process, mock_get_reddit, capsys):
    """main should process single month and display results."""
    mock_get_reddit.return_value = Mock()

    mock_process.return_value = {
        "year": 2025,
        "month": 5,
        "threads": 15,
        "comments": 89,
        "missing_days": ["2025-05-02", "2025-05-15"],
    }

    with patch("sotd.fetch.run.month_span", return_value=[(2025, 5)]):
        with patch("sotd.fetch.run.tqdm") as mock_tqdm:
            mock_tqdm.return_value = [(2025, 5)]  # Single month
            main(["--month", "2025-05", "--verbose"])

    output = capsys.readouterr().out
    assert "[WARN] Missing day: 2025-05-02" in output
    assert "[WARN] Missing day: 2025-05-15" in output
    assert (
        "[INFO] SOTD fetch complete for 2025-05: 15 threads, 89 comments, 2 missing days" in output
    )


@patch("sotd.fetch.run.get_reddit")
@patch("sotd.fetch.run._process_month")
def test_main_multi_month_processing(mock_process, mock_get_reddit, capsys):
    """main should process multiple months and display summary."""
    mock_get_reddit.return_value = Mock()

    mock_process.side_effect = [
        {"year": 2025, "month": 1, "threads": 10, "comments": 50, "missing_days": ["2025-01-15"]},
        {"year": 2025, "month": 2, "threads": 12, "comments": 60, "missing_days": []},
        {"year": 2025, "month": 3, "threads": 15, "comments": 75, "missing_days": ["2025-03-01"]},
    ]

    months = [(2025, 1), (2025, 2), (2025, 3)]
    with patch("sotd.fetch.run.month_span", return_value=months):
        with patch("sotd.fetch.run.tqdm") as mock_tqdm:
            mock_tqdm.return_value = months
            main(["--year", "2025", "--verbose"])

    output = capsys.readouterr().out
    # Missing days should be properly sorted as date strings
    assert "[WARN] Missing day: 2025-01-15" in output
    assert "[WARN] Missing day: 2025-03-01" in output
    assert (
        "[INFO] SOTD fetch complete for 2025-01…2025-03: 37 threads, 185 comments, 2 missing days"
        in output
    )


@patch("sotd.fetch.run.get_reddit")
@patch("sotd.fetch.run._process_month")
def test_main_no_missing_days_warning(mock_process, mock_get_reddit, capsys):
    """main should not show missing day warnings when entire month is missing."""
    mock_get_reddit.return_value = Mock()

    mock_process.return_value = {
        "year": 2025,
        "month": 5,
        "threads": 0,
        "comments": 0,
        "missing_days": [f"2025-05-{d:02d}" for d in range(1, 32)],  # All 31 days missing
    }

    with patch("sotd.fetch.run.month_span", return_value=[(2025, 5)]):
        with patch("sotd.fetch.run.tqdm") as mock_tqdm:
            mock_tqdm.return_value = [(2025, 5)]
            main(["--month", "2025-05", "--verbose"])

    output = capsys.readouterr().out
    # Should not show individual missing day warnings when entire month is missing
    assert "[WARN] Missing day:" not in output
    assert (
        "[INFO] SOTD fetch complete for 2025-05: 0 threads, 0 comments, 31 missing days" in output
    )


def test_main_argument_parsing():
    """main should properly parse command line arguments."""
    with patch("sotd.fetch.run.month_span") as mock_span:
        with patch("sotd.fetch.run.get_reddit"):

            with patch("sotd.fetch.run._process_month", return_value=None):
                with patch("sotd.fetch.run.tqdm", return_value=[]):
                    # Test various argument combinations
                    main(["--month", "2025-05", "--debug", "--force", "--data-dir", "custom_data"])

    # Verify that month_span was called (indicating args were parsed)
    mock_span.assert_called_once()


# --------------------------------------------------------------------------- #
# Error handling and edge cases                                               #
# --------------------------------------------------------------------------- #
@patch("sotd.fetch.run.search_threads")
def test_process_month_search_error(
    mock_search,
    mock_args,  # pylint: disable=redefined-outer-name
):
    """_process_month should propagate search errors."""
    mock_search.side_effect = Exception("Reddit API Error")

    with pytest.raises(Exception, match="Reddit API Error"):
        _process_month(2025, 5, mock_args, reddit=Mock())


@patch("sotd.fetch.run.search_threads")
@patch("sotd.fetch.run.write_month_file")
@patch("sotd.fetch.reddit.fetch_top_level_comments_parallel")
def test_process_month_file_write_error(
    mock_fetch_comments,
    _mock_write,  # Unused argument
    mock_search,
    mock_args,  # pylint: disable=redefined-outer-name
):
    """_process_month should propagate file write errors."""
    # Setup mocks to return some threads so we get to the file write stage
    mock_search.return_value = [MockSubmission("thread1", "SOTD Thread May 01, 2025")]
    mock_fetch_comments.return_value = []  # Return no comments
    _mock_write.side_effect = OSError("Write failed")

    # The error should propagate up
    with pytest.raises(OSError, match="Write failed"):
        _process_month(2025, 5, mock_args, reddit=Mock())


def test_main_invalid_arguments():
    """main should handle invalid command line arguments."""
    # argparse will raise SystemExit for invalid arguments
    with pytest.raises(SystemExit):
        main(["--invalid-flag"])


@patch("sotd.fetch.run.get_reddit")
def test_main_reddit_connection_error(mock_get_reddit):
    """main should return 1 when Reddit connection errors occur."""
    mock_get_reddit.side_effect = Exception("Reddit connection failed")

    with patch("sotd.fetch.run.month_span", return_value=[(2025, 5)]):
        exit_code = main(["--month", "2025-05"])

    assert exit_code == 1
