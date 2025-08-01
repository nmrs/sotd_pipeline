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

    def _create_enriched_data(
        self, user_data: Dict[str, Any], catalog_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create enriched data with proper source tracking.

        Args:
            user_data: Data extracted from user comment (can be empty dict)
            catalog_data: Data from catalog/match phase (can be empty dict)

        Returns:
            Enriched data with proper source tracking
        """
        # Determine sources
        sources = []
        if user_data:
            sources.append("user_comment")
        if catalog_data:
            sources.append("catalog_data")

        # Create base enriched data
        enriched_data = {
            "_enriched_by": self.get_enricher_name(),
            "_extraction_source": " + ".join(sources) if sources else "none",
        }

        # Merge data (user takes precedence, but None values don't override catalog)
        merged_data = {**catalog_data, **user_data}
        # Handle None values: if user data is None, use catalog data
        for key in user_data:
            if user_data[key] is None and key in catalog_data:
                merged_data[key] = catalog_data[key]
        enriched_data.update(merged_data)

        return enriched_data

    def _create_single_source_enriched_data(
        self, data: Dict[str, Any], source: str
    ) -> Dict[str, Any]:
        """Create enriched data for single-source extraction.

        Args:
            data: Extracted data
            source: Source of the data ("user_comment", "catalog_data", etc.)

        Returns:
            Enriched data with proper source tracking
        """
        return {"_enriched_by": self.get_enricher_name(), "_extraction_source": source, **data}
