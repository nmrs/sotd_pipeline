#!/usr/bin/env python3
"""CLI entry point for mismatch identification tool.

USAGE:
------
To revalidate all entries in correct_matches.yaml against current regex patterns:

    python -m sotd.match.tools.legacy.analyze_mismatches --revalidate-correct-matches

To restrict revalidation to a specific field (razor, blade, brush, or soap):

    python -m sotd.match.tools.legacy.analyze_mismatches --revalidate-correct-matches --field razor

This will:
- Check every entry in correct_matches.yaml
- Report entries that no longer match any regex
- Report entries that now match a different product/model than originally expected
- Summarize results and show tables of problematic entries (first 10 of each type)

Use --clear-correct or --clear-field <field> to reset problematic entries if needed.
"""

from typing import List

from sotd.match.tools.analyzers.mismatch_analyzer import MismatchAnalyzer


def get_parser():
    """Get CLI parser for mismatch identification tool."""
    analyzer = MismatchAnalyzer()
    return analyzer.get_parser()


def run(args) -> None:
    """Run the mismatch identification tool."""
    analyzer = MismatchAnalyzer()
    analyzer.run(args)


def main(argv: List[str] | None = None) -> None:
    """Main entry point for the mismatch identification tool."""
    parser = get_parser()
    args = parser.parse_args(argv)
    run(args)


if __name__ == "__main__":
    main()
