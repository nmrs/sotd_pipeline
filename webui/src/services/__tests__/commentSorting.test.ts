/**
 * Tests for comment ID sorting behavior in unmatched analysis (via Match Analyzer display_mode: 'unmatched')
 */

import { analyzeMismatch } from '../api';

jest.mock('../api', () => ({
  analyzeMismatch: jest.fn(),
}));

const mockAnalyzeMismatch = analyzeMismatch as jest.MockedFunction<typeof analyzeMismatch>;

function mismatchItem(original: string, commentIds: string[], examples: string[]) {
  return {
    original,
    matched: {},
    pattern: '',
    match_type: 'unmatched',
    mismatch_type: 'unmatched',
    count: commentIds.length,
    examples,
    comment_ids: commentIds,
  };
}

describe('Comment ID Sorting Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('should return comment IDs sorted by month (newest first) when both months have data', async () => {
    const mockResponse = {
      field: 'blade',
      months: ['2025-08', '2020-08'],
      total_matches: 0,
      total_mismatches: 1,
      mismatch_items: [
        mismatchItem('Lord', ['n9d8qy1', 'g00m6ou', 'g042aih', 'g0706vx', 'g0b8wta'], [
          '2025-08.json',
          '2020-08.json',
        ]),
      ],
      processing_time: 0.5,
    };

    mockAnalyzeMismatch.mockResolvedValue(mockResponse);

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

  test('should return comment IDs from only one month when other month has no data', async () => {
    const mockResponse = {
      field: 'blade',
      months: ['2025-08', '2020-08'],
      total_matches: 0,
      total_mismatches: 1,
      mismatch_items: [
        mismatchItem('Lord', ['g00m6ou', 'g042aih', 'g0706vx', 'g0b8wta', 'g0fgbhn'], [
          '2020-08.json',
        ]),
      ],
      processing_time: 0.5,
    };

    mockAnalyzeMismatch.mockResolvedValue(mockResponse);

    const result = await analyzeMismatch({
      field: 'blade',
      months: ['2025-08', '2020-08'],
      display_mode: 'unmatched',
      limit: 1000,
    });

    const commentIds = result.mismatch_items[0].comment_ids;
    expect(commentIds).toEqual(['g00m6ou', 'g042aih', 'g0706vx', 'g0b8wta', 'g0fgbhn']);
    expect(commentIds[0]).toBe('g00m6ou');
  });

  test('should handle multiple months with proper sorting', async () => {
    const mockResponse = {
      field: 'blade',
      months: ['2025-08', '2024-08', '2020-08'],
      total_matches: 0,
      total_mismatches: 1,
      mismatch_items: [
        mismatchItem('Lord', ['n9d8qy1', 'naxiyxz', 'g24a1b2', 'g24c3d4', 'g24e5f6'], [
          '2025-08.json',
          '2024-08.json',
          '2020-08.json',
        ]),
      ],
      processing_time: 0.5,
    };

    mockAnalyzeMismatch.mockResolvedValue(mockResponse);

    const result = await analyzeMismatch({
      field: 'blade',
      months: ['2025-08', '2024-08', '2020-08'],
      display_mode: 'unmatched',
      limit: 1000,
    });

    const commentIds = result.mismatch_items[0].comment_ids;
    expect(commentIds).toEqual(['n9d8qy1', 'naxiyxz', 'g24a1b2', 'g24c3d4', 'g24e5f6']);
    expect(commentIds[0]).toBe('n9d8qy1');
    expect(commentIds[1]).toBe('naxiyxz');
  });

  test('should limit comment IDs to 5 even when more are available', async () => {
    const mockResponse = {
      field: 'blade',
      months: ['2025-08', '2020-08'],
      total_matches: 0,
      total_mismatches: 1,
      mismatch_items: [
        mismatchItem('Lord', ['n9d8qy1', 'g00m6ou', 'g042aih', 'g0706vx', 'g0b8wta'], [
          '2025-08.json',
          '2020-08.json',
        ]),
      ],
      processing_time: 0.5,
    };

    mockAnalyzeMismatch.mockResolvedValue(mockResponse);

    const result = await analyzeMismatch({
      field: 'blade',
      months: ['2025-08', '2020-08'],
      display_mode: 'unmatched',
      limit: 1000,
    });

    const commentIds = result.mismatch_items[0].comment_ids;
    expect(commentIds).toHaveLength(5);
    expect(commentIds).toEqual(['n9d8qy1', 'g00m6ou', 'g042aih', 'g0706vx', 'g0b8wta']);
  });
});
