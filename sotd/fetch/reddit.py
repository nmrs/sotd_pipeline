"""Reddit‐helpers: authentication, searching, comment harvesting – plus
a small `safe_call` wrapper that handles Reddit's `RateLimitExceeded`.
"""

from __future__ import annotations

import calendar
import os
import time
from datetime import date as _date
from typing import List, Sequence, TypeVar, cast

import praw
from praw.models import Comment, Submission
from prawcore.exceptions import NotFound, RequestException

# PRAW 7.x has RateLimitExceeded; newer prawcore switched to TooManyRequests.
try:
    from prawcore.exceptions import RateLimitExceeded  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover
    from prawcore.exceptions import TooManyRequests as RateLimitExceeded  # type: ignore


T = TypeVar("T")


# --------------------------------------------------------------------------- #
# rate-limit wrapper                                                          #
# --------------------------------------------------------------------------- #
def safe_call(fn, *args, **kwargs):  # type: ignore[no-untyped-def]
    """Call *fn* with enhanced rate limit detection and smart backoff.

    Enhanced features:
    - Extracts wait time from Reddit's rate limit headers when available
    - Falls back to exponential backoff with jitter when no explicit wait time
    - Prevents thundering herd with randomized delays
    - Tracks rate limit frequency and patterns
    - Provides structured logging for rate limit events

    Prints a human-readable warning:

        [WARN] Reddit rate-limit hit; waiting 8m 20s (from headers)…
        [WARN] Reddit rate-limit hit; waiting 1m 30s (exponential backoff)…

    If the retry also fails, the exception propagates.
    Returns None if any other exception occurs.
    """
    import random

    # Exponential backoff configuration
    max_attempts = 3  # Maximum retry attempts
    base_delay = 1.0  # Base delay in seconds
    max_delay = 60.0  # Maximum delay in seconds
    backoff_factor = 2.0  # Exponential backoff factor
    jitter_factor = 0.1  # Jitter factor (10% of delay)

    rate_limit_hits = 0
    start_time = time.time()

    for attempt in range(max_attempts):
        try:
            # Track response time for rate limit detection
            call_start = time.time()
            result = fn(*args, **kwargs)
            call_duration = time.time() - call_start

            # Detect rate limits from slow response times (> 2 seconds)
            if call_duration > 2.0 and attempt > 0:
                rate_limit_hits += 1
                duration_str = f"{call_duration:.1f}s"
                print(f"[WARN] Slow response detected ({duration_str}); treating as rate limit")
                # Simulate rate limit behavior for slow responses
                time.sleep(5)  # Brief delay for slow responses
                continue

            return result

        except RateLimitExceeded as exc:
            rate_limit_hits += 1

            # Calculate delay with smart backoff strategy
            if attempt < max_attempts - 1:
                # Try to extract wait time from Reddit's headers first
                wait_time = None

                # Check for explicit wait time in exception
                if hasattr(exc, "sleep_time") and exc.sleep_time is not None:  # type: ignore
                    wait_time = int(exc.sleep_time)  # type: ignore[attr-defined]
                elif hasattr(exc, "retry_after") and exc.retry_after is not None:  # type: ignore
                    wait_time = int(exc.retry_after)  # type: ignore[attr-defined]
                elif hasattr(exc, "response") and exc.response is not None:
                    # Try to extract from response headers
                    headers = getattr(exc.response, "headers", {})
                    retry_after = headers.get("Retry-After")
                    if retry_after:
                        try:
                            wait_time = int(retry_after)
                        except (ValueError, TypeError):
                            pass

                if wait_time is not None:
                    # Use Reddit's explicit wait time with small jitter
                    jitter = random.uniform(0, wait_time * jitter_factor)
                    delay = wait_time + jitter
                    delay_source = "headers"
                else:
                    # Fall back to exponential backoff with jitter
                    base_delay_calc = base_delay * (backoff_factor**attempt)
                    delay = min(base_delay_calc, max_delay)
                    jitter = random.uniform(0, delay * jitter_factor)
                    delay = delay + jitter
                    delay_source = "exponential backoff"

                mins, secs = divmod(int(delay), 60)

                # Enhanced logging with rate limit statistics and attempt info
                total_duration = time.time() - start_time
                print(
                    f"[WARN] Reddit rate-limit hit (hit #{rate_limit_hits} in "
                    f"{total_duration:.1f}s, attempt {attempt + 1}/{max_attempts}); "
                    f"waiting {mins}m {secs}s ({delay_source})…"
                )

                time.sleep(delay)
            else:
                # Final attempt failed
                total_duration = time.time() - start_time
                print(
                    f"[WARN] Rate limit exceeded after {rate_limit_hits} hits in "
                    f"{total_duration:.1f}s (max attempts reached)"
                )
                raise

        except (ConnectionError, RuntimeError, RequestException, NotFound, ValueError) as exc:
            print(f"[WARN] Reddit API error: {exc}")
            return None


