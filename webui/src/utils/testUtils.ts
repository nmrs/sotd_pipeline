/**
 * Test utility functions for common mocks
 *
 * This module provides reusable mock functions and utilities for testing
 * the SOTD Pipeline WebUI. It includes mocks for API calls, fetch requests,
 * and common data structures used throughout the application.
 *
 * @module TestUtils
 */

/**
 * Configuration for mock API responses and errors
 */
export interface MockApiConfig {
  responses?: Record<string, unknown>;
  errors?: Record<string, Error>;
}

/**
 * Mock fetch response structure
 */
export interface MockFetchResponse {
  status: number;
  data?: unknown;
  error?: string;
}

/**
 * Configuration for mock fetch responses by URL
 */
export interface MockFetchConfig {
  [url: string]: MockFetchResponse;
}

/**
 * Creates a mock API object with configurable responses and errors
 *
 * This function creates a comprehensive mock API that can be used
 * in tests to simulate various API scenarios including success responses,
 * errors, and different data structures.
 *
 * @param config - Optional configuration for custom responses and errors
 * @returns Mock API object with jest.Mock functions for all API methods
 *
 * @example
 * ```typescript
 * const mockApi = createMockApi({
 *   responses: {
 *     getAvailableMonths: ['2024-01', '2024-02'],
 *     analyzeUnmatched: { total_unmatched: 5 }
 *   },
 *   errors: {
 *     getMonthData: new Error('Network error')
 *   }
 * });
 * ```
 */
export function createMockApi(config?: MockApiConfig) {
  const defaultResponses = {
    getAvailableMonths: ['2024-01', '2024-02', '2024-03'],
    getMonthData: {
      month: '2024-01',
      total_shaves: 100,
      unique_shavers: 50,
      included_months: ['2024-01'],
      missing_months: [],
    },
    analyzeUnmatched: {
      field: 'brush',
      months: ['2024-01'],
      total_unmatched: 1,
      unmatched_items: [
        {
          item: 'Test Brush',
          count: 5,
          comment_ids: ['123', '456'],
          examples: ['Example 1', 'Example 2'],
        },
      ],
      processing_time: 0.5,
    },
    loadBrushSplits: {
      brush_splits: [
        {
          original: 'Test Brush',
          handle: 'Test Handle',
          knot: 'Test Knot',
          match_type: 'exact',
          validated: false,
          corrected: false,
          should_not_split: false,
        },
      ],
      statistics: {
        total: 1,
        validated: 0,
        corrected: 0,
      },
    },
  };

  const responses: Record<string, unknown> = { ...defaultResponses, ...config?.responses };
  const errors: Record<string, Error> = config?.errors || {};

  const mockApi: Record<string, jest.Mock> = {};

  // Create mock functions for all API methods
  const apiMethods = [
    'getAvailableMonths',
    'getMonthData',
    'analyzeUnmatched',
    'loadBrushSplits',
    'saveBrushSplit',
    'getCommentDetail',
    'checkFilteredStatus',
    'getCatalogs',
    'getCatalogContent',
    'checkHealth',
    'runMatchPhase',
    'getFilteredEntries',
    'getFilteredEntriesByCategory',
    'updateFilteredEntries',
  ];

  apiMethods.forEach(method => {
    if (errors[method]) {
      mockApi[method] = jest.fn().mockRejectedValue(errors[method]);
    } else if (responses[method]) {
      mockApi[method] = jest.fn().mockResolvedValue(responses[method]);
    } else {
      mockApi[method] = jest.fn().mockResolvedValue(null);
    }
  });

  return mockApi;
}

/**
 * Creates an array of mock month strings
 *
 * @param count - Number of months to generate (default: 6)
 * @param startDate - Starting date in YYYY-MM format (default: '2024-01')
 * @returns Array of month strings
 *
 * @example
 * ```typescript
 * const months = createMockMonths(3, '2024-01');
 * // Returns: ['2024-01', '2024-02', '2024-03']
 * ```
 */
export function createMockMonths(count: number = 6, startDate: string = '2024-01'): string[] {
  const months: string[] = [];
  const [year, month] = startDate.split('-').map(Number);

  for (let i = 0; i < count; i++) {
    const currentMonth = month + i;
    const currentYear = year + Math.floor((currentMonth - 1) / 12);
    const adjustedMonth = ((currentMonth - 1) % 12) + 1;

    months.push(`${currentYear}-${adjustedMonth.toString().padStart(2, '0')}`);
  }

  return months;
}

