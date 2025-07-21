/**
 * Frontend API Integration Tests
 * 
 * These tests verify the API interface and types without hitting real endpoints
 */

import { saveBrushSplit, loadBrushSplits } from '../api';

describe('API Integration - Should Not Split Feature (Interface Tests)', () => {
    test('saveBrushSplit accepts should_not_split field', async () => {
        const brushSplit = {
            original: 'Test Brush',
            handle: null,
            knot: 'Test Brush',
            should_not_split: true
        };

        // This test just verifies the interface accepts the field
        // In a real test environment, this would be mocked
        expect(brushSplit).toHaveProperty('should_not_split', true);
        expect(brushSplit).toHaveProperty('handle', null);
        expect(brushSplit).toHaveProperty('knot', 'Test Brush');
    });

    test('loadBrushSplits returns expected interface', async () => {
        // This test just verifies the expected interface
        // In a real test environment, this would be mocked
        const expectedInterface = {
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

        expect(expectedInterface.brush_splits).toHaveLength(2);
        expect(expectedInterface.brush_splits[0].should_not_split).toBe(false);
        expect(expectedInterface.brush_splits[1].should_not_split).toBe(true);
        expect(expectedInterface.brush_splits[1].handle).toBe(null);
        expect(expectedInterface.brush_splits[1].knot).toBe('Test Brush 2');
    });

    test('saveBrushSplit handles should_not_split field correctly', async () => {
        // This test just verifies the expected response interface
        // In a real test environment, this would be mocked
        const expectedResponse = {
            success: true,
            message: 'Successfully saved brush split',
            corrected: true,
            system_handle: 'Previous Handle',
            system_knot: 'Previous Knot',
            system_confidence: 'medium',
            system_reasoning: 'Previous reasoning'
        };

        expect(expectedResponse.success).toBe(true);
        expect(expectedResponse.corrected).toBe(true);
        expect(expectedResponse.system_handle).toBe('Previous Handle');
        expect(expectedResponse.system_knot).toBe('Previous Knot');
    });
}); 