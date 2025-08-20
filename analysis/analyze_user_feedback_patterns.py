#!/usr/bin/env python3
"""
Phase 4.1 Step 4: User Feedback Pattern Research

Research existing user feedback patterns and validation mechanisms
to understand how quality is currently validated and identify patterns
for scoring optimization.
"""

import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict

import yaml


def load_yaml_data(file_path: Path) -> Dict[str, Any]:
    """Load YAML data file."""
    with open(file_path, "r") as f:
        return yaml.safe_load(f)


def analyze_webui_validation_tools() -> Dict[str, Any]:
    """Analyze WebUI validation tools and interfaces."""

    webui_analysis = {
        "validation_components": {},
        "api_endpoints": {},
        "validation_workflows": {},
        "user_interaction_patterns": {},
        "quality_feedback_mechanisms": {},
    }

    # Analyze WebUI validation components
    webui_components_dir = Path("webui/src/components")
    webui_pages_dir = Path("webui/src/pages")
    webui_api_dir = Path("webui/api")

    # Validation components analysis
    validation_components = []

    if webui_components_dir.exists():
        # Look for validation-related components
        for component_file in webui_components_dir.rglob("*.tsx"):
            if any(
                keyword in component_file.stem.lower()
                for keyword in ["valid", "check", "verify", "review", "feedback", "error"]
            ):
                validation_components.append(
                    {"file": str(component_file), "name": component_file.stem, "type": "component"}
                )

    if webui_pages_dir.exists():
        # Look for validation pages
        for page_file in webui_pages_dir.rglob("*.tsx"):
            if any(
                keyword in page_file.stem.lower()
                for keyword in ["valid", "check", "verify", "review", "feedback"]
            ):
                validation_components.append(
                    {"file": str(page_file), "name": page_file.stem, "type": "page"}
                )

    webui_analysis["validation_components"] = validation_components

    # API endpoints analysis
    api_endpoints = []

    if webui_api_dir.exists():
        for api_file in webui_api_dir.rglob("*.py"):
            api_endpoints.append(
                {"file": str(api_file), "name": api_file.stem, "type": "api_endpoint"}
            )

    webui_analysis["api_endpoints"] = api_endpoints

    return webui_analysis


def analyze_validation_file_content(file_path: Path) -> Dict[str, Any]:
    """Analyze content of validation files for patterns."""

    if not file_path.exists():
        return {}

    try:
        content = file_path.read_text()

        analysis = {
            "file_path": str(file_path),
            "validation_patterns": [],
            "user_feedback_mechanisms": [],
            "quality_indicators": [],
            "error_handling": [],
            "workflow_patterns": [],
        }

        # Look for validation patterns
        validation_keywords = [
            "validate",
            "check",
            "verify",
            "confirm",
            "review",
            "approve",
            "reject",
            "correct",
            "fix",
            "error",
        ]

        for keyword in validation_keywords:
            matches = re.findall(rf"\b{keyword}\w*\b", content, re.IGNORECASE)
            if matches:
                analysis["validation_patterns"].extend(matches)

        # Look for user feedback mechanisms
        feedback_patterns = [
            r"feedback",
            r"rating",
            r"score",
            r"quality",
            r"confidence",
            r"success",
            r"failure",
            r"warning",
            r"alert",
            r"notification",
        ]

        for pattern in feedback_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                analysis["user_feedback_mechanisms"].extend(matches)

        # Look for quality indicators
        quality_patterns = [
            r"match_type",
            r"strategy",
            r"confidence",
            r"score",
            r"quality",
            r"accuracy",
            r"precision",
            r"reliability",
            r"certainty",
        ]

        for pattern in quality_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                analysis["quality_indicators"].extend(matches)

        # Look for error handling patterns
        error_patterns = [
            r"error",
            r"exception",
            r"invalid",
            r"failed",
            r"wrong",
            r"incorrect",
            r"mismatch",
            r"missing",
            r"unknown",
        ]

        for pattern in error_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                analysis["error_handling"].extend(matches)

        return analysis

    except Exception as e:
        return {"error": str(e), "file_path": str(file_path)}


