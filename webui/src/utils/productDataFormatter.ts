/**
 * Utility functions for formatting product data (matched and enriched) for display.
 * Extracted from MismatchAnalyzerDataTable.tsx for reuse across components.
 */

/**
 * Extract brush component pattern from matched data.
 */
export const getBrushComponentPattern = (
  matched: Record<string, unknown>,
  component: 'handle' | 'knot'
): string => {
  if (!matched || typeof matched !== 'object') return 'N/A';

  const componentData = matched[component] as Record<string, unknown>;
  if (!componentData || typeof componentData !== 'object') return 'N/A';

  return (componentData._pattern as string) || 'N/A';
};

/**
 * Format brush component data (handle or knot) for display.
 */
export const formatBrushComponent = (
  matched: Record<string, unknown>,
  component: 'handle' | 'knot'
): string => {
  if (!matched || typeof matched !== 'object') return 'N/A';

  const componentData = matched[component] as Record<string, unknown>;
  if (!componentData || typeof componentData !== 'object') return 'N/A';

  const parts = [];
  if (componentData.brand) parts.push(String(componentData.brand));
  if (componentData.model) parts.push(String(componentData.model));

  // Add fiber and size for knots
  if (component === 'knot') {
    if (componentData.fiber) parts.push(String(componentData.fiber));
    if (componentData.knot_size_mm) parts.push(`${componentData.knot_size_mm}mm`);
  }

  // If no brand/model/fiber/size, try to use source_text (for automated splits and known_split)
  if (parts.length === 0 && componentData.source_text) {
    return String(componentData.source_text);
  }

  return parts.length > 0 ? parts.join(' - ') : 'N/A';
};

/**
 * Format matched data for display based on field type.
 * @param matched - The matched data from the match phase
 * @param field - The field type (razor, blade, brush, soap)
 * @param enriched - Optional enriched data from the enrich phase
 */
export const formatMatchedData = (
  matched: unknown,
  field?: string,
  enriched?: unknown
): string => {
  if (!matched) return 'N/A';

  if (typeof matched === 'string') {
    return matched;
  }

  if (typeof matched === 'object' && matched !== null) {
    const matchedObj = matched as Record<string, unknown>;

    // Special handling for razor field - prefer enriched format when available
    if (field === 'razor') {
      const parts = [];
      if (matchedObj.brand) parts.push(String(matchedObj.brand));
      if (matchedObj.model) parts.push(String(matchedObj.model));
      
      // Use enriched format if available, otherwise fall back to matched format
      if (enriched && typeof enriched === 'object' && enriched !== null) {
        const enrichedObj = enriched as Record<string, unknown>;
        if (enrichedObj.format) {
          parts.push(String(enrichedObj.format));
          return parts.length > 0 ? parts.join(' - ') : JSON.stringify(matched);
        }
      }
      
      // Fall back to matched format if no enriched format
      if (matchedObj.format) parts.push(String(matchedObj.format));
      return parts.length > 0 ? parts.join(' - ') : JSON.stringify(matched);
    }

    // Special handling for brush field
    if (field === 'brush') {
      // Check if this is a complete brush (has top-level brand AND model)
      const hasTopLevelBrand =
        matchedObj.brand && matchedObj.brand !== null && matchedObj.brand !== undefined;
      const hasTopLevelModel =
        matchedObj.model && matchedObj.model !== null && matchedObj.model !== undefined;
      const hasHandle =
        matchedObj.handle && typeof matchedObj.handle === 'object' && matchedObj.handle !== null;
      const hasKnot =
        matchedObj.knot && typeof matchedObj.knot === 'object' && matchedObj.knot !== null;

      // Complete brush: must have BOTH top-level brand AND model
      if (hasTopLevelBrand && hasTopLevelModel) {
        const parts = [];
        if (matchedObj.brand) parts.push(String(matchedObj.brand));
        if (matchedObj.model) parts.push(String(matchedObj.model));
        if (matchedObj.fiber) parts.push(String(matchedObj.fiber));
        if (matchedObj.knot_size_mm) parts.push(`${matchedObj.knot_size_mm}mm`);
        // Only include handle_maker if it's different from the brand
        if (matchedObj.handle_maker && matchedObj.handle_maker !== matchedObj.brand) {
          parts.push(String(matchedObj.handle_maker));
        }

        return parts.length > 0 ? parts.join(' - ') : JSON.stringify(matched);
      } else if (hasHandle && hasKnot) {
        // Composite brush: has handle/knot components but missing either brand or model
        // This includes cases where there's a top-level brand but no model
        const handleText = formatBrushComponent(matchedObj, 'handle');
        const knotText = formatBrushComponent(matchedObj, 'knot');

        if (handleText !== 'N/A' || knotText !== 'N/A') {
          const parts = [];
          if (handleText !== 'N/A') parts.push(`Handle: ${handleText}`);
          if (knotText !== 'N/A') parts.push(`Knot: ${knotText}`);
          return parts.join('\n');
        }
      } else {
        // Fallback: show whatever data is available
        const parts = [];
        if (matchedObj.brand) parts.push(String(matchedObj.brand));
        if (matchedObj.model) parts.push(String(matchedObj.model));
        if (matchedObj.fiber) parts.push(String(matchedObj.fiber));
        if (matchedObj.knot_size_mm) parts.push(`${matchedObj.knot_size_mm}mm`);
        if (matchedObj.handle_maker) parts.push(String(matchedObj.handle_maker));

        return parts.length > 0 ? parts.join(' - ') : JSON.stringify(matched);
      }
    }

    // For other fields, use the original logic
    const parts = [];
    if (matchedObj.brand) parts.push(String(matchedObj.brand));
    if (matchedObj.model) parts.push(String(matchedObj.model));
    if (matchedObj.format) parts.push(String(matchedObj.format));
    if (matchedObj.maker) parts.push(String(matchedObj.maker));
    if (matchedObj.scent) parts.push(String(matchedObj.scent));

    return parts.length > 0 ? parts.join(' - ') : JSON.stringify(matched);
  }

  return String(matched);
};

/**
 * Format enriched data for display.
 * Similar to formatMatchedData but handles enriched-specific fields.
 */
export const formatEnrichedData = (enriched: unknown): string => {
  if (!enriched) return 'N/A';

  if (typeof enriched === 'string') {
    return enriched;
  }

  if (typeof enriched === 'object' && enriched !== null) {
    const enrichedObj = enriched as Record<string, unknown>;

    // Filter out internal metadata fields
    const filteredObj: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(enrichedObj)) {
      if (!key.startsWith('_')) {
        filteredObj[key] = value;
      }
    }

    // If no fields after filtering, return N/A
    if (Object.keys(filteredObj).length === 0) {
      return 'N/A';
    }

    // Format as key-value pairs for readability
    const parts: string[] = [];
    for (const [key, value] of Object.entries(filteredObj)) {
      if (value !== null && value !== undefined) {
        const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        parts.push(`${formattedKey}: ${String(value)}`);
      }
    }

    return parts.length > 0 ? parts.join(', ') : 'N/A';
  }

  return String(enriched);
};

