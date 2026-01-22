#!/usr/bin/env python3
"""Test smart rate limiting algorithm with time-based pacing.

This script tests the new algorithm that calculates delay based on:
- reset_time / remaining_requests (when remaining is low)
- Fixed multipliers (when remaining is high)

Makes ~150 requests to validate behavior across different rate limit states.
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional

import requests

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sotd.fetch_via_json.json_scraper import get_reddit_cookies, get_reddit_session


def calculate_smart_delay(
    remaining: Optional[float],
    reset: Optional[float],
    base_delay: float = 0.1,
) -> float:
    """Calculate delay using smart time-based pacing algorithm.
    
    This is the NEW algorithm we're testing:
    - High remaining (> 20): Burst mode (base_delay)
    - Medium remaining (10-20): Slight increase, consider reset time
    - Low remaining (< 10): Time-based pacing = (reset / remaining) * 0.9
    
    Args:
        remaining: Number of requests remaining in window
        reset: Seconds until rate limit window resets
        base_delay: Base delay in seconds (default 0.1s)
        
    Returns:
        Calculated delay in seconds
    """
    if remaining is None:
        return base_delay
    
    if remaining > 20:
        # Burst mode - plenty of requests remaining
        delay = base_delay
    elif remaining > 10:
        # Moderate remaining - slight increase, but also check reset time
        if reset is not None and reset > 0:
            time_per_request = (reset / remaining) * 0.9  # Safety margin
            delay = max(base_delay * 1.5, time_per_request)
        else:
            delay = base_delay * 1.5
    elif remaining > 0:
        # Low remaining - pace across reset window
        if reset is not None and reset > 0:
            time_per_request = (reset / remaining) * 0.9  # Safety margin
            delay = max(time_per_request, base_delay)  # Don't go below base
            delay = min(delay, 60.0)  # Cap at 60s to avoid excessive waits
        else:
            # No reset time available, use conservative multiplier
            delay = base_delay * 5.0
    else:
        # Exhausted - should rarely happen, wait for reset
        delay = reset if reset and reset > 0 else base_delay * 10.0
    
    return delay


def extract_rate_limit_headers(response: requests.Response) -> dict:
    """Extract rate limit headers from response (case-insensitive)."""
    headers = response.headers
    result = {
        "remaining": None,
        "reset": None,
        "used": None,
    }
    
    for header_name in headers:
        header_lower = header_name.lower()
        if header_lower == "x-ratelimit-remaining":
            try:
                result["remaining"] = float(headers[header_name])
            except (ValueError, TypeError):
                pass
        elif header_lower == "x-ratelimit-reset":
            try:
                result["reset"] = float(headers[header_name])
            except (ValueError, TypeError):
                pass
        elif header_lower == "x-ratelimit-used":
            try:
                result["used"] = float(headers[header_name])
            except (ValueError, TypeError):
                pass
    
    return result


def test_smart_rate_limiting():
    """Test smart rate limiting algorithm with ~150 requests."""
    
    import sys
    sys.stdout.flush()
    
    print("=" * 70, flush=True)
    print("SMART RATE LIMITING ALGORITHM TEST", flush=True)
    print("=" * 70, flush=True)
    print("\n[INFO] Loading cookies...", flush=True)
    
    cookies = get_reddit_cookies()
    if not cookies:
        print("ERROR: No cookie found. Set REDDIT_SESSION_COOKIE or create .reddit_cookies.json", flush=True)
        return
    
    print(f"[INFO] Cookie loaded: {len(cookies)} cookie(s)", flush=True)
    print("[INFO] Creating session...", flush=True)
    
    session = get_reddit_session(cookies=cookies)
    url = "https://www.reddit.com/r/wetshaving/about.json"
    base_delay = 0.1
    
    print(f"\nMaking ~150 requests to: {url}", flush=True)
    print("Testing time-based pacing algorithm...\n", flush=True)
    print("Algorithm behavior:", flush=True)
    print("  - Remaining > 20:  Burst mode (0.1s delay)", flush=True)
    print("  - Remaining 10-20: Moderate (1.5x or reset/remaining)", flush=True)
    print("  - Remaining < 10:   Time-based pacing (reset/remaining * 0.9)", flush=True)
    print(flush=True)
    
    # Track metrics
    request_count = 0
    total_time = 0
    start_time = time.time()
    last_request_time = start_time
    
    # Track rate limit states
    burst_mode_requests = 0
    moderate_mode_requests = 0
    pacing_mode_requests = 0
    errors = 0
    
    # Detailed log for analysis
    log_entries = []
    
    print("[INFO] Starting requests...", flush=True)
    
    try:
        for i in range(1, 151):
            request_start = time.time()
            
            # Print progress every 5 requests or on first request
            if i == 1 or i % 5 == 0:
                elapsed = time.time() - start_time
                print(f"[INFO] Starting request {i}/150 (elapsed: {elapsed:.1f}s)...", flush=True)
            
            try:
                if i == 1:
                    print(f"[INFO] Making first request to {url}...", flush=True)
                response = session.get(url, timeout=30)
                if i == 1:
                    print(f"[INFO] First request completed: {response.status_code}", flush=True)
                request_count += 1
                
                # Extract rate limit headers
                rate_limit = extract_rate_limit_headers(response)
                remaining = rate_limit["remaining"]
                reset = rate_limit["reset"]
                used = rate_limit["used"]
                
                # Calculate delay using new algorithm
                calculated_delay = calculate_smart_delay(remaining, reset, base_delay)
                
                # Determine mode
                if remaining is None:
                    mode = "unknown"
                elif remaining > 20:
                    mode = "burst"
                    burst_mode_requests += 1
                elif remaining > 10:
                    mode = "moderate"
                    moderate_mode_requests += 1
                else:
                    mode = "pacing"
                    pacing_mode_requests += 1
                
                # Calculate actual time since last request
                actual_time_since_last = request_start - last_request_time
                
                # Log entry
                log_entry = {
                    "request": i,
                    "status": response.status_code,
                    "remaining": remaining,
                    "reset": reset,
                    "used": used,
                    "calculated_delay": calculated_delay,
                    "actual_delay": actual_time_since_last,
                    "mode": mode,
                }
                log_entries.append(log_entry)
                
                # Print every 5 requests, when mode changes, or when delay is significant
                should_print = (
                    i % 5 == 0 or
                    (i > 1 and log_entries[-2]["mode"] != mode) or
                    calculated_delay > 5.0  # Print if delay is > 5 seconds
                )
                
                if should_print:
                    reset_str = f", reset: {reset:.0f}s" if reset else ""
                    used_str = f", used: {used:.0f}" if used else ""
                    remaining_str = f"{remaining:.1f}" if remaining is not None else "N/A"
                    print(
                        f"Request {i:3d}: {response.status_code} | "
                        f"Remaining: {remaining_str:>6}{used_str} | "
                        f"Delay: {calculated_delay:5.2f}s | Mode: {mode:8s}{reset_str}"
                    )
                
                # Handle 429 errors
                if response.status_code == 429:
                    errors += 1
                    print(f"\n[WARN] Request {i} got 429! Remaining: {remaining}, Reset: {reset}")
                    # Wait for reset if available
                    if reset and reset > 0:
                        print(f"[INFO] Waiting {reset:.0f}s for rate limit reset...")
                        # Show progress during long waits
                        wait_start = time.time()
                        while time.time() - wait_start < reset:
                            elapsed_wait = time.time() - wait_start
                            remaining_wait = reset - elapsed_wait
                            if remaining_wait > 10:
                                print(f"  {remaining_wait:.0f}s remaining...", end="\r", flush=True)
                                time.sleep(min(10, remaining_wait))
                            else:
                                time.sleep(remaining_wait)
                                break
                        print()  # New line after wait
                
                # Apply calculated delay (with progress for long delays)
                if calculated_delay > 5.0:
                    print(f"[INFO] Waiting {calculated_delay:.1f}s before next request...")
                    delay_start = time.time()
                    while time.time() - delay_start < calculated_delay:
                        elapsed_delay = time.time() - delay_start
                        remaining_delay = calculated_delay - elapsed_delay
                        if remaining_delay > 5:
                            print(f"  {remaining_delay:.0f}s remaining...", end="\r", flush=True)
                            time.sleep(min(5, remaining_delay))
                        else:
                            time.sleep(remaining_delay)
                            break
                    print()  # New line after delay
                else:
                    time.sleep(calculated_delay)
                
                last_request_time = time.time()
                
            except Exception as e:
                errors += 1
                print(f"[ERROR] Request {i} failed: {e}")
                time.sleep(1.0)  # Small delay on error
        
        total_time = time.time() - start_time
        
    except KeyboardInterrupt:
        print("\n[INFO] Test interrupted by user")
        total_time = time.time() - start_time
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total requests: {request_count}")
    print(f"Total time: {total_time:.1f}s ({total_time/60:.2f} minutes)")
    print(f"Errors (429s): {errors}")
    print()
    print("Mode distribution:")
    print(f"  Burst mode (>20 remaining):   {burst_mode_requests} requests")
    print(f"  Moderate mode (10-20):        {moderate_mode_requests} requests")
    print(f"  Pacing mode (<10 remaining): {pacing_mode_requests} requests")
    print()
    
    # Analyze delays
    if log_entries:
        delays_by_mode = {"burst": [], "moderate": [], "pacing": [], "unknown": []}
        for entry in log_entries:
            mode = entry["mode"]
            if entry["calculated_delay"] is not None:
                delays_by_mode[mode].append(entry["calculated_delay"])
        
        print("Delay statistics by mode:")
        for mode, delays in delays_by_mode.items():
            if delays:
                avg = sum(delays) / len(delays)
                min_delay = min(delays)
                max_delay = max(delays)
                print(f"  {mode:8s}: avg={avg:5.2f}s, min={min_delay:5.2f}s, max={max_delay:5.2f}s ({len(delays)} requests)")
        print()
        
        # Show transitions
        print("Mode transitions (first occurrence):")
        last_mode = None
        for entry in log_entries:
            if entry["mode"] != last_mode:
                print(f"  Request {entry['request']:3d}: {last_mode or 'start'} -> {entry['mode']}")
                last_mode = entry["mode"]
        print()
        
        # Show pacing examples (when remaining < 10)
        pacing_examples = [
            e for e in log_entries
            if e["mode"] == "pacing" and e["remaining"] is not None and e["reset"] is not None
        ]
        if pacing_examples:
            print("Pacing mode examples (remaining < 10):")
            for entry in pacing_examples[:10]:  # Show first 10
                expected_delay = (entry["reset"] / entry["remaining"]) * 0.9 if entry["remaining"] > 0 else 0
                print(
                    f"  Request {entry['request']:3d}: "
                    f"remaining={entry['remaining']:5.1f}, reset={entry['reset']:6.0f}s, "
                    f"delay={entry['calculated_delay']:5.2f}s (expected: {expected_delay:.2f}s)"
                )
    
    print("=" * 70)
    print("VALIDATION CHECKLIST")
    print("=" * 70)
    print(f"✓ Burst mode works (>20 remaining): {burst_mode_requests > 0}")
    print(f"✓ Moderate mode works (10-20 remaining): {moderate_mode_requests > 0}")
    print(f"✓ Pacing mode works (<10 remaining): {pacing_mode_requests > 0}")
    print(f"✓ No excessive 429s: {errors <= 2} ({errors} errors)")
    print(f"✓ Delays scale with reset time: Check pacing examples above")
    print("=" * 70)


if __name__ == "__main__":
    test_smart_rate_limiting()
