# SOTD Fetcher – Developer Specification

## Overview
This tool extracts "Shave of the Day" (SOTD) reports from Reddit's r/wetshaving subreddit by crawling top-level comments in daily SOTD threads. It supports monthly and yearly extraction, manual overrides, hybrid thread sourcing via Pushshift and PRAW, and outputs clean, sorted JSON files for later analysis.

---

## Goals
- Fetch all top-level comments from each day's SOTD thread.
- Combine Reddit and Pushshift APIs for coverage and redundancy.
- Allow manual overrides to include or exclude specific threads.
- Store clean JSON files per month and include metadata.
- Be testable, modular, and resilient to missing or malformed data.

---

## Key Features

### ✅ Reddit Integration (via PRAW)
- Connects using credentials from `praw.ini`
- Validates subreddit access
- Pulls comment data per thread (top-level only)

### ✅ Pushshift Integration
- Primary source for historical thread discovery
- Fetches metadata: title, flair, timestamp, id
- Falls back to Reddit for recent N days or failures
- Automatically retries with known mirror endpoints if primary Pushshift URL fails

### ✅ Hybrid Fetching
- Combines Pushshift and Reddit submissions
- For the last N days (`--fallback-days`), always uses Reddit directly
- De-duplicates threads by ID
- Flags partial matches (e.g., title match but no flair)

### ✅ Manual Overrides
- User-defined JSON includes and excludes
- Each entry specifies: thread ID, date, optional title and URL
- Validated at load-time
- In strict mode, validation errors halt execution; otherwise, warnings are logged

### ✅ JSON Output
- One JSON file per month, stored in `data/YYYY/YYYYMM.json`
- Pretty-printed, sorted by UTC timestamp
- Metadata includes retrieval date and missing thread days
- `retrieved_utc` reflects the moment the data was fetched

---

## File Format

### Example Output File (202505.json)
```json
{
  "month": "2025-05",
  "retrieved_utc": "2025-05-21T22:00:00Z",
  "missing_days": ["2025-05-02", "2025-05-17"],
  "comments": [
    {
      "id": "abc123",
      "author": "user123",
      "body": "Razor: Karve CB, Soap: MWF",
      "created_utc": 1746169200,
      "url": "https://reddit.com/r/wetshaving/comments/xyz"
    }
  ]
}
```

### Example Thread Cache (202505_threads.json)
```json
{
  "month": "2025-05",
  "retrieved_utc": "2025-05-21T22:00:00Z",
  "thread_count": 29,
  "missing_days": ["2025-05-02"],
  "partial_matches": [
    {
      "id": "xyz789",
      "url": "https://reddit.com/r/wetshaving/comments/xyz789",
      "title_match": true,
      "flair_match": false
    }
  ]
}
```

### Example Manual File (manual_threads.json)
```json
{
  "include": [
    {
      "id": "abc123",
      "date": "2025-05-03",
      "title": "Saturday SOTD Thread - May 3, 2025",
      "url": "https://reddit.com/r/wetshaving/comments/abc123"
    }
  ],
  "exclude": [
    {
      "id": "def456",
      "date": "2025-05-04",
      "title": "Sunday SOTD Thread - May 4, 2025",
      "url": "https://reddit.com/r/wetshaving/comments/def456"
    }
  ]
}
```

---

## Error Handling
- 403s from Pushshift retry with Reddit (if recent enough)
- If primary Pushshift mirror fails, retry alternate mirrors
- Missing days logged and included in output metadata
- Invalid manual threads reported via console
- Strict mode halts on validation issues; otherwise logs warnings

---

## Testing
- Unit tests for each module using pytest
- Mocking for PRAW and filesystem
- Full integration test for one month with fake data

---

## CLI Usage

### Unified Pipeline Interface (Recommended)
```bash
# Individual phases
python run.py fetch --month 2025-05 --force
python run.py extract --month 2025-05 --force
python run.py match --month 2025-05 --force
python run.py enrich --month 2025-05 --force
python run.py aggregate --month 2025-05 --force
python run.py report --month 2025-05 --force

# Complete pipeline
python run.py pipeline --month 2025-05 --force

# Phase ranges
python run.py pipeline --month 2025-05 --force extract:enrich
python run.py pipeline --month 2025-05 --force match:
python run.py pipeline --month 2025-05 --force :enrich

# Date ranges
python run.py pipeline --year 2024 --force
python run.py pipeline --start-month 2024-01 --end-month 2024-06 --force
python run.py pipeline --range 2024-01:2024-06 --force

# Debug mode
python run.py pipeline --month 2025-05 --force --debug
```

### Legacy Direct Phase Execution
```bash
python sotd/fetch/run.py --month 2025-05 --force
python sotd/extract/run.py --month 2025-05 --force
python sotd/match/run.py --month 2025-05 --force
python sotd/enrich/run.py --month 2025-05 --force
```

**Note**: The `--force` flag is MANDATORY for all pipeline operations unless explicitly specified otherwise. This ensures fresh data processing and avoids cached results.

---

## Logging and Verbosity
- `--debug` shows:
  - Real-time progress updates
  - Thread and comment totals
  - Partial match detection
  - Fallback source usage
  - Manual file issues
- Default output is concise

---

## Comment Filtering Rules
- Comments are skipped if:
  - The body is `[removed]` or `[deleted]`
  - The body is empty or whitespace only
- Comments with only a URL **are retained**

---

## Dependencies
- Python 3.8+
- `praw`, `requests`, `tqdm`, `pytest`, `python-dateutil`, `mypy`, `flake8`

---

## Status
Production-ready.  
Future enhancements could include:
- Analysis tooling
- Frontend dashboard
- Docker packaging
- Scheduling integration