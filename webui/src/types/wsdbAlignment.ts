/** Shared types for WSDB Alignment Analyzer (page and result-expanded component). */

export interface FuzzyMatch {
  brand: string;
  name: string;
  confidence: number;
  brand_score: number;
  scent_score: number;
  source: string;
  matched_via?: 'canonical' | 'alias';
  scent_matched_via?: 'canonical' | 'alias';
  details: {
    slug?: string;
    scent_notes?: string[];
    collaborators?: string[];
    tags?: string[];
    category?: string;
    type?: string; // WSDB format: e.g. "Soap", "Cream"
    patterns?: string[];
  };
}

export interface AlignmentResult {
  source_brand: string;
  source_scent: string;
  matches?: FuzzyMatch[];
  expanded?: boolean;
  original_texts?: string[];
  match_types?: string[];
  count?: number;
  comment_ids?: string[];
}
