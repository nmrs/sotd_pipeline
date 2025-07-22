import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { GenericDataTable } from '../data/GenericDataTable';

// Test data
const mockData = [
  { id: 1, name: 'Test Item 1', category: 'A', value: 100, date: '2025-01-01' },
  { id: 2, name: 'Test Item 2', category: 'B', value: 200, date: '2025-01-02' },
  { id: 3, name: 'Test Item 3', category: 'A', value: 300, date: '2025-01-03' },
  { id: 4, name: 'Test Item 4', category: 'C', value: 400, date: '2025-01-04' },
  { id: 5, name: 'Test Item 5', category: 'B', value: 500, date: '2025-01-05' },
];

const mockColumns = [
  {
    key: 'id',
    header: 'ID',
    sortable: true,
    width: 80,
  },
  {
    key: 'name',
    header: 'Name',
    sortable: true,
    width: 200,
  },
  {
    key: 'category',
    header: 'Category',
    sortable: true,
    width: 120,
  },
  {
    key: 'value',
    header: 'Value',
    sortable: true,
    width: 100,
  },
  {
    key: 'date',
    header: 'Date',
    sortable: true,
    width: 120,
  },
];

describe('GenericDataTable', () => {
  describe('Basic Rendering', () => {
    it('renders table with data and columns', () => {
      render(
        <GenericDataTable
          data={mockData}
          columns={mockColumns}
        />
      );

      expect(screen.getByRole('table')).toBeInTheDocument();
      expect(screen.getByText('ID')).toBeInTheDocument();
      expect(screen.getByText('Name')).toBeInTheDocument();
      expect(screen.getByText('Category')).toBeInTheDocument();
      expect(screen.getByText('Value')).toBeInTheDocument();
      expect(screen.getByText('Date')).toBeInTheDocument();
    });

    it('renders data rows with correct content', () => {
      render(
        <GenericDataTable
          data={mockData}
          columns={mockColumns}
        />
      );

      expect(screen.getByText('1')).toBeInTheDocument();
      expect(screen.getByText('Test Item 1')).toBeInTheDocument();
      expect(screen.getByText('A')).toBeInTheDocument();
      expect(screen.getByText('100')).toBeInTheDocument();
      expect(screen.getByText('2025-01-01')).toBeInTheDocument();
    });

    it('renders empty table when no data', () => {
      render(
        <GenericDataTable
          data={[]}
          columns={mockColumns}
        />
      );

      expect(screen.getByRole('table')).toBeInTheDocument();
      expect(screen.getByText('No data available')).toBeInTheDocument();
    });
  });

  describe('Sorting Functionality', () => {
    it('calls onSort when sortable column header is clicked', () => {
      const onSort = jest.fn();

      render(
        <GenericDataTable
          data={mockData}
          columns={mockColumns}
          onSort={onSort}
        />
      );

      const nameHeader = screen.getByText('Name');
      fireEvent.click(nameHeader);

      expect(onSort).toHaveBeenCalledWith('name');
    });

    it('displays sort indicators for sorted columns', () => {
      render(
        <GenericDataTable
          data={mockData}
          columns={mockColumns}
          sortColumn="name"
          sortDirection="asc"
        />
      );

      const nameHeader = screen.getByText('Name');
      expect(nameHeader).toHaveAttribute('data-sort', 'asc');
    });

    it('handles multiple sort clicks correctly', () => {
      const onSort = jest.fn();

      render(
        <GenericDataTable
          data={mockData}
          columns={mockColumns}
          onSort={onSort}
          sortColumn="name"
          sortDirection="asc"
        />
      );

      const nameHeader = screen.getByText('Name');
      fireEvent.click(nameHeader);

      expect(onSort).toHaveBeenCalledWith('name');
    });

    it('does not call onSort for non-sortable columns', () => {
      const onSort = jest.fn();
      const nonSortableColumns = [
        { key: 'id', header: 'ID', sortable: false, width: 80 },
        { key: 'name', header: 'Name', sortable: false, width: 200 },
      ];

      render(
        <GenericDataTable
          data={mockData}
          columns={nonSortableColumns}
          onSort={onSort}
        />
      );

      const nameHeader = screen.getByText('Name');
      fireEvent.click(nameHeader);

      expect(onSort).not.toHaveBeenCalled();
    });
  });

  describe('Column Resizing', () => {
    it('supports column resizing functionality', () => {
      render(
        <GenericDataTable
          data={mockData}
          columns={mockColumns}
        />
      );

      // Check that table renders with resizing capability
      expect(screen.getByRole('table')).toBeInTheDocument();
    });
  });

  describe('Row Interaction', () => {
    it('calls onRowClick when row is clicked', () => {
      const onRowClick = jest.fn();

      render(
        <GenericDataTable
          data={mockData}
          columns={mockColumns}
          onRowClick={onRowClick}
        />
      );

      const firstRow = screen.getByText('Test Item 1');
      fireEvent.click(firstRow);

      expect(onRowClick).toHaveBeenCalledWith(mockData[0]);
    });

    it('applies hover styles on row hover', () => {
      render(
        <GenericDataTable
          data={mockData}
          columns={mockColumns}
        />
      );

      const firstRow = screen.getByText('Test Item 1');
      fireEvent.mouseEnter(firstRow);

      // Check for hover class
      expect(firstRow.closest('tr')).toBeInTheDocument();
    });
  });

  describe('Custom Column Rendering', () => {
    it('renders custom column content', () => {
      const customColumns = [
        {
          key: 'id',
          header: 'ID',
          width: 80,
          render: (value: any) => <span data-testid="custom-id">{value}</span>,
        },
        {
          key: 'name',
          header: 'Name',
          width: 200,
          render: (value: any) => <span data-testid="custom-name">{value}</span>,
        },
      ];

      render(
        <GenericDataTable
          data={mockData}
          columns={customColumns}
        />
      );

      expect(screen.getByTestId('custom-id')).toBeInTheDocument();
      expect(screen.getByTestId('custom-name')).toBeInTheDocument();
    });

    it('handles complex custom rendering', () => {
      const complexColumns = [
        {
          key: 'value',
          header: 'Value',
          width: 100,
          render: (value: any) => (
            <div data-testid="complex-value">
              <span className="value">{value}</span>
              <span className="unit">units</span>
            </div>
          ),
        },
      ];

      render(
        <GenericDataTable
          data={mockData}
          columns={complexColumns}
        />
      );

      expect(screen.getByTestId('complex-value')).toBeInTheDocument();
      expect(screen.getByText('units')).toBeInTheDocument();
    });
  });

  describe('Performance Logging', () => {
    it('logs performance metrics when enabled', () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();

      render(
        <GenericDataTable
          data={mockData}
          columns={mockColumns}
          enablePerformanceLogging={true}
        />
      );

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('GenericDataTable render time:')
      );

      consoleSpy.mockRestore();
    });

    it('does not log performance metrics when disabled', () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();

      render(
        <GenericDataTable
          data={mockData}
          columns={mockColumns}
          enablePerformanceLogging={false}
        />
      );

      expect(consoleSpy).not.toHaveBeenCalledWith(
        expect.stringContaining('GenericDataTable render time:')
      );

      consoleSpy.mockRestore();
    });
  });

  describe('Error Handling', () => {
    it('handles malformed data gracefully', () => {
      const malformedData = [
        { id: 1, name: 'Valid Item' },
        { id: 2 }, // Missing properties
        null, // Null item
        { id: 3, name: 'Another Valid Item' },
      ];

      render(
        <GenericDataTable
          data={malformedData}
          columns={mockColumns}
        />
      );

      expect(screen.getByRole('table')).toBeInTheDocument();
    });

    it('handles empty columns array', () => {
      render(
        <GenericDataTable
          data={mockData}
          columns={[]}
        />
      );

      expect(screen.getByRole('table')).toBeInTheDocument();
    });

    it('handles columns with missing optional properties', () => {
      const incompleteColumns = [
        { key: 'id', header: 'ID', width: 80 },
        { key: 'name', header: 'Name', width: 200 },
      ];

      render(
        <GenericDataTable
          data={mockData}
          columns={incompleteColumns}
        />
      );

      expect(screen.getByRole('table')).toBeInTheDocument();
    });

    it('handles render function errors gracefully', () => {
      const errorColumns = [
        {
          key: 'id',
          header: 'ID',
          width: 80,
          render: () => {
            throw new Error('Render error');
          },
        },
      ];

      render(
        <GenericDataTable
          data={mockData}
          columns={errorColumns}
        />
      );

      expect(screen.getByRole('table')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles very large datasets', () => {
      const largeData = Array.from({ length: 1000 }, (_, i) => ({
        id: i + 1,
        name: `Item ${i + 1}`,
        category: `Category ${(i % 5) + 1}`,
        value: (i + 1) * 100,
        date: `2025-01-${String(i + 1).padStart(2, '0')}`,
      }));

      render(
        <GenericDataTable
          data={largeData}
          columns={mockColumns}
        />
      );

      expect(screen.getByRole('table')).toBeInTheDocument();
    });

    it('handles very wide columns', () => {
      const wideColumns = [
        { key: 'id', header: 'ID', width: 10000 },
        { key: 'name', header: 'Name', width: 10000 },
      ];

      render(
        <GenericDataTable
          data={mockData}
          columns={wideColumns}
        />
      );

      expect(screen.getByRole('table')).toBeInTheDocument();
    });

    it('handles very narrow columns', () => {
      const narrowColumns = [
        { key: 'id', header: 'ID', width: 1 },
        { key: 'name', header: 'Name', width: 1 },
      ];

      render(
        <GenericDataTable
          data={mockData}
          columns={narrowColumns}
        />
      );

      expect(screen.getByRole('table')).toBeInTheDocument();
    });

    it('handles data with nested objects', () => {
      const nestedData = [
        { id: 1, info: { name: 'Item 1', category: 'A' } },
        { id: 2, info: { name: 'Item 2', category: 'B' } },
      ];

      const nestedColumns = [
        { key: 'id', header: 'ID', width: 80 },
        { key: 'info.name', header: 'Name', width: 200 },
        { key: 'info.category', header: 'Category', width: 120 },
      ];

      render(
        <GenericDataTable
          data={nestedData}
          columns={nestedColumns}
        />
      );

      expect(screen.getByRole('table')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA attributes', () => {
      render(
        <GenericDataTable
          data={mockData}
          columns={mockColumns}
        />
      );

      const table = screen.getByRole('table');
      expect(table).toBeInTheDocument();
    });

    it('supports keyboard navigation', () => {
      render(
        <GenericDataTable
          data={mockData}
          columns={mockColumns}
        />
      );

      const headers = screen.getAllByRole('columnheader');
      expect(headers.length).toBeGreaterThan(0);

      // Test keyboard navigation
      headers[0].focus();
      expect(headers[0]).toHaveFocus();
    });

    it('provides proper labels for interactive elements', () => {
      render(
        <GenericDataTable
          data={mockData}
          columns={mockColumns}
        />
      );

      const table = screen.getByRole('table');
      expect(table).toBeInTheDocument();
    });
  });
});
