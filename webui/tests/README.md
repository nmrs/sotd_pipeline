# WebUI E2E Tests

## Overview

This directory contains simplified E2E tests that focus on **Safari browser compatibility** and basic app functionality. The tests are designed to be fast, reliable, and focused on what matters most.

## Test Strategy

### Safari-First Approach
- **Primary Target**: Safari (webkit) browser
- **Focus**: Basic app functionality, navigation, and form interactions
- **Scope**: Core user workflows only
- **Speed**: Fast, focused tests that run quickly

### What We Test
- ✅ App loading and basic structure
- ✅ Navigation between pages
- ✅ Form interactions and accessibility
- ✅ Basic user workflows

### What We Don't Test
- ❌ Complex browser-specific features
- ❌ Performance benchmarks
- ❌ Edge cases that don't matter for Safari
- ❌ Multiple browser compatibility (Chrome, Firefox, etc.)

## Running Tests

### Quick Safari Test
```bash
npm run test:e2e:safari
```

### All E2E Tests (Safari only)
```bash
npm run test:e2e
```

### Debug Mode
```bash
npm run test:e2e:debug
```

### UI Mode (Interactive)
```bash
npm run test:e2e:ui
```

## Test Files

### `safari-basic.spec.ts`
- **Purpose**: Basic Safari functionality verification
- **Tests**:
  - App loading and structure
  - Navigation between pages
  - Form interactions
- **Duration**: ~30 seconds
- **Reliability**: High (mocked API calls)

## Configuration

### Playwright Config (`playwright.config.ts`)
- **Browser**: Safari (webkit) only
- **Parallel**: Enabled for faster execution
- **Retries**: 2 on CI, 0 locally
- **Timeout**: 30 seconds per test
- **Screenshots**: On failure only
- **Video**: On failure only

### Test Environment
- **Base URL**: `http://localhost:3000`
- **API Mocking**: All API calls are mocked
- **Network**: Simulated network conditions
- **Viewport**: Desktop Safari resolution

## Best Practices

### Test Design
- **Keep tests simple** - focus on user workflows
- **Mock external dependencies** - avoid real API calls
- **Test behavior, not implementation** - verify user experience
- **Fast execution** - tests should run quickly

### Maintenance
- **Update tests when UI changes** - keep tests in sync
- **Remove obsolete tests** - don't maintain unused tests
- **Focus on Safari** - don't add browser-specific workarounds
- **Document changes** - update this README when needed

## Troubleshooting

### Common Issues
1. **Tests fail on CI but pass locally**
   - Check network timeouts
   - Verify API mocking is working
   - Check for race conditions

2. **Tests are slow**
   - Reduce test scope
   - Optimize API mocking
   - Check for unnecessary waits

3. **Tests are flaky**
   - Add proper waits
   - Improve test isolation
   - Check for timing issues

### Debug Commands
```bash
# Run with debug output
npm run test:e2e:debug

# Run with UI for visual debugging
npm run test:e2e:ui

# Run specific test file
npx playwright test safari-basic.spec.ts
```

## Future Improvements

### Potential Enhancements
- Add more specific user workflow tests
- Improve test data management
- Add visual regression tests
- Optimize test execution time

### When to Add Tests
- New user workflows are added
- Critical functionality changes
- Safari-specific issues are found
- Performance regressions occur

---

**Note**: This simplified approach focuses on what matters most - ensuring the app works correctly in Safari with fast, reliable tests. 