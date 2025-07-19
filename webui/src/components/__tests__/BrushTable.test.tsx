import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import BrushTable from '../BrushTable';

// Mock data for testing
const mockBrushData = [
    {
        id: '1',
        original: 'Simpson Chubby 2',
        matched: {
            brand: 'Simpson',
            model: 'Chubby 2',
            fiber: 'Badger',
            knot_size_mm: 27,
            handle_maker: 'Simpson'
        },
        match_type: 'regex',
        pattern: 'simp.*chubby\\s*2'
    },
    {
        id: '2',
        original: 'Declaration B15',
        matched: {
            brand: 'Declaration Grooming',
            model: 'B15',
            fiber: 'Badger',
            knot_size_mm: 26,
            handle_maker: 'Declaration Grooming'
        },
        match_type: 'regex',
        pattern: 'declaration.*b15'
    }
];

describe('BrushTable', () => {
    test('should render brush data correctly', () => {
        render(<BrushTable data={mockBrushData} />);

        // Check that brush data is displayed
        expect(screen.getByText('Simpson Chubby 2')).toBeInTheDocument();
        expect(screen.getByText('Declaration B15')).toBeInTheDocument();
        expect(screen.getByText('Simpson')).toBeInTheDocument();
        expect(screen.getByText('Declaration Grooming')).toBeInTheDocument();
    });

    test('should handle empty data gracefully', () => {
        render(<BrushTable data={[]} />);

        // Should show empty state or no data message
        expect(screen.getByText(/no data/i) || screen.getByText(/empty/i)).toBeInTheDocument();
    });

    test('should handle filtering by brand', async () => {
        const user = userEvent.setup();
        render(<BrushTable data={mockBrushData} />);

        // Find filter input (assuming it has a placeholder or label)
        const filterInput = screen.getByPlaceholderText(/filter/i) || screen.getByLabelText(/filter/i);

        // Type in filter
        await user.type(filterInput, 'Simpson');

        // Should show only Simpson brushes
        expect(screen.getByText('Simpson Chubby 2')).toBeInTheDocument();
        expect(screen.queryByText('Declaration B15')).not.toBeInTheDocument();
    });

    test('should display match information correctly', () => {
        render(<BrushTable data={mockBrushData} />);

        // Check that match type is displayed
        expect(screen.getByText('regex')).toBeInTheDocument();

        // Check that fiber information is displayed
        expect(screen.getByText('Badger')).toBeInTheDocument();
    });

    test('should handle row selection', async () => {
        const user = userEvent.setup();
        render(<BrushTable data={mockBrushData} />);

        // Find and click on a row
        const firstRow = screen.getByText('Simpson Chubby 2').closest('tr');
        if (firstRow) {
            await user.click(firstRow);

            // Should show selection state (this depends on your implementation)
            expect(firstRow).toHaveClass(/selected/i);
        }
    });
}); 