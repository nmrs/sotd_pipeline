# Test Cookie Setup for Rate Limit Testing

To safely test rate limits without risking your main Reddit account:

## Option 1: Environment Variable (Recommended)

```bash
export REDDIT_SESSION_COOKIE_TEST="your_test_account_cookie_value"
python test_01s_delay.py
```

## Option 2: Test Cookie File

1. Create a test Reddit account (separate from your main account)
2. Log in to Reddit with the test account
3. Extract the `reddit_session` cookie:
   - Open Developer Tools (F12 or Cmd+Option+I)
   - Go to Application tab → Cookies → https://www.reddit.com
   - Find the 'reddit_session' cookie
   - Copy its value
4. Create `.reddit_cookies_test.json` in the project root:

```json
{
  "reddit_session": "your_test_account_cookie_value"
}
```

5. Run the test:

```bash
python test_01s_delay.py
```

## Notes

- The test cookie file (`.reddit_cookies_test.json`) is already in `.gitignore`
- This keeps your main account safe from rate limit testing
- The test script will automatically use the test cookie if available
- If no test cookie is found, it will warn and fall back to regular cookies
