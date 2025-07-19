#!/bin/bash

# Playwright Test Runner Script
# This script runs Playwright tests in the background and provides better automation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
PROJECT="chromium"
PATTERN=""
HEADED=false
DEBUG=false
UI=false
REPORTER="html"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -p, --project PROJECT    Browser project to use (default: chromium)"
    echo "  -g, --grep PATTERN       Run tests matching pattern"
    echo "  -h, --headed             Run in headed mode (see browser)"
    echo "  -d, --debug              Run in debug mode"
    echo "  -u, --ui                 Run in UI mode (interactive)"
    echo "  -r, --reporter TYPE      Reporter type (html, line, json)"
    echo "  --help                   Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Run all tests in chromium"
    echo "  $0 -p firefox                         # Run all tests in firefox"
    echo "  $0 -g 'navigation'                    # Run tests matching 'navigation'"
    echo "  $0 -h -d                              # Run in headed debug mode"
    echo "  $0 -u                                 # Run in UI mode"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--project)
            PROJECT="$2"
            shift 2
            ;;
        -g|--grep)
            PATTERN="$2"
            shift 2
            ;;
        -h|--headed)
            HEADED=true
            shift
            ;;
        -d|--debug)
            DEBUG=true
            shift
            ;;
        -u|--ui)
            UI=true
            shift
            ;;
        -r|--reporter)
            REPORTER="$2"
            shift 2
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Build command
CMD="npx playwright test"

# Add project
if [[ "$PROJECT" != "all" ]]; then
    CMD="$CMD --project=$PROJECT"
fi

# Add grep pattern
if [[ -n "$PATTERN" ]]; then
    CMD="$CMD --grep=\"$PATTERN\""
fi

# Add headed mode
if [[ "$HEADED" == true ]]; then
    CMD="$CMD --headed"
fi

# Add debug mode
if [[ "$DEBUG" == true ]]; then
    CMD="$CMD --debug"
fi

# Add UI mode
if [[ "$UI" == true ]]; then
    CMD="$CMD --ui"
fi

# Add reporter
if [[ "$REPORTER" != "html" ]]; then
    CMD="$CMD --reporter=$REPORTER"
fi

# Print command being executed
print_status "Running: $CMD"

# Create log file
LOG_FILE="playwright-test-$(date +%Y%m%d-%H%M%S).log"
print_status "Log file: $LOG_FILE"

# Run the command in background and capture output
if [[ "$UI" == true || "$DEBUG" == true ]]; then
    # For UI and debug mode, run in foreground
    print_status "Running in foreground mode..."
    eval $CMD
else
    # For regular tests, run in background
    print_status "Running in background mode..."
    eval $CMD > "$LOG_FILE" 2>&1 &
    TEST_PID=$!
    
    print_status "Test PID: $TEST_PID"
    print_status "Monitor progress with: tail -f $LOG_FILE"
    print_status "Stop tests with: kill $TEST_PID"
    
    # Wait for completion
    wait $TEST_PID
    EXIT_CODE=$?
    
    # Show results
    if [[ $EXIT_CODE -eq 0 ]]; then
        print_success "Tests completed successfully!"
        print_status "View report: npx playwright show-report"
    else
        print_error "Tests failed with exit code: $EXIT_CODE"
        print_status "Check log file: $LOG_FILE"
    fi
    
    # Show last few lines of log
    if [[ -f "$LOG_FILE" ]]; then
        echo ""
        print_status "Last 10 lines of log:"
        tail -10 "$LOG_FILE"
    fi
fi 