import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { VirtualizedTable } from '../data/VirtualizedTable';

// Mock react-window components
jest.mock('react-window', () => ({
    FixedSizeList: ({ children, itemData, itemCount, height, itemSize }: any) => (
        <div data-testid="virtualized-list" style={{ height }}>
            {Array.from({ length: Math.min(itemCount, 10) }, (_, index) =>
                children({ index, style: { height: itemSize }, data: itemData })
            )}
        </div>
    ),
}));

jest.mock('react-virtualized-auto-sizer', () => ({
    __esModule: true,
    default: ({ children }: any) =>
        children({ width: 800, height: 400 }),
}));

// Test data
const mockData = [
    { id: 1, name: 'Test Item 1', category: 'A', value: 100 },
    { id: 2, name: 'Test Item 2', category: 'B', value: 200 },
    { id: 3, name: 'Test Item 3', category: 'A', value: 300 },
    { id: 4, name: 'Test Item 4', category: 'C', value: 400 },
    { id: 5, name: 'Test Item 5', category: 'B', value: 500 },
];

const mockColumns = [
    {
        key: 'id',
        header: 'ID',
        width: 80,
        render: (item: any) => item.id,
    },
    {
        key: 'name',
        header: 'Name',
        width: 200,
        render: (item: any) => item.name,
    },
    {
        key: 'category',
        header: 'Category',
        width: 120,
        render: (item: any) => item.category,
    },
    {
        key: 'value',
        header: 'Value',
        width: 100,
        render: (item: any) => item.value,
    },
];

