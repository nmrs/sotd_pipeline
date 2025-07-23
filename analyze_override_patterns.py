#!/usr/bin/env python3
"""
Script to analyze naming conventions and patterns in successful thread overrides
"""

import yaml
import re
from pathlib import Path
from urllib.parse import urlparse
from collections import defaultdict


def analyze_thread_overrides():
    """Analyze patterns in thread_overrides.yaml"""
    overrides_file = Path("data/thread_overrides.yaml")

    with open(overrides_file, "r") as f:
        content = f.read()

    # Parse YAML content
    overrides = yaml.safe_load(content)

    # Extract patterns
    patterns = {
        "title_patterns": [],
        "url_patterns": [],
        "date_patterns": [],
        "author_patterns": [],
        "flair_patterns": [],
        "thread_id_patterns": [],
    }

    successful_overrides = []
    missing_dates = []

    for date, urls in overrides.items():
        if isinstance(urls, list) and urls:
            # Successful override
            successful_overrides.append({"date": date, "urls": urls})

            for url in urls:
                # Extract URL components
                parsed = urlparse(url)
                path_parts = parsed.path.split("/")

                # Extract thread ID and title from URL
                if len(path_parts) >= 4:
                    thread_id = path_parts[3]
                    title_slug = path_parts[4] if len(path_parts) > 4 else ""

                    patterns["thread_id_patterns"].append(thread_id)
                    patterns["url_patterns"].append(title_slug)
        else:
            # Missing date
            missing_dates.append(date)

    return patterns, successful_overrides, missing_dates


def analyze_title_patterns(overrides):
    """Analyze title patterns from successful overrides"""
    title_analysis = {
        "day_patterns": defaultdict(int),
        "date_format_patterns": defaultdict(int),
        "special_patterns": defaultdict(int),
        "author_patterns": defaultdict(int),
    }

    for override in overrides:
        for url in override["urls"]:
            # Extract title from URL slug
            title_slug = url.split("/")[-2] if url.endswith("/") else url.split("/")[-1]

            # Analyze day patterns
            day_patterns = [
                "sunday",
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sun",
                "mon",
                "tue",
                "wed",
                "thu",
                "fri",
                "sat",
            ]

            for day in day_patterns:
                if day in title_slug.lower():
                    title_analysis["day_patterns"][day] += 1
                    break

            # Analyze date format patterns
            date_patterns = [
                r"\d{1,2}_\d{1,2}_\d{4}",  # 5_1_2016
                r"\d{1,2}_\d{1,2}",  # 5_1
                r"\d{4}_\d{1,2}_\d{1,2}",  # 2016_5_1
                r"[a-z]{3}_\d{1,2}",  # may_01
                r"\d{1,2}_[a-z]{3}",  # 01_may
            ]

            for pattern in date_patterns:
                if re.search(pattern, title_slug.lower()):
                    title_analysis["date_format_patterns"][pattern] += 1
                    break

            # Analyze special patterns
            special_patterns = [
                "theme_thursday",
                "sotd_thread",
                "daily_sotd",
                "shave_of_the_day",
                "thread",
                "sotd",
                "motd",
            ]

            for pattern in special_patterns:
                if pattern in title_slug.lower():
                    title_analysis["special_patterns"][pattern] += 1
                    break

    return title_analysis


def analyze_thread_id_patterns(overrides):
    """Analyze thread ID patterns"""
    thread_ids = []

    for override in overrides:
        for url in override["urls"]:
            # Extract thread ID from URL
            path_parts = url.split("/")
            if len(path_parts) >= 4:
                thread_id = path_parts[3]
                thread_ids.append(thread_id)

    # Analyze thread ID characteristics
    id_analysis = {
        "length_distribution": defaultdict(int),
        "character_patterns": defaultdict(int),
        "prefix_patterns": defaultdict(int),
    }

    for thread_id in thread_ids:
        # Length analysis
        id_analysis["length_distribution"][len(thread_id)] += 1

        # Character pattern analysis
        if thread_id.isalnum():
            if thread_id.isalpha():
                id_analysis["character_patterns"]["alpha_only"] += 1
            elif thread_id.isdigit():
                id_analysis["character_patterns"]["numeric_only"] += 1
            else:
                id_analysis["character_patterns"]["alphanumeric"] += 1
        else:
            id_analysis["character_patterns"]["special_chars"] += 1

        # Prefix analysis (first few characters)
        if len(thread_id) >= 2:
            prefix = thread_id[:2]
            id_analysis["prefix_patterns"][prefix] += 1

    return id_analysis


