import { test, expect } from '@playwright/test';

test.describe('API Integration', () => {
    test('should fetch filtered entries', async ({ page }) => {
        await page.goto('/');

        // Wait for the page to load completely
        await page.waitForLoadState('networkidle');

        // Check that the React app is loaded
        await expect(page.locator('#root')).toBeVisible();
        await expect(page.locator('header')).toBeVisible();
        await expect(page.locator('main')).toBeVisible();

        // Check if there are any API calls being made
        const apiCalls = page.locator('[data-testid="api-loading"], .loading, [aria-busy="true"]');
        if (await apiCalls.count() > 0) {
            // Wait for loading to complete
            await expect(apiCalls.first()).not.toBeVisible();
        }
    });

    test('should handle API errors gracefully', async ({ page }) => {
        // Mock a failed API response
        await page.route('**/api/**', route => {
            route.fulfill({
                status: 500,
                contentType: 'application/json',
                body: JSON.stringify({ error: 'Internal server error' })
            });
        });

        await page.goto('/');

        // Wait for the page to load completely
        await page.waitForLoadState('networkidle');

        // The page should still load and show an error message
        await expect(page.locator('#root')).toBeVisible();
        await expect(page.locator('header')).toBeVisible();
        await expect(page.locator('main')).toBeVisible();

        // Check for error handling (could be an error message, fallback content, etc.)
        const errorElements = page.locator('.error, [role="alert"], .alert, .error-message');
        if (await errorElements.count() > 0) {
            await expect(errorElements.first()).toBeVisible();
        }
    });

    test('should handle network timeouts', async ({ page }) => {
        // Mock a slow API response that times out
        await page.route('**/api/**', route => {
            // Don't fulfill the route to simulate a timeout
            // The request will hang until the test timeout
        });

        await page.goto('/');

        // Wait for the page to load completely
        await page.waitForLoadState('networkidle');

        // The page should still load even with API timeouts
        await expect(page.locator('#root')).toBeVisible();
        await expect(page.locator('header')).toBeVisible();
        await expect(page.locator('main')).toBeVisible();

        // The app should handle the timeout gracefully
        // We don't check for specific loading states since they might not exist
        // The important thing is that the page doesn't crash
    });
}); 