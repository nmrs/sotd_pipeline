from abc import ABC, abstractmethod
from typing import Optional

from sotd.match.types import MatchResult


class BaseBrushMatchingStrategy(ABC):
    @abstractmethod
    def match(self, value: str) -> Optional[MatchResult]:
        """Attempt to match the given string to a known brush pattern.

        Returns a MatchResult object, or None if no match is found.
        """
        pass
