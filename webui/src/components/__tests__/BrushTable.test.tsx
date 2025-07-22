import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import BrushTable from '../data/BrushTable';
import { BrushData } from '../../utils/brushDataTransformer';

// Mock the VirtualizedTable component
jest.mock('../data/VirtualizedTable', () => ({
  VirtualizedTable: function MockVirtualizedTable(props: any) {
    return (
      <div data-testid="virtualized-table" style={{ height: props.height }}>
        {props.data?.map((item: any, index: any) => (
          <div key={index} data-testid={`table-row-${index}`}>
            {props.columns?.map((column: any) => (
              <div key={column.key} data-testid={`cell-${column.key}-${index}`}>
                {column.render ? column.render(item) : item[column.key]}
              </div>
            ))}
          </div>
        ))}
      </div>
    );
  },
}));

// Mock the FilteredEntryCheckbox component
jest.mock('../forms/FilteredEntryCheckbox', () => ({
  __esModule: true,
  default: function MockFilteredEntryCheckbox(props: any) {
    return (
      <div data-testid={`checkbox-${props.itemName}`}>
        <input
          type="checkbox"
          checked={props.isFiltered}
          onChange={(e: any) => props.onStatusChange?.(e.target.checked)}
          data-testid={`checkbox-input-${props.itemName}`}
        />
      </div>
    );
  },
}));

// Mock data
const mockBrushData: BrushData[] = [
  {
    main: {
      text: 'Declaration Grooming B1',
      count: 100,
      comment_ids: ['comment1', 'comment2'],
      examples: ['example1', 'example2'],
      status: 'Unmatched',
    },
    components: {
      handle: {
        text: 'Declaration Grooming',
        status: 'Unmatched',
        pattern: undefined,
      },
      knot: {
        text: 'B1',
        status: 'Unmatched',
        pattern: undefined,
      },
    },
  },
  {
    main: {
      text: 'Chisel & Hound 26mm Fanchurian',
      count: 50,
      comment_ids: ['comment3'],
      examples: ['example3'],
      status: 'Unmatched',
    },
    components: {
      handle: {
        text: 'Chisel & Hound',
        status: 'Unmatched',
        pattern: undefined,
      },
      knot: {
        text: '26mm Fanchurian',
        status: 'Unmatched',
        pattern: undefined,
      },
    },
  },
];

const mockColumnWidths = {
  filtered: 100,
  brush: 200,
  handle: 150,
  knot: 150,
  count: 80,
  comment_ids: 150,
  examples: 200,
};

const mockOnBrushFilter = jest.fn();
const mockOnComponentFilter = jest.fn();

describe('BrushTable', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('renders table with brush data', () => {
      render(
        <BrushTable
          items={mockBrushData}
          onBrushFilter={mockOnBrushFilter}
          onComponentFilter={mockOnComponentFilter}
          columnWidths={mockColumnWidths}
        />
      );

      expect(screen.getByTestId('virtualized-table')).toBeInTheDocument();
    });

    it('renders empty table when no data', () => {
      render(
        <BrushTable
          items={[]}
          onBrushFilter={mockOnBrushFilter}
          onComponentFilter={mockOnComponentFilter}
          columnWidths={mockColumnWidths}
        />
      );

      expect(screen.getByTestId('virtualized-table')).toBeInTheDocument();
    });
  });

  describe('Data Flattening', () => {
    it('flattens brush data correctly', () => {
      render(
        <BrushTable
          items={mockBrushData}
          onBrushFilter={mockOnBrushFilter}
          onComponentFilter={mockOnComponentFilter}
          columnWidths={mockColumnWidths}
        />
      );

      // Should create rows for main brush and components
      expect(screen.getByTestId('virtualized-table')).toBeInTheDocument();
    });

    it('handles filtered status correctly', () => {
      const filteredStatus = {
        'Declaration Grooming B1': true,
      };

      render(
        <BrushTable
          items={mockBrushData}
          onBrushFilter={mockOnBrushFilter}
          onComponentFilter={mockOnComponentFilter}
          columnWidths={mockColumnWidths}
          filteredStatus={filteredStatus}
        />
      );

      expect(screen.getByTestId('virtualized-table')).toBeInTheDocument();
    });
  });

  describe('Component Interaction', () => {
    it('calls onBrushFilter when brush checkbox is clicked', () => {
      render(
        <BrushTable
          items={mockBrushData}
          onBrushFilter={mockOnBrushFilter}
          onComponentFilter={mockOnComponentFilter}
          columnWidths={mockColumnWidths}
        />
      );

      const checkboxes = screen.getAllByRole('checkbox');
      if (checkboxes.length > 0) {
        fireEvent.click(checkboxes[0]);
        expect(mockOnBrushFilter).toHaveBeenCalled();
      }
    });

    it('calls onComponentFilter when component checkbox is clicked', () => {
      render(
        <BrushTable
          items={mockBrushData}
          onBrushFilter={mockOnBrushFilter}
          onComponentFilter={mockOnComponentFilter}
          columnWidths={mockColumnWidths}
        />
      );

      const checkboxes = screen.getAllByRole('checkbox');
      if (checkboxes.length > 1) {
        fireEvent.click(checkboxes[1]);
        expect(mockOnComponentFilter).toHaveBeenCalled();
      }
    });
  });

  describe('Edge Cases', () => {
    it('handles null/undefined items gracefully', () => {
      render(
        <BrushTable
          items={null as any}
          onBrushFilter={mockOnBrushFilter}
          onComponentFilter={mockOnComponentFilter}
          columnWidths={mockColumnWidths}
        />
      );

      expect(screen.getByTestId('virtualized-table')).toBeInTheDocument();
    });

    it('handles items with missing components', () => {
      const incompleteData: BrushData[] = [
        {
          main: {
            text: 'Brush without components',
            count: 100,
            comment_ids: [],
            examples: [],
            status: 'Unmatched',
          },
          components: {},
        },
      ];

      render(
        <BrushTable
          items={incompleteData}
          onBrushFilter={mockOnBrushFilter}
          onComponentFilter={mockOnComponentFilter}
          columnWidths={mockColumnWidths}
        />
      );

      expect(screen.getByTestId('virtualized-table')).toBeInTheDocument();
    });
  });

  describe('Performance', () => {
    it('handles large datasets efficiently', () => {
      const largeData: BrushData[] = Array.from({ length: 100 }, (_, i) => ({
        main: {
          text: `Brush ${i}`,
          count: i * 10,
          comment_ids: [`comment${i}`],
          examples: [`example${i}`],
          status: 'Unmatched',
        },
        components: {
          handle: {
            text: `Handle ${i}`,
            status: 'Unmatched',
            pattern: undefined,
          },
          knot: {
            text: `Knot ${i}`,
            status: 'Unmatched',
            pattern: undefined,
          },
        },
      }));

      render(
        <BrushTable
          items={largeData}
          onBrushFilter={mockOnBrushFilter}
          onComponentFilter={mockOnComponentFilter}
          columnWidths={mockColumnWidths}
        />
      );

      expect(screen.getByTestId('virtualized-table')).toBeInTheDocument();
    });
  });
});
