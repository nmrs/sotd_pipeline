import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import CommentModal from '../CommentModal';
import { CommentDetail } from '../../../services/api';

jest.mock('../../../services/api', () => {
  const actual = jest.requireActual('../../../services/api');
  return {
    ...actual,
    saveExtractOverrides: jest.fn(),
  };
});

import { saveExtractOverrides } from '../../../services/api';

const baseComment: CommentDetail = {
  id: 'abc123',
  author: 'tester',
  body: 'Razor: Ko',
  created_utc: '2026-08-01T12:00:00Z',
  thread_id: 't1',
  thread_title: 'SOTD',
  url: 'https://reddit.com/r/wetshaving/comments/x',
  month: '2026-08',
  data_source: 'enriched',
  product_data: {
    razor: {
      original: 'Ko',
      normalized: 'Ko',
      matched: null,
      enriched: null,
      override_value: null,
      override_pending: false,
    },
  },
};

describe('CommentModal extract overrides', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('shows edit overrides and saves YAML-only message', async () => {
    (saveExtractOverrides as jest.Mock).mockResolvedValue({
      success: true,
      message: 'Extract overrides saved. Re-run extract→match→enrich with --force for 2026-08 to apply.',
      month: '2026-08',
      comment_id: 'abc123',
      fields: { razor: 'Koraat' },
    });

    render(<CommentModal comment={baseComment} isOpen={true} onClose={() => {}} />);

    fireEvent.click(screen.getByRole('button', { name: /edit overrides/i }));
    const razorInput = screen.getByLabelText(/razor override/i);
    fireEvent.change(razorInput, { target: { value: 'Koraat' } });
    fireEvent.click(screen.getByRole('button', { name: /^save$/i }));

    await waitFor(() => {
      expect(saveExtractOverrides).toHaveBeenCalledWith('2026-08', 'abc123', {
        razor: 'Koraat',
        blade: '',
        brush: '',
        soap: '',
      });
    });

    expect(
      await screen.findByText(/re-run extract→match→enrich/i)
    ).toBeInTheDocument();
  });

  it('shows pending badge for pending override', () => {
    const comment: CommentDetail = {
      ...baseComment,
      product_data: {
        razor: {
          original: 'Ko',
          normalized: 'Ko',
          matched: null,
          enriched: null,
          override_value: 'Koraat',
          override_pending: true,
        },
      },
    };
    render(<CommentModal comment={comment} isOpen={true} onClose={() => {}} />);
    expect(screen.getByText('Koraat')).toBeInTheDocument();
    expect(screen.getByText('Pending')).toBeInTheDocument();
  });
});
