/**
 * Brush data transformation utilities
 *
 * This module converts brush matcher output from the backend to the format
 * required by the BrushTable component. It uses the generic data transformer
 * pattern for consistency and maintainability.
 *
 * @module BrushDataTransformer
 */

import { createBrushTransformer } from './genericDataTransformer';

/**
 * Brush matcher output structure from the backend API
 *
 * This interface represents the raw data structure returned by the brush matcher
 * in the pipeline. It includes both matched and unmatched components with
 * detailed information about the matching process.
 */
export interface BrushMatcherOutput {
  item: string;
  count: number;
  comment_ids: string[];
  examples: string[];
  match_type?: string;
  matched?: {
    brand?: string;
    model?: string;
    handle?: {
      brand?: string;
      model?: string;
      source_text?: string;
      _matched_by?: string;
      _pattern?: string;
    };
    knot?: {
      brand?: string;
      model?: string;
      fiber?: string;
      knot_size_mm?: number;
      source_text?: string;
      _matched_by?: string;
      _pattern?: string;
    };
  };
  unmatched?: {
    handle?: {
      pattern?: string;
      text?: string;
    };
    knot?: {
      pattern?: string;
      text?: string;
    };
  };
}

/**
 * Component data structure for brush components (handle/knot)
 *
 * Represents the transformed data for individual brush components
 * with their status and pattern information.
 */
export interface ComponentData {
  text: string;
  status: 'Matched' | 'Unmatched' | 'Filtered';
  pattern?: string;
}

/**
 * Main brush data structure for BrushTable component
 *
 * This is the final transformed structure that the BrushTable component
 * expects. It includes both the main brush information and component details.
 */
export interface BrushData {
  main: {
    text: string;
    count: number;
    comment_ids: string[];
    examples: string[];
    status: 'Matched' | 'Unmatched' | 'Filtered';
  };
  components: {
    handle?: ComponentData;
    knot?: ComponentData;
  };
}

/**
 * Creates the brush transformer using the generic pattern
 *
 * This transformer is configured specifically for brush data and handles
 * the complex component structure of brushes (handle and knot components).
 */
const brushTransformer = createBrushTransformer();

/**
 * Transforms brush matcher output to BrushTable format
 *
 * This function converts the raw brush matcher output from the backend
 * into the structured format required by the BrushTable component.
 * It handles both matched and unmatched brushes with proper component
 * extraction and status determination.
 *
 * @param matcherOutput - The brush matcher output from the backend
 * @returns BrushData object suitable for BrushTable component
 *
 * @example
 * ```typescript
 * const brushData = transformBrushData({
 *   item: 'Test Brush',
 *   count: 5,
 *   comment_ids: ['123', '456'],
 *   examples: ['example1.json', 'example2.json'],
 *   matched: {
 *     handle: { brand: 'Test', model: 'Handle', source_text: 'Test Handle' },
 *     knot: { brand: 'Test', model: 'Knot', source_text: 'Test Knot' }
 *   }
 * });
 * ```
 */
export function transformBrushData(
  matcherOutput: BrushMatcherOutput | null | undefined
): BrushData {
  const result = brushTransformer.transform(matcherOutput);
  return result as BrushData; // Type assertion since we know the structure matches
}

/**
 * Transforms an array of brush matcher outputs to BrushData array
 *
 * This function processes multiple brush matcher outputs efficiently
 * using the generic transformer pattern. It's useful for bulk processing
 * of brush data from the backend.
 *
 * @param matcherOutputs - Array of brush matcher outputs
 * @returns Array of BrushData objects
 *
 * @example
 * ```typescript
 * const brushDataArray = transformBrushDataArray([
 *   { item: 'Brush 1', count: 3, comment_ids: ['123'], examples: ['ex1.json'] },
 *   { item: 'Brush 2', count: 2, comment_ids: ['456'], examples: ['ex2.json'] }
 * ]);
 * ```
 */
export function transformBrushDataArray(matcherOutputs: BrushMatcherOutput[]): BrushData[] {
  const results = brushTransformer.transformArray(matcherOutputs);
  return results as BrushData[]; // Type assertion since we know the structure matches
}
