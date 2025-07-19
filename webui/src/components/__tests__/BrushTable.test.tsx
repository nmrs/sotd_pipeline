// import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import BrushTable from '../BrushTable';
import { BrushData } from '../../utils/brushDataTransformer';

// Mock the FilteredEntryCheckbox component
jest.mock('../FilteredEntryCheckbox', () => {
    return function MockFilteredEntryCheckbox(props: any) {
        return (
            <div data-testid={`checkbox-${props.itemName}`}>
                <input
                    type="checkbox"
                    checked={props.isFiltered}
                    onChange={(e: any) => props.onStatusChange?.(e.target.checked)}
                    data-testid={`checkbox-input-${props.itemName}`}
                />
            </div>
        );
    };
});

const mockBrushData: BrushData[] = [
    {
        main: {
            text: 'Test Brush',
            count: 5,
            comment_ids: ['comment1', 'comment2'],
            examples: ['example1', 'example2'],
            status: 'Unmatched' as const
        },
        components: {
            handle: {
                text: 'Test Handle',
                status: 'Unmatched' as const,
                pattern: undefined
            },
            knot: {
                text: 'Test Knot',
                status: 'Unmatched' as const,
                pattern: undefined
            }
        }
    }
];

const mockColumnWidths = {
    filtered: 100,
    brush: 200,
    handle: 150,
    knot: 150,
    count: 80,
    comment_ids: 150,
    examples: 200
};

const mockOnBrushFilter = jest.fn();
const mockOnComponentFilter = jest.fn();

describe('BrushTable', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    test('should render brush table with correct structure', () => {
        render(
            <BrushTable
                items={mockBrushData}
                onBrushFilter={mockOnBrushFilter}
                onComponentFilter={mockOnComponentFilter}
                filteredStatus={{}}
                pendingChanges={{}}
                columnWidths={mockColumnWidths}
            />
        );

        // Check that the main brush checkbox is rendered
        expect(screen.getByTestId('checkbox-Test Brush')).toBeInTheDocument();
        expect(screen.getByTestId('checkbox-input-Test Brush')).toBeInTheDocument();

        // Check that component checkboxes are rendered
        expect(screen.getByTestId('checkbox-Test Handle')).toBeInTheDocument();
        expect(screen.getByTestId('checkbox-Test Knot')).toBeInTheDocument();
    });

    test('should pass correct isFiltered prop to checkboxes', () => {
        const filteredStatus = {
            'Test Brush': true,
            'Test Handle': false,
            'Test Knot': true
        };

        render(
            <BrushTable
                items={mockBrushData}
                onBrushFilter={mockOnBrushFilter}
                onComponentFilter={mockOnComponentFilter}
                filteredStatus={filteredStatus}
                pendingChanges={{}}
                columnWidths={mockColumnWidths}
            />
        );

        // Check that the main brush checkbox is checked
        const mainCheckbox = screen.getByTestId('checkbox-input-Test Brush') as HTMLInputElement;
        expect(mainCheckbox.checked).toBe(true);

        // Check that handle checkbox is unchecked
        const handleCheckbox = screen.getByTestId('checkbox-input-Test Handle') as HTMLInputElement;
        expect(handleCheckbox.checked).toBe(false);

        // Check that knot checkbox is checked
        const knotCheckbox = screen.getByTestId('checkbox-input-Test Knot') as HTMLInputElement;
        expect(knotCheckbox.checked).toBe(true);
    });

    test('should call onBrushFilter when main checkbox is clicked', () => {
        render(
            <BrushTable
                items={mockBrushData}
                onBrushFilter={mockOnBrushFilter}
                onComponentFilter={mockOnComponentFilter}
                filteredStatus={{}}
                pendingChanges={{}}
                columnWidths={mockColumnWidths}
            />
        );

        const mainCheckbox = screen.getByTestId('checkbox-input-Test Brush');
        fireEvent.click(mainCheckbox);

        expect(mockOnBrushFilter).toHaveBeenCalledWith('Test Brush', true);
    });

    test('should call onComponentFilter when component checkbox is clicked', () => {
        render(
            <BrushTable
                items={mockBrushData}
                onBrushFilter={mockOnBrushFilter}
                onComponentFilter={mockOnComponentFilter}
                filteredStatus={{}}
                pendingChanges={{}}
                columnWidths={mockColumnWidths}
            />
        );

        const handleCheckbox = screen.getByTestId('checkbox-input-Test Handle');
        fireEvent.click(handleCheckbox);

        expect(mockOnComponentFilter).toHaveBeenCalledWith('Test Handle', true);
    });
}); 