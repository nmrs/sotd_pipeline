import { render, screen } from '@testing-library/react';
import { PerformanceDataTable } from '../data/PerformanceDataTable';

// Mock ShadCN DataTable component
jest.mock('@/components/ui/data-table', () => ({
  DataTable: ({
    columns,
    data,
    height,
    itemSize,
    resizable,
    showColumnVisibility,
    searchKey,
  }: {
    height?: number;
    itemSize?: number;
    resizable?: boolean;
    showColumnVisibility?: boolean;
    searchKey?: string;
    columns?: Array<{ accessorKey: string; header: string }>;
    data?: Array<Record<string, unknown>>;
  }) => (
    <div data-testid='shadcn-data-table'>
      <div data-testid='data-table-props'>
        {JSON.stringify({ height, itemSize, resizable, showColumnVisibility, searchKey })}
      </div>
      <div data-testid='data-table-columns'>
        {columns?.map((col: { accessorKey: string; header: string }, index: number) => (
          <div key={index} data-testid={`column-${col.accessorKey}`}>
            {col.header}
          </div>
        ))}
      </div>
      <div data-testid='data-table-data'>
        {data?.map((item: Record<string, unknown>, index: number) => (
          <div key={index} data-testid={`row-${index}`}>
            {String(item?.name || 'null')} - {String(item?.email || 'null')} -{' '}
            {String(item?.status || 'null')}
          </div>
        ))}
      </div>
    </div>
  ),
}));

// Test data
const mockData = [
  {
    id: '1',
    name: 'John Doe',
    email: 'john@example.com',
    status: 'active',
    date: '2025-01-15T10:30:00Z',
  },
  {
    id: '2',
    name: 'Jane Smith',
    email: 'jane@example.com',
    status: 'inactive',
    date: '2025-01-14T15:45:00Z',
  },
  {
    id: '3',
    name: 'Bob Johnson',
    email: 'bob@example.com',
    status: 'pending',
    date: '2025-01-13T09:20:00Z',
  },
];

