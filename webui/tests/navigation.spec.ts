import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
    test('should load the main page', async ({ page }) => {
        await page.goto('/');

        // Wait for the page to load completely
        await page.waitForLoadState('networkidle');

        // Wait for React to hydrate the app
        await page.waitForFunction(() => {
            const root = document.getElementById('root');
            return root && root.children.length > 0;
        }, { timeout: 10000 });

        // Check that the page loads
        await expect(page).toHaveTitle(/SOTD Pipeline Analyzer/);

        // Check that the root div is visible (React app container)
        await expect(page.locator('#root')).toBeVisible();

        // Check that the header is visible
        await expect(page.locator('header')).toBeVisible();

        // Check that the main content area is visible
        await expect(page.locator('main')).toBeVisible();

        // Check that the navigation links are visible
        await expect(page.locator('nav a')).toHaveCount(3);
    });

    test('should navigate between pages', async ({ page }) => {
        await page.goto('/');

        // Check that navigation links exist
        const navLinks = page.locator('nav a');
        await expect(navLinks).toHaveCount(3); // Dashboard, Unmatched, Mismatch

        // Click on the Unmatched link
        await navLinks.filter({ hasText: 'Unmatched' }).click();

        // Verify we're on the unmatched page
        await expect(page).toHaveURL(/.*\/unmatched/);

        // Click on the Mismatch link
        await navLinks.filter({ hasText: 'Mismatch' }).click();

        // Verify we're on the mismatch page
        await expect(page).toHaveURL(/.*\/mismatch/);

        // Click on the Dashboard link
        await navLinks.filter({ hasText: 'Dashboard' }).click();

        // Verify we're back on the dashboard
        await expect(page).toHaveURL(/.*\/$/);
    });

    test('should handle 404 pages gracefully', async ({ page }) => {
        await page.goto('/nonexistent-page');

        // The page should still load (not crash)
        await expect(page.locator('body')).toBeVisible();
    });
}); 