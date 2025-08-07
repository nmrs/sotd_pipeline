"""
Typed data structures for brush matching system.

This module defines dataclasses for all data structures used throughout
the brush matching system to improve type safety and code clarity.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class MatchResult:
    """Unified result structure for all matching operations."""

    # Core data (always present)
    original: str
    matched: Optional[Dict[str, Any]] = None
    match_type: Optional[str] = None
    pattern: Optional[str] = None
    strategy: Optional[str] = None  # Name of the strategy that produced this result

    # DRY scoring fields (optional, for section-based matchers)
    section: Optional[str] = None  # "known_knots", "other_knots", etc.
    priority: Optional[int] = None  # 1 = highest, 2 = medium, 3 = lowest
    score: Optional[float] = None  # Calculated score for this result

    @property
    def matched_bool(self) -> bool:
        """Check if this represents a successful match."""
        return bool(self.matched)

    @property
    def has_section_info(self) -> bool:
        """Check if this has section/priority information for scoring."""
        return self.section is not None and self.priority is not None

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from matched data with default."""
        if self.matched is None:
            return default
        return self.matched.get(key, default)


@dataclass
class StrategyResult:
    """
    Result structure for individual strategy matches.

    Used by brush matching strategies to return consistent results
    that can be processed by the main orchestrator.
    """

    original_value: Any
    matched_data: Optional[Dict[str, Any]] = None
    pattern: Optional[str] = None
    strategy_name: str = ""
    match_type: Optional[str] = None


@dataclass
class CatalogData:
    """
    Structure for loaded catalog data from YAML files.

    Contains all catalog data loaded from brushes.yaml, handles.yaml,
    knots.yaml, and correct_matches.yaml files.
    """

    brushes: Dict[str, Any] = field(default_factory=dict)
    handles: Dict[str, Any] = field(default_factory=dict)
    knots: Dict[str, Any] = field(default_factory=dict)
    correct_matches: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BrushMatchData:
    """
    Standardized structure for brush match data.

    This structure is used internally by the brush matching system
    to represent matched brush information with all required fields.
    """

    brand: Optional[str] = None
    model: Optional[str] = None
    fiber: Optional[str] = None
    knot_size_mm: Optional[float] = None
    handle_maker: Optional[str] = None
    knot_maker: Optional[str] = None
    fiber_strategy: Optional[str] = None
    fiber_conflict: Optional[str] = None
    _matched_by_strategy: Optional[str] = None
    _pattern_used: Optional[str] = None
    _matched_from: Optional[str] = None
    _original_knot_text: Optional[str] = None
    _original_handle_text: Optional[str] = None


@dataclass
class HandleKnotData:
    """
    Structure for handle/knot subsection data.

    Used when brush input is split into handle and knot components.
    """

    brand: Optional[str] = None
    model: Optional[str] = None
    source_text: Optional[str] = None
    fiber: Optional[str] = None
    knot_size_mm: Optional[float] = None


@dataclass
class CorrectMatchData:
    """
    Structure for correct match data from correct_matches.yaml.

    Represents a match found in the correct_matches.yaml file,
    supporting both brush section and handle/knot section matches.
    """

    brand: Optional[str] = None
    model: Optional[str] = None
    handle_maker: Optional[str] = None
    handle_model: Optional[str] = None
    knot_info: Optional[Dict[str, Any]] = None
    # "brush_section", "handle_knot_section", or "split_brush_section"
    match_type: str = "brush_section"
    # Split brush fields
    handle_component: Optional[str] = None
    knot_component: Optional[str] = None


@dataclass
class PatternMetadata:
    """
    Metadata structure for compiled patterns.

    Used by pattern compilation utilities to store pattern metadata
    along with compiled regex patterns.
    """

    pattern: str
    compiled: Any  # re.Pattern
    brand: Optional[str] = None
    model: Optional[str] = None
    fiber: Optional[str] = None
    knot_size_mm: Optional[float] = None
    handle_maker: Optional[str] = None


@dataclass
class CatalogEntry:
    """
    Structure for individual catalog entries.

    Represents a single entry in a catalog (brushes, handles, knots)
    with all associated metadata and patterns.
    """

    brand: str
    model: Optional[str] = None
    patterns: List[str] = field(default_factory=list)
    fiber: Optional[str] = None
    knot_size_mm: Optional[float] = None
    handle_maker: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MatchStatistics:
    """
    Statistics structure for match operations.

    Used to track performance and success rates of matching operations.
    """

    total_attempts: int = 0
    successful_matches: int = 0
    correct_match_hits: int = 0
    strategy_matches: int = 0
    fallback_matches: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    average_response_time: float = 0.0


