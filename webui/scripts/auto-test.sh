#!/bin/bash

# Simple Playwright Auto Test Script
# Runs tests in background without blocking the conversation

echo "🚀 Starting Playwright tests in background..."

# Run tests in background
npx playwright test --project=chromium --reporter=line > playwright-auto.log 2>&1 &
TEST_PID=$!

echo "✅ Tests started with PID: $TEST_PID"
echo "📊 Monitor progress: tail -f playwright-auto.log"
echo "🛑 Stop tests: kill $TEST_PID"
echo "📋 View report: npx playwright show-report"

# Don't wait - let it run in background
echo "⏳ Tests are running in background..." 