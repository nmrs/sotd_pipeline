#!/usr/bin/env python3
"""Component Score Calculator for brush matching strategies.

This utility calculates scores for handle and knot components based on their
attributes, following the same scoring logic used in the analyzer.
"""

from typing import Any, Dict


class ComponentScoreCalculator:
    """Calculates component scores for handle and knot components."""

    @staticmethod
    def calculate_handle_score(handle_data: Dict[str, Any]) -> float:
        """
        Calculate score for a handle component.

        Args:
            handle_data: Dictionary containing handle component data

        Returns:
            Calculated score for the handle component
        """
        score = 0.0

        # Brand match (5 points)
        if handle_data.get("brand"):
            score += 5.0

        # Model match (5 points)
        if handle_data.get("model"):
            score += 5.0

        # Priority bonus (2 points for priority 1, 1 point for priority 2)
        priority = handle_data.get("priority")
        if priority == 1:
            score += 2.0
        elif priority == 2:
            score += 1.0

        return score

    @staticmethod
    def calculate_knot_score(knot_data: Dict[str, Any]) -> float:
        """
        Calculate score for a knot component.

        Args:
            knot_data: Dictionary containing knot component data

        Returns:
            Calculated score for the knot component
        """
        score = 0.0

        # Brand match (5 points)
        if knot_data.get("brand"):
            score += 5.0

        # Model match (5 points)
        if knot_data.get("model"):
            score += 5.0

        # Fiber match (5 points)
        if knot_data.get("fiber"):
            score += 5.0

        # Size match (2 points)
        if knot_data.get("knot_size_mm"):
            score += 2.0

        # Priority bonus (2 points for priority 1, 1 point for priority 2)
        priority = knot_data.get("priority")
        if priority == 1:
            score += 2.0
        elif priority == 2:
            score += 1.0

        return score

    @staticmethod
    def calculate_component_scores(matched_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate scores for both handle and knot components in matched data.

        Args:
            matched_data: Dictionary containing matched data with handle/knot components

        Returns:
            Updated matched_data with calculated component scores
        """
        # Create a copy to avoid modifying the original
        updated_data = matched_data.copy()

        # Calculate handle score if handle component exists
        if "handle" in updated_data and isinstance(updated_data["handle"], dict):
            handle_score = ComponentScoreCalculator.calculate_handle_score(updated_data["handle"])
            updated_data["handle"]["score"] = handle_score

        # Calculate knot score if knot component exists
        if "knot" in updated_data and isinstance(updated_data["knot"], dict):
            knot_score = ComponentScoreCalculator.calculate_knot_score(updated_data["knot"])
            updated_data["knot"]["score"] = knot_score

        return updated_data
