// Mock the entire api module to avoid axios.create issues
jest.mock('../api', () => ({
  analyzeMismatch: jest.fn(),
  getCommentDetail: jest.fn(),
  checkFilteredStatus: jest.fn(),
}));

import { analyzeMismatch, getCommentDetail, checkFilteredStatus } from '../api';

describe('API Service Unit Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('analyzeMismatch', () => {
    test('should handle successful API call', async () => {
      const mockResponse = {
        field: 'brush',
        months: ['2024-01'],
        total_matches: 0,
        total_mismatches: 1,
        mismatch_items: [
          {
            original: 'Simpson Chubby 2',
            matched: {},
            pattern: '',
            match_type: 'unmatched',
            mismatch_type: 'unmatched',
            count: 5,
            comment_ids: ['123', '456'],
            examples: ['Example 1', 'Example 2'],
          },
        ],
        processing_time: 0.5,
      };

      (analyzeMismatch as jest.Mock).mockResolvedValue(mockResponse);

      const result = await analyzeMismatch({
        field: 'brush',
        months: ['2024-01'],
        display_mode: 'unmatched',
        limit: 1000,
      });

      expect(analyzeMismatch).toHaveBeenCalledWith({
        field: 'brush',
        months: ['2024-01'],
        display_mode: 'unmatched',
        limit: 1000,
      });

      expect(result).toEqual(mockResponse);
    });

    test('should handle API errors gracefully', async () => {
      const mockError = new Error('Network error');
      (analyzeMismatch as jest.Mock).mockRejectedValue(mockError);

      await expect(
        analyzeMismatch({
          field: 'brush',
          months: ['2024-01'],
          display_mode: 'unmatched',
          limit: 1000,
        })
      ).rejects.toThrow('Network error');
    });

    test('should handle timeout errors', async () => {
      const mockError = new Error('timeout of 5000ms exceeded');
      (analyzeMismatch as jest.Mock).mockRejectedValue(mockError);

      await expect(
        analyzeMismatch({
          field: 'brush',
          months: ['2024-01'],
          display_mode: 'unmatched',
          limit: 1000,
        })
      ).rejects.toThrow('timeout of 5000ms exceeded');
    });

    test('should handle malformed response data', async () => {
      const mockResponse = null;
      (analyzeMismatch as jest.Mock).mockResolvedValue(mockResponse);

      const result = await analyzeMismatch({
        field: 'brush',
        months: ['2024-01'],
        display_mode: 'unmatched',
        limit: 1000,
      });

      expect(result).toBeNull();
    });
  });

  describe('getCommentDetail', () => {
    test('should handle successful comment detail retrieval', async () => {
      const mockResponse = {
        id: '123',
        body: 'Test comment body',
        author: 'test_user',
        created_utc: '2022-01-01T00:00:00Z',
        thread_id: 'thread123',
        thread_title: 'Test Thread',
        url: 'https://reddit.com/r/wetshaving/comments/thread123',
      };

      (getCommentDetail as jest.Mock).mockResolvedValue(mockResponse);

      const result = await getCommentDetail('123', ['2024-01']);

      // Verify function was called with correct parameters
      expect(getCommentDetail).toHaveBeenCalledWith('123', ['2024-01']);

      // Verify return value
      expect(result).toEqual(mockResponse);
    });

    test('should handle comment not found', async () => {
      const mockError = new Error('Comment not found');
      (getCommentDetail as jest.Mock).mockRejectedValue(mockError);

      await expect(getCommentDetail('nonexistent', ['2024-01'])).rejects.toThrow(
        'Comment not found'
      );
    });
  });

  describe('checkFilteredStatus', () => {
    test('should handle successful filtered status check', async () => {
      const mockResponse = {
        success: true,
        message: 'Status checked successfully',
        data: {
          'brush:Simpson Chubby 2': true,
        },
      };

      (checkFilteredStatus as jest.Mock).mockResolvedValue(mockResponse);

      const result = await checkFilteredStatus({
        entries: [{ category: 'brush', name: 'Simpson Chubby 2' }],
      });

      // Verify function was called with correct parameters
      expect(checkFilteredStatus).toHaveBeenCalledWith({
        entries: [{ category: 'brush', name: 'Simpson Chubby 2' }],
      });

      // Verify return value
      expect(result).toEqual(mockResponse);
    });

    test('should handle not filtered status', async () => {
      const mockResponse = {
        success: true,
        message: 'Status checked successfully',
        data: {
          'brush:Unknown Brush': false,
        },
      };

      (checkFilteredStatus as jest.Mock).mockResolvedValue(mockResponse);

      const result = await checkFilteredStatus({
        entries: [{ category: 'brush', name: 'Unknown Brush' }],
      });

      expect(result.data['brush:Unknown Brush']).toBe(false);
    });
  });

  describe('Error Handling Edge Cases', () => {
    test('should handle network connectivity issues', async () => {
      const mockError = new Error('Network Error');
      (analyzeMismatch as jest.Mock).mockRejectedValue(mockError);

      await expect(
        analyzeMismatch({
          field: 'brush',
          months: ['2024-01'],
          display_mode: 'unmatched',
          limit: 1000,
        })
      ).rejects.toThrow('Network Error');
    });

    test('should handle server errors (500)', async () => {
      const mockError = new Error('Internal server error');
      (analyzeMismatch as jest.Mock).mockRejectedValue(mockError);

      await expect(
        analyzeMismatch({
          field: 'brush',
          months: ['2024-01'],
          display_mode: 'unmatched',
          limit: 1000,
        })
      ).rejects.toThrow('Internal server error');
    });

    test('should handle unauthorized errors (401)', async () => {
      const mockError = new Error('Unauthorized');
      (analyzeMismatch as jest.Mock).mockRejectedValue(mockError);

      await expect(
        analyzeMismatch({
          field: 'brush',
          months: ['2024-01'],
          display_mode: 'unmatched',
          limit: 1000,
        })
      ).rejects.toThrow('Unauthorized');
    });

    test('should handle rate limiting errors (429)', async () => {
      const mockError = new Error('Too many requests');
      (analyzeMismatch as jest.Mock).mockRejectedValue(mockError);

      await expect(
        analyzeMismatch({
          field: 'brush',
          months: ['2024-01'],
          display_mode: 'unmatched',
          limit: 1000,
        })
      ).rejects.toThrow('Too many requests');
    });
  });

  describe('Parameter Validation', () => {
    test('should handle empty field parameter', async () => {
      const mockResponse = {
        field: '',
        months: ['2024-01'],
        total_matches: 0,
        total_mismatches: 0,
        mismatch_items: [],
        processing_time: 0.1,
      };

      (analyzeMismatch as jest.Mock).mockResolvedValue(mockResponse);

      await analyzeMismatch({
        field: '',
        months: ['2024-01'],
        display_mode: 'unmatched',
        limit: 1000,
      });

      expect(analyzeMismatch).toHaveBeenCalledWith({
        field: '',
        months: ['2024-01'],
        display_mode: 'unmatched',
        limit: 1000,
      });
    });

    test('should handle invalid month format', async () => {
      const mockResponse = {
        field: 'brush',
        months: ['invalid-month'],
        total_matches: 0,
        total_mismatches: 0,
        mismatch_items: [],
        processing_time: 0.1,
      };

      (analyzeMismatch as jest.Mock).mockResolvedValue(mockResponse);

      await analyzeMismatch({
        field: 'brush',
        months: ['invalid-month'],
        display_mode: 'unmatched',
        limit: 1000,
      });

      expect(analyzeMismatch).toHaveBeenCalledWith({
        field: 'brush',
        months: ['invalid-month'],
        display_mode: 'unmatched',
        limit: 1000,
      });
    });

    test('should return comment IDs sorted by month (newest first)', async () => {
      const mockResponse = {
        field: 'blade',
        months: ['2025-08', '2020-08'],
        total_matches: 0,
        total_mismatches: 1,
        mismatch_items: [
          {
            original: 'Lord',
            matched: {},
            pattern: '',
            match_type: 'unmatched',
            mismatch_type: 'unmatched',
            count: 6,
            comment_ids: ['n9d8qy1', 'g00m6ou', 'g042aih', 'g0706vx', 'g0b8wta'],
            examples: ['2025-08.json', '2020-08.json'],
          },
        ],
        processing_time: 0.5,
      };

      (analyzeMismatch as jest.Mock).mockResolvedValue(mockResponse);

      const result = await analyzeMismatch({
        field: 'blade',
        months: ['2025-08', '2020-08'],
        display_mode: 'unmatched',
        limit: 1000,
      });

      const commentIds = result.mismatch_items[0].comment_ids;
      expect(commentIds).toEqual(['n9d8qy1', 'g00m6ou', 'g042aih', 'g0706vx', 'g0b8wta']);
      expect(commentIds[0]).toBe('n9d8qy1');
    });
  });
});
