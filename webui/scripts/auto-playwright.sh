#!/bin/bash

# Automatic Playwright Test Runner
# Always runs tests in background mode to avoid blocking conversations

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Auto-Playwright: Running tests in background mode${NC}"

# Check if tests are already running
if pgrep -f "playwright test" > /dev/null; then
    echo -e "${YELLOW}⚠️  Tests are already running. Stopping previous tests...${NC}"
    pkill -f "playwright test"
    sleep 2
fi

# Run tests in background
echo -e "${BLUE}📊 Starting Playwright tests in background...${NC}"
npx playwright test --project=chromium --reporter=line > playwright-auto.log 2>&1 &
TEST_PID=$!

echo -e "${GREEN}✅ Tests started with PID: $TEST_PID${NC}"
echo -e "${BLUE}📊 Monitor progress: tail -f playwright-auto.log${NC}"
echo -e "${BLUE}🛑 Stop tests: kill $TEST_PID${NC}"
echo -e "${BLUE}📋 View report: npx playwright show-report${NC}"
echo -e "${GREEN}⏳ Tests are running in background - conversation can continue!${NC}"

# Don't wait - let it run in background
exit 0 