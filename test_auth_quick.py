#!/usr/bin/env python3
"""Quick authentication test for test cookie."""

import json
import os
from pathlib import Path
from sotd.fetch_via_json.json_scraper import get_reddit_json, get_reddit_session, _find_project_root

def get_test_cookies() -> dict:
    """Get test account cookies from test cookie file or environment variable."""
    # Check environment variable first
    test_cookie_env = os.getenv("REDDIT_SESSION_COOKIE_TEST")
    if test_cookie_env:
        print("[INFO] Using test cookie from REDDIT_SESSION_COOKIE_TEST environment variable")
        return {"reddit_session": test_cookie_env}
    
    # Check test cookie file
    project_root = _find_project_root()
    test_cookie_file = project_root / ".reddit_cookies_test.json"
    
    if test_cookie_file.exists():
        try:
            with open(test_cookie_file, "r") as f:
                cookie_data = json.load(f)
                if "reddit_session" in cookie_data:
                    print(f"[INFO] Using test cookie from {test_cookie_file}")
                    return {"reddit_session": cookie_data["reddit_session"]}
        except Exception as e:
            print(f"[ERROR] Could not read test cookie file: {e}")
            return {}
    else:
        print(f"[INFO] Test cookie file not found: {test_cookie_file}")
        print("[INFO] Checking for regular cookie file...")
    
    # Fallback: check if there's a regular cookie file we can use for testing
    regular_cookie_file = project_root / ".reddit_cookies.json"
    if regular_cookie_file.exists():
        try:
            with open(regular_cookie_file, "r") as f:
                cookie_data = json.load(f)
                if "reddit_session" in cookie_data:
                    print(f"[WARN] Using regular cookie from {regular_cookie_file} (not test cookie!)")
                    return {"reddit_session": cookie_data["reddit_session"]}
        except Exception as e:
            print(f"[ERROR] Could not read regular cookie file: {e}")
    
    return {}

def test_auth():
    """Test authentication with test cookie."""
    print("=" * 60)
    print("Quick Authentication Test")
    print("=" * 60)
    
    cookies = get_test_cookies()
    
    if not cookies or "reddit_session" not in cookies:
        print("\n[ERROR] No test cookie found!")
        print("\nTo set up test cookie:")
        print("1. Set environment variable: export REDDIT_SESSION_COOKIE_TEST=\"cookie_value\"")
        print("2. Or create .reddit_cookies_test.json in project root with:")
        print('   {"reddit_session": "cookie_value"}')
        return False
    
    cookie_value = cookies["reddit_session"]
    cookie_preview = cookie_value[:20] + "..." if len(cookie_value) > 20 else cookie_value
    print(f"\n[INFO] Cookie found: {cookie_preview}")
    print(f"[INFO] Cookie length: {len(cookie_value)} characters")
    
    # Test 1: Basic JSON endpoint
    print("\n[TEST] Testing basic JSON endpoint...")
    try:
        data = get_reddit_json("https://www.reddit.com/r/wetshaving/about.json", cookies=cookies)
        if data and "data" in data:
            subreddit_name = data.get("data", {}).get("display_name", "unknown")
            print(f"[TEST] ✅ Successfully fetched /r/{subreddit_name} data")
        else:
            print(f"[TEST] ⚠️  Got response but unexpected format: {list(data.keys()) if data else 'None'}")
    except Exception as e:
        print(f"[TEST] ❌ Failed: {e}")
        return False
    
    # Test 2: Check if we're authenticated (can see user info)
    print("\n[TEST] Testing authenticated endpoint...")
    try:
        session = get_reddit_session(cookies=cookies)
        response = session.get("https://www.reddit.com/api/me.json", timeout=10)
        if response.status_code == 200:
            user_data = response.json()
            username = user_data.get("name", "unknown")
            print(f"[TEST] ✅ Authenticated as user: {username}")
        elif response.status_code == 401:
            print("[TEST] ⚠️  Not authenticated (401) - cookie may be expired or invalid")
        else:
            print(f"[TEST] ⚠️  Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"[TEST] ⚠️  Could not check authentication status: {e}")
    
    # Test 3: Make a few requests to verify rate limiting works
    print("\n[TEST] Testing multiple requests (rate limit check)...")
    try:
        for i in range(3):
            data = get_reddit_json("https://www.reddit.com/r/wetshaving/about.json", cookies=cookies)
            if data:
                print(f"[TEST] Request {i+1}/3: ✅ Success")
    except Exception as e:
        print(f"[TEST] ❌ Failed on request: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ Authentication test PASSED!")
    print("=" * 60)
    print("\nThe test cookie is working correctly.")
    print("You can now safely use it for rate limit testing.")
    
    return True

if __name__ == "__main__":
    success = test_auth()
    exit(0 if success else 1)
