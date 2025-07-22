import {
  transformBrushData,
  transformBrushDataArray,
  BrushData,
  BrushMatcherOutput,
} from '../../utils/brushDataTransformer';

// Mock the API service for integration testing
jest.mock('../api', () => ({
  analyzeUnmatched: jest.fn(),
  getCommentDetail: jest.fn(),
  checkFilteredStatus: jest.fn(),
}));

// Import the mocked function
import { analyzeUnmatched } from '../api';

describe('BrushData Transformer Integration Tests', () => {
  beforeEach(() => {
    (analyzeUnmatched as jest.Mock).mockClear();
  });

  describe('Real Data Integration', () => {
    test('should transform real brush matcher output correctly', () => {
      // Real brush matcher output structure
      const realMatcherOutput: BrushMatcherOutput = {
        item: 'Elite handle w/ Declaration knot',
        count: 5,
        comment_ids: ['123', '456', '789'],
        examples: ['Elite handle w/ Declaration knot', 'Elite w/ Declaration'],
        match_type: 'exact',
        matched: {
          handle: {
            brand: 'Elite',
            model: 'handle',
            maker: 'Elite',
          },
          knot: {
            brand: 'Declaration',
            model: 'knot',
            maker: 'Declaration',
            fiber: 'badger',
            size: '24mm',
          },
        },
      };

      const brushData: BrushData = transformBrushData(realMatcherOutput);

      // Validate complete structure
      expect(brushData.main).toBeDefined();
      expect(brushData.main.text).toBe('Elite handle w/ Declaration knot');
      expect(brushData.main.count).toBe(5);
      expect(brushData.main.comment_ids).toEqual(['123', '456', '789']);
      expect(brushData.main.examples).toEqual([
        'Elite handle w/ Declaration knot',
        'Elite w/ Declaration',
      ]);
      expect(brushData.main.status).toBe('Matched');

      // Validate components structure
      expect(brushData.components).toBeDefined();
      expect(brushData.components.handle).toBeDefined();
      expect(brushData.components.knot).toBeDefined();

      // Validate handle component
      expect(brushData.components.handle!.text).toBe('Elite handle');
      expect(brushData.components.handle!.status).toBe('Matched');

      // Validate knot component
      expect(brushData.components.knot!.text).toBe('Declaration knot');
      expect(brushData.components.knot!.status).toBe('Matched');
    });

    test('should handle real unmatched brush data', () => {
      // Real unmatched brush data
      const realUnmatchedOutput: BrushMatcherOutput = {
        item: 'Custom handle w/ Unknown knot',
        count: 3,
        comment_ids: ['111', '222', '333'],
        examples: ['Custom handle w/ Unknown knot'],
        unmatched: {
          handle: {
            pattern: 'Custom',
            text: 'Custom handle',
          },
          knot: {
            pattern: 'Unknown',
            text: 'Unknown knot',
          },
        },
      };

      const brushData: BrushData = transformBrushData(realUnmatchedOutput);

      // Validate main structure
      expect(brushData.main.text).toBe('Custom handle w/ Unknown knot');
      expect(brushData.main.count).toBe(3);
      expect(brushData.main.status).toBe('Unmatched');

      // Validate components structure
      expect(brushData.components.handle!.text).toBe('Custom handle');
      expect(brushData.components.handle!.status).toBe('Unmatched');
      expect(brushData.components.handle!.pattern).toBe('Custom');

      expect(brushData.components.knot!.text).toBe('Unknown knot');
      expect(brushData.components.knot!.status).toBe('Unmatched');
      expect(brushData.components.knot!.pattern).toBe('Unknown');
    });

    test('should transform array of real brush data', () => {
      // Real brush matcher output array
      const realMatcherOutputArray: BrushMatcherOutput[] = [
        {
          item: 'Simpson Chubby 2',
          count: 10,
          comment_ids: ['123', '456'],
          examples: ['Simpson Chubby 2'],
          match_type: 'exact',
          matched: {
            handle: {
              brand: 'Simpson',
              model: 'Chubby 2',
              maker: 'Simpson',
            },
            knot: {
              brand: 'Simpson',
              model: 'Badger',
              maker: 'Simpson',
              fiber: 'badger',
              size: '27mm',
            },
          },
        },
        {
          item: 'Declaration B15',
          count: 5,
          comment_ids: ['789'],
          examples: ['Declaration B15'],
          unmatched: {
            handle: {
              pattern: 'Declaration',
              text: 'Declaration B15',
            },
            knot: {
              pattern: 'Declaration',
              text: 'Declaration Badger',
            },
          },
        },
      ];

      const brushDataArray: BrushData[] = transformBrushDataArray(realMatcherOutputArray);

      // Validate array structure
      expect(brushDataArray).toHaveLength(2);

      // Validate first item (matched)
      expect(brushDataArray[0].main.text).toBe('Simpson Chubby 2');
      expect(brushDataArray[0].main.status).toBe('Matched');
      expect(brushDataArray[0].components.handle!.status).toBe('Matched');
      expect(brushDataArray[0].components.knot!.status).toBe('Matched');

      // Validate second item (unmatched)
      expect(brushDataArray[1].main.text).toBe('Declaration B15');
      expect(brushDataArray[1].main.status).toBe('Unmatched');
      expect(brushDataArray[1].components.handle!.status).toBe('Unmatched');
      expect(brushDataArray[1].components.knot!.status).toBe('Unmatched');
    });
  });

  describe('Edge Case Integration', () => {
    test('should handle handle-only brushes with real data', () => {
      const handleOnlyOutput: BrushMatcherOutput = {
        item: 'Elite handle',
        count: 2,
        comment_ids: ['333', '444'],
        examples: ['Elite handle'],
        match_type: 'exact',
        matched: {
          handle: {
            brand: 'Elite',
            model: 'handle',
            maker: 'Elite',
          },
        },
      };

      const brushData: BrushData = transformBrushData(handleOnlyOutput);

      // Validate main structure
      expect(brushData.main.text).toBe('Elite handle');
      expect(brushData.main.status).toBe('Matched');

      // Validate handle component exists
      expect(brushData.components.handle).toBeDefined();
      expect(brushData.components.handle!.text).toBe('Elite handle');
      expect(brushData.components.handle!.status).toBe('Matched');

      // Validate knot component is undefined
      expect(brushData.components.knot).toBeUndefined();
    });

    test('should handle knot-only brushes with real data', () => {
      const knotOnlyOutput: BrushMatcherOutput = {
        item: 'Declaration knot',
        count: 4,
        comment_ids: ['555', '666'],
        examples: ['Declaration knot'],
        match_type: 'exact',
        matched: {
          knot: {
            brand: 'Declaration',
            model: 'knot',
            maker: 'Declaration',
            fiber: 'badger',
            size: '24mm',
          },
        },
      };

      const brushData: BrushData = transformBrushData(knotOnlyOutput);

      // Validate main structure
      expect(brushData.main.text).toBe('Declaration knot');
      expect(brushData.main.status).toBe('Matched');

      // Validate handle component is undefined
      expect(brushData.components.handle).toBeUndefined();

      // Validate knot component exists
      expect(brushData.components.knot).toBeDefined();
      expect(brushData.components.knot!.text).toBe('Declaration knot');
      expect(brushData.components.knot!.status).toBe('Matched');
    });

    test('should handle mixed status brushes with real data', () => {
      const mixedOutput: BrushMatcherOutput = {
        item: 'Elite handle w/ Unknown knot',
        count: 3,
        comment_ids: ['777', '888'],
        examples: ['Elite handle w/ Unknown knot'],
        matched: {
          handle: {
            brand: 'Elite',
            model: 'handle',
            maker: 'Elite',
          },
        },
        unmatched: {
          knot: {
            pattern: 'Unknown',
            text: 'Unknown knot',
          },
        },
      };

      const brushData: BrushData = transformBrushData(mixedOutput);

      // Validate main structure (should be unmatched due to mixed status)
      expect(brushData.main.text).toBe('Elite handle w/ Unknown knot');
      expect(brushData.main.status).toBe('Unmatched');

      // Validate handle component (matched)
      expect(brushData.components.handle!.text).toBe('Elite handle');
      expect(brushData.components.handle!.status).toBe('Matched');

      // Validate knot component (unmatched)
      expect(brushData.components.knot!.text).toBe('Unknown knot');
      expect(brushData.components.knot!.status).toBe('Unmatched');
      expect(brushData.components.knot!.pattern).toBe('Unknown');
    });
  });

  describe('Error Handling Integration', () => {
    test('should handle malformed real data gracefully', () => {
      const malformedOutput = {
        item: 'Valid Brush',
        count: 1,
        comment_ids: ['123'],
        examples: ['Example'],
        // Missing match_type and matched/unmatched fields
      } as any;

      // Should not throw error
      expect(() => transformBrushData(malformedOutput)).not.toThrow();

      const brushData = transformBrushData(malformedOutput);

      // Should handle gracefully
      expect(brushData.main.text).toBe('Valid Brush');
      expect(brushData.main.count).toBe(1);
      expect(brushData.main.status).toBe('Unmatched');
    });

    test('should handle null/undefined real data gracefully', () => {
      // Should not throw error
      expect(() => transformBrushData(null as any)).not.toThrow();
      expect(() => transformBrushData(undefined as any)).not.toThrow();

      const nullResult = transformBrushData(null as any);
      const undefinedResult = transformBrushData(undefined as any);

      // Should return default structure
      expect(nullResult.main.text).toBe('');
      expect(undefinedResult.main.text).toBe('');
    });

    test('should handle empty arrays gracefully', () => {
      const emptyArray: BrushMatcherOutput[] = [];

      const result = transformBrushDataArray(emptyArray);

      expect(result).toEqual([]);
    });
  });

  describe('Performance Integration', () => {
    test('should handle large datasets efficiently', () => {
      const largeDataset: BrushMatcherOutput[] = Array.from({ length: 100 }, (_, i) => ({
        item: `Brush ${i}`,
        count: i,
        comment_ids: [`comment-${i}`],
        examples: [`example-${i}`],
        match_type: 'exact',
        matched: {
          handle: {
            brand: `Brand ${i}`,
            model: `Model ${i}`,
            maker: `Maker ${i}`,
          },
        },
      }));

      const startTime = performance.now();
      const result = transformBrushDataArray(largeDataset);
      const transformTime = performance.now() - startTime;

      // Should transform efficiently (under 50ms for 100 items)
      expect(transformTime).toBeLessThan(50);
      expect(result).toHaveLength(100);
    });
  });
});