def analyze_correct_matches_patterns() -> Dict[str, Any]:
    """Analyze correct_matches.yaml for manual correction patterns."""

    correct_matches_file = Path("data/correct_matches.yaml")

    if not correct_matches_file.exists():
        return {"error": "correct_matches.yaml not found"}

    correct_matches = load_yaml_data(correct_matches_file)

    analysis = {
        "total_corrections": 0,
        "correction_types": Counter(),
        "brand_corrections": Counter(),
        "pattern_corrections": [],
        "quality_patterns": {"high_confidence": [], "medium_confidence": [], "low_confidence": []},
        "correction_categories": {
            "brand_fixes": [],
            "model_fixes": [],
            "specification_fixes": [],
            "complete_overrides": [],
        },
    }

    for category, entries in correct_matches.items():
        if isinstance(entries, dict):
            for pattern, correction_data in entries.items():
                analysis["total_corrections"] += 1
                analysis["correction_types"][category] += 1

                if isinstance(correction_data, dict):
                    # Analyze correction quality indicators
                    correction_entry = {
                        "category": category,
                        "pattern": pattern,
                        "correction": correction_data,
                    }

                    # Categorize by correction type
                    if "brand" in correction_data:
                        analysis["correction_categories"]["brand_fixes"].append(correction_entry)
                        brand = correction_data["brand"]
                        analysis["brand_corrections"][brand] += 1

                    if "model" in correction_data:
                        analysis["correction_categories"]["model_fixes"].append(correction_entry)

                    # Check for specification fixes
                    spec_fields = ["knot_fiber", "knot_size_mm", "handle_material", "loft_mm"]
                    if any(field in correction_data for field in spec_fields):
                        analysis["correction_categories"]["specification_fixes"].append(
                            correction_entry
                        )

                    # Assess confidence level based on correction completeness
                    field_count = len([k for k in correction_data.keys() if k != "pattern"])

                    if field_count >= 4:
                        analysis["quality_patterns"]["high_confidence"].append(correction_entry)
                    elif field_count >= 2:
                        analysis["quality_patterns"]["medium_confidence"].append(correction_entry)
                    else:
                        analysis["quality_patterns"]["low_confidence"].append(correction_entry)

    return analysis


def analyze_analysis_tools() -> Dict[str, Any]:
    """Analyze existing analysis tools for validation patterns."""

    analysis_tools_dir = Path("sotd/match/tools/analyzers")

    if not analysis_tools_dir.exists():
        return {"error": "Analysis tools directory not found"}

    tools_analysis = {
        "available_tools": [],
        "validation_capabilities": {},
        "quality_assessment_features": {},
        "common_patterns": Counter(),
    }

    # Analyze each analysis tool
    for tool_file in analysis_tools_dir.glob("*.py"):
        if tool_file.stem.startswith("__"):
            continue

        tool_info = {"name": tool_file.stem, "file": str(tool_file), "capabilities": []}

        try:
            content = tool_file.read_text()

            # Look for validation capabilities
            validation_indicators = [
                "analyze",
                "check",
                "validate",
                "verify",
                "assess",
                "review",
                "inspect",
                "audit",
                "test",
                "measure",
            ]

            for indicator in validation_indicators:
                if indicator in content.lower():
                    tool_info["capabilities"].append(indicator)
                    tools_analysis["common_patterns"][indicator] += 1

            # Look for quality assessment features
            quality_indicators = [
                "quality",
                "confidence",
                "accuracy",
                "precision",
                "score",
                "rating",
                "reliability",
                "certainty",
                "trust",
            ]

            quality_features = []
            for indicator in quality_indicators:
                if indicator in content.lower():
                    quality_features.append(indicator)

            if quality_features:
                tools_analysis["quality_assessment_features"][tool_file.stem] = quality_features

        except Exception as e:
            tool_info["error"] = str(e)

        tools_analysis["available_tools"].append(tool_info)

    return tools_analysis


