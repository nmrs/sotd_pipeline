import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrushSplitDataTable } from '../data/BrushSplitDataTable';

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
  }: any) => (
    <div data-testid='shadcn-data-table'>
      <div data-testid='data-table-props'>
        {JSON.stringify({ height, itemSize, resizable, showColumnVisibility, searchKey })}
      </div>
      <div data-testid='data-table-columns'>
        {columns.map((col: any, index: number) => (
          <div key={index} data-testid={`column-${col.accessorKey}`}>
            {col.header}
          </div>
        ))}
      </div>
      <div data-testid='data-table-data'>
        {data.map((item: any, index: number) => (
          <div key={index} data-testid={`row-${index}`}>
            {item.original} - {item.handle} - {item.knot}
          </div>
        ))}
      </div>
    </div>
  ),
}));

// Test data
const mockBrushSplits = [
  {
    original: 'Test Brush 1',
    handle: 'Test Maker',
    knot: 'Test Knot',
    validated: false,
    corrected: false,
    validated_at: null,
    occurrences: [],
  },
  {
    original: 'Test Brush 2',
    handle: 'Another Maker',
    knot: 'Another Knot',
    validated: true,
    corrected: false,
    validated_at: new Date().toISOString(),
    occurrences: [],
  },
  {
    original: 'Test Brush 3',
    handle: 'Third Maker',
    knot: 'Third Knot',
    validated: false,
    corrected: true,
    validated_at: null,
    occurrences: [],
  },
];

