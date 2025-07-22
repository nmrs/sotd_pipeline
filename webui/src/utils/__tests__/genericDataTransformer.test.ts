import { createGenericTransformer, TransformerConfig, ProductType } from '../genericDataTransformer';

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

// Generic product data interface
interface ProductData {
    main: {
        text: string;
        count: number;
        comment_ids: string[];
        examples: string[];
        status: 'Matched' | 'Unmatched' | 'Filtered';
    };
    components?: Record<string, any>;
}

describe('Generic Data Transformer', () => {
    describe('createGenericTransformer', () => {
        test('should create transformer with basic configuration', () => {
            const config: TransformerConfig = {
                productType: 'razor',
                extractMainData: (data: any) => ({
                    text: data.item,
                    count: data.count,
                    comment_ids: data.comment_ids,
                    examples: data.examples,
                    status: data.matched ? 'Matched' : 'Unmatched'
                }),
                extractComponents: (data: any) => ({}),
                determineStatus: (data: any) => data.matched ? 'Matched' : 'Unmatched'
            };

            const transformer = createGenericTransformer(config);
            expect(transformer).toBeDefined();
            expect(typeof transformer.transform).toBe('function');
            expect(typeof transformer.transformArray).toBe('function');
        });

        test('should transform razor data correctly', () => {
            const razorConfig: TransformerConfig = {
                productType: 'razor',
                extractMainData: (data: RazorMatcherOutput) => ({
                    text: data.item,
                    count: data.count,
                    comment_ids: data.comment_ids,
                    examples: data.examples,
                    status: data.matched ? 'Matched' : 'Unmatched'
                }),
                extractComponents: (data: RazorMatcherOutput) => ({}),
                determineStatus: (data: RazorMatcherOutput) => data.matched ? 'Matched' : 'Unmatched'
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
                    format: 'DE'
                }
            };

            const result = transformer.transform(razorData);
            expect(result.main.text).toBe('Blackbird');
            expect(result.main.count).toBe(10);
            expect(result.main.status).toBe('Matched');
        });

        test('should transform blade data correctly', () => {
            const bladeConfig: TransformerConfig = {
                productType: 'blade',
                extractMainData: (data: BladeMatcherOutput) => ({
                    text: data.item,
                    count: data.count,
                    comment_ids: data.comment_ids,
                    examples: data.examples,
                    status: data.matched ? 'Matched' : 'Unmatched'
                }),
                extractComponents: (data: BladeMatcherOutput) => ({}),
                determineStatus: (data: BladeMatcherOutput) => data.matched ? 'Matched' : 'Unmatched'
            };

            const transformer = createGenericTransformer(bladeConfig);
            const bladeData: BladeMatcherOutput = {
                item: 'Feather',
                count: 15,
                comment_ids: ['789'],
                examples: ['Feather'],
                unmatched: {
                    pattern: 'Feather',
                    text: 'Feather blade'
                }
            };

            const result = transformer.transform(bladeData);
            expect(result.main.text).toBe('Feather');
            expect(result.main.count).toBe(15);
            expect(result.main.status).toBe('Unmatched');
        });

        test('should transform soap data correctly', () => {
            const soapConfig: TransformerConfig = {
                productType: 'soap',
                extractMainData: (data: SoapMatcherOutput) => ({
                    text: data.item,
                    count: data.count,
                    comment_ids: data.comment_ids,
                    examples: data.examples,
                    status: data.matched ? 'Matched' : 'Unmatched'
                }),
                extractComponents: (data: SoapMatcherOutput) => ({}),
                determineStatus: (data: SoapMatcherOutput) => data.matched ? 'Matched' : 'Unmatched'
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
                    maker: 'Declaration Grooming'
                }
            };

            const result = transformer.transform(soapData);
            expect(result.main.text).toBe('Declaration Grooming');
            expect(result.main.count).toBe(8);
            expect(result.main.status).toBe('Matched');
        });

        test('should handle null/undefined input gracefully', () => {
            const config: TransformerConfig = {
                productType: 'razor',
                extractMainData: (data: any) => ({
                    text: data?.item || '',
                    count: data?.count || 0,
                    comment_ids: data?.comment_ids || [],
                    examples: data?.examples || [],
                    status: 'Unmatched'
                }),
                extractComponents: (data: any) => ({}),
                determineStatus: (data: any) => 'Unmatched'
            };

            const transformer = createGenericTransformer(config);

            const nullResult = transformer.transform(null as any);
            expect(nullResult.main.text).toBe('');
            expect(nullResult.main.count).toBe(0);

            const undefinedResult = transformer.transform(undefined as any);
            expect(undefinedResult.main.text).toBe('');
            expect(undefinedResult.main.count).toBe(0);
        });

        test('should transform arrays correctly', () => {
            const config: TransformerConfig = {
                productType: 'razor',
                extractMainData: (data: RazorMatcherOutput) => ({
                    text: data.item,
                    count: data.count,
                    comment_ids: data.comment_ids,
                    examples: data.examples,
                    status: data.matched ? 'Matched' : 'Unmatched'
                }),
                extractComponents: (data: RazorMatcherOutput) => ({}),
                determineStatus: (data: RazorMatcherOutput) => data.matched ? 'Matched' : 'Unmatched'
            };

            const transformer = createGenericTransformer(config);
            const razorArray: RazorMatcherOutput[] = [
                {
                    item: 'Blackbird',
                    count: 10,
                    comment_ids: ['123'],
                    examples: ['Blackbird'],
                    matched: { brand: 'Blackbird', model: 'Razor' }
                },
                {
                    item: 'Merkur',
                    count: 5,
                    comment_ids: ['456'],
                    examples: ['Merkur'],
                    unmatched: { pattern: 'Merkur', text: 'Merkur razor' }
                }
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
                extractMainData: (data: any) => ({
                    text: data.item,
                    count: data.count,
                    comment_ids: data.comment_ids,
                    examples: data.examples,
                    status: data.matched ? 'Matched' : 'Unmatched'
                }),
                extractComponents: (data: any) => {
                    const components: Record<string, any> = {};
                    if (data.matched?.handle) {
                        components.handle = {
                            text: data.matched.handle.source_text || 'Unknown handle',
                            status: 'Matched'
                        };
                    }
                    if (data.matched?.knot) {
                        components.knot = {
                            text: data.matched.knot.source_text || 'Unknown knot',
                            status: 'Matched'
                        };
                    }
                    return components;
                },
                determineStatus: (data: any) => data.matched ? 'Matched' : 'Unmatched'
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
                        brand: 'Elite'
                    },
                    knot: {
                        source_text: 'Declaration knot',
                        brand: 'Declaration'
                    }
                }
            };

            const result = transformer.transform(brushData);
            expect(result.main.text).toBe('Elite handle w/ Declaration knot');
            expect(result.components?.handle?.text).toBe('Elite handle');
            expect(result.components?.knot?.text).toBe('Declaration knot');
        });

        test('should handle validation errors gracefully', () => {
            const config: TransformerConfig = {
                productType: 'razor',
                extractMainData: (data: any) => {
                    if (!data?.item) {
                        throw new Error('Invalid item');
                    }
                    return {
                        text: data.item,
                        count: data.count || 0,
                        comment_ids: data.comment_ids || [],
                        examples: data.examples || [],
                        status: 'Unmatched'
                    };
                },
                extractComponents: (data: any) => ({}),
                determineStatus: (data: any) => 'Unmatched'
            };

            const transformer = createGenericTransformer(config);
            const invalidData = {
                count: 5,
                comment_ids: ['123'],
                examples: ['Test']
                // Missing item field
            };

            const result = transformer.transform(invalidData);
            expect(result.main.text).toBe('');
            expect(result.main.count).toBe(5); // Should preserve the count from the data
        });

        test('should support custom status determination', () => {
            const config: TransformerConfig = {
                productType: 'razor',
                extractMainData: (data: any) => ({
                    text: data.item,
                    count: data.count,
                    comment_ids: data.comment_ids,
                    examples: data.examples,
                    status: 'Unmatched' // Will be overridden by determineStatus
                }),
                extractComponents: (data: any) => ({}),
                determineStatus: (data: any) => {
                    if (data.match_type === 'filtered') return 'Filtered';
                    if (data.matched) return 'Matched';
                    return 'Unmatched';
                }
            };

            const transformer = createGenericTransformer(config);
            const filteredData = {
                item: 'Filtered Razor',
                count: 1,
                comment_ids: ['123'],
                examples: ['Filtered Razor'],
                match_type: 'filtered'
            };

            const result = transformer.transform(filteredData);
            expect(result.main.status).toBe('Filtered');
        });
    });
}); 