@dataclass
class ValidationResult:
    """
    Structure for validation results.

    Used by validation utilities to return structured validation results
    with error details and success status.
    """

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    field_name: Optional[str] = None


# Type aliases for common patterns
MatchDict = Dict[str, Any]
CatalogDict = Dict[str, Any]
PatternList = List[Dict[str, Any]]
StrategyList = List[Any]  # List of strategy objects


class MatchType:
    """Constants for match types to improve semantic clarity."""

    EXACT = "exact"  # From correct_matches.yaml (manually verified)
    REGEX = "regex"  # From regex patterns in YAML catalogs
    ALIAS = "alias"  # Brand/model aliases
    BRAND = "brand"  # Brand-only fallback
    UNMATCHED = "unmatched"  # No match found

    # Intentional skipping scenarios
    FILTERED = "filtered"  # From intentionally_unmatched.yaml (user filtered)
    IRRELEVANT_RAZOR_FORMAT = (
        "irrelevant_razor_format"  # Blade irrelevant for razor format (straight, cartridge, etc.)
    )


def create_match_result(
    original: str,
    matched: Optional[Dict[str, Any]],
    match_type: Optional[str],
    pattern: Optional[str],
    strategy: Optional[str] = None,
) -> "MatchResult":
    """Create a MatchResult from legacy match data."""
    # This is a compatibility function for existing code
    # In the future, matchers should return MatchResult directly
    return MatchResult(
        original=original,
        matched=matched,
        match_type=match_type,
        pattern=pattern,
        strategy=strategy,
    )


def create_brush_match_data(
    brand: Optional[str] = None,
    model: Optional[str] = None,
    fiber: Optional[str] = None,
    knot_size_mm: Optional[float] = None,
    handle_maker: Optional[str] = None,
    knot_maker: Optional[str] = None,
    **kwargs: Any,
) -> BrushMatchData:
    """
    Create a BrushMatchData instance with proper defaults.

    Args:
        brand: Brand name
        model: Model name
        fiber: Fiber type
        knot_size_mm: Knot size in mm
        handle_maker: Handle maker
        knot_maker: Knot maker
        **kwargs: Additional fields

    Returns:
        BrushMatchData instance
    """
    data = BrushMatchData(
        brand=brand,
        model=model,
        fiber=fiber,
        knot_size_mm=knot_size_mm,
        handle_maker=handle_maker,
        knot_maker=knot_maker,
    )

    # Add any additional fields
    for key, value in kwargs.items():
        if hasattr(data, key):
            setattr(data, key, value)

    return data


def create_catalog_data(
    brushes: Optional[Dict[str, Any]] = None,
    handles: Optional[Dict[str, Any]] = None,
    knots: Optional[Dict[str, Any]] = None,
    correct_matches: Optional[Dict[str, Any]] = None,
) -> CatalogData:
    """
    Create a CatalogData instance with proper defaults.

    Args:
        brushes: Brushes catalog data
        handles: Handles catalog data
        knots: Knots catalog data
        correct_matches: Correct matches data

    Returns:
        CatalogData instance
    """
    return CatalogData(
        brushes=brushes or {},
        handles=handles or {},
        knots=knots or {},
        correct_matches=correct_matches or {},
    )


def dict_to_brush_match_data(data: Dict[str, Any]) -> BrushMatchData:
    """
    Convert a dictionary to BrushMatchData.

    Args:
        data: Dictionary with brush match data

    Returns:
        BrushMatchData instance
    """
    return BrushMatchData(**data)


def brush_match_data_to_dict(data: BrushMatchData) -> Dict[str, Any]:
    """
    Convert BrushMatchData to dictionary.

    Args:
        data: BrushMatchData instance

    Returns:
        Dictionary representation
    """
    return {
        "brand": data.brand,
        "model": data.model,
        "fiber": data.fiber,
        "knot_size_mm": data.knot_size_mm,
        "handle_maker": data.handle_maker,
        "knot_maker": data.knot_maker,
        "fiber_strategy": data.fiber_strategy,
        "fiber_conflict": data.fiber_conflict,
        "_matched_by_strategy": data._matched_by_strategy,
        "_pattern_used": data._pattern_used,
        "_matched_from": data._matched_from,
        "_original_knot_text": data._original_knot_text,
        "_original_handle_text": data._original_handle_text,
    }
