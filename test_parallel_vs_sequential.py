#!/usr/bin/env python3
"""Test parallel vs sequential comment fetching performance."""

import subprocess
import time
import sys

def run_fetch(month: str, parallel: bool, max_workers: int = 5) -> tuple[float, int]:
    """Run fetch_json for a month and return timing and exit code."""
    cmd = ["python", "run.py", "fetch_json", "--month", month, "--force"]
    if parallel:
        cmd.extend(["--parallel-comments", "--max-workers", str(max_workers)])
    
    print(f"\n{'='*60}")
    mode = f"PARALLEL (workers={max_workers})" if parallel else "SEQUENTIAL"
    print(f"Testing {mode} for {month}")
    print(f"{'='*60}")
    sys.stdout.flush()
    
    start = time.time()
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        elapsed = time.time() - start
        return elapsed, result.returncode
    except KeyboardInterrupt:
        elapsed = time.time() - start
        print(f"\n[INTERRUPTED] After {elapsed:.2f} seconds")
        return elapsed, 1

if __name__ == "__main__":
    # Test month with good data
    test_month = "2025-06"  # June typically has good activity
    
    print("Comparing parallel vs sequential comment fetching")
    print(f"Test month: {test_month}")
    print("\nNote: This will run each mode twice to get average timings")
    
    # Run sequential first
    seq_times = []
    for i in range(2):
        elapsed, code = run_fetch(test_month, parallel=False)
        if code == 0:
            seq_times.append(elapsed)
            print(f"[RESULT] Sequential run {i+1}: {elapsed:.2f} seconds")
        else:
            print(f"[ERROR] Sequential run {i+1} failed with exit code {code}")
    
    # Run parallel
    parallel_times = []
    for i in range(2):
        elapsed, code = run_fetch(test_month, parallel=True, max_workers=5)
        if code == 0:
            parallel_times.append(elapsed)
            print(f"[RESULT] Parallel run {i+1}: {elapsed:.2f} seconds")
        else:
            print(f"[ERROR] Parallel run {i+1} failed with exit code {code}")
    
    # Summary
    print(f"\n{'='*60}")
    print("PERFORMANCE COMPARISON")
    print(f"{'='*60}")
    
    if seq_times:
        avg_seq = sum(seq_times) / len(seq_times)
        print(f"Sequential (avg of {len(seq_times)} runs): {avg_seq:.2f} seconds")
        print(f"  Individual times: {[f'{t:.2f}s' for t in seq_times]}")
    
    if parallel_times:
        avg_parallel = sum(parallel_times) / len(parallel_times)
        print(f"Parallel (avg of {len(parallel_times)} runs): {avg_parallel:.2f} seconds")
        print(f"  Individual times: {[f'{t:.2f}s' for t in parallel_times]}")
    
    if seq_times and parallel_times:
        ratio = avg_parallel / avg_seq
        improvement = ((avg_seq - avg_parallel) / avg_seq) * 100
        print(f"\nParallel is {ratio:.2f}x {'faster' if ratio < 1 else 'slower'} than sequential")
        if improvement > 0:
            print(f"Parallel is {improvement:.1f}% faster")
        else:
            print(f"Parallel is {abs(improvement):.1f}% slower")
        
        if ratio < 0.9:
            print("\n✅ RECOMMENDATION: Use parallel processing (significant speedup)")
        elif ratio > 1.1:
            print("\n✅ RECOMMENDATION: Use sequential processing (parallel is slower)")
        else:
            print("\n⚠️  RECOMMENDATION: Performance is similar, use sequential (simpler)")
    
    print(f"{'='*60}\n")
