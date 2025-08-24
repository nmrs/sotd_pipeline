"""Legacy table generators - moved to preserve functionality during transition."""

# Import all legacy table generators for backward compatibility
from .base import BaseTableGenerator, NoDeltaMixin
from .blade_tables import (
    BladeManufacturersTableGenerator,
    BladesTableGenerator,
    BladeUsageDistributionTableGenerator,
)
from .brush_tables import (
    BrushesTableGenerator,
    BrushFibersTableGenerator,
    BrushHandleMakersTableGenerator,
    BrushKnotMakersTableGenerator,
    BrushKnotSizesTableGenerator,
)
from .cross_product_tables import (
    HighestUseCountPerBladeTableGenerator,
    RazorBladeCombinationsTableGenerator,
)
from .razor_tables import (
    RazorFormatsTableGenerator,
    RazorManufacturersTableGenerator,
    RazorsTableGenerator,
)
from .soap_tables import (
    BrandDiversityTableGenerator,
    SoapBrandsTableGenerator,
    SoapMakersTableGenerator,
    SoapsTableGenerator,
    TopSampledSoapsTableGenerator,
)
from .specialized_tables import (
    BlackbirdPlatesTableGenerator,
    ChristopherBradleyPlatesTableGenerator,
    GameChangerPlatesTableGenerator,
    StraightGrindsTableGenerator,
    StraightPointsTableGenerator,
    StraightWidthsTableGenerator,
    SuperSpeedTipsTableGenerator,
)
from .user_tables import TopShaversTableGenerator

__all__ = [
    # Base classes
    "BaseTableGenerator",
    "NoDeltaMixin",
    # Soap tables
    "SoapMakersTableGenerator",
    "SoapsTableGenerator",
    "TopSampledSoapsTableGenerator",
    "SoapBrandsTableGenerator",
    "BrandDiversityTableGenerator",
    # Specialized tables
    "BlackbirdPlatesTableGenerator",
    "ChristopherBradleyPlatesTableGenerator",
    "GameChangerPlatesTableGenerator",
    "StraightGrindsTableGenerator",
    "StraightPointsTableGenerator",
    "StraightWidthsTableGenerator",
    "SuperSpeedTipsTableGenerator",
    # Brush tables
    "BrushesTableGenerator",
    "BrushFibersTableGenerator",
    "BrushHandleMakersTableGenerator",
    "BrushKnotMakersTableGenerator",
    "BrushKnotSizesTableGenerator",
    # Razor tables
    "RazorFormatsTableGenerator",
    "RazorManufacturersTableGenerator",
    "RazorsTableGenerator",
    # Cross-product tables
    "HighestUseCountPerBladeTableGenerator",
    "RazorBladeCombinationsTableGenerator",
    # Blade tables
    "BladeManufacturersTableGenerator",
    "BladesTableGenerator",
    "BladeUsageDistributionTableGenerator",
    # User tables
    "TopShaversTableGenerator",
]
