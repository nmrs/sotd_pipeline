import { createMockApi, createMockMonths, createMockFetch, MockApiConfig } from '../testUtils';

describe('Test Utilities', () => {
  describe('createMockApi', () => {
    test('should create basic API mock with default responses', () => {
      const mockApi = createMockApi();

      expect(mockApi.getAvailableMonths).toBeDefined();
      expect(mockApi.getMonthData).toBeDefined();
      expect(mockApi.analyzeUnmatched).toBeDefined();
      expect(mockApi.loadBrushSplits).toBeDefined();
    });

    test('should create API mock with custom responses', () => {
      const customResponses = {
        getAvailableMonths: ['2024-01', '2024-02'],
        getMonthData: {
          month: '2024-01',
          total_shaves: 100,
          unique_shavers: 50,
          included_months: ['2024-01'],
          missing_months: [],
        },
      };

      const mockApi = createMockApi({ responses: customResponses });

      expect(mockApi.getAvailableMonths).toBeDefined();
      expect(mockApi.getMonthData).toBeDefined();
    });

    test('should create API mock with error responses', () => {
      const errorConfig: MockApiConfig = {
        errors: {
          getAvailableMonths: new Error('Network error'),
          getMonthData: new Error('Server error'),
        },
      };

      const mockApi = createMockApi(errorConfig);

      expect(mockApi.getAvailableMonths).toBeDefined();
      expect(mockApi.getMonthData).toBeDefined();
    });

    test('should create API mock with mixed success and error responses', () => {
      const mixedConfig: MockApiConfig = {
        responses: {
          getAvailableMonths: ['2024-01', '2024-02'],
        },
        errors: {
          getMonthData: new Error('Server error'),
        },
      };

      const mockApi = createMockApi(mixedConfig);

      expect(mockApi.getAvailableMonths).toBeDefined();
      expect(mockApi.getMonthData).toBeDefined();
    });
  });

  describe('createMockMonths', () => {
    test('should create default mock months', () => {
      const mockMonths = createMockMonths();

      expect(Array.isArray(mockMonths)).toBe(true);
      expect(mockMonths.length).toBeGreaterThan(0);
      expect(mockMonths[0]).toMatch(/^\d{4}-\d{2}$/);
    });

    test('should create mock months with custom count', () => {
      const mockMonths = createMockMonths(5);

      expect(mockMonths).toHaveLength(5);
      mockMonths.forEach(month => {
        expect(month).toMatch(/^\d{4}-\d{2}$/);
      });
    });

    test('should create mock months with custom start date', () => {
      const mockMonths = createMockMonths(3, '2023-01');

      expect(mockMonths).toHaveLength(3);
      expect(mockMonths[0]).toBe('2023-01');
      expect(mockMonths[1]).toBe('2023-02');
      expect(mockMonths[2]).toBe('2023-03');
    });

    test('should create mock months with custom start date and count', () => {
      const mockMonths = createMockMonths(2, '2024-06');

      expect(mockMonths).toHaveLength(2);
      expect(mockMonths[0]).toBe('2024-06');
      expect(mockMonths[1]).toBe('2024-07');
    });
  });

  describe('createMockFetch', () => {
    test('should create basic fetch mock', () => {
      const mockFetch = createMockFetch();

      expect(typeof mockFetch).toBe('function');
    });

    test('should create fetch mock with custom responses', () => {
      const customResponses = {
        '/api/health': { status: 200, data: { status: 'ok' } },
        '/api/files/available-months': { status: 200, data: { months: ['2024-01'] } },
      };

      const mockFetch = createMockFetch(customResponses);

      expect(typeof mockFetch).toBe('function');
    });

    test('should create fetch mock with error responses', () => {
      const errorResponses = {
        '/api/health': { status: 500, error: 'Server error' },
        '/api/files/available-months': { status: 404, error: 'Not found' },
      };

      const mockFetch = createMockFetch(errorResponses);

      expect(typeof mockFetch).toBe('function');
    });

    test('should create fetch mock with mixed responses', () => {
      const mixedResponses = {
        '/api/health': { status: 200, data: { status: 'ok' } },
        '/api/files/available-months': { status: 500, error: 'Server error' },
      };

      const mockFetch = createMockFetch(mixedResponses);

      expect(typeof mockFetch).toBe('function');
    });
  });

  describe('MockApiConfig', () => {
    test('should have correct type structure', () => {
      const config: MockApiConfig = {
        responses: {
          getAvailableMonths: ['2024-01'],
          getMonthData: {
            month: '2024-01',
            total_shaves: 100,
            unique_shavers: 50,
            included_months: ['2024-01'],
            missing_months: [],
          },
        },
        errors: {
          analyzeUnmatched: new Error('Test error'),
        },
      };

      expect(config.responses).toBeDefined();
      expect(config.errors).toBeDefined();
    });
  });
});
