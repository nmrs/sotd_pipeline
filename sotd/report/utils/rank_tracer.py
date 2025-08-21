"""Rank tracing utility for debugging rank corruption in report generation pipeline.

This module provides a standardized way to trace rank data through each step of the
report generation process to identify where ranks get corrupted.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class RankTracer:
    """Utility class for tracing rank data through the report generation pipeline."""

    def __init__(self, enabled: bool = True):
        """Initialize the rank tracer.
        
        Args:
            enabled: Whether rank tracing is enabled
        """
        self.enabled = enabled

    def trace_ranks(
        self, 
        step_name: str, 
        data: Any, 
        data_key: str = "data",
        max_ranks: int = 5
    ) -> None:
        """Trace rank values at a specific pipeline step.
        
        Args:
            step_name: Name of the pipeline step
            data: Data to trace ranks from
            data_key: Key to use when data is nested
            max_ranks: Maximum number of ranks to log
        """
        if not self.enabled:
            return

        try:
            # Extract rank data
            if isinstance(data, dict) and data_key in data:
                # Handle nested data structure like {'data': {'highest_use_count_per_blade': [...]}}
                rank_data = data[data_key]
            elif isinstance(data, list):
                # Handle direct list of items
                rank_data = data
            else:
                logger.warning(f"[RANK_TRACE] {step_name}: Unable to extract rank data from {type(data)}")
                return

            if not isinstance(rank_data, list):
                logger.warning(f"[RANK_TRACE] {step_name}: Rank data is not a list: {type(rank_data)}")
                return

            # Extract ranks from the data
            ranks = []
            for item in rank_data:
                if isinstance(item, dict) and "rank" in item:
                    ranks.append(item["rank"])
                else:
                    ranks.append("N/A")

            # Log the rank information
            if ranks:
                first_ranks = ranks[:max_ranks]
                total_items = len(ranks)
                logger.info(
                    f"[RANK_TRACE] {step_name}: "
                    f"Total items: {total_items}, "
                    f"First {len(first_ranks)} ranks: {first_ranks}"
                )
                
                # Check for rank corruption patterns
                if len(set(ranks)) == 1 and ranks[0] != "N/A":
                    logger.warning(
                        f"[RANK_TRACE] {step_name}: "
                        f"POTENTIAL RANK CORRUPTION - All ranks are {ranks[0]}"
                    )
                elif "N/A" in ranks:
                    logger.warning(
                        f"[RANK_TRACE] {step_name}: "
                        f"Missing rank data - {ranks.count('N/A')}/{total_items} items have no rank"
                    )
            else:
                logger.warning(f"[RANK_TRACE] {step_name}: No rank data found")

        except Exception as e:
            logger.error(f"[RANK_TRACE] {step_name}: Error tracing ranks: {e}")

    def trace_rank_transformation(
        self,
        step_name: str,
        input_data: List[Dict[str, Any]],
        output_data: List[Dict[str, Any]],
        input_key: str = "data",
        output_key: str = "data"
    ) -> None:
        """Trace rank transformation between input and output data.
        
        Args:
            step_name: Name of the transformation step
            input_data: Input data before transformation
            output_data: Output data after transformation
            input_key: Key for input data extraction
            output_key: Key for output data extraction
        """
        if not self.enabled:
            return

        try:
            # Extract input ranks
            input_ranks = self._extract_ranks(input_data, input_key)
            output_ranks = self._extract_ranks(output_data, output_key)

            if input_ranks and output_ranks:
                logger.info(
                    f"[RANK_TRACE] {step_name}: "
                    f"Input ranks: {input_ranks[:5]}... (total: {len(input_ranks)}), "
                    f"Output ranks: {output_ranks[:5]}... (total: {len(output_ranks)})"
                )

                # Check for rank corruption
                if input_ranks != output_ranks:
                    logger.warning(
                        f"[RANK_TRACE] {step_name}: "
                        f"RANK CORRUPTION DETECTED! "
                        f"Input and output ranks differ: {input_ranks[:5]} vs {output_ranks[:5]}"
                    )
                else:
                    logger.info(f"[RANK_TRACE] {step_name}: Ranks preserved correctly")

        except Exception as e:
            logger.error(f"[RANK_TRACE] {step_name}: Error tracing rank transformation: {e}")

    def _extract_ranks(self, data: Any, data_key: str) -> List[Any]:
        """Extract ranks from data structure.
        
        Args:
            data: Data to extract ranks from
            data_key: Key to use when data is nested
            
        Returns:
            List of rank values
        """
        try:
            if isinstance(data, dict) and data_key in data:
                rank_data = data[data_key]
            elif isinstance(data, list):
                rank_data = data
            else:
                return []

            if not isinstance(rank_data, list):
                return []

            ranks = []
            for item in rank_data:
                if isinstance(item, dict) and "rank" in item:
                    ranks.append(item["rank"])
                else:
                    ranks.append("N/A")

            return ranks

        except Exception:
            return []

    def trace_markdown_ranks(
        self, 
        step_name: str, 
        markdown_content: str,
        table_name: str = "highest-use-count-per-blade"
    ) -> None:
        """Trace ranks from markdown table content.
        
        Args:
            step_name: Name of the pipeline step
            markdown_content: Markdown table content to parse
            table_name: Name of the table being traced
        """
        if not self.enabled:
            return

        try:
            # Parse markdown table to extract rank numbers from first column
            
            # Look for rank patterns in markdown table
            # Pattern: | 1 | u/user | Blade | Format | uses |
            # We want to match the first column (rank) specifically
            lines = markdown_content.strip().split('\n')
            ranks = []
            
            for line in lines:
                if line.startswith('|') and '|' in line[1:]:
                    # Split by | and get the first data column (index 1, since index 0 is empty)
                    parts = line.split('|')
                    if len(parts) >= 2:
                        first_col = parts[1].strip()
                        if first_col.isdigit():
                            ranks.append(first_col)
            
            if ranks:
                # Convert to integers
                rank_numbers = [int(r) for r in ranks]
                first_ranks = rank_numbers[:5]
                total_items = len(rank_numbers)
                
                logger.info(
                    f"[RANK_TRACE] {step_name} (Markdown): "
                    f"Total items: {total_items}, "
                    f"First {len(first_ranks)} ranks: {first_ranks}"
                )
                
                # Check for rank corruption in markdown
                if len(set(rank_numbers)) == 1:
                    logger.warning(
                        f"[RANK_TRACE] {step_name} (Markdown): "
                        f"POTENTIAL RANK CORRUPTION - All ranks are {rank_numbers[0]}"
                    )
                elif rank_numbers != sorted(rank_numbers):
                    logger.warning(
                        f"[RANK_TRACE] {step_name} (Markdown): "
                        f"Ranks are not sequential: {rank_numbers[:5]}..."
                    )
            else:
                logger.warning(f"[RANK_TRACE] {step_name} (Markdown): No rank data found in markdown")

        except Exception as e:
            logger.error(f"[RANK_TRACE] {step_name} (Markdown): Error tracing markdown ranks: {e}")

    def enable(self) -> None:
        """Enable rank tracing."""
        self.enabled = True
        logger.info("[RANK_TRACE] Rank tracing enabled")

    def disable(self) -> None:
        """Disable rank tracing."""
        self.enabled = False
        logger.info("[RANK_TRACE] Rank tracing disabled")

    def is_enabled(self) -> bool:
        """Check if rank tracing is enabled."""
        return self.enabled


# Global rank tracer instance
_rank_tracer = RankTracer()


def get_rank_tracer() -> RankTracer:
    """Get the global rank tracer instance."""
    return _rank_tracer


def enable_rank_tracing() -> None:
    """Enable global rank tracing."""
    _rank_tracer.enable()


def disable_rank_tracing() -> None:
    """Disable global rank tracing."""
    _rank_tracer.disable()


def trace_ranks(step_name: str, data: List[Dict[str, Any]], **kwargs) -> None:
    """Convenience function to trace ranks using the global tracer."""
    _rank_tracer.trace_ranks(step_name, data, **kwargs)


def trace_rank_transformation(step_name: str, input_data: Any, output_data: Any, **kwargs) -> None:
    """Convenience function to trace rank transformation using the global tracer."""
    _rank_tracer.trace_rank_transformation(step_name, input_data, output_data, **kwargs)


def trace_markdown_ranks(step_name: str, markdown_content: str, **kwargs) -> None:
    """Convenience function to trace ranks from markdown using the global tracer."""
    _rank_tracer.trace_markdown_ranks(step_name, markdown_content, **kwargs)
