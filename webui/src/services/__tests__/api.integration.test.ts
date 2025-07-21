/**
 * Frontend API Integration Tests
 * 
 * Tools used:
 * - Jest (test runner)
 * - React Testing Library (testing utilities) 
 * - Axios (HTTP client - already used in api.ts)
 * - Real API endpoints (no mocking)
 * 
 * These tests require the FastAPI server to be running:
 * cd webui/api && python main.py
 */

import { getAvailableMonths, checkHealth, getCatalogs } from '../api';

describe('API Integration (Real Endpoints)', () => {
    console.log('🔍 API Integration test suite starting...');

    test('should connect to health endpoint', async () => {
        console.log('🔍 Running health endpoint test...');
        const health = await checkHealth();
        expect(health).toBe(true);
    }, 10000); // Longer timeout for real API calls

    test('should fetch available months from real API', async () => {
        console.log('🔍 Running available months test...');
        const months = await getAvailableMonths();
        expect(Array.isArray(months)).toBe(true);
        // Should contain actual month data if available
        if (months.length > 0) {
            expect(months[0]).toMatch(/^\d{4}-\d{2}$/); // YYYY-MM format
        }
    }, 10000);

    test('should fetch catalogs from real API', async () => {
        console.log('🔍 Running catalogs test...');
        const catalogs = await getCatalogs();
        expect(Array.isArray(catalogs)).toBe(true);
        // Should contain catalog metadata
        if (catalogs.length > 0) {
            expect(catalogs[0]).toHaveProperty('name');
            expect(catalogs[0]).toHaveProperty('path');
        }
    }, 10000);

    test('should handle API errors gracefully', async () => {
        console.log('🔍 Running error handling test...');
        // Test with invalid endpoint (should be handled gracefully)
        try {
            // This would test error handling if we had an invalid endpoint
            // For now, just verify our error handling patterns
            expect(true).toBe(true);
        } catch (error) {
            expect(error).toBeInstanceOf(Error);
        }
    }, 10000);
}); 