#!/usr/bin/env python3
"""Test actual Reddit rate limits by making requests without delays."""

import time
import requests
from sotd.fetch_via_json.json_scraper import get_reddit_cookies, get_reddit_session

def test_rate_limits():
    """Test what rate limits Reddit actually enforces."""
    cookies = get_reddit_cookies()
    session = get_reddit_session(cookies=cookies)
    
    url = "https://www.reddit.com/r/wetshaving/about.json"
    
    print("Testing actual Reddit rate limits...")
    print(f"Using cookie auth: {bool(cookies)}\n")
    
    # Test 1: Rapid requests (no delay) to see when we hit limits
    print("=" * 60)
    print("Test 1: Rapid requests (no delay between requests)")
    print("=" * 60)
    
    rate_limited = False
    rate_limit_count = 0
    successful = 0
    
    for i in range(20):
        start = time.time()
        try:
            response = session.get(url, timeout=10)
            elapsed = time.time() - start
            
            if response.status_code == 429:
                rate_limited = True
                rate_limit_count += 1
                retry_after = response.headers.get("Retry-After", "N/A")
                print(f"Request {i+1}: 429 Rate Limited! Retry-After: {retry_after}s (elapsed: {elapsed:.2f}s)")
                if retry_after != "N/A":
                    print(f"  Waiting {retry_after}s as instructed...")
                    time.sleep(int(retry_after))
            elif response.status_code == 200:
                successful += 1
                print(f"Request {i+1}: 200 OK (elapsed: {elapsed:.2f}s)")
            else:
                print(f"Request {i+1}: {response.status_code} (elapsed: {elapsed:.2f}s)")
        except Exception as e:
            print(f"Request {i+1}: ERROR - {e}")
        
        # Small delay to avoid overwhelming
        time.sleep(0.1)
    
    print(f"\nResults: {successful} successful, {rate_limit_count} rate limited")
    
    # Test 2: With 0.5s delay
    print("\n" + "=" * 60)
    print("Test 2: Requests with 0.5s delay")
    print("=" * 60)
    
    successful = 0
    rate_limit_count = 0
    
    for i in range(20):
        start = time.time()
        try:
            response = session.get(url, timeout=10)
            elapsed = time.time() - start
            
            if response.status_code == 429:
                rate_limit_count += 1
                retry_after = response.headers.get("Retry-After", "N/A")
                print(f"Request {i+1}: 429 Rate Limited! Retry-After: {retry_after}s")
            elif response.status_code == 200:
                successful += 1
                if i < 5 or i % 5 == 0:
                    print(f"Request {i+1}: 200 OK (elapsed: {elapsed:.2f}s)")
        except Exception as e:
            print(f"Request {i+1}: ERROR - {e}")
        
        time.sleep(0.5)
    
    print(f"\nResults: {successful} successful, {rate_limit_count} rate limited")
    
    # Test 3: With 1.0s delay (current setting)
    print("\n" + "=" * 60)
    print("Test 3: Requests with 1.0s delay (current setting)")
    print("=" * 60)
    
    successful = 0
    rate_limit_count = 0
    
    for i in range(10):
        start = time.time()
        try:
            response = session.get(url, timeout=10)
            elapsed = time.time() - start
            
            if response.status_code == 429:
                rate_limit_count += 1
                retry_after = response.headers.get("Retry-After", "N/A")
                print(f"Request {i+1}: 429 Rate Limited! Retry-After: {retry_after}s")
            elif response.status_code == 200:
                successful += 1
                if i < 3 or i % 3 == 0:
                    print(f"Request {i+1}: 200 OK (elapsed: {elapsed:.2f}s)")
        except Exception as e:
            print(f"Request {i+1}: ERROR - {e}")
        
        time.sleep(1.0)
    
    print(f"\nResults: {successful} successful, {rate_limit_count} rate limited")
    print("\n" + "=" * 60)
    print("CONCLUSION:")
    print("=" * 60)
    print("Check the results above to see what delay is actually needed.")

if __name__ == "__main__":
    test_rate_limits()
