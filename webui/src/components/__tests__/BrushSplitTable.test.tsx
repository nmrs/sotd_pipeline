import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import BrushSplitTable from '../BrushSplitTable';
import type { BrushSplit } from '../BrushSplitTable';

describe('BrushSplitTable - Should Not Split Feature', () => {
    const mockBrushSplits: BrushSplit[] = [
        {
            original: 'Test Brush 1',
            handle: 'Test Handle',
            knot: 'Test Knot',
            match_type: 'regex',
            should_not_split: false
        },
        {
            original: 'Test Brush 2',
            handle: null,
            knot: 'Test Brush 2',
            match_type: 'none',
            should_not_split: true
        }
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

        // First brush should not have should_not_split checked
        const firstCheckbox = screen.getAllByRole('checkbox')[1]; // Skip selection checkbox
        expect(firstCheckbox).not.toBeChecked();

        // Second brush should have should_not_split checked
        const secondCheckbox = screen.getAllByRole('checkbox')[3]; // Skip selection checkbox
        expect(secondCheckbox).toBeChecked();
    });

    test('clicking should not split checkbox calls onSave with updated data', () => {
        render(
            <BrushSplitTable
                brushSplits={mockBrushSplits}
                onSave={mockOnSave}
                onSelectionChange={mockOnSelectionChange}
            />
        );

        const shouldNotSplitCheckbox = screen.getAllByRole('checkbox')[1]; // Skip selection checkbox
        fireEvent.click(shouldNotSplitCheckbox);

        expect(mockOnSave).toHaveBeenCalledWith(0, {
            ...mockBrushSplits[0],
            should_not_split: true
        });
    });

    test('handle and knot fields are disabled when should_not_split is true', () => {
        render(
            <BrushSplitTable
                brushSplits={mockBrushSplits}
                onSave={mockOnSave}
                onSelectionChange={mockOnSelectionChange}
            />
        );

        // For the second brush (should_not_split: true), fields should show as disabled
        const disabledFields = screen.getAllByText('(disabled)');
        expect(disabledFields.length).toBe(2); // One for handle, one for knot
    });

    test('status shows no-split when should_not_split is true', () => {
        render(
            <BrushSplitTable
                brushSplits={mockBrushSplits}
                onSave={mockOnSave}
                onSelectionChange={mockOnSelectionChange}
            />
        );

        // Check that the status shows 'no-split' for the second brush
        const statusElements = screen.getAllByText('no-split');
        expect(statusElements.length).toBeGreaterThan(0);
    });

    test('clicking handle field does nothing when should_not_split is true', () => {
        render(
            <BrushSplitTable
                brushSplits={mockBrushSplits}
                onSave={mockOnSave}
                onSelectionChange={mockOnSelectionChange}
            />
        );

        // Find the disabled handle field and click it
        const disabledFields = screen.getAllByText('(disabled)');
        const disabledHandleField = disabledFields[0]; // First disabled field is handle
        fireEvent.click(disabledHandleField);

        // Should not trigger any save operations
        expect(mockOnSave).not.toHaveBeenCalled();
    });

    test('clicking knot field does nothing when should_not_split is true', () => {
        render(
            <BrushSplitTable
                brushSplits={mockBrushSplits}
                onSave={mockOnSave}
                onSelectionChange={mockOnSelectionChange}
            />
        );

        // Find the disabled knot field and click it
        const disabledFields = screen.getAllByText('(disabled)');
        const disabledKnotField = disabledFields[1]; // Second disabled field is knot
        fireEvent.click(disabledKnotField);

        // Should not trigger any save operations
        expect(mockOnSave).not.toHaveBeenCalled();
    });
}); 