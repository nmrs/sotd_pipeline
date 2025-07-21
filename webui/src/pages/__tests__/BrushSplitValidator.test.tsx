import React from 'react';
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
import BrushSplitValidator from '../BrushSplitValidator';

// Mock the API service
jest.mock('../../services/api', () => ({
    getAvailableMonths: jest.fn()
}));

// Mock fetch for brush splits API
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Import the mocked function
import { getAvailableMonths } from '../../services/api';

describe('BrushSplitValidator', () => {
    beforeEach(() => {
        mockFetch.mockClear();
        (getAvailableMonths as jest.Mock).mockClear();

        // Clear the global cache in the hook
        // @ts-ignore - accessing private cache for testing
        if ((global as any).monthsCache !== undefined) {
            (global as any).monthsCache = null;
        }
        // @ts-ignore - accessing private cache for testing
        if ((global as any).cachePromise !== undefined) {
            (global as any).cachePromise = null;
        }

        // Default mock for getAvailableMonths
        (getAvailableMonths as jest.Mock).mockResolvedValue(['2024-01', '2024-02', '2024-03']);

        // Default mock for fetch
        mockFetch.mockImplementation(() =>
            Promise.resolve({
                ok: true,
                json: () => Promise.resolve({ brush_splits: [], statistics: {} })
            })
        );
    });

    it('renders without crashing', () => {
        render(<BrushSplitValidator />);
        expect(screen.getByTestId('brush-split-validator')).toBeInTheDocument();
        expect(screen.getByText('Brush Split Validator')).toBeInTheDocument();
    });

    it('shows month selector after loading', async () => {
        render(<BrushSplitValidator />);

        // Wait for the component to render and show the month selector
        await waitFor(() => {
            expect(screen.getByText('Select Months')).toBeInTheDocument();
        });
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

        render(<BrushSplitValidator />);

        // Wait for month selector to appear
        await waitFor(() => {
            expect(screen.getByText('Select Months')).toBeInTheDocument();
        });

        // Click on month selector to open dropdown
        fireEvent.click(screen.getByText('Select Months'));

        // Select a month
        await waitFor(() => {
            expect(screen.getByText('2024-01')).toBeInTheDocument();
        });

        fireEvent.click(screen.getByText('2024-01'));

        // Wait for the API call to be made
        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('/api/brush-splits/load?months=2024-01'));
        });
    });

    it('displays brush strings when data is loaded', async () => {
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

        render(<BrushSplitValidator />);

        // Wait for month selector to appear
        await waitFor(() => {
            expect(screen.getByText('Select Months')).toBeInTheDocument();
        });

        fireEvent.click(screen.getByText('Select Months'));

        await waitFor(() => {
            expect(screen.getByText('2024-01')).toBeInTheDocument();
        });

        fireEvent.click(screen.getByText('2024-01'));

        // Wait for the brush string to be displayed
        await waitFor(() => {
            expect(screen.getByText('Test Brush')).toBeInTheDocument();
        });
    });

    it('handles API errors gracefully', async () => {
        mockFetch.mockRejectedValueOnce(new Error('Network Error'));

        render(<BrushSplitValidator />);

        // Wait for month selector to appear
        await waitFor(() => {
            expect(screen.getByText('Select Months')).toBeInTheDocument();
        });

        fireEvent.click(screen.getByText('Select Months'));

        await waitFor(() => {
            expect(screen.getByText('2024-01')).toBeInTheDocument();
        });

        fireEvent.click(screen.getByText('2024-01'));

        // Wait for error message to appear
        await waitFor(() => {
            expect(screen.getByText('Error loading brush splits')).toBeInTheDocument();
        });
    });

    it('shows loading state when fetching brush splits', async () => {
        // Mock a delayed response
        mockFetch.mockImplementation(() =>
            new Promise(resolve =>
                setTimeout(() =>
                    resolve({
                        ok: true,
                        json: () => Promise.resolve({ brush_splits: [], statistics: {} })
                    }), 100
                )
            )
        );

        render(<BrushSplitValidator />);

        // Wait for month selector to appear
        await waitFor(() => {
            expect(screen.getByText('Select Months')).toBeInTheDocument();
        });

        fireEvent.click(screen.getByText('Select Months'));

        await waitFor(() => {
            expect(screen.getByText('2024-01')).toBeInTheDocument();
        });

        fireEvent.click(screen.getByText('2024-01'));

        // Should show loading state
        expect(screen.getByText('Loading...')).toBeInTheDocument();
    });
}); 