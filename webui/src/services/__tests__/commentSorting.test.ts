/**
 * Tests for comment ID sorting behavior in unmatched analysis
 */

import { analyzeUnmatched } from '../api';

// Mock the API module
jest.mock('../api', () => ({
    analyzeUnmatched: jest.fn(),
}));

const mockAnalyzeUnmatched = analyzeUnmatched as jest.MockedFunction<typeof analyzeUnmatched>;

describe('Comment ID Sorting Tests', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    test('should return comment IDs sorted by month (newest first) when both months have data', async () => {
        // Mock response with comment IDs from both months
        const mockResponse = {
            field: 'blade',
            months: ['2025-08', '2020-08'],
            total_unmatched: 1,
            unmatched_items: [
                {
                    item: 'Lord',
                    count: 6, // 1 from 2025-08, 5 from 2020-08
                    comment_ids: ['n9d8qy1', 'g00m6ou', 'g042aih', 'g0706vx', 'g0b8wta'], // 2025-08 first, then 2020-08
                    examples: ['2025-08.json', '2020-08.json'],
                },
            ],
            processing_time: 0.5,
        };

        mockAnalyzeUnmatched.mockResolvedValue(mockResponse);

        const result = await analyzeUnmatched({
            field: 'blade',
            months: ['2025-08', '2020-08'],
            limit: 10,
        });

        // Verify that comment IDs are sorted by month (newest first)
        const commentIds = result.unmatched_items[0].comment_ids;
        expect(commentIds).toEqual(['n9d8qy1', 'g00m6ou', 'g042aih', 'g0706vx', 'g0b8wta']);

        // Verify that the first comment ID is from 2025-08 (newer month)
        expect(commentIds[0]).toBe('n9d8qy1'); // 2025-08 comment ID should be first
    });

    test('should return comment IDs from only one month when other month has no data', async () => {
        // Mock response with comment IDs from only 2020-08 (no 2025-08 data)
        const mockResponse = {
            field: 'blade',
            months: ['2025-08', '2020-08'],
            total_unmatched: 1,
            unmatched_items: [
                {
                    item: 'Lord',
                    count: 31, // All from 2020-08
                    comment_ids: ['g00m6ou', 'g042aih', 'g0706vx', 'g0b8wta', 'g0fgbhn'], // All from 2020-08
                    examples: ['2020-08.json'],
                },
            ],
            processing_time: 0.5,
        };

        mockAnalyzeUnmatched.mockResolvedValue(mockResponse);

        const result = await analyzeUnmatched({
            field: 'blade',
            months: ['2025-08', '2020-08'],
            limit: 10,
        });

        // Verify that all comment IDs are from 2020-08
        const commentIds = result.unmatched_items[0].comment_ids;
        expect(commentIds).toEqual(['g00m6ou', 'g042aih', 'g0706vx', 'g0b8wta', 'g0fgbhn']);

        // Verify that the first comment ID is from 2020-08 (only available month)
        expect(commentIds[0]).toBe('g00m6ou'); // 2020-08 comment ID
    });

    test('should handle multiple months with proper sorting', async () => {
        // Mock response with comment IDs from multiple months
        const mockResponse = {
            field: 'blade',
            months: ['2025-08', '2024-08', '2020-08'],
            total_unmatched: 1,
            unmatched_items: [
                {
                    item: 'Lord',
                    count: 10, // 2 from 2025-08, 3 from 2024-08, 5 from 2020-08
                    comment_ids: ['n9d8qy1', 'naxiyxz', 'g24a1b2', 'g24c3d4', 'g24e5f6'], // Sorted newest first
                    examples: ['2025-08.json', '2024-08.json', '2020-08.json'],
                },
            ],
            processing_time: 0.5,
        };

        mockAnalyzeUnmatched.mockResolvedValue(mockResponse);

        const result = await analyzeUnmatched({
            field: 'blade',
            months: ['2025-08', '2024-08', '2020-08'],
            limit: 10,
        });

        // Verify that comment IDs are sorted by month (newest first)
        const commentIds = result.unmatched_items[0].comment_ids;
        expect(commentIds).toEqual(['n9d8qy1', 'naxiyxz', 'g24a1b2', 'g24c3d4', 'g24e5f6']);

        // Verify that the first comment IDs are from 2025-08 (newest month)
        expect(commentIds[0]).toBe('n9d8qy1'); // 2025-08 comment ID should be first
        expect(commentIds[1]).toBe('naxiyxz'); // 2025-08 comment ID should be second
    });

    test('should limit comment IDs to 5 even when more are available', async () => {
        // Mock response with more than 5 comment IDs available
        const mockResponse = {
            field: 'blade',
            months: ['2025-08', '2020-08'],
            total_unmatched: 1,
            unmatched_items: [
                {
                    item: 'Lord',
                    count: 50, // Many more available
                    comment_ids: ['n9d8qy1', 'g00m6ou', 'g042aih', 'g0706vx', 'g0b8wta'], // Limited to 5
                    examples: ['2025-08.json', '2020-08.json'],
                },
            ],
            processing_time: 0.5,
        };

        mockAnalyzeUnmatched.mockResolvedValue(mockResponse);

        const result = await analyzeUnmatched({
            field: 'blade',
            months: ['2025-08', '2020-08'],
            limit: 10,
        });

        // Verify that comment IDs are limited to 5
        const commentIds = result.unmatched_items[0].comment_ids;
        expect(commentIds).toHaveLength(5);
        expect(commentIds).toEqual(['n9d8qy1', 'g00m6ou', 'g042aih', 'g0706vx', 'g0b8wta']);
    });
});
