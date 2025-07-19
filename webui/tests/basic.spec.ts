import { test, expect } from '@playwright/test';

test.describe('Basic App Loading', () => {
    test('should load the app without API calls', async ({ page }) => {
        // Mock all API calls to return success
        await page.route('**/api/**', route => {
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({ status: 'ok' })
            });
        });

        await page.goto('/');

        // Wait for the page to load
        await page.waitForLoadState('networkidle');

        // Wait for React to hydrate the app
        await page.waitForFunction(() => {
            const root = document.getElementById('root');
            return root && root.children.length > 0;
        }, { timeout: 10000 });

        // Check that the page loads
        await expect(page).toHaveTitle(/SOTD Pipeline Analyzer/);

        // Check that the root div is visible
        await expect(page.locator('#root')).toBeVisible();

        // Check that the header is visible
        await expect(page.locator('header')).toBeVisible();

        // Check that the main content area is visible
        await expect(page.locator('main')).toBeVisible();

        // Check that the navigation links are visible
        await expect(page.locator('nav a')).toHaveCount(3);
    });
}); 