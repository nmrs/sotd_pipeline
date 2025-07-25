import { render, screen, fireEvent } from '@testing-library/react';
import { CommentList } from '../CommentList';

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
});
