from pathlib import Path

from sotd.cli_utils.base_parser import BaseCLIParser
from sotd.cli_utils.date_span import month_span
from sotd.extract.analyze import (
    analyze_common_prefixes,
    analyze_garbage_leading_chars,
    analyze_missing_files,
    analyze_skipped_patterns,
)


def get_parser() -> BaseCLIParser:
    """Get CLI parser for extract analysis tool."""
    parser = BaseCLIParser(
        description="Analyze skipped SOTD lines for new extraction patterns",
        add_help=True,
    )

    # Add analysis-specific arguments
    parser.add_argument("--top", type=int, default=20, help="Number of top patterns to show")
    parser.add_argument(
        "--examples", type=int, default=3, help="Number of example lines per pattern"
    )
    parser.add_argument(
        "--mode",
        choices=["skipped", "garbage", "missing", "prefix"],
        default="skipped",
        help="Mode of analysis to perform",
    )

    return parser


def run(args) -> None:
    """Run the extract analysis tool."""
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


def main(argv: list[str] | None = None) -> None:
    """Main entry point for the extract analysis tool."""
    parser = get_parser()
    args = parser.parse_args(argv)
    run(args)


if __name__ == "__main__":
    main()
