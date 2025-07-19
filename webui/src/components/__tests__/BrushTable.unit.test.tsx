// import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import BrushTable from '../BrushTable';
import { BrushData } from '../../utils/brushDataTransformer';

// Mock the VirtualizedTable component (ESM default export)
jest.mock('../VirtualizedTable', () => ({
    __esModule: true,
    default: function MockVirtualizedTable(props: any) {
        return (
            <div data-testid="virtualized-table" style={{ height: props.height }}>
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
    }
}));

// Mock the FilteredEntryCheckbox component (ESM default export)
jest.mock('../FilteredEntryCheckbox', () => ({
    __esModule: true,
    default: function MockFilteredEntryCheckbox(props: any) {
        return (
            <input
                data-testid={`checkbox-${props.itemName}`}
                type="checkbox"
                onChange={(e) => props.onStatusChange(e.target.checked)}
                className="mock-filtered-checkbox"
            />
        );
    }
}));

// Mock data for testing
const mockBrushData: BrushData[] = [
    {
        main: {
            text: 'Simpson Chubby 2',
            count: 5,
            comment_ids: ['123', '456'],
            examples: ['Example 1', 'Example 2'],
            status: 'Matched'
        },
        components: {
            handle: {
                text: 'Simpson Chubby 2',
                status: 'Matched'
            },
            knot: {
                text: 'Simpson Badger',
                status: 'Matched'
            }
        }
    },
    {
        main: {
            text: 'Declaration B15',
            count: 3,
            comment_ids: ['789'],
            examples: ['Example 3'],
            status: 'Unmatched'
        },
        components: {
            handle: {
                text: 'Declaration B15',
                status: 'Unmatched',
                pattern: 'Declaration'
            },
            knot: {
                text: 'Declaration Badger',
                status: 'Unmatched',
                pattern: 'Declaration'
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

describe('BrushTable Unit Tests', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('Component Rendering', () => {
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

            // Check that the table container exists
            expect(screen.getByTestId('virtualized-table')).toBeInTheDocument();

            // Check that rows are rendered
            expect(screen.getByTestId('table-row-0')).toBeInTheDocument();
            expect(screen.getByTestId('table-row-1')).toBeInTheDocument();
        });

        test('should render empty table when no data provided', () => {
            render(
                <BrushTable
                    items={[]}
                    onBrushFilter={mockOnBrushFilter}
                    onComponentFilter={mockOnComponentFilter}
                    filteredStatus={{}}
                    pendingChanges={{}}
                    columnWidths={mockColumnWidths}
                />
            );

            // Check that the empty state message is displayed
            expect(screen.getByText('No unmatched brushes found for the selected criteria.')).toBeInTheDocument();

            // Check that headers are still displayed
            expect(screen.getByText('Filtered')).toBeInTheDocument();
            expect(screen.getByText('Brush')).toBeInTheDocument();
            expect(screen.getByText('Count')).toBeInTheDocument();
            expect(screen.getByText('Comment IDs')).toBeInTheDocument();
            expect(screen.getByText('Examples')).toBeInTheDocument();

            // Check that footer shows 0 items
            expect(screen.getByText('Showing 0 of 0 items')).toBeInTheDocument();
        });

        test('should render brush text in item column', () => {
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

            // Check that brush text is displayed
            expect(screen.getByText('Simpson Chubby 2')).toBeInTheDocument();
            expect(screen.getByText('Declaration B15')).toBeInTheDocument();
        });

        test('should render count in count column', () => {
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

            // Check that counts are displayed
            expect(screen.getByText('5')).toBeInTheDocument();
            expect(screen.getByText('3')).toBeInTheDocument();
        });

        test('should render comment IDs in comment_ids column', () => {
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

            // Check that comment IDs are displayed
            expect(screen.getByText('123, 456')).toBeInTheDocument();
            expect(screen.getByText('789')).toBeInTheDocument();
        });

        test('should render examples in examples column', () => {
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

            // Check that examples are displayed
            expect(screen.getByText('Example 1, Example 2')).toBeInTheDocument();
            expect(screen.getByText('Example 3')).toBeInTheDocument();
        });
    });

    describe('Checkbox Interactions', () => {
        test('should render checkboxes for each brush item', () => {
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

            // Check that checkboxes are rendered for each brush
            expect(screen.getByTestId('checkbox-Simpson Chubby 2')).toBeInTheDocument();
            expect(screen.getByTestId('checkbox-Declaration B15')).toBeInTheDocument();
        });

        test('should call onBrushFilter when checkbox is clicked', async () => {
            const user = userEvent.setup();

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

            const checkbox = screen.getByTestId('checkbox-Simpson Chubby 2');
            await user.click(checkbox);

            expect(mockOnBrushFilter).toHaveBeenCalledWith('Simpson Chubby 2', true);
        });

        test('should handle multiple checkbox interactions', async () => {
            const user = userEvent.setup();

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

            const checkbox1 = screen.getByTestId('checkbox-Simpson Chubby 2');
            const checkbox2 = screen.getByTestId('checkbox-Declaration B15');

            await user.click(checkbox1);
            await user.click(checkbox2);

            expect(mockOnBrushFilter).toHaveBeenCalledTimes(2);
            expect(mockOnBrushFilter).toHaveBeenCalledWith('Simpson Chubby 2', true);
            expect(mockOnBrushFilter).toHaveBeenCalledWith('Declaration B15', true);
        });
    });

    describe('Props Validation', () => {
        test('should handle missing onComponentFilter prop', () => {
            render(
                <BrushTable
                    items={mockBrushData}
                    onBrushFilter={mockOnBrushFilter}
                    onComponentFilter={undefined as any}
                    filteredStatus={{}}
                    pendingChanges={{}}
                    columnWidths={mockColumnWidths}
                />
            );

            // Should render without errors
            expect(screen.getByTestId('virtualized-table')).toBeInTheDocument();
        });

        test('should handle missing filteredStatus prop', () => {
            render(
                <BrushTable
                    items={mockBrushData}
                    onBrushFilter={mockOnBrushFilter}
                    onComponentFilter={mockOnComponentFilter}
                    filteredStatus={undefined as any}
                    pendingChanges={{}}
                    columnWidths={mockColumnWidths}
                />
            );

            // Should render without errors
            expect(screen.getByTestId('virtualized-table')).toBeInTheDocument();
        });

        test('should handle missing pendingChanges prop', () => {
            render(
                <BrushTable
                    items={mockBrushData}
                    onBrushFilter={mockOnBrushFilter}
                    onComponentFilter={mockOnComponentFilter}
                    filteredStatus={{}}
                    pendingChanges={undefined as any}
                    columnWidths={mockColumnWidths}
                />
            );

            // Should render without errors
            expect(screen.getByTestId('virtualized-table')).toBeInTheDocument();
        });
    });

    describe('Error Handling', () => {
        test('should handle malformed brush data gracefully', () => {
            const malformedData = [
                {
                    main: {
                        text: 'Valid Brush',
                        count: 1,
                        comment_ids: ['123'],
                        examples: ['Example'],
                        status: 'Matched'
                    },
                    components: {
                        // Missing components - should not crash
                    }
                }
            ];

            render(
                <BrushTable
                    items={malformedData as any}
                    onBrushFilter={mockOnBrushFilter}
                    onComponentFilter={mockOnComponentFilter}
                    filteredStatus={{}}
                    pendingChanges={{}}
                    columnWidths={mockColumnWidths}
                />
            );

            // Should render without crashing
            expect(screen.getByTestId('virtualized-table')).toBeInTheDocument();
            expect(screen.getByText('Valid Brush')).toBeInTheDocument();
        });

        test('should handle null/undefined data gracefully', () => {
            render(
                <BrushTable
                    items={null as any}
                    onBrushFilter={mockOnBrushFilter}
                    onComponentFilter={mockOnComponentFilter}
                    filteredStatus={{}}
                    pendingChanges={{}}
                    columnWidths={mockColumnWidths}
                />
            );

            // Should render without crashing and show empty state
            expect(screen.getByText('No unmatched brushes found for the selected criteria.')).toBeInTheDocument();
        });
    });

    describe('Performance', () => {
        test('should render large datasets efficiently', () => {
            const largeDataset = Array.from({ length: 100 }, (_, i) => ({
                main: {
                    text: `Brush ${i}`,
                    count: i,
                    comment_ids: [`comment-${i}`],
                    examples: [`example-${i}`],
                    status: 'Matched' as const
                },
                components: {
                    handle: {
                        text: `Handle ${i}`,
                        status: 'Matched' as const
                    }
                }
            }));

            const startTime = performance.now();

            render(
                <BrushTable
                    items={largeDataset}
                    onBrushFilter={mockOnBrushFilter}
                    onComponentFilter={mockOnComponentFilter}
                    filteredStatus={{}}
                    pendingChanges={{}}
                    columnWidths={mockColumnWidths}
                />
            );

            const renderTime = performance.now() - startTime;

            // Should render in reasonable time (under 100ms for 100 items)
            expect(renderTime).toBeLessThan(100);
            expect(screen.getByTestId('virtualized-table')).toBeInTheDocument();
        });
    });
}); 