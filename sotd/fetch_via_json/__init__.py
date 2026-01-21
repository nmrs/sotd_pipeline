"""HTML-based Reddit fetch implementation.

This module provides an alternative to the PRAW-based fetch implementation,
using HTML scraping instead of the Reddit API. This enables A/B testing
and provides a fallback when Reddit API access is restricted.
"""
