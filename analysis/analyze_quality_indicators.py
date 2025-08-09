#!/usr/bin/env python3
"""
Phase 4.1 Step 2: Quality Indicator Discovery

Analyzes catalog and match data to identify patterns that indicate
high-quality, medium-quality, and low-quality brush matches.
"""

import json
import yaml
from collections import defaultdict, Counter
from pathlib import Path
import sys
from typing import Dict, List, Any, Optional, Set


def load_yaml_catalog(file_path: Path) -> Dict[str, Any]:
    """Load YAML catalog file."""
    with open(file_path, "r") as f:
        return yaml.safe_load(f)


def load_match_data(file_path: Path) -> Dict[str, Any]:
    """Load match data from JSON file."""
    with open(file_path, "r") as f:
        return json.load(f)


def analyze_catalog_completeness(catalog_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze completeness of catalog entries."""
    completeness_stats = {
        "total_entries": 0,
        "complete_entries": 0,
        "partial_entries": 0,
        "minimal_entries": 0,
        "completeness_by_brand": defaultdict(list),
        "field_coverage": Counter(),
        "quality_examples": {"complete": [], "partial": [], "minimal": []},
    }

    # Define required fields for completeness assessment
    core_fields = ["brand", "model"]
    quality_fields = ["knot_fiber", "knot_size_mm", "handle_material", "loft_mm"]
    optional_fields = ["year", "price", "discontinued", "notes"]

    for brand, models in catalog_data.items():
        if isinstance(models, dict):
            for model_name, model_data in models.items():
                completeness_stats["total_entries"] += 1

                # Count field coverage
                for field in core_fields + quality_fields + optional_fields:
                    if (
                        field in model_data
                        or (field == "brand" and brand)
                        or (field == "model" and model_name)
                    ):
                        completeness_stats["field_coverage"][field] += 1

                # Assess completeness level
                has_core = all(
                    model_data.get(field)
                    or (field == "brand" and brand)
                    or (field == "model" and model_name)
                    for field in core_fields
                )
                quality_field_count = sum(1 for field in quality_fields if model_data.get(field))

                entry = {
                    "brand": brand,
                    "model": model_name,
                    "data": model_data,
                    "quality_field_count": quality_field_count,
                }

                if has_core and quality_field_count >= 3:
                    completeness_stats["complete_entries"] += 1
                    completeness_stats["completeness_by_brand"][brand].append("complete")
                    if len(completeness_stats["quality_examples"]["complete"]) < 5:
                        completeness_stats["quality_examples"]["complete"].append(entry)
                elif has_core and quality_field_count >= 1:
                    completeness_stats["partial_entries"] += 1
                    completeness_stats["completeness_by_brand"][brand].append("partial")
                    if len(completeness_stats["quality_examples"]["partial"]) < 5:
                        completeness_stats["quality_examples"]["partial"].append(entry)
                else:
                    completeness_stats["minimal_entries"] += 1
                    completeness_stats["completeness_by_brand"][brand].append("minimal")
                    if len(completeness_stats["quality_examples"]["minimal"]) < 5:
                        completeness_stats["quality_examples"]["minimal"].append(entry)

    return completeness_stats


def analyze_pattern_specificity(match_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze pattern specificity and match confidence indicators."""
    specificity_analysis = {
        "pattern_categories": Counter(),
        "brand_pattern_quality": defaultdict(list),
        "strategy_specificity": defaultdict(list),
        "confidence_indicators": {
            "high_confidence": [],
            "medium_confidence": [],
            "low_confidence": [],
        },
    }

    for record in match_data:
        brush = record.get("brush")
        if not brush or not brush.get("strategy"):
            continue

        strategy = brush["strategy"]
        pattern = brush.get("pattern", "")
        matched = brush.get("matched", {})
        brand = matched.get("brand", "")

        # Categorize pattern complexity
        pattern_length = len(pattern)
        regex_complexity = (
            pattern.count("(") + pattern.count("[") + pattern.count("?") + pattern.count("*")
        )

        if regex_complexity >= 5 or pattern_length > 50:
            category = "high_specificity"
        elif regex_complexity >= 2 or pattern_length > 20:
            category = "medium_specificity"
        else:
            category = "low_specificity"

        specificity_analysis["pattern_categories"][category] += 1
        specificity_analysis["strategy_specificity"][strategy].append(category)

        if brand:
            specificity_analysis["brand_pattern_quality"][brand].append(category)

        # Assess confidence based on multiple factors
        confidence_score = 0
        confidence_factors = []

        # Strategy-based confidence
        if strategy == "known_brush":
            confidence_score += 3
            confidence_factors.append("known_brush_strategy")
        elif strategy in ["omega_semogue", "zenith"]:
            confidence_score += 2
            confidence_factors.append("manufacturer_specific_strategy")
        elif strategy == "dual_component":
            confidence_score += 1
            confidence_factors.append("dual_component_strategy")

        # Pattern specificity confidence
        if category == "high_specificity":
            confidence_score += 2
            confidence_factors.append("high_specificity_pattern")
        elif category == "medium_specificity":
            confidence_score += 1
            confidence_factors.append("medium_specificity_pattern")

        # Match completeness confidence
        handle = matched.get("handle", {})
        knot = matched.get("knot", {})

        if handle and knot:
            if handle.get("brand") and knot.get("brand"):
                confidence_score += 1
                confidence_factors.append("complete_handle_knot_brands")
            if knot.get("fiber") and knot.get("knot_size_mm"):
                confidence_score += 1
                confidence_factors.append("complete_knot_specs")

        # Categorize by confidence level
        entry = {
            "original": brush.get("original", ""),
            "strategy": strategy,
            "brand": brand,
            "confidence_score": confidence_score,
            "confidence_factors": confidence_factors,
            "pattern_category": category,
        }

        if confidence_score >= 5:
            specificity_analysis["confidence_indicators"]["high_confidence"].append(entry)
        elif confidence_score >= 3:
            specificity_analysis["confidence_indicators"]["medium_confidence"].append(entry)
        else:
            specificity_analysis["confidence_indicators"]["low_confidence"].append(entry)

    return specificity_analysis


def analyze_brand_authority(
    catalog_data: Dict[str, Any], match_data: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Analyze brand authority and manufacturer vs artisan patterns."""
    brand_analysis = {
        "catalog_brands": set(),
        "match_brands": Counter(),
        "manufacturer_brands": set(),
        "artisan_brands": set(),
        "authority_classification": {},
        "coverage_analysis": {},
    }

    # Get catalog brands
    for brand in catalog_data.keys():
        if isinstance(catalog_data[brand], dict):
            brand_analysis["catalog_brands"].add(brand)

    # Known manufacturer brands (from domain knowledge)
    known_manufacturers = {
        "Omega",
        "Semogue",
        "Simpson",
        "Kent",
        "Vulfix",
        "Zenith",
        "Muhle",
        "Edwin Jagger",
        "Parker",
        "Merkur",
        "Proraso",
    }

    # Get match brands and classify
    for record in match_data:
        brush = record.get("brush")
        if not brush:
            continue

        matched = brush.get("matched")
        if not matched:
            continue

        brand = matched.get("brand")

        if brand:
            brand_analysis["match_brands"][brand] += 1

            # Classify brand authority
            if brand in known_manufacturers:
                brand_analysis["manufacturer_brands"].add(brand)
                brand_analysis["authority_classification"][brand] = "manufacturer"
            elif brand in brand_analysis["catalog_brands"]:
                brand_analysis["authority_classification"][brand] = "cataloged_artisan"
            else:
                brand_analysis["artisan_brands"].add(brand)
                brand_analysis["authority_classification"][brand] = "uncataloged_artisan"

    # Coverage analysis
    cataloged_matches = sum(
        count
        for brand, count in brand_analysis["match_brands"].items()
        if brand in brand_analysis["catalog_brands"]
    )
    total_matches = sum(brand_analysis["match_brands"].values())

    brand_analysis["coverage_analysis"] = {
        "total_catalog_brands": len(brand_analysis["catalog_brands"]),
        "total_match_brands": len(brand_analysis["match_brands"]),
        "manufacturer_brands_count": len(brand_analysis["manufacturer_brands"]),
        "cataloged_artisan_count": len(
            [
                b
                for b, c in brand_analysis["authority_classification"].items()
                if c == "cataloged_artisan"
            ]
        ),
        "uncataloged_artisan_count": len(brand_analysis["artisan_brands"]),
        "catalog_coverage_rate": cataloged_matches / total_matches if total_matches > 0 else 0,
    }

    return brand_analysis


def generate_quality_indicators_report(analysis_results: Dict[str, Any]) -> str:
    """Generate quality indicators taxonomy report."""

    catalog_analysis = analysis_results["catalog_completeness"]
    pattern_analysis = analysis_results["pattern_specificity"]
    brand_analysis = analysis_results["brand_authority"]

    report = f"""# Phase 4.1 Step 2: Quality Indicators Taxonomy

**Analysis Date**: {analysis_results["analysis_date"]}  
**Data Sources**: Brush catalogs and May 2025 match data  
**Total Catalog Entries**: {catalog_analysis["total_entries"]:,}  
**Total Match Records**: {analysis_results["total_matches"]:,}

## Executive Summary

Quality indicators have been identified across three dimensions:
1. **Catalog Completeness**: {catalog_analysis["complete_entries"]:,} complete entries ({(catalog_analysis["complete_entries"] / catalog_analysis["total_entries"]) * 100:.1f}%)
2. **Pattern Specificity**: {pattern_analysis["pattern_categories"]["high_specificity"]} high-specificity patterns identified
3. **Brand Authority**: {brand_analysis["coverage_analysis"]["manufacturer_brands_count"]} manufacturer brands, {brand_analysis["coverage_analysis"]["catalog_coverage_rate"] * 100:.1f}% catalog coverage

## Catalog Completeness Analysis

### Completeness Distribution

| Quality Level | Count | Percentage | Definition |
|---------------|-------|------------|------------|
| Complete | {catalog_analysis["complete_entries"]:,} | {(catalog_analysis["complete_entries"] / catalog_analysis["total_entries"]) * 100:.1f}% | Brand, model + 3+ quality fields |
| Partial | {catalog_analysis["partial_entries"]:,} | {(catalog_analysis["partial_entries"] / catalog_analysis["total_entries"]) * 100:.1f}% | Brand, model + 1-2 quality fields |
| Minimal | {catalog_analysis["minimal_entries"]:,} | {(catalog_analysis["minimal_entries"] / catalog_analysis["total_entries"]) * 100:.1f}% | Brand, model only |

### Field Coverage Analysis

| Field | Coverage | Percentage |
|-------|----------|------------|
"""

    # Field coverage table
    total_entries = catalog_analysis["total_entries"]
    for field, count in catalog_analysis["field_coverage"].most_common():
        percentage = (count / total_entries) * 100
        report += f"| {field} | {count:,} | {percentage:.1f}% |\n"

    report += f"""
### Quality Examples

#### Complete Entries (High Quality)
"""
    for example in catalog_analysis["quality_examples"]["complete"]:
        report += f"- **{example['brand']} {example['model']}**: {example['quality_field_count']} quality fields\n"

    report += f"""
#### Partial Entries (Medium Quality)  
"""
    for example in catalog_analysis["quality_examples"]["partial"]:
        report += f"- **{example['brand']} {example['model']}**: {example['quality_field_count']} quality fields\n"

    report += f"""
## Pattern Specificity Analysis

### Specificity Distribution

| Specificity Level | Count | Percentage | Characteristics |
|-------------------|-------|------------|-----------------|
"""

    total_patterns = sum(pattern_analysis["pattern_categories"].values())
    for category, count in pattern_analysis["pattern_categories"].items():
        percentage = (count / total_patterns) * 100

        if category == "high_specificity":
            chars = "Complex regex, 50+ chars, 5+ operators"
        elif category == "medium_specificity":
            chars = "Moderate regex, 20-50 chars, 2-4 operators"
        else:
            chars = "Simple pattern, <20 chars, <2 operators"

        report += (
            f"| {category.replace('_', ' ').title()} | {count:,} | {percentage:.1f}% | {chars} |\n"
        )

    report += f"""
### Confidence Indicators Analysis

#### High Confidence Matches ({len(pattern_analysis["confidence_indicators"]["high_confidence"])} total)
"""

    # Show top 5 high confidence examples
    for example in pattern_analysis["confidence_indicators"]["high_confidence"][:5]:
        factors = ", ".join(example["confidence_factors"])
        report += f"- **{example['brand']}** ({example['strategy']}): Score {example['confidence_score']} - {factors}\n"

    report += f"""
#### Medium Confidence Matches ({len(pattern_analysis["confidence_indicators"]["medium_confidence"])} total)
"""

    # Show top 5 medium confidence examples
    for example in pattern_analysis["confidence_indicators"]["medium_confidence"][:5]:
        factors = ", ".join(example["confidence_factors"])
        report += f"- **{example['brand']}** ({example['strategy']}): Score {example['confidence_score']} - {factors}\n"

    report += f"""
#### Low Confidence Matches ({len(pattern_analysis["confidence_indicators"]["low_confidence"])} total)
"""

    # Show top 5 low confidence examples
    for example in pattern_analysis["confidence_indicators"]["low_confidence"][:5]:
        factors = (
            ", ".join(example["confidence_factors"])
            if example["confidence_factors"]
            else "No confidence factors"
        )
        report += f"- **{example['brand'] or 'Unknown'}** ({example['strategy']}): Score {example['confidence_score']} - {factors}\n"

    report += f"""
## Brand Authority Analysis

### Authority Classification

| Authority Type | Count | Match Volume | Definition |
|----------------|-------|--------------|------------|
| Manufacturer | {brand_analysis["coverage_analysis"]["manufacturer_brands_count"]} | {sum(brand_analysis["match_brands"][b] for b in brand_analysis["manufacturer_brands"]):,} | Established manufacturers |
| Cataloged Artisan | {brand_analysis["coverage_analysis"]["cataloged_artisan_count"]} | {sum(brand_analysis["match_brands"][b] for b, c in brand_analysis["authority_classification"].items() if c == "cataloged_artisan"):,} | Artisans with catalog entries |
| Uncataloged Artisan | {brand_analysis["coverage_analysis"]["uncataloged_artisan_count"]} | {sum(brand_analysis["match_brands"][b] for b in brand_analysis["artisan_brands"]):,} | Artisans without catalog entries |

### Coverage Analysis

- **Total Brands in Catalog**: {brand_analysis["coverage_analysis"]["total_catalog_brands"]:,}
- **Total Brands in Matches**: {brand_analysis["coverage_analysis"]["total_match_brands"]:,}
- **Catalog Coverage Rate**: {brand_analysis["coverage_analysis"]["catalog_coverage_rate"] * 100:.1f}%

### Top Manufacturer Brands by Volume
"""

    # Top manufacturer brands
    manufacturer_volumes = [
        (brand, brand_analysis["match_brands"][brand])
        for brand in brand_analysis["manufacturer_brands"]
    ]
    manufacturer_volumes.sort(key=lambda x: x[1], reverse=True)

    for brand, volume in manufacturer_volumes[:10]:
        report += f"- **{brand}**: {volume:,} matches\n"

    report += f"""
## Quality Classification System

Based on the analysis, we can define a quality hierarchy:

### Tier 1: Highest Quality (Score 90-100)
- **Known brush strategy** with complete catalog entry
- **High specificity patterns** with manufacturer brands
- **Complete handle/knot specifications** with matching brands
- **Examples**: Established manufacturer brushes with full catalog data

### Tier 2: High Quality (Score 70-89)  
- **Manufacturer-specific strategies** (omega_semogue, zenith)
- **Medium specificity patterns** with cataloged brands
- **Partial specifications** with brand authority
- **Examples**: Manufacturer brushes with partial catalog data

### Tier 3: Medium Quality (Score 50-69)
- **Dual component strategy** with catalog presence
- **Simple patterns** with brand authority
- **Basic brand/model matching** only
- **Examples**: Cataloged artisan brushes

### Tier 4: Low Quality (Score 30-49)
- **Generic strategies** without catalog presence  
- **Simple patterns** without brand authority
- **Incomplete specifications**
- **Examples**: Uncataloged artisan brushes

### Tier 5: Lowest Quality (Score 0-29)
- **No strategy match** (failed matches)
- **No brand identification**
- **No catalog presence**
- **Examples**: Unmatched or severely incomplete entries

## Quality Scoring Recommendations

### Pattern Specificity Modifiers
- **High Specificity**: +15 points
- **Medium Specificity**: +10 points  
- **Low Specificity**: +0 points

### Brand Authority Modifiers
- **Manufacturer Brand**: +20 points
- **Cataloged Artisan**: +10 points
- **Uncataloged Artisan**: +0 points

### Catalog Completeness Modifiers
- **Complete Entry**: +15 points
- **Partial Entry**: +10 points
- **Minimal Entry**: +5 points
- **No Entry**: +0 points

### Strategy Confidence Modifiers
- **Known Brush**: +25 points
- **Manufacturer Specific**: +20 points
- **Dual Component**: +10 points
- **Generic**: +5 points

## Implementation Recommendations

### Immediate Opportunities
1. **Boost known_brush matches**: Currently only 18.6% usage but highest quality
2. **Improve dual_component quality**: 50.6% usage with medium quality potential
3. **Address 29.7% no_strategy failures**: Major quality improvement opportunity

### Scoring System Enhancements
1. **Implement quality modifiers** based on pattern specificity and brand authority
2. **Create catalog completeness bonus** for well-documented brushes
3. **Add manufacturer recognition bonus** for established brands
4. **Implement confidence penalties** for low-specificity matches

### Quality Validation Priorities
1. **Focus on manufacturer brands**: Semogue, Omega, Zenith coverage
2. **Enhance catalog completeness**: Target high-volume brands first
3. **Improve pattern specificity**: Convert simple patterns to medium/high specificity

---

*This analysis provides the foundation for Phase 4.1 Step 3: Catalog Quality Assessment*
"""

    return report


def main():
    """Main analysis function."""
    # Load data sources
    brushes_file = Path("data/brushes.yaml")
    match_file = Path("data/matched/2025-05.json")

    if not brushes_file.exists():
        print(f"Error: Brushes catalog {brushes_file} not found")
        sys.exit(1)
    if not match_file.exists():
        print(f"Error: Match data {match_file} not found")
        sys.exit(1)

    print("Loading brush catalog...")
    brushes_catalog = load_yaml_catalog(brushes_file)

    print("Loading match data...")
    match_data = load_match_data(match_file)

    print("Analyzing catalog completeness...")
    catalog_analysis = analyze_catalog_completeness(brushes_catalog)

    print("Analyzing pattern specificity...")
    pattern_analysis = analyze_pattern_specificity(match_data["data"])

    print("Analyzing brand authority...")
    brand_analysis = analyze_brand_authority(brushes_catalog, match_data["data"])

    # Compile results
    analysis_results = {
        "analysis_date": "2025-08-08",
        "total_matches": len(match_data["data"]),
        "catalog_completeness": catalog_analysis,
        "pattern_specificity": pattern_analysis,
        "brand_authority": brand_analysis,
    }

    print("Generating quality indicators report...")
    report = generate_quality_indicators_report(analysis_results)

    # Save report
    output_file = Path("analysis/phase_4_1_quality_indicators_taxonomy.md")
    with open(output_file, "w") as f:
        f.write(report)

    print(f"Analysis complete! Report saved to: {output_file}")

    # Print summary
    print(f"\nSummary:")
    print(f"- Catalog entries: {catalog_analysis['total_entries']:,}")
    print(
        f"- Complete entries: {catalog_analysis['complete_entries']:,} ({(catalog_analysis['complete_entries'] / catalog_analysis['total_entries']) * 100:.1f}%)"
    )
    print(
        f"- High specificity patterns: {pattern_analysis['pattern_categories']['high_specificity']:,}"
    )
    print(
        f"- Manufacturer brands: {brand_analysis['coverage_analysis']['manufacturer_brands_count']:,}"
    )
    print(
        f"- Catalog coverage: {brand_analysis['coverage_analysis']['catalog_coverage_rate'] * 100:.1f}%"
    )


if __name__ == "__main__":
    main()
