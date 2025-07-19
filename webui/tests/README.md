# Playwright E2E Tests

This directory contains end-to-end tests for the SOTD WebUI using Playwright.

## Test Structure

- `navigation.spec.ts` - Tests for basic navigation and routing
- `api-integration.spec.ts` - Tests for API integration and error handling
- `ui-components.spec.ts` - Tests for UI components, forms, and accessibility

## Running Tests

### Quick Start
```bash
# Run all tests
npm run test:e2e

# Run tests with UI mode (interactive)
npm run test:e2e:ui

# Run tests in headed mode (see browser)
npm run test:e2e:headed

# Run tests in debug mode
npm run test:e2e:debug
```

### Specific Test Files
```bash
# Run specific test file
npx playwright test navigation.spec.ts

# Run tests matching a pattern
npx playwright test --grep "navigation"
```

### Browser-Specific Tests
```bash
# Run tests in specific browser
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

## Test Features

### Automatic Screenshots and Videos
- Screenshots are taken on test failures
- Videos are recorded for failed tests
- Trace files are generated for debugging

### Cross-Browser Testing
- Chrome (Chromium)
- Firefox
- Safari (WebKit)
- Mobile Chrome
- Mobile Safari

### Network Interception
Tests can mock API responses to test error scenarios:
```typescript
await page.route('**/api/**', route => {
  route.fulfill({
    status: 500,
    contentType: 'application/json',
    body: JSON.stringify({ error: 'Test error' })
  });
});
```

### Responsive Testing
Tests automatically run on different viewport sizes:
- Desktop (1280x720)
- Mobile (375x667)
- Tablet (768x1024)

## Debugging

### View Test Results
```bash
# Open HTML report
npx playwright show-report
```

### Debug Mode
```bash
# Run in debug mode with step-by-step execution
npm run test:e2e:debug
```

### UI Mode
```bash
# Interactive test runner
npm run test:e2e:ui
```

## Writing New Tests

### Test Structure
```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test('should do something', async ({ page }) => {
    await page.goto('/');
    // Test implementation
  });
});
```

### Best Practices
1. Use descriptive test names
2. Test one thing per test
3. Use page objects for complex interactions
4. Mock external dependencies
5. Test error scenarios
6. Include accessibility tests

### Locators
Use semantic selectors when possible:
```typescript
// Good - semantic
await page.locator('[role="button"]').click();

// Good - accessible
await page.locator('[aria-label="Close"]').click();

// Avoid - fragile
await page.locator('.btn-primary').click();
```

## Configuration

The Playwright configuration is in `playwright.config.ts` and includes:
- Automatic dev server startup
- Cross-browser testing
- Screenshot and video capture
- Trace file generation
- Mobile viewport testing

## CI/CD Integration

Tests can be run in CI environments:
```bash
# Install browsers for CI
npx playwright install --with-deps

# Run tests
npx playwright test
``` 