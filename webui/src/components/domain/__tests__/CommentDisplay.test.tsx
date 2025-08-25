import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { CommentDisplay } from '../CommentDisplay';

describe('CommentDisplay', () => {
  const mockOnCommentClick = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders empty state when no comment IDs provided', () => {
    render(<CommentDisplay commentIds={[]} onCommentClick={mockOnCommentClick} />);
    expect(screen.getByText('-')).toBeInTheDocument();
  });

  test('renders single comment ID as clickable button', () => {
    render(<CommentDisplay commentIds={['abc123']} onCommentClick={mockOnCommentClick} />);
    expect(screen.getByText('abc123')).toBeInTheDocument();
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  test('renders multiple comment IDs up to maxDisplay limit', () => {
    render(
      <CommentDisplay
        commentIds={['abc123', 'def456', 'ghi789']}
        onCommentClick={mockOnCommentClick}
        maxDisplay={2}
      />
    );

    expect(screen.getByText('abc123')).toBeInTheDocument();
    expect(screen.getByText('def456')).toBeInTheDocument();
    expect(screen.queryByText('ghi789')).not.toBeInTheDocument();
  });

  test('shows "+X more" link when exceeding maxDisplay', () => {
    render(
      <CommentDisplay
        commentIds={['abc123', 'def456', 'ghi789', 'jkl012']}
        onCommentClick={mockOnCommentClick}
        maxDisplay={3}
      />
    );

    expect(screen.getByText('+1 more')).toBeInTheDocument();
  });

  test('expands to show all comments when "+X more" is clicked', () => {
    render(
      <CommentDisplay
        commentIds={['abc123', 'def456', 'ghi789', 'jkl012']}
        onCommentClick={mockOnCommentClick}
        maxDisplay={3}
      />
    );

    // Should show first 3 comments initially
    expect(screen.getByText('abc123')).toBeInTheDocument();
    expect(screen.getByText('def456')).toBeInTheDocument();
    expect(screen.getByText('ghi789')).toBeInTheDocument();
    expect(screen.queryByText('jkl012')).not.toBeInTheDocument();

    // Click "+1 more" to expand
    fireEvent.click(screen.getByText('+1 more'));

    // Should now show all comments
    expect(screen.getByText('abc123')).toBeInTheDocument();
    expect(screen.getByText('def456')).toBeInTheDocument();
    expect(screen.getByText('ghi789')).toBeInTheDocument();
    expect(screen.getByText('jkl012')).toBeInTheDocument();

    // Should show "Show less" button
    expect(screen.getByText('Show less')).toBeInTheDocument();
    expect(screen.queryByText('+1 more')).not.toBeInTheDocument();
  });

  test('collapses back when "Show less" is clicked', () => {
    render(
      <CommentDisplay
        commentIds={['abc123', 'def456', 'ghi789', 'jkl012']}
        onCommentClick={mockOnCommentClick}
        maxDisplay={3}
      />
    );

    // Expand first
    fireEvent.click(screen.getByText('+1 more'));
    expect(screen.getByText('jkl012')).toBeInTheDocument();

    // Collapse back
    fireEvent.click(screen.getByText('Show less'));
    expect(screen.queryByText('jkl012')).not.toBeInTheDocument();
    expect(screen.getByText('+1 more')).toBeInTheDocument();
  });

  test('calls onCommentClick when comment ID is clicked', () => {
    render(<CommentDisplay commentIds={['abc123']} onCommentClick={mockOnCommentClick} />);

    fireEvent.click(screen.getByText('abc123'));
    expect(mockOnCommentClick).toHaveBeenCalledWith('abc123');
  });

  test('handles loading state correctly', () => {
    render(
      <CommentDisplay
        commentIds={['abc123', 'def456']}
        onCommentClick={mockOnCommentClick}
        commentLoading={true}
      />
    );

    const buttons = screen.getAllByRole('button');
    buttons.forEach(button => {
      expect(button).toBeDisabled();
    });
  });

  test('filters out empty comment IDs', () => {
    render(
      <CommentDisplay
        commentIds={['abc123', '', 'def456', '   ', 'ghi789']}
        onCommentClick={mockOnCommentClick}
        maxDisplay={2}
      />
    );

    // Should only show valid comment IDs
    expect(screen.getByText('abc123')).toBeInTheDocument();
    expect(screen.getByText('def456')).toBeInTheDocument();
    expect(screen.queryByText('ghi789')).not.toBeInTheDocument();
    expect(screen.getByText('+1 more')).toBeInTheDocument();
  });

  test('applies custom className', () => {
    const { container } = render(
      <CommentDisplay
        commentIds={['abc123']}
        onCommentClick={mockOnCommentClick}
        className='custom-class'
      />
    );

    expect(container.firstChild).toHaveClass('custom-class');
  });

  // New tests for date display functionality
  describe('Date Display Mode', () => {
    test('renders dates when displayMode is "dates" and dates are provided', () => {
      const dates = ['2024-01-15', '2024-01-18', '2024-01-22'];
      render(
        <CommentDisplay
          commentIds={['abc123', 'def456', 'ghi789']}
          onCommentClick={mockOnCommentClick}
          displayMode='dates'
          dates={dates}
        />
      );

      expect(screen.getByText('Jan 15')).toBeInTheDocument();
      expect(screen.getByText('Jan 18')).toBeInTheDocument();
      expect(screen.getByText('Jan 22')).toBeInTheDocument();
    });

    test('calls onCommentClick with correct comment ID when date is clicked', () => {
      const dates = ['2024-01-15', '2024-01-18'];
      const commentIds = ['abc123', 'def456'];

      render(
        <CommentDisplay
          commentIds={commentIds}
          onCommentClick={mockOnCommentClick}
          displayMode='dates'
          dates={dates}
        />
      );

      fireEvent.click(screen.getByText('Jan 15'));
      expect(mockOnCommentClick).toHaveBeenCalledWith('abc123');

      fireEvent.click(screen.getByText('Jan 18'));
      expect(mockOnCommentClick).toHaveBeenCalledWith('def456');
    });

    test('handles expand/collapse with dates correctly', () => {
      const dates = ['2024-01-15', '2024-01-18', '2024-01-22', '2024-01-25'];
      const commentIds = ['abc123', 'def456', 'ghi789', 'jkl012'];

      render(
        <CommentDisplay
          commentIds={commentIds}
          onCommentClick={mockOnCommentClick}
          displayMode='dates'
          dates={dates}
          maxDisplay={2}
        />
      );

      // Should show first 2 dates initially
      expect(screen.getByText('Jan 15')).toBeInTheDocument();
      expect(screen.getByText('Jan 18')).toBeInTheDocument();
      expect(screen.queryByText('Jan 22')).not.toBeInTheDocument();
      expect(screen.queryByText('Jan 25')).not.toBeInTheDocument();

      // Click "+2 more" to expand
      fireEvent.click(screen.getByText('+2 more'));

      // Should now show all dates
      expect(screen.getByText('Jan 15')).toBeInTheDocument();
      expect(screen.getByText('Jan 18')).toBeInTheDocument();
      expect(screen.getByText('Jan 22')).toBeInTheDocument();
      expect(screen.getByText('Jan 25')).toBeInTheDocument();
    });

    test('falls back to comment IDs when dates array is shorter than commentIds', () => {
      const dates = ['2024-01-15']; // Only 1 date for 2 comment IDs
      const commentIds = ['abc123', 'def456'];

      render(
        <CommentDisplay
          commentIds={commentIds}
          onCommentClick={mockOnCommentClick}
          displayMode='dates'
          dates={dates}
        />
      );

      // Should show the date for the first comment
      expect(screen.getByText('Jan 15')).toBeInTheDocument();
      // Should show comment ID for the second comment (fallback)
      expect(screen.getByText('def456')).toBeInTheDocument();
    });

    test('falls back to comment IDs when dates array is empty', () => {
      const dates: string[] = [];
      const commentIds = ['abc123', 'def456'];

      render(
        <CommentDisplay
          commentIds={commentIds}
          onCommentClick={mockOnCommentClick}
          displayMode='dates'
          dates={dates}
        />
      );

      // Should fall back to showing comment IDs
      expect(screen.getByText('abc123')).toBeInTheDocument();
      expect(screen.getByText('def456')).toBeInTheDocument();
    });

    test('formats dates correctly for different months and years', () => {
      const dates = ['2024-01-15', '2024-12-25', '2023-06-10'];
      const commentIds = ['abc123', 'def456', 'ghi789'];

      render(
        <CommentDisplay
          commentIds={commentIds}
          onCommentClick={mockOnCommentClick}
          displayMode='dates'
          dates={dates}
        />
      );

      expect(screen.getByText('Jan 15')).toBeInTheDocument();
      expect(screen.getByText('Dec 25')).toBeInTheDocument();
      expect(screen.getByText('Jun 10')).toBeInTheDocument();
    });

    test('maintains loading state when displaying dates', () => {
      const dates = ['2024-01-15', '2024-01-18'];
      const commentIds = ['abc123', 'def456'];

      render(
        <CommentDisplay
          commentIds={commentIds}
          onCommentClick={mockOnCommentClick}
          displayMode='dates'
          dates={dates}
          commentLoading={true}
        />
      );

      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        expect(button).toBeDisabled();
      });
    });
  });

  describe('Synchronized Expand/Collapse', () => {
    test('should use external expanded state when provided', () => {
      const onExpandChange = jest.fn();
      render(
        <CommentDisplay
          commentIds={['abc123', 'def456', 'ghi789', 'jkl012']}
          onCommentClick={mockOnCommentClick}
          expanded={true}
          onExpandChange={onExpandChange}
        />
      );

      // Should show "Show less" button when externally expanded
      expect(screen.getByText('Show less')).toBeInTheDocument();
      expect(screen.queryByText('+1 more')).not.toBeInTheDocument();
    });

    test('should call onExpandChange when expand/collapse buttons are clicked', () => {
      const onExpandChange = jest.fn();
      render(
        <CommentDisplay
          commentIds={['abc123', 'def456', 'ghi789', 'jkl012']}
          onCommentClick={mockOnCommentClick}
          expanded={false}
          onExpandChange={onExpandChange}
        />
      );

      // Click expand button
      const expandButton = screen.getByText('+1 more');
      fireEvent.click(expandButton);
      expect(onExpandChange).toHaveBeenCalledWith(true);

      // Reset mock
      onExpandChange.mockClear();

      // Update to expanded state
      render(
        <CommentDisplay
          commentIds={['abc123', 'def456', 'ghi789', 'jkl012']}
          onCommentClick={mockOnCommentClick}
          expanded={true}
          onExpandChange={onExpandChange}
        />
      );

      // Click collapse button
      const collapseButton = screen.getByText('Show less');
      fireEvent.click(collapseButton);
      expect(onExpandChange).toHaveBeenCalledWith(false);
    });

    test('should fall back to internal state when no external control provided', () => {
      render(
        <CommentDisplay
          commentIds={['abc123', 'def456', 'ghi789', 'jkl012']}
          onCommentClick={mockOnCommentClick}
        />
      );

      // Initially collapsed
      expect(screen.getByText('+1 more')).toBeInTheDocument();

      // Click expand
      const expandButton = screen.getByText('+1 more');
      fireEvent.click(expandButton);

      // Should now show collapse button
      expect(screen.getByText('Show less')).toBeInTheDocument();
      expect(screen.queryByText('+1 more')).not.toBeInTheDocument();
    });
  });
});
