/**
 * Generic data transformation utilities
 *
 * This module provides a reusable pattern for transforming different product types
 * in the SOTD Pipeline WebUI. It includes generic transformers that can be configured
 * for different product types (razor, blade, brush, soap) with consistent interfaces.
 *
 * @module GenericDataTransformer
 */

/**
 * Supported product types for data transformation
 */
export type ProductType = 'razor' | 'blade' | 'brush' | 'soap';

/**
 * Main data structure for transformed product information
 */
export interface MainData {
  text: string;
  count: number;
  comment_ids: string[];
  examples: string[];
  status: 'Matched' | 'Unmatched' | 'Filtered';
}

/**
 * Complete product data structure with main data and optional components
 */
export interface ProductData {
  main: MainData;
  components?: Record<string, any>;
}

/**
 * Configuration for creating a generic data transformer
 *
 * @template T - The type of input data to transform
 */
export interface TransformerConfig<T = any> {
  productType: ProductType;
  extractMainData: (data: T) => MainData;
  extractComponents: (data: T) => Record<string, any>;
  determineStatus: (data: T) => 'Matched' | 'Unmatched' | 'Filtered';
}

/**
 * Generic data transformer interface
 *
 * @template T - The type of input data to transform
 */
export interface DataTransformer<T = any> {
  transform: (data: T | null | undefined) => ProductData;
  transformArray: (data: T[]) => ProductData[];
}

/**
 * Creates a generic data transformer based on configuration
 *
 * This function creates a reusable transformer that can handle different product types
 * with consistent interfaces. It provides error handling and graceful degradation
 * for malformed data.
 *
 * @param config - Configuration object defining how to transform the data
 * @returns A transformer object with transform and transformArray methods
 *
 * @example
 * ```typescript
 * const razorTransformer = createGenericTransformer({
 *   productType: 'razor',
 *   extractMainData: (data) => ({
 *     text: data.item,
 *     count: data.count,
 *     comment_ids: data.comment_ids,
 *     examples: data.examples,
 *     status: 'Unmatched'
 *   }),
 *   extractComponents: (data) => ({}),
 *   determineStatus: (data) => 'Unmatched'
 * });
 * ```
 */
export function createGenericTransformer<T = any>(
  config: TransformerConfig<T>
): DataTransformer<T> {
  const { extractMainData, extractComponents, determineStatus } = config;

  /**
   * Transforms a single data item
   *
   * @param data - Input data to transform
   * @returns Transformed product data with consistent structure
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
          status: 'Unmatched',
        },
        components: {},
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
          status: overallStatus,
        },
        components: Object.keys(components).length > 0 ? components : undefined,
      };
    } catch (error) {
      // Return default structure on validation errors
      return {
        main: {
          text: (data as any)?.item || '',
          count: (data as any)?.count || 0,
          comment_ids: (data as any)?.comment_ids || [],
          examples: (data as any)?.examples || [],
          status: 'Unmatched',
        },
        components: {},
      };
    }
  }

  /**
   * Transforms an array of data items
   *
   * @param data - Array of input data to transform
   * @returns Array of transformed product data
   */
  function transformArray(data: T[]): ProductData[] {
    return data.map(item => transform(item));
  }

  return {
    transform,
    transformArray,
  };
}

/**
 * Creates a simple transformer for basic product types
 *
 * This function creates a basic transformer that doesn't extract components.
 * It's useful for simple product types like razors and blades that don't have
 * complex component structures.
 *
 * @param productType - The type of product to transform
 * @returns A simple transformer for the specified product type
 *
 * @example
 * ```typescript
 * const razorTransformer = createSimpleTransformer('razor');
 * const bladeTransformer = createSimpleTransformer('blade');
 * ```
 */
export function createSimpleTransformer(productType: ProductType): DataTransformer<any> {
  return createGenericTransformer({
    productType,
    extractMainData: (data: any) => ({
      text: data.item || '',
      count: data.count || 0,
      comment_ids: data.comment_ids || [],
      examples: data.examples || [],
      status: 'Unmatched',
    }),
    extractComponents: () => ({}),
    determineStatus: () => 'Unmatched',
  });
}

/**
 * Creates a specialized transformer for brush data
 *
 * This function creates a brush-specific transformer that handles the complex
 * component structure of brushes (handle and knot components). It extracts
 * both main brush data and individual component information.
 *
 * @returns A specialized transformer for brush data
 *
 * @example
 * ```typescript
 * const brushTransformer = createBrushTransformer();
 * const transformedBrush = brushTransformer.transform(brushData);
 * ```
 */
export function createBrushTransformer(): DataTransformer<any> {
  return createGenericTransformer({
    productType: 'brush',
    extractMainData: (data: any) => ({
      text: data.item || '',
      count: data.count || 0,
      comment_ids: data.comment_ids || [],
      examples: data.examples || [],
      status: 'Unmatched', // Will be overridden by determineStatus
    }),
    extractComponents: (data: any) => {
      const components: Record<string, any> = {};

      // Extract handle component from matched data
      if (data.matched?.handle) {
        components.handle = {
          text:
            data.matched.handle.source_text ||
            `${data.matched.handle.brand} ${data.matched.handle.model}`,
          status: 'Matched',
          pattern: data.matched.handle._pattern || 'exact',
        };
      } else if (data.unmatched?.handle) {
        components.handle = {
          text: data.unmatched.handle.text || '',
          status: 'Unmatched',
          pattern: data.unmatched.handle.pattern || '',
        };
      }

      // Extract knot component from matched data
      if (data.matched?.knot) {
        components.knot = {
          text:
            data.matched.knot.source_text ||
            `${data.matched.knot.brand} ${data.matched.knot.model}`,
          status: 'Matched',
          pattern: data.matched.knot._pattern || 'exact',
        };
      } else if (data.unmatched?.knot) {
        components.knot = {
          text: data.unmatched.knot.text || '',
          status: 'Unmatched',
          pattern: data.unmatched.knot.pattern || '',
        };
      }

      return components;
    },
    determineStatus: (data: any) => {
      // Determine overall status based on component statuses
      const handleStatus = data.matched?.handle
        ? 'Matched'
        : data.unmatched?.handle
          ? 'Unmatched'
          : undefined;
      const knotStatus = data.matched?.knot
        ? 'Matched'
        : data.unmatched?.knot
          ? 'Unmatched'
          : undefined;

      // If any component is matched, overall status is matched
      if (handleStatus === 'Matched' || knotStatus === 'Matched') {
        return 'Matched';
      }

      // Default to unmatched
      return 'Unmatched';
    },
  });
}