/**
 * Creates a mock fetch function with configurable responses
 *
 * @param config - Configuration object mapping URLs to responses
 * @returns Jest mock function that simulates fetch behavior
 *
 * @example
 * ```typescript
 * const mockFetch = createMockFetch({
 *   '/api/months': { status: 200, data: ['2024-01', '2024-02'] },
 *   '/api/analysis': { status: 500, error: 'Server error' }
 * });
 * ```
 */
export function createMockFetch(config?: MockFetchConfig): jest.Mock {
  return jest.fn().mockImplementation((url: string) => {
    const response = config?.[url];

    if (!response) {
      return Promise.resolve({
        ok: false,
        status: 404,
        json: () => Promise.resolve({ error: 'Not found' }),
      });
    }

    if (response.status >= 400) {
      return Promise.resolve({
        ok: false,
        status: response.status,
        json: () => Promise.resolve({ error: response.error }),
      });
    }

    return Promise.resolve({
      ok: true,
      status: response.status,
      json: () => Promise.resolve(response.data),
    });
  });
}

/**
 * Creates a mock axios instance with configurable responses
 *
 * @param config - Configuration for API responses and errors
 * @returns Mock axios object with jest.Mock functions
 *
 * @example
 * ```typescript
 * const mockAxios = createMockAxios({
 *   responses: {
 *     get: { data: { months: ['2024-01'] } },
 *     post: { data: { success: true } }
 *   }
 * });
 * ```
 */
export function createMockAxios(config?: MockApiConfig) {
  const defaultResponses = {
    get: { data: { months: ['2024-01', '2024-02'] } },
    post: { data: { success: true } },
    put: { data: { success: true } },
    delete: { data: { success: true } },
  };

  const responses: Record<string, unknown> = { ...defaultResponses, ...config?.responses };
  const errors: Record<string, Error> = config?.errors || {};

  const mockAxios: Record<string, jest.Mock> = {};

  ['get', 'post', 'put', 'delete'].forEach(method => {
    if (errors[method]) {
      mockAxios[method] = jest.fn().mockRejectedValue(errors[method]);
    } else if (responses[method]) {
      mockAxios[method] = jest.fn().mockResolvedValue(responses[method]);
    } else {
      mockAxios[method] = jest.fn().mockResolvedValue({ data: null });
    }
  });

  return mockAxios;
}

/**
 * Creates mock brush data for testing
 *
 * @param count - Number of brush items to generate (default: 3)
 * @returns Array of mock brush data objects
 *
 * @example
 * ```typescript
 * const brushData = createMockBrushData(2);
 * // Returns array with 2 mock brush items
 * ```
 */
export function createMockBrushData(count: number = 3) {
  return Array.from({ length: count }, (_, i) => ({
    id: `brush-${i + 1}`,
    original: `Test Brush ${i + 1}`,
    handle: `Test Handle ${i + 1}`,
    knot: `Test Knot ${i + 1}`,
    match_type: 'exact',
    validated: false,
    corrected: false,
    should_not_split: false,
    comment_ids: [`comment-${i + 1}-1`, `comment-${i + 1}-2`],
    examples: [`Example ${i + 1} A`, `Example ${i + 1} B`],
  }));
}

/**
 * Creates mock brush splits data for testing
 *
 * @param count - Number of brush splits to generate (default: 3)
 * @returns Mock brush splits data structure
 *
 * @example
 * ```typescript
 * const brushSplits = createMockBrushSplits(2);
 * // Returns object with brush_splits array and statistics
 * ```
 */
export function createMockBrushSplits(count: number = 3) {
  const brush_splits = Array.from({ length: count }, (_, i) => ({
    original: `Test Brush ${i + 1}`,
    handle: `Test Handle ${i + 1}`,
    knot: `Test Knot ${i + 1}`,
    match_type: 'exact',
    validated: false,
    corrected: false,
    should_not_split: false,
  }));

  return {
    brush_splits,
    statistics: {
      total: count,
      validated: 0,
      corrected: 0,
    },
  };
}
