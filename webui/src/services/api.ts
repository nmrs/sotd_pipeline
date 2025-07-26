import axios from 'axios';
import { BrushSplit } from '@/types/brushSplit';

// Use different base URL for tests vs development
const API_BASE_URL =
  process.env.NODE_ENV === 'test'
    ? 'http://localhost:8000/api' // Direct connection for tests
    : '/api'; // Proxy for development

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    Pragma: 'no-cache',
    Expires: '0',
  },
});

// Add cache-busting interceptor to all requests
api.interceptors.request.use(config => {
  // Add timestamp to prevent caching
  const separator = config.url?.includes('?') ? '&' : '?';
  config.url = `${config.url}${separator}_t=${Date.now()}`;
  return config;
});

// Health check
export const checkHealth = async (): Promise<boolean> => {
  try {
    const response = await api.get('/health');
    return response.status === 200;
  } catch (error) {
    console.error('Health check failed:', error);
    return false;
  }
};

// File system operations
export interface MonthData {
  month: string;
  total_shaves: number;
  unique_shavers: number;
  included_months: string[];
  missing_months: string[];
}

export const getAvailableMonths = async (): Promise<string[]> => {
  try {
    const response = await api.get('/files/available-months');
    return response.data.months;
  } catch (error) {
    console.error('Failed to fetch available months:', error);
    throw error;
  }
};

export const getMonthData = async (month: string): Promise<MonthData> => {
  try {
    const response = await api.get(`/files/month/${month}`);
    return response.data;
  } catch (error) {
    console.error(`Failed to fetch data for month ${month}:`, error);
    throw error;
  }
};

// Catalog operations
export interface CatalogInfo {
  name: string;
  path: string;
  size: number;
  last_modified: string;
}

export const getCatalogs = async (): Promise<CatalogInfo[]> => {
  try {
    const response = await api.get('/catalogs/');
    return response.data.catalogs;
  } catch (error) {
    console.error('Failed to fetch catalogs:', error);
    throw error;
  }
};

export const getCatalogContent = async (catalogName: string): Promise<Record<string, unknown>> => {
  try {
    const response = await api.get(`/catalogs/${catalogName}`);
    return response.data;
  } catch (error) {
    console.error(`Failed to fetch catalog ${catalogName}:`, error);
    throw error;
  }
};

// Comment operations
export interface CommentDetail {
  id: string;
  author: string;
  body: string;
  created_utc: string;
  thread_id: string;
  thread_title: string;
  url: string;
}

export const getCommentDetail = async (
  commentId: string,
  months: string[]
): Promise<CommentDetail> => {
  try {
    const monthsParam = months.join(',');
    const response = await api.get(`/analyze/comment/${commentId}?months=${monthsParam}`);
    return response.data;
  } catch (error) {
    console.error(`Failed to fetch comment ${commentId}:`, error);
    throw error;
  }
};

// Analysis operations
export interface UnmatchedAnalysisRequest {
  field: string;
  months: string[];
  limit?: number;
}

export interface UnmatchedItem {
  item: string;
  count: number;
  examples: string[];
  comment_ids: string[];
  // Optional fields for brush matching data
  match_type?: string;
  matched?: Record<string, unknown>;
  unmatched?: Record<string, unknown>;
}

export interface UnmatchedAnalysisResult {
  field: string;
  months: string[];
  total_unmatched: number;
  unmatched_items: UnmatchedItem[];
  processing_time: number;
  partial_results?: boolean;
  error?: string;
  missing_data?: boolean;
}

export const analyzeUnmatched = async (
  request: UnmatchedAnalysisRequest
): Promise<UnmatchedAnalysisResult> => {
  try {
    const response = await api.post('/analyze/unmatched', request);
    return response.data;
  } catch (error) {
    console.error('Failed to analyze unmatched items:', error);
    throw error;
  }
};

// Mismatch analyzer types and functions
export interface MismatchAnalysisRequest {
  field: string;
  month: string;
  threshold?: number;
}

