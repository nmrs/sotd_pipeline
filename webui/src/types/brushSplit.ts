export interface BrushSplitOccurrence {
  file: string;
  comment_ids: string[];
}

export interface BrushSplit {
  original: string;
  handle: string | null;
  knot: string;
  validated: boolean;
  corrected: boolean;
  validated_at: string | null; // ISO timestamp
  system_handle?: string | null; // Only if corrected=true
  system_knot?: string; // Only if corrected=true
  system_confidence?: 'high' | 'medium' | 'low'; // Only if corrected=true
  system_reasoning?: string; // Only if corrected=true
  occurrences: BrushSplitOccurrence[];
}

export interface BrushSplitValidationStatus {
  validated: boolean;
  corrected: boolean;
  validated_at: string | null;
}

export interface BrushSplitStatistics {
  total: number;
  validated: number;
  corrected: number;
  validation_percentage: number;
  correction_percentage: number;
  split_types: {
    delimiter: number;
    fiber_hint: number;
    brand_context: number;
    no_split: number;
  };
}

export interface BrushSplitLoadResponse {
  brush_splits: BrushSplit[];
  statistics: BrushSplitStatistics;
}

export interface BrushSplitSaveRequest {
  brush_splits: BrushSplit[];
}

export interface BrushSplitSaveResponse {
  success: boolean;
  message: string;
  saved_count: number;
}
