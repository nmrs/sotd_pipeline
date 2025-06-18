from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseEnricher(ABC):
    """Base class for all enrichers in the enrich phase.

    Enrichers perform sophisticated analysis requiring knowledge of matched products
    to extract detailed specifications and metadata that don't affect product identification.
    """

    @property
    @abstractmethod
    def target_field(self) -> str:
        """The field type this enricher targets (e.g., 'blade', 'razor', 'brush', 'soap')."""
        pass

    @abstractmethod
    def applies_to(self, record: Dict[str, Any]) -> bool:
        """Determine if this enricher applies to the given record.

        Args:
            record: A comment record with matched product data

        Returns:
            True if this enricher should process this record, False otherwise
        """
        pass

    @abstractmethod
    def enrich(self, field_data: Dict[str, Any], original_comment: str) -> Optional[Dict[str, Any]]:
        """Enrich the given field data with additional specifications.

        Args:
            field_data: The matched product data for the target field
            original_comment: The original user comment text for extraction

        Returns:
            Dictionary with enriched data, or None if no enrichment possible.
            Should include _enriched_by and _extraction_source metadata fields.
        """
        pass

    def get_enricher_name(self) -> str:
        """Get the name of this enricher for metadata purposes."""
        return self.__class__.__name__
