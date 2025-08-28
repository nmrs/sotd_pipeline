"""Integration tests for ResultConflictResolver in scoring engine."""

from sotd.match.brush_scoring_components.result_conflict_resolver import (
    ConflictType,
    ResultConflictResolver,
)
from sotd.match.brush_matcher import BrushMatcher
from sotd.match.types import MatchResult


class TestResultConflictResolverIntegration:
    """Test ResultConflictResolver integration with scoring engine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.matcher = BrushMatcher()
        self.conflict_resolver = ResultConflictResolver()

    def test_integration_with_conflicting_results(self):
        """Test that conflict resolver can handle conflicting strategy results."""
        # Create conflicting results that might come from different strategies
        result1 = MatchResult(
            original="Declaration B2 badger",
            matched={"brand": "Declaration Grooming", "model": "B2", "fiber": "badger"},
            strategy="BrushSplitter",
            score=0.8,
        )
        result2 = MatchResult(
            original="Declaration B2 badger",
            matched={"brand": "Dogwood Handcrafts", "model": "B2", "fiber": "badger"},
            strategy="HandleMatcher",
            score=0.7,
        )

        # Detect conflicts
        conflicts = self.conflict_resolver.detect_conflicts([result1, result2])

        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == ConflictType.BRAND
        assert conflicts[0].field == "brand"
        assert conflicts[0].values == {"Declaration Grooming", "Dogwood Handcrafts"}

    def test_integration_resolution_by_score(self):
        """Test conflict resolution by score in integration context."""
        result1 = MatchResult(
            original="Declaration B2",
            matched={"brand": "Declaration Grooming", "model": "B2"},
            strategy="BrushSplitter",
            score=0.9,
        )
        result2 = MatchResult(
            original="Declaration B2",
            matched={"brand": "Dogwood Handcrafts", "model": "B2"},
            strategy="HandleMatcher",
            score=0.7,
        )

        # Resolve conflicts
        resolution = self.conflict_resolver.resolve_conflicts(
            [result1, result2], resolution_method="score"
        )

        assert resolution.winning_result == result1
        assert resolution.resolution_method == "score"
        assert len(resolution.resolved_conflicts) == 1

    def test_integration_resolution_by_priority(self):
        """Test conflict resolution by strategy priority in integration context."""
        result1 = MatchResult(
            original="Declaration B2",
            matched={"brand": "Declaration Grooming", "model": "B2"},
            strategy="BrushSplitter",  # Higher priority
            score=0.8,
        )
        result2 = MatchResult(
            original="Declaration B2",
            matched={"brand": "Dogwood Handcrafts", "model": "B2"},
            strategy="HandleMatcher",  # Lower priority
            score=0.8,
        )

        # Resolve conflicts
        resolution = self.conflict_resolver.resolve_conflicts(
            [result1, result2], resolution_method="priority"
        )

        assert resolution.winning_result == result1
        assert resolution.resolution_method == "priority"

    def test_integration_no_conflicts(self):
        """Test that conflict resolver handles no conflicts correctly."""
        result1 = MatchResult(
            original="Declaration B2",
            matched={"brand": "Declaration Grooming", "model": "B2"},
            strategy="BrushSplitter",
            score=0.8,
        )
        result2 = MatchResult(
            original="Declaration B2",
            matched={"brand": "Declaration Grooming", "model": "B2"},
            strategy="HandleMatcher",
            score=0.7,
        )

        # Detect conflicts
        conflicts = self.conflict_resolver.detect_conflicts([result1, result2])

        assert len(conflicts) == 0

    def test_integration_empty_results(self):
        """Test that conflict resolver handles empty results correctly."""
        conflicts = self.conflict_resolver.detect_conflicts([])
        assert len(conflicts) == 0

        resolution = self.conflict_resolver.resolve_conflicts([])
        assert resolution.winning_result is None

    def test_integration_single_result(self):
        """Test that conflict resolver handles single result correctly."""
        result = MatchResult(
            original="Declaration B2",
            matched={"brand": "Declaration Grooming", "model": "B2"},
            strategy="BrushSplitter",
            score=0.8,
        )

        conflicts = self.conflict_resolver.detect_conflicts([result])
        assert len(conflicts) == 0

        resolution = self.conflict_resolver.resolve_conflicts([result])
        assert resolution.winning_result == result
        assert len(resolution.resolved_conflicts) == 0

    def test_integration_multiple_conflict_types(self):
        """Test that conflict resolver handles multiple conflict types correctly."""
        result1 = MatchResult(
            original="Declaration B2 badger",
            matched={
                "brand": "Declaration Grooming",
                "model": "B2",
                "fiber": "badger",
                "knot_size": "26mm",
            },
            strategy="BrushSplitter",
            score=0.8,
        )
        result2 = MatchResult(
            original="Declaration B2 badger",
            matched={
                "brand": "Dogwood Handcrafts",
                "model": "B3",
                "fiber": "boar",
                "knot_size": "28mm",
            },
            strategy="HandleMatcher",
            score=0.7,
        )

        # Detect conflicts
        conflicts = self.conflict_resolver.detect_conflicts([result1, result2])

        assert len(conflicts) == 4

        conflict_types = {c.conflict_type for c in conflicts}
        expected_types = {
            ConflictType.BRAND,
            ConflictType.MODEL,
            ConflictType.FIBER,
            ConflictType.KNOT_SIZE,
        }
        assert conflict_types == expected_types

    def test_integration_conflict_summary(self):
        """Test that conflict resolver generates useful summaries for integration."""
        result1 = MatchResult(
            original="Declaration B2 badger",
            matched={"brand": "Declaration Grooming", "model": "B2", "fiber": "badger"},
            strategy="BrushSplitter",
            score=0.8,
        )
        result2 = MatchResult(
            original="Declaration B2 badger",
            matched={"brand": "Dogwood Handcrafts", "model": "B3", "fiber": "boar"},
            strategy="HandleMatcher",
            score=0.7,
        )

        conflicts = self.conflict_resolver.detect_conflicts([result1, result2])
        summary = self.conflict_resolver.get_conflict_summary(conflicts)

        assert "3 conflicts detected" in summary
        assert "brand" in summary
        assert "model" in summary
        assert "fiber" in summary
        assert "Declaration Grooming vs Dogwood Handcrafts" in summary
        assert "B2 vs B3" in summary
        assert "badger vs boar" in summary
