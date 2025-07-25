import { createGenericTransformer, TransformerConfig } from '../genericDataTransformer';

// Mock product type interfaces for testing
interface RazorMatcherOutput {
  item: string;
  count: number;
  comment_ids: string[];
  examples: string[];
  match_type?: string;
  matched?: {
    brand?: string;
    model?: string;
    format?: string;
  };
  unmatched?: {
    pattern?: string;
    text?: string;
  };
}

interface BladeMatcherOutput {
  item: string;
  count: number;
  comment_ids: string[];
  examples: string[];
  match_type?: string;
  matched?: {
    brand?: string;
    model?: string;
    manufacturer?: string;
  };
  unmatched?: {
    pattern?: string;
    text?: string;
  };
}

interface SoapMatcherOutput {
  item: string;
  count: number;
  comment_ids: string[];
  examples: string[];
  match_type?: string;
  matched?: {
    brand?: string;
    model?: string;
    maker?: string;
  };
  unmatched?: {
    pattern?: string;
    text?: string;
  };
}

interface BrushMatcherOutput {
  item: string;
  count: number;
  comment_ids: string[];
  examples: string[];
  matched?: {
    handle?: {
      source_text: string;
      brand: string;
    };
    knot?: {
      source_text: string;
      brand: string;
    };
  };
}

interface TestData {
  item?: string;
  count?: number;
  comment_ids?: string[];
  examples?: string[];
  match_type?: string;
  matched?: unknown;
}

