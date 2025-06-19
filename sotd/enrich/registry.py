import logging
from typing import Any, Dict, List

from .enricher import BaseEnricher

logger = logging.getLogger(__name__)


class EnricherRegistry:
    """Registry for managing enricher instances and coordinating enrichment operations."""

    def __init__(self):
        self._enrichers: List[BaseEnricher] = []
        self._enrichers_by_field: Dict[str, List[BaseEnricher]] = {}

    def register(self, enricher: BaseEnricher) -> None:
        """Register an enricher instance.

        Args:
            enricher: The enricher instance to register
        """
        if not isinstance(enricher, BaseEnricher):
            raise ValueError(f"Enricher must inherit from BaseEnricher, got {type(enricher)}")

        self._enrichers.append(enricher)
        target_field = enricher.target_field

        if target_field not in self._enrichers_by_field:
            self._enrichers_by_field[target_field] = []

        self._enrichers_by_field[target_field].append(enricher)
        logger.debug(f"Registered enricher {enricher.get_enricher_name()} for field {target_field}")

    def get_enrichers_for_field(self, field: str) -> List[BaseEnricher]:
        """Get all enrichers that target the specified field.

        Args:
            field: The field name to get enrichers for

        Returns:
            List of enrichers that target this field
        """
        return self._enrichers_by_field.get(field, [])

    def get_all_enrichers(self) -> List[BaseEnricher]:
        """Get all registered enrichers.

        Returns:
            List of all registered enrichers
        """
        return self._enrichers.copy()

    def enrich_record(self, record: Dict[str, Any], original_comment: str) -> Dict[str, Any]:
        """Enrich a single record with all applicable enrichers.

        Args:
            record: A comment record with matched product data
            original_comment: The original user comment text (unused for enrichment)

        Returns:
            The enriched record with additional specifications written directly to product fields
        """
        enriched_record = record.copy()

        # Process each field that has enrichers
        for field, enrichers in self._enrichers_by_field.items():
            field_data = enriched_record.get(field)
            if not field_data:
                continue

            # Use the corresponding *_extracted field for enrichment, else fall back to
            # product['original']
            extracted_field_name = f"{field}_extracted"
            extracted_value = record.get(extracted_field_name, "")
            if not extracted_value and isinstance(field_data, dict):
                extracted_value = field_data.get("original", "")

            field_enriched_data = {}

            for enricher in enrichers:
                try:
                    if enricher.applies_to(record):
                        enrichment_result = enricher.enrich(field_data, extracted_value)
                        if enrichment_result:
                            field_enriched_data.update(enrichment_result)
                            logger.debug(f"Applied {enricher.get_enricher_name()} to {field}")
                except Exception as e:
                    logger.error(
                        f"Error applying enricher {enricher.get_enricher_name()} to {field}: {e}"
                    )
                    # Continue with other enrichers even if one fails

            # Write enriched data directly to product field
            if field_enriched_data:
                # Ensure field_data is a dict with proper structure
                if not isinstance(field_data, dict):
                    field_data = {"original": field_data}

                # Add enriched data to the product field
                field_data["enriched"] = field_enriched_data
                enriched_record[field] = field_data

        return enriched_record

    def enrich_records(
        self, records: List[Dict[str, Any]], original_comments: List[str]
    ) -> List[Dict[str, Any]]:
        """Enrich multiple records with all applicable enrichers.

        Args:
            records: List of comment records with matched product data
            original_comments: List of original user comment texts

        Returns:
            List of enriched records
        """
        if len(records) != len(original_comments):
            raise ValueError("Records and original_comments must have the same length")

        enriched_records = []

        for i, (record, original_comment) in enumerate(zip(records, original_comments)):
            try:
                enriched_record = self.enrich_record(record, original_comment)
                enriched_records.append(enriched_record)
            except Exception as e:
                logger.error(f"Error enriching record {i}: {e}")
                # Include the original record if enrichment fails
                enriched_records.append(record)

        return enriched_records


# Global registry instance
enricher_registry = EnricherRegistry()
