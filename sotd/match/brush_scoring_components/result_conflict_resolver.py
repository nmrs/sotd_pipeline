"""ResultConflictResolver component for multi-strategy brush matching."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from sotd.match.types import MatchResult


class ConflictType(Enum):
    """Types of conflicts that can occur between strategy results."""

    BRAND = "brand"
    MODEL = "model"
    FIBER = "fiber"
    KNOT_SIZE = "knot_size"
    HANDLE_MAKER = "handle_maker"
    KNOT_MAKER = "knot_maker"


@dataclass
class Conflict:
    """Represents a conflict between strategy results."""

    conflict_type: ConflictType
    field: str
    values: Set[str]
    affected_results: List[MatchResult]


@dataclass
class ConflictResolution:
    """Represents the resolution of conflicts between strategy results."""

    winning_result: Optional[MatchResult]
    resolution_method: str
    resolved_conflicts: List[Conflict] = field(default_factory=list)
    resolution_notes: str = ""


class ResultConflictResolver:
    """Detects and resolves conflicts between brush matching strategy results."""

    def __init__(self):
        """Initialize the conflict resolver."""
        self.conflicts: List[Conflict] = []
        self.resolutions: List[ConflictResolution] = []

    def detect_conflicts(self, results: List[MatchResult]) -> List[Conflict]:
        """
        Detect conflicts between multiple strategy results.

        Args:
            results: List of MatchResult objects from different strategies

        Returns:
            List of detected conflicts
        """
        if len(results) < 2:
            return []

        conflicts = []

        # Define fields to check for conflicts
        conflict_fields = {
            "brand": ConflictType.BRAND,
            "model": ConflictType.MODEL,
            "fiber": ConflictType.FIBER,
            "knot_size": ConflictType.KNOT_SIZE,
            "handle_maker": ConflictType.HANDLE_MAKER,
            "knot_maker": ConflictType.KNOT_MAKER,
        }

        # Check each field for conflicts
        for field_name, conflict_type in conflict_fields.items():
            field_values = {}

            for result in results:
                if result.matched and field_name in result.matched:
                    value = result.matched[field_name]
                    if value not in field_values:
                        field_values[value] = []
                    field_values[value].append(result)

            # If we have multiple different values for the same field, it's a conflict
            if len(field_values) > 1:
                # Flatten the list of results from all field values
                affected_results = []
                for results_list in field_values.values():
                    affected_results.extend(results_list)

                conflict = Conflict(
                    conflict_type=conflict_type,
                    field=field_name,
                    values=set(field_values.keys()),
                    affected_results=affected_results,
                )
                conflicts.append(conflict)

        self.conflicts = conflicts
        return conflicts

    def resolve_conflicts(
        self,
        results: List[MatchResult],
        resolution_method: str = "score",
        selected_result: Optional[MatchResult] = None,
    ) -> ConflictResolution:
        """
        Resolve conflicts between strategy results.

        Args:
            results: List of MatchResult objects
            resolution_method: Method to use for resolution
                ("score", "priority", "confidence", "manual")
            selected_result: Manually selected result (for manual resolution)

        Returns:
            ConflictResolution object
        """
        if not results:
            return ConflictResolution(
                winning_result=None,
                resolution_method=resolution_method,
                resolution_notes="No results to resolve",
            )

        if len(results) == 1:
            return ConflictResolution(
                winning_result=results[0],
                resolution_method=resolution_method,
                resolution_notes="Single result, no conflicts",
            )

        # Detect conflicts
        conflicts = self.detect_conflicts(results)

        if not conflicts:
            # No conflicts, return the highest scoring result
            winning_result = max(results, key=lambda r: r.score or 0.0)
            return ConflictResolution(
                winning_result=winning_result,
                resolution_method=resolution_method,
                resolution_notes="No conflicts detected",
            )

        # Resolve conflicts based on method
        if resolution_method == "manual" and selected_result:
            winning_result = selected_result
        elif resolution_method == "score":
            winning_result = self._resolve_by_score(results)
        elif resolution_method == "priority":
            winning_result = self._resolve_by_priority(results)
        elif resolution_method == "confidence":
            winning_result = self._resolve_by_confidence(results)
        else:
            # Default to score-based resolution
            winning_result = self._resolve_by_score(results)

        return ConflictResolution(
            winning_result=winning_result,
            resolution_method=resolution_method,
            resolved_conflicts=conflicts,
            resolution_notes=(
                f"Resolved {len(conflicts)} conflicts using {resolution_method} method"
            ),
        )

    def _resolve_by_score(self, results: List[MatchResult]) -> MatchResult:
        """Resolve conflicts by selecting the result with the highest score."""
        return max(results, key=lambda r: r.score or 0.0)

    def _resolve_by_priority(self, results: List[MatchResult]) -> MatchResult:
        """Resolve conflicts by strategy priority."""
        # Define strategy priorities (higher number = higher priority)
        strategy_priorities = {
            "BrushSplitter": 5,
            "KnownSplitWrapperStrategy": 4,
            "HandleMatcher": 3,
            "KnotMatcher": 2,
            "FiberProcessor": 1,
        }

        def get_priority(result: MatchResult) -> int:
            return strategy_priorities.get(result.strategy or "", 0)

        return max(results, key=get_priority)

    def _resolve_by_confidence(self, results: List[MatchResult]) -> MatchResult:
        """Resolve conflicts by confidence level."""
        return max(results, key=lambda r: r.score or 0.0)

    def get_conflict_summary(self, conflicts: List[Conflict]) -> str:
        """
        Generate a human-readable summary of detected conflicts.

        Args:
            conflicts: List of conflicts to summarize

        Returns:
            String summary of conflicts
        """
        if not conflicts:
            return "No conflicts detected"

        summary_parts = [f"{len(conflicts)} conflicts detected:"]

        for conflict in conflicts:
            values_list = sorted(list(conflict.values))
            values_str = " vs ".join(values_list)
            summary_parts.append(f"- {conflict.field}: {values_str}")

        return "\n".join(summary_parts)

    def validate_resolution(self, resolution: ConflictResolution) -> bool:
        """
        Validate that a conflict resolution is valid.

        Args:
            resolution: ConflictResolution to validate

        Returns:
            True if resolution is valid, False otherwise
        """
        if not resolution.winning_result:
            return False

        # Check that the winning result is among the affected results for all conflicts
        for conflict in resolution.resolved_conflicts:
            if resolution.winning_result not in conflict.affected_results:
                return False

        return True

    def get_conflict_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about detected conflicts.

        Returns:
            Dictionary with conflict statistics
        """
        if not self.conflicts:
            return {"total_conflicts": 0, "conflicts_by_type": {}, "most_common_conflict": None}

        conflicts_by_type = {}
        for conflict in self.conflicts:
            conflict_type = conflict.conflict_type.value
            if conflict_type not in conflicts_by_type:
                conflicts_by_type[conflict_type] = 0
            conflicts_by_type[conflict_type] += 1

        most_common_conflict = (
            max(conflicts_by_type.items(), key=lambda x: x[1])[0] if conflicts_by_type else None
        )

        return {
            "total_conflicts": len(self.conflicts),
            "conflicts_by_type": conflicts_by_type,
            "most_common_conflict": most_common_conflict,
        }