def main():
    print("Analyzing naming conventions and patterns in successful thread overrides...")
    print("=" * 70)

    # Analyze overrides
    patterns, successful_overrides, missing_dates = analyze_thread_overrides()

    print("📊 ANALYSIS SUMMARY:")
    print(f"Successful overrides: {len(successful_overrides)}")
    print(f"Missing dates: {len(missing_dates)}")
    print(f"Total dates analyzed: {len(successful_overrides) + len(missing_dates)}")

    # Analyze title patterns
    title_analysis = analyze_title_patterns(successful_overrides)

    print("\n📝 TITLE PATTERN ANALYSIS:")
    print("Day patterns found:")
    for day, count in sorted(
        title_analysis["day_patterns"].items(), key=lambda x: x[1], reverse=True
    ):
        print(f"  - {day}: {count} occurrences")

    print("\nDate format patterns found:")
    for pattern, count in sorted(
        title_analysis["date_format_patterns"].items(), key=lambda x: x[1], reverse=True
    ):
        print(f"  - {pattern}: {count} occurrences")

    print("\nSpecial patterns found:")
    for pattern, count in sorted(
        title_analysis["special_patterns"].items(), key=lambda x: x[1], reverse=True
    ):
        print(f"  - {pattern}: {count} occurrences")

    # Analyze thread ID patterns
    id_analysis = analyze_thread_id_patterns(successful_overrides)

    print("\n🆔 THREAD ID ANALYSIS:")
    print("Length distribution:")
    for length, count in sorted(id_analysis["length_distribution"].items()):
        print(f"  - {length} chars: {count} threads")

    print("\nCharacter patterns:")
    for pattern, count in sorted(
        id_analysis["character_patterns"].items(), key=lambda x: x[1], reverse=True
    ):
        print(f"  - {pattern}: {count} threads")

    print("\nMost common prefixes:")
    for prefix, count in sorted(
        id_analysis["prefix_patterns"].items(), key=lambda x: x[1], reverse=True
    )[:10]:
        print(f"  - {prefix}: {count} threads")

    # Analyze by year
    year_analysis = defaultdict(list)
    for override in successful_overrides:
        # Extract year from date string (YYYY-MM-DD format)
        if isinstance(override["date"], str):
            year = override["date"].split("-")[0]
        else:
            # Handle datetime.date object
            year = str(override["date"].year)
        year_analysis[year].append(override)

    print("\n📅 ANALYSIS BY YEAR:")
    for year in sorted(year_analysis.keys()):
        overrides = year_analysis[year]
        print(f"  {year}: {len(overrides)} overrides")

        # Show sample URLs for each year
        for override in overrides[:3]:  # Show first 3
            print(f"    - {override['date']}: {override['urls'][0]}")

    # Generate search strategies
    print("\n🔍 RECOMMENDED SEARCH STRATEGIES:")
    day_patterns = [day for day, count in title_analysis["day_patterns"].items() if count > 2]
    print(f"1. Focus on day-based searches: {', '.join(day_patterns)}")

    date_patterns = [
        pattern for pattern, count in title_analysis["date_format_patterns"].items() if count > 1
    ]
    print(f"2. Use date format patterns: {', '.join(date_patterns)}")

    special_patterns = [
        pattern for pattern, count in title_analysis["special_patterns"].items() if count > 1
    ]
    print(f"3. Include special patterns: {', '.join(special_patterns)}")

    most_common_pattern = max(id_analysis["character_patterns"].items(), key=lambda x: x[1])[0]
    print(f"4. Thread ID patterns: Most are {most_common_pattern}")


if __name__ == "__main__":
    main()
