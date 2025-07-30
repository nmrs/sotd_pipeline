import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import MismatchAnalyzer from '../MismatchAnalyzer';

// Mock the API functions
jest.mock('../../services/api', () => ({
    analyzeMismatch: jest.fn(),
    getCorrectMatches: jest.fn(),
    markAsCorrect: jest.fn(),
    markAsIntentionallyUnmatched: jest.fn(),
    getAvailableMonths: jest.fn().mockResolvedValue(['2025-01', '2025-02', '2025-03']),
}));

describe('MismatchAnalyzer Split Brush Filters', () => {
    beforeEach(() => {
        // Clear all mocks before each test
        jest.clearAllMocks();
    });

    it('should show split brush filter buttons when field is brush', async () => {
        await act(async () => {
            render(<MismatchAnalyzer />);
        });

        // Change field to brush using the select element directly
        const comboboxes = screen.getAllByRole('combobox');
        const fieldSelect = comboboxes[0]; // First combobox should be the field select
        await act(async () => {
            fireEvent.change(fieldSelect, { target: { value: 'brush' } });
        });

        // Check that split brush filter buttons are now visible
        expect(screen.getByText(/split brushes/i)).toBeInTheDocument();
        expect(screen.getByText(/complete brushes/i)).toBeInTheDocument();
    });

    it('should not show split brush filter buttons when field is not brush', async () => {
        await act(async () => {
            render(<MismatchAnalyzer />);
        });

        // Field should default to razor, so split brush buttons should not be visible
        expect(screen.queryByText(/split brushes/i)).not.toBeInTheDocument();
        expect(screen.queryByText(/complete brushes/i)).not.toBeInTheDocument();
    });

    it('should switch to split brushes filter when button is clicked', async () => {
        await act(async () => {
            render(<MismatchAnalyzer />);
        });

        // Change field to brush
        const comboboxes = screen.getAllByRole('combobox');
        const fieldSelect = comboboxes[0]; // First combobox should be the field select
        await act(async () => {
            fireEvent.change(fieldSelect, { target: { value: 'brush' } });
        });

        // Click the split brushes filter button
        const splitBrushesButton = screen.getByText(/split brushes/i);
        await act(async () => {
            fireEvent.click(splitBrushesButton);
        });

        // The button should now be highlighted (active state)
        expect(splitBrushesButton).toHaveClass('bg-blue-600', 'text-white');
    });

    it('should switch to complete brushes filter when button is clicked', async () => {
        await act(async () => {
            render(<MismatchAnalyzer />);
        });

        // Change field to brush
        const comboboxes = screen.getAllByRole('combobox');
        const fieldSelect = comboboxes[0]; // First combobox should be the field select
        await act(async () => {
            fireEvent.change(fieldSelect, { target: { value: 'brush' } });
        });

        // Click the complete brushes filter button
        const completeBrushesButton = screen.getByText(/complete brushes/i);
        await act(async () => {
            fireEvent.click(completeBrushesButton);
        });

        // The button should now be highlighted (active state)
        expect(completeBrushesButton).toHaveClass('bg-blue-600', 'text-white');
    });
}); 