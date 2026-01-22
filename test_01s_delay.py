#!/usr/bin/env python3
"""Test 0.1s delay to see if we hit rate limits with more requests.

This script uses a test cookie file (.reddit_cookies_test.json) to avoid
risking the main account. Set REDDIT_SESSION_COOKIE_TEST environment variable
or create .reddit_cookies_test.json with your test account cookie.
"""

import json
import os
import time
from pathlib import Path
import requests
from sotd.fetch_via_json.json_scraper import get_reddit_session, _find_project_root

def get_test_cookies() -> dict:
    """Get test account cookies from test cookie file or environment variable."""
    # Check environment variable first
    test_cookie_env = os.getenv("REDDIT_SESSION_COOKIE_TEST")
    if test_cookie_env:
        return {"reddit_session": test_cookie_env}
    
    # Check test cookie file
    project_root = _find_project_root()
    test_cookie_file = project_root / ".reddit_cookies_test.json"
    
    if test_cookie_file.exists():
        try:
            with open(test_cookie_file, "r") as f:
                cookie_data = json.load(f)
                if "reddit_session" in cookie_data:
                    return {"reddit_session": cookie_data["reddit_session"]}
        except Exception as e:
            print(f"[WARN] Could not read test cookie file: {e}")
    
    # Fallback to regular cookies (but warn)
    print("[WARN] No test cookie found. Using regular cookies (risky for rate limit testing!)")
    print(f"       Set REDDIT_SESSION_COOKIE_TEST or create {test_cookie_file}")
    from sotd.fetch_via_json.json_scraper import get_reddit_cookies
    return get_reddit_cookies()


def test_01s_delay():
    """Test 0.1s delay with many requests to check for rate limits."""
    cookies = get_test_cookies()
    session = get_reddit_session(cookies=cookies)
    
    url = "https://www.reddit.com/r/wetshaving/about.json"
    
    print("Testing 0.1s delay with many requests...")
    print(f"Using test cookie: {bool(cookies)}\n")
    if not cookies:
        print("[ERROR] No cookies available. Cannot test.")
        return
    print("This will make 100 requests with 0.1s delay between each")
    print("=" * 60)
    
    successful = 0
    rate_limited = 0
    errors = 0
    retry_after_times = []
    
    start_time = time.time()
    
    for i in range(100):
        req_start = time.time()
        try:
            response = session.get(url, timeout=10)
            req_time = time.time() - req_start
            
            if response.status_code == 429:
                rate_limited += 1
                retry_after = response.headers.get("Retry-After")
                if retry_after:
                    retry_after_times.append(int(retry_after))
                    print(f"Request {i+1}: 429 Rate Limited! Retry-After: {retry_after}s")
                    # Wait as instructed
                    time.sleep(int(retry_after))
                else:
                    print(f"Request {i+1}: 429 Rate Limited! (no Retry-After header)")
            elif response.status_code == 200:
                successful += 1
                # Only print first few and then every 20th
                if i < 5 or (i + 1) % 20 == 0:
                    print(f"Request {i+1}: 200 OK ({req_time:.2f}s)")
            else:
                errors += 1
                print(f"Request {i+1}: {response.status_code} ({req_time:.2f}s)")
        except Exception as e:
            errors += 1
            print(f"Request {i+1}: ERROR - {e}")
        
        # 0.1s delay between requests
        time.sleep(0.1)
    
    total_time = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("RESULTS:")
    print("=" * 60)
    print(f"Total requests: 100")
    print(f"Successful (200): {successful}")
    print(f"Rate limited (429): {rate_limited}")
    print(f"Errors: {errors}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Average per request: {total_time/100:.2f}s")
    print(f"Requests per minute: {60 / (total_time/100):.1f}")
    
    if retry_after_times:
        print(f"\nRetry-After values seen: {retry_after_times}")
        print(f"Average Retry-After: {sum(retry_after_times)/len(retry_after_times):.1f}s")
    
    if rate_limited == 0:
        print("\n✅ No rate limits hit with 0.1s delay!")
        print("   This suggests 0.1s delay is safe for this endpoint.")
    else:
        print(f"\n⚠️  Hit {rate_limited} rate limits with 0.1s delay")
        print("   May need to increase delay or respect Retry-After headers")
    
    # Test per-minute rate limit
    print("\n" + "=" * 60)
    print("Testing per-minute rate limit...")
    print("=" * 60)
    print("Making 70 requests in rapid succession (to test 60/min limit)...")
    
    successful = 0
    rate_limited = 0
    minute_start = time.time()
    
    for i in range(70):
        try:
            response = session.get(url, timeout=10)
            if response.status_code == 429:
                rate_limited += 1
                retry_after = response.headers.get("Retry-After")
                if retry_after:
                    print(f"Request {i+1}: 429! Retry-After: {retry_after}s")
                    time.sleep(int(retry_after))
            elif response.status_code == 200:
                successful += 1
        except Exception as e:
            print(f"Request {i+1}: ERROR - {e}")
        
        time.sleep(0.1)
    
    minute_time = time.time() - minute_start
    requests_per_min = (70 / minute_time) * 60
    
    print(f"\nMade 70 requests in {minute_time:.2f}s")
    print(f"Rate: {requests_per_min:.1f} requests/minute")
    print(f"Successful: {successful}, Rate limited: {rate_limited}")
    
    if rate_limited == 0:
        print("✅ No rate limits even at high request rate!")

if __name__ == "__main__":
    test_01s_delay()
