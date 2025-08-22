import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import MismatchAnalyzerDataTable from '../MismatchAnalyzerDataTable';
import { MismatchItem } from '../../../services/api';

// Mock CommentList component
jest.mock('../../domain/CommentList', () => ({
  CommentList: ({
    commentIds,
    onCommentClick,
    commentLoading,
    'aria-label': ariaLabel,
  }: {
    commentIds: string[];
    onCommentClick: (id: string) => void;
    commentLoading?: boolean;
    'aria-label'?: string;
  }) => (
    <div data-testid='comment-list' aria-label={ariaLabel}>
      {commentIds.map((id, index) => (
        <button
          key={id}
          onClick={() => onCommentClick(id)}
          data-testid={`comment-${id}`}
          disabled={commentLoading}
          aria-label={`View comment ${index + 1} of ${commentIds.length}`}
        >
          {id}
        </button>
      ))}
    </div>
  ),
}));

const mockOnCommentClick = jest.fn();

const mockData: MismatchItem[] = [
  {
    original: 'Test Razor 1',
    matched: { brand: 'Test Brand', model: 'Model 1' },
    mismatch_type: 'levenshtein_distance',
    match_type: 'regex',
    pattern: 'test_pattern',
    confidence: 0.8,
    count: 5,
    comment_ids: ['123', '456'],
    examples: ['example1', 'example2'],
  },
  {
    original: 'Test Razor 2',
    matched: { brand: 'Test Brand', model: 'Model 2' },
    mismatch_type: 'multiple_patterns',
    match_type: 'alias',
    pattern: 'test_pattern_2',
    confidence: 0.6,
    count: 3,
    comment_ids: ['789'],
    examples: ['example3'],
  },
];

