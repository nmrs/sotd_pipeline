import { test, expect } from '@playwright/test';

test.describe('BrushTable Checkbox Behavior', () => {
    test('should handle main brush checkbox filtering', async ({ page }) => {
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

        // Check that brush table is displayed
        const brushTable = await page.locator('.brush-table');
        await expect(brushTable).toBeVisible();

        // Check that checkboxes are present
        const checkboxes = await page.locator('.brush-table input[type="checkbox"]');
        await expect(checkboxes).toHaveCount(1); // At least one checkbox should be present
    });

    test('should handle component-level checkbox filtering', async ({ page }) => {
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

        // Check that component checkboxes are present for complex brushes
        const componentCheckboxes = await page.locator('.brush-component-row input[type="checkbox"]');
        const componentCount = await componentCheckboxes.count();

        // If there are component checkboxes, verify they work
        if (componentCount > 0) {
            // Click on the first component checkbox
            await componentCheckboxes.first().click();

            // Verify the checkbox state changed
            await expect(componentCheckboxes.first()).toBeChecked();
        }
    });

    test('should display visual feedback for filtered items', async ({ page }) => {
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

        // Check that filtered status is displayed
        const filteredElements = await page.locator('.brush-table .filtered-status');
        const filteredCount = await filteredElements.count();

        // If there are filtered items, verify they have visual indicators
        if (filteredCount > 0) {
            await expect(filteredElements.first()).toBeVisible();
        }
    });

    test('should handle independent operation of main vs component filtering', async ({ page }) => {
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

        // Get main brush checkboxes
        const mainCheckboxes = await page.locator('.brush-main-row input[type="checkbox"]');
        const componentCheckboxes = await page.locator('.brush-component-row input[type="checkbox"]');

        const mainCount = await mainCheckboxes.count();
        const componentCount = await componentCheckboxes.count();

        // If we have both main and component checkboxes, test independent operation
        if (mainCount > 0 && componentCount > 0) {
            // Click main checkbox
            await mainCheckboxes.first().click();
            await expect(mainCheckboxes.first()).toBeChecked();

            // Verify component checkboxes are still unchecked
            await expect(componentCheckboxes.first()).not.toBeChecked();

            // Click component checkbox
            await componentCheckboxes.first().click();
            await expect(componentCheckboxes.first()).toBeChecked();

            // Verify main checkbox is still checked
            await expect(mainCheckboxes.first()).toBeChecked();
        }
    });

    test('should handle callback integration with filtering system', async ({ page }) => {
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

        // Check that apply changes button is present
        const applyButton = await page.locator('button:has-text("Apply Changes")');
        await expect(applyButton).toBeVisible();

        // Click on a checkbox to create pending changes
        const checkboxes = await page.locator('.brush-table input[type="checkbox"]');
        if (await checkboxes.count() > 0) {
            await checkboxes.first().click();

            // Verify apply button is enabled
            await expect(applyButton).toBeEnabled();
        }
    });

    test('should handle error states gracefully', async ({ page }) => {
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

        // Check that error handling is in place
        const errorElements = await page.locator('.error-message');
        const errorCount = await errorElements.count();

        // If there are errors, verify they're displayed properly
        if (errorCount > 0) {
            await expect(errorElements.first()).toBeVisible();
        }
    });

    test('should maintain accessibility standards', async ({ page }) => {
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

        // Check that checkboxes have proper accessibility attributes
        const checkboxes = await page.locator('.brush-table input[type="checkbox"]');
        if (await checkboxes.count() > 0) {
            const firstCheckbox = checkboxes.first();

            // Verify checkbox has proper attributes
            await expect(firstCheckbox).toHaveAttribute('type', 'checkbox');

            // Check that it's keyboard accessible
            await firstCheckbox.focus();
            await expect(firstCheckbox).toBeFocused();
        }
    });
}); 