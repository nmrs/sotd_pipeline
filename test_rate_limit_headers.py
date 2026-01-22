#!/usr/bin/env python3
"""Test what rate limit headers Reddit sends on every request vs only on 429s."""

import os
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any

import requests

def get_test_cookies() -> Optional[dict]:
    """Get test cookies from environment or file."""
    # Check environment variable first
    cookie_value = os.getenv("REDDIT_SESSION_COOKIE_TEST")
    if cookie_value:
        return {"reddit_session": cookie_value}
    
    # Check project root for test cookie file
    project_root = Path(__file__).parent
    cookie_file = project_root / ".reddit_cookies_test.json"
    if cookie_file.exists():
        with open(cookie_file) as f:
            data = json.load(f)
            if "reddit_session" in data:
                return {"reddit_session": data["reddit_session"]}
    
    return None

def test_rate_limit_headers():
    """Test what headers Reddit sends on successful requests."""
    
    cookies = get_test_cookies()
    if not cookies:
        print("ERROR: No test cookie found. Set REDDIT_SESSION_COOKIE_TEST or create .reddit_cookies_test.json")
        return
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    })
    session.cookies.update(cookies)
    
    url = "https://www.reddit.com/r/wetshaving/about.json"
    
    print("=" * 60)
    print("TESTING RATE LIMIT HEADERS ON SUCCESSFUL REQUESTS")
    print("=" * 60)
    print(f"\nMaking 10 requests to: {url}")
    print("Checking headers on each response...\n")
    
    rate_limit_headers_found = set()
    all_headers_seen = set()
    
    for i in range(1, 11):
        response = session.get(url, timeout=30)
        
        if response.status_code == 200:
            # Check for rate limit headers (case-insensitive)
            headers = response.headers
            rate_limit_related = {}
            
            for header_name, header_value in headers.items():
                all_headers_seen.add(header_name.lower())
                header_lower = header_name.lower()
                
                if any(keyword in header_lower for keyword in ['ratelimit', 'rate-limit', 'rate_limit', 'retry']):
                    rate_limit_related[header_name] = header_value
                    rate_limit_headers_found.add(header_name.lower())
            
            if rate_limit_related:
                print(f"Request {i} (200 OK):")
                for name, value in rate_limit_related.items():
                    print(f"  {name}: {value}")
            else:
                print(f"Request {i} (200 OK): No rate limit headers found")
            
            # Small delay to avoid hitting rate limit
            time.sleep(0.5)
        else:
            print(f"Request {i} ({response.status_code}):")
            # Check headers even on non-200
            for header_name, header_value in response.headers.items():
                header_lower = header_name.lower()
                if any(keyword in header_lower for keyword in ['ratelimit', 'rate-limit', 'rate_limit', 'retry']):
                    print(f"  {header_name}: {header_value}")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"\nRate limit headers found: {sorted(rate_limit_headers_found)}")
    print(f"\nAll headers seen (sample): {sorted(list(all_headers_seen))[:20]}")
    
    # Now test what happens on a 429
    print("\n" + "=" * 60)
    print("TESTING HEADERS ON 429 RESPONSE")
    print("=" * 60)
    print("\nMaking rapid requests until we hit a 429...\n")
    
    request_count = 0
    while request_count < 150:  # Should hit 429 before this
        response = session.get(url, timeout=30)
        request_count += 1
        
        if response.status_code == 429:
            print(f"Got 429 at request {request_count}")
            print("\nAll headers on 429 response:")
            for header_name, header_value in sorted(response.headers.items()):
                print(f"  {header_name}: {header_value}")
            break
        
        if request_count % 20 == 0:
            print(f"Request {request_count}: {response.status_code}")
        
        time.sleep(0.1)  # Fast requests to hit rate limit
    
    if request_count >= 150:
        print("Did not hit 429 in 150 requests")

if __name__ == "__main__":
    test_rate_limit_headers()
