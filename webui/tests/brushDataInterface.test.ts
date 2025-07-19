import { test, expect } from '@playwright/test';
import { BrushData, BrushMatcherOutput, transformBrushData } from '../src/utils/brushDataTransformer';

test.describe('BrushData Interface Validation', () => {
    test('should validate interface structure for matched brush with both components', async () => {
        const matcherOutput: BrushMatcherOutput = {
            item: 'Elite handle w/ Declaration knot',
            count: 5,
            comment_ids: ['123', '456', '789'],
            examples: ['Elite handle w/ Declaration knot'],
            match_type: 'exact',
            matched: {
                handle: {
                    brand: 'Elite',
                    model: 'handle',
                    maker: 'Elite'
                },
                knot: {
                    brand: 'Declaration',
                    model: 'knot',
                    maker: 'Declaration',
                    fiber: 'badger',
                    size: '24mm'
                }
            }
        };

        const brushData: BrushData = transformBrushData(matcherOutput);

        // Validate main structure
        expect(brushData.main).toBeDefined();
        expect(brushData.main.text).toBe('Elite handle w/ Declaration knot');
        expect(brushData.main.count).toBe(5);
        expect(brushData.main.comment_ids).toEqual(['123', '456', '789']);
        expect(brushData.main.examples).toEqual(['Elite handle w/ Declaration knot']);
        expect(brushData.main.status).toBe('Matched');

        // Validate components structure
        expect(brushData.components).toBeDefined();
        expect(brushData.components.handle).toBeDefined();
        expect(brushData.components.knot).toBeDefined();

        // Validate handle component
        expect(brushData.components.handle!.text).toBe('Elite handle');
        expect(brushData.components.handle!.status).toBe('Matched');
        expect(brushData.components.handle!.pattern).toBeUndefined();

        // Validate knot component
        expect(brushData.components.knot!.text).toBe('Declaration knot');
        expect(brushData.components.knot!.status).toBe('Matched');
        expect(brushData.components.knot!.pattern).toBeUndefined();
    });

    test('should validate interface structure for unmatched brush with both components', async () => {
        const matcherOutput: BrushMatcherOutput = {
            item: 'Custom handle w/ Unknown knot',
            count: 3,
            comment_ids: ['111', '222'],
            examples: ['Custom handle w/ Unknown knot'],
            unmatched: {
                handle: {
                    pattern: 'Custom',
                    text: 'Custom handle'
                },
                knot: {
                    pattern: 'Unknown',
                    text: 'Unknown knot'
                }
            }
        };

        const brushData: BrushData = transformBrushData(matcherOutput);

        // Validate main structure
        expect(brushData.main.status).toBe('Unmatched');

        // Validate handle component
        expect(brushData.components.handle!.text).toBe('Custom handle');
        expect(brushData.components.handle!.status).toBe('Unmatched');
        expect(brushData.components.handle!.pattern).toBe('Custom');

        // Validate knot component
        expect(brushData.components.knot!.text).toBe('Unknown knot');
        expect(brushData.components.knot!.status).toBe('Unmatched');
        expect(brushData.components.knot!.pattern).toBe('Unknown');
    });

    test('should validate interface structure for handle-only brush', async () => {
        const matcherOutput: BrushMatcherOutput = {
            item: 'Elite handle',
            count: 2,
            comment_ids: ['333'],
            examples: ['Elite handle'],
            matched: {
                handle: {
                    brand: 'Elite',
                    model: 'handle',
                    maker: 'Elite'
                }
            }
        };

        const brushData: BrushData = transformBrushData(matcherOutput);

        // Validate main structure
        expect(brushData.main.status).toBe('Matched');

        // Validate handle component exists
        expect(brushData.components.handle).toBeDefined();
        expect(brushData.components.handle!.text).toBe('Elite handle');
        expect(brushData.components.handle!.status).toBe('Matched');

        // Validate knot component is undefined
        expect(brushData.components.knot).toBeUndefined();
    });

    test('should validate interface structure for knot-only brush', async () => {
        const matcherOutput: BrushMatcherOutput = {
            item: 'Declaration knot',
            count: 4,
            comment_ids: ['555', '666'],
            examples: ['Declaration knot'],
            matched: {
                knot: {
                    brand: 'Declaration',
                    model: 'knot',
                    maker: 'Declaration'
                }
            }
        };

        const brushData: BrushData = transformBrushData(matcherOutput);

        // Validate main structure
        expect(brushData.main.status).toBe('Matched');

        // Validate handle component is undefined
        expect(brushData.components.handle).toBeUndefined();

        // Validate knot component exists
        expect(brushData.components.knot).toBeDefined();
        expect(brushData.components.knot!.text).toBe('Declaration knot');
        expect(brushData.components.knot!.status).toBe('Matched');
    });

    test('should validate status consistency between main brush and components', async () => {
        // Test all matched components
        const allMatchedOutput: BrushMatcherOutput = {
            item: 'Elite handle w/ Declaration knot',
            count: 5,
            comment_ids: ['123'],
            examples: ['Elite handle w/ Declaration knot'],
            match_type: 'exact',
            matched: {
                handle: { brand: 'Elite', model: 'handle' },
                knot: { brand: 'Declaration', model: 'knot' }
            }
        };

        const allMatchedData = transformBrushData(allMatchedOutput);
        expect(allMatchedData.main.status).toBe('Matched');
        expect(allMatchedData.components.handle!.status).toBe('Matched');
        expect(allMatchedData.components.knot!.status).toBe('Matched');

        // Test all unmatched components
        const allUnmatchedOutput: BrushMatcherOutput = {
            item: 'Unknown handle w/ Unknown knot',
            count: 2,
            comment_ids: ['456'],
            examples: ['Unknown handle w/ Unknown knot'],
            unmatched: {
                handle: { pattern: 'Unknown', text: 'Unknown handle' },
                knot: { pattern: 'Unknown', text: 'Unknown knot' }
            }
        };

        const allUnmatchedData = transformBrushData(allUnmatchedOutput);
        expect(allUnmatchedData.main.status).toBe('Unmatched');
        expect(allUnmatchedData.components.handle!.status).toBe('Unmatched');
        expect(allUnmatchedData.components.knot!.status).toBe('Unmatched');

        // Test mixed status (should default to unmatched)
        const mixedOutput: BrushMatcherOutput = {
            item: 'Elite handle w/ Unknown knot',
            count: 3,
            comment_ids: ['789'],
            examples: ['Elite handle w/ Unknown knot'],
            matched: {
                handle: { brand: 'Elite', model: 'handle' }
            },
            unmatched: {
                knot: { pattern: 'Unknown', text: 'Unknown knot' }
            }
        };

        const mixedData = transformBrushData(mixedOutput);
        expect(mixedData.main.status).toBe('Unmatched');
        expect(mixedData.components.handle!.status).toBe('Matched');
        expect(mixedData.components.knot!.status).toBe('Unmatched');
    });

    test('should validate filtered status detection', async () => {
        const filteredOutput: BrushMatcherOutput = {
            item: 'Filtered brush',
            count: 1,
            comment_ids: ['999'],
            examples: ['Filtered brush'],
            match_type: 'filtered'
        };

        const filteredData = transformBrushData(filteredOutput);
        expect(filteredData.main.status).toBe('Filtered');
    });

    test('should validate error handling for invalid data', async () => {
        // Test missing required fields
        const invalidOutput = {
            count: 1,
            comment_ids: ['123'],
            examples: ['test']
        } as BrushMatcherOutput;

        expect(() => transformBrushData(invalidOutput)).toThrow('Invalid item value');

        // Test null item
        const nullItemOutput: BrushMatcherOutput = {
            item: null as any,
            count: 1,
            comment_ids: ['123'],
            examples: ['test']
        };

        expect(() => transformBrushData(nullItemOutput)).toThrow('Invalid item value');

        // Test empty item
        const emptyItemOutput: BrushMatcherOutput = {
            item: '',
            count: 1,
            comment_ids: ['123'],
            examples: ['test']
        };

        expect(() => transformBrushData(emptyItemOutput)).toThrow('Invalid item value');
    });

    test('should validate TypeScript compilation and type safety', async () => {
        // This test validates that the interface is properly typed
        const matcherOutput: BrushMatcherOutput = {
            item: 'Test brush',
            count: 1,
            comment_ids: ['123'],
            examples: ['Test brush']
        };

        const brushData: BrushData = transformBrushData(matcherOutput);

        // TypeScript should enforce these types
        expect(typeof brushData.main.text).toBe('string');
        expect(typeof brushData.main.count).toBe('number');
        expect(Array.isArray(brushData.main.comment_ids)).toBe(true);
        expect(Array.isArray(brushData.main.examples)).toBe(true);
        expect(['Matched', 'Unmatched', 'Filtered']).toContain(brushData.main.status);

        // Validate component types
        if (brushData.components.handle) {
            expect(typeof brushData.components.handle.text).toBe('string');
            expect(['Matched', 'Unmatched', 'Filtered']).toContain(brushData.components.handle.status);
            if (brushData.components.handle.pattern) {
                expect(typeof brushData.components.handle.pattern).toBe('string');
            }
        }

        if (brushData.components.knot) {
            expect(typeof brushData.components.knot.text).toBe('string');
            expect(['Matched', 'Unmatched', 'Filtered']).toContain(brushData.components.knot.status);
            if (brushData.components.knot.pattern) {
                expect(typeof brushData.components.knot.pattern).toBe('string');
            }
        }
    });
}); 