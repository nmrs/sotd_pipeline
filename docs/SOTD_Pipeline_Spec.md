# 🧸 SOTD Pipeline Specification

## 🛠️ Pipeline Structure Overview

The SOTD Fetcher is built as a multi-phase data pipeline designed to extract, normalize, and analyze r/wetshaving content from Reddit. It is structured as follows:

This pipeline extracts, processes, and summarizes Shave of the Day (SOTD) content from Reddit. Each step writes its output to disk, allowing easy reruns of individual phases and inspection of intermediate results.

---

## 1. **Fetching**
Extract relevant threads and top-level comments from Reddit using PRAW. Save raw Reddit data locally:

- `data/threads/YYYY-MM.json`
- `data/comments/YYYY-MM.json`

Each file includes metadata (e.g., extraction time, thread/comment counts) and raw Reddit content.

---

## 2. **Extraction**
Parse downloaded comment bodies to identify product mentions:

- `razor`
- `blade`
- `brush`
- `soap`

Convert each comment into a structured "shave" record. Save to:

- `data/extracted/YYYY-MM.json`

Fields include metadata (`id`, `author`, `created_utc`, etc.) and raw extracted values.

---

## 3. **Matching**
Match extracted product names to known item catalogs to normalize naming:

- `Karve CB` → `Karve Christopher Bradley`
- `RR GC .84` → `RazoRock Game Changer 0.84`

Track original values, match results, and confidence levels. **Preserves all catalog specifications** (e.g., straight razor grind, width, point type from YAML catalog). Save to:

- `data/matched/YYYY-MM.json`

---

## 4. **Field Metadata Enrichment**
Analyze matched field values to extract structured metadata that benefits from knowing the identified product first, such as:

- Blade usage count (e.g., `Astra SP (3)`)
- Straight razor specifications (grind, width as string fraction, point type; e.g., grind: "full hollow", width: "15/16", point: "barbers_notch").
  - Grind types: full hollow, extra hollow, pretty hollow, half hollow, quarter hollow, three quarter hollow, wedge, near wedge, frameback
  - Width: string fraction (e.g., "6/8", "15/16", "3/4", "1.0")
  - Point: round, square, french, spanish, barbers_notch, spear, spike (with 'tip' as synonym for 'point')
  - Only applies to razors with format: Straight
- DE razor plate information (Game Changer gaps, Christopher Bradley plates, Blackbird plates)
  - Game Changer: gap (.68, .76, .84, 1.05), variant (OC, JAWS)
  - Christopher Bradley: plate (A-G), material (brass, copper, stainless)
  - Blackbird: plate (Standard, Lite, OC/Open Comb)
  - Super Speed: tip color (Red, Blue, Black), tip variant (Flare/Flair)

Uses an extensible enricher strategy pattern for sophisticated analysis. Save to:

- `data/enriched/YYYY-MM.json`

**Detailed specification**: See [Enrich Phase Specification](enrich_phase_spec.md)

---

## 5. **Aggregation**
Summarize enriched product data for downstream reporting:

- Usage counts by brand/model
- Most-used products
- User statistics
- Product category summaries

Save aggregate summaries to:

- `data/aggregated/YYYY-MM.json`

**Detailed specification**: See [Aggregate Phase Specification](aggregate_phase_spec.md)

---

## 6. **Report Generation**
Generate human-readable summaries for publication on r/wetshaving. Include product rankings, trends, and commentary excerpts. Save reports to:

- `reports/YYYY-MM.md`
- `reports/YYYY-MM-assets/`

---

Each step is isolated and writes its output to disk, enabling traceable processing and modular development.

Additional steps may be introduced as the project evolves.

This specification defines the structure, configuration, and operational behavior of the Shave of the Day (SOTD) pipeline for extracting, normalizing, and reporting shaving-related content from Reddit's r/wetshaving community.

## Phase 0: Project Setup

### 📄 Environment
- Python version: **3.11.8**
- Type checking: **Pyright** (`typeCheckingMode: "standard"`)
- Code formatting: **Black**
- Linting: **Ruff**v
- Testing: **Pytest + Pytest-Cov**
- Credentials: **praw.ini** (section name set via SOTD_REDDIT_SITE, default "sotd_bot")

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
│   ├── extract/
│   │   └── ...
│   ├── match/
│   │   └── ...
│   ├── enrich/
│   │   ├── run.py
│   │   ├── enrich.py
│   │   ├── base_enricher.py
│   │   └── ...
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
exclude = ["data", "tests", ".venv", "venv"]

[tool.ruff.lint]
select = ["E", "F", "I"]

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]
```

### 📁 .gitignore
```
__pycache__/
*.pyc
venv/
.venv/
.env/
.vscode/
.coverage
coverage/
htmlcov/
data/
```

### 📂 Makefile
```makefile
.PHONY: all lint format ruff-format typecheck test coverage fetch

all: lint format typecheck test

# Ruff linting
lint:
	ruff check .

# Ruff auto‑formatter then Black
ruff-format:
	ruff format .

format: ruff-format
	black .

typecheck:
	pyright

test:
	pytest tests/

coverage:
	pytest --cov=sotd --cov-report=term-missing tests/

fetch:
	python -m sotd.fetch.run --month 2025-05 --debug
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

## 📌 Version History

### v1.0 – Initial MVP Extraction Pipeline (2025-05-23)
This version marks the completion of the minimal viable product for the Extraction phase of the SOTD pipeline.

**Highlights:**
- Added field extractors for `razor`, `blade`, `brush`, and `soap`, using strict markdown pattern: `* **Field:** Value`
- Implemented comment-level parsing to generate structured shave records
- Batched extraction per month from `data/comments/YYYY-MM.json`
- Generated enriched metadata including field coverage and record counts
- Saved outputs to `data/extracted/YYYY-MM.json` with meta, data, and skipped sections
- Built CLI entry point with `--month` and `--debug` options
- Added full unit test coverage and CLI integration test
