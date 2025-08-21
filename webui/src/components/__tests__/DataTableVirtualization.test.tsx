import { render, screen, fireEvent, act } from '@testing-library/react';
import { DataTable } from '../ui/data-table';
import { ColumnDef } from '@tanstack/react-table';

// Mock data for testing
interface TestData {
  id: string;
  name: string;
  value: string;
}

const mockData: TestData[] = [
  { id: '1', name: 'Item 1', value: 'Value 1' },
  { id: '2', name: 'Item 2', value: 'Value 2' },
  { id: '3', name: 'Item 3', value: 'Value 3' },
  { id: '4', name: 'Item 4', value: 'Value 4' },
  { id: '5', name: 'Item 5', value: 'Value 5' },
];

const columns: ColumnDef<TestData>[] = [
  {
    accessorKey: 'name',
    header: 'Name',
  },
  {
    accessorKey: 'value',
    header: 'Value',
  },
];

describe('DataTable Virtualization Layout Issues', () => {
  describe('Filtering Behavior', () => {
    it('should not cause row overlap when filtering', async () => {
      await act(async () => {
        render(<DataTable columns={columns} data={mockData} searchKey='name' />);
      });

      // Get the search input
      const searchInput = screen.getByPlaceholderText('Filter name...');
      expect(searchInput).toBeInTheDocument();

      // Filter to show only one item
      fireEvent.change(searchInput, { target: { value: 'Item 1' } });

      // Check that only one row is visible
      const visibleRows = screen.getAllByRole('row');
      // Should have header row + 1 data row
      expect(visibleRows.length).toBe(2);

      // Verify the row is properly positioned and not overlapping
      const dataRow = visibleRows[1];
      const rowStyle = window.getComputedStyle(dataRow);

      // The row should have proper positioning
      expect(rowStyle.position).not.toBe('absolute');
      expect(rowStyle.zIndex).not.toBe('auto');
    });

    it('should maintain proper table structure when filtering', async () => {
      await act(async () => {
        render(<DataTable columns={columns} data={mockData} searchKey='name' />);
      });

      const searchInput = screen.getByPlaceholderText('Filter name...');
      fireEvent.change(searchInput, { target: { value: 'Item' } });

      // Check that the table structure is maintained
      const table = screen.getByRole('table');
      expect(table).toBeInTheDocument();

      // Check that rows are properly nested in table structure
      const rows = screen.getAllByRole('row');
      rows.forEach(row => {
        expect(row.tagName).toBe('TR');
      });
    });
  });

  describe('Scrolling Behavior', () => {
    it('should maintain proper row positioning during scroll', async () => {
      await act(async () => {
        render(<DataTable columns={columns} data={mockData} searchKey='name' />);
      });

      // Get the virtualized container
      const virtualizedContainer = screen.getByRole('table').parentElement;
      expect(virtualizedContainer).toBeInTheDocument();

      // Simulate scrolling
      fireEvent.scroll(virtualizedContainer!, { target: { scrollTop: 100 } });

      // Verify that rows are still properly positioned
      const rows = screen.getAllByRole('row');
      rows.forEach(row => {
        const style = window.getComputedStyle(row);
        expect(style.position).not.toBe('absolute');
      });
    });
  });

  describe('Input Editing with Virtualization', () => {
    it('should allow editing inputs in virtualized rows', async () => {
      // Create columns with editable cells
      const editableColumns: ColumnDef<TestData>[] = [
        {
          accessorKey: 'name',
          header: 'Name',
          cell: ({ row }) => (
            <input
              data-testid={`input-${row.original.id}`}
              defaultValue={row.original.name}
              onChange={() => {}}
            />
          ),
        },
        {
          accessorKey: 'value',
          header: 'Value',
        },
      ];

      await act(async () => {
        render(<DataTable columns={editableColumns} data={mockData} searchKey='name' />);
      });

      // Find and edit an input
      const firstInput = screen.getByTestId('input-1');
      expect(firstInput).toBeInTheDocument();

      fireEvent.change(firstInput, { target: { value: 'Updated Item' } });
      expect(firstInput).toHaveValue('Updated Item');
    });
  });

  describe('Performance Characteristics', () => {
    it('should maintain virtualization benefits', async () => {
      const largeData = Array.from({ length: 1000 }, (_, i) => ({
        id: `${i}`,
        name: `Item ${i}`,
        value: `Value ${i}`,
      }));

      await act(async () => {
        render(<DataTable columns={columns} data={largeData} searchKey='name' />);
      });

      // Check that not all 1000 rows are rendered
      const rows = screen.getAllByRole('row');
      // Should only render visible rows + header
      expect(rows.length).toBeLessThan(1000);
    });
  });

  describe('HTML Semantics', () => {
    it('should maintain proper HTML table structure', async () => {
      await act(async () => {
        render(<DataTable columns={columns} data={mockData} searchKey='name' />);
      });

      // Check that we have a proper table structure
      const table = screen.getByRole('table');
      expect(table).toBeInTheDocument();

      // Check that all rows are proper TR elements
      const rows = screen.getAllByRole('row');
      rows.forEach(row => {
        expect(row.tagName).toBe('TR');
      });

      // Check that cells are proper TD/TH elements
      const cells = screen.getAllByRole('cell');
      cells.forEach(cell => {
        expect(['TD', 'TH']).toContain(cell.tagName);
      });
    });
  });
});
