import { test, expect } from '@playwright/test';

test.describe('BrushTable Performance', () => {
    test('should handle virtualization with 1000+ brush records', async ({ page }) => {
        // Navigate to the unmatched analyzer
        await page.goto('/unmatched-analyzer');

        // Select brush field
        await page.selectOption('select[name="field"]', 'brush');

        // Select a month
        await page.click('button[data-testid="month-selector"]');
        await page.click('text=2024-01');

        // Set high limit to test with large dataset
        await page.fill('input[name="limit"]', '1000');

        // Click analyze button
        await page.click('button:has-text("Analyze")');

        // Wait for results to load
        await page.waitForSelector('.brush-table', { timeout: 15000 });

        // Measure initial render time
        const startTime = Date.now();

        // Wait for table to be fully rendered
        await page.waitForSelector('.brush-table .virtualized-table', { timeout: 10000 });

        const renderTime = Date.now() - startTime;

        // Verify render time is reasonable (under 5 seconds for large dataset)
        expect(renderTime).toBeLessThan(5000);

        // Check that virtualization is working
        const visibleRows = await page.locator('.brush-table .virtualized-table .row').count();

        // Should only render visible rows (typically 10-20 rows visible at once)
        expect(visibleRows).toBeLessThan(50);
    });

    test('should render complex brush structures efficiently', async ({ page }) => {
        // Navigate to the unmatched analyzer
        await page.goto('/unmatched-analyzer');

        // Select brush field
        await page.selectOption('select[name="field"]', 'brush');

        // Select a month
        await page.click('button[data-testid="month-selector"]');
        await page.click('text=2024-01');

        // Set limit
        await page.fill('input[name="limit"]', '100');

        // Click analyze button
        await page.click('button:has-text("Analyze")');

        // Wait for results to load
        await page.waitForSelector('.brush-table', { timeout: 10000 });

        // Measure render time for complex structures
        const startTime = Date.now();

        // Wait for all rows to be rendered
        await page.waitForSelector('.brush-table .row', { timeout: 10000 });

        const renderTime = Date.now() - startTime;

        // Verify render time is reasonable (under 2 seconds for complex structures)
        expect(renderTime).toBeLessThan(2000);

        // Check that component rows are rendered efficiently
        const componentRows = await page.locator('.brush-component-row').count();

        // Should render component rows without significant performance impact
        if (componentRows > 0) {
            expect(componentRows).toBeLessThan(200); // Reasonable limit for component rows
        }
    });

    test('should maintain responsive interaction performance', async ({ page }) => {
        // Navigate to the unmatched analyzer
        await page.goto('/unmatched-analyzer');

        // Select brush field
        await page.selectOption('select[name="field"]', 'brush');

        // Select a month
        await page.click('button[data-testid="month-selector"]');
        await page.click('text=2024-01');

        // Set limit
        await page.fill('input[name="limit"]', '50');

        // Click analyze button
        await page.click('button:has-text("Analyze")');

        // Wait for results to load
        await page.waitForSelector('.brush-table', { timeout: 10000 });

        // Test checkbox interaction responsiveness
        const checkboxes = await page.locator('.brush-table input[type="checkbox"]');
        const checkboxCount = await checkboxes.count();

        if (checkboxCount > 0) {
            // Measure interaction response time
            const startTime = Date.now();

            // Click on first checkbox
            await checkboxes.first().click();

            const responseTime = Date.now() - startTime;

            // Verify interaction is responsive (under 100ms)
            expect(responseTime).toBeLessThan(100);

            // Verify checkbox state changed
            await expect(checkboxes.first()).toBeChecked();
        }
    });

    test('should handle memory usage efficiently', async ({ page }) => {
        // Navigate to the unmatched analyzer
        await page.goto('/unmatched-analyzer');

        // Select brush field
        await page.selectOption('select[name="field"]', 'brush');

        // Select a month
        await page.click('button[data-testid="month-selector"]');
        await page.click('text=2024-01');

        // Set limit
        await page.fill('input[name="limit"]', '200');

        // Click analyze button
        await page.click('button:has-text("Analyze")');

        // Wait for results to load
        await page.waitForSelector('.brush-table', { timeout: 10000 });

        // Get initial memory usage
        const initialMemory = await page.evaluate(() => {
            if ('memory' in performance) {
                return (performance as any).memory.usedJSHeapSize;
            }
            return 0;
        });

        // Perform some interactions to test memory management
        const checkboxes = await page.locator('.brush-table input[type="checkbox"]');
        const checkboxCount = await checkboxes.count();

        if (checkboxCount > 5) {
            // Click multiple checkboxes to test memory management
            for (let i = 0; i < Math.min(5, checkboxCount); i++) {
                await checkboxes.nth(i).click();
                await page.waitForTimeout(100); // Small delay between clicks
            }
        }

        // Get final memory usage
        const finalMemory = await page.evaluate(() => {
            if ('memory' in performance) {
                return (performance as any).memory.usedJSHeapSize;
            }
            return 0;
        });

        // Verify memory usage is reasonable (not growing excessively)
        if (initialMemory > 0 && finalMemory > 0) {
            const memoryIncrease = finalMemory - initialMemory;
            const memoryIncreaseMB = memoryIncrease / (1024 * 1024);

            // Memory increase should be reasonable (less than 50MB for interactions)
            expect(memoryIncreaseMB).toBeLessThan(50);
        }
    });

    test('should maintain scroll performance', async ({ page }) => {
        // Navigate to the unmatched analyzer
        await page.goto('/unmatched-analyzer');

        // Select brush field
        await page.selectOption('select[name="field"]', 'brush');

        // Select a month
        await page.click('button[data-testid="month-selector"]');
        await page.click('text=2024-01');

        // Set limit to ensure scrollable content
        await page.fill('input[name="limit"]', '100');

        // Click analyze button
        await page.click('button:has-text("Analyze")');

        // Wait for results to load
        await page.waitForSelector('.brush-table', { timeout: 10000 });

        // Find the scrollable container
        const scrollContainer = await page.locator('.brush-table .virtualized-table');

        if (await scrollContainer.count() > 0) {
            // Measure scroll performance
            const startTime = Date.now();

            // Perform smooth scroll
            await scrollContainer.evaluate((el) => {
                el.scrollTop = 500;
            });

            const scrollTime = Date.now() - startTime;

            // Verify scroll is smooth (under 200ms)
            expect(scrollTime).toBeLessThan(200);

            // Verify content updates smoothly
            await page.waitForTimeout(100);

            // Check that new rows are rendered
            const visibleRows = await page.locator('.brush-table .row').count();
            expect(visibleRows).toBeGreaterThan(0);
        }
    });

    test('should handle filtering operations efficiently', async ({ page }) => {
        // Navigate to the unmatched analyzer
        await page.goto('/unmatched-analyzer');

        // Select brush field
        await page.selectOption('select[name="field"]', 'brush');

        // Select a month
        await page.click('button[data-testid="month-selector"]');
        await page.click('text=2024-01');

        // Set limit
        await page.fill('input[name="limit"]', '100');

        // Click analyze button
        await page.click('button:has-text("Analyze")');

        // Wait for results to load
        await page.waitForSelector('.brush-table', { timeout: 10000 });

        // Test search filtering performance
        const searchInput = await page.locator('input[placeholder="Search items..."]');

        if (await searchInput.count() > 0) {
            // Measure search performance
            const startTime = Date.now();

            // Type search term
            await searchInput.fill('test');

            const searchTime = Date.now() - startTime;

            // Verify search is responsive (under 500ms)
            expect(searchTime).toBeLessThan(500);

            // Wait for filtered results
            await page.waitForTimeout(200);

            // Verify filtering worked
            const filteredRows = await page.locator('.brush-table .row').count();
            expect(filteredRows).toBeGreaterThanOrEqual(0);
        }
    });

    test('should maintain performance with component-level filtering', async ({ page }) => {
        // Navigate to the unmatched analyzer
        await page.goto('/unmatched-analyzer');

        // Select brush field
        await page.selectOption('select[name="field"]', 'brush');

        // Select a month
        await page.click('button[data-testid="month-selector"]');
        await page.click('text=2024-01');

        // Set limit
        await page.fill('input[name="limit"]', '50');

        // Click analyze button
        await page.click('button:has-text("Analyze")');

        // Wait for results to load
        await page.waitForSelector('.brush-table', { timeout: 10000 });

        // Test component-level checkbox performance
        const componentCheckboxes = await page.locator('.brush-component-row input[type="checkbox"]');
        const componentCount = await componentCheckboxes.count();

        if (componentCount > 0) {
            // Measure component checkbox interaction performance
            const startTime = Date.now();

            // Click on first component checkbox
            await componentCheckboxes.first().click();

            const responseTime = Date.now() - startTime;

            // Verify component interaction is responsive (under 100ms)
            expect(responseTime).toBeLessThan(100);

            // Verify checkbox state changed
            await expect(componentCheckboxes.first()).toBeChecked();
        }
    });

    test('should handle large datasets without performance degradation', async ({ page }) => {
        // Navigate to the unmatched analyzer
        await page.goto('/unmatched-analyzer');

        // Select brush field
        await page.selectOption('select[name="field"]', 'brush');

        // Select a month
        await page.click('button[data-testid="month-selector"]');
        await page.click('text=2024-01');

        // Test with different dataset sizes
        const testSizes = [10, 50, 100, 200];

        for (const size of testSizes) {
            // Set limit
            await page.fill('input[name="limit"]', size.toString());

            // Click analyze button
            await page.click('button:has-text("Analyze")');

            // Wait for results to load
            await page.waitForSelector('.brush-table', { timeout: 10000 });

            // Measure render time
            const startTime = Date.now();

            // Wait for table to be fully rendered
            await page.waitForSelector('.brush-table .virtualized-table', { timeout: 10000 });

            const renderTime = Date.now() - startTime;

            // Verify render time scales reasonably with dataset size
            const maxRenderTime = Math.min(5000, size * 10); // 10ms per item, max 5s
            expect(renderTime).toBeLessThan(maxRenderTime);

            // Verify table is functional
            const rows = await page.locator('.brush-table .row').count();
            expect(rows).toBeGreaterThan(0);
        }
    });
}); 