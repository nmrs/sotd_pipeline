import {
    BrushSplit,
    BrushSplitOccurrence,
    BrushSplitValidationStatus,
    BrushSplitStatistics,
    BrushSplitLoadResponse,
    BrushSplitSaveRequest,
    BrushSplitSaveResponse
} from '../brushSplit';

describe('BrushSplit Types', () => {
    describe('BrushSplitOccurrence', () => {
        it('should have correct structure', () => {
            const occurrence: BrushSplitOccurrence = {
                file: '2025-01.json',
                comment_ids: ['abc123', 'def456']
            };

            expect(occurrence.file).toBe('2025-01.json');
            expect(occurrence.comment_ids).toEqual(['abc123', 'def456']);
        });
    });

    describe('BrushSplit', () => {
        it('should handle single component brush', () => {
            const split: BrushSplit = {
                original: 'Declaration B15',
                handle: null,
                knot: 'Declaration B15',
                validated: true,
                corrected: false,
                validated_at: '2025-01-27T14:30:00Z',
                occurrences: [{
                    file: '2025-01.json',
                    comment_ids: ['abc123']
                }]
            };

            expect(split.handle).toBeNull();
            expect(split.knot).toBe('Declaration B15');
            expect(split.validated).toBe(true);
        });

        it('should handle corrected split with system fields', () => {
            const split: BrushSplit = {
                original: 'Declaration B15 w/ Chisel & Hound Zebra',
                handle: 'Chisel & Hound Zebra',
                knot: 'Declaration B15',
                validated: true,
                corrected: true,
                validated_at: '2025-01-27T14:30:00Z',
                system_handle: 'Declaration B15',
                system_knot: 'Chisel & Hound Zebra',
                system_confidence: 'high',
                system_reasoning: 'Delimiter split: w/ detected',
                occurrences: [{
                    file: '2025-01.json',
                    comment_ids: ['abc123']
                }]
            };

            expect(split.corrected).toBe(true);
            expect(split.system_handle).toBe('Declaration B15');
            expect(split.system_confidence).toBe('high');
        });
    });

    describe('BrushSplitValidationStatus', () => {
        it('should have correct structure', () => {
            const status: BrushSplitValidationStatus = {
                validated: true,
                corrected: false,
                validated_at: '2025-01-27T14:30:00Z'
            };

            expect(status.validated).toBe(true);
            expect(status.corrected).toBe(false);
            expect(status.validated_at).toBe('2025-01-27T14:30:00Z');
        });
    });

    describe('BrushSplitStatistics', () => {
        it('should have correct structure', () => {
            const stats: BrushSplitStatistics = {
                total: 100,
                validated: 50,
                corrected: 10,
                validation_percentage: 50.0,
                correction_percentage: 20.0,
                split_types: {
                    delimiter: 30,
                    fiber_hint: 20,
                    brand_context: 40,
                    no_split: 10
                }
            };

            expect(stats.total).toBe(100);
            expect(stats.validation_percentage).toBe(50.0);
            expect(stats.split_types.delimiter).toBe(30);
        });
    });

    describe('BrushSplitLoadResponse', () => {
        it('should have correct structure', () => {
            const response: BrushSplitLoadResponse = {
                brush_splits: [{
                    original: 'Declaration B15',
                    handle: null,
                    knot: 'Declaration B15',
                    validated: false,
                    corrected: false,
                    validated_at: null,
                    occurrences: []
                }],
                statistics: {
                    total: 1,
                    validated: 0,
                    corrected: 0,
                    validation_percentage: 0.0,
                    correction_percentage: 0.0,
                    split_types: {
                        delimiter: 0,
                        fiber_hint: 0,
                        brand_context: 0,
                        no_split: 1
                    }
                }
            };

            expect(response.brush_splits).toHaveLength(1);
            expect(response.statistics.total).toBe(1);
        });
    });

    describe('BrushSplitSaveRequest', () => {
        it('should have correct structure', () => {
            const request: BrushSplitSaveRequest = {
                brush_splits: [{
                    original: 'Declaration B15',
                    handle: null,
                    knot: 'Declaration B15',
                    validated: true,
                    corrected: false,
                    validated_at: '2025-01-27T14:30:00Z',
                    occurrences: []
                }]
            };

            expect(request.brush_splits).toHaveLength(1);
        });
    });

    describe('BrushSplitSaveResponse', () => {
        it('should have correct structure', () => {
            const response: BrushSplitSaveResponse = {
                success: true,
                message: 'Saved 1 brush splits',
                saved_count: 1
            };

            expect(response.success).toBe(true);
            expect(response.saved_count).toBe(1);
        });
    });
}); 