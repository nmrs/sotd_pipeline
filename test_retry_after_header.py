#!/usr/bin/env python3
"""Test if Reddit sends Retry-After headers in 429 responses."""

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

def test_retry_after():
    """Make rapid requests until we get a 429, then inspect the response headers."""
    cookies = get_test_cookies()
    if not cookies:
        print("[ERROR] No test cookie found")
        return
    
    session = get_reddit_session(cookies=cookies)
    url = "https://www.reddit.com/r/wetshaving/about.json"
    
    print("Making rapid requests until we hit a 429...")
    print("=" * 60)
    
    request_count = 0
    start_time = time.time()
    
    while True:
        request_count += 1
        try:
            response = session.get(url, timeout=10)
            
            if response.status_code == 429:
                print(f"\n✅ Got 429 on request #{request_count}")
                print(f"Time elapsed: {time.time() - start_time:.2f}s")
                print(f"Requests per second: {request_count / (time.time() - start_time):.2f}")
                print("\n" + "=" * 60)
                print("429 RESPONSE HEADERS:")
                print("=" * 60)
                
                # Print all headers
                for header_name, header_value in response.headers.items():
                    print(f"{header_name}: {header_value}")
                
                # Specifically check for Retry-After
                retry_after = response.headers.get("Retry-After")
                if retry_after:
                    print(f"\n✅ Retry-After header found: {retry_after}")
                    print(f"   Type: {type(retry_after)}")
                    print(f"   Value (as int): {int(retry_after) if retry_after.isdigit() else 'N/A'}")
                else:
                    print("\n❌ No Retry-After header found")
                
                # Check for other rate limit related headers
                print("\n" + "=" * 60)
                print("RATE LIMIT RELATED HEADERS:")
                print("=" * 60)
                rate_limit_headers = [
                    "Retry-After",
                    "X-RateLimit-Remaining",
                    "X-RateLimit-Used",
                    "X-RateLimit-Reset",
                    "X-Ratelimit-Remaining",
                    "X-Ratelimit-Used",
                    "X-Ratelimit-Reset",
                ]
                found_any = False
                for header in rate_limit_headers:
                    value = response.headers.get(header)
                    if value:
                        print(f"✅ {header}: {value}")
                        found_any = True
                
                if not found_any:
                    print("❌ No rate limit headers found")
                
                # Print response body (might have useful info)
                print("\n" + "=" * 60)
                print("RESPONSE BODY (first 500 chars):")
                print("=" * 60)
                try:
                    body = response.text[:500]
                    print(body)
                except:
                    print("Could not read response body")
                
                break
            elif response.status_code == 200:
                if request_count % 10 == 0:
                    print(f"Request {request_count}: 200 OK")
            else:
                print(f"Request {request_count}: {response.status_code}")
                break
            
            # Small delay to avoid overwhelming
            time.sleep(0.1)
            
        except Exception as e:
            print(f"\n[ERROR] Request {request_count} failed: {e}")
            break
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_retry_after()
