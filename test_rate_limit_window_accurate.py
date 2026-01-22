#!/usr/bin/env python3
"""Accurately measure Reddit's rate limit window duration.

This test determines the exact rate limit window by:
1. Recording start time
2. Making requests until hitting 429
3. Capturing time elapsed and remaining reset time
4. Calculating: window_duration = time_elapsed + reset_time
5. Reporting: "X requests per Y time" with accurate measurements
"""

import json
import time
from datetime import datetime
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
    """Test to accurately determine Reddit's rate limit window duration."""
    cookies = get_test_cookies()
    if not cookies:
        print("[ERROR] No test cookie found")
        print("Create .reddit_cookies_test.json in project root with test account cookie")
        return
    
    session = get_reddit_session(cookies=cookies)
    url = "https://www.reddit.com/r/wetshaving/about.json"
    
    print("=" * 60)
    print("RATE LIMIT WINDOW MEASUREMENT")
    print("=" * 60)
    
    # Record exact start time
    start_time = time.time()
    start_datetime = datetime.fromtimestamp(start_time)
    print(f"Start time: {start_datetime.strftime('%H:%M:%S')}")
    print("\nMaking requests until rate limit...")
    print("(Using 0.1s delay between requests)\n")
    
    successful_requests = 0
    first_429_time = None
    reset_time_remaining = None
    rate_limit_used = None
    rate_limit_remaining = None
    
    # Make requests until we hit the limit
    while True:
        try:
            response = session.get(url, timeout=10)
            
            if response.status_code == 429:
                if first_429_time is None:
                    first_429_time = time.time()
                    time_elapsed = first_429_time - start_time
                    
                    # Extract rate limit headers (check both case variations)
                    reset_time_remaining = (
                        response.headers.get("x-ratelimit-reset") 
                        or response.headers.get("X-RateLimit-Reset")
                    )
                    rate_limit_used = (
                        response.headers.get("x-ratelimit-used")
                        or response.headers.get("X-RateLimit-Used")
                    )
                    rate_limit_remaining = (
                        response.headers.get("x-ratelimit-remaining")
                        or response.headers.get("X-RateLimit-Remaining")
                    )
                    
                    print(f"\n{'='*60}")
                    print("RATE LIMIT HIT")
                    print(f"{'='*60}")
                    print(f"Successful requests: {successful_requests}")
                    print(f"Time elapsed: {time_elapsed:.2f} seconds")
                    
                    if reset_time_remaining:
                        try:
                            reset_seconds = int(float(reset_time_remaining))
                            print(f"Reset time remaining: {reset_seconds} seconds ({reset_seconds/60:.2f} minutes)")
                            print(f"  (from x-ratelimit-reset header)")
                        except (ValueError, TypeError):
                            print(f"Reset time remaining: {reset_time_remaining} (could not parse)")
                    else:
                        print("Reset time remaining: NOT FOUND in headers")
                    
                    if rate_limit_used:
                        print(f"Rate limit used: {rate_limit_used}%")
                    if rate_limit_remaining:
                        print(f"Rate limit remaining: {rate_limit_remaining}%")
                    
                    # Calculate window duration
                    print(f"\n{'='*60}")
                    print("CALCULATED WINDOW DURATION")
                    print(f"{'='*60}")
                    print(f"Time elapsed: {time_elapsed:.2f} seconds")
                    
                    if reset_time_remaining:
                        try:
                            reset_seconds = int(float(reset_time_remaining))
                            window_duration = time_elapsed + reset_seconds
                            print(f"+ Reset remaining: {reset_seconds:.0f} seconds")
                            print(f"= Window duration: {window_duration:.2f} seconds ({window_duration/60:.2f} minutes)")
                            
                            # Final answer
                            print(f"\n{'='*60}")
                            print("FINAL ANSWER")
                            print(f"{'='*60}")
                            print(f"{successful_requests} requests per {window_duration:.2f} seconds")
                            print(f"{successful_requests} requests per {window_duration/60:.2f} minutes")
                            effective_rate = (successful_requests / window_duration) * 60
                            print(f"Effective rate: {effective_rate:.2f} requests/minute")
                            print(f"{'='*60}\n")
                        except (ValueError, TypeError):
                            print("Could not calculate window duration (invalid reset time)")
                    else:
                        print("Could not calculate window duration (no reset time in headers)")
                    
                    break
                else:
                    # Already hit limit, stop
                    break
                    
            elif response.status_code == 200:
                successful_requests += 1
                # Print progress every 10 requests
                if successful_requests % 10 == 0:
                    elapsed = time.time() - start_time
                    print(f"Request {successful_requests}: ✅ ({elapsed:.1f}s elapsed)")
            else:
                print(f"[WARN] Unexpected status: {response.status_code}")
                break
            
            # 0.1s delay between requests
            time.sleep(0.1)
            
        except KeyboardInterrupt:
            print("\n[INFO] Test interrupted by user")
            break
        except Exception as e:
            print(f"\n[ERROR] Request failed: {e}")
            break
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\nTest completed in {total_time:.2f} seconds")
    print(f"End time: {datetime.fromtimestamp(end_time).strftime('%H:%M:%S')}")


if __name__ == "__main__":
    test_rate_limit_window()
