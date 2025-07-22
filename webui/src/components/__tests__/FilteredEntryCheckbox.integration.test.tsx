// import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import FilteredEntryCheckbox from '../forms/FilteredEntryCheckbox';

// Mock the API functions to verify they're not called
jest.mock('../../services/api', () => ({
    checkFilteredStatus: jest.fn(),
    updateFilteredEntries: jest.fn(),
}));

describe('FilteredEntryCheckbox Integration', () => {
    const mockOnStatusChange = jest.fn();

    beforeEach(() => {
        jest.clearAllMocks();
    });

    test('should update checkbox state immediately without API calls', () => {
        render(
            <FilteredEntryCheckbox
                itemName="test-brush"
                commentIds={['comment1', 'comment2']}
                isFiltered={false}
                onStatusChange={mockOnStatusChange}
            />
        );

        const checkbox = screen.getByRole('checkbox');

        // Initially unchecked
        expect(checkbox).not.toBeChecked();

        // Click the checkbox
        fireEvent.click(checkbox);

        // Should call onStatusChange immediately
        expect(mockOnStatusChange).toHaveBeenCalledWith(true);
        expect(mockOnStatusChange).toHaveBeenCalledTimes(1);

        // Should NOT make any API calls
        const { checkFilteredStatus, updateFilteredEntries } = require('../../services/api');
        expect(checkFilteredStatus).not.toHaveBeenCalled();
        expect(updateFilteredEntries).not.toHaveBeenCalled();
    });

    test('should handle unchecked to checked transition', () => {
        const { rerender } = render(
            <FilteredEntryCheckbox
                itemName="test-brush"
                commentIds={['comment1']}
                isFiltered={false}
                onStatusChange={mockOnStatusChange}
            />
        );

        const checkbox = screen.getByRole('checkbox');

        // Click to check
        fireEvent.click(checkbox);
        expect(mockOnStatusChange).toHaveBeenCalledWith(true);

        // Rerender with checked state
        rerender(
            <FilteredEntryCheckbox
                itemName="test-brush"
                commentIds={['comment1']}
                isFiltered={true}
                onStatusChange={mockOnStatusChange}
            />
        );

        // Should now be checked
        expect(checkbox).toBeChecked();

        // Click to uncheck
        fireEvent.click(checkbox);
        expect(mockOnStatusChange).toHaveBeenCalledWith(false);
    });

    test('should be disabled when no comment IDs', () => {
        render(
            <FilteredEntryCheckbox
                itemName="test-brush"
                commentIds={[]}
                isFiltered={false}
                onStatusChange={mockOnStatusChange}
            />
        );

        const checkbox = screen.getByRole('checkbox');
        expect(checkbox).toBeDisabled();

        // Should not call onStatusChange when disabled
        fireEvent.click(checkbox);
        expect(mockOnStatusChange).not.toHaveBeenCalled();
    });

    test('should be disabled when disabled prop is true', () => {
        render(
            <FilteredEntryCheckbox
                itemName="test-brush"
                commentIds={['comment1']}
                isFiltered={false}
                onStatusChange={mockOnStatusChange}
                disabled={true}
            />
        );

        const checkbox = screen.getByRole('checkbox');
        expect(checkbox).toBeDisabled();

        // Should not call onStatusChange when disabled
        fireEvent.click(checkbox);
        expect(mockOnStatusChange).not.toHaveBeenCalled();
    });
}); 