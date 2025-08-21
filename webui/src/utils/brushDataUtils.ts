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
export function structureBrushDataForAPI(matched: BrushMatchedData): {
  field: 'brush' | 'handle' | 'knot';
  data: Record<string, unknown>;
} {
  // Check if this has top-level brand and model populated
  const hasTopLevelBrand = matched.brand && matched.brand !== null && matched.brand !== undefined;
  const hasTopLevelModel = matched.model && matched.model !== null && matched.model !== undefined;

  // Check if this has handle/knot components
  const hasHandle = matched.handle && typeof matched.handle === 'object' && matched.handle !== null;
  const hasKnot = matched.knot && typeof matched.knot === 'object' && matched.knot !== null;

  // Rule: If top-level brand AND model are populated, save under brush section
  if (hasTopLevelBrand && hasTopLevelModel) {
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
            source_text: matched.handle!.source_text || null,
          },
          knot: {
            brand: matched.knot!.brand,
            model: matched.knot!.model,
            fiber: matched.knot!.fiber || null,
            knot_size_mm: matched.knot!.knot_size_mm || null,
            source_text: matched.knot!.source_text || null,
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
          source_text: matched.handle!.source_text || null,
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
          source_text: matched.knot!.source_text || null,
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
