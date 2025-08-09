"""
Pattern Specificity Analyzer

Analyzes pattern specificity and complexity for brush matches based on Phase 4.1 research findings.
Implements 3-tier specificity classification and confidence scoring.
"""

import re
from typing import Any, Dict


class PatternSpecificityAnalyzer:
    """
    Analyzes pattern specificity and complexity for brush matching.

    Based on Phase 4.1 research findings:
    - 3-tier specificity classification (high/medium/low)
    - Pattern complexity analysis and scoring
    - Brand pattern recognition and confidence assessment
    - Match pattern categorization and quality indicators
    """

    def __init__(self):
        """Initialize pattern specificity analyzer."""
        # Define specificity levels based on Phase 4.1 research
        self.specificity_levels = ["high", "medium", "low"]

        # Define pattern recognition keywords
        self.pattern_keywords = {
            "materials": ["boar", "badger", "synthetic", "silvertip", "super", "finest"],
            "sizes": [r"\d+mm", r"\d+cm"],
            "manufacturers": ["semogue", "omega", "zenith", "simpson"],
            "artisans": ["declaration", "ap shave", "maggard", "stirling"],
            "quality_indicators": ["professional", "grade", "premium", "deluxe"],
        }

    def analyze_pattern_specificity(self, pattern: str) -> Dict[str, Any]:
        """
        Analyze pattern specificity and return comprehensive assessment.

        Returns:
            Dict with specificity_level, complexity_score, confidence_score, etc.
        """
        # Handle edge cases
        if not pattern or not pattern.strip():
            return {
                "specificity_level": "low",
                "complexity_score": 0,
                "confidence_score": 0,
                "has_brand_identification": False,
                "has_size_specification": False,
                "has_material_specification": False,
            }

        # Get component assessments
        complexity_result = self.calculate_pattern_complexity_score(pattern)
        brand_result = self.assess_brand_specificity(pattern)
        spec_indicators = self.detect_specification_indicators(pattern)
        confidence_score = self.get_pattern_confidence_score(pattern)

        # Determine specificity level based on complexity and brand authority
        complexity_score = complexity_result["complexity_score"]
        brand_confidence = brand_result["brand_confidence"]
        has_brand = brand_result["has_brand_identification"]

        if complexity_score >= 60 and brand_confidence >= 60:
            specificity_level = "high"
        elif has_brand and complexity_score >= 30:
            specificity_level = "medium"  # Branded patterns with decent complexity
        elif not has_brand and complexity_score >= 45:
            specificity_level = "medium"  # Generic patterns need higher complexity
        elif brand_confidence >= 40:
            specificity_level = "medium"  # Good brand authority even with low complexity
        else:
            specificity_level = "low"

        return {
            "specificity_level": specificity_level,
            "complexity_score": complexity_score,
            "confidence_score": confidence_score,
            "has_brand_identification": brand_result["has_brand_identification"],
            "has_size_specification": spec_indicators["has_size_specification"],
            "has_material_specification": spec_indicators["has_material_specification"],
            "detected_features": complexity_result["detected_features"],
            "brand_analysis": brand_result,
        }

    def assess_brand_specificity(self, pattern: str) -> Dict[str, Any]:
        """Assess brand specificity and authority."""
        if not pattern or not pattern.strip():
            return {
                "brand_authority": "unknown",
                "brand_confidence": 0,
                "has_brand_identification": False,
                "has_model_number": False,
            }

        pattern_lower = pattern.lower().strip()

        # Check for manufacturer brands
        for manufacturer in self.pattern_keywords["manufacturers"]:
            if manufacturer in pattern_lower:
                # Check for model number (more permissive pattern including named models)
                has_model = bool(
                    re.search(r"\b[a-z]*\d+[a-z]*\b|\bb\d+\b|\bt\d+\b|\btrafalgar\b", pattern_lower)
                )
                return {
                    "brand_authority": "manufacturer",
                    "brand_confidence": 95 if has_model else 90,
                    "has_brand_identification": True,
                    "has_model_number": has_model,
                }

        # Check for artisan brands
        for artisan in self.pattern_keywords["artisans"]:
            if artisan in pattern_lower:
                # Determine if cataloged vs emerging based on pattern completeness
                has_detailed_specs = any(
                    keyword in pattern_lower for keyword in ["synthetic", "boar", "badger", "mm"]
                )
                authority = "cataloged_artisan" if has_detailed_specs else "emerging_artisan"
                confidence = 80 if has_detailed_specs else 60

                return {
                    "brand_authority": authority,
                    "brand_confidence": confidence,
                    "has_brand_identification": True,
                    "has_model_number": bool(re.search(r"\b[a-z]*\d+[a-z]*\b", pattern_lower)),
                }

        # Check for generic brand indicators
        brand_words = ["brush", "co", "company", "artisan", "shaving"]
        brand_indicators = sum(1 for word in brand_words if word in pattern_lower)

        if brand_indicators > 0:
            return {
                "brand_authority": "unknown",
                "brand_confidence": min(25, brand_indicators * 8),
                "has_brand_identification": False,
                "has_model_number": False,
            }

        return {
            "brand_authority": "unknown",
            "brand_confidence": 0,
            "has_brand_identification": False,
            "has_model_number": False,
        }

    def calculate_pattern_complexity_score(self, pattern: str) -> Dict[str, Any]:
        """Calculate pattern complexity scoring."""
        if not pattern or not pattern.strip():
            return {"complexity_score": 0, "detected_features": []}

        pattern_lower = pattern.lower().strip()
        detected_features = []
        score = 0

        # Brand identification (20-30 points based on authority)
        brand_result = self.assess_brand_specificity(pattern)
        if brand_result["has_brand_identification"]:
            detected_features.append("brand")
            if brand_result["brand_authority"] == "manufacturer":
                score += 30
            elif brand_result["brand_authority"] in ["cataloged_artisan", "emerging_artisan"]:
                score += 25
            else:
                score += 20

        # Model identification (20 points for specific models, 15 for general)
        if brand_result["has_model_number"] or any(
            model in pattern_lower for model in ["b35", "b15", "t3", "1305", "10049", "trafalgar"]
        ):
            detected_features.append("model")
            # Extra points for named models like "trafalgar"
            if "trafalgar" in pattern_lower or "t3" in pattern_lower:
                score += 20
            else:
                score += 15

        # Material specification (15 points)
        material_found = False
        for material in self.pattern_keywords["materials"]:
            if material in pattern_lower:
                if not material_found:  # Only count first material
                    detected_features.append("material")
                    score += 15
                    material_found = True

        # Size specification (20 points)
        if re.search(r"\d+\s*mm", pattern_lower):
            detected_features.append("size")
            score += 20

        # Loft specification (10 points)
        if "loft" in pattern_lower or re.search(r"\d+\s*mm.*loft", pattern_lower):
            detected_features.append("loft")
            score += 10

        # Quality indicators (15 points)
        for indicator in self.pattern_keywords["quality_indicators"]:
            if indicator in pattern_lower:
                detected_features.append("quality_indicator")
                score += 15
                break

        # Additional quality words (5 points each, max 10)
        quality_words = ["super", "premium", "deluxe", "finest", "pure"]
        quality_bonus = sum(1 for word in quality_words if word in pattern_lower)
        if quality_bonus > 0:
            detected_features.append("quality_bonus")
            score += min(10, quality_bonus * 5)

        # Handle specifications (5 points)
        if any(word in pattern_lower for word in ["handle", "mozingo", "resin", "wood"]):
            detected_features.append("handle")
            score += 5

        # Knot specifications (5 points)
        if any(word in pattern_lower for word in ["knot", "bristle", "fan", "bulb"]):
            detected_features.append("knot")
            score += 5

        return {"complexity_score": min(100, score), "detected_features": detected_features}

    def detect_specification_indicators(self, pattern: str) -> Dict[str, bool]:
        """Detect specification indicators in pattern."""
        if not pattern or not pattern.strip():
            return {
                "has_size_specification": False,
                "has_material_specification": False,
                "has_loft_specification": False,
                "has_knot_specification": False,
            }

        pattern_lower = pattern.lower().strip()

        # Size specification (e.g., "28mm", "26 mm")
        has_size = bool(re.search(r"\d+\s*mm", pattern_lower))

        # Material specification
        has_material = any(
            material in pattern_lower for material in self.pattern_keywords["materials"]
        )

        # Loft specification
        has_loft = "loft" in pattern_lower or "x" in pattern_lower

        # Knot specification (material + size, or specific knot characteristics)
        has_knot = (has_material and has_size) or any(
            word in pattern_lower for word in ["knot", "bristle", "fan", "bulb", "b35", "b15", "t3"]
        )

        return {
            "has_size_specification": has_size,
            "has_material_specification": has_material,
            "has_loft_specification": has_loft,
            "has_knot_specification": has_knot,
        }

    def get_pattern_confidence_score(self, pattern: str) -> int:
        """Get pattern confidence score."""
        if not pattern or not pattern.strip():
            return 0

        # Get component scores
        brand_result = self.assess_brand_specificity(pattern)
        complexity_result = self.calculate_pattern_complexity_score(pattern)

        # Base confidence from brand authority
        brand_confidence = brand_result["brand_confidence"]

        # Complexity bonus (up to 20 points)
        complexity_bonus = min(20, complexity_result["complexity_score"] // 5)

        # Combine scores
        total_confidence = min(100, brand_confidence + complexity_bonus)

        return int(total_confidence)

    def categorize_pattern_type(self, pattern: str) -> Dict[str, str]:
        """Categorize pattern type and category."""
        if not pattern or not pattern.strip():
            return {"pattern_type": "incomplete_specification", "pattern_category": "unidentified"}

        # Get component assessments
        complexity_result = self.calculate_pattern_complexity_score(pattern)
        brand_result = self.assess_brand_specificity(pattern)
        spec_indicators = self.detect_specification_indicators(pattern)

        complexity_score = complexity_result["complexity_score"]
        brand_authority = brand_result["brand_authority"]

        # Determine pattern type based on completeness
        # Include brand/model as specification indicators for categorization
        spec_count = sum(
            [
                spec_indicators["has_size_specification"],
                spec_indicators["has_material_specification"],
                spec_indicators["has_loft_specification"],
                spec_indicators["has_knot_specification"],
                brand_result["has_brand_identification"],  # Brand counts as specification
                brand_result["has_model_number"],  # Model counts as specification
            ]
        )

        if complexity_score >= 60 and spec_count >= 3:
            pattern_type = "complete_specification"
        elif complexity_score >= 30 and spec_count >= 2:
            pattern_type = "partial_specification"
        elif complexity_score >= 15 and spec_count >= 1:
            pattern_type = "minimal_specification"
        else:
            pattern_type = "incomplete_specification"

        # Determine pattern category based on brand and specifications
        if brand_authority == "manufacturer" and pattern_type == "complete_specification":
            pattern_category = "manufacturer_detailed"
        elif brand_authority == "manufacturer":
            pattern_category = "manufacturer_basic"
        elif brand_authority in ["cataloged_artisan", "emerging_artisan"] and pattern_type in [
            "complete_specification",
            "partial_specification",
        ]:
            pattern_category = "artisan_basic"
        elif brand_authority in ["cataloged_artisan", "emerging_artisan"]:
            pattern_category = "artisan_minimal"
        elif (
            spec_indicators["has_material_specification"]
            or spec_indicators["has_size_specification"]
        ):
            pattern_category = "generic_typed"
        else:
            pattern_category = "unidentified"

        return {"pattern_type": pattern_type, "pattern_category": pattern_category}

    def get_specificity_modifier_points(self, specificity_level: str) -> int:
        """Get specificity modifier points based on level."""
        # Based on Phase 4.1 quality metrics specification
        modifier_points = {"high": 15, "medium": 10, "low": 0}

        return modifier_points.get(specificity_level, 0)

    def calculate_comprehensive_pattern_analysis(self, pattern: str) -> Dict[str, Any]:
        """Calculate comprehensive pattern analysis combining all factors."""
        # Get all component analyses
        basic_analysis = self.analyze_pattern_specificity(pattern)
        pattern_type_result = self.categorize_pattern_type(pattern)

        # Combine results
        comprehensive_result = {
            "specificity_level": basic_analysis["specificity_level"],
            "complexity_score": basic_analysis["complexity_score"],
            "confidence_score": basic_analysis["confidence_score"],
            "pattern_type": pattern_type_result["pattern_type"],
            "pattern_category": pattern_type_result["pattern_category"],
            "brand_analysis": basic_analysis["brand_analysis"],
            "detected_features": basic_analysis["detected_features"],
            "specification_indicators": {
                "has_size_specification": basic_analysis["has_size_specification"],
                "has_material_specification": basic_analysis["has_material_specification"],
            },
            "modifier_points": self.get_specificity_modifier_points(
                basic_analysis["specificity_level"]
            ),
        }

        return comprehensive_result
