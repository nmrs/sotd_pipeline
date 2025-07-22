// Test utility functions for common mocks

export interface MockApiConfig {
    responses?: Record<string, any>;
    errors?: Record<string, Error>;
}

export interface MockFetchResponse {
    status: number;
    data?: any;
    error?: string;
}

export interface MockFetchConfig {
    [url: string]: MockFetchResponse;
}

/**
 * Creates a mock API object with configurable responses and errors
 */
export function createMockApi(config?: MockApiConfig) {
    const defaultResponses = {
        getAvailableMonths: ['2024-01', '2024-02', '2024-03'],
        getMonthData: {
            month: '2024-01',
            total_shaves: 100,
            unique_shavers: 50,
            included_months: ['2024-01'],
            missing_months: []
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
                    examples: ['Example 1', 'Example 2']
                }
            ],
            processing_time: 0.5
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
                    should_not_split: false
                }
            ],
            statistics: {
                total: 1,
                validated: 0,
                corrected: 0
            }
        }
    };

    const responses: Record<string, any> = { ...defaultResponses, ...config?.responses };
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
        'updateFilteredEntries'
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
 * Creates an array of mock months with configurable count and start date
 */
export function createMockMonths(count: number = 6, startDate: string = '2024-01'): string[] {
    const months: string[] = [];
    const [year, month] = startDate.split('-').map(Number);

    for (let i = 0; i < count; i++) {
        const currentMonth = month + i;
        const currentYear = year + Math.floor((currentMonth - 1) / 12);
        const adjustedMonth = ((currentMonth - 1) % 12) + 1;

        const monthStr = adjustedMonth.toString().padStart(2, '0');
        const yearStr = currentYear.toString();

        months.push(`${yearStr}-${monthStr}`);
    }

    return months;
}

/**
 * Creates a mock fetch function with configurable responses
 */
export function createMockFetch(config?: MockFetchConfig): jest.Mock {
    const defaultResponses: MockFetchConfig = {
        '/api/health': { status: 200, data: { status: 'ok' } },
        '/api/files/available-months': { status: 200, data: { months: ['2024-01', '2024-02'] } },
        '/api/analyze/unmatched': { status: 200, data: { field: 'brush', unmatched_items: [] } }
    };

    const responses = { ...defaultResponses, ...config };

    return jest.fn().mockImplementation((url: string, options?: any) => {
        const response = responses[url];

        if (!response) {
            return Promise.resolve({
                ok: false,
                status: 404,
                json: () => Promise.resolve({ error: 'Not found' })
            });
        }

        if (response.status >= 400) {
            return Promise.resolve({
                ok: false,
                status: response.status,
                json: () => Promise.resolve({ error: response.error })
            });
        }

        return Promise.resolve({
            ok: true,
            status: response.status,
            json: () => Promise.resolve(response.data)
        });
    });
}

/**
 * Creates a mock axios instance with configurable responses
 */
export function createMockAxios(config?: MockApiConfig) {
    const mockApi = createMockApi(config);

    return {
        get: jest.fn().mockImplementation((url: string) => {
            if (url.includes('available-months')) {
                return Promise.resolve({ data: { months: mockApi.getAvailableMonths() } });
            }
            if (url.includes('month/')) {
                return Promise.resolve({ data: mockApi.getMonthData() });
            }
            return Promise.resolve({ data: null });
        }),
        post: jest.fn().mockImplementation((url: string, data: any) => {
            if (url.includes('analyze/unmatched')) {
                return Promise.resolve({ data: mockApi.analyzeUnmatched(data) });
            }
            if (url.includes('brush-splits/save')) {
                return Promise.resolve({ data: mockApi.saveBrushSplit(data) });
            }
            return Promise.resolve({ data: null });
        }),
        interceptors: {
            request: {
                use: jest.fn()
            },
            response: {
                use: jest.fn()
            }
        }
    };
}

/**
 * Creates mock brush data for testing
 */
export function createMockBrushData(count: number = 3) {
    return Array.from({ length: count }, (_, i) => ({
        main: {
            text: `Test Brush ${i + 1}`,
            count: Math.floor(Math.random() * 10) + 1,
            comment_ids: [`comment_${i + 1}_1`, `comment_${i + 1}_2`],
            examples: [`example_${i + 1}_1.json`, `example_${i + 1}_2.json`],
            status: 'Unmatched'
        },
        components: {
            handle: {
                text: `Test Handle ${i + 1}`,
                status: 'Unmatched',
                pattern: 'handle_pattern'
            },
            knot: {
                text: `Test Knot ${i + 1}`,
                status: 'Unmatched',
                pattern: 'knot_pattern'
            }
        }
    }));
}

/**
 * Creates mock brush split data for testing
 */
export function createMockBrushSplits(count: number = 3) {
    return Array.from({ length: count }, (_, i) => ({
        original: `Test Brush ${i + 1}`,
        handle: i % 2 === 0 ? `Test Handle ${i + 1}` : null,
        knot: `Test Knot ${i + 1}`,
        match_type: ['exact', 'regex', 'alias', 'brand'][i % 4],
        validated: i % 3 === 0,
        corrected: i % 4 === 0,
        should_not_split: i % 5 === 0,
        validated_at: i % 2 === 0 ? new Date().toISOString() : null
    }));
} 