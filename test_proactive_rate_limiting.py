#!/usr/bin/env python3
"""Test proactive rate limit management using rate limit headers."""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sotd.fetch_via_json.json_scraper import get_reddit_json, get_reddit_cookies

def test_proactive_rate_limiting():
    """Test that proactive rate limit management works correctly."""
    
    cookies = get_reddit_cookies()
    if not cookies:
        print("ERROR: No cookie found. Set REDDIT_SESSION_COOKIE or create .reddit_cookies.json")
        return
    
    url = "https://www.reddit.com/r/wetshaving/about.json"
    
    print("=" * 60)
    print("TESTING PROACTIVE RATE LIMIT MANAGEMENT")
    print("=" * 60)
    print(f"\nMaking 30 requests to: {url}")
    print("Monitoring rate limit headers and dynamic delay adjustments...\n")
    
    for i in range(1, 31):
        try:
            # Use verbose=True to see rate limit info
            data = get_reddit_json(url, cookies=cookies, verbose=(i % 10 == 0))
            
            if i % 10 == 0:
                print(f"Request {i} completed successfully")
        except Exception as e:
            print(f"Request {i} failed: {e}")
            break
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print("\nIf you see rate limit info printed every 10 requests,")
    print("and no 429 errors, proactive rate limiting is working!")

if __name__ == "__main__":
    test_proactive_rate_limiting()
