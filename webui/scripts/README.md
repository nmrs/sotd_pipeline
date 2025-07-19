# Playwright Test Automation Scripts

This directory contains automation scripts to run Playwright tests without blocking the conversation.

## Quick Start

### 🚀 **Background Testing (Recommended)**
```bash
# Run tests in background (non-blocking)
npm run test:e2e:background

# Monitor progress
tail -f playwright-auto.log

# Stop tests if needed
kill <PID>
```

### 📊 **Advanced Automation**
```bash
# Run with custom options
./scripts/run-tests.sh -p chromium -g 'navigation'

# Run all browsers
./scripts/run-tests.sh -p all

# Run in headed mode
./scripts/run-tests.sh -h

# Run in debug mode
./scripts/run-tests.sh -d
```

## Scripts Overview

### `auto-test.sh` - Simple Background Runner
- **Purpose**: Quick background testing without blocking
- **Usage**: `npm run test:e2e:background`
- **Features**:
  - Runs tests in background
  - Logs to `playwright-auto.log`
  - Provides PID for monitoring/stopping
  - Non-blocking execution

### `run-tests.sh` - Advanced Test Runner
- **Purpose**: Full-featured test automation
- **Usage**: `./scripts/run-tests.sh [OPTIONS]`
- **Features**:
  - Multiple browser support
  - Pattern matching
  - Different modes (headed, debug, UI)
  - Comprehensive logging
  - Progress monitoring

## Package.json Scripts

```bash
# Background testing (non-blocking)
npm run test:e2e:background

# Quick test (basic tests only)
npm run test:e2e:quick

# All browsers
npm run test:e2e:all

# Monitor logs
npm run test:e2e:monitor

# Standard Playwright commands
npm run test:e2e          # All tests
npm run test:e2e:ui       # Interactive UI
npm run test:e2e:headed   # See browser
npm run test:e2e:debug    # Debug mode
```

## Monitoring and Control

### Monitor Test Progress
```bash
# Watch log file
tail -f playwright-auto.log

# Watch with timestamps
tail -f playwright-auto.log | while read line; do echo "$(date): $line"; done
```

### Stop Running Tests
```bash
# Find test process
ps aux | grep playwright

# Kill by PID
kill <PID>

# Kill all playwright processes
pkill -f playwright
```

### View Results
```bash
# Open HTML report
npx playwright show-report

# View test results
cat playwright-auto.log
```

## Troubleshooting

### Tests Not Starting
```bash
# Check if dev server is running
curl http://localhost:3000

# Restart dev server
npm run dev
```

### Tests Hanging
```bash
# Kill hanging processes
pkill -f playwright
pkill -f vite

# Restart everything
npm run dev &
sleep 5
npm run test:e2e:background
```

### Permission Issues
```bash
# Make scripts executable
chmod +x scripts/*.sh
```

## Best Practices

1. **Use Background Mode**: Always use `npm run test:e2e:background` for non-blocking testing
2. **Monitor Progress**: Use `tail -f playwright-auto.log` to watch progress
3. **Clean Up**: Kill processes when done: `pkill -f playwright`
4. **Check Logs**: Always check logs for errors and results
5. **Use Quick Tests**: Use `npm run test:e2e:quick` for fast feedback

## Integration with Development

### During Development
```bash
# Start dev server
npm run dev

# In another terminal, run tests in background
npm run test:e2e:background

# Monitor progress
tail -f playwright-auto.log
```

### Continuous Testing
```bash
# Run tests every 30 seconds
watch -n 30 'npm run test:e2e:background'
```

This automation setup ensures that Playwright tests never block your conversation and provide easy monitoring and control. 