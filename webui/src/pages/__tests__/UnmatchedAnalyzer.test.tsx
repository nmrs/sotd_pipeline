import { render, screen, fireEvent, waitFor } from '@testing-library/react';

// Mock the API calls
jest.mock('../../services/api', () => ({
  fetchUnmatchedData: jest.fn(),
  updateFilteredStatus: jest.fn(),
  fetchCommentDetails: jest.fn(),
  getAvailableMonths: jest.fn(),
  handleApiError: jest.fn(err => err.message || 'API Error'),
  analyzeUnmatched: jest.fn(),
  checkFilteredStatus: jest.fn(),
}));

import UnmatchedAnalyzer from '../UnmatchedAnalyzer';
import * as mockApi from '../../services/api';

describe('UnmatchedAnalyzer Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Mock successful API response for analyzeUnmatched

    // Mock analyzeUnmatched to return the same data
    (
      mockApi.analyzeUnmatched as jest.MockedFunction<typeof mockApi.analyzeUnmatched>
    ).mockResolvedValue({
      field: 'brush',
      months: ['2024-01', '2024-02', '2024-03'],
      total_unmatched: 2,
      unmatched_items: [
        {
          item: 'Simpson Chubby 2',
          count: 5,
          comment_ids: ['123', '456'],
          examples: ['2024-01.json', '2024-02.json'],
          unmatched: {
            handle: { text: 'Elite handle', pattern: 'handle_pattern' },
            knot: { text: 'Declaration knot', pattern: 'knot_pattern' },
          },
        },
        {
          item: 'Declaration B15',
          count: 3,
          comment_ids: ['789'],
          examples: ['2024-03.json'],
          unmatched: {
            handle: { text: 'Declaration handle', pattern: 'handle_pattern' },
            knot: { text: 'Declaration knot', pattern: 'knot_pattern' },
          },
        },
      ],
      processing_time: 1.5,
    });

    // Mock available months
    (
      mockApi.getAvailableMonths as jest.MockedFunction<typeof mockApi.getAvailableMonths>
    ).mockResolvedValue(['2024-01', '2024-02', '2024-03']);
  });

  test('should display brush data correctly in standard table format', async () => {
    render(<UnmatchedAnalyzer />);

    // Wait for months to load
    await waitFor(() => {
      expect(screen.queryByText('Loading available months...')).not.toBeInTheDocument();
    });

    // Select brush field
    const fieldSelect = screen.getByRole('combobox');
    fireEvent.change(fieldSelect, { target: { value: 'brush' } });

    // Select months (wait for the button to be available)
    await waitFor(() => {
      expect(screen.getByText('Select Months')).toBeInTheDocument();
    });
    const monthButton = screen.getByText('Select Months');
    fireEvent.click(monthButton);

    // Select a month from the dropdown
    const monthCheckbox = screen.getByLabelText('2024-01');
    fireEvent.click(monthCheckbox);

    // Click analyze button
    const analyzeButton = screen.getByText('Analyze');
    fireEvent.click(analyzeButton);

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByTestId('unmatched-analyzer-data-table')).toBeInTheDocument();
    });

    // Verify that we have the expected number of items (2 brushes)
    expect(screen.getByText('Simpson Chubby 2')).toBeInTheDocument();
    expect(screen.getByText('Declaration B15')).toBeInTheDocument();

    // Verify the counts are displayed
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();

    // Verify that the table shows the standard format for unmatched items
    expect(screen.getByText('Filtered')).toBeInTheDocument();
    expect(screen.getByText('Item')).toBeInTheDocument();
    expect(screen.getByText('Count')).toBeInTheDocument();
    expect(screen.getByText('Comments')).toBeInTheDocument();
    expect(screen.getByText('Examples')).toBeInTheDocument();
  });

  test('should render brush field when selected', async () => {
    render(<UnmatchedAnalyzer />);

    // Select brush field from dropdown
    const fieldSelect = screen.getByRole('combobox');
    fireEvent.change(fieldSelect, { target: { value: 'brush' } });

    // The data table should not appear until analysis is triggered
    // Just verify that the field selection worked
    expect(fieldSelect).toHaveValue('brush');

    // Verify that no table is rendered initially (since no analysis has been run)
    expect(screen.queryByTestId('unmatched-analyzer-data-table')).not.toBeInTheDocument();
  });
});
