import argparse
from pathlib import Path

from sotd.cli_utils.date_span import month_span
from sotd.extract.analyze import (
    analyze_common_prefixes,
    analyze_garbage_leading_chars,
    analyze_missing_files,
    analyze_skipped_patterns,
)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Analyze skipped SOTD lines for new extraction patterns"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--month", help="Month to analyze, in YYYY-MM format")
    group.add_argument("--year", help="Year to analyze")
    group.add_argument("--range", help="Range of months, format: YYYY-MM:YYYY-MM")
    parser.add_argument("--start", help="Start month (inclusive), format: YYYY-MM")
    parser.add_argument("--end", help="End month (inclusive), format: YYYY-MM")
    parser.add_argument(
        "--out-dir", default="data/extracted", help="Directory containing extracted files"
    )
    parser.add_argument("--top", type=int, default=20, help="Number of top patterns to show")
    parser.add_argument(
        "--examples", type=int, default=3, help="Number of example lines per pattern"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--mode",
        choices=["skipped", "garbage", "missing", "prefix"],
        default="skipped",
        help="Mode of analysis to perform",
    )

    args = parser.parse_args(argv)
    months = month_span(args)
    files = [Path(args.out_dir) / f"{y:04d}-{m:02d}.json" for y, m in months]

    if not files:
        print("No matching files found.")
        return

    if args.mode == "garbage":
        analyze_garbage_leading_chars(files, top_n=args.top, show_examples=args.examples)
    elif args.mode == "missing":
        analyze_missing_files(files)
    elif args.mode == "prefix":
        analyze_common_prefixes(files, show_examples=args.examples)
    else:
        analyze_skipped_patterns(files, top_n=args.top, show_examples=args.examples)


if __name__ == "__main__":
    main()
