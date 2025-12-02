#!/usr/bin/env python3
"""
Phase 4.1 Step 1: Current Match Distribution Analysis

Analyzes brush match distribution across strategy types, success rates,
and performance patterns in May 2025 data.
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List


def load_match_data(file_path: Path) -> Dict[str, Any]:
    """Load match data from JSON file."""
    with open(file_path, "r") as f:
        return json.load(f)


def analyze_strategy_distribution(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze distribution of brush matching strategies."""
    strategy_counts = Counter()
    match_type_counts = Counter()
    strategy_match_types = defaultdict(Counter)
    total_brushes = 0
    successful_matches = 0

    for record in data:
        brush = record.get("brush")
        if not brush:
            continue

        total_brushes += 1

        # Count strategies
        strategy = brush.get("strategy")
        if strategy:
            strategy_counts[strategy] += 1
            successful_matches += 1

            # Count match types by strategy
            match_type = brush.get("match_type")
            if match_type:
                match_type_counts[match_type] += 1
                strategy_match_types[strategy][match_type] += 1
        else:
            strategy_counts["no_strategy"] += 1

    return {
        "total_brushes": total_brushes,
        "successful_matches": successful_matches,
        "success_rate": successful_matches / total_brushes if total_brushes > 0 else 0,
        "strategy_counts": dict(strategy_counts),
        "match_type_counts": dict(match_type_counts),
        "strategy_match_types": dict(strategy_match_types),
    }