describe('MismatchAnalyzerDataTable', () => {
  const defaultProps = {
    data: mockData,
    field: 'razor',
    onCommentClick: mockOnCommentClick,
    commentLoading: false,
  };

  describe('MismatchAnalyzerDataTable with CommentDisplay Integration', () => {
    test('renders CommentDisplay component in comments column', () => {
      render(<MismatchAnalyzerDataTable {...defaultProps} />);

      // Look for comment buttons - first item has 2 comments, second has 1
      const commentButtons = screen.getAllByText('123');
      expect(commentButtons).toHaveLength(1);

      const commentButtons456 = screen.getAllByText('456');
      expect(commentButtons456).toHaveLength(1);

      const commentButtons789 = screen.getAllByText('789');
      expect(commentButtons789).toHaveLength(1);
    });

    test('passes correct props to CommentDisplay component', () => {
      render(<MismatchAnalyzerDataTable {...defaultProps} />);

      // Verify comment buttons are rendered correctly
      expect(screen.getByText('123')).toBeInTheDocument();
      expect(screen.getByText('456')).toBeInTheDocument();
      expect(screen.getByText('789')).toBeInTheDocument();
    });

    test('handles empty comment_ids array', () => {
      const dataWithEmptyComments = [{ ...mockData[0], comment_ids: [] }];

      render(<MismatchAnalyzerDataTable {...defaultProps} data={dataWithEmptyComments} />);

      // Should show "-" for empty comments
      expect(screen.getByText('-')).toBeInTheDocument();
    });

    test('passes commentLoading prop to CommentDisplay', () => {
      render(<MismatchAnalyzerDataTable {...defaultProps} commentLoading={true} />);

      // All comment buttons should be disabled when loading
      const commentButtons = screen.getAllByText('123');
      commentButtons.forEach(button => {
        expect(button).toBeDisabled();
      });
    });

    test('calls onCommentClick when comment is clicked', () => {
      const onCommentClick = jest.fn();
      render(<MismatchAnalyzerDataTable {...defaultProps} onCommentClick={onCommentClick} />);

      const commentButtons = screen.getAllByText('123');
      fireEvent.click(commentButtons[0]);

      expect(onCommentClick).toHaveBeenCalledWith('123');
    });
  });

  describe('MismatchAnalyzerDataTable with Selection and Confirmation', () => {
    test('renders selection checkboxes when onItemSelection is provided', () => {
      const onItemSelection = jest.fn();
      render(<MismatchAnalyzerDataTable {...defaultProps} onItemSelection={onItemSelection} />);

      // Should have a "Select" column header
      expect(screen.getByText('Select')).toBeInTheDocument();

      // Should have checkboxes for each row (2 items in test data)
      const checkboxes = screen.getAllByRole('checkbox');
      expect(checkboxes).toHaveLength(2); // One for each visible data item (2 items in test data)
    });

    test('renders confirmation status when isItemConfirmed is provided', () => {
      const isItemConfirmed = jest.fn().mockReturnValue(true);
      render(<MismatchAnalyzerDataTable {...defaultProps} isItemConfirmed={isItemConfirmed} />);

      // Should have a "Status" column header
      expect(screen.getByText('Status')).toBeInTheDocument();

      // Should show confirmed status (multiple elements expected)
      const confirmedElements = screen.getAllByText('✅ Confirmed');
      expect(confirmedElements).toHaveLength(2); // One for each data item
    });

    test('shows unconfirmed status for non-confirmed items', () => {
      const isItemConfirmed = jest.fn().mockReturnValue(false);
      render(<MismatchAnalyzerDataTable {...defaultProps} isItemConfirmed={isItemConfirmed} />);

      // Should show unconfirmed status (multiple elements expected)
      const unconfirmedElements = screen.getAllByText('⚠️ Unconfirmed');
      expect(unconfirmedElements).toHaveLength(2); // One for each data item
    });

    test('handles item selection correctly', () => {
      const onItemSelection = jest.fn();
      const selectedItems = new Set<string>();

      render(
        <MismatchAnalyzerDataTable
          {...defaultProps}
          onItemSelection={onItemSelection}
          selectedItems={selectedItems}
        />
      );

      const checkboxes = screen.getAllByRole('checkbox');
      // Click the first row checkbox (index 0, since there's no "Select All" checkbox)
      fireEvent.click(checkboxes[0]);

      expect(onItemSelection).toHaveBeenCalledWith('razor:test razor 1', true);
    });

    test('reflects selected state in checkboxes', () => {
      const onItemSelection = jest.fn();
      const selectedItems = new Set<string>(['razor:test razor 1']);

      render(
        <MismatchAnalyzerDataTable
          {...defaultProps}
          onItemSelection={onItemSelection}
          selectedItems={selectedItems}
        />
      );

      const checkboxes = screen.getAllByRole('checkbox');
      // The first row checkbox (index 0) should be checked
      expect(checkboxes[0]).toBeChecked();
      // The second row checkbox (index 1) should not be checked
      expect(checkboxes[1]).not.toBeChecked();
    });

    test('does not render selection or status columns when props are not provided', () => {
      render(<MismatchAnalyzerDataTable {...defaultProps} />);

      // Should not have Select or Status columns
      expect(screen.queryByText('Select')).not.toBeInTheDocument();
      expect(screen.queryByText('Status')).not.toBeInTheDocument();
    });

    test('shows confirmed status for confirmed items', () => {
      const confirmedData = [
        {
          original: 'Confirmed Item A',
          matched: { brand: 'Brand A', model: 'Model A' },
          mismatch_type: 'good_match',
          match_type: 'regex',
          pattern: 'pattern_a',
          confidence: 0.8,
          count: 1,
          comment_ids: ['id1'],
          examples: ['example1'],
        },
      ];

      // Deterministic mock function based on input, not call order
      const isItemConfirmed = jest.fn((item: MismatchItem) => {
        return item.original === 'Confirmed Item A';
      });

      render(
        <MismatchAnalyzerDataTable
          data={confirmedData}
          field='razor'
          onCommentClick={mockOnCommentClick}
          isItemConfirmed={isItemConfirmed}
        />
      );

      expect(screen.getByText('✅ Confirmed')).toBeInTheDocument();
    });

    test('shows unconfirmed status for unconfirmed items', () => {
      const unconfirmedData = [
        {
          original: 'Unconfirmed Item B',
          matched: { brand: 'Brand B', model: 'Model B' },
          mismatch_type: 'potential_mismatch',
          match_type: 'regex',
          pattern: 'pattern_b',
          confidence: 0.6,
          count: 1,
          comment_ids: ['id2'],
          examples: ['example2'],
        },
      ];

      // Deterministic mock function based on input, not call order
      const isItemConfirmed = jest.fn((item: MismatchItem) => {
        return item.original === 'Confirmed Item A'; // Will return false for this item
      });

      render(
        <MismatchAnalyzerDataTable
          data={unconfirmedData}
          field='razor'
          onCommentClick={mockOnCommentClick}
          isItemConfirmed={isItemConfirmed}
        />
      );

      expect(screen.getByText('⚠️ Unconfirmed')).toBeInTheDocument();
    });
  });

  describe('MismatchAnalyzerDataTable with Handle and Knot Columns', () => {
    test('shows handle and knot columns for brush fields', () => {
      // Known brush data (has top-level brand/model)
      const knownBrushData: MismatchItem[] = [
        {
          original: 'Omega 10049',
          matched: {
            brand: 'Omega',
            model: '10049',
            format: 'Boar',
          },
          pattern: 'omega.*(pro)*.*49',
          match_type: 'regex',
          confidence: 0.9,
          mismatch_type: 'good_match',
          reason: 'Good match found',
          count: 8,
          examples: ['2025-06.json'],
          comment_ids: ['mvepnsn', 'mvqyczm', 'mxjl2io'],
          is_confirmed: true,
        },
      ];

      // Split brush data (no top-level brand/model)
      const splitBrushData: MismatchItem[] = [
        {
          original: 'Declaration B2 in Mozingo handle',
          matched: {
            handle: {
              brand: 'Mozingo',
              model: 'Custom',
              _pattern: 'mozingo.*handle',
            },
            knot: {
              brand: 'Declaration',
              model: 'B2',
              _pattern: 'declaration.*b2',
            },
          },
          pattern: 'declaration.*b2.*mozingo.*handle',
          match_type: 'regex',
          confidence: 0.8,
          mismatch_type: 'potential_mismatch',
          reason: 'Multiple patterns found',
          count: 3,
          examples: ['2025-06.json'],
          comment_ids: ['abc123', 'def456'],
          is_confirmed: false,
        },
      ];

      // Test known brush (should show handle/knot columns for brush field)
      const { rerender } = render(
        <MismatchAnalyzerDataTable
          data={knownBrushData}
          field='brush'
          onCommentClick={mockOnCommentClick}
        />
      );

      // Should show brush pattern column AND handle/knot pattern columns for brush field
      expect(screen.getByText('Type')).toBeInTheDocument();
      expect(screen.getByText('Handle Pattern')).toBeInTheDocument();
      expect(screen.getByText('Knot Pattern')).toBeInTheDocument();

      // Test split brush (should also show handle/knot columns)
      rerender(
        <MismatchAnalyzerDataTable
          data={splitBrushData}
          field='brush'
          onCommentClick={mockOnCommentClick}
        />
      );

      // Should show handle/knot pattern columns
      expect(screen.getByText('Handle Pattern')).toBeInTheDocument();
      expect(screen.getByText('Knot Pattern')).toBeInTheDocument();
    });

    test('displays correct icon and text for exact_matches type', () => {
      const exactMatchData: MismatchItem[] = [
        {
          original: 'Gillette Super Speed',
          matched: {
            brand: 'Gillette',
            model: 'Super Speed',
            format: 'DE',
          },
          pattern: 'gillette.*super.*speed',
          match_type: 'exact',
          confidence: 1.0,
          mismatch_type: 'exact_matches',
          reason: 'Exact match from correct_matches.yaml',
          count: 5,
          examples: ['2025-06.json'],
          comment_ids: ['abc123'],
          is_confirmed: true,
        },
      ];

      render(
        <MismatchAnalyzerDataTable
          data={exactMatchData}
          field='razor'
          onCommentClick={mockOnCommentClick}
        />
      );

      // Should show ✅ icon and "Exact Match" text
      expect(screen.getByText('✅')).toBeInTheDocument();
      expect(screen.getByText('Exact Match')).toBeInTheDocument();
    });

    test('displays correct brush data for complete vs split brushes', () => {
      // Complete brush data (has top-level brand/model)
      const completeBrushData: MismatchItem[] = [
        {
          original: 'Simpson Chubby 2 Best Badger',
          matched: {
            brand: 'Simpson',
            model: 'Chubby 2',
            fiber: 'best_badger',
            knot_size_mm: 27.0,
            handle_maker: 'Simpson',
          },
          pattern: 'simpson.*chubby.*2',
          match_type: 'exact',
          confidence: 1.0,
          mismatch_type: 'exact_matches',
          reason: 'Exact match from catalog',
          count: 5,
          examples: ['2025-06.json'],
          comment_ids: ['abc123'],
          is_confirmed: true,
        },
      ];

      // Split brush data (no top-level brand/model, has handle/knot components)
      const splitBrushData: MismatchItem[] = [
        {
          original: 'Declaration B2 in Mozingo handle',
          matched: {
            handle: {
              brand: 'Mozingo',
              model: 'Custom',
              _pattern: 'mozingo.*handle',
            },
            knot: {
              brand: 'Declaration',
              model: 'B2',
              _pattern: 'declaration.*b2',
            },
          },
          pattern: 'declaration.*b2.*mozingo.*handle',
          match_type: 'regex',
          confidence: 0.8,
          mismatch_type: 'potential_mismatch',
          reason: 'Multiple patterns found',
          count: 3,
          examples: ['2025-06.json'],
          comment_ids: ['def456'],
          is_confirmed: false,
          is_split_brush: true,
          handle_component: 'Mozingo handle',
          knot_component: 'Declaration B2',
        },
      ];

      // Test complete brush - should show brand/model in "Matched" column
      const { rerender } = render(
        <MismatchAnalyzerDataTable
          data={completeBrushData}
          field='brush'
          onCommentClick={mockOnCommentClick}
        />
      );

      // Complete brush should show brand-model-fiber-size format
      // Look specifically for the matched data format (not the original)
      expect(
        screen.getByText('Simpson - Chubby 2 - best_badger - 27mm - Simpson')
      ).toBeInTheDocument();

      // Test split brush - should show handle/knot components in "Matched" column
      rerender(
        <MismatchAnalyzerDataTable
          data={splitBrushData}
          field='brush'
          onCommentClick={mockOnCommentClick}
        />
      );

      // Split brush should show handle/knot format
      expect(screen.getByText('Handle: Mozingo - Custom')).toBeInTheDocument();
      expect(screen.getByText('Knot: Declaration - B2')).toBeInTheDocument();

      // Split brush should show the new brush pattern format
      // Use getAllByText since there might be multiple elements with similar content
      // The component renders "Handle: Mozingo - Custom" and "Knot: Declaration - B2"
      // Verify that the split brush data is properly displayed

      // The handle and knot text is already verified above with the exact text
      // No need for additional fuzzy matching tests
    });

    test('displays brush type column with correct validation', () => {
      const brushData: MismatchItem[] = [
        {
          original: 'Simpson Chubby 2 Best Badger',
          matched: {
            brand: 'Simpson',
            model: 'Chubby 2',
            fiber: 'best_badger',
            knot_size_mm: 27.0,
            handle_maker: 'Simpson',
          },
          pattern: 'simpson.*chubby.*2',
          match_type: 'exact',
          confidence: 1.0,
          mismatch_type: 'exact_matches',
          reason: 'Exact match from catalog',
          count: 5,
          examples: ['2025-06.json'],
          comment_ids: ['abc123'],
          is_confirmed: true,
        },
        {
          original: 'Declaration B2 in Declaration handle',
          matched: {
            handle: {
              brand: 'Declaration',
              model: 'Custom',
              _pattern: 'declaration.*handle',
            },
            knot: {
              brand: 'Declaration',
              model: 'B2',
              _pattern: 'declaration.*b2',
            },
          },
          pattern: 'declaration.*b2.*declaration.*handle',
          match_type: 'regex',
          confidence: 0.8,
          mismatch_type: 'potential_mismatch',
          reason: 'Multiple patterns found',
          count: 3,
          examples: ['2025-06.json'],
          comment_ids: ['def456'],
          is_confirmed: false,
          handle_component: 'Declaration handle',
          knot_component: 'Declaration B2',
        },
      ];

      render(
        <MismatchAnalyzerDataTable
          data={brushData}
          field='brush'
          onCommentClick={mockOnCommentClick}
        />
      );

      // Should show "Brush Type" column header (use getAllByText and check for the header specifically)
      const brushTypeElements = screen.getAllByText('Brush Type');
      expect(brushTypeElements.length).toBeGreaterThan(0);

      // Should show "Complete" for the first item
      expect(screen.getByText('Complete')).toBeInTheDocument();
      // Should show "ERROR" for the second item (same brands but no top-level brand/model)
      expect(screen.getByText('ERROR')).toBeInTheDocument();
    });

    test('does not show enrich adjustment icon when there are no changes', async () => {
      const brushData: MismatchItem[] = [
        {
          original: 'Simpson Chubby 2 Best Badger',
          matched: {
            brand: 'Simpson',
            model: 'Chubby 2',
            fiber: 'best_badger',
            knot_size_mm: 27.0,
            handle_maker: 'Simpson',
          },
          pattern: 'simpson.*chubby.*2',
          match_type: 'exact',
          confidence: 1.0,
          mismatch_type: 'exact_matches',
          reason: 'Exact match from catalog',
          count: 5,
          examples: ['2025-06.json'],
          comment_ids: ['abc123'],
          is_confirmed: true,
        },
      ];

      await act(async () => {
        render(
          <MismatchAnalyzerDataTable
            data={brushData}
            field='brush'
            onCommentClick={mockOnCommentClick}
          />
        );
      });

      // Should not show the enrich adjustment icon
      expect(screen.queryByText('🔗 enrich')).not.toBeInTheDocument();
    });

    test('shows enrich adjustment icon when there are actual changes', async () => {
      const brushData: MismatchItem[] = [
        {
          original: 'Zenith 506U N (50/50 horse mane/tail)',
          matched: {
            brand: 'Zenith',
            model: '506U SE',
            knot: {
              brand: 'Zenith',
              model: '506U SE',
              fiber: 'Boar', // Matched as Boar
              knot_size_mm: 27,
            },
          },
          enriched: {
            fiber: 'Horse', // Enriched as Horse (different!)
          },
          pattern: '506u',
          match_type: 'regex',
          confidence: 0.8,
          mismatch_type: 'regex_match',
          reason: 'Regex match',
          count: 1,
          examples: ['2025-06.json'],
          comment_ids: ['abc123'],
          is_confirmed: false,
        },
      ];

      await act(async () => {
        render(
          <MismatchAnalyzerDataTable
            data={brushData}
            field='brush'
            onCommentClick={mockOnCommentClick}
          />
        );
      });

      // Should show the enrich adjustment icon
      expect(screen.getByText('🔄')).toBeInTheDocument();
    });

    test('shows enrich adjustment icon when knot_size_mm changes from null to value', async () => {
      const brushData: MismatchItem[] = [
        {
          original: 'C&H + TnS 27mm H8',
          matched: {
            brand: 'Turn-N-Shave',
            model: 'High Density Badger (H*)',
            knot: {
              brand: 'Turn-N-Shave',
              model: 'High Density Badger (H*)',
              fiber: 'Badger',
              knot_size_mm: null, // Matched as null
            },
          },
          enriched: {
            knot_size_mm: 27.0, // Enriched as 27.0 (different!)
          },
          pattern: 't[&n]s.*h\\d',
          match_type: 'regex',
          confidence: 0.8,
          mismatch_type: 'levenshtein_distance',
          reason: 'Levenshtein distance',
          count: 1,
          examples: ['2025-06.json'],
          comment_ids: ['abc123'],
          is_confirmed: false,
        },
      ];

      await act(async () => {
        render(
          <MismatchAnalyzerDataTable
            data={brushData}
            field='brush'
            onCommentClick={mockOnCommentClick}
          />
        );
      });

      // Should show the enrich adjustment icon
      expect(screen.getByText('🔄')).toBeInTheDocument();
    });

    test('does not show enrich adjustment icon for Bristle Brushworks B9B (no actual changes)', async () => {
      const brushData: MismatchItem[] = [
        {
          original: 'Bristle Brushworks B9B',
          matched: {
            brand: 'Declaration Grooming',
            model: 'B9B',
            knot: {
              brand: 'Declaration Grooming',
              model: 'B9B',
              fiber: 'Badger',
              knot_size_mm: 28, // Matched has knot_size_mm: 28
            },
          },
          enriched: {
            fiber: 'Badger', // Enriched only has fiber, no knot_size_mm
          },
          pattern: '(declaration|\\bdg\\b)?.*\\bb9b\\+?\\b',
          match_type: 'regex',
          confidence: 0.8,
          mismatch_type: 'exact_matches',
          reason: 'Exact match',
          count: 1,
          examples: ['2025-06.json'],
          comment_ids: ['abc123'],
          is_confirmed: true,
        },
      ];

      await act(async () => {
        render(
          <MismatchAnalyzerDataTable
            data={brushData}
            field='brush'
            onCommentClick={mockOnCommentClick}
          />
        );
      });

      // Should NOT show the enrich adjustment icon since there are no actual changes
      expect(screen.queryByText('🔄')).not.toBeInTheDocument();
    });
  });
});
