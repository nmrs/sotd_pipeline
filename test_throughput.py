#!/usr/bin/env python3
"""Test actual throughput - how many requests can we make before rate limit."""

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

def test_throughput():
    """Test how many requests we can make before hitting rate limits."""
    cookies = get_test_cookies()
    if not cookies:
        print("[ERROR] No test cookie found")
        return
    
    session = get_reddit_session(cookies=cookies)
    url = "https://www.reddit.com/r/wetshaving/about.json"
    
    print("=" * 60)
    print("THROUGHPUT TEST")
    print("=" * 60)
    print("Making requests with 0.1s delay until we hit rate limit...")
    print("This will show actual throughput capacity.\n")
    
    successful_requests = 0
    rate_limited_requests = 0
    start_time = time.time()
    first_429_time = None
    
    # Track rate limit headers from successful requests
    rate_limit_info = []
    
    while True:
        try:
            response = session.get(url, timeout=10)
            
            if response.status_code == 429:
                if first_429_time is None:
                    first_429_time = time.time()
                    elapsed = first_429_time - start_time
                    
                    print(f"\n{'='*60}")
                    print(f"RATE LIMIT HIT!")
                    print(f"{'='*60}")
                    print(f"Successful requests before rate limit: {successful_requests}")
                    print(f"Time elapsed: {elapsed:.2f} seconds")
                    print(f"Requests per second: {successful_requests / elapsed:.2f}")
                    print(f"Requests per minute: {(successful_requests / elapsed) * 60:.2f}")
                    
                    # Show rate limit headers
                    reset_time = response.headers.get("x-ratelimit-reset") or response.headers.get("X-RateLimit-Reset")
                    used = response.headers.get("x-ratelimit-used") or response.headers.get("X-RateLimit-Used")
                    remaining = response.headers.get("x-ratelimit-remaining") or response.headers.get("X-RateLimit-Remaining")
                    
                    print(f"\nRate limit info from 429 response:")
                    if reset_time:
                        print(f"  Reset in: {reset_time} seconds ({int(reset_time)/60:.1f} minutes)")
                    if used:
                        print(f"  Used: {used}%")
                    if remaining:
                        print(f"  Remaining: {remaining}%")
                    
                    # Show last successful request's rate limit info
                    if rate_limit_info:
                        last_info = rate_limit_info[-1]
                        print(f"\nLast successful request rate limit info:")
                        print(f"  Used: {last_info.get('used', 'N/A')}%")
                        print(f"  Remaining: {last_info.get('remaining', 'N/A')}%")
                        print(f"  Reset in: {last_info.get('reset', 'N/A')} seconds")
                    
                    break
                else:
                    rate_limited_requests += 1
                    if rate_limited_requests > 3:
                        print("\n[WARN] Still rate limited after multiple requests, stopping test")
                        break
                    
            elif response.status_code == 200:
                successful_requests += 1
                
                # Track rate limit info
                reset = response.headers.get("x-ratelimit-reset") or response.headers.get("X-RateLimit-Reset")
                used = response.headers.get("x-ratelimit-used") or response.headers.get("X-RateLimit-Used")
                remaining = response.headers.get("x-ratelimit-remaining") or response.headers.get("X-RateLimit-Remaining")
                
                if reset or used or remaining:
                    rate_limit_info.append({
                        "request": successful_requests,
                        "reset": reset,
                        "used": used,
                        "remaining": remaining,
                    })
                
                # Print progress every 10 requests
                if successful_requests % 10 == 0:
                    elapsed = time.time() - start_time
                    rate = successful_requests / elapsed
                    print(f"Request {successful_requests}: ✅ (rate: {rate:.2f} req/s, {rate*60:.1f} req/min)")
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
    
    total_time = time.time() - start_time
    
    print(f"\n{'='*60}")
    print("FINAL RESULTS")
    print(f"{'='*60}")
    print(f"Total successful requests: {successful_requests}")
    print(f"Total time: {total_time:.2f} seconds")
    if successful_requests > 0:
        print(f"Average rate: {successful_requests / total_time:.2f} requests/second")
        print(f"Average rate: {(successful_requests / total_time) * 60:.1f} requests/minute")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    # Wait until 12:54 PM
    target_time = datetime.now().replace(hour=12, minute=54, second=0, microsecond=0)
    current_time = datetime.now()
    
    if current_time < target_time:
        wait_seconds = (target_time - current_time).total_seconds()
        print(f"Waiting until 12:54 PM ({wait_seconds:.0f} seconds)...")
        print(f"Current time: {current_time.strftime('%H:%M:%S')}")
        print(f"Target time: {target_time.strftime('%H:%M:%S')}\n")
        time.sleep(wait_seconds)
    
    print(f"Starting test at {datetime.now().strftime('%H:%M:%S')}\n")
    test_throughput()