# --------------------------------------------------------------------------- #
# auth                                                                        #
# --------------------------------------------------------------------------- #
def _require_env(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise RuntimeError(f"Missing environment variable: {key}")
    return val


def get_reddit() -> praw.Reddit:  # noqa: D401
    """Return a PRAW instance using the section in praw.ini."""
    return praw.Reddit()  # relies on praw.ini in project root


# --------------------------------------------------------------------------- #
# searching & filtering                                                       #
# --------------------------------------------------------------------------- #
def search_threads(
    subreddit_name: str, year: int, month: int, *, debug: bool = False
) -> List[Submission]:
    reddit = get_reddit()
    subreddit = reddit.subreddit(subreddit_name)

    month_abbr = calendar.month_abbr[month].lower()
    month_name = calendar.month_name[month].lower()
    # Two search patterns: normal and "yearSOTD" style
    queries = [
        f"flair:SOTD {month_abbr} {month_name} {year}",
        f"flair:SOTD {month_abbr} {month_name} {year}SOTD",
    ]

    all_results = {}
    for query in queries:
        if debug:
            print(f"[DEBUG] Search query: {query!r}")
        raw_results = safe_call(subreddit.search, query, sort="relevance", syntax="lucene")
        if raw_results is None:
            raw_results = []
        raw_results = list(raw_results)
        if debug:
            print(f"[DEBUG] PRAW raw results for {query!r}: {len(raw_results)}")
        for sub in raw_results:
            all_results[sub.id] = sub  # dedupe by Reddit submission ID

    combined = list(all_results.values())
    if debug:
        print(f"[DEBUG] Combined raw results (deduped): {len(combined)}")

    # Process thread overrides
    month_str = f"{year:04d}-{month:02d}"
    override_threads = process_thread_overrides(month_str, reddit, debug=debug)

    # Add override threads to results (existing deduplication will handle duplicates)
    for override_thread in override_threads:
        all_results[override_thread.id] = override_thread

    if debug and override_threads:
        print(f"[DEBUG] Added {len(override_threads)} override threads")

    # Re-combine and filter
    combined = list(all_results.values())
    if debug:
        print(f"[DEBUG] Combined results with overrides: {len(combined)}")

    valid = filter_valid_threads(combined, year, month, debug=debug)
    return valid


def filter_valid_threads(
    threads: Sequence[Submission], year: int, month: int, *, debug: bool = False
) -> List[Submission]:
    from datetime import datetime

    from sotd.utils import parse_thread_date

    kept: List[Submission] = []
    for sub in threads:
        d = parse_thread_date(sub.title, year)
        # --- CHANGED: Fallback to _override_date if present and title is unparsable ---
        if d is None and hasattr(sub, "_override_date"):
            try:
                d = datetime.strptime(sub._override_date, "%Y-%m-%d").date()
            except Exception:
                d = None
        if d is None:
            if debug:
                print(f"[DEBUG] Skip (no-date) {sub.title}")
            continue
        if (d.year, d.month) != (year, month):
            if debug:
                print(f"[DEBUG] Skip (wrong-month) {sub.title}")
            continue
        kept.append(sub)

    # --- CHANGED: Sort using fallback date if present ---
    def sort_key(s):
        d = parse_thread_date(s.title, year)
        if d is None and hasattr(s, "_override_date"):
            try:
                d = datetime.strptime(s._override_date, "%Y-%m-%d").date()
            except Exception:
                d = None
        return d or _date.min

    kept.sort(key=sort_key)
    if debug:
        print(f"[DEBUG] Valid threads:     {len(kept)}")
    return kept


# --------------------------------------------------------------------------- #
# comments                                                                    #
# --------------------------------------------------------------------------- #
def fetch_top_level_comments(submission: Submission) -> List[Comment]:
    """Return only root comments (shaves)."""
    safe_call(submission.comments.replace_more, limit=None)

    return cast(
        List[Comment],
        [c for c in submission.comments.list() if getattr(c, "is_root", False)],
    )


# --------------------------------------------------------------------------- #
# parallel comment fetching                                                   #
# --------------------------------------------------------------------------- #
def fetch_top_level_comments_parallel(
    submissions: Sequence[Submission],
    max_workers: int = 3,
    chunk_size: int = 1,
    timeout: int = 30,
    adaptive_workers: bool = False,
    fallback_to_sequential: bool = True,
    return_metrics: bool = False,
) -> List[List[Comment]] | tuple[List[List[Comment]], dict]:
    """Fetch top-level comments for multiple submissions in parallel.

    Args:
        submissions: List of Reddit submissions to fetch comments for
        max_workers: Maximum number of worker threads (default: 3)
        chunk_size: Number of submissions per worker chunk (default: 1)
        timeout: Timeout in seconds for each worker (default: 30)
        adaptive_workers: Whether to adjust worker count based on rate limits
        fallback_to_sequential: Whether to fall back to sequential processing if parallel fails
        return_metrics: Whether to return performance metrics along with results

    Returns:
        List of comment lists (one per submission) or tuple of (results, metrics)
    """
    import concurrent.futures
    import time
    from typing import Optional, Tuple

    if not submissions:
        return ([], {}) if return_metrics else []

    # Initialize metrics
    start_time = time.time()
    rate_limit_hits = 0
    worker_utilization = 0.0

    def fetch_comments_worker(submission: Submission) -> Tuple[str, List[Comment]]:
        """Worker function to fetch comments for a single submission."""
        nonlocal rate_limit_hits

        try:
            # Use safe_call to handle rate limits properly
            comments = safe_call(fetch_top_level_comments, submission)
            if comments is None:
                # safe_call returned None due to error
                return (submission.id, [])
            return (submission.id, comments)
        except Exception as e:
            # Handle rate limits and other errors gracefully
            if "rate limit" in str(e).lower() or "429" in str(e):
                rate_limit_hits += 1
            print(f"[WARN] Error fetching comments for {submission.id}: {e}")
            return (submission.id, [])

    # Determine optimal worker count
    if max_workers <= 0:
        if fallback_to_sequential:
            # Fall back to sequential processing
            sequential_results: List[List[Comment]] = []
            for submission in submissions:
                try:
                    comments = safe_call(fetch_top_level_comments, submission)
                    if comments is None:
                        sequential_results.append([])
                    else:
                        sequential_results.append(comments)
                except Exception as e:
                    print(f"[WARN] Error in sequential fallback for {submission.id}: {e}")
                    sequential_results.append([])

            if return_metrics:
                total_time = time.time() - start_time
                metrics = {
                    "total_time": total_time,
                    "worker_utilization": 1.0,  # Sequential = 100% utilization
                    "rate_limit_hits": 0,
                    "processing_mode": "sequential_fallback",
                }
                return sequential_results, metrics
            return sequential_results
        else:
            raise ValueError("max_workers must be > 0 when fallback_to_sequential=False")

    # Adjust worker count based on rate limit frequency if adaptive
    if adaptive_workers and rate_limit_hits > 0:
        # Reduce workers if we're hitting rate limits
        adjusted_workers = max(1, max_workers - min(rate_limit_hits, max_workers - 1))
        if adjusted_workers != max_workers:
            print(
                f"[INFO] Adjusting workers from {max_workers} to {adjusted_workers} "
                f"due to rate limits"
            )
            max_workers = adjusted_workers

    # Process submissions in parallel
    parallel_results: List[Optional[List[Comment]]] = [None] * len(
        submissions
    )  # Pre-allocate results list

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_index = {
                executor.submit(fetch_comments_worker, submission): i
                for i, submission in enumerate(submissions)
            }

            # Collect results as they complete
            completed_count = 0
            for future in concurrent.futures.as_completed(future_to_index, timeout=timeout):
                index = future_to_index[future]
                try:
                    submission_id, comments = future.result()
                    parallel_results[index] = comments
                    completed_count += 1
                except concurrent.futures.TimeoutError:
                    print(f"[WARN] Timeout while fetching comments for submission at index {index}")
                    parallel_results[index] = []
                except Exception as e:
                    print(f"[WARN] Exception in worker for submission at index {index}: {e}")
                    parallel_results[index] = []

            # Calculate worker utilization
            worker_utilization = completed_count / len(submissions) if submissions else 0.0

    except Exception as e:
        print(f"[WARN] Parallel processing failed: {e}")
        if fallback_to_sequential:
            print("[INFO] Falling back to sequential processing")
            return fetch_top_level_comments_parallel(
                submissions,
                max_workers=0,
                fallback_to_sequential=True,
                return_metrics=return_metrics,
            )
        else:
            raise

    # Convert None values to empty lists and ensure proper typing
    final_results: List[List[Comment]] = [r if r is not None else [] for r in parallel_results]

    # Calculate final metrics
    total_time = time.time() - start_time

    if return_metrics:
        metrics = {
            "total_time": total_time,
            "worker_utilization": worker_utilization,
            "rate_limit_hits": rate_limit_hits,
            "processing_mode": "parallel",
            "submissions_processed": len(submissions),
            "successful_fetches": sum(1 for r in final_results if r),
            "average_time_per_submission": total_time / len(submissions) if submissions else 0.0,
        }
        return final_results, metrics

    return final_results


# --------------------------------------------------------------------------- #
# thread override functionality                                               #
# --------------------------------------------------------------------------- #


def load_thread_overrides(month: str) -> List[str]:
    """Load manual thread overrides from YAML file.

    Args:
        month: Month in YYYY-MM format (e.g., "2025-06")

    Returns:
        List of Reddit URLs for manual override threads

    Raises:
        yaml.YAMLError: If YAML file is malformed
    """
    from pathlib import Path

    from sotd.utils.yaml_loader import load_yaml_with_nfc

    override_path = Path("data/thread_overrides.yaml")

    if not override_path.exists():
        return []

    try:
        data = load_yaml_with_nfc(override_path)
        if not data:
            return []

        # Extract URLs for the specified month
        urls = []
        for date_key, url_list in data.items():
            # Convert date_key to string (handle datetime.date or str)
            if hasattr(date_key, "isoformat"):
                date_str = date_key.isoformat()
            else:
                date_str = str(date_key)
            if date_str.startswith(month):
                if isinstance(url_list, list):
                    urls.extend(url_list)
                else:
                    # Handle single URL case
                    urls.append(url_list)

        return urls
    except Exception as e:
        # Handle YAML errors gracefully
        print(f"[WARN] Failed to load thread overrides: {e}")
        return []


def validate_thread_override(url: str, reddit) -> Submission:
    """Validate a thread override URL with PRAW.

    Args:
        url: Reddit thread URL
        reddit: PRAW Reddit instance

    Returns:
        Submission object if valid

    Raises:
        ValueError: If thread is not found or not accessible
    """
    try:
        submission = reddit.submission(url=url)

        # Basic validation that thread exists and is accessible
        if not submission.title or submission.author is None:
            raise ValueError(f"Thread not accessible: {url}")

        return submission
    except Exception as e:
        raise ValueError(f"Failed to fetch thread override: {url} - {e}")


def process_thread_overrides(month: str, reddit, debug: bool = False) -> List[Submission]:
    # from datetime import datetime  # Not needed, remove
    # --- CHANGED: Load mapping of date_key -> list of URLs ---
    from pathlib import Path

    from sotd.utils.yaml_loader import load_yaml_with_nfc

    override_path = Path("data/thread_overrides.yaml")
    if not override_path.exists():
        if debug:
            print(f"[DEBUG] No thread overrides found for {month}")
        return []
    try:
        data = load_yaml_with_nfc(override_path)
        if not data:
            if debug:
                print(f"[DEBUG] No thread overrides found for {month}")
            return []
    except Exception as e:
        print(f"[WARN] Failed to load thread overrides: {e}")
        return []

    # Build list of (date_key, url) for the month
    url_date_pairs = []
    for date_key, url_list in data.items():
        # Convert date_key to string (handle datetime.date or str)
        if hasattr(date_key, "isoformat"):
            date_str = date_key.isoformat()
        else:
            date_str = str(date_key)
        if date_str.startswith(month):
            if isinstance(url_list, list):
                for url in url_list:
                    url_date_pairs.append((date_str, url))
            else:
                url_date_pairs.append((date_str, url_list))

    if not url_date_pairs:
        if debug:
            print(f"[DEBUG] No thread overrides found for {month}")
        return []

    if debug:
        print(f"[DEBUG] Processing {len(url_date_pairs)} thread overrides for {month}")

    valid_submissions = []

    for date_str, url in url_date_pairs:
        try:
            submission = validate_thread_override(url, reddit)
            # Attach the YAML date as _override_date for fallback
            setattr(submission, "_override_date", date_str)
            valid_submissions.append(submission)
            if debug:
                print(f"[DEBUG] Validated override: {submission.title}")
        except ValueError as e:
            print(f"[WARN] Failed to fetch thread override: {url} - {e}")
            continue

    if debug:
        print(
            f"[DEBUG] Successfully processed {len(valid_submissions)}/"
            f"{len(url_date_pairs)} overrides"
        )

    return valid_submissions