export interface MismatchItem {
  original: string;
  matched: Record<string, unknown>;
  pattern: string;
  match_type: string;
  confidence?: number;
  mismatch_type?: string;
  reason?: string;
  count: number;
  examples: string[];
  comment_ids: string[];
}

export interface MismatchAnalysisResult {
  field: string;
  month: string;
  total_matches: number;
  total_mismatches: number;
  mismatch_items: MismatchItem[];
  processing_time: number;
  partial_results?: boolean;
  error?: string;
}

export const analyzeMismatch = async (
  request: MismatchAnalysisRequest
): Promise<MismatchAnalysisResult> => {
  try {
    const response = await api.post('/analyze/mismatch', request);
    return response.data;
  } catch (error) {
    console.error('Failed to analyze mismatches:', error);
    throw error;
  }
};

// Match phase operations
export interface MatchPhaseRequest {
  months: string[];
  force: boolean;
}

export interface MatchPhaseResult {
  months: string[];
  force: boolean;
  success: boolean;
  message: string;
  error_details?: string;
  processing_time: number;
}

export const runMatchPhase = async (request: MatchPhaseRequest): Promise<MatchPhaseResult> => {
  try {
    const response = await api.post('/analyze/match-phase', request);
    return response.data;
  } catch (error) {
    console.error('Failed to run match phase:', error);
    throw error;
  }
};

// Brush split operations
export interface LoadBrushSplitsResponse {
  brush_splits: BrushSplit[];
  statistics: Record<string, unknown>;
  processing_info?: Record<string, unknown>;
  errors?: Array<Record<string, unknown>>;
}

export interface SaveBrushSplitRequest {
  original: string;
  handle: string | null;
  knot: string;
  validated_at?: string;
  should_not_split?: boolean;
}

export interface SaveBrushSplitResponse {
  success: boolean;
  message: string;
  corrected?: boolean;
  system_handle?: string | null;
  system_knot?: string | null;
  system_confidence?: string | null;
  system_reasoning?: string | null;
}

export interface SaveBrushSplitsRequest {
  brush_splits: BrushSplit[];
}

export interface SaveBrushSplitsResponse {
  success: boolean;
  message: string;
  saved_count: number;
}

export const loadBrushSplits = async (
  months: string[],
  unmatchedOnly: boolean = true
): Promise<LoadBrushSplitsResponse> => {
  try {
    const queryParams = months.map(month => `months=${encodeURIComponent(month)}`).join('&');
    const unmatchedParam = `unmatched_only=${unmatchedOnly}`;
    const response = await api.get(`/brush-splits/load?${queryParams}&${unmatchedParam}`);
    return response.data;
  } catch (error) {
    console.error('Failed to load brush splits:', error);
    throw error;
  }
};

export const saveBrushSplit = async (
  brushSplit: SaveBrushSplitRequest
): Promise<SaveBrushSplitResponse> => {
  try {
    const response = await api.post('/brush-splits/save-split', {
      ...brushSplit,
      validated_at: brushSplit.validated_at || new Date().toISOString(),
    });
    return response.data;
  } catch (error) {
    console.error('Failed to save brush split:', error);
    throw error;
  }
};

export const saveBrushSplits = async (
  brushSplits: BrushSplit[]
): Promise<SaveBrushSplitsResponse> => {
  try {
    // Convert BrushSplit objects to the format expected by the API
    const formattedSplits = brushSplits.map(split => ({
      original: split.original,
      handle: split.handle,
      knot: split.knot,
      validated: split.validated,
      corrected: split.corrected,
      system_handle: split.system_handle,
      system_knot: split.system_knot,
      system_confidence: split.system_confidence,
      system_reasoning: split.system_reasoning,
      should_not_split: split.should_not_split,
      occurrences:
        split.occurrences?.map(occ => ({
          file: occ.file,
          comment_ids: occ.comment_ids,
        })) || [],
    }));

    // Debug: Log the data we're sending
    console.log('Sending brush splits to API:', JSON.stringify(formattedSplits, null, 2));

    const response = await api.post('/brush-splits/save', {
      brush_splits: formattedSplits,
    });
    return response.data;
  } catch (error) {
    console.error('Failed to save brush splits:', error);
    throw error;
  }
};

