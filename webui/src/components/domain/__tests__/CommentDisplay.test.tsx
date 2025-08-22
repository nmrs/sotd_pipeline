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
        className="custom-class"
      />
    );

    expect(container.firstChild).toHaveClass('custom-class');
  });
});
