# Fetch Performance Comparison: PRAW vs JSON

## Test Configuration
- **Test Period**: Year 2025 (12 months)
- **Authentication**: Both using authenticated requests (PRAW with OAuth, JSON with cookie-based)
- **Date**: 2026-01-21

## Single Month Results (2025-01)

### PRAW Fetch (`fetch`)
- **Time**: ~3.2 seconds
- **Rate**: ~3.0 seconds/month

### JSON Fetch (`fetch_json`)
- **Time**: ~55.7 seconds  
- **Rate**: ~55.7 seconds/month
- **Ratio**: **17.4x slower** than PRAW

## Full Year Results (2025)

### PRAW Fetch (`fetch`)
- **Status**: Completed
- **Time**: ~49.6 seconds (from earlier run)
- **Average**: ~4.1 seconds/month

### JSON Fetch (`fetch_json`)
- **Status**: In progress (estimated ~11 minutes based on single-month rate)
- **Estimated Time**: ~668 seconds (~11.1 minutes)
- **Estimated Ratio**: ~13.5x slower than PRAW

## Analysis

### Why JSON Fetch is Slower

1. **Rate Limiting**:
   - PRAW with OAuth: Higher rate limits (60+ requests/minute)
   - JSON with cookies: 1 second delay between requests (60 requests/minute max)
   - JSON unauthenticated: 6 second delays (10 requests/minute)

2. **API Call Patterns**:
   - **PRAW**: Optimized API calls, batch operations
   - **JSON**: Individual HTTP requests for:
     - Each search query (multiple per month)
     - Each thread's comments endpoint
     - Each "more comments" batch via `morechildren.json`
   
3. **Network Overhead**:
   - PRAW uses efficient API endpoints
   - JSON uses public endpoints with more overhead per request

### Performance Breakdown (Single Month)

For January 2025:
- **PRAW**: ~3.2s total
- **JSON**: ~55.7s total
  - Thread search: Multiple queries with 1s delays
  - Comment fetching: One request per thread + "more" requests
  - Estimated: ~50-60 API calls × 1s delay = ~50-60s minimum

## Recommendations

1. **For Production Use**: PRAW is significantly faster and should be preferred when available
2. **For Fallback**: JSON fetch is acceptable as a fallback when PRAW API is unavailable
3. **Optimization Opportunities**:
   - Reduce delays if rate limits allow
   - Batch requests where possible
   - Cache search results

## Notes

- Both implementations produce identical data (verified via A/B testing)
- JSON fetch uses cookie-based authentication (60+ QPM) for better performance
- Unauthenticated JSON fetch would be even slower (~6s delays = ~5-6 minutes per month)
