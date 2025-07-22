import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import BrushSplitTable from '../data/BrushSplitTable';
import type { BrushSplit } from '../../types/brushSplit';

describe('BrushSplitTable - Should Not Split Feature', () => {
  const mockBrushSplits: BrushSplit[] = [
    {
      original: 'Test Brush 1',
      handle: 'Test Handle',
      knot: 'Test Knot',
      validated: false,
      corrected: false,
      validated_at: null,
      occurrences: [],
    },
    {
      original: 'Test Brush 2',
      handle: null,
      knot: 'Test Brush 2',
      validated: false,
      corrected: false,
      validated_at: null,
      occurrences: [],
    },
  ];

  const mockOnSave = jest.fn();
  const mockOnSelectionChange = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders should not split checkbox column', () => {
    render(
      <BrushSplitTable
        brushSplits={mockBrushSplits}
        onSave={mockOnSave}
        onSelectionChange={mockOnSelectionChange}
      />
    );

    // Check that the column header is present
    expect(screen.getByText('Should Not Split')).toBeInTheDocument();
  });

  test('renders should not split checkboxes for each row', () => {
    render(
      <BrushSplitTable
        brushSplits={mockBrushSplits}
        onSave={mockOnSave}
        onSelectionChange={mockOnSelectionChange}
      />
    );

    // Check that checkboxes are rendered
    const checkboxes = screen.getAllByRole('checkbox');
    expect(checkboxes.length).toBeGreaterThan(0);
  });

  test('should not split checkbox reflects correct state', () => {
    render(
      <BrushSplitTable
        brushSplits={mockBrushSplits}
        onSave={mockOnSave}
        onSelectionChange={mockOnSelectionChange}
      />
    );

    // First brush should not have should_not_split checked (defaults to false)
    const firstCheckbox = screen.getAllByRole('checkbox')[1]; // Skip selection checkbox
    expect(firstCheckbox).not.toBeChecked();

    // Second brush should not have should_not_split checked (defaults to false)
    const secondCheckbox = screen.getAllByRole('checkbox')[3]; // Skip selection checkbox
    expect(secondCheckbox).not.toBeChecked();
  });

  test('clicking should not split checkbox tracks changes for bulk save', () => {
    render(
      <BrushSplitTable
        brushSplits={mockBrushSplits}
        onSave={mockOnSave}
        onSelectionChange={mockOnSelectionChange}
      />
    );

    const shouldNotSplitCheckbox = screen.getAllByRole('checkbox')[1]; // Skip selection checkbox
    fireEvent.click(shouldNotSplitCheckbox);

    // Should show unsaved changes indicator
    expect(screen.getByText('1 unsaved change')).toBeInTheDocument();

    // Should show save button
    expect(screen.getByText('Save All Changes')).toBeInTheDocument();

    // Click save button to trigger onSave
    fireEvent.click(screen.getByText('Save All Changes'));

    expect(mockOnSave).toHaveBeenCalledWith(0, {
      ...mockBrushSplits[0],
      should_not_split: true,
    });
  });

  test('handle and knot fields are enabled by default', () => {
    render(
      <BrushSplitTable
        brushSplits={mockBrushSplits}
        onSave={mockOnSave}
        onSelectionChange={mockOnSelectionChange}
      />
    );

    // For the first brush (should_not_split: false), fields should be enabled
    // In ShadCN version, enabled fields show the actual value
    const enabledHandleInputs = screen.getAllByDisplayValue('Test Handle');
    expect(enabledHandleInputs.length).toBe(1);

    // Check that the field is clickable by verifying it has the correct role
    const handleInput = screen.getByDisplayValue('Test Handle');
    expect(handleInput).toBeInTheDocument();
    expect(handleInput).not.toBeDisabled();
  });

  test('clicking handle field triggers edit mode when enabled', () => {
    render(
      <BrushSplitTable
        brushSplits={mockBrushSplits}
        onSave={mockOnSave}
        onSelectionChange={mockOnSelectionChange}
      />
    );

    // Find the enabled handle field and click it
    const enabledHandleField = screen.getByDisplayValue('Test Handle');
    fireEvent.click(enabledHandleField);

    // Should be clickable and not disabled
    expect(enabledHandleField).toBeInTheDocument();
    expect(enabledHandleField).not.toBeDisabled();
  });

  test('clicking knot field triggers edit mode when enabled', () => {
    render(
      <BrushSplitTable
        brushSplits={mockBrushSplits}
        onSave={mockOnSave}
        onSelectionChange={mockOnSelectionChange}
      />
    );

    // Find the enabled knot field and click it
    const enabledKnotField = screen.getByDisplayValue('Test Knot');
    fireEvent.click(enabledKnotField);

    // Should be clickable and not disabled
    expect(enabledKnotField).toBeInTheDocument();
    expect(enabledKnotField).not.toBeDisabled();
  });
});
