#!/usr/bin/env python3
"""Estimate time to refetch all 2025 data using JSON API.

Based on:
- Thread count: 428 threads
- Rate limit: 100 requests per 328.5 seconds (5.47 minutes)
- API calls per thread: 1 (comments) + potentially 1 (morechildren)
- Search calls per month: varies (broad + day-specific if needed)
"""

import json
from pathlib import Path

def analyze_2025_data():
    """Analyze 2025 data to estimate API calls needed."""
    
    threads_dir = Path('data/threads')
    comments_dir = Path('data/comments')
    
    total_threads = 0
    total_comments = 0
    month_data = []
    
    # Count threads and comments per month
    for month_file in sorted(threads_dir.glob('2025-*.json')):
        if month_file.name.startswith('2025-') and not month_file.name.endswith('.html.json') and not month_file.name.endswith('.praw.json'):
            month = month_file.stem
            try:
                with open(month_file) as f:
                    threads_data = json.load(f)
                threads = threads_data.get('data', [])
                thread_count = len(threads)
                
                # Count comments for this month
                comments_file = comments_dir / f'{month}.json'
                comment_count = 0
                if comments_file.exists():
                    with open(comments_file) as f:
                        comments_data = json.load(f)
                    comment_count = len(comments_data.get('data', []))
                
                month_data.append({
                    'month': month,
                    'threads': thread_count,
                    'comments': comment_count,
                })
                
                total_threads += thread_count
                total_comments += comment_count
            except Exception as e:
                print(f'Error processing {month_file}: {e}')
    
    print("=" * 60)
    print("2025 DATA ANALYSIS")
    print("=" * 60)
    print(f"\nTotal threads: {total_threads}")
    print(f"Total comments: {total_comments}")
    print(f"Average comments per thread: {total_comments/total_threads:.1f}")
    
    # Estimate API calls
    # Reddit's initial comment JSON typically shows ~25-50 top-level comments
    # If there are more, it uses "more" objects that require morechildren calls
    # With ~47 comments per thread average, most threads will need morechildren
    
    # Conservative estimate: 80% of threads need morechildren
    # (threads with <25 comments won't, but most will)
    threads_needing_more = int(total_threads * 0.8)
    
    print(f"\nAPI Call Estimates:")
    print(f"  Thread comment calls: {total_threads} (1 per thread)")
    print(f"  Morechildren calls: {threads_needing_more} (estimated 80% of threads)")
    print(f"  Total comment-related calls: {total_threads + threads_needing_more}")
    
    # Search calls: varies by month
    # Broad queries: 2 per month (usually)
    # Day-specific: only if hit 100-result limit (some months like June)
    # Overrides: 1 call per override thread (usually 0-2 per month)
    # Estimate: 2-5 search calls per month average
    avg_search_calls_per_month = 3
    total_search_calls = 12 * avg_search_calls_per_month
    
    print(f"  Search calls: ~{total_search_calls} (estimated {avg_search_calls_per_month} per month)")
    print(f"  Total API calls: {total_threads + threads_needing_more + total_search_calls}")
    
    total_api_calls = total_threads + threads_needing_more + total_search_calls
    
    # Rate limit calculations
    # From test: 100 requests per 328.5 seconds (5.47 minutes)
    # Effective rate: 18.26 requests/minute sustained
    # But we can burst at ~4 req/s until hitting limit
    
    print(f"\n" + "=" * 60)
    print("TIME ESTIMATION")
    print("=" * 60)
    
    # Calculate using rate limit window
    window_duration = 328.5  # seconds (5.47 minutes)
    requests_per_window = 100
    
    # Number of full windows needed
    full_windows = total_api_calls // requests_per_window
    remaining_requests = total_api_calls % requests_per_window
    
    # Time for full windows (each window takes window_duration + wait time)
    # But wait time is already included in the next window's start
    # So it's: (full_windows * window_duration) + time for remaining requests
    
    # Time for remaining requests (at ~4 req/s burst rate)
    remaining_time = remaining_requests * 0.25  # 0.25s per request at burst rate
    
    total_time_seconds = (full_windows * window_duration) + remaining_time
    total_time_minutes = total_time_seconds / 60
    total_time_hours = total_time_minutes / 60
    
    print(f"\nRate Limit Info:")
    print(f"  Window duration: {window_duration} seconds ({window_duration/60:.2f} minutes)")
    print(f"  Requests per window: {requests_per_window}")
    print(f"  Effective rate: {requests_per_window/window_duration*60:.2f} requests/minute")
    
    print(f"\nTime Calculation:")
    print(f"  Total API calls: {total_api_calls}")
    print(f"  Full windows: {full_windows}")
    print(f"  Remaining requests: {remaining_requests}")
    print(f"  Time for full windows: {full_windows * window_duration / 60:.2f} minutes")
    print(f"  Time for remaining: {remaining_time:.2f} seconds")
    
    print(f"\n" + "=" * 60)
    print("ESTIMATED TOTAL TIME")
    print("=" * 60)
    print(f"  {total_time_seconds:.0f} seconds")
    print(f"  {total_time_minutes:.1f} minutes")
    print(f"  {total_time_hours:.2f} hours")
    
    # Breakdown by phase
    print(f"\n" + "=" * 60)
    print("BREAKDOWN BY PHASE")
    print("=" * 60)
    
    # Search phase
    search_windows = total_search_calls // requests_per_window
    search_remaining = total_search_calls % requests_per_window
    search_time = (search_windows * window_duration) + (search_remaining * 0.25)
    print(f"Search phase:")
    print(f"  Calls: {total_search_calls}")
    print(f"  Time: {search_time/60:.1f} minutes ({search_time/3600:.2f} hours)")
    
    # Comment fetching phase
    comment_calls = total_threads + threads_needing_more
    comment_windows = comment_calls // requests_per_window
    comment_remaining = comment_calls % requests_per_window
    comment_time = (comment_windows * window_duration) + (comment_remaining * 0.25)
    print(f"\nComment fetching phase:")
    print(f"  Calls: {comment_calls}")
    print(f"  Time: {comment_time/60:.1f} minutes ({comment_time/3600:.2f} hours)")
    
    print(f"\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total threads: {total_threads}")
    print(f"Estimated API calls: {total_api_calls}")
    print(f"Estimated time: {total_time_hours:.2f} hours ({total_time_minutes:.0f} minutes)")
    print("=" * 60)

if __name__ == "__main__":
    analyze_2025_data()
