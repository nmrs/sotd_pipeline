/**
 * Backend simulation tests for comment ID sorting behavior
 * These tests simulate the backend logic to verify sorting works correctly
 */

describe('Comment ID Sorting Backend Simulation Tests', () => {
  // Simulate the backend sorting logic
  function simulateCommentIdSorting(fileInfos: Array<{ comment_id: string; file: string }>) {
    // Get unique comment IDs with their source files, prioritizing newer months
    const commentFiles: Record<string, string> = {};

    for (const info of fileInfos) {
      const commentId = info.comment_id;
      if (commentId) {
        const sourceFile = info.file;
        // Only keep if we haven't seen this comment_id, or if this month is newer
        if (!(commentId in commentFiles) || sourceFile > commentFiles[commentId]) {
          commentFiles[commentId] = sourceFile;
        }
      }
    }

    // Sort by filename (month) newest first and take first 5
    const sortedComments = Object.entries(commentFiles)
      .sort(([, fileA], [, fileB]) => fileB.localeCompare(fileA)) // Reverse sort (newest first)
      .slice(0, 5);

    return sortedComments.map(([commentId]) => commentId);
  }

  test('should sort comment IDs by month (newest first) when both months have data', () => {
    const fileInfos = [
      // 2020-08 data (older)
      { comment_id: 'g00m6ou', file: '2020-08.json' },
      { comment_id: 'g042aih', file: '2020-08.json' },
      { comment_id: 'g0706vx', file: '2020-08.json' },
      { comment_id: 'g0b8wta', file: '2020-08.json' },
      { comment_id: 'g0fgbhn', file: '2020-08.json' },

      // 2025-08 data (newer)
      { comment_id: 'n9d8qy1', file: '2025-08.json' },
      { comment_id: 'naxiyxz', file: '2025-08.json' },
      { comment_id: 'nb5f6lv', file: '2025-08.json' },
    ];

    const sortedCommentIds = simulateCommentIdSorting(fileInfos);

    // Should return 5 comment IDs, with 2025-08 ones first
    expect(sortedCommentIds).toHaveLength(5);
    expect(sortedCommentIds).toEqual(['n9d8qy1', 'naxiyxz', 'nb5f6lv', 'g00m6ou', 'g042aih']);

    // Verify that 2025-08 comment IDs come first
    expect(sortedCommentIds[0]).toBe('n9d8qy1'); // 2025-08
    expect(sortedCommentIds[1]).toBe('naxiyxz'); // 2025-08
    expect(sortedCommentIds[2]).toBe('nb5f6lv'); // 2025-08
    expect(sortedCommentIds[3]).toBe('g00m6ou'); // 2020-08
    expect(sortedCommentIds[4]).toBe('g042aih'); // 2020-08
  });

  test('should handle only one month correctly', () => {
    const fileInfos = [
      // Only 2020-08 data
      { comment_id: 'g00m6ou', file: '2020-08.json' },
      { comment_id: 'g042aih', file: '2020-08.json' },
      { comment_id: 'g0706vx', file: '2020-08.json' },
      { comment_id: 'g0b8wta', file: '2020-08.json' },
      { comment_id: 'g0fgbhn', file: '2020-08.json' },
    ];

    const sortedCommentIds = simulateCommentIdSorting(fileInfos);

    // Should return 5 comment IDs from 2020-08
    expect(sortedCommentIds).toHaveLength(5);
    expect(sortedCommentIds).toEqual(['g00m6ou', 'g042aih', 'g0706vx', 'g0b8wta', 'g0fgbhn']);
  });

  test('should handle multiple months with proper sorting', () => {
    const fileInfos = [
      // 2020-08 data (oldest)
      { comment_id: 'g00m6ou', file: '2020-08.json' },
      { comment_id: 'g042aih', file: '2020-08.json' },

      // 2024-08 data (middle)
      { comment_id: 'g24a1b2', file: '2024-08.json' },
      { comment_id: 'g24c3d4', file: '2024-08.json' },

      // 2025-08 data (newest)
      { comment_id: 'n9d8qy1', file: '2025-08.json' },
      { comment_id: 'naxiyxz', file: '2025-08.json' },
    ];

    const sortedCommentIds = simulateCommentIdSorting(fileInfos);

    // Should return 5 comment IDs, sorted newest first
    expect(sortedCommentIds).toHaveLength(5);
    expect(sortedCommentIds).toEqual(['n9d8qy1', 'naxiyxz', 'g24a1b2', 'g24c3d4', 'g00m6ou']);

    // Verify proper month ordering
    expect(sortedCommentIds[0]).toBe('n9d8qy1'); // 2025-08 (newest)
    expect(sortedCommentIds[1]).toBe('naxiyxz'); // 2025-08 (newest)
    expect(sortedCommentIds[2]).toBe('g24a1b2'); // 2024-08 (middle)
    expect(sortedCommentIds[3]).toBe('g24c3d4'); // 2024-08 (middle)
    expect(sortedCommentIds[4]).toBe('g00m6ou'); // 2020-08 (oldest)
  });

  test('should limit to 5 comment IDs even when more are available', () => {
    const fileInfos = [
      // Many 2020-08 entries
      { comment_id: 'g00m6ou', file: '2020-08.json' },
      { comment_id: 'g042aih', file: '2020-08.json' },
      { comment_id: 'g0706vx', file: '2020-08.json' },
      { comment_id: 'g0b8wta', file: '2020-08.json' },
      { comment_id: 'g0fgbhn', file: '2020-08.json' },
      { comment_id: 'g0h7i8j', file: '2020-08.json' },
      { comment_id: 'g0k9l0m', file: '2020-08.json' },

      // Some 2025-08 entries
      { comment_id: 'n9d8qy1', file: '2025-08.json' },
      { comment_id: 'naxiyxz', file: '2025-08.json' },
    ];

    const sortedCommentIds = simulateCommentIdSorting(fileInfos);

    // Should return exactly 5 comment IDs
    expect(sortedCommentIds).toHaveLength(5);

    // Should prioritize 2025-08 entries first
    expect(sortedCommentIds[0]).toBe('n9d8qy1'); // 2025-08
    expect(sortedCommentIds[1]).toBe('naxiyxz'); // 2025-08
    // Then 3 from 2020-08
    expect(sortedCommentIds[2]).toBe('g00m6ou'); // 2020-08
    expect(sortedCommentIds[3]).toBe('g042aih'); // 2020-08
    expect(sortedCommentIds[4]).toBe('g0706vx'); // 2020-08
  });

  test('should handle duplicate comment IDs correctly', () => {
    const fileInfos = [
      // Same comment ID in both months (should prioritize newer month)
      { comment_id: 'g00m6ou', file: '2020-08.json' },
      { comment_id: 'g00m6ou', file: '2025-08.json' }, // Same ID, newer month
      { comment_id: 'g042aih', file: '2020-08.json' },
      { comment_id: 'g0706vx', file: '2020-08.json' },
    ];

    const sortedCommentIds = simulateCommentIdSorting(fileInfos);

    // Should return 3 unique comment IDs
    expect(sortedCommentIds).toHaveLength(3);

    // The duplicate comment ID should be associated with the newer month (2025-08)
    // Since we're sorting by month, the 2025-08 version should come first
    expect(sortedCommentIds[0]).toBe('g00m6ou'); // From 2025-08 (newer)
    expect(sortedCommentIds[1]).toBe('g042aih'); // From 2020-08
    expect(sortedCommentIds[2]).toBe('g0706vx'); // From 2020-08
  });
});
