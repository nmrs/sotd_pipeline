import { test, expect } from '@playwright/test';

test.describe('Debug', () => {
    test('should debug page load', async ({ page }) => {
        // Listen for console messages
        page.on('console', msg => console.log('PAGE LOG:', msg.text()));
        page.on('pageerror', error => console.log('PAGE ERROR:', error.message));

        await page.goto('/');

        // Wait for the page to load
        await page.waitForLoadState('networkidle');

        // Take a screenshot for debugging
        await page.screenshot({ path: 'debug-screenshot.png' });

        // Log the page content
        const bodyContent = await page.locator('body').innerHTML();
        console.log('Body content:', bodyContent.substring(0, 500) + '...');

        // Check if root exists and has content
        const rootExists = await page.locator('#root').count() > 0;
        console.log('Root exists:', rootExists);

        if (rootExists) {
            const rootContent = await page.locator('#root').innerHTML();
            console.log('Root content:', rootContent);

            const rootVisible = await page.locator('#root').isVisible();
            console.log('Root visible:', rootVisible);
        }

        // Basic assertion that the page loaded
        await expect(page).toHaveTitle(/SOTD Pipeline Analyzer/);
    });
}); 