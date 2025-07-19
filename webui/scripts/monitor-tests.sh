#!/bin/bash

# Playwright Test Monitor Script
# Monitors test progress in real-time

echo "🔍 Monitoring Playwright tests..."
echo "Press Ctrl+C to stop monitoring"
echo ""

# Monitor the log file with timestamps
tail -f playwright-auto.log | while read line; do
    echo "[$(date '+%H:%M:%S')] $line"
done 