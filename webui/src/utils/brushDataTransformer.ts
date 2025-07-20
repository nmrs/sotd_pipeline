/**
 * Brush data transformation utilities
 * Converts brush matcher output to BrushTable format
 */

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

/**
 * Determines the status of a component based on match data
 */
function determineComponentStatus(
    matched: any,
    unmatched: any,
    matchType?: string
): 'Matched' | 'Unmatched' | 'Filtered' {
    if (matchType === 'filtered') {
        return 'Filtered';
    }

    if (matched) {
        return 'Matched';
    }

    if (unmatched) {
        return 'Unmatched';
    }

    return 'Unmatched';
}

/**
 * Determines the overall brush status based on component statuses
 */
function determineBrushStatus(
    handleStatus: 'Matched' | 'Unmatched' | 'Filtered' | undefined,
    knotStatus: 'Matched' | 'Unmatched' | 'Filtered' | undefined,
    matchType?: string
): 'Matched' | 'Unmatched' | 'Filtered' {
    if (matchType === 'filtered') {
        return 'Filtered';
    }

    // If any component is filtered, overall status is filtered
    if (handleStatus === 'Filtered' || knotStatus === 'Filtered') {
        return 'Filtered';
    }

    // Handle cases where only one component exists
    if (handleStatus && !knotStatus) {
        // Only handle component exists
        return handleStatus;
    }

    if (knotStatus && !handleStatus) {
        // Only knot component exists
        return knotStatus;
    }

    // Both components exist
    if (handleStatus && knotStatus) {
        // If both components are matched, overall status is matched
        if (handleStatus === 'Matched' && knotStatus === 'Matched') {
            return 'Matched';
        }

        // If both components are unmatched, overall status is unmatched
        if (handleStatus === 'Unmatched' && knotStatus === 'Unmatched') {
            return 'Unmatched';
        }

        // Mixed status (one matched, one unmatched) defaults to unmatched
        return 'Unmatched';
    }

    // No components exist (shouldn't happen with valid data)
    return 'Unmatched';
}

/**
 * Extracts handle component data from brush matcher output
 */
function extractHandleComponent(matcherOutput: BrushMatcherOutput): ComponentData | undefined {
    const { matched, unmatched } = matcherOutput;

    if (!matched?.handle && !unmatched?.handle) {
        return undefined;
    }

    const status = determineComponentStatus(matched?.handle, unmatched?.handle, matcherOutput.match_type);

    if (matched?.handle) {
        // Extract text from matched handle using source_text or brand/model combination
        const { brand, model, source_text } = matched.handle;
        const text = source_text || (brand && model ? `${brand} ${model}` : brand || model || 'Unknown handle');

        return {
            text,
            status
        };
    }

    if (unmatched?.handle) {
        return {
            text: unmatched.handle.text || 'Unknown handle',
            status,
            pattern: unmatched.handle.pattern
        };
    }

    return undefined;
}

/**
 * Extracts knot component data from brush matcher output
 */
function extractKnotComponent(matcherOutput: BrushMatcherOutput): ComponentData | undefined {
    const { matched, unmatched } = matcherOutput;

    if (!matched?.knot && !unmatched?.knot) {
        return undefined;
    }

    const status = determineComponentStatus(matched?.knot, unmatched?.knot, matcherOutput.match_type);

    if (matched?.knot) {
        // Extract text from matched knot using source_text or brand/model combination
        const { brand, model, source_text } = matched.knot;
        const text = source_text || (brand && model ? `${brand} ${model}` : brand || model || 'Unknown knot');

        return {
            text,
            status
        };
    }

    if (unmatched?.knot) {
        return {
            text: unmatched.knot.text || 'Unknown knot',
            status,
            pattern: unmatched.knot.pattern
        };
    }

    return undefined;
}

/**
 * Validates required fields in brush matcher output
 */
function validateMatcherOutput(matcherOutput: BrushMatcherOutput): void {
    // Handle null/undefined input gracefully
    if (!matcherOutput) {
        throw new Error('Invalid matcher output: null or undefined');
    }

    if (!matcherOutput.item || typeof matcherOutput.item !== 'string' || matcherOutput.item.trim() === '') {
        throw new Error('Invalid item value');
    }

    if (typeof matcherOutput.count !== 'number' || matcherOutput.count < 0) {
        throw new Error('Missing required field: count');
    }

    if (!Array.isArray(matcherOutput.comment_ids)) {
        throw new Error('Missing required field: comment_ids');
    }

    if (!Array.isArray(matcherOutput.examples)) {
        throw new Error('Missing required field: examples');
    }
}

/**
 * Transforms brush matcher output to BrushTable format
 * 
 * @param matcherOutput - The brush matcher output from the backend
 * @returns BrushData object suitable for BrushTable component
 * @throws Error if required fields are missing or invalid
 */
export function transformBrushData(matcherOutput: BrushMatcherOutput | null | undefined): BrushData {
    // Handle null/undefined input gracefully
    if (!matcherOutput) {
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
        // Validate input
        validateMatcherOutput(matcherOutput);

        // Extract components
        const handleComponent = extractHandleComponent(matcherOutput);
        const knotComponent = extractKnotComponent(matcherOutput);

        // Determine overall status
        const overallStatus = determineBrushStatus(
            handleComponent?.status,
            knotComponent?.status,
            matcherOutput.match_type
        );

        // Build components object
        const components: BrushData['components'] = {};
        if (handleComponent) {
            components.handle = handleComponent;
        }
        if (knotComponent) {
            components.knot = knotComponent;
        }

        return {
            main: {
                text: matcherOutput.item,
                count: matcherOutput.count,
                comment_ids: matcherOutput.comment_ids,
                examples: matcherOutput.examples,
                status: overallStatus
            },
            components
        };
    } catch (error) {
        // Return default structure on validation errors
        return {
            main: {
                text: matcherOutput.item || '',
                count: matcherOutput.count || 0,
                comment_ids: matcherOutput.comment_ids || [],
                examples: matcherOutput.examples || [],
                status: 'Unmatched'
            },
            components: {}
        };
    }
}

/**
 * Transforms an array of brush matcher outputs to BrushData array
 * 
 * @param matcherOutputs - Array of brush matcher outputs
 * @returns Array of BrushData objects
 */
export function transformBrushDataArray(matcherOutputs: BrushMatcherOutput[]): BrushData[] {
    return matcherOutputs.map(output => transformBrushData(output));
} 