from abc import ABC, abstractmethod
from typing import List, Optional

from sotd.match.types import MatchResult


class BaseBrushMatchingStrategy(ABC):
    """Base class for strategies that return a single match result."""

    @abstractmethod
    def match(self, value: str, full_string: Optional[str] = None) -> Optional[MatchResult]:
        """Attempt to match the given string to a known brush pattern.

        Args:
            value: The text to match against (may be a split portion)
            full_string: The full original string (for negative lookahead patterns).
                        If None, uses value as full_string.

        Returns:
            MatchResult object, or None if no match is found.
        """


class BaseMultiResultBrushMatchingStrategy(ABC):
    """Base class for strategies that can return multiple match results."""

    @abstractmethod
    def match(self, value: str, full_string: Optional[str] = None) -> Optional[MatchResult]:
        """Attempt to match the given string to a known brush pattern.

        Args:
            value: The text to match against (may be a split portion)
            full_string: The full original string (for negative lookahead patterns).
                        If None, uses value as full_string.

        Returns:
            MatchResult object, or None if no match is found.
            This method should return the best single result for backward compatibility.
        """

    @abstractmethod
    def match_all(self, value: str) -> List[MatchResult]:
        """Attempt to match the given string and return all possible results.

        Returns a list of MatchResult objects for all possible matches,
        empty list if no matches are found.
        """
