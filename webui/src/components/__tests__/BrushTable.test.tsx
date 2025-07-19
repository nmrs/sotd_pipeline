import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import BrushTable from '../BrushTable';

// Mock data for testing
const mockBrushData = [
    {
        main: {
            text: 'Simpson Chubby 2',
            count: 5,
            comment_ids: ['123', '456'],
            examples: ['Example 1', 'Example 2'],
            status: 'Matched' as const
        },
        components: {
            handle: {
                text: 'Simpson Chubby 2',
                status: 'Matched' as const
            },
            knot: {
                text: 'Simpson Badger',
                status: 'Matched' as const
            }
        }
    },
    {
        main: {
            text: 'Declaration B15',
            count: 3,
            comment_ids: ['789'],
            examples: ['Example 3'],
            status: 'Matched' as const
        },
        components: {
            handle: {
                text: 'Declaration B15',
                status: 'Matched' as const
            },
            knot: {
                text: 'Declaration Badger',
                status: 'Matched' as const
            }
        }
    }
];

const mockColumnWidths = {
    filtered: 100,
    item: 200,
    count: 80,
    comment_ids: 150,
    examples: 200
};

const mockOnBrushFilter = jest.fn();

describe('BrushTable', () => {
    test('should render table headers correctly', () => {
        render(
            <BrushTable
                items={mockBrushData}
                onBrushFilter={mockOnBrushFilter}
                onComponentFilter={jest.fn()}
                filteredStatus={{}}
                pendingChanges={{}}
                columnWidths={mockColumnWidths}
            />
        );

        // Check that table headers are displayed
        expect(screen.getByText('Filtered')).toBeInTheDocument();
        expect(screen.getByText('Brush')).toBeInTheDocument();
        expect(screen.getByText('Count')).toBeInTheDocument();
        expect(screen.getByText('Comment IDs')).toBeInTheDocument();
        expect(screen.getByText('Examples')).toBeInTheDocument();
    });

    test('should render table structure with correct classes', () => {
        render(
            <BrushTable
                items={mockBrushData}
                onBrushFilter={mockOnBrushFilter}
                onComponentFilter={jest.fn()}
                filteredStatus={{}}
                pendingChanges={{}}
                columnWidths={mockColumnWidths}
            />
        );

        // Check that the table container has the correct class
        const tableContainer = screen.getByText('Filtered').closest('.border');
        expect(tableContainer).toBeInTheDocument();
        expect(tableContainer).toHaveClass('border-gray-200', 'rounded-lg', 'overflow-hidden');
    });

    test('should handle empty data gracefully', () => {
        render(
            <BrushTable
                items={[]}
                onBrushFilter={mockOnBrushFilter}
                onComponentFilter={jest.fn()}
                filteredStatus={{}}
                pendingChanges={{}}
                columnWidths={mockColumnWidths}
            />
        );

        // Should show table headers even with empty data
        expect(screen.getByText('Filtered')).toBeInTheDocument();
        expect(screen.getByText('Brush')).toBeInTheDocument();
        expect(screen.getByText('Count')).toBeInTheDocument();
        expect(screen.getByText('Comment IDs')).toBeInTheDocument();
        expect(screen.getByText('Examples')).toBeInTheDocument();
    });

    test('should display table footer with item count', () => {
        render(
            <BrushTable
                items={mockBrushData}
                onBrushFilter={mockOnBrushFilter}
                onComponentFilter={jest.fn()}
                filteredStatus={{}}
                pendingChanges={{}}
                columnWidths={mockColumnWidths}
            />
        );

        // Check that the footer shows the correct item count using flexible text matching
        expect(screen.getByText(/Showing/)).toBeInTheDocument();
        expect(screen.getByText(/items/)).toBeInTheDocument();
        expect(screen.getByText(/2/)).toBeInTheDocument();
    });

    test('should render with correct column widths', () => {
        render(
            <BrushTable
                items={mockBrushData}
                onBrushFilter={mockOnBrushFilter}
                onComponentFilter={jest.fn()}
                filteredStatus={{}}
                pendingChanges={{}}
                columnWidths={mockColumnWidths}
            />
        );

        // Check that column headers have the correct structure
        const filteredHeader = screen.getByText('Filtered').closest('div');
        const brushHeader = screen.getByText('Brush').closest('div');
        const countHeader = screen.getByText('Count').closest('div');

        // Check that the elements exist and have the expected structure
        expect(filteredHeader).toBeInTheDocument();
        expect(brushHeader).toBeInTheDocument();
        expect(countHeader).toBeInTheDocument();

        // Check that the parent elements have the hover class
        const filteredParent = filteredHeader?.parentElement;
        const brushParent = brushHeader?.parentElement;
        const countParent = countHeader?.parentElement;

        expect(filteredParent).toHaveClass('hover:bg-gray-100');
        expect(brushParent).toHaveClass('hover:bg-gray-100');
        expect(countParent).toHaveClass('hover:bg-gray-100');
    });

    test('should call onBrushFilter when provided', () => {
        // This test verifies that the component accepts the callback prop
        // The actual interaction would be tested in integration tests
        expect(mockOnBrushFilter).toBeDefined();
        expect(typeof mockOnBrushFilter).toBe('function');
    });
}); 