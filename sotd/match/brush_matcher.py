"""
Brush Matcher Entry Point

This module provides backward compatibility for existing imports.
The actual implementation is now in the brush/ module.
"""

from sotd.match.brush.matcher import BrushMatcher
from sotd.match.brush.config import BrushMatcherConfig

# Re-export for backward compatibility
__all__ = ['BrushMatcher', 'BrushMatcherConfig']
