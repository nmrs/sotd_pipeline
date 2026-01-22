#!/usr/bin/env python3
"""300 Request Rate Limit Test with Detailed Metrics.

This test makes 300 total requests with proper rate limit handling:
1. Make requests until 429 (first batch)
2. Wait based on x-ratelimit-reset header
3. Make requests until 429 again (second batch)
4. Wait again
5. Make final batch to reach 300 total requests

Tracks detailed metrics for each batch and overall performance.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List
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


def wait_with_progress(wait_seconds: int) -> None:
    """Wait for specified seconds with progress updates."""
    if wait_seconds <= 0:
        return
    
    print(f"Waiting {wait_seconds} seconds for rate limit reset...")
    
    # Show progress every 30 seconds for long waits, every 10 for shorter
    update_interval = 30 if wait_seconds > 120 else 10
    
    start_wait = time.time()
    last_update = 0
    
    while True:
        elapsed = time.time() - start_wait
        remaining = wait_seconds - elapsed
        
        if remaining <= 0:
            break
        
        # Update progress
        if elapsed - last_update >= update_interval:
            print(f"  {int(remaining)} seconds remaining...")
            last_update = elapsed
        
        time.sleep(min(1.0, remaining))  # Sleep in 1s increments
    
    print("Wait complete.\n")


def test_300_requests():
    """Test making 300 requests with proper rate limit handling and detailed metrics."""
    cookies = get_test_cookies()
    if not cookies:
        print("[ERROR] No test cookie found")
        print("Create .reddit_cookies_test.json in project root with test account cookie")
        return
    
    session = get_reddit_session(cookies=cookies)
    url = "https://www.reddit.com/r/wetshaving/about.json"
    
    target_requests = 300
    
    print("=" * 60)
    print("300 REQUEST RATE LIMIT TEST")
    print("=" * 60)
    print(f"Target: {target_requests} total requests")
    
    # Record overall start time
    overall_start_time = time.time()
    overall_start_datetime = datetime.fromtimestamp(overall_start_time)
    print(f"Start time: {overall_start_datetime.strftime('%H:%M:%S')}")
    print("\n" + "=" * 60)
    
    # Track batches
    batches: List[Dict] = []
    total_requests = 0
    total_active_time = 0.0
    total_wait_time = 0.0
    batch_number = 0
    
    # Process in batches until we reach target
    while total_requests < target_requests:
        batch_number += 1
        batch_start_time = time.time()
        batch_requests = 0
        
        print(f"\nBATCH {batch_number}")
        print("-" * 60)
        print("Making requests...")
        
        # Make requests until we hit rate limit or reach target
        while total_requests < target_requests:
            try:
                response = session.get(url, timeout=10)
                
                if response.status_code == 429:
                    batch_end_time = time.time()
                    batch_active_time = batch_end_time - batch_start_time
                    
                    # Extract rate limit headers
                    reset_time_str = (
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
                    
                    print(f"\nRate limit hit at request {total_requests + 1}")
                    
                    # Batch summary
                    batch_rate = batch_requests / batch_active_time if batch_active_time > 0 else 0
                    
                    print(f"\nBatch {batch_number} Summary:")
                    print(f"  Requests: {batch_requests}")
                    print(f"  Time to limit: {batch_active_time:.2f} seconds")
                    if reset_time_str:
                        try:
                            reset_seconds = int(float(reset_time_str))
                            print(f"  Reset time: {reset_seconds} seconds ({reset_seconds/60:.2f} minutes) (from header)")
                        except (ValueError, TypeError):
                            print(f"  Reset time: {reset_time_str} (could not parse)")
                    else:
                        print("  Reset time: NOT FOUND in headers")
                    print(f"  Rate: {batch_rate:.2f} requests/second")
                    if rate_limit_used:
                        print(f"  Rate limit used: {rate_limit_used}%")
                    if rate_limit_remaining:
                        print(f"  Rate limit remaining: {rate_limit_remaining}%")
                    
                    # Store batch metrics
                    batch_metrics = {
                        "batch_number": batch_number,
                        "requests": batch_requests,
                        "active_time": batch_active_time,
                        "reset_time": int(float(reset_time_str)) if reset_time_str else None,
                        "rate": batch_rate,
                    }
                    
                    total_active_time += batch_active_time
                    
                    # Wait for reset if we haven't reached target yet
                    if total_requests < target_requests and reset_time_str:
                        try:
                            reset_seconds = int(float(reset_time_str))
                            wait_start = time.time()
                            wait_with_progress(reset_seconds)
                            wait_end = time.time()
                            actual_wait_time = wait_end - wait_start
                            total_wait_time += actual_wait_time
                            batch_metrics["wait_time"] = actual_wait_time
                            print(f"Wait completed. Actual wait time: {actual_wait_time:.2f} seconds\n")
                        except (ValueError, TypeError):
                            print(f"Could not parse reset time: {reset_time_str}\n")
                            batch_metrics["wait_time"] = 0
                    else:
                        batch_metrics["wait_time"] = 0
                    
                    batches.append(batch_metrics)
                    break
                    
                elif response.status_code == 200:
                    batch_requests += 1
                    total_requests += 1
                    
                    # Print progress every 10 requests
                    if batch_requests % 10 == 0:
                        elapsed = time.time() - batch_start_time
                        print(f"Request {total_requests} (batch {batch_number}): ✅ ({elapsed:.1f}s elapsed)")
                    
                    # Check if we've reached target
                    if total_requests >= target_requests:
                        batch_end_time = time.time()
                        batch_active_time = batch_end_time - batch_start_time
                        batch_rate = batch_requests / batch_active_time if batch_active_time > 0 else 0
                        
                        print(f"\nTarget reached! ({total_requests} requests)")
                        
                        # Store final batch metrics
                        batch_metrics = {
                            "batch_number": batch_number,
                            "requests": batch_requests,
                            "active_time": batch_active_time,
                            "reset_time": None,
                            "wait_time": 0,
                            "rate": batch_rate,
                        }
                        batches.append(batch_metrics)
                        total_active_time += batch_active_time
                        break
                else:
                    print(f"[WARN] Unexpected status: {response.status_code}")
                    break
                
                # 0.1s delay between requests
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                print("\n[INFO] Test interrupted by user")
                return
            except Exception as e:
                print(f"\n[ERROR] Request failed: {e}")
                break
    
    # Calculate final metrics
    overall_end_time = time.time()
    total_elapsed_time = overall_end_time - overall_start_time
    rate_limit_hits = len([b for b in batches if b.get("reset_time") is not None])
    
    active_rate = total_requests / total_active_time if total_active_time > 0 else 0
    overall_rate = total_requests / total_elapsed_time if total_elapsed_time > 0 else 0
    efficiency = (total_active_time / total_elapsed_time * 100) if total_elapsed_time > 0 else 0
    
    # Print final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"Total requests: {total_requests}")
    print(f"Total batches: {batch_number}")
    print(f"Rate limit hits: {rate_limit_hits}")
    
    print(f"\nTiming Breakdown:")
    print(f"  Active request time: {total_active_time:.2f} seconds ({total_active_time/60:.2f} minutes)")
    print(f"  Total wait time: {total_wait_time:.2f} seconds ({total_wait_time/60:.2f} minutes)")
    print(f"  Total elapsed time: {total_elapsed_time:.2f} seconds ({total_elapsed_time/60:.2f} minutes)")
    
    print(f"\nPerformance Metrics:")
    print(f"  Active rate: {active_rate:.2f} requests/second ({active_rate*60:.2f} requests/minute)")
    print(f"  Overall rate: {overall_rate:.2f} requests/second ({overall_rate*60:.2f} requests/minute)")
    print(f"  Efficiency: {efficiency:.1f}% (active time / total time)")
    
    print(f"\nPer-Batch Details:")
    for batch in batches:
        batch_num = batch["batch_number"]
        reqs = batch["requests"]
        active = batch["active_time"]
        rate = batch["rate"]
        reset = batch.get("reset_time")
        wait = batch.get("wait_time", 0)
        
        batch_info = f"  Batch {batch_num}: {reqs} requests in {active:.2f}s ({rate:.2f} req/s)"
        if reset:
            batch_info += f", waited {wait:.2f}s (reset: {reset}s)"
        print(batch_info)
    
    print("=" * 60)
    print(f"\nTest completed at {datetime.fromtimestamp(overall_end_time).strftime('%H:%M:%S')}")
    print(f"Total duration: {total_elapsed_time/60:.2f} minutes")


if __name__ == "__main__":
    test_300_requests()
