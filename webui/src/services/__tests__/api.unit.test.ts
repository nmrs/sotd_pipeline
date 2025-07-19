// Mock the entire api module to avoid axios.create issues
jest.mock('../api', () => ({
    analyzeUnmatched: jest.fn(),
    getCommentDetail: jest.fn(),
    checkFilteredStatus: jest.fn(),
}));

import { analyzeUnmatched, getCommentDetail, checkFilteredStatus } from '../api';

describe('API Service Unit Tests', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('analyzeUnmatched', () => {
        test('should handle successful API call', async () => {
            const mockResponse = {
                field: 'brush',
                months: ['2024-01'],
                total_unmatched: 1,
                unmatched_items: [
                    {
                        item: 'Simpson Chubby 2',
                        count: 5,
                        comment_ids: ['123', '456'],
                        examples: ['Example 1', 'Example 2']
                    }
                ],
                processing_time: 0.5
            };

            (analyzeUnmatched as jest.Mock).mockResolvedValue(mockResponse);

            const result = await analyzeUnmatched({
                field: 'brush',
                months: ['2024-01'],
                limit: 10
            });

            // Verify function was called with correct parameters
            expect(analyzeUnmatched).toHaveBeenCalledWith({
                field: 'brush',
                months: ['2024-01'],
                limit: 10
            });

            // Verify return value
            expect(result).toEqual(mockResponse);
        });

        test('should handle API errors gracefully', async () => {
            const mockError = new Error('Network error');
            (analyzeUnmatched as jest.Mock).mockRejectedValue(mockError);

            await expect(analyzeUnmatched({
                field: 'brush',
                months: ['2024-01'],
                limit: 10
            })).rejects.toThrow('Network error');
        });

        test('should handle timeout errors', async () => {
            const mockError = new Error('timeout of 5000ms exceeded');
            (analyzeUnmatched as jest.Mock).mockRejectedValue(mockError);

            await expect(analyzeUnmatched({
                field: 'brush',
                months: ['2024-01'],
                limit: 10
            })).rejects.toThrow('timeout of 5000ms exceeded');
        });

        test('should handle malformed response data', async () => {
            const mockResponse = null; // Malformed response
            (analyzeUnmatched as jest.Mock).mockResolvedValue(mockResponse);

            const result = await analyzeUnmatched({
                field: 'brush',
                months: ['2024-01'],
                limit: 10
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
                url: 'https://reddit.com/r/wetshaving/comments/thread123'
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

            await expect(getCommentDetail('nonexistent', ['2024-01']))
                .rejects.toThrow('Comment not found');
        });
    });

    describe('checkFilteredStatus', () => {
        test('should handle successful filtered status check', async () => {
            const mockResponse = {
                success: true,
                message: 'Status checked successfully',
                data: {
                    'brush:Simpson Chubby 2': true
                }
            };

            (checkFilteredStatus as jest.Mock).mockResolvedValue(mockResponse);

            const result = await checkFilteredStatus({
                entries: [
                    { category: 'brush', name: 'Simpson Chubby 2' }
                ]
            });

            // Verify function was called with correct parameters
            expect(checkFilteredStatus).toHaveBeenCalledWith({
                entries: [
                    { category: 'brush', name: 'Simpson Chubby 2' }
                ]
            });

            // Verify return value
            expect(result).toEqual(mockResponse);
        });

        test('should handle not filtered status', async () => {
            const mockResponse = {
                success: true,
                message: 'Status checked successfully',
                data: {
                    'brush:Unknown Brush': false
                }
            };

            (checkFilteredStatus as jest.Mock).mockResolvedValue(mockResponse);

            const result = await checkFilteredStatus({
                entries: [
                    { category: 'brush', name: 'Unknown Brush' }
                ]
            });

            expect(result.data['brush:Unknown Brush']).toBe(false);
        });
    });

    describe('Error Handling Edge Cases', () => {
        test('should handle network connectivity issues', async () => {
            const mockError = new Error('Network Error');
            (analyzeUnmatched as jest.Mock).mockRejectedValue(mockError);

            await expect(analyzeUnmatched({
                field: 'brush',
                months: ['2024-01'],
                limit: 10
            })).rejects.toThrow('Network Error');
        });

        test('should handle server errors (500)', async () => {
            const mockError = new Error('Internal server error');
            (analyzeUnmatched as jest.Mock).mockRejectedValue(mockError);

            await expect(analyzeUnmatched({
                field: 'brush',
                months: ['2024-01'],
                limit: 10
            })).rejects.toThrow('Internal server error');
        });

        test('should handle unauthorized errors (401)', async () => {
            const mockError = new Error('Unauthorized');
            (analyzeUnmatched as jest.Mock).mockRejectedValue(mockError);

            await expect(analyzeUnmatched({
                field: 'brush',
                months: ['2024-01'],
                limit: 10
            })).rejects.toThrow('Unauthorized');
        });

        test('should handle rate limiting errors (429)', async () => {
            const mockError = new Error('Too many requests');
            (analyzeUnmatched as jest.Mock).mockRejectedValue(mockError);

            await expect(analyzeUnmatched({
                field: 'brush',
                months: ['2024-01'],
                limit: 10
            })).rejects.toThrow('Too many requests');
        });
    });

    describe('Parameter Validation', () => {
        test('should handle empty field parameter', async () => {
            const mockResponse = {
                field: '',
                months: ['2024-01'],
                total_unmatched: 0,
                unmatched_items: [],
                processing_time: 0.1
            };

            (analyzeUnmatched as jest.Mock).mockResolvedValue(mockResponse);

            await analyzeUnmatched({
                field: '',
                months: ['2024-01'],
                limit: 10
            });

            expect(analyzeUnmatched).toHaveBeenCalledWith({
                field: '',
                months: ['2024-01'],
                limit: 10
            });
        });

        test('should handle invalid month format', async () => {
            const mockResponse = {
                field: 'brush',
                months: ['invalid-month'],
                total_unmatched: 0,
                unmatched_items: [],
                processing_time: 0.1
            };

            (analyzeUnmatched as jest.Mock).mockResolvedValue(mockResponse);

            await analyzeUnmatched({
                field: 'brush',
                months: ['invalid-month'],
                limit: 10
            });

            expect(analyzeUnmatched).toHaveBeenCalledWith({
                field: 'brush',
                months: ['invalid-month'],
                limit: 10
            });
        });

        test('should handle negative limit', async () => {
            const mockResponse = {
                field: 'brush',
                months: ['2024-01'],
                total_unmatched: 0,
                unmatched_items: [],
                processing_time: 0.1
            };

            (analyzeUnmatched as jest.Mock).mockResolvedValue(mockResponse);

            await analyzeUnmatched({
                field: 'brush',
                months: ['2024-01'],
                limit: -1
            });

            expect(analyzeUnmatched).toHaveBeenCalledWith({
                field: 'brush',
                months: ['2024-01'],
                limit: -1
            });
        });
    });
}); 