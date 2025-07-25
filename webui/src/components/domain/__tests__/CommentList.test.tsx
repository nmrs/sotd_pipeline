import { render, screen, fireEvent } from '@testing-library/react';
import { CommentList } from '../CommentList';

// Test utilities for CommentList
export const createMockCommentListProps = (overrides = {}) => ({
  commentIds: ['abc123', 'def456'],
  onCommentClick: jest.fn(),
  commentLoading: false,
  maxDisplay: 3,
  ...overrides,
});

describe('CommentList', () => {
  test('renders empty state when no comment IDs provided', () => {
    render(<CommentList commentIds={[]} onCommentClick={jest.fn()} />);
    expect(screen.getByText('No comments')).toBeInTheDocument();
  });

  test('renders single comment ID as clickable button', () => {
    const mockOnCommentClick = jest.fn();
    render(<CommentList commentIds={['abc123']} onCommentClick={mockOnCommentClick} />);

    expect(screen.getByText('abc123')).toBeInTheDocument();
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  test('calls onCommentClick when comment ID is clicked', () => {
    const mockOnCommentClick = jest.fn();
    render(<CommentList commentIds={['abc123']} onCommentClick={mockOnCommentClick} />);

    fireEvent.click(screen.getByText('abc123'));
    expect(mockOnCommentClick).toHaveBeenCalledWith('abc123');
  });

  test('renders multiple comment IDs up to maxDisplay limit', () => {
    const mockOnCommentClick = jest.fn();
    render(
      <CommentList
        commentIds={['abc123', 'def456', 'ghi789']}
        onCommentClick={mockOnCommentClick}
        maxDisplay={2}
      />
    );

    expect(screen.getByText('abc123')).toBeInTheDocument();
    expect(screen.getByText('def456')).toBeInTheDocument();
    expect(screen.queryByText('ghi789')).not.toBeInTheDocument();
  });

  test('shows "+X more" indicator when exceeding maxDisplay', () => {
    const mockOnCommentClick = jest.fn();
    render(
      <CommentList
        commentIds={['abc123', 'def456', 'ghi789', 'jkl012']}
        onCommentClick={mockOnCommentClick}
        maxDisplay={2}
      />
    );

    expect(screen.getByText('+2 more')).toBeInTheDocument();
  });

  test('handles loading state correctly', () => {
    const mockOnCommentClick = jest.fn();
    render(
      <CommentList
        commentIds={['abc123']}
        onCommentClick={mockOnCommentClick}
        commentLoading={true}
      />
    );

    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
  });

  test('handles null/undefined commentIds gracefully', () => {
    render(<CommentList commentIds={null as unknown as string[]} onCommentClick={jest.fn()} />);
    expect(screen.getByText('No comments')).toBeInTheDocument();
  });

  test('handles empty string comment IDs', () => {
    render(<CommentList commentIds={['', 'abc123', '']} onCommentClick={jest.fn()} />);
    expect(screen.getByText('abc123')).toBeInTheDocument();
    // Check that no empty strings are rendered as buttons
    const buttons = screen.getAllByRole('button');
    buttons.forEach(button => {
      expect(button.textContent).not.toBe('');
    });
  });

  test('handles very long comment IDs', () => {
    const longCommentId = 'a'.repeat(100);
    const mockOnCommentClick = jest.fn();
    render(<CommentList commentIds={[longCommentId]} onCommentClick={mockOnCommentClick} />);

    expect(screen.getByText(longCommentId)).toBeInTheDocument();
  });

  test('handles missing onCommentClick prop gracefully', () => {
    const props = createMockCommentListProps({
      onCommentClick: undefined as unknown as (commentId: string) => void,
    });
    render(<CommentList {...props} />);

    // Should not throw error when clicking
    const buttons = screen.getAllByRole('button');
    expect(() => fireEvent.click(buttons[0])).not.toThrow();
  });

  test('handles undefined onCommentClick with optional chaining', () => {
    // Test the specific case where onCommentClick is undefined
    render(
      <CommentList
        commentIds={['abc123']}
        onCommentClick={undefined as unknown as (commentId: string) => void}
      />
    );

    const button = screen.getByRole('button');
    // This should not throw and should execute the optional chaining
    expect(() => fireEvent.click(button)).not.toThrow();
  });

  test('supports keyboard navigation', () => {
    const mockOnCommentClick = jest.fn();
    render(<CommentList commentIds={['abc123', 'def456']} onCommentClick={mockOnCommentClick} />);

    const firstButton = screen.getByText('abc123');

    // Test that button is focusable and clickable
    firstButton.focus();
    expect(firstButton).toHaveFocus();

    // Test click works
    fireEvent.click(firstButton);
    expect(mockOnCommentClick).toHaveBeenCalledWith('abc123');

    // Test that buttons are accessible via keyboard (Tab navigation)
    const buttons = screen.getAllByRole('button');
    expect(buttons).toHaveLength(2);

    // Test that buttons are focusable
    buttons.forEach(button => {
      button.focus();
      expect(button).toHaveFocus();
    });
  });

  test('has proper ARIA labels and roles', () => {
    const mockOnCommentClick = jest.fn();
    render(
      <CommentList
        commentIds={['abc123', 'def456']}
        onCommentClick={mockOnCommentClick}
        aria-label='Comment list'
      />
    );

    const container = screen.getByLabelText('Comment list');
    expect(container).toBeInTheDocument();

    const buttons = screen.getAllByRole('button');
    expect(buttons[0]).toHaveAttribute('aria-label', 'View comment 1 of 2');
    expect(buttons[1]).toHaveAttribute('aria-label', 'View comment 2 of 2');
  });

  test('handles custom maxDisplay values', () => {
    const mockOnCommentClick = jest.fn();
    render(
      <CommentList
        commentIds={['abc123', 'def456', 'ghi789']}
        onCommentClick={mockOnCommentClick}
        maxDisplay={1}
      />
    );

    expect(screen.getByText('abc123')).toBeInTheDocument();
    expect(screen.queryByText('def456')).not.toBeInTheDocument();
    expect(screen.getByText('+2 more')).toBeInTheDocument();
  });

  test('does not show "+X more" when all comments are displayed', () => {
    const mockOnCommentClick = jest.fn();
    render(
      <CommentList
        commentIds={['abc123', 'def456']}
        onCommentClick={mockOnCommentClick}
        maxDisplay={3}
      />
    );

    expect(screen.getByText('abc123')).toBeInTheDocument();
    expect(screen.getByText('def456')).toBeInTheDocument();
    expect(screen.queryByText(/\+.*more/)).not.toBeInTheDocument();
  });
});