// Error handling utility
export const handleApiError = (error: unknown): string => {
  if (error && typeof error === 'object' && 'response' in error) {
    const apiError = error as { response: { data?: { message?: string }; status?: number } };
    if (apiError.response?.data?.message) {
      return apiError.response.data.message;
    }
    if (apiError.response?.status) {
      return `HTTP ${apiError.response.status} error`;
    }
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unexpected error occurred';
};

// Filtered entries operations
export interface FilteredEntry {
  name: string;
  action: 'add' | 'remove';
  comment_id?: string;
  source?: string;
  month: string; // Add month to each entry
}

export interface FilteredEntryRequest {
  category: string;
  entries: FilteredEntry[];
  reason?: string;
}

export interface FilteredEntryResponse {
  success: boolean;
  message: string;
  data?: Record<string, unknown>;
  added_count: number;
  removed_count: number;
  errors: string[];
}

export interface FilteredStatusRequest {
  entries: Array<{
    category: string;
    name: string;
  }>;
}

export interface FilteredStatusResponse {
  success: boolean;
  message: string;
  data: Record<string, boolean>;
}

export const getFilteredEntries = async (): Promise<FilteredEntryResponse> => {
  try {
    const response = await api.get('/filtered/');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch filtered entries:', error);
    throw error;
  }
};

export const getFilteredEntriesByCategory = async (
  category: string
): Promise<FilteredEntryResponse> => {
  try {
    const response = await api.get(`/filtered/${category}`);
    return response.data;
  } catch (error) {
    console.error(`Failed to fetch filtered entries for ${category}:`, error);
    throw error;
  }
};

export const updateFilteredEntries = async (
  request: FilteredEntryRequest
): Promise<FilteredEntryResponse> => {
  try {
    const response = await api.post('/filtered/', request);
    return response.data;
  } catch (error) {
    console.error('Failed to update filtered entries:', error);
    throw error;
  }
};

export const checkFilteredStatus = async (
  request: FilteredStatusRequest
): Promise<FilteredStatusResponse> => {
  try {
    const response = await api.post('/filtered/check', request);
    return response.data;
  } catch (error) {
    console.error('Failed to check filtered status:', error);
    throw error;
  }
};

export interface MarkCorrectRequest {
  field: string;
  matches: Array<{
    original: string;
    matched: any;
  }>;
  force?: boolean;
}

export interface MarkCorrectResponse {
  success: boolean;
  message: string;
  marked_count: number;
  errors: string[];
}

export interface CorrectMatchesResponse {
  field: string;
  total_entries: number;
  entries: Record<string, any>;
}

export const getCorrectMatches = async (field: string): Promise<CorrectMatchesResponse> => {
  try {
    const response = await api.get(`/analyze/correct-matches/${field}`);
    return response.data;
  } catch (error) {
    console.error('Failed to get correct matches:', error);
    throw error;
  }
};

export const markMatchesAsCorrect = async (request: MarkCorrectRequest): Promise<MarkCorrectResponse> => {
  try {
    const response = await api.post('/analyze/mark-correct', request);
    return response.data;
  } catch (error) {
    console.error('Failed to mark matches as correct:', error);
    throw error;
  }
};

export const clearCorrectMatchesByField = async (field: string): Promise<{ success: boolean; message: string }> => {
  try {
    const response = await api.delete(`/analyze/correct-matches/${field}`);
    return response.data;
  } catch (error) {
    console.error('Failed to clear correct matches:', error);
    throw error;
  }
};

export const clearAllCorrectMatches = async (): Promise<{ success: boolean; message: string }> => {
  try {
    const response = await api.delete('/analyze/correct-matches');
    return response.data;
  } catch (error) {
    console.error('Failed to clear all correct matches:', error);
    throw error;
  }
};
