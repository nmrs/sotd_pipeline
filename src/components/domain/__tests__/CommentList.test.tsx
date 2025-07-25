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
    describe('Rendering Tests', () => {
        test('renders empty state when no comment IDs provided', () => {
            const props = createMockCommentListProps({ commentIds: [] });
            render(<CommentList {...props} />);

            expect(screen.getByText('No comments')).toBeInTheDocument();
        });

        test('renders single comment ID as clickable button', () => {
            const props = createMockCommentListProps({ commentIds: ['abc123'] });
            render(<CommentList {...props} />);

            expect(screen.getByText('abc123')).toBeInTheDocument();
            expect(screen.getByRole('button', { name: /abc123/i })).toBeInTheDocument();
        });

        test('renders multiple comment IDs up to maxDisplay limit', () => {
            const props = createMockCommentListProps({
                commentIds: ['abc123', 'def456', 'ghi789'],
                maxDisplay: 2,
            });
            render(<CommentList {...props} />);

            expect(screen.getByText('abc123')).toBeInTheDocument();
            expect(screen.getByText('def456')).toBeInTheDocument();
            expect(screen.queryByText('ghi789')).not.toBeInTheDocument();
        });

        test('shows "+X more" indicator when exceeding maxDisplay', () => {
            const props = createMockCommentListProps({
                commentIds: ['abc123', 'def456', 'ghi789', 'jkl012'],
                maxDisplay: 2,
            });
            render(<CommentList {...props} />);

            expect(screen.getByText('+2 more')).toBeInTheDocument();
        });

        test('handles loading state correctly', () => {
            const props = createMockCommentListProps({ commentLoading: true });
            render(<CommentList {...props} />);

            const buttons = screen.getAllByRole('button');
            buttons.forEach(button => {
                expect(button).toBeDisabled();
            });
        });
    });

    describe('Interaction Tests', () => {
        test('calls onCommentClick when comment ID is clicked', () => {
            const mockOnCommentClick = jest.fn();
            const props = createMockCommentListProps({
                commentIds: ['abc123'],
                onCommentClick: mockOnCommentClick,
            });
            render(<CommentList {...props} />);

            fireEvent.click(screen.getByText('abc123'));
            expect(mockOnCommentClick).toHaveBeenCalledWith('abc123');
        });

        test('disables buttons during loading state', () => {
            const mockOnCommentClick = jest.fn();
            const props = createMockCommentListProps({
                commentIds: ['abc123'],
                onCommentClick: mockOnCommentClick,
                commentLoading: true,
            });
            render(<CommentList {...props} />);

            const button = screen.getByRole('button', { name: /abc123/i });
            expect(button).toBeDisabled();

            fireEvent.click(button);
            expect(mockOnCommentClick).not.toHaveBeenCalled();
        });
    });

    describe('Accessibility Tests', () => {
        test('has proper ARIA labels and roles', () => {
            const props = createMockCommentListProps({
                commentIds: ['abc123'],
                'aria-label': 'Comment list',
            });
            render(<CommentList {...props} />);

            const container = screen.getByLabelText('Comment list');
            expect(container).toBeInTheDocument();
        });

        test('supports keyboard navigation', () => {
            const mockOnCommentClick = jest.fn();
            const props = createMockCommentListProps({
                commentIds: ['abc123'],
                onCommentClick: mockOnCommentClick,
            });
            render(<CommentList {...props} />);

            const button = screen.getByRole('button', { name: /abc123/i });
            button.focus();

            fireEvent.keyDown(button, { key: 'Enter' });
            expect(mockOnCommentClick).toHaveBeenCalledWith('abc123');
        });
    });

    describe('Edge Cases', () => {
        test('handles null/undefined commentIds', () => {
            const props = createMockCommentListProps({ commentIds: undefined as any });
            render(<CommentList {...props} />);

            expect(screen.getByText('No comments')).toBeInTheDocument();
        });

        test('handles empty string comment IDs', () => {
            const props = createMockCommentListProps({ commentIds: ['', 'abc123'] });
            render(<CommentList {...props} />);

            expect(screen.getByText('abc123')).toBeInTheDocument();
            expect(screen.queryByRole('button', { name: '' })).not.toBeInTheDocument();
        });

        test('handles very long comment IDs', () => {
            const longCommentId = 'a'.repeat(100);
            const props = createMockCommentListProps({ commentIds: [longCommentId] });
            render(<CommentList {...props} />);

            expect(screen.getByText(longCommentId)).toBeInTheDocument();
        });

        test('handles missing onCommentClick prop gracefully', () => {
            const props = createMockCommentListProps({ onCommentClick: undefined as any });
            render(<CommentList {...props} />);

            const button = screen.getByRole('button', { name: /abc123/i });
            fireEvent.click(button);
            // Should not throw error
        });
    });
}); 