import { test, expect } from '@playwright/test';

test.describe('Safari Basic Functionality', () => {
  test('should load the app and display navigation', async ({ page }) => {
    // Mock API calls to avoid real network requests
    await page.route('**/api/**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'ok' }),
      });
    });

    await page.goto('/');

    // Wait for the page to load
    await page.waitForLoadState('networkidle');

    // Basic app structure checks
    await expect(page).toHaveTitle(/SOTD Pipeline Analyzer/);
    await expect(page.locator('#root')).toBeVisible();
    await expect(page.locator('header')).toBeVisible();
    await expect(page.locator('main')).toBeVisible();

    // Check navigation links exist
    const navLinks = page.locator('nav a');
    await expect(navLinks).toHaveCount(6);
  });

  test('should handle navigation between pages', async ({ page }) => {
    // Mock API calls
    await page.route('**/api/**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'ok' }),
      });
    });

    await page.goto('/');

    // Wait for page load
    await page.waitForLoadState('networkidle');

    // Test navigation to different pages
    const navLinks = page.locator('nav a');

    // Click on each navigation link and verify the page changes
    for (let i = 0; i < (await navLinks.count()); i++) {
      const link = navLinks.nth(i);
      const href = await link.getAttribute('href');

      if (href && href !== '#') {
        await link.click();

        // Wait for navigation
        await page.waitForLoadState('networkidle');

        // Verify we're on a different page (URL changed)
        const currentUrl = page.url();
        expect(currentUrl).toContain(href);
      }
    }
  });

  test('should handle form interactions', async ({ page }) => {
    // Mock API calls
    await page.route('**/api/**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'ok' }),
      });
    });

    await page.goto('/');

    // Wait for page load
    await page.waitForLoadState('networkidle');

    // Test basic form interactions if they exist
    const inputs = page.locator('input, select, textarea');
    const buttons = page.locator('button');

    // Verify forms are interactive
    if ((await inputs.count()) > 0) {
      const firstInput = inputs.first();
      await firstInput.focus();
      await expect(firstInput).toBeFocused();
    }

    if ((await buttons.count()) > 0) {
      const firstButton = buttons.first();
      await expect(firstButton).toBeVisible();
    }
  });
});
