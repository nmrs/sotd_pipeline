/**
 * WSDB lookup utility with alias support.
 * 
 * Provides functions to lookup WSDB slugs for brand/scent combinations,
 * respecting aliases from pipeline soaps configuration.
 */

export interface WSDBSoap {
  brand: string;
  name: string;
  slug: string;
  scent_notes?: string[];
  collaborators?: string[];
  tags?: string[];
  category?: string;
}

export interface PipelineSoap {
  brand: string;
  aliases?: string[];
  scents: Array<{
    name: string;
    alias?: string;
    patterns: string[];
  }>;
}

/**
 * Remove accents from characters (e.g., 'Café' → 'Cafe').
 * 
 * Uses Unicode normalization to separate base characters from combining marks.
 * 
 * @param text - String to normalize
 * @returns String with accents removed
 */
function normalizeAccents(text: string): string {
  if (!text) {
    return text;
  }
  // Use Unicode normalization to decompose characters, then remove combining marks
  return text.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
}

/**
 * Normalize 'and' and '&' to a consistent form.
 * 
 * Converts both 'and' and '&' (with or without spaces) to 'and'.
 * 
 * @param text - String to normalize
 * @returns String with 'and' and '&' normalized to 'and'
 */
function normalizeAndAmpersand(text: string): string {
  if (!text) {
    return text;
  }
  // Replace '&' (with optional spaces) with 'and'
  let normalized = text.replace(/\s*&\s*/g, ' and ');
  // Normalize multiple spaces
  normalized = normalized.replace(/\s+/g, ' ');
  return normalized.trim();
}

/**
 * Apply all virtual pattern normalizations for matching.
 * 
 * This is the main normalization function that should be used for all
 * WSDB matching operations. It applies:
 * - Lowercase and trim
 * - Accent removal
 * - "and"/"&" normalization
 * 
 * @param text - String to normalize
 * @returns Fully normalized string for matching
 */
function normalizeForMatching(text: string): string {
  if (!text) {
    return text;
  }
  // Apply all normalizations
  let normalized = text.toLowerCase().trim();
  normalized = normalizeAccents(normalized);
  normalized = normalizeAndAmpersand(normalized);
  return normalized;
}

/**
 * Normalize a string for comparison (lowercase and trim).
 * 
 * @deprecated Use normalizeForMatching instead for WSDB matching
 * @param text - String to normalize
 * @returns Normalized string
 */
function normalizeString(text: string): string {
  return normalizeForMatching(text);
}

/**
 * Strip trailing 'soap' (case-insensitive) from text.
 * 
 * This is a virtual alias helper that computes a stripped version on-the-fly.
 * The result is NOT saved to soaps.yaml.
 * 
 * @param text - The string to process
 * @returns Stripped version if 'soap' found at end, null otherwise
 */
function stripTrailingSoap(text: string): string | null {
  if (!text) {
    return null;
  }
  const textLower = text.toLowerCase().trim();
  if (textLower.endsWith('soap')) {
    const stripped = text.slice(0, -4).trim();
    return stripped || null;
  }
  return null;
}

/**
 * Get WSDB slug for a brand/scent combination, respecting aliases.
 * 
 * Checks canonical brand/scent first, then tries all aliases from pipeline soaps.
 * 
 * @param brand - Brand name to lookup
 * @param scent - Scent name to lookup
 * @param wsdbSoaps - Array of WSDB soaps (already loaded)
 * @param pipelineSoaps - Array of pipeline soaps with aliases (already loaded)
 * @returns WSDB slug if found, null otherwise
 */
export function getWsdbSlug(
  brand: string,
  scent: string,
  wsdbSoaps: WSDBSoap[],
  pipelineSoaps: PipelineSoap[]
): string | null {
  if (!brand || !scent || wsdbSoaps.length === 0) {
    return null;
  }

  // Normalize input using full normalization (includes accents, and/&)
  const normalizedBrand = normalizeForMatching(brand);
  const normalizedScent = normalizeForMatching(scent);

  // Find brand entry in pipeline soaps for alias lookup
  const brandEntry = pipelineSoaps.find(p => normalizeForMatching(p.brand) === normalizedBrand);

  // Get all brand names to try: canonical + aliases + virtual alias (stripped "soap")
  const brandNamesToTry = [normalizedBrand];
  if (brandEntry?.aliases) {
    brandNamesToTry.push(...brandEntry.aliases.map(alias => normalizeForMatching(alias)));
  }
  // Add virtual alias: strip trailing "soap" if present
  const brandVirtualAlias = stripTrailingSoap(normalizedBrand);
  if (brandVirtualAlias) {
    const brandVirtualAliasNormalized = normalizeForMatching(brandVirtualAlias);
    if (!brandNamesToTry.includes(brandVirtualAliasNormalized)) {
      brandNamesToTry.push(brandVirtualAliasNormalized);
    }
  }

  // Get scent names to try: canonical + alias + virtual alias (stripped "soap")
  const scentNamesToTry = [normalizedScent];
  if (brandEntry) {
    const scentInfo = brandEntry.scents.find(s => normalizeForMatching(s.name) === normalizedScent);
    if (scentInfo?.alias) {
      scentNamesToTry.push(normalizeForMatching(scentInfo.alias));
    }
  }
  // Add virtual alias: strip trailing "soap" if present
  const scentVirtualAlias = stripTrailingSoap(normalizedScent);
  if (scentVirtualAlias) {
    const scentVirtualAliasNormalized = normalizeForMatching(scentVirtualAlias);
    if (!scentNamesToTry.includes(scentVirtualAliasNormalized)) {
      scentNamesToTry.push(scentVirtualAliasNormalized);
    }
  }

  // Try all combinations: brand names × scent names
  for (const brandName of brandNamesToTry) {
    for (const scentName of scentNamesToTry) {
      const match = wsdbSoaps.find(soap => {
        // Normalize WSDB entries using full normalization
        const soapBrand = normalizeForMatching(soap.brand || '');
        const soapName = normalizeForMatching(soap.name || '');
        
        // Also try matching against WSDB entries with stripped "soap" (virtual alias)
        const soapBrandVirtual = stripTrailingSoap(soapBrand);
        const soapBrandVirtualNormalized = soapBrandVirtual ? normalizeForMatching(soapBrandVirtual) : null;
        const soapNameVirtual = stripTrailingSoap(soapName);
        const soapNameVirtualNormalized = soapNameVirtual ? normalizeForMatching(soapNameVirtual) : null;
        
        // Match against original or virtual alias versions
        const brandMatches = (soapBrand === brandName || 
                            (soapBrandVirtualNormalized && soapBrandVirtualNormalized === brandName));
        const nameMatches = (soapName === scentName || 
                           (soapNameVirtualNormalized && soapNameVirtualNormalized === scentName));
        
        return brandMatches && nameMatches;
      });

      if (match) {
        return match.slug;
      }
    }
  }

  return null;
}

