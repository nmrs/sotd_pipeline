import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import BrushSplitValidator from '../BrushSplitValidator';

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Default mock for fetch to prevent errors in tests that don't set up specific mocks
mockFetch.mockImplementation(() =>
    Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ brush_splits: [], statistics: {} })
    })
);

describe('BrushSplitValidator', () => {
    beforeEach(() => {
        mockFetch.mockClear();
        // Reset to default mock
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

    it('loads data when mounted', async () => {
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

        // Wait for the API call to be made
        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith('/api/brush-splits/load');
        });
    });

    it('displays brush strings', async () => {
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

        // Wait for the brush string to be displayed
        await waitFor(() => {
            expect(screen.getByText('Test Brush')).toBeInTheDocument();
        });
    });

    it('displays data in table format', async () => {
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

        // Wait for the table to be displayed
        await waitFor(() => {
            expect(screen.getByRole('table')).toBeInTheDocument();
        });

        // Check for table headers
        expect(screen.getByText('Handle')).toBeInTheDocument();
        expect(screen.getByText('Knot')).toBeInTheDocument();
        expect(screen.getByText('Original')).toBeInTheDocument();
    });

    it('has search input field', () => {
        render(<BrushSplitValidator />);
        expect(screen.getByPlaceholderText('Search brush splits...')).toBeInTheDocument();
    });

    it('filters data when search is used', async () => {
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
                },
                {
                    original: 'Another Brush',
                    handle: 'Another Handle',
                    knot: 'Another Knot',
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
                total: 2,
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

        // Wait for data to load
        await waitFor(() => {
            expect(screen.getByText('Test Brush')).toBeInTheDocument();
            expect(screen.getByText('Another Brush')).toBeInTheDocument();
        });

        // Type in search field
        const searchInput = screen.getByPlaceholderText('Search brush splits...');
        fireEvent.change(searchInput, { target: { value: 'Test' } });

        // Check that only matching data is displayed
        expect(screen.getByText('Test Brush')).toBeInTheDocument();
        expect(screen.queryByText('Another Brush')).not.toBeInTheDocument();
    });

    it('allows row selection', async () => {
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

        // Wait for data to load
        await waitFor(() => {
            expect(screen.getByText('Test Brush')).toBeInTheDocument();
        });

        // Check for checkbox in the first row
        const checkbox = screen.getByRole('checkbox');
        expect(checkbox).toBeInTheDocument();

        // Click the checkbox
        fireEvent.click(checkbox);

        // Check that the checkbox is now checked
        expect(checkbox).toBeChecked();
    });
}); 