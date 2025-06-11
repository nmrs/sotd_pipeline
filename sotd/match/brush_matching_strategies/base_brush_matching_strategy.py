from abc import ABC, abstractmethod
from typing import Optional


class BaseBrushMatchingStrategy(ABC):
    @abstractmethod
    def match(self, value: str) -> Optional[dict]:
        """Attempt to match the given string to a known brush pattern.

        Returns a dict with match results (including at least a 'matched' field),
        or None if no match is found.
        """
        pass
