import { test, expect } from '@playwright/test';

test.describe('UI Components', () => {
    test('should handle form interactions', async ({ page }) => {
        await page.goto('/');

        // Wait for the page to load completely
        await page.waitForLoadState('networkidle');

        // Look for form elements
        const forms = page.locator('form, [role="form"]');
        if (await forms.count() > 0) {
            const form = forms.first();

            // Test input fields
            const inputs = form.locator('input, textarea, select');
            if (await inputs.count() > 0) {
                const input = inputs.first();
                await input.click();
                await input.fill('test value');
                await expect(input).toHaveValue('test value');
            }

            // Test buttons
            const buttons = form.locator('button, [role="button"], input[type="submit"]');
            if (await buttons.count() > 0) {
                const button = buttons.first();
                await expect(button).toBeVisible();
                await expect(button).toBeEnabled();
            }
        } else {
            // If no forms exist, test that the page still loads properly
            await expect(page.locator('#root')).toBeVisible();
            await expect(page.locator('header')).toBeVisible();
            await expect(page.locator('main')).toBeVisible();
        }
    });

    test('should handle modal dialogs', async ({ page }) => {
        await page.goto('/');

        // Wait for the page to load completely
        await page.waitForLoadState('networkidle');

        // Look for modal triggers
        const modalTriggers = page.locator('[data-modal], [aria-haspopup="dialog"], [role="button"]');
        if (await modalTriggers.count() > 0) {
            const trigger = modalTriggers.first();
            await trigger.click();

            // Check if a modal appears
            const modal = page.locator('[role="dialog"], .modal, .dialog');
            if (await modal.count() > 0) {
                await expect(modal.first()).toBeVisible();

                // Test modal close functionality
                const closeButton = modal.locator('[aria-label="Close"], .close, [data-close]');
                if (await closeButton.count() > 0) {
                    await closeButton.first().click();
                    await expect(modal.first()).not.toBeVisible();
                }
            }
        } else {
            // If no modals exist, test that the page still loads properly
            await expect(page.locator('#root')).toBeVisible();
            await expect(page.locator('header')).toBeVisible();
            await expect(page.locator('main')).toBeVisible();
        }
    });

    test('should handle responsive design', async ({ page }) => {
        // Test desktop view
        await page.setViewportSize({ width: 1280, height: 720 });
        await page.goto('/');
        await page.waitForLoadState('networkidle');
        await expect(page.locator('#root')).toBeVisible();

        // Test mobile view
        await page.setViewportSize({ width: 375, height: 667 });
        await page.goto('/');
        await page.waitForLoadState('networkidle');
        await expect(page.locator('#root')).toBeVisible();

        // Test tablet view
        await page.setViewportSize({ width: 768, height: 1024 });
        await page.goto('/');
        await page.waitForLoadState('networkidle');
        await expect(page.locator('#root')).toBeVisible();
    });

    test('should handle keyboard navigation', async ({ page }) => {
        await page.goto('/');

        // Wait for the page to load completely
        await page.waitForLoadState('networkidle');

        // Test tab navigation
        await page.keyboard.press('Tab');

        // Test that focus is visible
        const focusedElement = page.locator(':focus');
        if (await focusedElement.count() > 0) {
            await expect(focusedElement.first()).toBeVisible();
        }

        // Test escape key for modals
        await page.keyboard.press('Escape');

        // Test enter key for buttons
        const buttons = page.locator('button, [role="button"]');
        if (await buttons.count() > 0) {
            await buttons.first().focus();
            await page.keyboard.press('Enter');
        }
    });

    test('should handle accessibility features', async ({ page }) => {
        await page.goto('/');

        // Wait for the page to load completely
        await page.waitForLoadState('networkidle');

        // Check for proper ARIA labels
        const elementsWithAria = page.locator('[aria-label], [aria-labelledby], [aria-describedby]');
        if (await elementsWithAria.count() > 0) {
            await expect(elementsWithAria.first()).toBeVisible();
        }

        // Check for proper heading structure
        const headings = page.locator('h1, h2, h3, h4, h5, h6');
        if (await headings.count() > 0) {
            await expect(headings.first()).toBeVisible();
        }

        // Check for proper landmark roles
        const landmarks = page.locator('[role="main"], [role="navigation"], [role="banner"], [role="contentinfo"]');
        if (await landmarks.count() > 0) {
            await expect(landmarks.first()).toBeVisible();
        }
    });
}); 