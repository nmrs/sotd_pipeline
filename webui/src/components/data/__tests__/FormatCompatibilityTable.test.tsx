import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import FormatCompatibilityTable from '../FormatCompatibilityTable';
import { FormatCompatibilityResult } from '@/services/api';

// Mock CommentDisplay
jest.mock('@/components/domain/CommentDisplay', () => ({
  CommentDisplay: ({
    commentIds,
    onCommentClick,
  }: {
    commentIds: string[];
    onCommentClick: (id: string) => void;
  }) => (
    <div data-testid="comment-display">
      {commentIds.map(id => (
        <button key={id} onClick={() => onCommentClick(id)} data-testid={`comment-${id}`}>
          {id}
        </button>
      ))}
    </div>
  ),
}));

const mockData: FormatCompatibilityResult[] = [
  {
    razor_original: 'Gillette Tech',
    razor_matched: { brand: 'Gillette', model: 'Tech', format: 'DE' },
    razor_enriched: { format: 'DE' },
    blade_original: 'Feather AC',
    blade_matched: { brand: 'Feather', format: 'AC' },
    severity: 'error',
    issue_type: 'DE razor incompatible with AC blade',
    comment_ids: ['comment1', 'comment2'],
    count: 2,
  },
  {
    razor_original: 'Cartridge Razor',
    razor_matched: { brand: 'Gillette', format: 'Cartridge/Disposable' },
    blade_original: 'Some Blade',
    blade_matched: { brand: 'Gillette', format: 'DE' },
    severity: 'warning',
    issue_type: 'Cartridge/Disposable razor should not have blade format',
    comment_ids: ['comment3'],
    count: 1,
  },
];

describe('FormatCompatibilityTable', () => {
  const mockOnCommentClick = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders table with all columns', () => {
    render(
      <FormatCompatibilityTable
        data={mockData}
        onCommentClick={mockOnCommentClick}
        commentLoading={false}
      />
    );

    expect(screen.getByText('Razor')).toBeInTheDocument();
    expect(screen.getByText('Blade')).toBeInTheDocument();
    expect(screen.getByText('Issue')).toBeInTheDocument();
    expect(screen.getByText('Count')).toBeInTheDocument();
    expect(screen.getByText('Comments')).toBeInTheDocument();
  });

  test('displays razor data correctly', () => {
    render(
      <FormatCompatibilityTable
        data={mockData}
        onCommentClick={mockOnCommentClick}
        commentLoading={false}
      />
    );

    expect(screen.getByText('Gillette Tech')).toBeInTheDocument();
    expect(screen.getByText(/Gillette - Tech - DE/)).toBeInTheDocument();
  });

  test('displays blade data correctly', () => {
    render(
      <FormatCompatibilityTable
        data={mockData}
        onCommentClick={mockOnCommentClick}
        commentLoading={false}
      />
    );

    expect(screen.getByText('Feather AC')).toBeInTheDocument();
    expect(screen.getByText(/Feather - AC/)).toBeInTheDocument();
  });

  test('displays severity badges correctly', () => {
    render(
      <FormatCompatibilityTable
        data={mockData}
        onCommentClick={mockOnCommentClick}
        commentLoading={false}
      />
    );

    expect(screen.getByText('Error')).toBeInTheDocument();
    expect(screen.getByText('Warning')).toBeInTheDocument();
  });

  test('displays issue type correctly', () => {
    render(
      <FormatCompatibilityTable
        data={mockData}
        onCommentClick={mockOnCommentClick}
        commentLoading={false}
      />
    );

    expect(screen.getByText('DE razor incompatible with AC blade')).toBeInTheDocument();
    expect(
      screen.getByText('Cartridge/Disposable razor should not have blade format')
    ).toBeInTheDocument();
  });

  test('displays count correctly', () => {
    render(
      <FormatCompatibilityTable
        data={mockData}
        onCommentClick={mockOnCommentClick}
        commentLoading={false}
      />
    );

    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  test('displays comment IDs and handles clicks', async () => {
    const user = userEvent.setup();
    render(
      <FormatCompatibilityTable
        data={mockData}
        onCommentClick={mockOnCommentClick}
        commentLoading={false}
      />
    );

    const comment1Button = screen.getByTestId('comment-comment1');
    expect(comment1Button).toBeInTheDocument();

    await user.click(comment1Button);

    // FormatCompatibilityTable wraps CommentDisplay's onCommentClick to pass allCommentIds
    expect(mockOnCommentClick).toHaveBeenCalledWith('comment1', ['comment1', 'comment2']);
  });

  test('uses enriched format when available', () => {
    const dataWithEnriched: FormatCompatibilityResult[] = [
      {
        razor_original: 'Other Shavette',
        razor_matched: { brand: 'Other Shavette', format: 'Shavette' },
        razor_enriched: { format: 'Shavette (AC)' },
        blade_original: 'Feather AC',
        blade_matched: { brand: 'Feather', format: 'AC' },
        severity: 'error',
        issue_type: 'Test issue',
        comment_ids: ['comment1'],
        count: 1,
      },
    ];

    render(
      <FormatCompatibilityTable
        data={dataWithEnriched}
        onCommentClick={mockOnCommentClick}
        commentLoading={false}
      />
    );

    // Should show enriched format
    expect(screen.getByText(/Shavette \(AC\)/)).toBeInTheDocument();
  });

  test('displays empty state when no data', () => {
    render(
      <FormatCompatibilityTable
        data={[]}
        onCommentClick={mockOnCommentClick}
        commentLoading={false}
      />
    );

    expect(screen.getByText('No format compatibility issues found')).toBeInTheDocument();
  });

  test('handles missing blade format gracefully', () => {
    const dataWithoutBladeFormat: FormatCompatibilityResult[] = [
      {
        razor_original: 'Gillette Tech',
        razor_matched: { brand: 'Gillette', format: 'DE' },
        blade_original: 'Some Blade',
        blade_matched: { brand: 'Feather' }, // No format
        severity: 'warning',
        issue_type: 'Missing blade format',
        comment_ids: ['comment1'],
        count: 1,
      },
    ];

    render(
      <FormatCompatibilityTable
        data={dataWithoutBladeFormat}
        onCommentClick={mockOnCommentClick}
        commentLoading={false}
      />
    );

    expect(screen.getByText('Some Blade')).toBeInTheDocument();
    expect(screen.getByText(/Feather/)).toBeInTheDocument();
  });
});

