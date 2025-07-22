import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { GenericDataTable } from '../GenericDataTable';

describe('GenericDataTable', () => {
    const mockData = [
        { id: 1, name: 'Item 1', count: 10, status: 'active' },
        { id: 2, name: 'Item 2', count: 5, status: 'inactive' },
        { id: 3, name: 'Item 3', count: 15, status: 'active' },
    ];

    const mockColumns = [
        { key: 'id', header: 'ID', width: 50 },
        { key: 'name', header: 'Name', width: 200 },
        { key: 'count', header: 'Count', width: 100 },
        { key: 'status', header: 'Status', width: 100 },
    ];

    describe('Basic Rendering', () => {
        test('should render table with data', () => {
            render(
                <GenericDataTable
                    data={mockData}
                    columns={mockColumns}
                />
            );

            expect(screen.getByTestId('generic-data-table')).toBeInTheDocument();
            expect(screen.getByText('Item 1')).toBeInTheDocument();
            expect(screen.getByText('Item 2')).toBeInTheDocument();
            expect(screen.getByText('Item 3')).toBeInTheDocument();
        });

        test('should render empty state when no data', () => {
            render(
                <GenericDataTable
                    data={[]}
                    columns={mockColumns}
                    emptyMessage="No items found"
                />
            );

            expect(screen.getByText('No items found')).toBeInTheDocument();
        });

        test('should render loading state', () => {
            render(
                <GenericDataTable
                    data={mockData}
                    columns={mockColumns}
                    loading={true}
                />
            );

            expect(screen.getByText('Loading...')).toBeInTheDocument();
        });
    });

    describe('Column Headers', () => {
        test('should render all column headers', () => {
            render(
                <GenericDataTable
                    data={mockData}
                    columns={mockColumns}
                />
            );

            expect(screen.getByText('ID')).toBeInTheDocument();
            expect(screen.getByText('Name')).toBeInTheDocument();
            expect(screen.getByText('Count')).toBeInTheDocument();
            expect(screen.getByText('Status')).toBeInTheDocument();
        });

        test('should show sort indicators when sorting is enabled', () => {
            const mockOnSort = jest.fn();

            render(
                <GenericDataTable
                    data={mockData}
                    columns={mockColumns}
                    onSort={mockOnSort}
                    sortColumn="name"
                    sortDirection="asc"
                />
            );

            // Check for the sort indicator span
            expect(screen.getByText('↑')).toBeInTheDocument();
        });
    });

    describe('Row Interactions', () => {
        test('should call onRowClick when row is clicked', () => {
            const mockOnRowClick = jest.fn();

            render(
                <GenericDataTable
                    data={mockData}
                    columns={mockColumns}
                    onRowClick={mockOnRowClick}
                />
            );

            fireEvent.click(screen.getByText('Item 1').closest('tr')!);
            expect(mockOnRowClick).toHaveBeenCalledWith(mockData[0]);
        });

        test('should call onSort when header is clicked', () => {
            const mockOnSort = jest.fn();

            render(
                <GenericDataTable
                    data={mockData}
                    columns={mockColumns}
                    onSort={mockOnSort}
                />
            );

            fireEvent.click(screen.getByText('Name'));
            expect(mockOnSort).toHaveBeenCalledWith('name');
        });
    });

    describe('Custom Column Rendering', () => {
        test('should use custom render function for columns', () => {
            const customColumns = [
                ...mockColumns.slice(0, -1), // Remove the original status column
                {
                    key: 'status',
                    header: 'Status',
                    render: (value: string) => (
                        <span style={{ color: value === 'active' ? 'green' : 'red' }}>
                            {value}
                        </span>
                    )
                }
            ];

            render(
                <GenericDataTable
                    data={mockData}
                    columns={customColumns}
                />
            );

            // The custom render function should be applied - check for the colored span
            const activeSpans = screen.getAllByText('active', { selector: 'span' });
            expect(activeSpans.length).toBeGreaterThan(0);
            expect(activeSpans[0]).toHaveStyle({ color: 'green' });
        });
    });

    describe('Accessibility', () => {
        test('should have proper table structure', () => {
            render(
                <GenericDataTable
                    data={mockData}
                    columns={mockColumns}
                />
            );

            const table = screen.getByRole('table');
            expect(table).toBeInTheDocument();

            const headers = screen.getAllByRole('columnheader');
            expect(headers).toHaveLength(mockColumns.length);
        });

        test('should have clickable headers when sorting is enabled', () => {
            const mockOnSort = jest.fn();

            render(
                <GenericDataTable
                    data={mockData}
                    columns={mockColumns}
                    onSort={mockOnSort}
                />
            );

            const headers = screen.getAllByRole('columnheader');
            headers.forEach(header => {
                expect(header).toHaveStyle({ cursor: 'pointer' });
            });
        });
    });

    describe('Performance', () => {
        test('should render large datasets efficiently', () => {
            const largeData = Array.from({ length: 100 }, (_, i) => ({
                id: i + 1,
                name: `Item ${i + 1}`,
                count: i * 10,
                status: i % 2 === 0 ? 'active' : 'inactive'
            }));

            const startTime = performance.now();

            render(
                <GenericDataTable
                    data={largeData}
                    columns={mockColumns}
                />
            );

            const renderTime = performance.now() - startTime;

            // Should render 100 rows in reasonable time (under 100ms for test environment)
            expect(renderTime).toBeLessThan(100);
            expect(screen.getByTestId('generic-data-table')).toBeInTheDocument();
        });
    });
}); 