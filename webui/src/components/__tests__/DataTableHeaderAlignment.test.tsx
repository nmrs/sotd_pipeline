import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
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

describe('DataTable Header Alignment', () => {
  beforeEach(() => {
    // Mock window.getComputedStyle for virtualization
    Object.defineProperty(window, 'getComputedStyle', {
      value: () => ({
        getPropertyValue: () => '0px',
      }),
    });
  });

  test('should maintain proper header-body visual connection', () => {
    render(<DataTable columns={columns} data={mockData} searchKey='name' />);

    // Check that header and body are properly connected
    const table = screen.getByRole('table');
    expect(table).toBeInTheDocument();

    // Check that header cells exist
    const headerCells = screen.getAllByRole('columnheader');
    expect(headerCells).toHaveLength(2);
    expect(headerCells[0]).toHaveTextContent('Name');
    expect(headerCells[1]).toHaveTextContent('Value');

    // Check that body cells exist and align with headers
    const bodyCells = screen.getAllByRole('cell');
    expect(bodyCells.length).toBeGreaterThan(0);

    // The issue: VirtualizedTableBody renders as a div inside TableBody
    // This breaks the visual connection between header and body
    const tableBody = table.querySelector('tbody');
    const virtualizedBody = tableBody?.querySelector('div');

    // This should pass - pagination implementation has proper table structure
    expect(virtualizedBody).not.toBeInTheDocument();
  });

  test('should maintain header alignment during filtering', async () => {
    render(<DataTable columns={columns} data={mockData} searchKey='name' />);

    // Find the search input (DataTable uses 'Search all columns...' placeholder)
    const searchInput = screen.getByPlaceholderText('Search all columns...') as HTMLInputElement;
    expect(searchInput).toBeInTheDocument();

    // Filter the data - use userEvent or ensure the change event properly updates state
    await act(async () => {
      fireEvent.change(searchInput, { target: { value: 'Item 1' } });
      // Wait a bit for React state to update
      await new Promise(resolve => setTimeout(resolve, 100));
    });

    // Wait for filtering to complete - may need more time for state updates
    await waitFor(
      () => {
        // Check that only filtered rows are shown
        // The search "Item 1" should match "Item 1" but not "Item 2"
        expect(screen.getByText('Item 1')).toBeInTheDocument();
        expect(screen.queryByText('Item 2')).not.toBeInTheDocument();
      },
      { timeout: 5000 }
    );

    // The issue: Header should remain visually connected to filtered rows
    // But the virtualization structure breaks this connection
    const table = screen.getByRole('table');
    const tableBody = table.querySelector('tbody');
    const virtualizedBody = tableBody?.querySelector('div');

    // This should pass - pagination implementation maintains proper alignment
    expect(virtualizedBody).not.toBeInTheDocument();
  });

  test('should maintain proper table border structure', () => {
    render(<DataTable columns={columns} data={mockData} searchKey='name' />);

    // Check that the table has proper border structure
    const tableContainer = screen.getByRole('table').closest('.rounded-md.border');
    expect(tableContainer).toBeInTheDocument();

    // The issue: The virtualized body breaks the table border structure
    // because it's rendered as a div inside the table body
    const table = screen.getByRole('table');
    const tableBody = table.querySelector('tbody');
    const virtualizedBody = tableBody?.querySelector('div');

    // This should pass - pagination implementation has proper table structure
    expect(virtualizedBody).not.toBeInTheDocument();
  });

  test('should maintain column width consistency between header and body', () => {
    render(<DataTable columns={columns} data={mockData} searchKey='name' resizable={true} />);

    // Check that header and body cells have consistent styling
    const headerCells = screen.getAllByRole('columnheader');
    const bodyCells = screen.getAllByRole('cell');

    expect(headerCells.length).toBe(2);
    expect(bodyCells.length).toBeGreaterThan(0);

    // The issue: The virtualized structure may cause column width inconsistencies
    // because the header and body are rendered in different contexts
    const table = screen.getByRole('table');
    const tableBody = table.querySelector('tbody');
    const virtualizedBody = tableBody?.querySelector('div');

    // This should pass - pagination implementation maintains proper column alignment
    expect(virtualizedBody).not.toBeInTheDocument();
  });
});