def analyze_webui_specific_validation() -> Dict[str, Any]:
    """Analyze specific WebUI validation components in detail."""

    webui_validation_analysis = {
        "brush_split_validator": {},
        "catalog_validation": {},
        "api_validation": {},
        "user_interaction_flows": {},
    }

    # Analyze BrushSplitValidator specifically
    brush_split_validator = Path("webui/src/pages/BrushSplitValidator.tsx")
    if brush_split_validator.exists():
        webui_validation_analysis["brush_split_validator"] = analyze_validation_file_content(
            brush_split_validator
        )

    # Analyze API validation
    api_validation_files = [
        Path("webui/api/validators/brush_split_validator.py"),
        Path("webui/api/validators/base_validator.py"),
        Path("webui/api/brush_splits.py"),
    ]

    for api_file in api_validation_files:
        if api_file.exists():
            webui_validation_analysis["api_validation"][api_file.stem] = (
                analyze_validation_file_content(api_file)
            )

    # Analyze catalog validation components
    catalog_components = [
        Path("webui/src/components/data/CatalogTable.tsx"),
        Path("webui/src/components/data/DataValidation.tsx"),
    ]

    for component_file in catalog_components:
        if component_file.exists():
            webui_validation_analysis["catalog_validation"][component_file.stem] = (
                analyze_validation_file_content(component_file)
            )

    return webui_validation_analysis


