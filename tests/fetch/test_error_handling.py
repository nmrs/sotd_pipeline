"""Tests for error handling across the fetch pipeline."""

import os
import argparse
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from types import SimpleNamespace
from typing import List, cast
from praw.models import Submission

import pytest

from sotd.fetch.reddit import get_reddit, safe_call
from sotd.fetch.save import load_month_file, write_month_file
from sotd.fetch.overrides import load_overrides, apply_overrides
from sotd.fetch.run import _process_month


# --------------------------------------------------------------------------- #
# Reddit API Error Handling                                                   #
# --------------------------------------------------------------------------- #
def test_reddit_connection_timeout():
    """Test handling of network timeouts during Reddit API calls."""
    with patch("praw.Reddit") as mock_reddit:
        mock_reddit.side_effect = ConnectionError("Network timeout")

        with pytest.raises(ConnectionError, match="Network timeout"):
            get_reddit()


def test_reddit_authentication_failure():
    """Test handling of Reddit authentication failures."""
    with patch("praw.Reddit") as mock_reddit:
        mock_reddit.side_effect = Exception("Invalid credentials")

        with pytest.raises(Exception, match="Invalid credentials"):
            get_reddit()


def test_safe_call_network_error():
    """Test that safe_call returns None on non-rate-limit network errors."""

    def failing_function():
        raise ConnectionError("Network unreachable")

    result = safe_call(failing_function)
    assert result is None


def test_safe_call_reddit_server_error():
    """Test that safe_call returns None on Reddit server errors."""

    def failing_function():
        raise RuntimeError("Reddit is down")

    result = safe_call(failing_function)
    assert result is None


# --------------------------------------------------------------------------- #
# File System Error Handling                                                  #
# --------------------------------------------------------------------------- #
def test_load_month_file_permission_denied(tmp_path):
    """Test handling of permission errors when loading files."""
    file_path = tmp_path / "restricted.json"
    file_path.write_text('{"meta": {}, "data": []}')

    # Make file unreadable (permission denied)
    os.chmod(file_path, 0o000)

    try:
        with pytest.raises(PermissionError):
            load_month_file(file_path)
    finally:
        # Restore permissions for cleanup
        os.chmod(file_path, 0o644)


def test_load_month_file_corrupted_json(tmp_path):
    """Test handling of corrupted JSON files."""
    file_path = tmp_path / "corrupted.json"
    file_path.write_text("invalid json content {")

    result = load_month_file(file_path)
    assert result is None


def test_load_month_file_empty_file(tmp_path):
    """Test handling of empty files."""
    file_path = tmp_path / "empty.json"
    file_path.touch()  # Create empty file

    result = load_month_file(file_path)
    assert result is None


def test_write_month_file_permission_denied(tmp_path):
    """Test handling of permission errors when writing files."""
    # Create directory without write permissions
    restricted_dir = tmp_path / "restricted"
    restricted_dir.mkdir()
    os.chmod(restricted_dir, 0o555)  # Read and execute only

    file_path = restricted_dir / "test.json"

    try:
        with pytest.raises(PermissionError):
            write_month_file(file_path, {"test": "meta"}, [])
    finally:
        # Restore permissions for cleanup
        os.chmod(restricted_dir, 0o755)


def test_write_month_file_disk_full_simulation(tmp_path):
    """Test handling of disk full scenarios."""
    file_path = tmp_path / "test.json"

    # Mock Path.open to raise OSError (disk full) - this is what save_json_data actually uses
    with patch.object(Path, "open", side_effect=OSError("No space left on device")):
        with pytest.raises(OSError, match="No space left on device"):
            write_month_file(file_path, {"test": "meta"}, [])


def test_write_month_file_directory_creation_error(tmp_path):
    """Test handling of directory creation failures."""
    # Try to write to a path where parent directory creation would fail
    file_path = tmp_path / "nonexistent" / "deep" / "path" / "test.json"

    # Mock mkdir to fail
    with patch.object(Path, "mkdir", side_effect=OSError("Permission denied")):
        with pytest.raises(OSError, match="Permission denied"):
            write_month_file(file_path, {"test": "meta"}, [])


# --------------------------------------------------------------------------- #
# Override System Error Handling                                              #
# --------------------------------------------------------------------------- #
def test_load_overrides_file_not_found():
    """Test handling when override files don't exist."""
    with patch("sotd.fetch.overrides.Path.is_file", return_value=False):
        include, exclude = load_overrides()

        assert include == {}
        assert exclude == {}