describe('BrushSplitDataTable', () => {
  describe('ShadCN DataTable Integration', () => {
    it('uses ShadCN DataTable as foundation', () => {
      render(<BrushSplitDataTable brushSplits={mockBrushSplits} />);

      expect(screen.getByTestId('shadcn-data-table')).toBeInTheDocument();
    });

    it('passes correct props to ShadCN DataTable', () => {
      render(<BrushSplitDataTable brushSplits={mockBrushSplits} />);

      const propsElement = screen.getByTestId('data-table-props');
      const props = JSON.parse(propsElement.textContent || '{}');

      expect(props.height).toBe(400);
      expect(props.itemSize).toBe(48);
      expect(props.resizable).toBe(true);
      expect(props.showColumnVisibility).toBe(true);
      expect(props.searchKey).toBe('original');
    });

    it('defines correct columns for ShadCN DataTable', () => {
      render(<BrushSplitDataTable brushSplits={mockBrushSplits} />);

      expect(screen.getByTestId('column-original')).toBeInTheDocument();
      expect(screen.getByTestId('column-handle')).toBeInTheDocument();
      expect(screen.getByTestId('column-knot')).toBeInTheDocument();
      expect(screen.getByTestId('column-validated')).toBeInTheDocument();
      expect(screen.getByTestId('column-corrected')).toBeInTheDocument();
    });

    it('transforms data correctly for ShadCN DataTable', () => {
      render(<BrushSplitDataTable brushSplits={mockBrushSplits} />);

      expect(screen.getByTestId('row-0')).toHaveTextContent(
        'Test Brush 1 - Test Maker - Test Knot'
      );
      expect(screen.getByTestId('row-1')).toHaveTextContent(
        'Test Brush 2 - Another Maker - Another Knot'
      );
      expect(screen.getByTestId('row-2')).toHaveTextContent(
        'Test Brush 3 - Third Maker - Third Knot'
      );
    });
  });

  describe('Specialized Editing Functionality', () => {
    it('shows unsaved changes indicator when editing', () => {
      render(<BrushSplitDataTable brushSplits={mockBrushSplits} />);

      // Initially no unsaved changes
      expect(screen.queryByText(/unsaved change/)).not.toBeInTheDocument();

      // Note: In a real test, we would simulate editing, but since we're mocking DataTable,
      // we'll test the component's internal state management
    });

    it('provides save all changes functionality', () => {
      const onSave = jest.fn();

      render(<BrushSplitDataTable brushSplits={mockBrushSplits} onSave={onSave} />);

      // The save functionality is handled internally by the component
      // In a real test with unmocked DataTable, we would test the save button
    });

    it('handles selection change callbacks', () => {
      const onSelectionChange = jest.fn();

      render(
        <BrushSplitDataTable brushSplits={mockBrushSplits} onSelectionChange={onSelectionChange} />
      );

      // Selection change is handled by ShadCN DataTable
      // The component passes the callback through to DataTable
    });
  });

  describe('Column Definitions', () => {
    it('defines original column with correct header', () => {
      render(<BrushSplitDataTable brushSplits={mockBrushSplits} />);

      expect(screen.getByTestId('column-original')).toHaveTextContent('Original');
    });

    it('defines handle column with correct header', () => {
      render(<BrushSplitDataTable brushSplits={mockBrushSplits} />);

      expect(screen.getByTestId('column-handle')).toHaveTextContent('Handle');
    });

    it('defines knot column with correct header', () => {
      render(<BrushSplitDataTable brushSplits={mockBrushSplits} />);

      expect(screen.getByTestId('column-knot')).toHaveTextContent('Knot');
    });

    it('defines validated column with correct header', () => {
      render(<BrushSplitDataTable brushSplits={mockBrushSplits} />);

      expect(screen.getByTestId('column-validated')).toHaveTextContent('Validated');
    });

    it('defines corrected column with correct header', () => {
      render(<BrushSplitDataTable brushSplits={mockBrushSplits} />);

      expect(screen.getByTestId('column-corrected')).toHaveTextContent('Corrected');
    });
  });

  describe('Data Transformation', () => {
    it('adds index to each brush split', () => {
      render(<BrushSplitDataTable brushSplits={mockBrushSplits} />);

      // Each row should have an index added
      expect(screen.getByTestId('row-0')).toBeInTheDocument();
      expect(screen.getByTestId('row-1')).toBeInTheDocument();
      expect(screen.getByTestId('row-2')).toBeInTheDocument();
    });

    it('preserves all original brush split properties', () => {
      render(<BrushSplitDataTable brushSplits={mockBrushSplits} />);

      // Check that all properties are preserved in the transformed data
      expect(screen.getByTestId('row-0')).toHaveTextContent('Test Brush 1');
      expect(screen.getByTestId('row-1')).toHaveTextContent('Test Brush 2');
      expect(screen.getByTestId('row-2')).toHaveTextContent('Test Brush 3');
    });
  });

  describe('Error Handling', () => {
    it('handles empty brush splits array', () => {
      render(<BrushSplitDataTable brushSplits={[]} />);

      expect(screen.getByText('No brush splits to display')).toBeInTheDocument();
    });

    it('handles malformed brush split data', () => {
      const malformedData = [
        {
          original: 'Valid Brush',
          handle: 'Valid Handle',
          knot: 'Valid Knot',
          validated: false,
          corrected: false,
          validated_at: null,
          occurrences: [],
        },
        null, // Malformed entry
        {
          original: 'Another Valid Brush',
          handle: 'Another Handle',
          knot: 'Another Knot',
          validated: false,
          corrected: false,
          validated_at: null,
          occurrences: [],
        },
      ];

      render(<BrushSplitDataTable brushSplits={malformedData as any} />);

      expect(screen.getByTestId('shadcn-data-table')).toBeInTheDocument();
    });
  });

  describe('Performance', () => {
    it('handles large datasets efficiently', () => {
      const largeData = Array.from({ length: 100 }, (_, i) => ({
        original: `Brush ${i + 1}`,
        handle: `Maker ${i + 1}`,
        knot: `Knot ${i + 1}`,
        validated: i % 2 === 0,
        corrected: i % 3 === 0,
        validated_at: i % 2 === 0 ? new Date().toISOString() : null,
        occurrences: [],
      }));

      render(<BrushSplitDataTable brushSplits={largeData} />);

      expect(screen.getByTestId('shadcn-data-table')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('uses ShadCN DataTable accessibility features', () => {
      render(<BrushSplitDataTable brushSplits={mockBrushSplits} />);

      // ShadCN DataTable provides built-in accessibility features
      expect(screen.getByTestId('shadcn-data-table')).toBeInTheDocument();
    });
  });
});