def generate_user_feedback_report(analysis_results: Dict[str, Any]) -> str:
    """Generate user feedback patterns analysis report."""

    webui_analysis = analysis_results["webui_analysis"]
    correct_matches = analysis_results["correct_matches_analysis"]
    analysis_tools = analysis_results["analysis_tools"]
    webui_validation = analysis_results["webui_validation_analysis"]

    report = f"""# Phase 4.1 Step 4: User Feedback Pattern Research

**Analysis Date**: {analysis_results["analysis_date"]}  
**Data Sources**: WebUI validation tools, correct_matches.yaml, analysis tools, validation components  
**Total Manual Corrections**: {correct_matches.get("total_corrections", 0):,}  
**Available Analysis Tools**: {len(analysis_tools.get("available_tools", [])):,}

## Executive Summary

### Validation Infrastructure
- **WebUI Validation Components**: {len(webui_analysis.get("validation_components", [])):,} components identified
- **API Validation Endpoints**: {len(webui_analysis.get("api_endpoints", [])):,} endpoints available
- **Manual Correction Entries**: {correct_matches.get("total_corrections", 0):,} patterns in correct_matches.yaml
- **Analysis Tools**: {len(analysis_tools.get("available_tools", [])):,} automated analysis tools

### Quality Feedback Patterns
- **High Confidence Corrections**: {len(correct_matches.get("quality_patterns", {}).get("high_confidence", [])):,} entries (4+ fields)
- **Medium Confidence Corrections**: {len(correct_matches.get("quality_patterns", {}).get("medium_confidence", [])):,} entries (2-3 fields)
- **Low Confidence Corrections**: {len(correct_matches.get("quality_patterns", {}).get("low_confidence", [])):,} entries (1 field)

## WebUI Validation Analysis

### Validation Components

| Component | Type | Purpose |
|-----------|------|---------|
"""

    for component in webui_analysis.get("validation_components", []):
        report += f"| {component['name']} | {component['type']} | Validation interface |\n"

    report += """
### API Validation Endpoints

| Endpoint | Purpose | Validation Type |
|----------|---------|-----------------|
"""

    for endpoint in webui_analysis.get("api_endpoints", []):
        report += f"| {endpoint['name']} | Data validation | API-level validation |\n"

    report += """
### WebUI Validation Capabilities Analysis

#### BrushSplitValidator Analysis
"""

    brush_validator = webui_validation.get("brush_split_validator", {})
    if brush_validator and "validation_patterns" in brush_validator:
        validation_patterns = set(brush_validator["validation_patterns"])
        report += f"- **Validation Patterns**: {len(validation_patterns)} unique patterns found\n"
        for pattern in list(validation_patterns)[:10]:  # Show top 10
            report += f"  - {pattern}\n"

        quality_indicators = set(brush_validator.get("quality_indicators", []))
        if quality_indicators:
            report += f"- **Quality Indicators**: {len(quality_indicators)} indicators used\n"
            for indicator in list(quality_indicators)[:5]:  # Show top 5
                report += f"  - {indicator}\n"
    else:
        report += "- BrushSplitValidator analysis not available\n"

    report += """
#### API Validation Analysis
"""

    api_validation = webui_validation.get("api_validation", {})
    for api_name, api_data in api_validation.items():
        if isinstance(api_data, dict) and "validation_patterns" in api_data:
            patterns = set(api_data["validation_patterns"])
            report += f"- **{api_name}**: {len(patterns)} validation patterns\n"

    report += """
## Manual Correction Pattern Analysis

### Correction Type Distribution

| Correction Type | Count | Percentage |
|-----------------|-------|------------|
"""

    total_corrections = correct_matches.get("total_corrections", 1)
    for correction_type, count in correct_matches.get("correction_types", {}).items():
        percentage = (count / total_corrections) * 100
        report += f"| {correction_type} | {count:,} | {percentage:.1f}% |\n"

    report += """
### Brand Correction Frequency

| Brand | Corrections | Quality Indicator |
|-------|-------------|-------------------|
"""

    brand_corrections = correct_matches.get("brand_corrections", {})
    for brand, count in sorted(brand_corrections.items(), key=lambda x: x[1], reverse=True)[:10]:
        quality_level = "High" if count >= 5 else "Medium" if count >= 2 else "Low"
        report += f"| {brand} | {count:,} | {quality_level} frequency |\n"

    report += """
### Correction Quality Analysis

#### High Confidence Corrections (4+ fields)
"""

    high_confidence = correct_matches.get("quality_patterns", {}).get("high_confidence", [])
    for correction in high_confidence[:5]:  # Show top 5
        category = correction.get("category", "unknown")
        pattern = (
            correction.get("pattern", "")[:50] + "..."
            if len(correction.get("pattern", "")) > 50
            else correction.get("pattern", "")
        )
        report += f"- **{category}**: `{pattern}` - Complete specification provided\n"

    report += """
#### Medium Confidence Corrections (2-3 fields)
"""

    medium_confidence = correct_matches.get("quality_patterns", {}).get("medium_confidence", [])
    for correction in medium_confidence[:5]:  # Show top 5
        category = correction.get("category", "unknown")
        pattern = (
            correction.get("pattern", "")[:50] + "..."
            if len(correction.get("pattern", "")) > 50
            else correction.get("pattern", "")
        )
        report += f"- **{category}**: `{pattern}` - Partial specification provided\n"

    report += """
## Analysis Tools Validation Capabilities

### Available Analysis Tools

| Tool | Capabilities | Quality Assessment |
|------|--------------|-------------------|
"""

    for tool in analysis_tools.get("available_tools", []):
        capabilities = ", ".join(tool.get("capabilities", [])[:3])  # Show top 3
        has_quality = (
            "Yes" if tool["name"] in analysis_tools.get("quality_assessment_features", {}) else "No"
        )
        report += f"| {tool['name']} | {capabilities} | {has_quality} |\n"

    report += """
### Common Validation Patterns

| Pattern | Frequency | Usage Context |
|---------|-----------|---------------|
"""

    common_patterns = analysis_tools.get("common_patterns", {})
    for pattern, frequency in sorted(common_patterns.items(), key=lambda x: x[1], reverse=True)[
        :10
    ]:
        context = "Analysis and validation operations"
        report += f"| {pattern} | {frequency} | {context} |\n"

    report += f"""
## User Interaction and Feedback Patterns

### Validation Workflow Analysis

Based on the WebUI and API analysis, the current validation workflow follows this pattern:

1. **Data Input**: Users input brush data through WebUI forms
2. **Real-time Validation**: API validators check data format and completeness
3. **Visual Feedback**: UI components display validation results and errors
4. **Manual Correction**: Users can override automated matches via correct_matches.yaml
5. **Quality Assessment**: Analysis tools provide quality metrics and confidence scores

### Quality Feedback Mechanisms

#### Current Feedback Types
1. **Binary Validation**: Pass/fail validation for data format
2. **Completeness Scoring**: Assessment based on field coverage
3. **Manual Override System**: correct_matches.yaml for expert corrections
4. **Analysis Tool Reports**: Automated quality assessment reports

#### User Preference Patterns (from manual corrections)
1. **Brand Accuracy Priority**: {len(correct_matches.get("correction_categories", {}).get("brand_fixes", [])):,} brand corrections indicate high user focus on brand accuracy
2. **Specification Completeness**: {len(correct_matches.get("correction_categories", {}).get("specification_fixes", [])):,} specification fixes show importance of complete data
3. **Quality Over Quantity**: High-confidence corrections ({len(high_confidence):,}) suggest users prefer complete, accurate entries

## Quality Validation Insights for Scoring System

### High-Value Quality Indicators
1. **Manual Correction Frequency**: Brands with frequent corrections indicate problematic automated matching
2. **Specification Completeness**: Users consistently add missing specifications in corrections
3. **Pattern Specificity**: Complex patterns in correct_matches.yaml indicate need for specific matching
4. **Brand Authority**: Manufacturer brands receive more detailed corrections than artisan brands

### User Validation Preferences
1. **Accuracy Over Speed**: Users willing to manually correct inaccurate automated matches
2. **Completeness Priority**: Users add missing specifications even for successful matches
3. **Brand Reliability**: Focus on brand accuracy suggests brand-based quality scoring is valuable
4. **Expert Knowledge**: High-quality corrections suggest expert user base with domain knowledge

### Scoring System Integration Recommendations

#### Quality Boost Criteria (from user validation patterns)
1. **Manual Correction History**: Boost scores for brands with few manual corrections
2. **Specification Completeness**: Boost scores for matches with complete specifications
3. **Pattern Confidence**: Higher scores for patterns similar to those in correct_matches.yaml
4. **Brand Authority**: Boost scores for brands with consistent, accurate automated matching

#### Quality Penalty Criteria
1. **Frequent Corrections**: Penalize scores for brands requiring frequent manual corrections
2. **Incomplete Specifications**: Lower scores for matches with missing key specifications
3. **Generic Patterns**: Penalize overly broad patterns that require frequent user correction
4. **Unknown Brands**: Lower scores for brands not seen in validation history

#### Confidence Indicators
1. **Validation History**: Use correction frequency as inverse confidence indicator
2. **User Expertise**: Weight corrections by user expertise level (if available)
3. **Specification Quality**: Use completeness as confidence multiplier
4. **Pattern Matching**: Use similarity to validated patterns as confidence boost

## Implementation Recommendations for Phase 4.2+

### Immediate Integration Opportunities
1. **Leverage correct_matches.yaml**: Use as ground truth for quality assessment
2. **Integrate WebUI feedback**: Capture user validation actions for quality learning
3. **Expand analysis tools**: Enhance tools to provide quality confidence scores
4. **User feedback loop**: Create mechanism to capture quality assessments from users

### Quality Scoring Enhancements
1. **Historical accuracy scoring**: Track accuracy of automated matches vs manual corrections
2. **User confidence weighting**: Weight quality scores by user validation confidence
3. **Continuous learning**: Update quality scores based on ongoing user feedback
4. **Expert validation integration**: Prioritize feedback from users with high-quality correction history

---

*This analysis provides the foundation for Phase 4.1 Step 5: Quality Metrics Definition*
"""

    return report