def analyze_performance_patterns(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze performance metrics from metadata."""
    performance = metadata.get("performance", {})
    brush_stats = performance.get("brush_strategy_times", {})
    cache_stats = performance.get("cache_stats", {}).get("brush_matcher", {})

    return {
        "total_processing_time": performance.get("processing_time_seconds", 0),
        "brush_processing_time": performance.get("matcher_times", {}).get("brush", {}),
        "strategy_times": brush_stats,
        "cache_performance": cache_stats,
    }


def analyze_match_patterns(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze patterns in match quality and specificity."""
    pattern_complexity = Counter()
    brand_specificity = Counter()
    handle_knot_patterns = defaultdict(list)

    for record in data:
        brush = record.get("brush")
        if not brush or not brush.get("strategy"):
            continue

        strategy = brush["strategy"]
        matched = brush.get("matched", {})

        # Analyze pattern complexity
        pattern = brush.get("pattern", "")
        if pattern:
            pattern_length = len(pattern)
            if pattern_length < 20:
                pattern_complexity["simple"] += 1
            elif pattern_length < 50:
                pattern_complexity["medium"] += 1
            else:
                pattern_complexity["complex"] += 1

        # Analyze brand specificity
        brand = matched.get("brand")
        if brand:
            brand_specificity[brand] += 1

        # Analyze handle/knot patterns for dual_component strategy
        if strategy == "dual_component":
            handle = matched.get("handle", {})
            knot = matched.get("knot", {})
            handle_brand = handle.get("brand") if handle else None
            knot_brand = knot.get("brand") if knot else None

            handle_knot_patterns[strategy].append(
                {
                    "handle_brand": handle_brand,
                    "knot_brand": knot_brand,
                    "same_brand": (
                        handle_brand == knot_brand if handle_brand and knot_brand else False
                    ),
                }
            )

    return {
        "pattern_complexity": dict(pattern_complexity),
        "brand_specificity": dict(brand_specificity),
        "handle_knot_patterns": dict(handle_knot_patterns),
    }


def generate_analysis_report(analysis_results: Dict[str, Any]) -> str:
    """Generate markdown analysis report."""

    strategy_dist = analysis_results["strategy_distribution"]
    performance = analysis_results["performance"]
    patterns = analysis_results["patterns"]

    report = f"""# Phase 4.1 Step 1: Current Match Distribution Analysis

**Analysis Date**: {analysis_results["analysis_date"]}  
**Data Source**: {analysis_results["data_source"]}  
**Total Records Analyzed**: {analysis_results["total_records"]:,}

## Executive Summary

- **Total Brush Matches**: {strategy_dist["total_brushes"]:,}
- **Successful Matches**: {strategy_dist["successful_matches"]:,}
- **Overall Success Rate**: {strategy_dist["success_rate"]:.1%}
 - **Primary Strategies**: 
   {len(strategy_dist["strategy_counts"])} different strategy types 
   identified

## Strategy Distribution Analysis

### Strategy Usage Statistics

| Strategy | Count | Percentage | Success Rate |
|----------|-------|------------|--------------|
"""

    # Strategy statistics table
    total_successful = strategy_dist["successful_matches"]
    strategy_counts = strategy_dist["strategy_counts"]

    for strategy, count in sorted(strategy_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / strategy_dist["total_brushes"]) * 100
        success_rate = (count / total_successful) * 100 if strategy != "no_strategy" else 0
        report += f"| {strategy} | {count:,} | {percentage:.1f}% | {success_rate:.1f}% |\n"

    report += """
### Match Type Distribution

| Match Type | Count | Percentage |
|------------|-------|------------|
"""

    # Match type statistics
    match_type_counts = strategy_dist["match_type_counts"]
    total_match_types = sum(match_type_counts.values())

    for match_type, count in sorted(match_type_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_match_types) * 100
        report += f"| {match_type} | {count:,} | {percentage:.1f}% |\n"

    report += f"""
## Performance Analysis

### Processing Performance
- **Total Processing Time**: {performance["total_processing_time"]:.2f} seconds
 - **Brush Processing Time**: 
   {performance["brush_processing_time"].get("total_time_seconds", 0):.2f} 
   seconds
 - **Average Time per Brush**: 
   {performance["brush_processing_time"].get("avg_time_seconds", 0):.4f} 
   seconds

### Cache Performance
"""

    cache_stats = performance["cache_performance"]
    # Initialize cache_hit_rate to avoid unbound variable
    cache_hit_rate = 0.0
    if cache_stats:
        cache_size = cache_stats.get("size", 0)
        cache_hits = cache_stats.get("hits", 0)
        cache_misses = cache_stats.get("misses", 0)
        cache_hit_rate = (
            (cache_hits / (cache_hits + cache_misses)) * 100
            if (cache_hits + cache_misses) > 0
            else 0
        )

        report += f"""- **Cache Size**: {cache_size:,} entries
- **Cache Hits**: {cache_hits:,}
- **Cache Misses**: {cache_misses:,}
- **Cache Hit Rate**: {cache_hit_rate:.1f}%
"""

    report += """
## Pattern Analysis

### Pattern Complexity Distribution
"""

    pattern_complexity = patterns["pattern_complexity"]
    total_patterns = sum(pattern_complexity.values())

    for complexity, count in pattern_complexity.items():
        percentage = (count / total_patterns) * 100 if total_patterns > 0 else 0
        report += f"- **{complexity.title()} Patterns**: {count:,} ({percentage:.1f}%)\n"

    report += """
### Top Brands by Match Frequency

| Brand | Matches | Percentage |
|-------|---------|------------|
"""

    brand_specificity = patterns["brand_specificity"]
    total_brand_matches = sum(brand_specificity.values())

    # Show top 10 brands
    for brand, count in sorted(brand_specificity.items(), key=lambda x: x[1], reverse=True)[:10]:
        percentage = (count / total_brand_matches) * 100
        report += f"| {brand} | {count:,} | {percentage:.1f}% |\n"

    report += f"""
## Key Findings and Observations

### Strategy Effectiveness
1. **Primary Strategy**: `{max(strategy_counts.items(), key=lambda x: x[1])[0]}` 
   is the most used strategy ({max(strategy_counts.values()):,} matches)
2. **Strategy Diversity**: 
   {len([s for s in strategy_counts.keys() if s != "no_strategy"])} different 
   strategies are actively used
3. **Success Rate**: {strategy_dist["success_rate"]:.1%} overall success rate 
   indicates effective matching

### Performance Insights
1. **Processing Efficiency**: Average 
   {performance["brush_processing_time"].get("avg_time_seconds", 0) * 1000:.1f}ms 
   per brush match
2. **Cache Effectiveness**: {cache_hit_rate:.1f}% cache hit rate reduces 
   redundant processing
3. **Bottleneck Analysis**: Brush matching takes 
   {
        (
            performance["brush_processing_time"].get("total_time_seconds", 0)
            / performance["total_processing_time"]
        )
        * 100:.1f}% 
   of total processing time

### Quality Indicators
1. **Pattern Specificity**: 
   {pattern_complexity.get("complex", 0):,} complex patterns suggest 
   high specificity
2. **Brand Coverage**: {len(brand_specificity)} unique brands matched across all strategies
3. **Match Type Distribution**: 
   `{max(match_type_counts.items(), key=lambda x: x[1])[0]}` is the 
   primary match type

## Recommendations for Quality Improvements

### High Priority
1. **Strategy Optimization**: Focus on improving 
   `{max(strategy_counts.items(), key=lambda x: x[1])[0]}` strategy 
   (highest usage)
2. **Pattern Enhancement**: 
   {pattern_complexity.get("simple", 0):,} simple patterns could benefit 
   from increased specificity
3. **Cache Optimization**: Consider cache size increase to improve {cache_hit_rate:.1f}% hit rate

### Medium Priority  
1. **Brand-Specific Tuning**: Top brands like 
   `{sorted(brand_specificity.items(), key=lambda x: x[1], reverse=True)[0][0]}` 
   could benefit from specialized handling
2. **Performance Monitoring**: Track strategy-specific performance for optimization opportunities
3. **Match Type Balancing**: Consider rebalancing match types for better quality distribution

### Research Directions
1. **Quality Scoring**: Implement quality scores based on pattern complexity and brand specificity
2. **Strategy Hierarchy**: Establish quality hierarchy based on match confidence and specificity
3. **User Feedback Integration**: Correlate strategy effectiveness with user validation patterns

---

*This analysis provides the foundation for Phase 4.1 Step 2: Quality Indicator Discovery*
"""

    return report


def main():
    """Main analysis function."""
    # Load data
    data_file = Path("data/matched/2025-05.json")
    if not data_file.exists():
        print(f"Error: Data file {data_file} not found")
        sys.exit(1)

    print("Loading match data...")
    match_data = load_match_data(data_file)

    print("Analyzing strategy distribution...")
    strategy_analysis = analyze_strategy_distribution(match_data["data"])

    print("Analyzing performance patterns...")
    performance_analysis = analyze_performance_patterns(match_data["metadata"])

    print("Analyzing match patterns...")
    pattern_analysis = analyze_match_patterns(match_data["data"])

    # Compile results
    analysis_results = {
        "analysis_date": "2025-08-08",
        "data_source": str(data_file),
        "total_records": len(match_data["data"]),
        "strategy_distribution": strategy_analysis,
        "performance": performance_analysis,
        "patterns": pattern_analysis,
    }

    print("Generating analysis report...")
    report = generate_analysis_report(analysis_results)

    # Save report
    output_file = Path("analysis/phase_4_1_match_distribution_analysis.md")
    with open(output_file, "w") as f:
        f.write(report)

    print(f"Analysis complete! Report saved to: {output_file}")

    # Print summary
    print("\nSummary:")
    print(f"- Total brush matches: {strategy_analysis['total_brushes']:,}")
    print(f"- Success rate: {strategy_analysis['success_rate']:.1%}")
    print(f"- Strategies found: {len(strategy_analysis['strategy_counts'])}")
    print(
        f"- Top strategy: {max(strategy_analysis['strategy_counts'].items(), key=lambda x: x[1])}"
    )


if __name__ == "__main__":
    main()
