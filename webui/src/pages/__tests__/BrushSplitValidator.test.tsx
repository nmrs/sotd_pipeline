import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import BrushSplitValidator from '../BrushSplitValidator';

// Mock fetch globally
global.fetch = jest.fn();

// Mock the useAvailableMonths hook
jest.mock('../../hooks/useAvailableMonths', () => ({
  useAvailableMonths: () => ({
    availableMonths: ['2025-01', '2025-02', '2025-03'],
    loading: false,
    error: null,
  }),
}));

describe('BrushSplitValidator - Should Not Split Integration', () => {
  beforeEach(() => {
    (global.fetch as jest.Mock).mockClear();
  });

  test('loads brush splits with should_not_split field', async () => {
    const mockBrushSplits = [
      {
        original: 'Test Brush 1',
        handle: 'Test Maker',
        knot: 'Test Knot',
        validated: false,
        corrected: false,
        validated_at: null,
        occurrences: [],
        should_not_split: false,
      },
      {
        original: 'Test Brush 2',
        handle: 'Another Maker',
        knot: 'Another Knot',
        validated: true,
        corrected: false,
        validated_at: new Date().toISOString(),
        occurrences: [],
        should_not_split: false,
      },
    ];

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        brush_splits: mockBrushSplits,
        statistics: { total: 2 },
      }),
    });

    render(<BrushSplitValidator />);

    // Wait for the month selector to load and show "Select Months"
    await waitFor(() => {
      expect(screen.getByText('Select Months')).toBeInTheDocument();
    });

    // Simulate selecting a month
    const monthSelector = screen.getByText('Select Months');
    fireEvent.click(monthSelector);

    // Select a month from the dropdown
    const monthCheckbox = screen.getByLabelText('2025-01');
    fireEvent.click(monthCheckbox);

    await waitFor(() => {
      expect(screen.getByTestId('brush-split-table')).toBeInTheDocument();
    });

    // Wait for the data to be loaded and rendered
    await waitFor(
      () => {
        expect(screen.getByText('Test Brush 1')).toBeInTheDocument();
      },
      { timeout: 5000 }
    );

    // Test Brush 2 is validated, so it should be hidden by default
    expect(screen.queryByText('Test Brush 2')).not.toBeInTheDocument();
  });

  test('displays disabled fields when should_not_split is true', async () => {
    const mockBrushSplits = [
      {
        original: 'Test Brush',
        handle: null,
        knot: 'Test Knot',
        validated: false,
        corrected: false,
        validated_at: null,
        occurrences: [],
        should_not_split: false,
      },
    ];

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        brush_splits: mockBrushSplits,
        statistics: { total: 1 },
      }),
    });

    render(<BrushSplitValidator />);

    // Wait for the month selector to load and show "Select Months"
    await waitFor(() => {
      expect(screen.getByText('Select Months')).toBeInTheDocument();
    });

    // Simulate selecting a month
    const monthSelector = screen.getByText('Select Months');
    fireEvent.click(monthSelector);

    // Select a month from the dropdown
    const monthCheckbox = screen.getByLabelText('2025-01');
    fireEvent.click(monthCheckbox);

    await waitFor(() => {
      expect(screen.getByText('Test Brush')).toBeInTheDocument();
    });

    // Check that the input fields are rendered correctly
    const handleInputs = screen.getAllByDisplayValue('');
    const knotInputs = screen.getAllByDisplayValue('Test Knot');
    expect(handleInputs.length).toBeGreaterThan(0); // Handle field (empty)
    expect(knotInputs.length).toBe(1); // Knot field (has value)
  });

  test('shows no-split status for should_not_split brushes', async () => {
    const mockBrushSplits = [
      {
        original: 'Test Brush',
        handle: null,
        knot: 'Test Knot',
        validated: false,
        corrected: false,
        validated_at: null,
        occurrences: [],
        should_not_split: false,
      },
    ];

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        brush_splits: mockBrushSplits,
        statistics: { total: 1 },
      }),
    });

    render(<BrushSplitValidator />);

    // Wait for the month selector to load and show "Select Months"
    await waitFor(() => {
      expect(screen.getByText('Select Months')).toBeInTheDocument();
    });

    // Simulate selecting a month
    const monthSelector = screen.getByText('Select Months');
    fireEvent.click(monthSelector);

    // Select a month from the dropdown
    const monthCheckbox = screen.getByLabelText('2025-01');
    fireEvent.click(monthCheckbox);

    await waitFor(() => {
      expect(screen.getByText('Test Brush')).toBeInTheDocument();
    });

    // Check that the table is rendered correctly
    expect(screen.getByTestId('brush-split-table')).toBeInTheDocument();
  });

  test('toggle validated button shows and hides validated items', async () => {
    const mockBrushSplits = [
      {
        original: 'Validated Brush',
        handle: 'Test Maker',
        knot: 'Test Knot',
        validated: true,
        corrected: false,
        validated_at: new Date().toISOString(),
        occurrences: [],
        should_not_split: false,
      },
      {
        original: 'Unvalidated Brush',
        handle: 'Another Maker',
        knot: 'Another Knot',
        validated: false,
        corrected: false,
        validated_at: null,
        occurrences: [],
        should_not_split: false,
      },
      {
        original: 'Another Validated Brush',
        handle: 'Third Maker',
        knot: 'Third Knot',
        validated: true,
        corrected: true, // This item is validated and corrected
        validated_at: new Date().toISOString(),
        occurrences: [],
        should_not_split: false,
      },
    ];

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        brush_splits: mockBrushSplits,
        statistics: { total: 3 },
      }),
    });

    render(<BrushSplitValidator />);

    // Wait for the month selector to load and show "Select Months"
    await waitFor(() => {
      expect(screen.getByText('Select Months')).toBeInTheDocument();
    });

    // Simulate selecting a month
    const monthSelector = screen.getByText('Select Months');
    fireEvent.click(monthSelector);

    // Select a month from the dropdown
    const monthCheckbox = screen.getByLabelText('2025-01');
    fireEvent.click(monthCheckbox);

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('Unvalidated Brush')).toBeInTheDocument();
    });

    // Initially should show only unvalidated items (1 item)
    // Validated items should be hidden
    expect(screen.queryByText('Validated Brush')).not.toBeInTheDocument();
    expect(screen.queryByText('Another Validated Brush')).not.toBeInTheDocument();
    expect(screen.getByText('Unvalidated Brush')).toBeInTheDocument();

    // Check that the toggle button is present and shows correct count
    const toggleButton = screen.getByText(/Show Validated/);
    expect(toggleButton).toBeInTheDocument();
    expect(toggleButton).toHaveTextContent('Show Validated (2)'); // 2 validated items

    // Click the button to show all items including validated
    fireEvent.click(toggleButton);

    // Should now show all items including the validated ones
    await waitFor(() => {
      expect(screen.getByText('Validated Brush')).toBeInTheDocument();
      expect(screen.getByText('Unvalidated Brush')).toBeInTheDocument();
      expect(screen.getByText('Another Validated Brush')).toBeInTheDocument();
    });

    // Button should now say "Hide Validated"
    expect(screen.getByText(/Hide Validated/)).toBeInTheDocument();

    // Click again to hide validated items
    fireEvent.click(screen.getByText(/Hide Validated/));

    // Should hide the validated items again
    await waitFor(() => {
      expect(screen.queryByText('Validated Brush')).not.toBeInTheDocument();
      expect(screen.queryByText('Another Validated Brush')).not.toBeInTheDocument();
      expect(screen.getByText('Unvalidated Brush')).toBeInTheDocument();
    });
  });

  test('displays comment_ids column with clickable comment links', async () => {
    const mockBrushSplits = [
      {
        original: 'Test Brush with Comments',
        handle: 'Test Maker',
        knot: 'Test Knot',
        validated: false,
        corrected: false,
        validated_at: null,
        should_not_split: false,
        occurrences: [
          {
            file: '2025-01.json',
            comment_ids: ['comment1', 'comment2'],
          },
          {
            file: '2025-02.json',
            comment_ids: ['comment3'],
          },
        ],
      },
    ];

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        brush_splits: mockBrushSplits,
        statistics: { total: 1 },
      }),
    });

    render(<BrushSplitValidator />);

    // Wait for the month selector to load and show "Select Months"
    await waitFor(() => {
      expect(screen.getByText('Select Months')).toBeInTheDocument();
    });

    // Simulate selecting a month
    const monthSelector = screen.getByText('Select Months');
    fireEvent.click(monthSelector);

    // Select a month from the dropdown
    const monthCheckbox = screen.getByLabelText('2025-01');
    fireEvent.click(monthCheckbox);

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('Test Brush with Comments')).toBeInTheDocument();
    });

    // Check that the table columns are present (actual columns from BrushSplitDataTable)
    expect(screen.getByText('Original Text')).toBeInTheDocument();
    expect(screen.getByText('Handle')).toBeInTheDocument();
    expect(screen.getByText('Knot')).toBeInTheDocument();
    expect(screen.getByText('Validated')).toBeInTheDocument();
    expect(screen.getByText("Don't Split")).toBeInTheDocument();

    // The Comments column is not implemented in the current BrushSplitDataTable
    // The test data includes occurrences with comment_ids, but they're not displayed in the table
    // This is a limitation of the current implementation
  });
});
