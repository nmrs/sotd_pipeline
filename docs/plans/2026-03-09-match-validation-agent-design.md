# Match Validation Agent Design

**Date**: 2026-03-09
**Status**: Approved

## Problem

After running the match phase, hundreds of non-exact matches per month require manual human review. The workflow is: review matches, approve easy ones, make catalog updates for misses, repeat until near-100% exact match coverage. Brushes take the most time (handle/knot splits), followed by soaps (missing scents). Razors and blades are simpler but still require effort.

## Solution

A Claude Code skill (`/validate-matches`) that uses LLM contextual understanding to:
1. **Verify** non-exact matches — judge whether regex/brand matches are correct
2. **Propose** catalog changes — suggest new scents, patterns, and products for misses

## Architecture

### Invocation

```
/validate-matches --month 2026-02
```

### Orchestration Flow

The skill acts as an orchestrator:

1. Reads `data/matched/YYYY-MM.json`
2. Filters to non-exact entries, partitions by field (razor, blade, brush, soap)
3. Reads the relevant catalog and correct_matches file for each field
4. Dispatches 4 parallel agents (one per field), each receiving:
   - Non-exact entries for that field
   - Field's catalog (e.g., `soaps.yaml`, `brushes.yaml`)
   - Field's correct_matches (e.g., `correct_matches/brush.yaml`)
   - Field-specific instructions (e.g., brush agent gets handle/knot split awareness)
5. Merges agent outputs into `data/verified/YYYY-MM.json` and `data/proposed/YYYY-MM.json`
6. Prints a summary

### Per-Field Agents

Each agent iterates its entries and for each one:

1. Reads the original comment text and the matched result
2. Judges correctness — produces a verdict + confidence + reasoning
3. If match is wrong or missing — checks the catalog for near-misses, proposes a catalog change
4. If product is unknown — uses web search to research it, proposes a new entry with source URL
5. Validates that any proposed regex pattern actually matches the original text before including it

**Agent complexity by field:**
- **Brush** — most complex: handle/knot split awareness, scoring config, largest catalog
- **Soap** — scent gap detection, many missing scent proposals expected
- **Razor** — simpler matching, format awareness (DE/SE/SR)
- **Blade** — simplest, smallest catalog

### Context Management

Each field agent only receives its own field's data and catalogs. This keeps context focused and avoids quality degradation from overloaded context windows.

If a field has many entries, the agent processes them in batches to avoid context limits, writing partial results that the orchestrator merges.

## Output Data Model

### `data/verified/YYYY-MM.json`

Agent judgments on non-exact matches:

```json
{
  "metadata": {
    "month": "2026-02",
    "processed_at": "...",
    "stats": {
      "total_non_exact": 115,
      "verified_correct": 82,
      "needs_review": 18,
      "proposals_generated": 15
    }
  },
  "verifications": [
    {
      "comment_id": "abc123",
      "field": "razor",
      "original": "Karve CB SB-B",
      "matched": {"brand": "Karve", "model": "Christopher Bradley", "format": "DE"},
      "match_type": "regex",
      "verdict": "verified",
      "confidence": 0.95,
      "reasoning": "CB is a well-known abbreviation for Christopher Bradley, SB-B indicates plate variant"
    },
    {
      "comment_id": "def456",
      "field": "brush",
      "original": "Chisel & Hound 28mm B17",
      "matched": {"handle": {"brand": "Chisel & Hound", "model": "Unspecified"}, "knot": {"brand": "Unknown", "model": "B17"}},
      "match_type": "regex",
      "verdict": "needs_review",
      "confidence": 0.4,
      "reasoning": "B17 knot brand unclear - could be Declaration Grooming B17 batch or a model name"
    }
  ]
}
```

### `data/proposed/YYYY-MM.json`

Catalog change proposals:

```json
{
  "metadata": {"month": "2026-02", "processed_at": "...", "proposal_count": 15},
  "proposals": [
    {
      "type": "new_scent",
      "field": "soap",
      "brand": "House of Mammoth",
      "scent": "Cerulean",
      "suggested_pattern": "(?:house of )?mammoth.*cerulean",
      "evidence": ["comment abc123: 'HoM Cerulean'", "comment def456: 'House of Mammoth - Cerulean'"],
      "source_url": "https://houseofmammoth.com/cerulean",
      "confidence": 0.9
    },
    {
      "type": "new_pattern",
      "field": "razor",
      "brand": "Karve",
      "model": "Christopher Bradley",
      "suggested_pattern": "karve.*cb(?:\\s*sb)?",
      "evidence": ["comment xyz: 'Karve CB SB-B'"],
      "confidence": 0.85
    },
    {
      "type": "new_product",
      "field": "razor",
      "brand": "Yates",
      "model": "921-H",
      "suggested_entry": {"format": "DE", "patterns": ["yates.*921"]},
      "evidence": ["comment ghi789: 'Yates 921-H'"],
      "research": "Found on yatesprecision.com - stainless steel DE razor",
      "confidence": 0.75
    }
  ]
}
```

### `data/validation/rejections.json`

Accumulates rejected proposals with human reasons. Not consumed by the agent yet — stored for potential future use as negative examples.

```json
[
  {
    "rejected_at": "...",
    "month": "2026-02",
    "proposal": { "...original proposal object..." },
    "reason": "This is actually a different product"
  }
]
```

## WebUI Changes

### MatchAnalyzer Enhancement

No new page. The existing MatchAnalyzer gets a **source toggle**:
- **Match file** (existing behavior) — shows mismatches from `data/matched/YYYY-MM.json`
- **Agent review** (new) — loads from `data/verified/YYYY-MM.json` and `data/proposed/YYYY-MM.json`

### Agent Review Mode

Displays in the existing table layout with additional columns for agent output (verdict, confidence, reasoning).

**Actions:**
- **Bulk approve** — select multiple verified entries, writes them to `correct_matches/{field}.yaml`
- **Accept proposal** — writes to the appropriate catalog file (`soaps.yaml`, `razors.yaml`, etc.)
- **Edit + Accept** — modify a proposal before applying (e.g., tweak regex pattern)
- **Reject** — dismiss with optional reason, appends to `data/validation/rejections.json`

### New Backend Endpoints

- Writing to catalog YAML files (`soaps.yaml`, `razors.yaml`, `blades.yaml`, `brushes.yaml`) — new
- Writing to `correct_matches/{field}.yaml` — already exists
- Appending to `data/validation/rejections.json` — new

## Agent Requirements

- Proposed regex patterns MUST be tested against the original text before inclusion
- Each verification must include reasoning (not just a verdict)
- Web search should be used for unknown products to gather evidence
- Proposals should follow existing catalog naming conventions (learned from correct_matches context)

## Deferred to v2

- **Rejection consumption** — agent reads `rejections.json` as negative few-shot examples
- **Pattern impact analysis** — UI shows all strings a proposed pattern would match and existing entries it would affect (broad-match detection)
- No changes to the match phase itself — this sits alongside it
