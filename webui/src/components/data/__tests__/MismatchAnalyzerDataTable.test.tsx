import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import MismatchAnalyzerDataTable from '../MismatchAnalyzerDataTable';
import { MismatchItem } from '../../../services/api';

// Mock the CommentList component
jest.mock('../../domain/CommentList', () => {
  return {
    CommentList: ({
      commentIds,
      onCommentClick,
      commentLoading,
      maxDisplay,
      'aria-label': ariaLabel,
    }: any) => (
      <div data-testid='comment-list' aria-label={ariaLabel}>
        {commentIds.map((id: string, index: number) => (
          <button
            key={id}
            onClick={() => onCommentClick?.(id)}
            disabled={commentLoading}
            aria-label={`View comment ${index + 1} of ${commentIds.length}`}
          >
            {id}
          </button>
        ))}
      </div>
    ),
  };
});

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
  },
];

describe('MismatchAnalyzerDataTable', () => {
  const defaultProps = {
    data: mockData,
    onCommentClick: jest.fn(),
    commentLoading: false,
  };

  describe('MismatchAnalyzerDataTable with CommentList Integration', () => {
    test('renders CommentList component in comments column', () => {
      render(<MismatchAnalyzerDataTable {...defaultProps} />);

      const commentLists = screen.getAllByTestId('comment-list');
      expect(commentLists).toHaveLength(2);
    });

    test('passes correct props to CommentList component', () => {
      render(<MismatchAnalyzerDataTable {...defaultProps} />);

      const commentLists = screen.getAllByTestId('comment-list');
      expect(commentLists[0]).toHaveAttribute('aria-label', '2 comments available');
      expect(commentLists[1]).toHaveAttribute('aria-label', '1 comment available');
    });

    test('handles empty comment_ids array', () => {
      const dataWithEmptyComments = [{ ...mockData[0], comment_ids: [] }];

      render(<MismatchAnalyzerDataTable {...defaultProps} data={dataWithEmptyComments} />);

      const commentList = screen.getByTestId('comment-list');
      expect(commentList).toHaveAttribute('aria-label', '0 comments available');
    });

    test('passes commentLoading prop to CommentList', () => {
      render(<MismatchAnalyzerDataTable {...defaultProps} commentLoading={true} />);

      const commentLists = screen.getAllByTestId('comment-list');
      const buttons = commentLists[0].querySelectorAll('button');
      buttons.forEach(button => {
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

      // Should have checkboxes for each row plus the "Select All" checkbox
      const checkboxes = screen.getAllByRole('checkbox');
      expect(checkboxes).toHaveLength(3); // One "Select All" + one for each visible data item (2 items in test data)
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
      const selectedItems = new Set();

      render(
        <MismatchAnalyzerDataTable
          {...defaultProps}
          onItemSelection={onItemSelection}
          selectedItems={selectedItems}
        />
      );

      const checkboxes = screen.getAllByRole('checkbox');
      // Click the first row checkbox (index 1, since index 0 is the "Select All" checkbox)
      fireEvent.click(checkboxes[1]);

      expect(onItemSelection).toHaveBeenCalledWith(
        'Test Razor 1|{"brand":"Test Brand","model":"Model 1"}',
        true
      );
    });

    test('reflects selected state in checkboxes', () => {
      const onItemSelection = jest.fn();
      const selectedItems = new Set(['Test Razor 1|{"brand":"Test Brand","model":"Model 1"}']);

      render(
        <MismatchAnalyzerDataTable
          {...defaultProps}
          onItemSelection={onItemSelection}
          selectedItems={selectedItems}
        />
      );

      const checkboxes = screen.getAllByRole('checkbox');
      // The "Select All" checkbox (index 0) should be indeterminate since only one item is selected
      expect(checkboxes[0]).not.toBeChecked();
      // The first row checkbox (index 1) should be checked
      expect(checkboxes[1]).toBeChecked();
      // The second row checkbox (index 2) should not be checked
      expect(checkboxes[2]).not.toBeChecked();
    });

    test('does not render selection or status columns when props are not provided', () => {
      render(<MismatchAnalyzerDataTable {...defaultProps} />);

      // Should not have Select or Status columns
      expect(screen.queryByText('Select')).not.toBeInTheDocument();
      expect(screen.queryByText('Status')).not.toBeInTheDocument();
    });

    test('handles mixed confirmation status', () => {
      const isItemConfirmed = jest
        .fn()
        .mockReturnValueOnce(true) // First item confirmed
        .mockReturnValueOnce(false); // Second item unconfirmed

      render(<MismatchAnalyzerDataTable {...defaultProps} isItemConfirmed={isItemConfirmed} />);

      expect(screen.getByText('✅ Confirmed')).toBeInTheDocument();
      expect(screen.getByText('⚠️ Unconfirmed')).toBeInTheDocument();
    });
  });
});
