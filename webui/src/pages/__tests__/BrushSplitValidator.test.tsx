import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

// Mock the API service
jest.mock('../../services/api', () => ({
  getAvailableMonths: jest.fn(),
}));

// Mock fetch globally
global.fetch = jest.fn();

import { getAvailableMonths } from '../../services/api';
import BrushSplitValidator from '../BrushSplitValidator';

describe('BrushSplitValidator - Should Not Split Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Mock getAvailableMonths to return some months
    (getAvailableMonths as jest.Mock).mockResolvedValue(['2025-01', '2025-02']);
  });

  test('loads brush splits with should_not_split field', async () => {
    const mockBrushSplits = [
      {
        original: 'Test Brush 1',
        handle: 'Test Handle',
        knot: 'Test Knot',
        should_not_split: false,
        match_type: 'regex',
      },
      {
        original: 'Test Brush 2',
        handle: null,
        knot: 'Test Knot 2',
        should_not_split: true,
        match_type: 'none',
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

    // Wait for the month selector to load
    await waitFor(() => {
      expect(screen.getByText('Select Months')).toBeInTheDocument();
    });

    // Simulate selecting a month
    const monthSelector = screen.getByText('Select Months');
    fireEvent.click(monthSelector);

    // Select a month from the dropdown
    const monthCheckbox = screen.getByLabelText('2025-01');
    fireEvent.click(monthCheckbox);

    // Wait for the component to load data
    await waitFor(() => {
      // Check that the table is rendered with the expected data
      expect(screen.getByTestId('brush-split-table')).toBeInTheDocument();
      // Check that the original brush names are present
      expect(screen.getByText('Test Brush 1')).toBeInTheDocument();
      expect(screen.getByText('Test Brush 2')).toBeInTheDocument();
    });

    // Check that the should_not_split checkbox is rendered
    expect(screen.getByText('Should Not Split')).toBeInTheDocument();
  });

  test('displays disabled fields when should_not_split is true', async () => {
    const mockBrushSplits = [
      {
        original: 'Test Brush',
        handle: null,
        knot: 'Test Knot',
        should_not_split: true,
        match_type: 'none',
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

    // Wait for the month selector to load
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

    // Check that disabled fields show appropriate text (handle shows "Click to edit", knot shows actual value)
    const clickToEditInputs = screen.getAllByPlaceholderText('Click to edit');
    const knotInputs = screen.getAllByDisplayValue('Test Knot');
    expect(clickToEditInputs.length).toBe(2); // Both handle and knot fields (handle is null, knot has value)
    expect(knotInputs.length).toBe(1); // Knot field (has value)
  });

  test('shows no-split status for should_not_split brushes', async () => {
    const mockBrushSplits = [
      {
        original: 'Test Brush',
        handle: null,
        knot: 'Test Knot',
        should_not_split: true,
        match_type: 'none',
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

    // Wait for the month selector to load
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

    // Check that the should_not_split checkbox is checked
    const checkboxes = screen.getAllByRole('checkbox');
    const shouldNotSplitCheckbox = checkboxes[1]; // Skip selection checkbox
    expect(shouldNotSplitCheckbox).toBeChecked();
  });
});
