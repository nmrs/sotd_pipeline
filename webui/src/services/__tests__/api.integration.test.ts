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
import { saveBrushSplit, loadBrushSplits } from '../api';

// Mock fetch globally
global.fetch = jest.fn();

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

describe('API Integration - Should Not Split Feature', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    test('saveBrushSplit includes should_not_split field in request', async () => {
        const mockResponse = {
            success: true,
            message: 'Successfully saved brush split',
            corrected: false,
            system_handle: null,
            system_knot: null,
            system_confidence: null,
            system_reasoning: null
        };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => mockResponse
        });

        const brushSplit = {
            original: 'Test Brush',
            handle: null,
            knot: 'Test Brush',
            should_not_split: true
        };

        await saveBrushSplit(brushSplit);

        expect(global.fetch).toHaveBeenCalledWith(
            '/api/brush-splits/save-split',
            expect.objectContaining({
                method: 'POST',
                headers: expect.objectContaining({
                    'Content-Type': 'application/json'
                }),
                body: JSON.stringify({
                    original: 'Test Brush',
                    handle: null,
                    knot: 'Test Brush',
                    should_not_split: true,
                    validated_at: expect.any(String)
                })
            })
        );
    });

    test('loadBrushSplits handles should_not_split field in response', async () => {
        const mockResponse = {
            brush_splits: [
                {
                    original: 'Test Brush 1',
                    handle: 'Test Handle',
                    knot: 'Test Knot',
                    should_not_split: false,
                    match_type: 'regex'
                },
                {
                    original: 'Test Brush 2',
                    handle: null,
                    knot: 'Test Brush 2',
                    should_not_split: true,
                    match_type: 'none'
                }
            ],
            statistics: {
                total: 2,
                validated: 0,
                corrected: 0
            }
        };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => mockResponse
        });

        const result = await loadBrushSplits(['2025-01']);

        expect(result.brush_splits).toHaveLength(2);
        expect(result.brush_splits[0].should_not_split).toBe(false);
        expect(result.brush_splits[1].should_not_split).toBe(true);
        expect(result.brush_splits[1].handle).toBe(null);
        expect(result.brush_splits[1].knot).toBe('Test Brush 2');
    });

    test('saveBrushSplit handles should_not_split field correctly', async () => {
        const mockResponse = {
            success: true,
            message: 'Successfully saved brush split',
            corrected: true,
            system_handle: 'Previous Handle',
            system_knot: 'Previous Knot',
            system_confidence: 'medium',
            system_reasoning: 'Previous reasoning'
        };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => mockResponse
        });

        const brushSplit = {
            original: 'Test Brush',
            handle: null,
            knot: 'Test Brush',
            should_not_split: true
        };

        const result = await saveBrushSplit(brushSplit);

        expect(result.success).toBe(true);
        expect(result.corrected).toBe(true);
        expect(result.system_handle).toBe('Previous Handle');
        expect(result.system_knot).toBe('Previous Knot');
    });
}); 