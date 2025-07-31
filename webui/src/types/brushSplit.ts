export interface BrushSplitOccurrence {
  file: string;
  comment_ids: string[];
}

export interface BrushSplit {
  original: string;
  handle: string | null;
  knot: string | null;
  match_type?: string | null;
  corrected: boolean;
  validated_at: string | null;
  system_handle?: string | null;
  system_knot?: string | null;
  system_confidence?: string | null;
  system_reasoning?: string | null;
  should_not_split: boolean;
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
