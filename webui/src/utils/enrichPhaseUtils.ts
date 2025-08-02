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
    // Check fiber changes (enriched data overrides matched)
    const matchedKnotFiber = matchedData?.knot?.fiber;
    const enrichedFiber = enrichedData?.fiber;

    // Only consider it a change if both values exist and are different
    if (matchedKnotFiber !== undefined && enrichedFiber !== undefined && matchedKnotFiber !== enrichedFiber) {
      return true;
    }

    // Check knot size changes
    const matchedKnotSize = matchedData?.knot?.knot_size_mm;
    const enrichedKnotSize = enrichedData?.knot_size_mm;

    // Consider it a change if:
    // 1. Both values exist and are different, OR
    // 2. One value exists and the other is null/undefined (indicating a change from no data to data or vice versa)
    if (matchedKnotSize !== undefined && enrichedKnotSize !== undefined && matchedKnotSize !== enrichedKnotSize) {
      return true;
    }
    if ((matchedKnotSize === null || matchedKnotSize === undefined) && enrichedKnotSize !== undefined && enrichedKnotSize !== null) {
      return true;
    }
    if ((enrichedKnotSize === null || enrichedKnotSize === undefined) && matchedKnotSize !== undefined && matchedKnotSize !== null) {
      return true;
    }

    // For brush enrichment, only fiber and knot_size_mm can change
    // Brand, model, handle_maker, etc. should remain the same from match phase
    // Don't check other fields as they shouldn't change during brush enrichment

    // No changes detected for fiber or knot size
    return false;
  } else {
    // For other fields, check top-level fields
    const fieldsToCheck = ['fiber', 'knot_size_mm', 'handle_maker', 'brand', 'model'];

    return fieldsToCheck.some(fieldName => {
      const original = matchedData[fieldName];
      const enriched = enrichedData[fieldName];
      // Only consider it a change if both values exist and are different
      return original !== undefined && enriched !== undefined && original !== enriched;
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
    // Check fiber changes
    const matchedKnotFiber = matchedData?.knot?.fiber;
    const enrichedFiber = enrichedData?.fiber;

    if (matchedKnotFiber !== undefined && enrichedFiber !== undefined && matchedKnotFiber !== enrichedFiber) {
      changes.push({
        field: 'fiber',
        originalValue: matchedKnotFiber,
        enrichedValue: enrichedFiber,
        displayName: 'Fiber'
      });
    }

    // Check knot size changes
    const matchedKnotSize = matchedData?.knot?.knot_size_mm;
    const enrichedKnotSize = enrichedData?.knot_size_mm;

    if (matchedKnotSize !== undefined && enrichedKnotSize !== undefined && matchedKnotSize !== enrichedKnotSize) {
      changes.push({
        field: 'knot_size_mm',
        originalValue: matchedKnotSize,
        enrichedValue: enrichedKnotSize,
        displayName: 'Knot Size (mm)'
      });
    }

    // Check null-to-value changes
    if ((matchedKnotSize === null || matchedKnotSize === undefined) && enrichedKnotSize !== undefined && enrichedKnotSize !== null) {
      changes.push({
        field: 'knot_size_mm',
        originalValue: matchedKnotSize,
        enrichedValue: enrichedKnotSize,
        displayName: 'Knot Size (mm)'
      });
    }

    if ((enrichedKnotSize === null || enrichedKnotSize === undefined) && matchedKnotSize !== undefined && matchedKnotSize !== null) {
      changes.push({
        field: 'knot_size_mm',
        originalValue: matchedKnotSize,
        enrichedValue: enrichedKnotSize,
        displayName: 'Knot Size (mm)'
      });
    }

    // Check null-to-value changes for fiber
    if ((matchedKnotFiber === null || matchedKnotFiber === undefined) && enrichedFiber !== undefined && enrichedFiber !== null) {
      changes.push({
        field: 'fiber',
        originalValue: matchedKnotFiber,
        enrichedValue: enrichedFiber,
        displayName: 'Fiber'
      });
    }

    if ((enrichedFiber === null || enrichedFiber === undefined) && matchedKnotFiber !== undefined && matchedKnotFiber !== null) {
      changes.push({
        field: 'fiber',
        originalValue: matchedKnotFiber,
        enrichedValue: enrichedFiber,
        displayName: 'Fiber'
      });
    }
  } else {
    // For other fields, check top-level fields
    const fieldsToCheck = ['fiber', 'knot_size_mm', 'handle_maker', 'brand', 'model'];

    fieldsToCheck.forEach(fieldName => {
      const original = matchedData[fieldName];
      const enriched = enrichedData[fieldName];
      
      if (original !== undefined && enriched !== undefined && original !== enriched) {
        changes.push({
          field: fieldName,
          originalValue: original,
          enrichedValue: enriched,
          displayName: fieldName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
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

  return changes.map(change => {
    const displayOriginal = change.originalValue ?? 'None';
    const displayEnriched = change.enrichedValue ?? 'None';
    return `${change.displayName}: ${displayOriginal} → ${displayEnriched}`;
  }).join('\n');
}; 