#!/usr/bin/env python3
"""
Phase 4.1 Step 3: Catalog Quality Assessment

Comprehensive assessment of brush catalog data quality, completeness,
and coverage to understand known vs inferred vs fallback patterns.
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List

import yaml


def load_yaml_catalog(file_path: Path) -> Dict[str, Any]:
    """Load YAML catalog file."""
    with open(file_path, "r") as f:
        return yaml.safe_load(f)


def load_match_data(file_path: Path) -> Dict[str, Any]:
    """Load match data from JSON file."""
    with open(file_path, "r") as f:
        return json.load(f)


def analyze_catalog_completeness_detailed(catalog_data: Dict[str, Any]) -> Dict[str, Any]:
    """Detailed analysis of catalog data completeness by brand and category."""

    # Define field categories for analysis
    field_categories = {
        "core_fields": ["brand", "model"],
        "knot_fields": ["knot_fiber", "knot_size_mm", "loft_mm"],
        "handle_fields": ["handle_material", "handle_color", "handle_shape"],
        "metadata_fields": ["year", "price", "discontinued", "limited_edition", "notes"],
        "quality_fields": ["knot_fiber", "knot_size_mm", "handle_material", "loft_mm"],
    }

    analysis = {
        "brand_completeness": {},
        "field_category_coverage": defaultdict(Counter),
        "completeness_distribution": Counter(),
        "quality_tiers": {
            "complete": [],  # 4+ quality fields
            "substantial": [],  # 3 quality fields
            "moderate": [],  # 2 quality fields
            "basic": [],  # 1 quality field
            "minimal": [],  # 0 quality fields
        },
        "brand_quality_scores": {},
        "coverage_gaps": [],
        "exemplar_entries": {"highest_quality": [], "typical_quality": [], "lowest_quality": []},
    }

    for brand, models in catalog_data.items():
        if not isinstance(models, dict):
            continue

        brand_stats = {
            "total_models": 0,
            "field_coverage": Counter(),
            "quality_scores": [],
            "completeness_levels": Counter(),
        }

        for model_name, model_data in models.items():
            brand_stats["total_models"] += 1

            # Count field coverage by category
            quality_field_count = 0
            total_field_count = 0

            for category, fields in field_categories.items():
                category_count = 0
                for field in fields:
                    has_field = (
                        field in model_data
                        or (field == "brand" and brand)
                        or (field == "model" and model_name)
                    )
                    if has_field and model_data.get(field):
                        category_count += 1
                        brand_stats["field_coverage"][field] += 1
                        total_field_count += 1

                        if field in field_categories["quality_fields"]:
                            quality_field_count += 1

                analysis["field_category_coverage"][category][brand] = category_count

            # Calculate quality tier
            entry_data = {
                "brand": brand,
                "model": model_name,
                "data": model_data,
                "quality_field_count": quality_field_count,
                "total_field_count": total_field_count,
            }

            if quality_field_count >= 4:
                tier = "complete"
            elif quality_field_count == 3:
                tier = "substantial"
            elif quality_field_count == 2:
                tier = "moderate"
            elif quality_field_count == 1:
                tier = "basic"
            else:
                tier = "minimal"

            analysis["quality_tiers"][tier].append(entry_data)
            brand_stats["completeness_levels"][tier] += 1
            brand_stats["quality_scores"].append(quality_field_count)

        # Calculate brand-level quality score
        avg_quality = (
            sum(brand_stats["quality_scores"]) / len(brand_stats["quality_scores"])
            if brand_stats["quality_scores"]
            else 0
        )
        analysis["brand_quality_scores"][brand] = {
            "average_quality_score": avg_quality,
            "total_models": brand_stats["total_models"],
            "field_coverage": dict(brand_stats["field_coverage"]),
            "completeness_distribution": dict(brand_stats["completeness_levels"]),
        }

        analysis["brand_completeness"][brand] = brand_stats

    # Identify exemplar entries
    all_entries = []
    for tier_entries in analysis["quality_tiers"].values():
        all_entries.extend(tier_entries)

    # Sort by quality score for exemplars
    all_entries.sort(key=lambda x: x["quality_field_count"], reverse=True)

    if all_entries:
        analysis["exemplar_entries"]["highest_quality"] = all_entries[:3]
        analysis["exemplar_entries"]["typical_quality"] = all_entries[
            len(all_entries) // 2 - 1 : len(all_entries) // 2 + 2
        ]
        analysis["exemplar_entries"]["lowest_quality"] = all_entries[-3:]

    return analysis


def analyze_coverage_gaps(
    catalog_data: Dict[str, Any], match_data: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Analyze gaps between catalog coverage and actual usage patterns."""

    coverage_analysis = {
        "catalog_brands": set(),
        "match_brands": Counter(),
        "missing_from_catalog": set(),
        "unused_catalog_entries": set(),
        "high_volume_uncataloged": [],
        "low_volume_cataloged": [],
        "coverage_metrics": {},
    }

    # Get catalog brands
    for brand in catalog_data.keys():
        if isinstance(catalog_data[brand], dict):
            coverage_analysis["catalog_brands"].add(brand)

    # Get match brands and volumes
    for record in match_data:
        brush = record.get("brush")
        if not brush:
            continue

        matched = brush.get("matched")
        if not matched:
            continue

        brand = matched.get("brand")
        if brand:
            coverage_analysis["match_brands"][brand] += 1

    # Identify gaps
    match_brand_set = set(coverage_analysis["match_brands"].keys())

    coverage_analysis["missing_from_catalog"] = (
        match_brand_set - coverage_analysis["catalog_brands"]
    )
    coverage_analysis["unused_catalog_entries"] = (
        coverage_analysis["catalog_brands"] - match_brand_set
    )

    # Identify high-volume uncataloged brands (top 25% by volume)
    uncataloged_volumes = [
        (brand, count)
        for brand, count in coverage_analysis["match_brands"].items()
        if brand in coverage_analysis["missing_from_catalog"]
    ]
    uncataloged_volumes.sort(key=lambda x: x[1], reverse=True)

    total_uncataloged = len(uncataloged_volumes)
    high_volume_count = max(1, total_uncataloged // 4)
    coverage_analysis["high_volume_uncataloged"] = uncataloged_volumes[:high_volume_count]

    # Identify low-volume cataloged brands (bottom 25% by volume)
    cataloged_volumes = [
        (brand, coverage_analysis["match_brands"].get(brand, 0))
        for brand in coverage_analysis["catalog_brands"]
        if brand in match_brand_set
    ]
    cataloged_volumes.sort(key=lambda x: x[1])

    total_cataloged = len(cataloged_volumes)
    low_volume_count = max(1, total_cataloged // 4)
    coverage_analysis["low_volume_cataloged"] = cataloged_volumes[:low_volume_count]

    # Calculate coverage metrics
    total_matches = sum(coverage_analysis["match_brands"].values())
    cataloged_matches = sum(
        count
        for brand, count in coverage_analysis["match_brands"].items()
        if brand in coverage_analysis["catalog_brands"]
    )

    coverage_analysis["coverage_metrics"] = {
        "total_catalog_brands": len(coverage_analysis["catalog_brands"]),
        "total_match_brands": len(coverage_analysis["match_brands"]),
        "total_matches": total_matches,
        "cataloged_matches": cataloged_matches,
        "coverage_rate_by_volume": cataloged_matches / total_matches if total_matches > 0 else 0,
        "coverage_rate_by_brands": (
            len(coverage_analysis["catalog_brands"] & match_brand_set) / len(match_brand_set)
            if match_brand_set
            else 0
        ),
        "missing_brands_count": len(coverage_analysis["missing_from_catalog"]),
        "unused_entries_count": len(coverage_analysis["unused_catalog_entries"]),
    }

    return coverage_analysis


def classify_catalog_authority(catalog_data: Dict[str, Any]) -> Dict[str, Any]:
    """Classify catalog entries by authority level and data source quality."""

    # Known manufacturer classification based on industry knowledge
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

    # Established artisan classification (brands with substantial community presence)
    established_artisans = {
        "Declaration Grooming",
        "Chisel & Hound",
        "AP Shave Co",
        "Maggard",
        "Stirling",
        "Wild West Brushworks",
        "Dogwood Handcrafts",
    }

    authority_analysis = {
        "manufacturer_entries": {},
        "established_artisan_entries": {},
        "emerging_artisan_entries": {},
        "unknown_entries": {},
        "authority_distribution": Counter(),
        "quality_by_authority": defaultdict(list),
    }

    for brand, models in catalog_data.items():
        if not isinstance(models, dict):
            continue

        # Classify brand authority
        if brand in known_manufacturers:
            authority = "manufacturer"
            authority_analysis["manufacturer_entries"][brand] = models
        elif brand in established_artisans:
            authority = "established_artisan"
            authority_analysis["established_artisan_entries"][brand] = models
        elif len(models) >= 3:  # Multiple models suggests established artisan
            authority = "emerging_artisan"
            authority_analysis["emerging_artisan_entries"][brand] = models
        else:
            authority = "unknown"
            authority_analysis["unknown_entries"][brand] = models

        authority_analysis["authority_distribution"][authority] += len(models)

        # Analyze quality by authority
        for model_name, model_data in models.items():
            quality_fields = ["knot_fiber", "knot_size_mm", "handle_material", "loft_mm"]
            quality_score = sum(1 for field in quality_fields if model_data.get(field))

            authority_analysis["quality_by_authority"][authority].append(
                {
                    "brand": brand,
                    "model": model_name,
                    "quality_score": quality_score,
                    "data": model_data,
                }
            )

    return authority_analysis


def generate_catalog_quality_report(analysis_results: Dict[str, Any]) -> str:
    """Generate comprehensive catalog quality assessment report."""

    completeness = analysis_results["completeness_analysis"]
    coverage = analysis_results["coverage_analysis"]
    authority = analysis_results["authority_analysis"]

    report = f"""# Phase 4.1 Step 3: Catalog Quality Assessment

**Analysis Date**: {analysis_results["analysis_date"]}  
**Data Sources**: Brush catalogs (brushes.yaml, knots.yaml, handles.yaml) and May 2025 match data  
**Total Catalog Brands**: {len(analysis_results["catalog_brands"]):,}  
**Total Match Brands**: {coverage["coverage_metrics"]["total_match_brands"]:,}

## Executive Summary

### Quality Distribution
- **Complete Entries** (4+ quality fields): 
  {len(completeness["quality_tiers"]["complete"]):,} entries
- **Substantial Entries** (3 quality fields): 
  {len(completeness["quality_tiers"]["substantial"]):,} entries  
- **Moderate Entries** (2 quality fields): 
  {len(completeness["quality_tiers"]["moderate"]):,} entries
- **Basic Entries** (1 quality field): {len(completeness["quality_tiers"]["basic"]):,} entries
- **Minimal Entries** (0 quality fields): {len(completeness["quality_tiers"]["minimal"]):,} entries

### Coverage Metrics
- **Coverage Rate by Volume**: 
  {coverage["coverage_metrics"]["coverage_rate_by_volume"] * 100:.1f}% of 
  matches have catalog entries
- **Coverage Rate by Brands**: 
  {coverage["coverage_metrics"]["coverage_rate_by_brands"] * 100:.1f}% of 
  matched brands are cataloged
- **Missing Brands**: 
  {coverage["coverage_metrics"]["missing_brands_count"]:,} high-volume brands 
  not in catalog
- **Unused Entries**: 
  {coverage["coverage_metrics"]["unused_entries_count"]:,} catalog brands not 
  seen in matches

## Detailed Completeness Analysis

### Quality Tier Distribution

| Quality Tier | Count | Percentage | Definition |
|--------------|-------|------------|------------|
| Complete | {len(completeness["quality_tiers"]["complete"]):,} | 
  {
        (
            len(completeness["quality_tiers"]["complete"])
            / (sum(len(tier) for tier in completeness["quality_tiers"].values()))
        )
        * 100:.1f}% | 
  4+ quality fields (knot_fiber, knot_size_mm, handle_material, loft_mm) |
| Substantial | {len(completeness["quality_tiers"]["substantial"]):,} | 
  {
        (
            len(completeness["quality_tiers"]["substantial"])
            / (sum(len(tier) for tier in completeness["quality_tiers"].values()))
        )
        * 100:.1f}% | 
  3 quality fields |
| Moderate | {len(completeness["quality_tiers"]["moderate"]):,} | 
  {
        (
            len(completeness["quality_tiers"]["moderate"])
            / (sum(len(tier) for tier in completeness["quality_tiers"].values()))
        )
        * 100:.1f}% | 
  2 quality fields |
| Basic | {len(completeness["quality_tiers"]["basic"]):,} | 
  {
        (
            len(completeness["quality_tiers"]["basic"])
            / (sum(len(tier) for tier in completeness["quality_tiers"].values()))
        )
        * 100:.1f}% | 
  1 quality field |
| Minimal | {len(completeness["quality_tiers"]["minimal"]):,} | 
  {
        (
            len(completeness["quality_tiers"]["minimal"])
            / (sum(len(tier) for tier in completeness["quality_tiers"].values()))
        )
        * 100:.1f}% | 
  0 quality fields (brand/model only) |

### Brand Quality Scores

| Brand | Average Quality Score | Total Models | Best Model Quality |
|-------|----------------------|--------------|-------------------|
"""

    # Top brands by quality score
    brand_scores = [
        (brand, data["average_quality_score"], data["total_models"])
        for brand, data in completeness["brand_quality_scores"].items()
    ]
    brand_scores.sort(key=lambda x: x[1], reverse=True)

    for brand, avg_score, model_count in brand_scores[:10]:
        best_score = max(
            completeness["brand_quality_scores"][brand].get("quality_scores", [0]) or [0]
        )
        report += f"| {brand} | {avg_score:.1f} | {model_count} | {best_score} |\n"

    report += """
### Exemplar Entries

#### Highest Quality Entries
"""

    for entry in completeness["exemplar_entries"]["highest_quality"]:
        fields = [
            f
            for f in ["knot_fiber", "knot_size_mm", "handle_material", "loft_mm"]
            if entry["data"].get(f)
        ]
        fields_str = ", ".join(fields)
        report += (
            f"- **{entry['brand']} {entry['model']}**: "
            f"{entry['quality_field_count']} fields ({fields_str})\n"
        )

    report += """
#### Typical Quality Entries
"""

    for entry in completeness["exemplar_entries"]["typical_quality"]:
        fields = [
            f
            for f in ["knot_fiber", "knot_size_mm", "handle_material", "loft_mm"]
            if entry["data"].get(f)
        ]
        fields_str = ", ".join(fields)
        report += (
            f"- **{entry['brand']} {entry['model']}**: "
            f"{entry['quality_field_count']} fields ({fields_str})\n"
        )

    report += """
## Coverage Gap Analysis

### High-Volume Uncataloged Brands
These brands have significant match volume but no catalog entries:

| Brand | Match Count | Percentage of Total Matches |
|-------|-------------|----------------------------|
"""

    total_matches = coverage["coverage_metrics"]["total_matches"]
    for brand, count in coverage["high_volume_uncataloged"]:
        percentage = (count / total_matches) * 100
        report += f"| {brand} | {count:,} | {percentage:.1f}% |\n"

    report += """
### Low-Volume Cataloged Brands
These brands have catalog entries but low match volume:

| Brand | Match Count | Catalog Models |
|-------|-------------|----------------|
"""

    for brand, count in coverage["low_volume_cataloged"]:
        catalog_models = len(analysis_results["catalog_data"].get(brand, {}))
        report += f"| {brand} | {count:,} | {catalog_models} |\n"

    report += """
### Coverage Recommendations

#### High Priority Additions (Missing High-Volume Brands)
"""
    for brand, count in coverage["high_volume_uncataloged"][:5]:
        report += (
            f"1. **{brand}**: {count:,} matches - should be added to catalog "
            f"with full specifications\n"
        )

    report += """
#### Medium Priority Reviews (Low-Volume Cataloged)
"""
    for brand, count in coverage["low_volume_cataloged"][:5]:
        if count == 0:
            report += (
                f"1. **{brand}**: 0 matches - consider removing or verifying correct brand name\n"
            )
        else:
            report += (
                f"1. **{brand}**: {count:,} matches - verify catalog accuracy and completeness\n"
            )

    report += """
## Authority Classification Analysis

### Authority Distribution

| Authority Type | Brands | Total Models | Average Quality Score |
|----------------|--------|--------------|----------------------|
"""

    for authority_type, entries in [
        ("manufacturer", authority["manufacturer_entries"]),
        ("established_artisan", authority["established_artisan_entries"]),
        ("emerging_artisan", authority["emerging_artisan_entries"]),
        ("unknown", authority["unknown_entries"]),
    ]:
        brand_count = len(entries)
        model_count = sum(len(models) for models in entries.values())

        # Calculate average quality score for this authority type
        quality_scores = [
            entry["quality_score"]
            for entry in authority["quality_by_authority"].get(authority_type, [])
        ]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

        authority_title = authority_type.replace("_", " ").title()
        report += f"| {authority_title} | {brand_count} | {model_count} | {avg_quality:.1f} |\n"

    report += """
### Manufacturer Analysis
"""

    if authority["manufacturer_entries"]:
        for brand, models in authority["manufacturer_entries"].items():
            model_count = len(models)
            quality_scores = [
                entry["quality_score"]
                for entry in authority["quality_by_authority"]["manufacturer"]
                if entry["brand"] == brand
            ]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            report += f"- **{brand}**: {model_count} models, {avg_quality:.1f} avg quality\n"
    else:
        report += "- No manufacturer entries found in catalog\n"

    report += """
### Established Artisan Analysis
"""

    if authority["established_artisan_entries"]:
        for brand, models in authority["established_artisan_entries"].items():
            model_count = len(models)
            quality_scores = [
                entry["quality_score"]
                for entry in authority["quality_by_authority"]["established_artisan"]
                if entry["brand"] == brand
            ]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            report += f"- **{brand}**: {model_count} models, {avg_quality:.1f} avg quality\n"
    else:
        report += "- No established artisan entries found in catalog\n"

    report += """
## Quality Classification System for Catalog Entries

Based on this analysis, we can define catalog quality classifications:

### Tier 1: Premium Catalog Entries (Score 85-100)
- **Complete entries** (4+ quality fields) from manufacturer or established artisan brands
- **High authority** + **high completeness** = highest confidence
- **Usage**: Boost match scores by +15-20 points

### Tier 2: Good Catalog Entries (Score 70-84)  
- **Substantial entries** (3 quality fields) from any authority level
- **Moderate entries** (2 quality fields) from manufacturer/established artisan
- **Medium authority** + **good completeness** = good confidence
- **Usage**: Boost match scores by +10-15 points

### Tier 3: Basic Catalog Entries (Score 55-69)
- **Basic entries** (1 quality field) from any authority level
- **Minimal entries** from manufacturer/established artisan
- **Lower completeness** but some catalog presence = basic confidence
- **Usage**: Boost match scores by +5-10 points

### Tier 4: Minimal Catalog Entries (Score 40-54)
- **Minimal entries** (0 quality fields) from emerging/unknown brands
- **Placeholder entries** with brand/model only
- **Limited confidence** but catalog presence noted
- **Usage**: Boost match scores by +0-5 points

### Tier 5: No Catalog Entry (Score 0-39)
- **No catalog presence** for the brand
- **Unknown quality** and specifications
- **No confidence boost** from catalog
- **Usage**: No catalog-based score modification

## Implementation Recommendations

### Immediate Catalog Improvements
1. **Add high-volume missing brands**: Focus on top 10 uncataloged brands first
2. **Complete manufacturer entries**: Prioritize manufacturer brands for full specifications
3. **Verify low-volume entries**: Review accuracy of cataloged brands with 0-2 matches

### Scoring System Integration
1. **Implement catalog quality modifiers**: Use 5-tier system for match score boosts
2. **Authority-based bonuses**: Additional points for manufacturer/established artisan matches
3. **Completeness penalties**: Reduce confidence for minimal catalog entries

### Quality Assurance Priorities
1. **Data validation**: Verify accuracy of existing high-quality entries
2. **Standardization**: Ensure consistent field naming and value formats
3. **Coverage expansion**: Target 80%+ coverage rate by volume for Phase 4.2

---

*This analysis provides the foundation for Phase 4.1 Step 4: User Feedback Pattern Research*
"""

    return report


def main():
    """Main analysis function."""
    # Load data sources
    brushes_file = Path("data/brushes.yaml")
    knots_file = Path("data/knots.yaml")
    handles_file = Path("data/handles.yaml")
    match_file = Path("data/matched/2025-05.json")

    if not brushes_file.exists():
        print(f"Error: Brushes catalog {brushes_file} not found")
        sys.exit(1)
    if not match_file.exists():
        print(f"Error: Match data {match_file} not found")
        sys.exit(1)

    print("Loading brush catalogs...")
    brushes_catalog = load_yaml_catalog(brushes_file)

    # Load additional catalogs if they exist
    additional_catalogs = {}
    if knots_file.exists():
        additional_catalogs["knots"] = load_yaml_catalog(knots_file)
    if handles_file.exists():
        additional_catalogs["handles"] = load_yaml_catalog(handles_file)

    print("Loading match data...")
    match_data = load_match_data(match_file)

    print("Analyzing catalog completeness...")
    completeness_analysis = analyze_catalog_completeness_detailed(brushes_catalog)

    print("Analyzing coverage gaps...")
    coverage_analysis = analyze_coverage_gaps(brushes_catalog, match_data["data"])

    print("Classifying catalog authority...")
    authority_analysis = classify_catalog_authority(brushes_catalog)

    # Compile results
    analysis_results = {
        "analysis_date": "2025-08-08",
        "catalog_brands": list(brushes_catalog.keys()),
        "catalog_data": brushes_catalog,
        "additional_catalogs": additional_catalogs,
        "completeness_analysis": completeness_analysis,
        "coverage_analysis": coverage_analysis,
        "authority_analysis": authority_analysis,
    }

    print("Generating catalog quality report...")
    report = generate_catalog_quality_report(analysis_results)

    # Save report
    output_file = Path("analysis/phase_4_1_catalog_quality_assessment.md")
    with open(output_file, "w") as f:
        f.write(report)

    print(f"Analysis complete! Report saved to: {output_file}")

    # Print summary
    total_entries = sum(len(tier) for tier in completeness_analysis["quality_tiers"].values())
    complete_entries = len(completeness_analysis["quality_tiers"]["complete"])
    coverage_rate = coverage_analysis["coverage_metrics"]["coverage_rate_by_volume"]
    missing_brands = coverage_analysis["coverage_metrics"]["missing_brands_count"]

    print("\nSummary:")
    print(f"- Total catalog entries: {total_entries:,}")
    complete_pct = (complete_entries / total_entries) * 100
    print(f"- Complete entries: {complete_entries:,} ({complete_pct:.1f}%)")
    print(f"- Coverage rate: {coverage_rate * 100:.1f}%")
    print(f"- Missing high-volume brands: {missing_brands:,}")
    print(f"- Authority types: {len(authority_analysis['authority_distribution'])}")


if __name__ == "__main__":
    main()
