import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import FormatCompatibilityAnalyzer from '../FormatCompatibilityAnalyzer';
import * as api from '@/services/api';

// Mock the API
jest.mock('@/services/api', () => ({
  ...jest.requireActual('@/services/api'),
  analyzeFormatCompatibility: jest.fn(),
  getCommentDetail: jest.fn(),
  handleApiError: jest.fn((err: unknown) => {
    if (err instanceof Error) {
      return err.message;
    }
    return 'An unexpected error occurred';
  }),
}));

const mockAnalyzeFormatCompatibility = api.analyzeFormatCompatibility as jest.MockedFunction<
  typeof api.analyzeFormatCompatibility
>;
const mockGetCommentDetail = api.getCommentDetail as jest.MockedFunction<
  typeof api.getCommentDetail
>;

// Mock CommentModal
jest.mock('@/components/domain/CommentModal', () => ({
  __esModule: true,
  default: ({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) =>
    isOpen ? (
      <div data-testid="comment-modal">
        <button onClick={onClose}>Close</button>
      </div>
    ) : null,
}));

// Mock ErrorDisplay
jest.mock('@/components/feedback/ErrorDisplay', () => ({
  __esModule: true,
  default: ({ error }: { error: string }) => (
    <div data-testid="error-display">
      <div>Error</div>
      <div>{error}</div>
    </div>
  ),
}));

// Mock MonthSelector
jest.mock('@/components/forms/MonthSelector', () => ({
  __esModule: true,
  default: ({
    selectedMonths,
    onMonthsChange,
  }: {
    selectedMonths: string[];
    onMonthsChange: (months: string[]) => void;
  }) => (
    <div data-testid="month-selector">
      <button
        onClick={() => onMonthsChange(['2025-05'])}
        data-testid="select-month-button"
      >
        Select Month
      </button>
      <div data-testid="selected-months">{selectedMonths.join(', ')}</div>
    </div>
  ),
}));

const renderComponent = () => {
  return render(
    <BrowserRouter>
      <FormatCompatibilityAnalyzer />
    </BrowserRouter>
  );
};

describe('FormatCompatibilityAnalyzer', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders component with title and description', () => {
    renderComponent();

    expect(screen.getByText('Format Compatibility Analyzer')).toBeInTheDocument();
    expect(
      screen.getByText(
        /Identify incompatible razor and blade format combinations to catch matching errors/
      )
    ).toBeInTheDocument();
  });

  test('renders month selector and severity filter', () => {
    renderComponent();

    expect(screen.getByTestId('month-selector')).toBeInTheDocument();
    expect(screen.getByLabelText('Severity Filter')).toBeInTheDocument();
    expect(screen.getByText('Analyze')).toBeInTheDocument();
  });

  test('disables analyze button when no months selected', () => {
    renderComponent();

    const analyzeButton = screen.getByText('Analyze');
    expect(analyzeButton).toBeDisabled();
  });

  test('enables analyze button when month is selected', async () => {
    const user = userEvent.setup();
    renderComponent();

    const selectMonthButton = screen.getByTestId('select-month-button');
    await user.click(selectMonthButton);

    const analyzeButton = screen.getByText('Analyze');
    expect(analyzeButton).not.toBeDisabled();
  });

  test('calls API when analyze button is clicked', async () => {
    const user = userEvent.setup();
    const mockResults = {
      months: ['2025-05'],
      severity_filter: 'all',
      total_issues: 2,
      errors: 1,
      warnings: 1,
      results: [
        {
          razor_original: 'Gillette Tech',
          razor_matched: { brand: 'Gillette', model: 'Tech', format: 'DE' },
          blade_original: 'Feather AC',
          blade_matched: { brand: 'Feather', format: 'AC' },
          severity: 'error',
          issue_type: 'DE razor incompatible with AC blade',
          comment_ids: ['comment1'],
          count: 1,
        },
      ],
      processing_time: 0.5,
    };

    mockAnalyzeFormatCompatibility.mockResolvedValueOnce(mockResults);

    renderComponent();

    // Select month
    const selectMonthButton = screen.getByTestId('select-month-button');
    await user.click(selectMonthButton);

    // Click analyze
    const analyzeButton = screen.getByText('Analyze');
    await user.click(analyzeButton);

    await waitFor(() => {
      expect(mockAnalyzeFormatCompatibility).toHaveBeenCalledWith({
        months: ['2025-05'],
        severity: 'all',
      });
    });
  });

  test('displays results after analysis', async () => {
    const user = userEvent.setup();
    const mockResults = {
      months: ['2025-05'],
      severity_filter: 'all',
      total_issues: 1,
      errors: 1,
      warnings: 0,
      results: [
        {
          razor_original: 'Gillette Tech',
          razor_matched: { brand: 'Gillette', model: 'Tech', format: 'DE' },
          blade_original: 'Feather AC',
          blade_matched: { brand: 'Feather', format: 'AC' },
          severity: 'error',
          issue_type: 'DE razor incompatible with AC blade',
          comment_ids: ['comment1'],
          count: 1,
        },
      ],
      processing_time: 0.5,
    };

    mockAnalyzeFormatCompatibility.mockResolvedValueOnce(mockResults);

    renderComponent();

    // Select month and analyze
    const selectMonthButton = screen.getByTestId('select-month-button');
    await user.click(selectMonthButton);

    const analyzeButton = screen.getByText('Analyze');
    await user.click(analyzeButton);

    await waitFor(() => {
      expect(screen.getByText('Analysis Results')).toBeInTheDocument();
      // Check for parts of the text that are definitely there
      expect(screen.getByText('Total Issues:')).toBeInTheDocument();
      expect(screen.getByText('Errors:')).toBeInTheDocument();
      expect(screen.getByText('Gillette Tech')).toBeInTheDocument();
    });
  });

  test('displays error message on API failure', async () => {
    const user = userEvent.setup();
    const errorMessage = 'Network failure occurred';
    mockAnalyzeFormatCompatibility.mockRejectedValueOnce(new Error(errorMessage));

    renderComponent();

    const selectMonthButton = screen.getByTestId('select-month-button');
    await user.click(selectMonthButton);

    const analyzeButton = screen.getByText('Analyze');
    await user.click(analyzeButton);

    await waitFor(() => {
      // ErrorDisplay component shows "Error" heading and the error message
      // handleApiError returns error.message for Error objects
      expect(screen.getByText('Error')).toBeInTheDocument();
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  test('filters results by severity', async () => {
    const user = userEvent.setup();
    const mockResults = {
      months: ['2025-05'],
      severity_filter: 'error',
      total_issues: 1,
      errors: 1,
      warnings: 0,
      results: [
        {
          razor_original: 'Gillette Tech',
          razor_matched: { brand: 'Gillette', format: 'DE' },
          blade_original: 'Feather AC',
          blade_matched: { brand: 'Feather', format: 'AC' },
          severity: 'error',
          issue_type: 'DE razor incompatible with AC blade',
          comment_ids: ['comment1'],
          count: 1,
        },
      ],
      processing_time: 0.5,
    };

    mockAnalyzeFormatCompatibility.mockResolvedValueOnce(mockResults);

    renderComponent();

    // Select month
    const selectMonthButton = screen.getByTestId('select-month-button');
    await user.click(selectMonthButton);

    // Change severity filter
    const severityFilter = screen.getByLabelText('Severity Filter');
    await user.selectOptions(severityFilter, 'error');

    // Analyze
    const analyzeButton = screen.getByText('Analyze');
    await user.click(analyzeButton);

    await waitFor(() => {
      expect(mockAnalyzeFormatCompatibility).toHaveBeenCalledWith({
        months: ['2025-05'],
        severity: 'error',
      });
    });
  });

  test('opens comment modal when comment is clicked', async () => {
    const user = userEvent.setup();
    const mockComment = {
      id: 'comment1',
      author: 'user1',
      body: 'Test comment',
      created_utc: '2025-05-01',
      thread_id: 'thread1',
      thread_title: 'Test Thread',
      url: 'https://reddit.com/test',
    };

    mockGetCommentDetail.mockResolvedValueOnce(mockComment);

    const mockResults = {
      months: ['2025-05'],
      severity_filter: 'all',
      total_issues: 1,
      errors: 1,
      warnings: 0,
      results: [
        {
          razor_original: 'Gillette Tech',
          razor_matched: { brand: 'Gillette', format: 'DE' },
          blade_original: 'Feather AC',
          blade_matched: { brand: 'Feather', format: 'AC' },
          severity: 'error',
          issue_type: 'DE razor incompatible with AC blade',
          comment_ids: ['comment1'],
          count: 1,
        },
      ],
      processing_time: 0.5,
    };

    mockAnalyzeFormatCompatibility.mockResolvedValueOnce(mockResults);

    renderComponent();

    // Select month and analyze
    const selectMonthButton = screen.getByTestId('select-month-button');
    await user.click(selectMonthButton);

    const analyzeButton = screen.getByText('Analyze');
    await user.click(analyzeButton);

    // Wait for results and click comment
    await waitFor(() => {
      expect(screen.getByText('comment1')).toBeInTheDocument();
    });

    const commentLink = screen.getByText('comment1');
    await user.click(commentLink);

    await waitFor(() => {
      expect(mockGetCommentDetail).toHaveBeenCalledWith('comment1', ['2025-05']);
      expect(screen.getByTestId('comment-modal')).toBeInTheDocument();
    });
  });
});