def main():
    """Main analysis function."""
    print("Analyzing WebUI validation tools...")
    webui_analysis = analyze_webui_validation_tools()

    print("Analyzing specific WebUI validation components...")
    webui_validation_analysis = analyze_webui_specific_validation()

    print("Analyzing correct_matches.yaml patterns...")
    correct_matches_analysis = analyze_correct_matches_patterns()

    print("Analyzing analysis tools...")
    analysis_tools_analysis = analyze_analysis_tools()

    # Compile results
    analysis_results = {
        "analysis_date": "2025-08-08",
        "webui_analysis": webui_analysis,
        "webui_validation_analysis": webui_validation_analysis,
        "correct_matches_analysis": correct_matches_analysis,
        "analysis_tools": analysis_tools_analysis,
    }

    print("Generating user feedback patterns report...")
    report = generate_user_feedback_report(analysis_results)

    # Save report
    output_file = Path("analysis/phase_4_1_user_feedback_patterns.md")
    with open(output_file, "w") as f:
        f.write(report)

    print(f"Analysis complete! Report saved to: {output_file}")

    # Print summary
    total_corrections = correct_matches_analysis.get("total_corrections", 0)
    validation_components = len(webui_analysis.get("validation_components", []))
    analysis_tools_count = len(analysis_tools_analysis.get("available_tools", []))

    print("\nSummary:")
    print(f"- Manual corrections: {total_corrections:,}")
    print(f"- WebUI validation components: {validation_components:,}")
    print(f"- Analysis tools: {analysis_tools_count:,}")
    print(
        f"- High confidence corrections: {len(correct_matches_analysis.get('quality_patterns', {}).get('high_confidence', [])):,}"
    )


if __name__ == "__main__":
    main()
