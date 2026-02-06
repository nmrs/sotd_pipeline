#!/usr/bin/env python3
"""Auto-assign WSDB slugs when a pipeline soap has exactly one 100% match.

Uses the same catalog batch analysis as the WSDB Alignment Analyzer (threshold=1.0,
mode=brand_scent). For each pipeline soap with exactly one match and that match at
100% confidence, writes the match's slug to data/soaps.yaml under that brand/scent.

Respects non_matches and skips scents that already have a wsdb_slug (batch analysis
excludes them from results).

Recommendation: run with --dry-run first to see what would be assigned, then run
without --dry-run to apply changes.
"""

import argparse
import asyncio
import sys
from pathlib import Path

import yaml

# Add project root to path so we can import from webui.api
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def _filter_single_100_results(pipeline_results: list) -> list[dict]:
    """Return entries that have exactly one match at 100% confidence.

    We only consider 100% matches. The API may also include pattern matches at 95%
    in the same list; we ignore those and require exactly one match with
    confidence == 100, then use that match's slug.
    """
    out = []
    for r in pipeline_results:
        matches = r.get("matches") or []
        hundred_pct = [m for m in matches if m.get("confidence") == 100]
        if len(hundred_pct) != 1:
            continue
        m = hundred_pct[0]
        slug = (m.get("details") or {}).get("slug")
        if not slug:
            continue
        out.append(r)
    return out


async def _run_analysis(limit: int):
    from webui.api.wsdb_alignment import run_batch_analyze

    return await run_batch_analyze(
        threshold=1.0,
        limit=limit,
        mode="brand_scent",
        brand_threshold=0.8,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Auto-assign WSDB slugs for pipeline soaps with exactly one 100%% match."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print what would be assigned; do not modify data/soaps.yaml",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=15000,
        metavar="N",
        help="Max pipeline soaps to analyze (default: 15000)",
    )
    args = parser.parse_args()

    print("Running batch analysis (threshold=1.0, mode=brand_scent)...")
    try:
        result = asyncio.run(_run_analysis(limit=args.limit))
    except Exception as e:
        print(f"Batch analysis failed: {e}", file=sys.stderr)
        return 1

    pipeline_results = result.get("pipeline_results") or []
    candidates = _filter_single_100_results(pipeline_results)
    print(f"Found {len(candidates)} pipeline soaps with exactly one 100% match.")

    if not candidates:
        print("Nothing to assign.")
        return 0

    soaps_file = project_root / "data" / "soaps.yaml"
    if not soaps_file.exists():
        print(f"Error: {soaps_file} not found", file=sys.stderr)
        return 1

    with soaps_file.open("r", encoding="utf-8") as f:
        soaps_data = yaml.safe_load(f) or {}

    assigned = 0
    skipped = 0
    for r in candidates:
        brand = r.get("source_brand") or ""
        scent = r.get("source_scent") or ""
        hundred_pct = [m for m in (r.get("matches") or []) if m.get("confidence") == 100]
        slug = (hundred_pct[0].get("details") or {}).get("slug") if hundred_pct else ""
        slug = slug or ""
        if not brand or not scent or not slug:
            skipped += 1
            continue
        if brand not in soaps_data:
            print(f"  Skip (brand not in catalog): {brand} - {scent}", file=sys.stderr)
            skipped += 1
            continue
        brand_data = soaps_data[brand]
        if not isinstance(brand_data, dict) or "scents" not in brand_data:
            print(f"  Skip (no scents): {brand} - {scent}", file=sys.stderr)
            skipped += 1
            continue
        if scent not in brand_data["scents"]:
            print(f"  Skip (scent not in catalog): {brand} - {scent}", file=sys.stderr)
            skipped += 1
            continue
        scent_data = brand_data["scents"][scent]
        if not isinstance(scent_data, dict):
            scent_data = {}
            brand_data["scents"][scent] = scent_data
        if scent_data.get("wsdb_slug") == slug:
            skipped += 1
            continue
        print(f"  {'Would assign' if args.dry_run else 'Assign'}: {brand} - {scent} -> {slug}")
        scent_data["wsdb_slug"] = slug
        assigned += 1

    if args.dry_run:
        print(f"\nDry run: would assign {assigned} slug(s). Run without --dry-run to apply.")
        return 0

    if assigned == 0:
        print("No assignments made.")
        return 0

    temp_file = soaps_file.with_suffix(".tmp")
    with temp_file.open("w", encoding="utf-8") as f:
        yaml.dump(soaps_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    temp_file.replace(soaps_file)
    print(f"\nAssigned {assigned} slug(s) to {soaps_file}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
