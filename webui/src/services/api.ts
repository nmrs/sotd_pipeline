import axios from 'axios';
import { analysisCache, catalogCache, fileCache, generateAnalysisKey, generateCatalogKey, generateFileKey } from '../utils/cache';

const API_BASE_URL = '/api';

// Create axios instance with default config
const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
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
    const cacheKey = generateFileKey(month);
    const cached = fileCache.get(cacheKey);
    if (cached) {
        return cached;
    }

    try {
        const response = await api.get(`/files/month/${month}`);
        fileCache.set(cacheKey, response.data);
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
    const cacheKey = generateCatalogKey(catalogName);
    const cached = catalogCache.get(cacheKey);
    if (cached) {
        return cached;
    }

    try {
        const response = await api.get(`/catalogs/${catalogName}`);
        catalogCache.set(cacheKey, response.data);
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

export const getCommentDetail = async (commentId: string, months: string[]): Promise<CommentDetail> => {
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
}

export interface UnmatchedAnalysisResult {
    field: string;
    months: string[];
    total_unmatched: number;
    unmatched_items: UnmatchedItem[];
    processing_time: number;
}

export const analyzeUnmatched = async (
    request: UnmatchedAnalysisRequest
): Promise<UnmatchedAnalysisResult> => {
    const cacheKey = generateAnalysisKey(request.field, request.months, request.limit);
    const cached = analysisCache.get(cacheKey);
    if (cached) {
        return cached;
    }

    try {
        const response = await api.post('/analyze/unmatched', request);
        analysisCache.set(cacheKey, response.data);
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

export const runMatchPhase = async (
    request: MatchPhaseRequest
): Promise<MatchPhaseResult> => {
    try {
        const response = await api.post('/analyze/match-phase', request);
        return response.data;
    } catch (error) {
        console.error('Failed to run match phase:', error);
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