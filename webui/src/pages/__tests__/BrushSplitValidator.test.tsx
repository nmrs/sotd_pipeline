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

    it('has search input field', async () => {
        render(<BrushSplitValidator />);

        // Wait for loading to complete and search input to appear
        await waitFor(() => {
            expect(screen.getByPlaceholderText('Search brush splits...')).toBeInTheDocument();
        });
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

    it('allows editing handle field', async () => {
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
            expect(screen.getByText('Test Handle')).toBeInTheDocument();
        });

        // Click on the handle field to start editing
        const handleCell = screen.getByText('Test Handle');
        fireEvent.click(handleCell);

        // Check that an input field appears
        const inputField = screen.getByDisplayValue('Test Handle');
        expect(inputField).toBeInTheDocument();
    });

    it('saves individual changes', async () => {
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
            expect(screen.getByText('Test Handle')).toBeInTheDocument();
        });

        // Click on the handle field to start editing
        const handleCell = screen.getByText('Test Handle');
        fireEvent.click(handleCell);

        // Type in the input field
        const inputField = screen.getByDisplayValue('Test Handle');
        fireEvent.change(inputField, { target: { value: 'Updated Handle' } });

        // Blur the input to save the change
        fireEvent.blur(inputField);

        // Check that the updated value is displayed
        await waitFor(() => {
            expect(screen.getByText('Updated Handle')).toBeInTheDocument();
        });
    });

    it('shows loading state', () => {
        // Mock a slow response
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

        // Check that loading indicator is shown
        expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    it('handles API errors gracefully', async () => {
        // Mock a failed API response
        mockFetch.mockRejectedValueOnce(new Error('API Error'));

        render(<BrushSplitValidator />);

        // Wait for error message to appear
        await waitFor(() => {
            expect(screen.getByText('Error loading brush splits')).toBeInTheDocument();
        });
    });

    it('integrates with navigation', () => {
        render(<BrushSplitValidator />);

        // Check that the component has the correct test ID for navigation
        expect(screen.getByTestId('brush-split-validator')).toBeInTheDocument();

        // Check that the component title is displayed for navigation
        expect(screen.getByText('Brush Split Validator')).toBeInTheDocument();
    });
}); 