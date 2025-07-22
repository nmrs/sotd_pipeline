import axios from 'axios';

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

export const getCatalogContent = async (catalogName: string): Promise<any> => {
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
  matched?: any;
  unmatched?: any;
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
export interface BrushSplit {
  original: string;
  handle: string | null;
  knot: string;
  match_type?: string;
  validated?: boolean;
  corrected?: boolean;
  validated_at?: string | null;
  system_handle?: string | null;
  system_knot?: string | null;
  system_confidence?: string | null;
  system_reasoning?: string | null;
  occurrences?: any[];
  should_not_split?: boolean;
}

export interface LoadBrushSplitsResponse {
  brush_splits: BrushSplit[];
  statistics: any;
  processing_info?: any;
  errors?: any;
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
  corrected: boolean;
  system_handle?: string | null;
  system_knot?: string | null;
  system_confidence?: string | null;
  system_reasoning?: string | null;
}

export const loadBrushSplits = async (months: string[]): Promise<LoadBrushSplitsResponse> => {
  try {
    const queryParams = months.map(month => `months=${encodeURIComponent(month)}`).join('&');
    const response = await api.get(`/brush-splits/load?${queryParams}`);
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

// Error handling utility
export const handleApiError = (error: any): string => {
  if (error.response) {
    // Server responded with error status
    return error.response.data?.detail || `Server error: ${error.response.status}`;
  } else if (error.request) {
    // Request was made but no response received
    return 'Network error: Unable to reach the server';
  } else {
    // Something else happened
    return error.message || 'An unexpected error occurred';
  }
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
  data?: any;
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
