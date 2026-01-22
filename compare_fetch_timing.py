#!/usr/bin/env python3
"""Compare timing between PRAW fetch and JSON fetch for year 2025."""

import subprocess
import time
import sys

def run_command(cmd, label):
    """Run a command and return timing information."""
    print(f"\n{'='*60}")
    print(f"{label}")
    print(f"{'='*60}")
    sys.stdout.flush()
    
    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=False,  # Show output in real-time
            text=True,
        )
        elapsed = time.time() - start
        return elapsed, result.returncode
    except KeyboardInterrupt:
        elapsed = time.time() - start
        print(f"\n[INTERRUPTED] After {elapsed:.2f} seconds")
        return elapsed, 1

if __name__ == "__main__":
    print("Comparing fetch performance for year 2025...")
    print("This may take several minutes...")
    
    # Run PRAW fetch
    praw_cmd = "python run.py fetch --year 2025 --force"
    praw_time, praw_code = run_command(praw_cmd, "PRAW fetch (fetch)")
    
    print(f"\n[RESULT] PRAW fetch completed in {praw_time:.2f} seconds (exit code: {praw_code})")
    
    # Run JSON fetch
    json_cmd = "python run.py fetch_json --year 2025 --force"
    json_time, json_code = run_command(json_cmd, "JSON fetch (fetch_json)")
    
    print(f"\n[RESULT] JSON fetch completed in {json_time:.2f} seconds (exit code: {json_code})")
    
    # Summary
    print(f"\n{'='*60}")
    print("PERFORMANCE COMPARISON")
    print(f"{'='*60}")
    print(f"PRAW fetch:    {praw_time:.2f} seconds")
    print(f"JSON fetch:    {json_time:.2f} seconds")
    
    if praw_time > 0:
        ratio = json_time / praw_time
        print(f"JSON is {ratio:.2f}x {'slower' if ratio > 1 else 'faster'} than PRAW")
    
    print(f"{'='*60}\n")
