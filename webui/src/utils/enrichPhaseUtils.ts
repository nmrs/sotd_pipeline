/**
 * Shared utility functions for enrich phase change detection
 */

export interface EnrichPhaseChange {
  field: string;
  originalValue: any;
  enrichedValue: any;
  displayName: string;
}

/**
 * Check if there are enrich-phase changes between matched and enriched data
 */
export const hasEnrichPhaseChanges = (
  matchedData: Record<string, any>,
  enrichedData: Record<string, any>,
  field: string
): boolean => {
  if (!matchedData || !enrichedData) return false;

  // For brush field, check the enriched data against matched data
  if (field === 'brush') {
    // The enrich phase only adds fiber and knot_size_mm at the top level
    // We need to compare the matched brush structure with the enriched data

    const matchedBrush = matchedData;
    const enrichedBrush = enrichedData;

    // Check fiber changes
    const matchedFiber = matchedBrush?.knot?.fiber;
    const enrichedFiber = enrichedBrush?.fiber;

    if (enrichedFiber !== undefined && enrichedFiber !== matchedFiber) {
      return true;
    }

    // Check knot size changes
    const matchedKnotSize = matchedBrush?.knot?.knot_size_mm;
    const enrichedKnotSize = enrichedBrush?.knot_size_mm;

    if (enrichedKnotSize !== undefined && enrichedKnotSize !== matchedKnotSize) {
      return true;
    }

    // No changes detected
    return false;
  } else {
    // For other fields, check top-level fields
    const fieldsToCheck = ['fiber', 'knot_size_mm', 'handle_maker', 'brand', 'model'];

    return fieldsToCheck.some(fieldName => {
      const original = matchedData[fieldName];
      const enriched = enrichedData[fieldName];
      // Only consider it a change if the enriched value exists and is different
      return enriched !== undefined && enriched !== original;
    });
  }
};

/**
 * Get detailed enrich phase changes for display in modal
 */
export const getEnrichPhaseChanges = (
  matchedData: Record<string, any>,
  enrichedData: Record<string, any>,
  field: string
): EnrichPhaseChange[] => {
  const changes: EnrichPhaseChange[] = [];

  if (!matchedData || !enrichedData) return changes;

  // For brush field, check the enriched data against matched data
  if (field === 'brush') {
    const matchedBrush = matchedData;
    const enrichedBrush = enrichedData;

    // Check fiber changes
    const matchedFiber = matchedBrush?.knot?.fiber;
    const enrichedFiber = enrichedBrush?.fiber;

    if (enrichedFiber !== undefined && enrichedFiber !== matchedFiber) {
      changes.push({
        field: 'fiber',
        originalValue: matchedFiber,
        enrichedValue: enrichedFiber,
        displayName: 'Fiber',
      });
    }

    // Check knot size changes
    const matchedKnotSize = matchedBrush?.knot?.knot_size_mm;
    const enrichedKnotSize = enrichedBrush?.knot_size_mm;

    if (enrichedKnotSize !== undefined && enrichedKnotSize !== matchedKnotSize) {
      changes.push({
        field: 'knot_size_mm',
        originalValue: matchedKnotSize,
        enrichedValue: enrichedKnotSize,
        displayName: 'Knot Size (mm)',
      });
    }
  } else {
    // For other fields, check top-level fields
    const fieldsToCheck = ['fiber', 'knot_size_mm', 'handle_maker', 'brand', 'model'];

    fieldsToCheck.forEach(fieldName => {
      const original = matchedData[fieldName];
      const enriched = enrichedData[fieldName];

      if (enriched !== undefined && enriched !== original) {
        changes.push({
          field: fieldName,
          originalValue: original,
          enrichedValue: enriched,
          displayName: fieldName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        });
      }
    });
  }

  return changes;
};

/**
 * Format enrich phase changes for display
 */
export const formatEnrichPhaseChanges = (
  matchedData: Record<string, any>,
  enrichedData: Record<string, any>,
  field: string
): string => {
  const changes = getEnrichPhaseChanges(matchedData, enrichedData, field);

  if (changes.length === 0) {
    return 'No changes detected';
  }

  return changes
    .map(change => {
      const displayOriginal = change.originalValue ?? 'None';
      const displayEnriched = change.enrichedValue ?? 'None';
      return `${change.displayName}: ${displayOriginal} → ${displayEnriched}`;
    })
    .join('\n');
};
