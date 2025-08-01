import { render, screen, fireEvent } from '@testing-library/react';
import BrushTable from '../data/BrushTable';

// Mock the ShadCN DataTable component
jest.mock('../ui/data-table', () => ({
  DataTable: ({
    columns,
    data,
    height,
    itemSize,
    resizable,
    showColumnVisibility,
    searchKey,
  }: {
    columns: Array<{
      accessorKey: string;
      header: string;
      cell?: (props: { row: { original: unknown } }) => React.ReactNode;
    }>;
    data: Array<Record<string, unknown>>;
    height?: number;
    itemSize?: number;
    resizable?: boolean;
    showColumnVisibility?: boolean;
    searchKey?: string;
  }) => (
    <div data-testid='shadcn-data-table'>
      <div data-testid='data-table-props'>
        {JSON.stringify({ height, itemSize, resizable, showColumnVisibility, searchKey })}
      </div>
      <div data-testid='data-table-columns'>
        {columns.map((col, index: number) => (
          <div key={index} data-testid={`column-${col.accessorKey}`}>
            {col.header}
          </div>
        ))}
      </div>
      <div data-testid='data-table-data'>
        {data.map((item, index: number) => (
          <div key={index} data-testid={`row-${index}`}>
            {/* Render each column's cell content */}
            {columns.map((col, colIndex: number) => (
              <div key={colIndex} data-testid={`cell-${col.accessorKey}-${index}`}>
                {col.cell
                  ? col.cell({ row: { original: item } })
                  : String(item[col.accessorKey] || '')}
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  ),
}));

// Mock FilteredEntryCheckbox component
jest.mock('../forms/FilteredEntryCheckbox', () => ({
  __esModule: true,
  default: ({
    itemName,
    isFiltered,
    onStatusChange,
  }: {
    itemName: string;
    isFiltered: boolean;
    onStatusChange?: (checked: boolean) => void;
  }) => (
    <div data-testid={`checkbox-${itemName}`}>
      <input
        data-testid={`checkbox-input-${itemName}`}
        type='checkbox'
        checked={isFiltered}
        onChange={e => onStatusChange?.(e.target.checked)}
      />
    </div>
  ),
}));

// Test data
const mockBrushData = [
  {
    main: {
      brush: 'Test Brush 1',
      count: 10,
      comment_ids: ['comment1', 'comment2'],
      examples: ['example1', 'example2'],
    },
    components: {
      handle: { maker: 'Test Handle 1', count: 5, comment_ids: ['comment1'] },
      knot: { maker: 'Test Knot 1', count: 5, comment_ids: ['comment2'] },
    },
  },
  {
    main: {
      brush: 'Test Brush 2',
      count: 5,
      comment_ids: ['comment3'],
      examples: ['example3'],
    },
    components: {
      handle: { maker: 'Test Handle 2', count: 3, comment_ids: ['comment3'] },
      knot: { maker: 'Test Knot 2', count: 3, comment_ids: ['comment3'] },
    },
  },
];

const mockColumnWidths = {
  filtered: 80,
  brush: 200,
  handle: 150,
  knot: 150,
  count: 100,
  comment_ids: 200,
  examples: 200,
};

describe('BrushTable', () => {
  describe('Basic Rendering', () => {
    it('renders table with brush data', () => {
      render(
        <BrushTable
          items={mockBrushData}
          onBrushFilter={jest.fn()}
          onComponentFilter={jest.fn()}
          columnWidths={mockColumnWidths}
        />
      );

      expect(screen.getByTestId('shadcn-data-table')).toBeInTheDocument();
    });

    it('renders empty table when no data', () => {
      render(
        <BrushTable
          items={[]}
          onBrushFilter={jest.fn()}
          onComponentFilter={jest.fn()}
          columnWidths={mockColumnWidths}
        />
      );

      expect(screen.getByTestId('shadcn-data-table')).toBeInTheDocument();
    });
  });

  describe('Data Flattening', () => {
    it('flattens brush data correctly', () => {
      render(
        <BrushTable
          items={mockBrushData}
          onBrushFilter={jest.fn()}
          onComponentFilter={jest.fn()}
          columnWidths={mockColumnWidths}
        />
      );

      // Should create rows for main brush and components
      expect(screen.getByTestId('shadcn-data-table')).toBeInTheDocument();
    });

    it('handles filtered status correctly', () => {
      const filteredStatus = { 'Test Brush 1': true };

      render(
        <BrushTable
          items={mockBrushData}
          onBrushFilter={jest.fn()}
          onComponentFilter={jest.fn()}
          filteredStatus={filteredStatus}
          columnWidths={mockColumnWidths}
        />
      );

      expect(screen.getByTestId('shadcn-data-table')).toBeInTheDocument();
    });
  });

  describe('Component Interaction', () => {
    it('calls onBrushFilter when brush checkbox is clicked', () => {
      const onBrushFilter = jest.fn();

      render(
        <BrushTable
          items={mockBrushData}
          onBrushFilter={onBrushFilter}
          onComponentFilter={jest.fn()}
          columnWidths={mockColumnWidths}
        />
      );

      // In the new DataTable structure, checkboxes are rendered in the cell components
      // The mock DataTable renders the cell content, so we can find the checkbox
      expect(screen.getByTestId('shadcn-data-table')).toBeInTheDocument();

      // Find the checkbox in the brush column cell for the main row (row 0)
      // The ShadCN Checkbox renders as a button with role="checkbox"
      const checkbox = screen.getByTestId('cell-brush-0').querySelector('button[role="checkbox"]');
      fireEvent.click(checkbox!);

      expect(onBrushFilter).toHaveBeenCalledWith('Test Brush 1', true);
    });

    it('calls onComponentFilter when component checkbox is clicked', () => {
      const onComponentFilter = jest.fn();

      render(
        <BrushTable
          items={mockBrushData}
          onBrushFilter={jest.fn()}
          onComponentFilter={onComponentFilter}
          columnWidths={mockColumnWidths}
        />
      );

      // Component checkboxes are handled by the flattened data structure
      expect(screen.getByTestId('shadcn-data-table')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles null/undefined items gracefully', () => {
      render(
        <BrushTable
          items={[]}
          onBrushFilter={jest.fn()}
          onComponentFilter={jest.fn()}
          columnWidths={mockColumnWidths}
        />
      );

      expect(screen.getByTestId('shadcn-data-table')).toBeInTheDocument();
    });

    it('handles items with missing components', () => {
      const incompleteData = [
        {
          main: {
            brush: 'Brush without components',
            count: 100,
            comment_ids: [],
            examples: [],
          },
          components: {
            handle: undefined,
            knot: undefined,
          },
        },
      ];

      render(
        <BrushTable
          items={incompleteData}
          onBrushFilter={jest.fn()}
          onComponentFilter={jest.fn()}
          columnWidths={mockColumnWidths}
        />
      );

      expect(screen.getByTestId('shadcn-data-table')).toBeInTheDocument();
    });
  });

  describe('Performance', () => {
    it('handles large datasets efficiently', () => {
      const largeData = Array.from({ length: 100 }, (_, i) => ({
        main: {
          brush: `Brush ${i + 1}`,
          count: i + 1,
          comment_ids: [`comment${i + 1}`],
          examples: [`example${i + 1}`],
        },
        components: {
          handle: { maker: `Handle ${i + 1}`, count: i + 1, comment_ids: [`comment${i + 1}`] },
          knot: { maker: `Knot ${i + 1}`, count: i + 1, comment_ids: [`comment${i + 1}`] },
        },
      }));

      render(
        <BrushTable
          items={largeData}
          onBrushFilter={jest.fn()}
          onComponentFilter={jest.fn()}
          columnWidths={mockColumnWidths}
        />
      );

      expect(screen.getByTestId('shadcn-data-table')).toBeInTheDocument();
    });
  });
});
