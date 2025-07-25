import { render, screen, fireEvent } from '@testing-library/react';
import MismatchAnalyzerDataTable from '../MismatchAnalyzerDataTable';
import { MismatchItem } from '../../../services/api';

// Mock the CommentList component
jest.mock('../../domain/CommentList', () => ({
  CommentList: ({
    commentIds,
    onCommentClick,
  }: {
    commentIds: string[];
    onCommentClick: (commentId: string) => void;
  }) => (
    <div data-testid='comment-list'>
      {commentIds.map(id => (
        <button key={id} onClick={() => onCommentClick(id)}>
          {id}
        </button>
      ))}
    </div>
  ),
}));

const createMockMismatchItem = (overrides = {}): MismatchItem => ({
  original: 'test razor',
  matched: { brand: 'Test', model: 'Razor' },
  pattern: 'test pattern',
  match_type: 'regex',
  confidence: 0.8,
  mismatch_type: 'levenshtein_distance',
  reason: 'Distance exceeds threshold',
  count: 1,
  examples: ['example1'],
  comment_ids: ['abc123', 'def456'],
  ...overrides,
});

describe('MismatchAnalyzerDataTable with CommentList Integration', () => {
  const mockOnCommentClick = jest.fn();
  const mockCommentLoading = false;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders CommentList component in comments column', () => {
    const data = [createMockMismatchItem()];
    render(
      <MismatchAnalyzerDataTable
        data={data}
        onCommentClick={mockOnCommentClick}
        commentLoading={mockCommentLoading}
      />
    );

    expect(screen.getByTestId('comment-list')).toBeInTheDocument();
  });

  test('passes correct props to CommentList component', () => {
    const data = [createMockMismatchItem()];
    render(
      <MismatchAnalyzerDataTable
        data={data}
        onCommentClick={mockOnCommentClick}
        commentLoading={mockCommentLoading}
      />
    );

    // Verify CommentList is rendered with the correct comment IDs
    expect(screen.getByText('abc123')).toBeInTheDocument();
    expect(screen.getByText('def456')).toBeInTheDocument();
  });

  test('handles empty comment_ids array', () => {
    const data = [createMockMismatchItem({ comment_ids: [] })];
    render(
      <MismatchAnalyzerDataTable
        data={data}
        onCommentClick={mockOnCommentClick}
        commentLoading={mockCommentLoading}
      />
    );

    expect(screen.getByTestId('comment-list')).toBeInTheDocument();
  });

  test('passes commentLoading prop to CommentList', () => {
    const data = [createMockMismatchItem()];
    render(
      <MismatchAnalyzerDataTable
        data={data}
        onCommentClick={mockOnCommentClick}
        commentLoading={true}
      />
    );

    expect(screen.getByTestId('comment-list')).toBeInTheDocument();
  });

  test('calls onCommentClick when comment is clicked', () => {
    const data = [createMockMismatchItem()];
    render(
      <MismatchAnalyzerDataTable
        data={data}
        onCommentClick={mockOnCommentClick}
        commentLoading={mockCommentLoading}
      />
    );

    fireEvent.click(screen.getByText('abc123'));
    expect(mockOnCommentClick).toHaveBeenCalledWith('abc123');
  });
});
