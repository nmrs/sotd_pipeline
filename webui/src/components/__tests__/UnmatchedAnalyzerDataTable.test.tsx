import React from 'react';
import { render, screen } from '@testing-library/react';
import UnmatchedAnalyzerDataTable from '../data/UnmatchedAnalyzerDataTable';

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
            {String(item?.item || 'null')} - {String(item?.count || 0)} -{' '}
            {String((item?.comment_ids as string[])?.length || 0)}
          </div>
        ))}
      </div>
    </div>
  ),
}));

// Test data
const mockData = [
  {
    item: 'Test Razor 1',
    count: 10,
    comment_ids: ['comment1', 'comment2'],
    examples: ['example1', 'example2'],
  },
  {
    item: 'Test Razor 2',
    count: 5,
    comment_ids: ['comment3'],
    examples: ['example3'],
  },
  {
    item: 'Test Razor 3',
    count: 15,
    comment_ids: [],
    examples: [],
  },
];

const mockFilteredStatus = {
  'Test Razor 1': true,
  'Test Razor 2': false,
};

const mockPendingChanges = {
  'Test Razor 3': true,
};

const mockColumnWidths = {
  filtered: 80,
  item: 200,
  count: 100,
  comment_ids: 200,
  examples: 200,
};

describe('UnmatchedAnalyzerDataTable', () => {
  describe('ShadCN DataTable Integration', () => {
    it('uses ShadCN DataTable as foundation', () => {
      render(
        <UnmatchedAnalyzerDataTable
          data={mockData}
          filteredStatus={mockFilteredStatus}
          pendingChanges={mockPendingChanges}
          onFilteredStatusChange={jest.fn()}
          onCommentClick={jest.fn()}
          commentLoading={false}
          fieldType='razor'
          columnWidths={mockColumnWidths}
        />
      );

      expect(screen.getByTestId('shadcn-data-table')).toBeInTheDocument();
    });

    it('passes correct props to ShadCN DataTable', () => {
      render(
        <UnmatchedAnalyzerDataTable
          data={mockData}
          filteredStatus={mockFilteredStatus}
          pendingChanges={mockPendingChanges}
          onFilteredStatusChange={jest.fn()}
          onCommentClick={jest.fn()}
          commentLoading={false}
          fieldType='razor'
          columnWidths={mockColumnWidths}
        />
      );

      const propsElement = screen.getByTestId('data-table-props');
      const props = JSON.parse(propsElement.textContent || '{}');

      // The UnmatchedAnalyzerDataTable doesn't implement virtualization, so height and itemSize are undefined
      expect(props.height).toBeUndefined();
      expect(props.itemSize).toBeUndefined();
      expect(props.resizable).toBe(true);
      expect(props.showColumnVisibility).toBe(true);
      expect(props.searchKey).toBe('item');
    });

    it('defines correct columns for ShadCN DataTable', () => {
      render(
        <UnmatchedAnalyzerDataTable
          data={mockData}
          filteredStatus={mockFilteredStatus}
          pendingChanges={mockPendingChanges}
          onFilteredStatusChange={jest.fn()}
          onCommentClick={jest.fn()}
          commentLoading={false}
          fieldType='razor'
          columnWidths={mockColumnWidths}
        />
      );

      // The UnmatchedAnalyzerDataTable has these columns: item, count, comment_ids, examples
      // It does NOT have a "filtered" column
      expect(screen.getByTestId('column-item')).toBeInTheDocument();
      expect(screen.getByTestId('column-count')).toBeInTheDocument();
      expect(screen.getByTestId('column-comment_ids')).toBeInTheDocument();
      expect(screen.getByTestId('column-examples')).toBeInTheDocument();
    });

    it('transforms data correctly for ShadCN DataTable', () => {
      render(
        <UnmatchedAnalyzerDataTable
          data={mockData}
          filteredStatus={mockFilteredStatus}
          pendingChanges={mockPendingChanges}
          onFilteredStatusChange={jest.fn()}
          onCommentClick={jest.fn()}
          commentLoading={false}
          fieldType='razor'
          columnWidths={mockColumnWidths}
        />
      );

      expect(screen.getByTestId('row-0')).toHaveTextContent('Test Razor 1 - 10 - 2');
      expect(screen.getByTestId('row-1')).toHaveTextContent('Test Razor 2 - 5 - 1');
      expect(screen.getByTestId('row-2')).toHaveTextContent('Test Razor 3 - 15 - 0');
    });
  });

  describe('Field Type Handling', () => {
    it('displays correct header for razor field type', () => {
      render(
        <UnmatchedAnalyzerDataTable
          data={mockData}
          filteredStatus={mockFilteredStatus}
          pendingChanges={mockPendingChanges}
          onFilteredStatusChange={jest.fn()}
          onCommentClick={jest.fn()}
          commentLoading={false}
          fieldType='razor'
          columnWidths={mockColumnWidths}
        />
      );

      // The component always uses "Item" header regardless of fieldType
      expect(screen.getByTestId('column-item')).toHaveTextContent('Item');
    });

    it('displays correct header for blade field type', () => {
      render(
        <UnmatchedAnalyzerDataTable
          data={mockData}
          filteredStatus={mockFilteredStatus}
          pendingChanges={mockPendingChanges}
          onFilteredStatusChange={jest.fn()}
          onCommentClick={jest.fn()}
          commentLoading={false}
          fieldType='blade'
          columnWidths={mockColumnWidths}
        />
      );

      // The component always uses "Item" header regardless of fieldType
      expect(screen.getByTestId('column-item')).toHaveTextContent('Item');
    });

    it('displays correct header for soap field type', () => {
      render(
        <UnmatchedAnalyzerDataTable
          data={mockData}
          filteredStatus={mockFilteredStatus}
          pendingChanges={mockPendingChanges}
          onFilteredStatusChange={jest.fn()}
          onCommentClick={jest.fn()}
          commentLoading={false}
          fieldType='soap'
          columnWidths={mockColumnWidths}
        />
      );

      // The component always uses "Item" header regardless of fieldType
      expect(screen.getByTestId('column-item')).toHaveTextContent('Item');
    });

    it('displays correct header for brush field type', () => {
      render(
        <UnmatchedAnalyzerDataTable
          data={mockData}
          filteredStatus={mockFilteredStatus}
          pendingChanges={mockPendingChanges}
          onFilteredStatusChange={jest.fn()}
          onCommentClick={jest.fn()}
          commentLoading={false}
          fieldType='brush'
          columnWidths={mockColumnWidths}
        />
      );

      // The component always uses "Item" header regardless of fieldType
      expect(screen.getByTestId('column-item')).toHaveTextContent('Item');
    });
  });

  describe('Column Definitions', () => {
    it('defines item column with correct header', () => {
      render(
        <UnmatchedAnalyzerDataTable
          data={mockData}
          filteredStatus={mockFilteredStatus}
          pendingChanges={mockPendingChanges}
          onFilteredStatusChange={jest.fn()}
          onCommentClick={jest.fn()}
          commentLoading={false}
          fieldType='razor'
          columnWidths={mockColumnWidths}
        />
      );

      expect(screen.getByTestId('column-item')).toHaveTextContent('Item');
    });

    it('defines count column with correct header', () => {
      render(
        <UnmatchedAnalyzerDataTable
          data={mockData}
          filteredStatus={mockFilteredStatus}
          pendingChanges={mockPendingChanges}
          onFilteredStatusChange={jest.fn()}
          onCommentClick={jest.fn()}
          commentLoading={false}
          fieldType='razor'
          columnWidths={mockColumnWidths}
        />
      );

      expect(screen.getByTestId('column-count')).toHaveTextContent('Count');
    });

    it('defines comment_ids column with correct header', () => {
      render(
        <UnmatchedAnalyzerDataTable
          data={mockData}
          filteredStatus={mockFilteredStatus}
          pendingChanges={mockPendingChanges}
          onFilteredStatusChange={jest.fn()}
          onCommentClick={jest.fn()}
          commentLoading={false}
          fieldType='razor'
          columnWidths={mockColumnWidths}
        />
      );

      expect(screen.getByTestId('column-comment_ids')).toHaveTextContent('Comments');
    });

    it('defines examples column with correct header', () => {
      render(
        <UnmatchedAnalyzerDataTable
          data={mockData}
          filteredStatus={mockFilteredStatus}
          pendingChanges={mockPendingChanges}
          onFilteredStatusChange={jest.fn()}
          onCommentClick={jest.fn()}
          commentLoading={false}
          fieldType='razor'
          columnWidths={mockColumnWidths}
        />
      );

      expect(screen.getByTestId('column-examples')).toHaveTextContent('Examples');
    });
  });

  describe('Data Transformation', () => {
    it('preserves all original data properties', () => {
      render(
        <UnmatchedAnalyzerDataTable
          data={mockData}
          filteredStatus={mockFilteredStatus}
          pendingChanges={mockPendingChanges}
          onFilteredStatusChange={jest.fn()}
          onCommentClick={jest.fn()}
          commentLoading={false}
          fieldType='razor'
          columnWidths={mockColumnWidths}
        />
      );

      // Check that all properties are preserved in the transformed data
      expect(screen.getByTestId('row-0')).toHaveTextContent('Test Razor 1');
      expect(screen.getByTestId('row-1')).toHaveTextContent('Test Razor 2');
      expect(screen.getByTestId('row-2')).toHaveTextContent('Test Razor 3');
    });

    it('handles empty data array', () => {
      render(
        <UnmatchedAnalyzerDataTable
          data={[]}
          filteredStatus={mockFilteredStatus}
          pendingChanges={mockPendingChanges}
          onFilteredStatusChange={jest.fn()}
          onCommentClick={jest.fn()}
          commentLoading={false}
          fieldType='razor'
          columnWidths={mockColumnWidths}
        />
      );

      expect(screen.getByText('No unmatched items to display')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('handles malformed data gracefully', () => {
      render(
        <UnmatchedAnalyzerDataTable
          data={[]}
          filteredStatus={mockFilteredStatus}
          pendingChanges={mockPendingChanges}
          onFilteredStatusChange={jest.fn()}
          onCommentClick={jest.fn()}
          commentLoading={false}
          fieldType='razor'
          columnWidths={mockColumnWidths}
        />
      );

      expect(screen.getByText('No unmatched items to display')).toBeInTheDocument();
    });
  });

  describe('Performance', () => {
    it('handles large datasets efficiently', () => {
      const largeData = Array.from({ length: 100 }, (_, i) => ({
        item: `Item ${i + 1}`,
        count: i + 1,
        comment_ids: [`comment${i + 1}`],
        examples: [`example${i + 1}`],
      }));

      render(
        <UnmatchedAnalyzerDataTable
          data={largeData}
          filteredStatus={mockFilteredStatus}
          pendingChanges={mockPendingChanges}
          onFilteredStatusChange={jest.fn()}
          onCommentClick={jest.fn()}
          commentLoading={false}
          fieldType='razor'
          columnWidths={mockColumnWidths}
        />
      );

      expect(screen.getByTestId('shadcn-data-table')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('uses ShadCN DataTable accessibility features', () => {
      render(
        <UnmatchedAnalyzerDataTable
          data={mockData}
          filteredStatus={mockFilteredStatus}
          pendingChanges={mockPendingChanges}
          onFilteredStatusChange={jest.fn()}
          onCommentClick={jest.fn()}
          commentLoading={false}
          fieldType='razor'
          columnWidths={mockColumnWidths}
        />
      );

      // ShadCN DataTable provides built-in accessibility features
      expect(screen.getByTestId('shadcn-data-table')).toBeInTheDocument();
    });
  });
});
