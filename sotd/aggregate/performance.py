#!/usr/bin/env python3
"""Performance monitoring utilities for the aggregate phase."""


def get_memory_usage() -> dict:
    """
    Get current memory usage information.

    Returns:
        Dictionary with memory usage information
    """
    try:
        import psutil

        memory = psutil.virtual_memory()
        return {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "percent_used": memory.percent,
        }
    except ImportError:
        return {"error": "psutil not available"}


def log_performance_metrics(metrics: dict, debug: bool = False) -> None:
    """
    Log performance metrics in a structured way.

    Args:
        metrics: Performance metrics dictionary
        debug: Enable debug logging
    """
    if not debug:
        return

    print("\n[DEBUG] Performance Summary:")
    print("=" * 50)

    total_time = sum(op.get("elapsed_seconds", 0) for op in metrics.values())
    total_records = sum(op.get("record_count", 0) for op in metrics.values())

    print(f"Total processing time: {total_time:.3f}s")
    print(f"Total records processed: {total_records}")
    if total_time > 0:
        print(f"Overall throughput: {total_records / total_time:.1f} records/sec")

    print("\nOperation breakdown:")
    for operation, data in metrics.items():
        elapsed = data.get("elapsed_seconds", 0)
        records = data.get("record_count", 0)
        rate = data.get("records_per_second", 0)
        print(f"  {operation}: {elapsed:.3f}s, {records} records, {rate:.1f} records/sec")

    # Memory usage
    memory_info = get_memory_usage()
    if "error" not in memory_info:
        print(
            f"\nMemory usage: {memory_info['used_gb']}GB / {memory_info['total_gb']}GB "
            f"({memory_info['percent_used']}%)"
        )
    print("=" * 50)
