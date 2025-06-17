import argparse
import json
import subprocess
from pathlib import Path

from tqdm import tqdm

from sotd.cli_utils.date_span import month_span
from sotd.match.blade_matcher import BladeMatcher
from sotd.match.brush_matcher import BrushMatcher
from sotd.match.razor_matcher import RazorMatcher
from sotd.match.soap_matcher import SoapMatcher


def is_razor_matched(record: dict) -> bool:
    return (
        isinstance(record.get("razor"), dict)
        and isinstance(record["razor"].get("matched"), dict)
        and bool(record["razor"]["matched"].get("manufacturer"))
    )


def is_blade_matched(record: dict) -> bool:
    return (
        isinstance(record.get("blade"), dict)
        and isinstance(record["blade"].get("matched"), dict)
        and bool(record["blade"]["matched"].get("brand"))
    )


def is_soap_matched(record: dict) -> bool:
    return (
        isinstance(record.get("soap"), dict)
        and isinstance(record["soap"].get("matched"), dict)
        and bool(record["soap"]["matched"].get("maker"))
    )


def is_brush_matched(record: dict) -> bool:
    return (
        isinstance(record.get("brush"), dict)
        and isinstance(record["brush"].get("matched"), dict)
        and bool(record["brush"]["matched"].get("brand"))
    )


def match_record(
    record: dict,
    razor_matcher: RazorMatcher,
    blade_matcher: BladeMatcher,
    soap_matcher: SoapMatcher,
    brush_matcher: BrushMatcher,
) -> dict:
    result = record.copy()
    if "razor" in result:
        result["razor"] = razor_matcher.match(result["razor"])
    if "blade" in result:
        result["blade"] = blade_matcher.match(result["blade"])
    if "soap" in result:
        result["soap"] = soap_matcher.match(result["soap"])
    if "brush" in result:
        result["brush"] = brush_matcher.match(result["brush"])
    return result


def run_match(args):
    base_path = Path(args.out_dir)
    razor_matcher = RazorMatcher()
    blade_matcher = BladeMatcher()
    soap_matcher = SoapMatcher()
    brush_matcher = BrushMatcher()

    for year, month in tqdm(month_span(args), desc="Months", unit="month"):
        in_path = base_path / "extracted" / f"{year:04d}-{month:02d}.json"
        out_path = base_path / "matched" / f"{year:04d}-{month:02d}.json"

        if not in_path.exists():
            if args.debug:
                print(f"Skipping missing input: {in_path}")
            continue

        with in_path.open("r", encoding="utf-8") as f:
            data = json.load(f).get("data", [])
            if not isinstance(data, list):
                raise ValueError(
                    f"Unexpected JSON format in {in_path}. Expected a list of records under 'data'."
                )

        processed = [
            match_record(record, razor_matcher, blade_matcher, soap_matcher, brush_matcher)
            for record in tqdm(data, desc=f"{year}-{month:02d}", unit="record")
        ]

        razor_matches = sum(1 for r in processed if is_razor_matched(r))
        blade_matches = sum(1 for r in processed if is_blade_matched(r))
        soap_matches = sum(1 for r in processed if is_soap_matched(r))
        brush_matches = sum(1 for r in processed if is_brush_matched(r))
        no_matches = sum(
            1
            for r in processed
            if not (
                is_razor_matched(r)
                or is_blade_matched(r)
                or is_soap_matched(r)
                or is_brush_matched(r)
            )
        )

        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as f:
            output = {
                "data": processed,
                "meta": {
                    "month": f"{year:04d}-{month:02d}",
                    "records_input": len(data),
                    "record_count": len(processed),
                    "razor_matches": razor_matches,
                    "blade_matches": blade_matches,
                    "soap_matches": soap_matches,
                    "brush_matches": brush_matches,
                    "no_matches": no_matches,
                    "fields": ["razor", "blade", "soap", "brush"],
                },
            }
            json.dump(output, f, ensure_ascii=False, indent=2)


def run_analysis(args):
    for year, month in month_span(args):
        matched_path = Path(args.out_dir) / "matched" / f"{year:04d}-{month:02d}.json"
        if matched_path.exists():
            subprocess.run(
                ["python", "sotd/match/tools/analyze_unmatched_razors.py", str(matched_path)],
                check=True,
            )
        elif args.debug:
            print(f"Skipping missing file: {matched_path}")


def main(argv=None):
    p = argparse.ArgumentParser(description="Match razors and blades from extracted SOTD data")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--month", type=str, help="e.g., 2025-04")
    g.add_argument("--year", type=int, help="e.g., 2025 (runs all months in that year)")
    g.add_argument("--range", type=str, help="Format: YYYY-MM:YYYY-MM (inclusive)")
    p.add_argument("--start", type=str, help="Optional: overrides start date (YYYY-MM)")
    p.add_argument("--end", type=str, help="Optional: overrides end date (YYYY-MM)")
    p.add_argument("--out-dir", default="data")
    p.add_argument("--debug", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--mode", choices=["match", "analyze_unmatched_razors"], default="match")

    args = p.parse_args(argv)

    if args.mode == "match":
        run_match(args)
    elif args.mode == "analyze_unmatched_razors":
        run_analysis(args)


if __name__ == "__main__":
    main()
