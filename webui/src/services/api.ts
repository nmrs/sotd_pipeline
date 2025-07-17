import axios from 'axios';

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
    try {
        const response = await api.post('/analyze/unmatched', request);
        return response.data;
    } catch (error) {
        console.error('Failed to analyze unmatched items:', error);
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