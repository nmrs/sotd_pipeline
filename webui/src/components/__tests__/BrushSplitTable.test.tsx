import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import BrushSplitTable from '../BrushSplitTable';

describe('BrushSplitTable (TDD)', () => {
    it('renders with empty data (no errors)', () => {
        render(<BrushSplitTable />);
        expect(screen.getByTestId('brush-split-table')).toBeInTheDocument();
    });

    it('renders a single row of brush split data', () => {
        const data = [
            {
                original: 'Elite handle w/ Declaration knot',
                handle: 'Elite',
                knot: 'Declaration',
            }
        ];
        render(<BrushSplitTable brushSplits={data} />);
        expect(screen.getByText('Elite handle w/ Declaration knot')).toBeInTheDocument();
        expect(screen.getByText('Elite')).toBeInTheDocument();
        expect(screen.getByText('Declaration')).toBeInTheDocument();
    });

    it('renders multiple rows of brush split data', () => {
        const data = [
            { original: 'Elite handle w/ Declaration knot', handle: 'Elite', knot: 'Declaration' },
            { original: 'Omega boar brush', handle: '', knot: 'Omega boar brush' },
            { original: 'Simpson Chubby 2', handle: 'Simpson', knot: 'Chubby 2' }
        ];
        render(<BrushSplitTable brushSplits={data} />);
        expect(screen.getByText('Elite handle w/ Declaration knot')).toBeInTheDocument();
        // Omega boar brush appears twice (original and knot)
        expect(screen.getAllByText('Omega boar brush').length).toBe(2);
        expect(screen.getByText('Simpson Chubby 2')).toBeInTheDocument();
        expect(screen.getByText('Simpson')).toBeInTheDocument();
        expect(screen.getByText('Chubby 2')).toBeInTheDocument();
    });

    it('renders a checkbox for each row and allows selecting a single row', () => {
        const data = [
            { original: 'Elite handle w/ Declaration knot', handle: 'Elite', knot: 'Declaration' },
            { original: 'Omega boar brush', handle: '', knot: 'Omega boar brush' }
        ];
        const onSelectionChange = jest.fn();
        render(<BrushSplitTable brushSplits={data} onSelectionChange={onSelectionChange} />);
        const checkboxes = screen.getAllByRole('checkbox');
        expect(checkboxes.length).toBe(2);
        fireEvent.click(checkboxes[1]); // Select the second row
        expect(onSelectionChange).toHaveBeenCalledWith([1]);
    });

    it('allows selecting multiple rows and calls onSelectionChange with all selected indices', () => {
        const data = [
            { original: 'Elite handle w/ Declaration knot', handle: 'Elite', knot: 'Declaration' },
            { original: 'Omega boar brush', handle: '', knot: 'Omega boar brush' },
            { original: 'Simpson Chubby 2', handle: 'Simpson', knot: 'Chubby 2' }
        ];
        let selected: number[] = [];
        const onSelectionChange = (indices: number[]) => { selected = indices; };
        render(<BrushSplitTable brushSplits={data} onSelectionChange={onSelectionChange} />);
        const checkboxes = screen.getAllByRole('checkbox');
        fireEvent.click(checkboxes[0]); // Select first row
        expect(selected).toEqual([0]);
        fireEvent.click(checkboxes[2]); // Select third row
        expect(selected).toEqual([0, 2]);
        fireEvent.click(checkboxes[0]); // Deselect first row
        expect(selected).toEqual([2]);
    });

    it('allows inline editing of the handle field by clicking on it', () => {
        const data = [
            { original: 'Elite handle w/ Declaration knot', handle: 'Elite', knot: 'Declaration' }
        ];
        render(<BrushSplitTable brushSplits={data} />);
        const handleElement = screen.getByText('Elite');
        fireEvent.click(handleElement);
        const input = screen.getByDisplayValue('Elite');
        expect(input).toBeInTheDocument();
        fireEvent.change(input, { target: { value: 'New Handle' } });
        expect(input).toHaveValue('New Handle');
    });

    it('allows inline editing of the knot field by clicking on it', () => {
        const data = [
            { original: 'Elite handle w/ Declaration knot', handle: 'Elite', knot: 'Declaration' }
        ];
        render(<BrushSplitTable brushSplits={data} />);
        const knotElement = screen.getByText('Declaration');
        fireEvent.click(knotElement);
        const input = screen.getByDisplayValue('Declaration');
        expect(input).toBeInTheDocument();
        fireEvent.change(input, { target: { value: 'New Knot' } });
        expect(input).toHaveValue('New Knot');
    });

    it('saves individual changes when editing is complete', () => {
        const data = [
            { original: 'Elite handle w/ Declaration knot', handle: 'Elite', knot: 'Declaration' }
        ];
        const onSave = jest.fn();
        render(<BrushSplitTable brushSplits={data} onSave={onSave} />);
        const handleElement = screen.getByText('Elite');
        fireEvent.click(handleElement);
        const input = screen.getByDisplayValue('Elite');
        fireEvent.change(input, { target: { value: 'New Handle' } });
        fireEvent.keyDown(input, { key: 'Enter' });
        expect(onSave).toHaveBeenCalledWith(0, { original: 'Elite handle w/ Declaration knot', handle: 'New Handle', knot: 'Declaration' });
    });

    it('includes a search input that filters rows by handle, knot, or original text', () => {
        const data = [
            { original: 'Elite handle w/ Declaration knot', handle: 'Elite', knot: 'Declaration' },
            { original: 'Omega boar brush', handle: '', knot: 'Omega boar brush' },
            { original: 'Simpson Chubby 2', handle: 'Simpson', knot: 'Chubby 2' }
        ];
        render(<BrushSplitTable brushSplits={data} />);
        const searchInput = screen.getByPlaceholderText('Search...');
        expect(searchInput).toBeInTheDocument();
        fireEvent.change(searchInput, { target: { value: 'Simpson' } });
        expect(screen.getByText('Simpson Chubby 2')).toBeInTheDocument();
        expect(screen.getByText('Simpson')).toBeInTheDocument();
        expect(screen.getByText('Chubby 2')).toBeInTheDocument();
        expect(screen.queryByText('Elite handle w/ Declaration knot')).not.toBeInTheDocument();
        expect(screen.queryByText('Omega boar brush')).not.toBeInTheDocument();
    });

    it('shows a loading indicator when isLoading prop is true', () => {
        const data = [
            { original: 'Elite handle w/ Declaration knot', handle: 'Elite', knot: 'Declaration' }
        ];
        render(<BrushSplitTable brushSplits={data} isLoading={true} />);
        expect(screen.getByText('Loading...')).toBeInTheDocument();
        expect(screen.queryByText('Elite handle w/ Declaration knot')).not.toBeInTheDocument();
        expect(screen.queryByPlaceholderText('Search...')).not.toBeInTheDocument();
    });

    it('shows an error message when hasError prop is true', () => {
        const data = [
            { original: 'Elite handle w/ Declaration knot', handle: 'Elite', knot: 'Declaration' }
        ];
        render(<BrushSplitTable brushSplits={data} hasError={true} />);
        expect(screen.getByText('Error loading data')).toBeInTheDocument();
        expect(screen.queryByText('Elite handle w/ Declaration knot')).not.toBeInTheDocument();
        expect(screen.queryByPlaceholderText('Search...')).not.toBeInTheDocument();
    });

    it('uses virtualized rendering for large datasets', () => {
        const data = Array.from({ length: 1000 }, (_, i) => ({
            original: `Brush ${i}`,
            handle: `Handle ${i}`,
            knot: `Knot ${i}`
        }));
        render(<BrushSplitTable brushSplits={data} />);
        // Should render only visible rows (first few)
        expect(screen.getByText('Brush 0')).toBeInTheDocument();
        expect(screen.getByText('Handle 0')).toBeInTheDocument();
        expect(screen.getByText('Knot 0')).toBeInTheDocument();
        // Should not render all 1000 rows
        expect(screen.queryByText('Brush 999')).not.toBeInTheDocument();
        expect(screen.queryByText('Handle 999')).not.toBeInTheDocument();
        expect(screen.queryByText('Knot 999')).not.toBeInTheDocument();
    });

    it('supports keyboard navigation for moving between rows and fields', () => {
        const data = [
            { original: 'Elite handle w/ Declaration knot', handle: 'Elite', knot: 'Declaration' }
        ];
        render(<BrushSplitTable brushSplits={data} />);
        const handleElement = screen.getByText('Elite');
        handleElement.focus();
        fireEvent.keyDown(handleElement, { key: 'Enter' });
        // Should start editing the handle field
        const input = screen.getByDisplayValue('Elite');
        expect(input).toBeInTheDocument();
    });
}); 