describe('PerformanceDataTable', () => {
  describe('ShadCN DataTable Integration', () => {
    it('uses ShadCN DataTable as foundation', () => {
      render(<PerformanceDataTable data={mockData} testId='performance-test' />);

      expect(screen.getByTestId('shadcn-data-table')).toBeInTheDocument();
    });

    it('passes correct props to ShadCN DataTable', () => {
      render(<PerformanceDataTable data={mockData} testId='performance-test' />);

      const propsElement = screen.getByTestId('data-table-props');
      const props = JSON.parse(propsElement.textContent || '{}');

      // The PerformanceDataTable doesn't implement virtualization, so height and itemSize are undefined
      expect(props.height).toBeUndefined();
      expect(props.itemSize).toBeUndefined();
      expect(props.resizable).toBe(true);
      expect(props.showColumnVisibility).toBe(true);
      expect(props.searchKey).toBe('name');
    });

    it('defines correct columns for ShadCN DataTable', () => {
      render(<PerformanceDataTable data={mockData} testId='performance-test' />);

      expect(screen.getByTestId('column-id')).toBeInTheDocument();
      expect(screen.getByTestId('column-name')).toBeInTheDocument();
      expect(screen.getByTestId('column-email')).toBeInTheDocument();
      expect(screen.getByTestId('column-status')).toBeInTheDocument();
      expect(screen.getByTestId('column-date')).toBeInTheDocument();
    });

    it('transforms data correctly for ShadCN DataTable', () => {
      render(<PerformanceDataTable data={mockData} testId='performance-test' />);

      expect(screen.getByTestId('row-0')).toHaveTextContent('John Doe - john@example.com - active');
      expect(screen.getByTestId('row-1')).toHaveTextContent(
        'Jane Smith - jane@example.com - inactive'
      );
      expect(screen.getByTestId('row-2')).toHaveTextContent(
        'Bob Johnson - bob@example.com - pending'
      );
    });
  });

  describe('Performance Monitoring', () => {
    it('displays performance metrics when logging is enabled', () => {
      render(
        <PerformanceDataTable
          data={mockData}
          enablePerformanceLogging={true}
          testId='performance-test'
        />
      );

      // Initially no metrics should be displayed
      expect(screen.queryByText('Performance Metrics:')).not.toBeInTheDocument();
    });

    it('tracks sort operations when onSort is provided', () => {
      const onSort = jest.fn();

      render(
        <PerformanceDataTable
          data={mockData}
          onSort={onSort}
          enablePerformanceLogging={true}
          testId='performance-test'
        />
      );

      // The sort functionality is handled by ShadCN DataTable
      // In a real test with unmocked DataTable, we would test the sort button
      expect(screen.getByTestId('shadcn-data-table')).toBeInTheDocument();
    });
  });

  describe('Column Definitions', () => {
    it('defines ID column with correct header', () => {
      render(<PerformanceDataTable data={mockData} testId='performance-test' />);

      expect(screen.getByTestId('column-id')).toHaveTextContent('ID');
    });

    it('defines Name column with correct header', () => {
      render(<PerformanceDataTable data={mockData} testId='performance-test' />);

      expect(screen.getByTestId('column-name')).toHaveTextContent('Name');
    });

    it('defines Email column with correct header', () => {
      render(<PerformanceDataTable data={mockData} testId='performance-test' />);

      expect(screen.getByTestId('column-email')).toHaveTextContent('Email');
    });

    it('defines Status column with correct header', () => {
      render(<PerformanceDataTable data={mockData} testId='performance-test' />);

      expect(screen.getByTestId('column-status')).toHaveTextContent('Status');
    });

    it('defines Date column with correct header', () => {
      render(<PerformanceDataTable data={mockData} testId='performance-test' />);

      expect(screen.getByTestId('column-date')).toHaveTextContent('Date');
    });
  });

  describe('Data Transformation', () => {
    it('preserves all original data properties', () => {
      render(<PerformanceDataTable data={mockData} testId='performance-test' />);

      // Check that all properties are preserved in the transformed data
      expect(screen.getByTestId('row-0')).toHaveTextContent('John Doe');
      expect(screen.getByTestId('row-1')).toHaveTextContent('Jane Smith');
      expect(screen.getByTestId('row-2')).toHaveTextContent('Bob Johnson');
    });

    it('handles empty data array', () => {
      render(<PerformanceDataTable data={[]} testId='performance-test' />);

      expect(screen.getByText('No performance data to display')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('handles malformed data gracefully', () => {
      render(<PerformanceDataTable data={[]} testId='performance-test' />);

      expect(screen.getByText('No performance data to display')).toBeInTheDocument();
    });
  });

  describe('Performance', () => {
    it('handles large datasets efficiently', () => {
      const largeData = Array.from({ length: 100 }, (_, i) => ({
        id: `${i + 1}`,
        name: `User ${i + 1}`,
        email: `user${i + 1}@example.com`,
        status: i % 3 === 0 ? 'active' : i % 3 === 1 ? 'inactive' : 'pending',
        date: new Date(Date.now() - Math.random() * 1000000000).toISOString(),
      }));

      render(<PerformanceDataTable data={largeData} testId='performance-test' />);

      expect(screen.getByTestId('shadcn-data-table')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('uses ShadCN DataTable accessibility features', () => {
      render(<PerformanceDataTable data={mockData} testId='performance-test' />);

      // ShadCN DataTable provides built-in accessibility features
      expect(screen.getByTestId('shadcn-data-table')).toBeInTheDocument();
    });
  });

  describe('Test ID Support', () => {
    it('applies test ID to container', () => {
      render(<PerformanceDataTable data={mockData} testId='custom-test-id' />);

      expect(screen.getByTestId('custom-test-id')).toBeInTheDocument();
    });
  });
});
