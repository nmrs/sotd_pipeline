#!/usr/bin/env python3
"""Script to tail API logs in real-time for debugging."""

import sys
import time
from pathlib import Path


def tail_logs(log_file: str, lines: int = 50):
    """Tail a log file and show the last N lines."""
    log_path = Path(__file__).parent / "logs" / log_file

    if not log_path.exists():
        print(f"❌ Log file not found: {log_path}")
        return

    print(f"📖 Tailing log file: {log_path}")
    print(f"📊 Showing last {lines} lines:")
    print("=" * 80)

    # Read and display the last N lines
    with open(log_path, "r") as f:
        all_lines = f.readlines()
        last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        for line in last_lines:
            print(line.rstrip())

    print("=" * 80)
    print("🔄 Monitoring for new log entries... (Ctrl+C to stop)")

    # Monitor for new entries
    try:
        with open(log_path, "r") as f:
            # Move to end of file
            f.seek(0, 2)

            while True:
                line = f.readline()
                if line:
                    print(line.rstrip())
                else:
                    time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n👋 Stopped monitoring logs")


def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python tail_logs.py <log_file> [lines]")
        print("Available log files:")
        logs_dir = Path(__file__).parent / "logs"
        if logs_dir.exists():
            for log_file in logs_dir.glob("*.log"):
                print(f"  - {log_file.name}")
        else:
            print("  No logs directory found")
        return

    log_file = sys.argv[1]
    lines = int(sys.argv[2]) if len(sys.argv) > 2 else 50

    tail_logs(log_file, lines)


if __name__ == "__main__":
    main()
