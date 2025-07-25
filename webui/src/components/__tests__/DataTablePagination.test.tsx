import { render, screen, fireEvent, waitFor } from '@testing-library/react';
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
  { id: '6', name: 'Item 6', value: 'Value 6' },
  { id: '7', name: 'Item 7', value: 'Value 7' },
  { id: '8', name: 'Item 8', value: 'Value 8' },
  { id: '9', name: 'Item 9', value: 'Value 9' },
  { id: '10', name: 'Item 10', value: 'Value 10' },
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

describe('DataTable Pagination', () => {
  beforeEach(() => {
    // Mock window.getComputedStyle for any remaining virtualization code
    Object.defineProperty(window, 'getComputedStyle', {
      value: () => ({
        getPropertyValue: () => '0px',
      }),
    });
  });

  test('should render standard table structure without virtualization', () => {
    render(<DataTable columns={columns} data={mockData} showPagination={true} />);

    // Check that table has proper structure
    const table = screen.getByRole('table');
    expect(table).toBeInTheDocument();

    // Check that header and body are properly connected
    const headerCells = screen.getAllByRole('columnheader');
    expect(headerCells).toHaveLength(2);
    expect(headerCells[0]).toHaveTextContent('Name');
    expect(headerCells[1]).toHaveTextContent('Value');

    // Check that body cells exist and align with headers
    const bodyCells = screen.getAllByRole('cell');
    expect(bodyCells.length).toBeGreaterThan(0);

    // Verify no virtualization divs are present
    const tableBody = table.querySelector('tbody');
    const virtualizedBody = tableBody?.querySelector('div');
    expect(virtualizedBody).not.toBeInTheDocument();
  });

  test('should show pagination controls when showPagination is true', () => {
    render(<DataTable columns={columns} data={mockData} showPagination={true} />);

    // Check for pagination controls
    expect(screen.getByText('Rows per page')).toBeInTheDocument();
    expect(screen.getByText('1-10 of 10')).toBeInTheDocument();
  });

  test('should handle filtering with pagination', async () => {
    render(<DataTable columns={columns} data={mockData} searchKey='name' showPagination={true} />);

    // Find the search input
    const searchInput = screen.getByPlaceholderText('Filter name...');
    expect(searchInput).toBeInTheDocument();

    // Filter the data with a term that will match only one item
    fireEvent.change(searchInput, { target: { value: 'Item 5' } });

    await waitFor(() => {
      // Check that only filtered rows are shown
      expect(screen.getByText('Item 5')).toBeInTheDocument();
      expect(screen.queryByText('Item 2')).not.toBeInTheDocument();
    });

    // Verify pagination still works with filtered data
    expect(screen.getByText('1-1 of 1')).toBeInTheDocument();
  });

  test('should maintain proper table border structure', () => {
    render(<DataTable columns={columns} data={mockData} showPagination={true} />);

    // Check that the table has proper border structure
    const tableContainer = screen.getByRole('table').closest('.rounded-md.border');
    expect(tableContainer).toBeInTheDocument();

    // Verify no DOM nesting issues
    const table = screen.getByRole('table');
    const tableBody = table.querySelector('tbody');
    const virtualizedBody = tableBody?.querySelector('div');
    expect(virtualizedBody).not.toBeInTheDocument();
  });

  test('should maintain column width consistency between header and body', () => {
    render(<DataTable columns={columns} data={mockData} showPagination={true} resizable={true} />);

    // Check that header and body cells have consistent styling
    const headerCells = screen.getAllByRole('columnheader');
    const bodyCells = screen.getAllByRole('cell');

    expect(headerCells.length).toBe(2);
    expect(bodyCells.length).toBeGreaterThan(0);

    // Verify no virtualization structure that could cause width misalignment
    const table = screen.getByRole('table');
    const tableBody = table.querySelector('tbody');
    const virtualizedBody = tableBody?.querySelector('div');
    expect(virtualizedBody).not.toBeInTheDocument();
  });

  test('should work without virtualization props', () => {
    render(
      <DataTable
        columns={columns}
        data={mockData}
        showPagination={true}
        // No height or itemSize props - these should be removed
      />
    );

    // Verify table renders correctly without virtualization props
    const table = screen.getByRole('table');
    expect(table).toBeInTheDocument();

    // Verify no virtualization-related elements
    const tableBody = table.querySelector('tbody');
    const virtualizedBody = tableBody?.querySelector('div');
    expect(virtualizedBody).not.toBeInTheDocument();
  });
});
