/**
 * Brush data transformation utilities
 * Converts brush matcher output to BrushTable format
 * 
 * This module now uses the generic data transformer pattern
 */

import { createBrushTransformer, ProductData } from './genericDataTransformer';

// Brush matcher output structure from backend
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

// Component data structure for brush components
export interface ComponentData {
    text: string;
    status: 'Matched' | 'Unmatched' | 'Filtered';
    pattern?: string;
}

// Main brush data structure for BrushTable
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

// Create the brush transformer using the generic pattern
const brushTransformer = createBrushTransformer();

/**
 * Transforms brush matcher output to BrushTable format
 * 
 * @param matcherOutput - The brush matcher output from the backend
 * @returns BrushData object suitable for BrushTable component
 */
export function transformBrushData(matcherOutput: BrushMatcherOutput | null | undefined): BrushData {
    const result = brushTransformer.transform(matcherOutput);
    return result as BrushData; // Type assertion since we know the structure matches
}

/**
 * Transforms an array of brush matcher outputs to BrushData array
 * 
 * @param matcherOutputs - Array of brush matcher outputs
 * @returns Array of BrushData objects
 */
export function transformBrushDataArray(matcherOutputs: BrushMatcherOutput[]): BrushData[] {
    const results = brushTransformer.transformArray(matcherOutputs);
    return results as BrushData[]; // Type assertion since we know the structure matches
} 