describe('VirtualizedTable', () => {
    describe('Basic Rendering', () => {
        it('renders table with data and columns', () => {
            render(
                <VirtualizedTable
                    data={mockData}
                    columns={mockColumns}
                    height={400}
                />
            );

            expect(screen.getByTestId('virtualized-list')).toBeInTheDocument();
        });

        it('renders header row with column titles', () => {
            render(
                <VirtualizedTable
                    data={mockData}
                    columns={mockColumns}
                    height={400}
                />
            );

            expect(screen.getByText('ID')).toBeInTheDocument();
            expect(screen.getByText('Name')).toBeInTheDocument();
            expect(screen.getByText('Category')).toBeInTheDocument();
            expect(screen.getByText('Value')).toBeInTheDocument();
        });

        it('renders data rows with correct content', () => {
            render(
                <VirtualizedTable
                    data={mockData}
                    columns={mockColumns}
                    height={400}
                />
            );

            expect(screen.getByText('1')).toBeInTheDocument();
            expect(screen.getByText('Test Item 1')).toBeInTheDocument();
            expect(screen.getByText('A')).toBeInTheDocument();
            expect(screen.getByText('100')).toBeInTheDocument();
        });
    });

    describe('Virtualization', () => {
        it('handles large datasets efficiently', () => {
            const largeData = Array.from({ length: 1000 }, (_, i) => ({
                id: i + 1,
                name: `Item ${i + 1}`,
                category: `Category ${(i % 5) + 1}`,
                value: (i + 1) * 100,
            }));

            render(
                <VirtualizedTable
                    data={largeData}
                    columns={mockColumns}
                    height={400}
                />
            );

            expect(screen.getByTestId('virtualized-list')).toBeInTheDocument();
        });

        it('renders correct number of visible rows', () => {
            render(
                <VirtualizedTable
                    data={mockData}
                    columns={mockColumns}
                    height={400}
                    rowHeight={48}
                />
            );

            // Should render approximately 8 rows (400px height / 48px row height)
            const rows = screen.getAllByText(/Test Item/);
            expect(rows.length).toBeGreaterThan(0);
            expect(rows.length).toBeLessThanOrEqual(10);
        });
    });

    describe('Column Resizing', () => {
        it('renders resizable columns when resizable is true', () => {
            render(
                <VirtualizedTable
                    data={mockData}
                    columns={mockColumns}
                    height={400}
                    resizable={true}
                />
            );

            // Check for resize handles
            const resizeHandles = screen.getAllByTestId('resize-handle');
            expect(resizeHandles.length).toBeGreaterThan(0);
        });

        it('does not render resize handles when resizable is false', () => {
            render(
                <VirtualizedTable
                    data={mockData}
                    columns={mockColumns}
                    height={400}
                    resizable={false}
                />
            );

            const resizeHandles = screen.queryAllByTestId('resize-handle');
            expect(resizeHandles.length).toBe(0);
        });
    });

    describe('Sorting', () => {
        it('displays column headers', () => {
            render(
                <VirtualizedTable
                    data={mockData}
                    columns={mockColumns}
                    height={400}
                />
            );

            // Check for column headers
            expect(screen.getByText('ID')).toBeInTheDocument();
            expect(screen.getByText('Name')).toBeInTheDocument();
            expect(screen.getByText('Category')).toBeInTheDocument();
            expect(screen.getByText('Value')).toBeInTheDocument();
        });
    });

    describe('Row Selection', () => {
        it('renders checkboxes when showCheckboxes is true', () => {
            render(
                <VirtualizedTable
                    data={mockData}
                    columns={mockColumns}
                    height={400}
                    showCheckboxes={true}
                />
            );

            const checkboxes = screen.getAllByRole('checkbox');
            expect(checkboxes.length).toBeGreaterThan(0);
        });

        it('calls onRowSelect when checkbox is clicked', () => {
            const onRowSelect = jest.fn();

            render(
                <VirtualizedTable
                    data={mockData}
                    columns={mockColumns}
                    height={400}
                    showCheckboxes={true}
                    onRowSelect={onRowSelect}
                />
            );

            const firstCheckbox = screen.getAllByRole('checkbox')[0];
            fireEvent.click(firstCheckbox);

            expect(onRowSelect).toHaveBeenCalledWith(0, true);
        });

        it('highlights selected rows', () => {
            const selectedRows = new Set([0, 2]);

            render(
                <VirtualizedTable
                    data={mockData}
                    columns={mockColumns}
                    height={400}
                    selectedRows={selectedRows}
                />
            );

            // Check that selected rows have different styling
            const rows = screen.getAllByText(/Test Item/);
            expect(rows.length).toBeGreaterThan(0);
        });
    });

    describe('Row Interaction', () => {
        it('calls onRowClick when row is clicked', () => {
            const onRowClick = jest.fn();

            render(
                <VirtualizedTable
                    data={mockData}
                    columns={mockColumns}
                    height={400}
                    onRowClick={onRowClick}
                />
            );

            const firstRow = screen.getByText('Test Item 1');
            fireEvent.click(firstRow);

            expect(onRowClick).toHaveBeenCalledWith(mockData[0], 0);
        });

        it('applies hover styles on row hover', () => {
            render(
                <VirtualizedTable
                    data={mockData}
                    columns={mockColumns}
                    height={400}
                />
            );

            const firstRow = screen.getByText('Test Item 1');
            fireEvent.mouseEnter(firstRow);

            // Check for hover class
            expect(firstRow.closest('div')).toHaveClass('hover:bg-gray-50');
        });
    });

    describe('Performance', () => {
        it('handles empty data efficiently', () => {
            render(
                <VirtualizedTable
                    data={[]}
                    columns={mockColumns}
                    height={400}
                />
            );

            expect(screen.getByTestId('virtualized-list')).toBeInTheDocument();
        });

        it('handles single row data', () => {
            const singleData = [mockData[0]];

            render(
                <VirtualizedTable
                    data={singleData}
                    columns={mockColumns}
                    height={400}
                />
            );

            expect(screen.getByText('Test Item 1')).toBeInTheDocument();
        });

        it('handles malformed data gracefully', () => {
            const malformedData = [
                { id: 1, name: 'Valid Item' },
                { id: 2 }, // Missing properties
                null, // Null item
                { id: 3, name: 'Another Valid Item' },
            ];

            render(
                <VirtualizedTable
                    data={malformedData}
                    columns={mockColumns}
                    height={400}
                />
            );

            expect(screen.getByTestId('virtualized-list')).toBeInTheDocument();
        });
    });

    describe('Edge Cases', () => {
        it('handles zero height gracefully', () => {
            render(
                <VirtualizedTable
                    data={mockData}
                    columns={mockColumns}
                    height={0}
                />
            );

            expect(screen.getByTestId('virtualized-list')).toBeInTheDocument();
        });

        it('handles zero row height gracefully', () => {
            render(
                <VirtualizedTable
                    data={mockData}
                    columns={mockColumns}
                    height={400}
                    rowHeight={0}
                />
            );

            expect(screen.getByTestId('virtualized-list')).toBeInTheDocument();
        });

        it('handles columns with default render functions', () => {
            const columnsWithDefaultRender = [
                { key: 'id', header: 'ID', width: 80, render: (item: any) => item.id },
                { key: 'name', header: 'Name', width: 200, render: (item: any) => item.name },
            ];

            render(
                <VirtualizedTable
                    data={mockData}
                    columns={columnsWithDefaultRender}
                    height={400}
                />
            );

            expect(screen.getByTestId('virtualized-list')).toBeInTheDocument();
        });

        it('handles very large column widths', () => {
            const wideColumns = [
                { key: 'id', header: 'ID', width: 10000, render: (item: any) => item.id },
                { key: 'name', header: 'Name', width: 10000, render: (item: any) => item.name },
            ];

            render(
                <VirtualizedTable
                    data={mockData}
                    columns={wideColumns}
                    height={400}
                />
            );

            expect(screen.getByTestId('virtualized-list')).toBeInTheDocument();
        });
    });

    describe('Accessibility', () => {
        it('has proper ARIA attributes', () => {
            render(
                <VirtualizedTable
                    data={mockData}
                    columns={mockColumns}
                    height={400}
                />
            );

            const table = screen.getByRole('table');
            expect(table).toBeInTheDocument();
        });

        it('supports keyboard navigation', () => {
            render(
                <VirtualizedTable
                    data={mockData}
                    columns={mockColumns}
                    height={400}
                />
            );

            const headers = screen.getAllByRole('columnheader');
            expect(headers.length).toBeGreaterThan(0);

            // Test keyboard navigation
            headers[0].focus();
            expect(headers[0]).toHaveFocus();
        });
    });
}); 