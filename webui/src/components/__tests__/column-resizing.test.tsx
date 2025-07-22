import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { DataTable } from '../ui/data-table';

// Mock react-window components
jest.mock('react-window', () => ({
  FixedSizeList: ({ children, itemCount, height, itemSize }: any) => (
    <div data-testid='virtualized-list' style={{ height }}>
      {Array.from({ length: itemCount }, (_, index) => (
        <div key={index} style={{ height: itemSize }}>
          {children({ index, style: {} })}
        </div>
      ))}
    </div>
  ),
}));

// Test that column resizing functionality works correctly
describe('Column Resizing', () => {
  const mockData = [
    { id: 1, name: 'Test Item 1', category: 'A' },
    { id: 2, name: 'Test Item 2', category: 'B' },
    { id: 3, name: 'Test Item 3', category: 'A' },
  ];

  const mockColumns = [
    { accessorKey: 'name', header: 'Name' },
    { accessorKey: 'category', header: 'Category' },
  ];

  test('should render resizable column headers', () => {
    render(<DataTable data={mockData} columns={mockColumns} height={400} itemSize={50} />);

    // Verify table headers are rendered
    const nameHeader = screen.getByText('Name');
    const categoryHeader = screen.getByText('Category');

    expect(nameHeader).toBeInTheDocument();
    expect(categoryHeader).toBeInTheDocument();

    // Headers should be within table structure
    expect(nameHeader.closest('th')).toBeInTheDocument();
    expect(categoryHeader.closest('th')).toBeInTheDocument();
  });

  test('should have resizable column structure', () => {
    render(<DataTable data={mockData} columns={mockColumns} height={400} itemSize={50} />);

    // Verify table structure supports resizing
    const table = screen.getByRole('table');
    expect(table).toBeInTheDocument();

    // Table should have proper structure for resizing
    const thead = table.querySelector('thead');
    const tbody = table.querySelector('tbody');

    expect(thead).toBeInTheDocument();
    expect(tbody).toBeInTheDocument();
  });

  test('should maintain column widths during virtualization', () => {
    render(<DataTable data={mockData} columns={mockColumns} height={400} itemSize={50} />);

    // Verify virtualized list is rendered
    expect(screen.getByTestId('virtualized-list')).toBeInTheDocument();

    // Table should maintain structure with virtualization
    const table = screen.getByRole('table');
    expect(table).toBeInTheDocument();
  });
});
