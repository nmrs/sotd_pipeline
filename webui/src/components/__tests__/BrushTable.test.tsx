// import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import BrushTable from '../data/BrushTable';
import { BrushData } from '../../utils/brushDataTransformer';

// Mock the VirtualizedTable component (named export)
jest.mock('../data/VirtualizedTable', () => ({
  __esModule: true,
  VirtualizedTable: function MockVirtualizedTable(props: any) {
    return (
      <div data-testid='virtualized-table' style={{ height: props.height }}>
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
    // Create unique test ID to match the new format
    const testId = props.uniqueId
      ? `checkbox-${props.itemName}-${props.uniqueId}`
      : `checkbox-${props.itemName}`;
    const inputTestId = props.uniqueId
      ? `checkbox-input-${props.itemName}-${props.uniqueId}`
      : `checkbox-input-${props.itemName}`;

    return (
      <div data-testid={testId}>
        <input
          type='checkbox'
          checked={props.isFiltered}
          onChange={(e: any) => props.onStatusChange?.(e.target.checked)}
          data-testid={inputTestId}
        />
      </div>
    );
  },
}));

const mockBrushData: BrushData[] = [
  {
    main: {
      text: 'Test Brush',
      count: 5,
      comment_ids: ['comment1', 'comment2'],
      examples: ['example1', 'example2'],
      status: 'Unmatched' as const,
    },
    components: {
      handle: {
        text: 'Test Handle',
        status: 'Unmatched' as const,
        pattern: undefined,
      },
      knot: {
        text: 'Test Knot',
        status: 'Unmatched' as const,
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

  test('should render brush table with correct structure', () => {
    render(
      <BrushTable
        items={mockBrushData}
        onBrushFilter={mockOnBrushFilter}
        onComponentFilter={mockOnComponentFilter}
        filteredStatus={{}}
        pendingChanges={{}}
        columnWidths={mockColumnWidths}
      />
    );

    // Check that the main brush checkbox is rendered
    expect(screen.getByTestId('checkbox-Test Brush-main')).toBeInTheDocument();
    expect(screen.getByTestId('checkbox-input-Test Brush-main')).toBeInTheDocument();

    // Check that component checkboxes are rendered
    expect(screen.getByTestId('checkbox-Test Handle-handle')).toBeInTheDocument();
    expect(screen.getByTestId('checkbox-Test Knot-knot')).toBeInTheDocument();
  });

  test('should pass correct isFiltered prop to checkboxes', () => {
    const filteredStatus = {
      'Test Brush': true,
      'Test Handle': false,
      'Test Knot': true,
    };

    render(
      <BrushTable
        items={mockBrushData}
        onBrushFilter={mockOnBrushFilter}
        onComponentFilter={mockOnComponentFilter}
        filteredStatus={filteredStatus}
        pendingChanges={{}}
        columnWidths={mockColumnWidths}
      />
    );

    // Check that the main brush checkbox is checked
    const mainCheckbox = screen.getByTestId('checkbox-input-Test Brush-main') as HTMLInputElement;
    expect(mainCheckbox.checked).toBe(true);

    // When parent is filtered, component checkboxes should be hidden (not rendered)
    // So we shouldn't expect to find them
    expect(screen.queryByTestId('checkbox-input-Test Handle-handle')).not.toBeInTheDocument();
    expect(screen.queryByTestId('checkbox-input-Test Knot-knot')).not.toBeInTheDocument();
  });

  test('should show component checkboxes when parent is not filtered', () => {
    const filteredStatus = {
      'Test Brush': false,
      'Test Handle': false,
      'Test Knot': true,
    };

    render(
      <BrushTable
        items={mockBrushData}
        onBrushFilter={mockOnBrushFilter}
        onComponentFilter={mockOnComponentFilter}
        filteredStatus={filteredStatus}
        pendingChanges={{}}
        columnWidths={mockColumnWidths}
      />
    );

    // Check that the main brush checkbox is unchecked
    const mainCheckbox = screen.getByTestId('checkbox-input-Test Brush-main') as HTMLInputElement;
    expect(mainCheckbox.checked).toBe(false);

    // When parent is not filtered, component checkboxes should be visible
    const handleCheckbox = screen.getByTestId(
      'checkbox-input-Test Handle-handle'
    ) as HTMLInputElement;
    expect(handleCheckbox.checked).toBe(false);

    const knotCheckbox = screen.getByTestId('checkbox-input-Test Knot-knot') as HTMLInputElement;
    expect(knotCheckbox.checked).toBe(true);
  });

  test('should call onBrushFilter when main checkbox is clicked', () => {
    render(
      <BrushTable
        items={mockBrushData}
        onBrushFilter={mockOnBrushFilter}
        onComponentFilter={mockOnComponentFilter}
        filteredStatus={{}}
        pendingChanges={{}}
        columnWidths={mockColumnWidths}
      />
    );

    const mainCheckbox = screen.getByTestId('checkbox-input-Test Brush-main');
    fireEvent.click(mainCheckbox);

    expect(mockOnBrushFilter).toHaveBeenCalledWith('Test Brush', true);
  });

  test('should call onComponentFilter when component checkbox is clicked', () => {
    render(
      <BrushTable
        items={mockBrushData}
        onBrushFilter={mockOnBrushFilter}
        onComponentFilter={mockOnComponentFilter}
        filteredStatus={{}}
        pendingChanges={{}}
        columnWidths={mockColumnWidths}
      />
    );

    const handleCheckbox = screen.getByTestId('checkbox-input-Test Handle-handle');
    fireEvent.click(handleCheckbox);

    expect(mockOnComponentFilter).toHaveBeenCalledWith('Test Handle', true);
  });

  test('should not render component checkboxes when parent is filtered', () => {
    const filteredStatus = {
      'Test Brush': true,
    };

    render(
      <BrushTable
        items={mockBrushData}
        onBrushFilter={mockOnBrushFilter}
        onComponentFilter={mockOnComponentFilter}
        filteredStatus={filteredStatus}
        pendingChanges={{}}
        columnWidths={mockColumnWidths}
      />
    );

    // Main checkbox should be visible and checked
    expect(screen.getByTestId('checkbox-input-Test Brush-main')).toBeInTheDocument();

    // Component checkboxes should not be rendered when parent is filtered
    expect(screen.queryByTestId('checkbox-input-Test Handle-handle')).not.toBeInTheDocument();
    expect(screen.queryByTestId('checkbox-input-Test Knot-knot')).not.toBeInTheDocument();
  });

  test('should create subrows in flattened data', () => {
    const { container } = render(
      <BrushTable
        items={mockBrushData}
        onBrushFilter={mockOnBrushFilter}
        onComponentFilter={mockOnComponentFilter}
        filteredStatus={{}}
        pendingChanges={{}}
        columnWidths={mockColumnWidths}
      />
    );

    // Check that we have 3 rows total (1 main + 1 handle + 1 knot)
    const tableRows = container.querySelectorAll('[data-testid^="table-row-"]');
    expect(tableRows).toHaveLength(3);

    // Check that the subrows are rendered with proper indentation
    const handleRow = container.querySelector('[data-testid="table-row-1"]');
    const knotRow = container.querySelector('[data-testid="table-row-2"]');

    expect(handleRow).toBeInTheDocument();
    expect(knotRow).toBeInTheDocument();

    // Check that handle and knot text are present
    expect(screen.getByText('🔧 Handle: Test Handle')).toBeInTheDocument();
    expect(screen.getByText('🧶 Knot: Test Knot')).toBeInTheDocument();
  });
});
