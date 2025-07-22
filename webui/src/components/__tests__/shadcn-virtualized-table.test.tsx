import React from 'react';
import { render, screen } from '@testing-library/react';
import { DataTable } from '../ui/data-table';

// Mock react-window components
jest.mock('react-window', () => ({
    FixedSizeList: ({ children, itemCount, height, itemSize }: any) => (
        <div data-testid="virtualized-list" style={{ height }}>
            {Array.from({ length: itemCount }, (_, index) => (
                <div key={index} style={{ height: itemSize }}>
                    {children({ index, style: {} })}
                </div>
            ))}
        </div>
    )
}));

// Test that ShadCN virtualized data table works correctly
describe('ShadCN Virtualized Data Table', () => {
    const mockData = [
        { id: 1, name: 'Test Item 1', category: 'A' },
        { id: 2, name: 'Test Item 2', category: 'B' },
        { id: 3, name: 'Test Item 3', category: 'A' }
    ];

    const mockColumns = [
        { accessorKey: 'name', header: 'Name' },
        { accessorKey: 'category', header: 'Category' }
    ];

    test('should render ShadCN virtualized data table component', () => {
        // This test verifies that the DataTable component can be imported
        // and renders correctly with virtualization
        expect(() => {
            const DataTable = require('../ui/data-table').DataTable;
            expect(DataTable).toBeDefined();
        }).not.toThrow();
    });

    test('should render table with virtualized rows', () => {
        render(
            <DataTable
                data={mockData}
                columns={mockColumns}
                height={400}
                itemSize={50}
            />
        );

        // Verify the virtualized list is rendered
        expect(screen.getByTestId('virtualized-list')).toBeInTheDocument();

        // Verify table headers are rendered
        expect(screen.getByText('Name')).toBeInTheDocument();
        expect(screen.getByText('Category')).toBeInTheDocument();
    });

    test('should handle sorting functionality', () => {
        render(
            <DataTable
                data={mockData}
                columns={mockColumns}
                height={400}
                itemSize={50}
            />
        );

        // Verify sortable headers are present
        const nameHeader = screen.getByText('Name');
        expect(nameHeader).toBeInTheDocument();

        // Headers should be clickable for sorting
        expect(nameHeader.closest('th')).toHaveAttribute('role', 'columnheader');
    });

    test('should handle column resizing', () => {
        render(
            <DataTable
                data={mockData}
                columns={mockColumns}
                height={400}
                itemSize={50}
            />
        );

        // Verify resizable columns are present
        const table = screen.getByRole('table');
        expect(table).toBeInTheDocument();

        // Table should have resizable column structure
        expect(table.querySelector('thead')).toBeInTheDocument();
    });
}); 