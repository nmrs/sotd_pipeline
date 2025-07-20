import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import BrushSplitValidator from '../BrushSplitValidator';

// Mock the API calls
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock the MonthSelector component
jest.mock('../../components/MonthSelector', () => {
    return function MockMonthSelector({ selectedMonths, onMonthsChange }: any) {
        return (
            <div data-testid="month-selector">
                <button onClick={() => onMonthsChange(['2024-01'])}>
                    Select Month
                </button>
                <div>Selected: {selectedMonths.join(', ')}</div>
            </div>
        );
    };
});

// Mock the LoadingSpinner component
jest.mock('../../components/LoadingSpinner', () => {
    return function MockLoadingSpinner({ message }: any) {
        return <div data-testid="loading-spinner">{message}</div>;
    };
});

// Mock the ErrorDisplay component
jest.mock('../../components/ErrorDisplay', () => {
    return function MockErrorDisplay({ error, onRetry }: any) {
        return (
            <div data-testid="error-display">
                <div>{error}</div>
                <button onClick={onRetry}>Retry</button>
            </div>
        );
    };
});

const renderWithRouter = (component: React.ReactElement) => {
    return render(
        <BrowserRouter>
            {component}
        </BrowserRouter>
    );
};

describe('BrushSplitValidator', () => {
    beforeEach(() => {
        mockFetch.mockClear();
    });

    it('renders the component with initial state', () => {
        renderWithRouter(<BrushSplitValidator />);

        expect(screen.getByText('Brush Split Validator')).toBeInTheDocument();
        expect(screen.getByText('Select Months')).toBeInTheDocument();
        expect(screen.getByText('Select Months to Begin')).toBeInTheDocument();
    });

    it('shows month selector', () => {
        renderWithRouter(<BrushSplitValidator />);

        expect(screen.getByTestId('month-selector')).toBeInTheDocument();
    });

    it('loads brush splits when months are selected', async () => {
        const mockResponse = {
            brush_splits: [
                {
                    original: 'Test Brush',
                    handle: 'Test Handle',
                    knot: 'Test Knot',
                    validated: false,
                    corrected: false,
                    validated_at: null,
                    system_handle: null,
                    system_knot: null,
                    system_confidence: null,
                    system_reasoning: null,
                    occurrences: []
                }
            ],
            statistics: {
                total: 1,
                validated: 0,
                corrected: 0,
                validation_percentage: 0,
                correction_percentage: 0,
                split_types: {},
                confidence_breakdown: {},
                month_breakdown: {},
                recent_activity: {}
            }
        };

        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => mockResponse
        });

        renderWithRouter(<BrushSplitValidator />);

        // Click the month selector button to select a month
        fireEvent.click(screen.getByText('Select Month'));

        // Wait for the loading state
        await waitFor(() => {
            expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
        });

        // Wait for the data to load
        await waitFor(() => {
            expect(screen.getByText('Brush Splits (1)')).toBeInTheDocument();
        });

        expect(mockFetch).toHaveBeenCalledWith(
            expect.stringContaining('/api/brush-splits/load?months=2024-01')
        );
    });

    it('handles API errors gracefully', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: false,
            status: 500,
            json: async () => ({ detail: 'Internal server error' })
        });

        renderWithRouter(<BrushSplitValidator />);

        // Click the month selector button to select a month
        fireEvent.click(screen.getByText('Select Month'));

        // Wait for the error to be displayed
        await waitFor(() => {
            expect(screen.getByTestId('error-display')).toBeInTheDocument();
        });

        expect(screen.getByText('Server error: 500')).toBeInTheDocument();
    });

    it('shows statistics when data is loaded', async () => {
        const mockResponse = {
            brush_splits: [],
            statistics: {
                total: 100,
                validated: 50,
                corrected: 10,
                validation_percentage: 50.0,
                correction_percentage: 20.0,
                split_types: { delimiter: 30, fiber_hint: 20 },
                confidence_breakdown: { high: 40, medium: 30 },
                month_breakdown: {},
                recent_activity: {}
            }
        };

        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => mockResponse
        });

        renderWithRouter(<BrushSplitValidator />);

        // Click the month selector button to select a month
        fireEvent.click(screen.getByText('Select Month'));

        // Wait for the statistics to be displayed
        await waitFor(() => {
            expect(screen.getByText('Validation Statistics')).toBeInTheDocument();
        });

        expect(screen.getByText('100')).toBeInTheDocument(); // Total
        expect(screen.getByText('50')).toBeInTheDocument(); // Validated
        expect(screen.getByText('20.0%')).toBeInTheDocument(); // Correction rate
        expect(screen.getByText('50.0%')).toBeInTheDocument(); // Validation progress
    });

    it('shows empty state when no brush splits are found', async () => {
        const mockResponse = {
            brush_splits: [],
            statistics: {
                total: 0,
                validated: 0,
                corrected: 0,
                validation_percentage: 0,
                correction_percentage: 0,
                split_types: {},
                confidence_breakdown: {},
                month_breakdown: {},
                recent_activity: {}
            }
        };

        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => mockResponse
        });

        renderWithRouter(<BrushSplitValidator />);

        // Click the month selector button to select a month
        fireEvent.click(screen.getByText('Select Month'));

        // Wait for the empty state to be displayed
        await waitFor(() => {
            expect(screen.getByText('No Brush Splits Found')).toBeInTheDocument();
        });
    });
}); 