describe('Generic Data Transformer', () => {
  describe('createGenericTransformer', () => {
    test('should create transformer with basic configuration', () => {
      const config: TransformerConfig = {
        productType: 'razor',
        extractMainData: (data: unknown) => ({
          text: (data as RazorMatcherOutput).item,
          count: (data as RazorMatcherOutput).count,
          comment_ids: (data as RazorMatcherOutput).comment_ids,
          examples: (data as RazorMatcherOutput).examples,
          status: (data as RazorMatcherOutput).matched ? 'Matched' : 'Unmatched',
        }),
        extractComponents: () => ({}),
        determineStatus: (data: unknown) =>
          (data as RazorMatcherOutput).matched ? 'Matched' : 'Unmatched',
      };

      const transformer = createGenericTransformer(config);
      expect(transformer).toBeDefined();
      expect(typeof transformer.transform).toBe('function');
      expect(typeof transformer.transformArray).toBe('function');
    });

    test('should transform razor data correctly', () => {
      const razorConfig: TransformerConfig = {
        productType: 'razor',
        extractMainData: (data: unknown) => ({
          text: (data as RazorMatcherOutput).item,
          count: (data as RazorMatcherOutput).count,
          comment_ids: (data as RazorMatcherOutput).comment_ids,
          examples: (data as RazorMatcherOutput).examples,
          status: (data as RazorMatcherOutput).matched ? 'Matched' : 'Unmatched',
        }),
        extractComponents: () => ({}),
        determineStatus: (data: unknown) =>
          (data as RazorMatcherOutput).matched ? 'Matched' : 'Unmatched',
      };

      const transformer = createGenericTransformer(razorConfig);
      const razorData: RazorMatcherOutput = {
        item: 'Blackbird',
        count: 10,
        comment_ids: ['123', '456'],
        examples: ['Blackbird'],
        match_type: 'exact',
        matched: {
          brand: 'Blackbird',
          model: 'Razor',
          format: 'DE',
        },
      };

      const result = transformer.transform(razorData);
      expect(result.main.text).toBe('Blackbird');
      expect(result.main.count).toBe(10);
      expect(result.main.status).toBe('Matched');
    });

    test('should transform blade data correctly', () => {
      const bladeConfig: TransformerConfig = {
        productType: 'blade',
        extractMainData: (data: unknown) => ({
          text: (data as BladeMatcherOutput).item,
          count: (data as BladeMatcherOutput).count,
          comment_ids: (data as BladeMatcherOutput).comment_ids,
          examples: (data as BladeMatcherOutput).examples,
          status: (data as BladeMatcherOutput).matched ? 'Matched' : 'Unmatched',
        }),
        extractComponents: () => ({}),
        determineStatus: (data: unknown) =>
          (data as BladeMatcherOutput).matched ? 'Matched' : 'Unmatched',
      };

      const transformer = createGenericTransformer(bladeConfig);
      const bladeData: BladeMatcherOutput = {
        item: 'Feather',
        count: 15,
        comment_ids: ['789'],
        examples: ['Feather'],
        unmatched: {
          pattern: 'Feather',
          text: 'Feather blade',
        },
      };

      const result = transformer.transform(bladeData);
      expect(result.main.text).toBe('Feather');
      expect(result.main.count).toBe(15);
      expect(result.main.status).toBe('Unmatched');
    });

    test('should transform soap data correctly', () => {
      const soapConfig: TransformerConfig = {
        productType: 'soap',
        extractMainData: (_data: unknown) => ({
          text: (_data as SoapMatcherOutput).item,
          count: (_data as SoapMatcherOutput).count,
          comment_ids: (_data as SoapMatcherOutput).comment_ids,
          examples: (_data as SoapMatcherOutput).examples,
          status: (_data as SoapMatcherOutput).matched ? 'Matched' : 'Unmatched',
        }),
        extractComponents: () => ({}),
        determineStatus: (data: unknown) =>
          (data as SoapMatcherOutput).matched ? 'Matched' : 'Unmatched',
      };

      const transformer = createGenericTransformer(soapConfig);
      const soapData: SoapMatcherOutput = {
        item: 'Declaration Grooming',
        count: 8,
        comment_ids: ['101', '102'],
        examples: ['Declaration Grooming'],
        match_type: 'exact',
        matched: {
          brand: 'Declaration Grooming',
          model: 'Soap',
          maker: 'Declaration Grooming',
        },
      };

      const result = transformer.transform(soapData);
      expect(result.main.text).toBe('Declaration Grooming');
      expect(result.main.count).toBe(8);
      expect(result.main.status).toBe('Matched');
    });

    test('should handle null/undefined input gracefully', () => {
      const config: TransformerConfig = {
        productType: 'razor',
        extractMainData: (data: unknown) => ({
          text: (data as TestData | null | undefined)?.item || '',
          count: (data as TestData | null | undefined)?.count || 0,
          comment_ids: (data as TestData | null | undefined)?.comment_ids || [],
          examples: (data as TestData | null | undefined)?.examples || [],
          status: 'Unmatched',
        }),
        extractComponents: () => ({}),
        determineStatus: () => 'Unmatched',
      };

      const transformer = createGenericTransformer(config);

      const nullResult = transformer.transform(null as TestData | null | undefined);
      expect(nullResult.main.text).toBe('');
      expect(nullResult.main.count).toBe(0);

      const undefinedResult = transformer.transform(undefined as TestData | null | undefined);
      expect(undefinedResult.main.text).toBe('');
      expect(undefinedResult.main.count).toBe(0);
    });

    test('should transform arrays correctly', () => {
      const config: TransformerConfig = {
        productType: 'razor',
        extractMainData: (data: unknown) => ({
          text: (data as RazorMatcherOutput).item,
          count: (data as RazorMatcherOutput).count,
          comment_ids: (data as RazorMatcherOutput).comment_ids,
          examples: (data as RazorMatcherOutput).examples,
          status: (data as RazorMatcherOutput).matched ? 'Matched' : 'Unmatched',
        }),
        extractComponents: () => ({}),
        determineStatus: (data: unknown) =>
          (data as RazorMatcherOutput).matched ? 'Matched' : 'Unmatched',
      };

      const transformer = createGenericTransformer(config);
      const razorArray: RazorMatcherOutput[] = [
        {
          item: 'Blackbird',
          count: 10,
          comment_ids: ['123'],
          examples: ['Blackbird'],
          matched: { brand: 'Blackbird', model: 'Razor' },
        },
        {
          item: 'Merkur',
          count: 5,
          comment_ids: ['456'],
          examples: ['Merkur'],
          unmatched: { pattern: 'Merkur', text: 'Merkur razor' },
        },
      ];

      const results = transformer.transformArray(razorArray);
      expect(results).toHaveLength(2);
      expect(results[0].main.text).toBe('Blackbird');
      expect(results[0].main.status).toBe('Matched');
      expect(results[1].main.text).toBe('Merkur');
      expect(results[1].main.status).toBe('Unmatched');
    });

    test('should handle complex component extraction', () => {
      const config: TransformerConfig = {
        productType: 'brush',
        extractMainData: (data: unknown) => ({
          text: (data as BrushMatcherOutput).item,
          count: (data as BrushMatcherOutput).count,
          comment_ids: (data as BrushMatcherOutput).comment_ids,
          examples: (data as BrushMatcherOutput).examples,
          status: (data as BrushMatcherOutput).matched ? 'Matched' : 'Unmatched',
        }),
        extractComponents: (data: unknown) => {
          const brushData = data as BrushMatcherOutput;
          const components: Record<string, unknown> = {};
          if (brushData.matched?.handle) {
            components.handle = {
              text: brushData.matched.handle.source_text || 'Unknown handle',
              status: 'Matched',
            };
          }
          if (brushData.matched?.knot) {
            components.knot = {
              text: brushData.matched.knot.source_text || 'Unknown knot',
              status: 'Matched',
            };
          }
          return components;
        },
        determineStatus: (data: unknown) =>
          (data as BrushMatcherOutput).matched ? 'Matched' : 'Unmatched',
      };

      const transformer = createGenericTransformer(config);
      const brushData = {
        item: 'Elite handle w/ Declaration knot',
        count: 5,
        comment_ids: ['123'],
        examples: ['Elite handle w/ Declaration knot'],
        matched: {
          handle: {
            source_text: 'Elite handle',
            brand: 'Elite',
          },
          knot: {
            source_text: 'Declaration knot',
            brand: 'Declaration',
          },
        },
      };

      const result = transformer.transform(brushData);
      expect(result.main.text).toBe('Elite handle w/ Declaration knot');
      expect((result.components?.handle as { text: string })?.text).toBe('Elite handle');
      expect((result.components?.knot as { text: string })?.text).toBe('Declaration knot');
    });

    test('should handle validation errors gracefully', () => {
      const config: TransformerConfig = {
        productType: 'razor',
        extractMainData: (data: unknown) => {
          const testData = data as TestData;
          if (!testData?.item) {
            throw new Error('Invalid item');
          }
          return {
            text: testData.item,
            count: testData.count || 0,
            comment_ids: testData.comment_ids || [],
            examples: testData.examples || [],
            status: 'Unmatched',
          };
        },
        extractComponents: () => ({}),
        determineStatus: () => 'Unmatched',
      };

      const transformer = createGenericTransformer(config);
      const invalidData = {
        count: 5,
        comment_ids: ['123'],
        examples: ['Test'],
        // Missing item field
      };

      const result = transformer.transform(invalidData);
      expect(result.main.text).toBe('');
      expect(result.main.count).toBe(5); // Should preserve the count from the data
    });

    test('should support custom status determination', () => {
      const config: TransformerConfig = {
        productType: 'razor',
        extractMainData: (data: unknown) => ({
          text: (data as TestData).item || '',
          count: (data as TestData).count || 0,
          comment_ids: (data as TestData).comment_ids || [],
          examples: (data as TestData).examples || [],
          status: 'Unmatched', // Will be overridden by determineStatus
        }),
        extractComponents: () => ({}),
        determineStatus: (data: unknown) => {
          const testData = data as TestData;
          if (testData.match_type === 'filtered') return 'Filtered';
          if (testData.matched) return 'Matched';
          return 'Unmatched';
        },
      };

      const transformer = createGenericTransformer(config);
      const filteredData = {
        item: 'Filtered Razor',
        count: 1,
        comment_ids: ['123'],
        examples: ['Filtered Razor'],
        match_type: 'filtered',
      };

      const result = transformer.transform(filteredData);
      expect(result.main.status).toBe('Filtered');
    });
  });
});
