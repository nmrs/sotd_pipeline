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

// Mock the BrushTable component to verify it receives correct data
jest.mock('../../components/data/BrushTable', () => ({
  __esModule: true,
  default: function MockBrushTable(props: any) {
    // Log the data structure to help debug
    console.log('BrushTable received data:', JSON.stringify(props.items, null, 2));

    return (
      <div data-testid='brush-table'>
        <div data-testid='brush-table-item-count'>{props.items?.length || 0}</div>
        <div data-testid='brush-table-has-components'>
          {props.items?.some((item: any) => item.components?.handle || item.components?.knot)
            ? 'true'
            : 'false'}
        </div>
        {props.items?.map((item: any, index: number) => (
          <div key={index} data-testid={`brush-item-${index}`}>
            <span data-testid={`brush-item-main-${index}`}>{item.main?.text}</span>
            <span data-testid={`brush-item-handle-${index}`}>
              {item.components?.handle?.text || 'no-handle'}
            </span>
            <span data-testid={`brush-item-knot-${index}`}>
              {item.components?.knot?.text || 'no-knot'}
            </span>
          </div>
        ))}
      </div>
    );
  },
}));

// Mock the VirtualizedTable component
jest.mock('../../components/data/VirtualizedTable', () => ({
  VirtualizedTable: function MockVirtualizedTable(props: any) {
    return (
      <div data-testid='virtualized-table'>
        {props.data?.map((item: any, index: number) => (
          <div key={index} data-testid={`table-row-${index}`}>
            {props.columns?.map((column: any) => (
              <div key={column.key} data-testid={`cell-${column.key}-${index}`}>
                {column.render ? column.render(item) : item[column.key]}
              </div>
            ))}
          </div>
        ))}
      </div>
    );
  },
}));

import UnmatchedAnalyzer from '../UnmatchedAnalyzer';

describe('UnmatchedAnalyzer Integration Tests', () => {
  const mockApi = require('../../services/api');

  beforeEach(() => {
    jest.clearAllMocks();

    // Mock successful API response
    mockApi.fetchUnmatchedData.mockResolvedValue({
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
    });

    // Mock analyzeUnmatched to return the same data
    mockApi.analyzeUnmatched.mockResolvedValue({
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
    });

    // Mock available months
    mockApi.getAvailableMonths.mockResolvedValue(['2024-01', '2024-02', '2024-03']);
  });

  test('should transform brush data correctly for BrushTable with sub-rows', async () => {
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
      expect(screen.getByTestId('brush-table')).toBeInTheDocument();
    });

    // Verify that BrushTable received data with components
    expect(screen.getByTestId('brush-table-has-components')).toHaveTextContent('true');

    // Verify that we have the expected number of items (2 brushes)
    expect(screen.getByTestId('brush-table-item-count')).toHaveTextContent('2');

    // Verify that the transformed data has the correct structure
    expect(screen.getByTestId('brush-item-main-0')).toHaveTextContent('Simpson Chubby 2');
    expect(screen.getByTestId('brush-item-handle-0')).toHaveTextContent('Elite handle');
    expect(screen.getByTestId('brush-item-knot-0')).toHaveTextContent('Declaration knot');

    expect(screen.getByTestId('brush-item-main-1')).toHaveTextContent('Declaration B15');
    expect(screen.getByTestId('brush-item-handle-1')).toHaveTextContent('Declaration handle');
    expect(screen.getByTestId('brush-item-knot-1')).toHaveTextContent('Declaration knot');
  });

  test('should render brush field when selected', async () => {
    render(<UnmatchedAnalyzer />);

    // Select brush field from dropdown
    const fieldSelect = screen.getByRole('combobox');
    fireEvent.change(fieldSelect, { target: { value: 'brush' } });

    // The brush table should not appear until analysis is triggered
    // Just verify that the field selection worked
    expect(fieldSelect).toHaveValue('brush');

    // Verify that no table is rendered initially (since no analysis has been run)
    expect(screen.queryByTestId('brush-table')).not.toBeInTheDocument();
    expect(screen.queryByTestId('virtualized-table')).not.toBeInTheDocument();
  });
});
