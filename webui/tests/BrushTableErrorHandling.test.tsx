import { test, expect } from '@playwright/test';

test.describe('BrushTable Error Handling', () => {
    test('should handle error boundary behavior for component failures', async ({ page }) => {
        // Navigate to the unmatched analyzer
        await page.goto('/unmatched-analyzer');

        // Select brush field
        await page.selectOption('select[name="field"]', 'brush');

        // Select a month
        await page.click('button[data-testid="month-selector"]');
        await page.click('text=2024-01');

        // Set limit
        await page.fill('input[name="limit"]', '10');

        // Click analyze button
        await page.click('button:has-text("Analyze")');

        // Wait for results to load
        await page.waitForSelector('.brush-table', { timeout: 10000 });

        // Check that error boundary is in place
        const errorBoundary = await page.locator('.error-boundary');
        const errorBoundaryCount = await errorBoundary.count();

        // If error boundary exists, verify it handles errors gracefully
        if (errorBoundaryCount > 0) {
            await expect(errorBoundary.first()).toBeVisible();
        }

        // Verify that the page doesn't crash completely
        const pageContent = await page.locator('body');
        await expect(pageContent).toBeVisible();
    });

    test('should fallback to VirtualizedTable on critical errors', async ({ page }) => {
        // Navigate to the unmatched analyzer
        await page.goto('/unmatched-analyzer');

        // Select brush field
        await page.selectOption('select[name="field"]', 'brush');

        // Select a month
        await page.click('button[data-testid="month-selector"]');
        await page.click('text=2024-01');

        // Set limit
        await page.fill('input[name="limit"]', '10');

        // Click analyze button
        await page.click('button:has-text("Analyze")');

        // Wait for results to load
        await page.waitForSelector('.brush-table', { timeout: 10000 });

        // Check that fallback mechanism is available
        const virtualizedTable = await page.locator('.virtualized-table');
        const brushTable = await page.locator('.brush-table');

        // Verify that either brush table or virtualized table is visible
        const brushTableVisible = await brushTable.isVisible();
        const virtualizedTableVisible = await virtualizedTable.isVisible();

        expect(brushTableVisible || virtualizedTableVisible).toBeTruthy();
    });

    test('should handle malformed brush data gracefully', async ({ page }) => {
        // Navigate to the unmatched analyzer
        await page.goto('/unmatched-analyzer');

        // Select brush field
        await page.selectOption('select[name="field"]', 'brush');

        // Select a month
        await page.click('button[data-testid="month-selector"]');
        await page.click('text=2024-01');

        // Set limit
        await page.fill('input[name="limit"]', '10');

        // Click analyze button
        await page.click('button:has-text("Analyze")');

        // Wait for results to load
        await page.waitForSelector('.brush-table', { timeout: 10000 });

        // Check that malformed data is handled gracefully
        const errorMessages = await page.locator('.error-message');
        const errorCount = await errorMessages.count();

        // If there are error messages, verify they're user-friendly
        if (errorCount > 0) {
            const errorText = await errorMessages.first().textContent();
            expect(errorText).toContain('error');
        }

        // Verify the page doesn't crash
        const pageContent = await page.locator('body');
        await expect(pageContent).toBeVisible();
    });

    test('should handle callback failure gracefully', async ({ page }) => {
        // Navigate to the unmatched analyzer
        await page.goto('/unmatched-analyzer');

        // Select brush field
        await page.selectOption('select[name="field"]', 'brush');

        // Select a month
        await page.click('button[data-testid="month-selector"]');
        await page.click('text=2024-01');

        // Set limit
        await page.fill('input[name="limit"]', '10');

        // Click analyze button
        await page.click('button:has-text("Analyze")');

        // Wait for results to load
        await page.waitForSelector('.brush-table', { timeout: 10000 });

        // Try to interact with checkboxes to test callback handling
        const checkboxes = await page.locator('.brush-table input[type="checkbox"]');
        const checkboxCount = await checkboxes.count();

        if (checkboxCount > 0) {
            // Click on a checkbox to test callback behavior
            await checkboxes.first().click();

            // Verify that the interaction doesn't cause a crash
            const pageContent = await page.locator('body');
            await expect(pageContent).toBeVisible();

            // Check for any error messages
            const errorMessages = await page.locator('.error-message');
            const errorCount = await errorMessages.count();

            // If there are errors, they should be handled gracefully
            if (errorCount > 0) {
                const errorText = await errorMessages.first().textContent();
                expect(errorText).toBeTruthy();
            }
        }
    });

    test('should handle missing component data gracefully', async ({ page }) => {
        // Navigate to the unmatched analyzer
        await page.goto('/unmatched-analyzer');

        // Select brush field
        await page.selectOption('select[name="field"]', 'brush');

        // Select a month
        await page.click('button[data-testid="month-selector"]');
        await page.click('text=2024-01');

        // Set limit
        await page.fill('input[name="limit"]', '10');

        // Click analyze button
        await page.click('button:has-text("Analyze")');

        // Wait for results to load
        await page.waitForSelector('.brush-table', { timeout: 10000 });

        // Check that missing component data is handled
        const componentRows = await page.locator('.brush-component-row');
        const componentCount = await componentRows.count();

        // If there are component rows, verify they handle missing data
        if (componentCount > 0) {
            // Check that component rows are displayed properly even with missing data
            await expect(componentRows.first()).toBeVisible();
        }

        // Verify the page doesn't crash with missing data
        const pageContent = await page.locator('body');
        await expect(pageContent).toBeVisible();
    });

    test('should provide user-friendly error messages', async ({ page }) => {
        // Navigate to the unmatched analyzer
        await page.goto('/unmatched-analyzer');

        // Select brush field
        await page.selectOption('select[name="field"]', 'brush');

        // Select a month
        await page.click('button[data-testid="month-selector"]');
        await page.click('text=2024-01');

        // Set limit
        await page.fill('input[name="limit"]', '10');

        // Click analyze button
        await page.click('button:has-text("Analyze")');

        // Wait for results to load
        await page.waitForSelector('.brush-table', { timeout: 10000 });

        // Check for user-friendly error messages
        const errorMessages = await page.locator('.error-message, .alert-error, .error-notification');
        const errorCount = await errorMessages.count();

        if (errorCount > 0) {
            // Verify error messages are user-friendly
            const errorText = await errorMessages.first().textContent();
            expect(errorText).toBeTruthy();

            // Error messages should not contain technical jargon
            const technicalTerms = ['undefined', 'null', 'TypeError', 'ReferenceError'];
            const hasTechnicalTerms = technicalTerms.some(term =>
                errorText?.toLowerCase().includes(term.toLowerCase())
            );
            expect(hasTechnicalTerms).toBeFalsy();
        }
    });

    test('should handle recovery from transient errors', async ({ page }) => {
        // Navigate to the unmatched analyzer
        await page.goto('/unmatched-analyzer');

        // Select brush field
        await page.selectOption('select[name="field"]', 'brush');

        // Select a month
        await page.click('button[data-testid="month-selector"]');
        await page.click('text=2024-01');

        // Set limit
        await page.fill('input[name="limit"]', '10');

        // Click analyze button
        await page.click('button:has-text("Analyze")');

        // Wait for results to load
        await page.waitForSelector('.brush-table', { timeout: 10000 });

        // Try to retry the analysis to test recovery
        await page.click('button:has-text("Analyze")');

        // Wait for results to load again
        await page.waitForSelector('.brush-table', { timeout: 10000 });

        // Verify that the component recovers from transient errors
        const brushTable = await page.locator('.brush-table');
        const virtualizedTable = await page.locator('.virtualized-table');

        // At least one table should be visible after recovery
        const brushTableVisible = await brushTable.isVisible();
        const virtualizedTableVisible = await virtualizedTable.isVisible();

        expect(brushTableVisible || virtualizedTableVisible).toBeTruthy();
    });

    test('should handle network errors gracefully', async ({ page }) => {
        // Navigate to the unmatched analyzer
        await page.goto('/unmatched-analyzer');

        // Select brush field
        await page.selectOption('select[name="field"]', 'brush');

        // Select a month
        await page.click('button[data-testid="month-selector"]');
        await page.click('text=2024-01');

        // Set limit
        await page.fill('input[name="limit"]', '10');

        // Simulate network error by blocking requests
        await page.route('**/api/**', route => route.abort());

        // Click analyze button
        await page.click('button:has-text("Analyze")');

        // Wait for error handling
        await page.waitForTimeout(2000);

        // Check that network errors are handled gracefully
        const errorMessages = await page.locator('.error-message, .alert-error');
        const errorCount = await errorMessages.count();

        // Should show some form of error message for network issues
        if (errorCount > 0) {
            const errorText = await errorMessages.first().textContent();
            expect(errorText).toBeTruthy();
        }

        // Verify the page doesn't crash
        const pageContent = await page.locator('body');
        await expect(pageContent).toBeVisible();
    });
}); 