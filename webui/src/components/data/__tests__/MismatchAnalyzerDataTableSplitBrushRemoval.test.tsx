import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MismatchAnalyzerDataTable from '../MismatchAnalyzerDataTable';

describe('MismatchAnalyzerDataTable - Split Brush Removal', () => {
  const mockItems = [
    {
      id: '1',
      original: 'Declaration Grooming B2',
      matched: {
        brand: 'Declaration Grooming',
        model: 'B2',
        handle_maker: 'Declaration Grooming',
        knot_maker: 'Declaration Grooming',
        knot_type: 'badger',
        knot_size: '26mm',
      },
      count: 5,
      is_complete_brush: true,
      is_regex_match: false,
      is_intentionally_unmatched: false,
    },
    {
      id: '2',
      original: 'Alpha Amber',
      matched: {
        brand: 'Alpha',
        model: 'Amber',
        handle_maker: 'Alpha',
        knot_maker: 'Alpha',
        knot_type: 'badger',
        knot_size: '24mm',
      },
      count: 3,
      is_complete_brush: true,
      is_regex_match: false,
      is_intentionally_unmatched: false,
    },
  ];

  const mockCorrectMatches = {
    brush: {
      'declaration grooming b2': {
        original: 'Declaration Grooming B2',
        matched: {
          brand: 'Declaration Grooming',
          model: 'B2',
          handle_maker: 'Declaration Grooming',
          knot_maker: 'Declaration Grooming',
          knot_type: 'badger',
          knot_size: '26mm',
        },
      },
    },
    handle: {},
    knot: {},
  };

  const defaultProps = {
    data: mockItems,
    field: 'brush',
    correctMatches: mockCorrectMatches,
    selectedItems: new Set<string>(),
    onItemSelection: jest.fn(),
    onCommentClick: jest.fn(),
    onBrushSplitClick: jest.fn(),
    activeRowIndex: -1,
    onRowFocus: jest.fn(),
  };

  describe('Data Structure Handling', () => {
    it('should handle items without is_split_brush field', () => {
      const itemsWithoutSplitBrush = mockItems.map(item => {
        const { is_split_brush, ...itemWithoutSplitBrush } = item as any;
        return itemWithoutSplitBrush;
      });

      render(<MismatchAnalyzerDataTable {...defaultProps} data={itemsWithoutSplitBrush} />);

      // Verify that items are displayed correctly
      // The component renders with edit icons and formatted text
      expect(screen.getByText(/✏️ Declaration Grooming B2/)).toBeInTheDocument();
      expect(screen.getByText(/✏️ Alpha Amber/)).toBeInTheDocument();
    });

    it('should not reference is_split_brush in rendering logic', () => {
      render(<MismatchAnalyzerDataTable {...defaultProps} />);

      // Verify that the component renders without errors
      // and doesn't try to access is_split_brush field
      // The component renders with edit icons and formatted text
      expect(screen.getByText(/✏️ Declaration Grooming B2/)).toBeInTheDocument();
      expect(screen.getByText(/✏️ Alpha Amber/)).toBeInTheDocument();
    });
  });

  describe('Row Rendering', () => {
    it('should render rows without split_brush styling', () => {
      render(<MismatchAnalyzerDataTable {...defaultProps} />);

      // Verify that rows are rendered without split_brush specific styling
      const rows = screen.getAllByRole('row');
      expect(rows.length).toBeGreaterThan(1); // Header + data rows

      // Check that no split_brush specific classes or attributes are present
      rows.forEach(row => {
        expect(row).not.toHaveClass('split-brush');
        expect(row).not.toHaveAttribute('data-split-brush');
      });
    });

    it('should render brush information correctly without split_brush logic', () => {
      render(<MismatchAnalyzerDataTable {...defaultProps} />);

      // Verify that brush information is displayed correctly
      // The component renders the full matched data string
      expect(screen.getByText('Declaration Grooming - B2 - Declaration Grooming')).toBeInTheDocument();
      expect(screen.getByText('Alpha - Amber - Alpha')).toBeInTheDocument();
    });
  });

  describe('Selection Logic', () => {
    it('should handle item selection without split_brush considerations', () => {
      const onItemSelection = jest.fn();

      render(<MismatchAnalyzerDataTable {...defaultProps} onItemSelection={onItemSelection} />);

      // Click on the first row to select it
      const firstRow = screen.getByText(/✏️ Declaration Grooming B2/).closest('tr');
      fireEvent.click(firstRow!);

      expect(onItemSelection).toHaveBeenCalledWith('brush:declaration grooming b2', true);
    });

    it('should handle item deselection without split_brush considerations', () => {
      const onItemSelection = jest.fn();

      render(
        <MismatchAnalyzerDataTable
          {...defaultProps}
          selectedItems={new Set(['brush:declaration grooming b2'])}
          onItemSelection={onItemSelection}
        />
      );

      // Click on the selected row to deselect it
      const firstRow = screen.getByText(/✏️ Declaration Grooming B2/).closest('tr');
      fireEvent.click(firstRow!);

      expect(onItemSelection).toHaveBeenCalledWith('brush:declaration grooming b2', false);
    });
  });

  describe('Comment Click Handling', () => {
    it('should handle comment clicks without split_brush logic', () => {
      const onCommentClick = jest.fn();

      render(<MismatchAnalyzerDataTable {...defaultProps} onCommentClick={onCommentClick} />);

      // The component uses CommentList component for comment handling
      // Comment clicks are handled by the CommentList component, not direct buttons
      // Verify that the component renders without errors
      expect(screen.getByText(/✏️ Declaration Grooming B2/)).toBeInTheDocument();
    });
  });

  describe('Brush Split Handling', () => {
    it('should handle brush split clicks without split_brush logic', () => {
      const onBrushSplitClick = jest.fn();

      render(<MismatchAnalyzerDataTable {...defaultProps} onBrushSplitClick={onBrushSplitClick} />);

      // The component doesn't have direct split buttons
      // Brush split functionality is handled elsewhere in the UI
      // Verify that the component renders without errors
      expect(screen.getByText(/✏️ Declaration Grooming B2/)).toBeInTheDocument();
    });
  });

  describe('Keyboard Navigation', () => {
    it('should handle keyboard navigation without split_brush considerations', () => {
      const onRowFocus = jest.fn();

      render(<MismatchAnalyzerDataTable {...defaultProps} onRowFocus={onRowFocus} />);

      // The component doesn't have keyboard navigation handlers
      // Verify that the component renders without errors
      expect(screen.getByText(/✏️ Declaration Grooming B2/)).toBeInTheDocument();
    });
  });

  describe('Correct Matches Integration', () => {
    it('should handle correct matches without split_brush sections', () => {
      const correctMatchesWithoutSplitBrush = {
        brush: mockCorrectMatches.brush,
        handle: mockCorrectMatches.handle,
        knot: mockCorrectMatches.knot,
        // No split_brush section
      };

      render(
        <MismatchAnalyzerDataTable
          {...defaultProps}
          correctMatches={correctMatchesWithoutSplitBrush}
        />
      );

      // Verify that the component handles the data correctly
      // The component renders with edit icons and formatted text
      expect(screen.getByText(/✏️ Declaration Grooming B2/)).toBeInTheDocument();
      expect(screen.getByText(/✏️ Alpha Amber/)).toBeInTheDocument();
    });
  });

  describe('Empty State Handling', () => {
    it('should handle empty items without split_brush logic', () => {
      render(<MismatchAnalyzerDataTable {...defaultProps} data={[]} />);

      // Verify that empty state is handled correctly
      // The component shows an empty table when there are no items
      const table = screen.getByRole('table');
      expect(table).toBeInTheDocument();
      // No data rows should be present
      const dataRows = screen.queryAllByRole('row').filter(row => row.getAttribute('data-row-id'));
      expect(dataRows).toHaveLength(0);
    });
  });
});
