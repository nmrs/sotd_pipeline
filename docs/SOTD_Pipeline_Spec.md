# 🧸 SOTD Pipeline Specification

This specification defines the structure, configuration, and operational behavior of the Shave of the Day (SOTD) pipeline for extracting, normalizing, and reporting shaving-related content from Reddit's r/wetshaving community.

## Phase 0: Project Setup

### 📄 Environment
- Python version: **3.11.8**
- Type checking: **Pyright** (`typeCheckingMode: "standard"`)
- Code formatting: **Black**
- Linting: **Ruff**
- Testing: **Pytest + Pytest-Cov**

### 🌍 Directory Layout
```plaintext
sotd_fetcher/
├── data/
│   ├── threads/
│   ├── comments/
├── overrides/
│   └── sotd_thread_overrides.json
├── sotd/
│   ├── fetch/
│   │   ├── run.py
│   │   ├── reddit.py
│   │   ├── overrides.py
│   │   ├── merge.py
│   │   └── save.py
│   └── ...
├── tests/
│   ├── test_fetch.py
│   └── ...
├── cli.py (optional)
├── run.py (pipeline orchestration)
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── Makefile
└── .gitignore
```

### 🚀 Installation Steps
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
```

### 📁 requirements.txt
```
praw
dateparser
```

### 📁 requirements-dev.txt
```
-r requirements.txt
black
ruff
pytest
pytest-cov
pyright
```

### 📝 pyproject.toml
```toml
[tool.black]
line-length = 100
target-version = ["py311"]

[tool.ruff]
line-length = 100
select = ["E", "F", "I"]
exclude = ["data", "tests"]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]
```

### 📁 .gitignore
```
__pycache__/
*.pyc
venv/
.env/
.vscode/
.coverage
coverage/
htmlcov/
data/
```

### 📂 Makefile
```makefile
.PHONY: all lint format typecheck test coverage fetch

all: lint format typecheck test

lint:
	ruff .

format:
	black .

typecheck:
	pyright

test:
	pytest tests/

coverage:
	pytest --cov=sotd --cov-report=term-missing tests/

fetch:
	python sotd/fetch/run.py --month 2025-05
```

---

## Phase 1: Fetch (Thread + Comment Collection)

### ✅ Overview
Fetches SOTD threads and top-level comments from r/wetshaving for a specified month, with local caching and override support.

### ⚖️ Search Strategy
- Use **PRAW subreddit search**: `flair:SOTD mar march 2025`
- Fallback title matching via regex: `\b(SOTD|Shave of the Day)\b.*\bThread\b`
- Post-processing filters:
  - Title date must be parsable (via `dateparser`)
  - Thread must be a `self` post
  - Title date used to determine calendar coverage (not created_utc)

### 📁 File Outputs

#### `threads/YYYY-MM.json`
```json
{
  "meta": {
    "month": "2025-04",
    "extracted_at": "2025-05-21T18:40:00Z",
    "thread_count": 29,
    "expected_days": 30,
    "missing_days": ["2025-04-01", "2025-04-17"],
    "notes": "Based on title dates. Includes manual overrides."
  },
  "data": [
    {
      "id": "t3_abc123",
      "title": "Tuesday SOTD Thread - Apr 2, 2025",
      "url": "https://www.reddit.com/r/wetshaving/comments/abc123/",
      "author": "AutoModerator",
      "created_utc": "2025-04-02T12:00:00Z",
      "num_comments": 42,
      "flair": null
    }
  ]
}
```

#### `comments/YYYY-MM.json`
```json
{
  "meta": {
    "month": "2025-04",
    "extracted_at": "2025-05-21T18:40:00Z",
    "comment_count": 407,
    "thread_count_with_comments": 28,
    "missing_days": ["2025-04-01", "2025-04-17"],
    "threads_missing_comments": ["t3_abc123", "t3_def456"],
    "notes": "Only top-level comments included. Some threads empty or removed."
  },
  "data": [
    {
      "id": "t1_xyz789",
      "thread_id": "t3_abc123",
      "thread_title": "Tuesday SOTD Thread - Apr 2, 2025",
      "url": "https://www.reddit.com/r/wetshaving/comments/abc123/comment/xyz789/",
      "author": "shaver_joe",
      "created_utc": "2025-04-02T13:15:47Z",
      "body": "Razor: Karve CB\nBlade: Astra SP\nBrush: Simpson T3\nSoap: Stirling Bay Rum"
    }
  ]
}
```

### 📂 overrides/sotd_thread_overrides.json
```json
{
  "include": [
    {
      "id": "t3_abc123",
      "title": "Tuesday SOTD Thread - Apr 2, 2025",
      "url": "https://www.reddit.com/r/wetshaving/comments/abc123/"
    }
  ],
  "exclude": [
    {
      "id": "t3_xyz456",
      "title": "SOTD Recap",
      "url": "https://www.reddit.com/r/wetshaving/comments/xyz456/"
    }
  ]
}
```

### 🔁 Merging Behavior
- Files are **merged** by default
- For threads/comments with duplicate IDs, the version with the **latest `created_utc`** is retained
- If `--force` is passed, files are overwritten completely
- Files are **always written** even if unchanged, with normalized sort and fresh metadata
- Entries are sorted by `created_utc` ascending

### ⚠️ Warnings & Logging
- Warn on threads with no top-level comments
- Warn if a thread can't parse a date from title
- Log a final summary:
  ```
  [INFO] SOTD fetch complete for Apr 2025: 29 threads, 407 comments, 2 missing days (2025-04-01, 2025-04-17)
  ```
- Use `--debug` to log skipped threads/comments and reasons

---

Next phase: **Extraction** (parsing Razor, Blade, Soap, etc. from comment body)
