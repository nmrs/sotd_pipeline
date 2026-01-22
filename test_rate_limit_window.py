#!/usr/bin/env python3
"""Test to determine the actual rate limit window duration."""

import json
import time
from pathlib import Path
import requests
from sotd.fetch_via_json.json_scraper import get_reddit_session, _find_project_root

def get_test_cookies() -> dict:
    """Get test account cookies."""
    test_file = _find_project_root() / ".reddit_cookies_test.json"
    if test_file.exists():
        with open(test_file) as f:
            cookie_data = json.load(f)
        return {"reddit_session": cookie_data["reddit_session"]}
    return {}

def test_rate_limit_window():
    """Test to determine the rate limit window."""
    cookies = get_test_cookies()
    if not cookies:
        print("[ERROR] No test cookie found")
        return
    
    session = get_reddit_session(cookies=cookies)
    url = "https://www.reddit.com/r/wetshaving/about.json"
    
    print("=" * 60)
    print("RATE LIMIT WINDOW TEST")
    print("=" * 60)
    print("Making requests to hit rate limit, then checking reset time...\n")
    
    # Make requests until we hit the limit
    print("Step 1: Making requests until rate limit...")
    request_count = 0
    while request_count < 110:  # Make a few extra to be sure
        response = session.get(url, timeout=10)
        if response.status_code == 429:
            reset_time = response.headers.get("x-ratelimit-reset") or response.headers.get("X-RateLimit-Reset")
            print(f"Hit rate limit at request #{request_count}")
            print(f"Reset time from header: {reset_time} seconds ({int(reset_time)/60:.1f} minutes)")
            break
        elif response.status_code == 200:
            request_count += 1
            if request_count % 20 == 0:
                print(f"  Made {request_count} requests...")
        time.sleep(0.1)
    
    # Get the reset time
    response = session.get(url, timeout=10)
    if response.status_code == 429:
        reset_time_str = response.headers.get("x-ratelimit-reset") or response.headers.get("X-RateLimit-Reset")
        if reset_time_str:
            reset_time = int(float(reset_time_str))
            print(f"\nStep 2: Rate limit reset time: {reset_time} seconds ({reset_time/60:.1f} minutes)")
            print(f"\nConclusion:")
            print(f"  - Max requests per window: 100")
            print(f"  - Window duration: ~{reset_time/60:.1f} minutes ({reset_time} seconds)")
            print(f"  - Effective rate: {100 / (reset_time/60):.1f} requests/minute")
            print(f"  - Or: {100} requests per {reset_time/60:.1f} minute window")
        else:
            print("Could not determine reset time")
    else:
        print(f"Unexpected: got status {response.status_code}")

if __name__ == "__main__":
    test_rate_limit_window()
