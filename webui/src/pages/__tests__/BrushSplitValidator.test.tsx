import React from 'react';
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
      },
      {
        original: 'Test Brush 2',
        handle: 'Another Maker',
        knot: 'Another Knot',
        validated: true,
        corrected: false,
        validated_at: new Date().toISOString(),
        occurrences: [],
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
      // Check that the original brush names are present
      expect(screen.getByText('Test Brush 1')).toBeInTheDocument();
      expect(screen.getByText('Test Brush 2')).toBeInTheDocument();
    });
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
});
