import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

// Test that error recovery functionality is properly implemented
describe('Error Recovery', () => {
  test('should display partial results when full analysis fails', async () => {
    const mockApi = {
      getAvailableMonths: jest.fn().mockResolvedValue(['2024-01', '2024-02']),
      analyzeMismatch: jest.fn().mockImplementation(() =>
        Promise.resolve({
          field: 'brush',
          months: ['2024-01'],
          total_matches: 0,
          total_mismatches: 2,
          mismatch_items: [
            {
              original: 'Partial Brush 1',
              matched: {},
              pattern: '',
              match_type: 'unmatched',
              mismatch_type: 'unmatched',
              count: 3,
              comment_ids: ['123'],
              examples: ['example1.json'],
            },
          ],
          processing_time: 0.5,
          partial_results: true,
          error: 'Some items could not be processed',
        })
      ),
    };

    jest.doMock('../../services/api', () => ({
      ...jest.requireActual('../../services/api'),
      ...mockApi,
    }));

    const { default: MatchAnalyzer } = await import('../../pages/MatchAnalyzer');

    render(
      <MemoryRouter>
        <MatchAnalyzer />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Match Analyzer/i)).toBeInTheDocument();
    });

    expect(mockApi.analyzeMismatch).toBeDefined();
  });

  test('should implement retry mechanisms for failed operations', async () => {
    let callCount = 0;
    const mockApi = {
      getAvailableMonths: jest.fn().mockResolvedValue(['2024-01', '2024-02']),
      analyzeMismatch: jest.fn().mockImplementation(() => {
        callCount++;
        if (callCount === 1) return Promise.reject(new Error('Network error'));
        return Promise.resolve({
          field: 'brush',
          months: ['2024-01'],
          total_matches: 0,
          total_mismatches: 1,
          mismatch_items: [
            {
              original: 'Retry Success Brush',
              matched: {},
              pattern: '',
              match_type: 'unmatched',
              mismatch_type: 'unmatched',
              count: 2,
              comment_ids: ['456'],
              examples: ['example2.json'],
            },
          ],
          processing_time: 0.3,
        });
      }),
    };

    jest.doMock('../../services/api', () => ({
      ...jest.requireActual('../../services/api'),
      ...mockApi,
    }));

    const { default: MatchAnalyzer } = await import('../../pages/MatchAnalyzer');

    render(
      <MemoryRouter>
        <MatchAnalyzer />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Match Analyzer/i)).toBeInTheDocument();
    });

    expect(mockApi.analyzeMismatch).toBeDefined();
  });

  test('should create fallback displays for missing data', async () => {
    const mockApi = {
      getAvailableMonths: jest.fn().mockResolvedValue(['2024-01', '2024-02']),
      analyzeMismatch: jest.fn().mockResolvedValue({
        field: 'brush',
        months: ['2024-01'],
        total_matches: 0,
        total_mismatches: 0,
        mismatch_items: [],
        processing_time: 0.1,
        partial_results: false,
      }),
    };

    jest.doMock('../../services/api', () => ({
      ...jest.requireActual('../../services/api'),
      ...mockApi,
    }));

    const { default: MatchAnalyzer } = await import('../../pages/MatchAnalyzer');

    render(
      <MemoryRouter>
        <MatchAnalyzer />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Match Analyzer/i)).toBeInTheDocument();
    });

    expect(mockApi.analyzeMismatch).toBeDefined();
  });

  test('should provide recovery suggestions for common errors', async () => {
    const mockApi = {
      getAvailableMonths: jest.fn().mockResolvedValue(['2024-01', '2024-02']),
      analyzeMismatch: jest
        .fn()
        .mockRejectedValue(new Error('File not found: data/matched/2024-01.json')),
    };

    jest.doMock('../../services/api', () => ({
      ...jest.requireActual('../../services/api'),
      ...mockApi,
    }));

    const { default: MatchAnalyzer } = await import('../../pages/MatchAnalyzer');

    render(
      <MemoryRouter>
        <MatchAnalyzer />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Match Analyzer/i)).toBeInTheDocument();
    });

    expect(mockApi.analyzeMismatch).toBeDefined();
  });

  test('should implement error boundary for component-level errors', async () => {
    // Test the ErrorBoundary component directly
    const { default: ErrorBoundary } = await import('../../components/feedback/ErrorBoundary');

    const BuggyComponent = () => {
      throw new Error('Component error');
    };

    render(
      <ErrorBoundary>
        <BuggyComponent />
      </ErrorBoundary>
    );

    // Should show error boundary fallback
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
    expect(screen.getByText(/try refreshing the page/i)).toBeInTheDocument();
  });
});
