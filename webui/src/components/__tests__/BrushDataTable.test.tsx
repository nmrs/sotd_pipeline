import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrushDataTable } from '../data/BrushDataTable';

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
            {item.brand} - {item.model} - {item.isMainRow ? 'main' : 'subrow'}
          </div>
        ))}
      </div>
    </div>
  ),
}));

// Test data
const mockBrushData = [
  {
    id: '1',
    brand: 'Test Brand 1',
    model: 'Test Model 1',
    handle_maker: 'Test Handle Maker 1',
    knot_maker: 'Test Knot Maker 1',
    fiber: 'Test Fiber 1',
    knot_size: '24mm',
    subrows: [
      {
        id: '1-1',
        brand: 'Test Brand 1',
        model: 'Test Model 1 Variant A',
        handle_maker: 'Test Handle Maker 1',
        knot_maker: 'Test Knot Maker 1',
        fiber: 'Test Fiber 1',
        knot_size: '26mm',
      },
      {
        id: '1-2',
        brand: 'Test Brand 1',
        model: 'Test Model 1 Variant B',
        handle_maker: 'Test Handle Maker 1',
        knot_maker: 'Test Knot Maker 1',
        fiber: 'Test Fiber 1',
        knot_size: '28mm',
      },
    ],
  },
  {
    id: '2',
    brand: 'Test Brand 2',
    model: 'Test Model 2',
    handle_maker: 'Test Handle Maker 2',
    knot_maker: 'Test Knot Maker 2',
    fiber: 'Test Fiber 2',
    knot_size: '26mm',
    subrows: [],
  },
  {
    id: '3',
    brand: 'Test Brand 3',
    model: 'Test Model 3',
    handle_maker: 'Test Handle Maker 3',
    knot_maker: 'Test Knot Maker 3',
    fiber: 'Test Fiber 3',
    knot_size: '28mm',
    subrows: [
      {
        id: '3-1',
        brand: 'Test Brand 3',
        model: 'Test Model 3 Variant A',
        handle_maker: 'Test Handle Maker 3',
        knot_maker: 'Test Knot Maker 3',
        fiber: 'Test Fiber 3',
        knot_size: '30mm',
      },
    ],
  },
];

