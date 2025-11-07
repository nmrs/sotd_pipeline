/**
 * Shared utilities for brush data structuring
 * Used by both MismatchAnalyzer and BrushValidation components
 * to ensure consistent data formatting for the CorrectMatchesManager
 */

export interface BrushMatchedData {
  brand?: string | null;
  model?: string | null;
  fiber?: string | null;
  knot_size_mm?: number | null;
  handle_maker?: string | null;
  handle?: {
    brand: string;
    model: string;
    source_text?: string;
  } | null;
  knot?: {
    brand: string;
    model: string;
    fiber?: string;
    knot_size_mm?: number;
    source_text?: string;
  } | null;
  [key: string]: unknown;
}

/**
 * Structures brush data for the CorrectMatchesManager API
 * Determines whether to send as brush, handle, or knot based on data structure
 *
 * @param matched - The matched brush data from the matcher
 * @returns Properly structured data for the API
 */
export function structureBrushDataForAPI(
  matched: BrushMatchedData,
  original?: string
): {
  field: 'brush' | 'handle' | 'knot';
  data: Record<string, unknown>;
} {
  // Check if this has top-level brand and model populated
  // Handle empty strings as falsy (empty string means not populated)
  const hasTopLevelBrand = matched.brand && matched.brand !== null && matched.brand !== undefined && matched.brand !== '';
  const hasTopLevelModel = matched.model && matched.model !== null && matched.model !== undefined && matched.model !== '';
  
  // Debug logging for troubleshooting
  if (original && original.toLowerCase().includes('rubberset') && original.toLowerCase().includes('400')) {
    console.log('🔍 DEBUG structureBrushDataForAPI for Rubberset 400:', {
      original,
      hasTopLevelBrand,
      hasTopLevelModel,
      brand: matched.brand,
      model: matched.model,
      matchedKeys: Object.keys(matched),
      hasHandle: matched.handle && typeof matched.handle === 'object',
      hasKnot: matched.knot && typeof matched.knot === 'object',
    });
  }

  // Check if this has handle/knot components
  const hasHandle = matched.handle && typeof matched.handle === 'object' && matched.handle !== null;
  const hasKnot = matched.knot && typeof matched.knot === 'object' && matched.knot !== null;

  // Rule: If top-level brand AND model are populated, save under brush section
  // Even if handle/knot nested structures exist, if we have top-level brand/model,
  // it's a complete brush and should be saved as such
  // IMPORTANT: Preserve handle/knot structures in the data so backend can see them
  // The backend will check for top-level brand/model FIRST before checking handle/knot
  if (hasTopLevelBrand && hasTopLevelModel) {
    // Extract fiber from knot section if not at root level (for known_brush strategy)
    const fiber = matched.fiber || (matched.knot && typeof matched.knot === 'object' ? matched.knot.fiber : null);
    // Extract knot_size_mm from knot section if not at root level
    const knot_size_mm = matched.knot_size_mm || (matched.knot && typeof matched.knot === 'object' ? matched.knot.knot_size_mm : null);
    
    // Build the data object, preserving handle/knot structures if they exist
    const data: Record<string, unknown> = {
      brand: matched.brand || null,
      model: matched.model || null,
      fiber: fiber || null,
      knot_size_mm: knot_size_mm || null,
      handle_maker: matched.handle_maker || null,
    };
    
    // Preserve handle/knot structures if they exist - backend needs to see them
    // to properly identify this as a complete brush (not a split brush)
    if (hasHandle) {
      data.handle = {
        brand: matched.handle!.brand,
        model: matched.handle!.model,
        source_text: matched.handle!.source_text || original || null,
      };
    }
    
    if (hasKnot) {
      data.knot = {
        brand: matched.knot!.brand,
        model: matched.knot!.model,
        fiber: matched.knot!.fiber || null,
        knot_size_mm: matched.knot!.knot_size_mm || null,
        source_text: matched.knot!.source_text || original || null,
      };
    }
    
    return {
      field: 'brush',
      data,
    };
  }

  // Rule: If top-level model is None/not populated, save under handle and/or knot sections
  if (hasHandle || hasKnot) {
    if (hasHandle && hasKnot) {
      // Both handle and knot exist - this is a composite brush
      // The CorrectMatchesManager will handle routing to both sections
      return {
        field: 'brush',
        data: {
          brand: matched.brand || null,
          model: matched.model || null,
          handle: {
            brand: matched.handle!.brand,
            model: matched.handle!.model,
            source_text: matched.handle!.source_text || original || null,
          },
          knot: {
            brand: matched.knot!.brand,
            model: matched.knot!.model,
            fiber: matched.knot!.fiber || null,
            knot_size_mm: matched.knot!.knot_size_mm || null,
            source_text: matched.knot!.source_text || original || null,
          },
        },
      };
    } else if (hasHandle) {
      // Only handle exists - save as handle
      return {
        field: 'handle',
        data: {
          brand: matched.handle!.brand,
          model: matched.handle!.model,
          source_text: matched.handle!.source_text || original || null,
        },
      };
    } else {
      // Only knot exists - save as knot
      return {
        field: 'knot',
        data: {
          brand: matched.knot!.brand,
          model: matched.knot!.model,
          fiber: matched.knot!.fiber || null,
          knot_size_mm: matched.knot!.knot_size_mm || null,
          source_text: matched.knot!.source_text || original || null,
        },
      };
    }
  } else {
    // Fallback: no handle/knot components, save as brush (though this shouldn't happen)
    return {
      field: 'brush',
      data: {
        brand: matched.brand || null,
        model: matched.model || null,
        fiber: matched.fiber || null,
        knot_size_mm: matched.knot_size_mm || null,
        handle_maker: matched.handle_maker || null,
      },
    };
  }
}

/**
 * Determines the appropriate field for saving brush data
 * Used by components to know which field to send to the API
 *
 * @param matched - The matched brush data
 * @returns The field name where this data should be saved
 */
export function getBrushFieldForSaving(matched: BrushMatchedData): 'brush' | 'handle' | 'knot' {
  const { field } = structureBrushDataForAPI(matched);
  return field;
}
