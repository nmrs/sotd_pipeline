"""Phase 1 validation test - verify authentication and cookie handling works.

This is a simple test script to validate Phase 1 functionality before proceeding.
Run this to verify:
1. Cookie retrieval works
2. Can make authenticated requests to Reddit
3. Cookie persistence works
"""

from sotd.fetch_via_json.json_scraper import (
    get_reddit_cookies,
    get_reddit_json,
    get_reddit_session,
    print_cookie_instructions,
)


def test_cookie_retrieval() -> bool:
    """Test that we can retrieve cookies."""
    print("\n[TEST] Testing cookie retrieval...")
    cookies = get_reddit_cookies()
    if cookies:
        print(f"[TEST] ✅ Cookie retrieved: {list(cookies.keys())}")
        return True
    else:
        print("[TEST] ⚠️  No cookie found (will use unauthenticated)")
        return False


def test_authenticated_request() -> bool:
    """Test that we can make an authenticated request to Reddit."""
    print("\n[TEST] Testing authenticated request to Reddit...")
    try:
        cookies = get_reddit_cookies()
        session = get_reddit_session(cookies=cookies)

        # Try to fetch a simple Reddit page
        test_url = "https://www.reddit.com/r/wetshaving/about.json"
        response = session.get(test_url, timeout=10)

        if response.status_code == 200:
            print(f"[TEST] ✅ Successfully fetched {test_url}")
            print(f"[TEST] ✅ Response status: {response.status_code}")
            return True
        else:
            print(f"[TEST] ⚠️  Got status code {response.status_code}")
            return False
    except Exception as e:
        print(f"[TEST] ❌ Error: {e}")
        return False


def test_json_fetch() -> bool:
    """Test that we can fetch JSON from Reddit."""
    print("\n[TEST] Testing JSON fetch...")
    try:
        cookies = get_reddit_cookies()
        json_data = get_reddit_json(
            "https://www.reddit.com/r/wetshaving/about.json", cookies=cookies
        )

        if json_data and isinstance(json_data, dict):
            print(f"[TEST] ✅ Successfully fetched JSON data")
            return True
        else:
            print(f"[TEST] ⚠️  Got invalid JSON data")
            return False
    except Exception as e:
        print(f"[TEST] ❌ Error: {e}")
        return False


def main() -> None:
    """Run Phase 1 validation tests."""
    print("=" * 60)
    print("Phase 1 Validation: Authentication and Cookie Handling")
    print("=" * 60)

    results = []

    # Test 1: Cookie retrieval
    results.append(("Cookie Retrieval", test_cookie_retrieval()))

    # Test 2: Authenticated request
    results.append(("Authenticated Request", test_authenticated_request()))

    # Test 3: JSON fetch
    results.append(("JSON Fetch", test_json_fetch()))

    # Summary
    print("\n" + "=" * 60)
    print("Phase 1 Validation Summary:")
    print("=" * 60)
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name}: {status}")

    all_passed = all(result[1] for result in results)
    if all_passed:
        print("\n✅ Phase 1 validation PASSED - ready to proceed to Phase 2")
    else:
        print("\n⚠️  Phase 1 validation had issues - review before proceeding")


if __name__ == "__main__":
    main()