def test_load_overrides_malformed_json():
    """Test handling of malformed override JSON files."""
    with patch("sotd.fetch.overrides.Path.is_file", return_value=True):
        with patch("sotd.fetch.overrides.Path.open", mock_open(read_data="invalid json {")):
            with pytest.raises(RuntimeError, match=r"Invalid JSON in overrides file: .*"):
                load_overrides()


def test_apply_overrides_network_error():
    """Test handling of network errors when fetching override submissions."""
    base_threads = [
        Mock(
            id="thread1",
            title="SOTD Thread May 01, 2025",
            permalink="/r/wetshaving/comments/thread1/",
            author="test_user",
            created_utc=1640995200,
            num_comments=5,
            link_flair_text="SOTD",
        )
    ]
    include_overrides = {"override1": "some_submission_id"}

    mock_reddit = Mock()
    mock_reddit.submission.side_effect = ConnectionError("Network error")

    # Should handle gracefully and return original threads
    result = apply_overrides(
        cast(List[Submission], base_threads),
        include_overrides,
        {},
        reddit=mock_reddit,
        year=2025,
        month=5,
        debug=False,
    )  # type: ignore
    assert len(result) == 1  # Only the original thread is present


def test_apply_overrides_submission_not_found():
    """Test handling when override submission doesn't exist."""
    base_threads = [
        SimpleNamespace(
            id="thread1",
            title="SOTD Thread May 01, 2025",
            permalink="/r/wetshaving/comments/thread1/",
            author="test_user",
            created_utc=1640995200,
            num_comments=5,
            link_flair_text="SOTD",
        )
    ]
    include_overrides = {"nonexistent": "fake_id"}

    mock_reddit = Mock()
    mock_reddit.submission.side_effect = ConnectionError("not found")

    # Should handle gracefully and return original threads
    result = apply_overrides(
        cast(List[Submission], base_threads),
        include_overrides,
        {},
        reddit=mock_reddit,
        year=2025,
        month=5,
        debug=False,
    )  # type: ignore
    assert len(result) == 1  # Original thread preserved


def test_apply_overrides_invalid_submission():
    """Test handling when override submission is invalid."""
    base_threads = [
        SimpleNamespace(
            id="thread1",
            title="SOTD Thread May 01, 2025",
            permalink="/r/wetshaving/comments/thread1/",
            author="test_user",
            created_utc=1640995200,
            num_comments=5,
            link_flair_text="SOTD",
        )
    ]
    include_overrides = {"invalid": "fake_id"}

    mock_submission = SimpleNamespace(
        id="invalid",
        title="Not a SOTD Thread",
        permalink="/r/wetshaving/comments/invalid/",
        author="test_user",
        created_utc=1640995200,
        num_comments=5,
        link_flair_text="SOTD",
    )
    mock_reddit = Mock()
    mock_reddit.submission.return_value = mock_submission

    # Should handle gracefully and return original threads
    result = apply_overrides(
        cast(List[Submission], base_threads),
        include_overrides,
        {},
        reddit=mock_reddit,
        year=2025,
        month=5,
        debug=False,
    )  # type: ignore
    assert len(result) == 1  # Original thread preserved


# --------------------------------------------------------------------------- #
# Memory and Resource Error Handling                                          #
# --------------------------------------------------------------------------- #
def test_large_dataset_memory_handling(tmp_path):
    """Test handling of very large datasets that might cause memory issues."""
    # Create a large dataset (simulate memory pressure)
    large_meta = {"month": "2025-05", "count": 100000}
    large_data = [{"id": f"comment_{i}", "body": "x" * 1000} for i in range(1000)]

    file_path = tmp_path / "large.json"

    # This should complete without memory errors
    write_month_file(file_path, large_meta, large_data)

    # Verify it can be read back
    result = load_month_file(file_path)
    if result is not None:
        assert result[0]["count"] == 100000
        assert len(result[1]) == 1000
    else:
        assert False, "Expected result to be a list, got None"


def test_unicode_handling_in_files(tmp_path):
    """Test handling of Unicode content in JSON files."""
    meta = {"month": "2025-05", "note": "测试 émojis 🧔‍♂️"}
    data = [
        {"id": "1", "body": "Shaved with 日本 razor"},
        {"id": "2", "body": "Great shave! 🪒✨"},
        {"id": "3", "body": "Здравствуйте from Russia"},
    ]

    file_path = tmp_path / "unicode.json"

    # Should handle Unicode without errors
    write_month_file(file_path, meta, data)

    result = load_month_file(file_path)
    if result is not None:
        assert "测试" in result[0]["note"]
        assert "🧔‍♂️" in result[0]["note"]
        assert "日本" in result[1][0]["body"]
        assert "🪒✨" in result[1][1]["body"]
        assert "Здравствуйте" in result[1][2]["body"]
    else:
        assert False, "Expected result to be a list, got None"


