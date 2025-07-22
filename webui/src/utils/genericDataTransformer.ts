/**
 * Generic data transformation utilities
 * Provides a reusable pattern for transforming different product types
 */

export type ProductType = 'razor' | 'blade' | 'brush' | 'soap';

export interface MainData {
    text: string;
    count: number;
    comment_ids: string[];
    examples: string[];
    status: 'Matched' | 'Unmatched' | 'Filtered';
}

export interface ProductData {
    main: MainData;
    components?: Record<string, any>;
}

export interface TransformerConfig<T = any> {
    productType: ProductType;
    extractMainData: (data: T) => MainData;
    extractComponents: (data: T) => Record<string, any>;
    determineStatus: (data: T) => 'Matched' | 'Unmatched' | 'Filtered';
}

export interface DataTransformer<T = any> {
    transform: (data: T | null | undefined) => ProductData;
    transformArray: (data: T[]) => ProductData[];
}

/**
 * Creates a generic data transformer based on configuration
 * 
 * @param config - Configuration object defining how to transform the data
 * @returns A transformer object with transform and transformArray methods
 */
export function createGenericTransformer<T = any>(config: TransformerConfig<T>): DataTransformer<T> {
    const { extractMainData, extractComponents, determineStatus } = config;

    /**
     * Transforms a single data item
     */
    function transform(data: T | null | undefined): ProductData {
        // Handle null/undefined input gracefully
        if (!data) {
            return {
                main: {
                    text: '',
                    count: 0,
                    comment_ids: [],
                    examples: [],
                    status: 'Unmatched'
                },
                components: {}
            };
        }

        try {
            // Extract main data
            const mainData = extractMainData(data);

            // Determine overall status
            const overallStatus = determineStatus(data);

            // Extract components
            const components = extractComponents(data);

            return {
                main: {
                    ...mainData,
                    status: overallStatus
                },
                components: Object.keys(components).length > 0 ? components : undefined
            };
        } catch (error) {
            // Return default structure on validation errors
            return {
                main: {
                    text: (data as any)?.item || '',
                    count: (data as any)?.count || 0,
                    comment_ids: (data as any)?.comment_ids || [],
                    examples: (data as any)?.examples || [],
                    status: 'Unmatched'
                },
                components: {}
            };
        }
    }

    /**
     * Transforms an array of data items
     */
    function transformArray(data: T[]): ProductData[] {
        return data.map(item => transform(item));
    }

    return {
        transform,
        transformArray
    };
}

/**
 * Creates a simple transformer for products without components
 * 
 * @param productType - The type of product being transformed
 * @returns A transformer configured for simple product data
 */
export function createSimpleTransformer(productType: ProductType): DataTransformer<any> {
    return createGenericTransformer({
        productType,
        extractMainData: (data: any) => ({
            text: data?.item || '',
            count: data?.count || 0,
            comment_ids: data?.comment_ids || [],
            examples: data?.examples || [],
            status: 'Unmatched' // Will be overridden by determineStatus
        }),
        extractComponents: () => ({}),
        determineStatus: (data: any) => {
            if (data?.match_type === 'filtered') return 'Filtered';
            if (data?.matched) return 'Matched';
            return 'Unmatched';
        }
    });
}

/**
 * Creates a brush transformer with handle/knot components
 * 
 * @returns A transformer configured for brush data with components
 */
export function createBrushTransformer(): DataTransformer<any> {
    return createGenericTransformer({
        productType: 'brush',
        extractMainData: (data: any) => ({
            text: data?.item || '',
            count: data?.count || 0,
            comment_ids: data?.comment_ids || [],
            examples: data?.examples || [],
            status: 'Unmatched' // Will be overridden by determineStatus
        }),
        extractComponents: (data: any) => {
            const components: Record<string, any> = {};

            // Extract handle component
            if (data?.matched?.handle) {
                const { brand, model, source_text } = data.matched.handle;
                components.handle = {
                    text: source_text || (brand && model ? `${brand} ${model}` : brand || model || 'Unknown handle'),
                    status: 'Matched'
                };
            } else if (data?.unmatched?.handle) {
                components.handle = {
                    text: data.unmatched.handle.text || 'Unknown handle',
                    status: 'Unmatched',
                    pattern: data.unmatched.handle.pattern
                };
            }

            // Extract knot component
            if (data?.matched?.knot) {
                const { brand, model, source_text } = data.matched.knot;
                components.knot = {
                    text: source_text || (brand && model ? `${brand} ${model}` : brand || model || 'Unknown knot'),
                    status: 'Matched'
                };
            } else if (data?.unmatched?.knot) {
                components.knot = {
                    text: data.unmatched.knot.text || 'Unknown knot',
                    status: 'Unmatched',
                    pattern: data.unmatched.knot.pattern
                };
            }

            return components;
        },
        determineStatus: (data: any) => {
            if (data?.match_type === 'filtered') return 'Filtered';

            const handleMatched = !!data?.matched?.handle;
            const handleUnmatched = !!data?.unmatched?.handle;
            const knotMatched = !!data?.matched?.knot;
            const knotUnmatched = !!data?.unmatched?.knot;

            // Handle cases where only one component exists
            if ((handleMatched || handleUnmatched) && !(knotMatched || knotUnmatched)) {
                return handleMatched ? 'Matched' : 'Unmatched';
            }
            if ((knotMatched || knotUnmatched) && !(handleMatched || handleUnmatched)) {
                return knotMatched ? 'Matched' : 'Unmatched';
            }

            // Both components exist
            if ((handleMatched || handleUnmatched) && (knotMatched || knotUnmatched)) {
                if (handleMatched && knotMatched) {
                    return 'Matched';
                }
                if (handleUnmatched && knotUnmatched) {
                    return 'Unmatched';
                }
                // Mixed status defaults to unmatched
                return 'Unmatched';
            }

            return 'Unmatched';
        }
    });
} 