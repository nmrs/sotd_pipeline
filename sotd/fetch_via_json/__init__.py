"""JSON-based Reddit fetch implementation.

This module provides an alternative to the PRAW-based fetch implementation,
using Reddit's public JSON endpoints instead of the PRAW API. This enables A/B testing
and provides a fallback when Reddit API access is restricted.

No OAuth or client credentials required - uses public JSON endpoints.
"""