# --------------------------------------------------------------------------- #
# Concurrent Access Error Handling                                            #
# --------------------------------------------------------------------------- #
def test_concurrent_file_access(tmp_path):
    """Test handling of concurrent file access scenarios."""
    file_path = tmp_path / "concurrent.json"

    # Write initial file
    write_month_file(file_path, {"version": 1}, [{"id": "1"}])

    # Simulate concurrent modification by changing file between load and write
    def modify_file_during_operation():
        # This would happen if another process modifies the file
        write_month_file(file_path, {"version": 2}, [{"id": "2"}])
        return {"version": 1}, [{"id": "1"}]

    # The system should handle this gracefully (last write wins)
    with patch("sotd.fetch.save.load_month_file", side_effect=modify_file_during_operation):
        write_month_file(file_path, {"version": 3}, [{"id": "3"}])

    # Verify final state
    result = load_month_file(file_path)
    if result is not None:
        assert result[0]["version"] == 3
        assert result[1][0]["id"] == "3"
    else:
        assert False, "Expected result to be a list, got None"


def mock_open_with_content(content):
    """Helper function to create a mock open that returns specific content."""
    return mock_open(read_data=content)


# --------------------------------------------------------------------------- #
# Integration Error Scenarios                                                 #
# --------------------------------------------------------------------------- #
def test_partial_failure_recovery():
    """Test recovery from partial failures in the fetch pipeline."""
    # Simulate scenario where threads are fetched but comments fail

    args = argparse.Namespace()
    args.out_dir = "test_data"
    args.debug = False
    args.force = False

    with patch("sotd.fetch.run.search_threads") as mock_search:
        with patch("sotd.fetch.run.apply_overrides") as mock_apply:
            with patch("sotd.fetch.run.fetch_top_level_comments") as mock_fetch_comments:
                with patch("sotd.fetch.run.load_month_file", return_value=None):
                    with patch("sotd.fetch.run.write_month_file"):

                        # Setup: threads found successfully
                        mock_thread = Mock()
                        mock_thread.id = "thread1"
                        mock_thread.title = "SOTD Thread May 01, 2025"
                        mock_thread.permalink = "/r/wetshaving/comments/thread1/"
                        mock_thread.author = "test_user"
                        mock_thread.created_utc = 1640995200
                        mock_thread.num_comments = 5
                        mock_thread.link_flair_text = "SOTD"
                        mock_thread.title = "SOTD Thread May 01, 2025"  # Set title as string

                        mock_search.return_value = [mock_thread]
                        mock_apply.return_value = [mock_thread]

                        # But comment fetching fails
                        # This broad Exception is intentional for test simulation
                        mock_fetch_comments.side_effect = Exception("Reddit API error")

                        # Should propagate the error
                        with pytest.raises(Exception, match="Reddit API error"):
                            _process_month(
                                2025,
                                5,
                                args,
                                reddit=Mock(),
                                include_overrides={},
                                exclude_overrides={},
                            )


def test_graceful_degradation_no_comments():
    """Test graceful handling when comments can't be fetched but threads can."""
    args = argparse.Namespace()
    args.out_dir = "test_data"
    args.debug = False
    args.force = False

    with patch("sotd.fetch.run.search_threads") as mock_search:
        with patch("sotd.fetch.run.apply_overrides") as mock_apply:
            with patch("sotd.fetch.run.fetch_top_level_comments") as mock_fetch_comments:
                with patch("sotd.fetch.run.load_month_file", return_value=None):
                    with patch("sotd.fetch.run.write_month_file"):

                        # Setup successful thread fetching
                        mock_thread = Mock()
                        mock_thread.id = "thread1"
                        mock_thread.title = "SOTD Thread May 01, 2025"
                        mock_thread.created_utc = 1640995200
                        mock_thread.permalink = "/r/wetshaving/comments/thread1/"
                        mock_thread.num_comments = 0
                        mock_thread.link_flair_text = "SOTD"
                        mock_thread.author = "user1"

                        mock_search.return_value = [mock_thread]
                        mock_apply.return_value = [mock_thread]

                        # No comments available (empty list, not error)
                        mock_fetch_comments.return_value = []

                        # Should complete successfully with 0 comments
                        result = _process_month(
                            2025, 5, args, reddit=Mock(), include_overrides={}, exclude_overrides={}
                        )

                        assert result["threads"] == 1
                        assert result["comments"] == 0
                        assert result["year"] == 2025
                        assert result["month"] == 5