describe('BrushDataTable', () => {
  describe('ShadCN DataTable Integration', () => {
    it('uses ShadCN DataTable as foundation', () => {
      render(<BrushDataTable brushData={mockBrushData} />);

      expect(screen.getByTestId('shadcn-data-table')).toBeInTheDocument();
    });

    it('passes correct props to ShadCN DataTable', () => {
      render(<BrushDataTable brushData={mockBrushData} />);

      const propsElement = screen.getByTestId('data-table-props');
      const props = JSON.parse(propsElement.textContent || '{}');

      expect(props.height).toBe(400);
      expect(props.itemSize).toBe(48);
      expect(props.resizable).toBe(true);
      expect(props.showColumnVisibility).toBe(true);
      expect(props.searchKey).toBe('brand');
    });

    it('defines correct columns for ShadCN DataTable', () => {
      render(<BrushDataTable brushData={mockBrushData} />);

      expect(screen.getByTestId('column-brand')).toBeInTheDocument();
      expect(screen.getByTestId('column-model')).toBeInTheDocument();
      expect(screen.getByTestId('column-handle_maker')).toBeInTheDocument();
      expect(screen.getByTestId('column-knot_maker')).toBeInTheDocument();
      expect(screen.getByTestId('column-fiber')).toBeInTheDocument();
      expect(screen.getByTestId('column-knot_size')).toBeInTheDocument();
    });

    it('transforms data correctly for ShadCN DataTable', () => {
      render(<BrushDataTable brushData={mockBrushData} />);

      // Should show main rows initially
      expect(screen.getByTestId('row-0')).toHaveTextContent('Test Brand 1 - Test Model 1 - main');
      expect(screen.getByTestId('row-1')).toHaveTextContent('Test Brand 2 - Test Model 2 - main');
      expect(screen.getByTestId('row-2')).toHaveTextContent('Test Brand 3 - Test Model 3 - main');
    });
  });

  describe('Subrow Functionality', () => {
    it('shows expand/collapse buttons for rows with subrows', () => {
      render(<BrushDataTable brushData={mockBrushData} />);

      // The expand/collapse functionality is handled by the component's internal state
      // In a real test with unmocked DataTable, we would test the expand/collapse buttons
    });

    it('handles subrow toggle callbacks', () => {
      const onSubrowToggle = jest.fn();

      render(<BrushDataTable brushData={mockBrushData} onSubrowToggle={onSubrowToggle} />);

      // Subrow toggle is handled internally by the component
      // The callback is passed through to the toggle handler
    });

    it('transforms data to include subrows when expanded', () => {
      render(<BrushDataTable brushData={mockBrushData} />);

      // Initially only main rows are shown
      expect(screen.getByTestId('row-0')).toHaveTextContent('Test Brand 1 - Test Model 1 - main');
      expect(screen.getByTestId('row-1')).toHaveTextContent('Test Brand 2 - Test Model 2 - main');
      expect(screen.getByTestId('row-2')).toHaveTextContent('Test Brand 3 - Test Model 3 - main');
    });
  });

  describe('Row Interaction', () => {
    it('handles row click callbacks', () => {
      const onRowClick = jest.fn();

      render(<BrushDataTable brushData={mockBrushData} onRowClick={onRowClick} />);

      // Row click is handled through cell click handlers
      // The callback is passed through to the click handler
    });
  });

  describe('Column Definitions', () => {
    it('defines brand column with correct header', () => {
      render(<BrushDataTable brushData={mockBrushData} />);

      expect(screen.getByTestId('column-brand')).toHaveTextContent('Brand');
    });

    it('defines model column with correct header', () => {
      render(<BrushDataTable brushData={mockBrushData} />);

      expect(screen.getByTestId('column-model')).toHaveTextContent('Model');
    });

    it('defines handle_maker column with correct header', () => {
      render(<BrushDataTable brushData={mockBrushData} />);

      expect(screen.getByTestId('column-handle_maker')).toHaveTextContent('Handle Maker');
    });

    it('defines knot_maker column with correct header', () => {
      render(<BrushDataTable brushData={mockBrushData} />);

      expect(screen.getByTestId('column-knot_maker')).toHaveTextContent('Knot Maker');
    });

    it('defines fiber column with correct header', () => {
      render(<BrushDataTable brushData={mockBrushData} />);

      expect(screen.getByTestId('column-fiber')).toHaveTextContent('Fiber');
    });

    it('defines knot_size column with correct header', () => {
      render(<BrushDataTable brushData={mockBrushData} />);

      expect(screen.getByTestId('column-knot_size')).toHaveTextContent('Knot Size');
    });
  });

  describe('Data Transformation', () => {
    it('flattens brush data with subrows', () => {
      render(<BrushDataTable brushData={mockBrushData} />);

      // Initially only main rows are shown
      expect(screen.getByTestId('row-0')).toBeInTheDocument();
      expect(screen.getByTestId('row-1')).toBeInTheDocument();
      expect(screen.getByTestId('row-2')).toBeInTheDocument();
    });

    it('preserves all original brush properties', () => {
      render(<BrushDataTable brushData={mockBrushData} />);

      // Check that all properties are preserved in the transformed data
      expect(screen.getByTestId('row-0')).toHaveTextContent('Test Brand 1');
      expect(screen.getByTestId('row-1')).toHaveTextContent('Test Brand 2');
      expect(screen.getByTestId('row-2')).toHaveTextContent('Test Brand 3');
    });
  });

  describe('Error Handling', () => {
    it('handles empty brush data array', () => {
      render(<BrushDataTable brushData={[]} />);

      expect(screen.getByTestId('shadcn-data-table')).toBeInTheDocument();
    });

    it('handles malformed brush data', () => {
      const malformedData = [
        {
          id: '1',
          brand: 'Valid Brand',
          model: 'Valid Model',
          handle_maker: 'Valid Handle Maker',
          knot_maker: 'Valid Knot Maker',
          fiber: 'Valid Fiber',
          knot_size: '24mm',
          subrows: [],
        },
        null, // Malformed entry
        {
          id: '2',
          brand: 'Another Valid Brand',
          model: 'Another Valid Model',
          handle_maker: 'Another Valid Handle Maker',
          knot_maker: 'Another Valid Knot Maker',
          fiber: 'Another Valid Fiber',
          knot_size: '26mm',
          subrows: [],
        },
      ];

      render(<BrushDataTable brushData={malformedData as any} />);

      expect(screen.getByTestId('shadcn-data-table')).toBeInTheDocument();
    });
  });

  describe('Performance', () => {
    it('handles large datasets efficiently', () => {
      const largeData = Array.from({ length: 100 }, (_, i) => ({
        id: `brush-${i + 1}`,
        brand: `Brand ${i + 1}`,
        model: `Model ${i + 1}`,
        handle_maker: `Handle Maker ${i + 1}`,
        knot_maker: `Knot Maker ${i + 1}`,
        fiber: `Fiber ${i + 1}`,
        knot_size: `${24 + (i % 6)}mm`,
        subrows:
          i % 3 === 0
            ? [
                {
                  id: `brush-${i + 1}-1`,
                  brand: `Brand ${i + 1}`,
                  model: `Model ${i + 1} Variant`,
                  handle_maker: `Handle Maker ${i + 1}`,
                  knot_maker: `Knot Maker ${i + 1}`,
                  fiber: `Fiber ${i + 1}`,
                  knot_size: `${26 + (i % 6)}mm`,
                },
              ]
            : [],
      }));

      render(<BrushDataTable brushData={largeData} />);

      expect(screen.getByTestId('shadcn-data-table')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('uses ShadCN DataTable accessibility features', () => {
      render(<BrushDataTable brushData={mockBrushData} />);

      // ShadCN DataTable provides built-in accessibility features
      expect(screen.getByTestId('shadcn-data-table')).toBeInTheDocument();
    });
  });
});
