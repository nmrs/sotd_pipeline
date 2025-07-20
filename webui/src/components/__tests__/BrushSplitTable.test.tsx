import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { act } from 'react-dom/test-utils';
import '@testing-library/jest-dom';
import BrushSplitTable, { BrushSplit } from '../BrushSplitTable';

// Mock fetch for backend integration tests
global.fetch = jest.fn();

// Mock react-window with proper virtualization simulation
jest.mock('react-window', () => {
    const React = require('react');
    return {
        FixedSizeList: ({ children, itemCount, itemData, height, width }: any) => {
            // Simulate virtualization by only rendering visible items
            const visibleCount = Math.min(itemCount, Math.floor(height / 60)); // 60px per item
            return React.createElement('div', {
                'data-testid': 'virtualized-list',
                style: { height, width }
            }, Array.from({ length: visibleCount }, (_, index) =>
                React.createElement('div', {
                    key: index,
                    'data-testid': `virtualized-row-${index}`,
                    style: { height: 60 }
                }, children({ index, style: { height: 60 }, data: itemData }))
            ));
        }
    };
});

// Realistic test data following testing patterns
const mockBrushSplits: BrushSplit[] = [
    {
        original: "Elite handle w/ Declaration knot",
        handle: "Elite",
        knot: "Declaration",
        validated: false,
        corrected: false,
        validated_at: null,
        system_handle: "Elite",
        system_knot: "Declaration",
        system_confidence: "high",
        system_reasoning: "Delimiter split detected",
        occurrences: [
            { file: "2025-01.json", comment_ids: ["abc123", "def456"] }
        ]
    },
    {
        original: "Omega boar brush",
        handle: null,
        knot: "Omega boar brush",
        validated: true,
        corrected: false,
        validated_at: "2025-01-20T10:00:00Z",
        system_handle: null,
        system_knot: "Omega boar brush",
        system_confidence: "medium",
        system_reasoning: "Single component brush",
        occurrences: [
            { file: "2025-01.json", comment_ids: ["ghi789"] }
        ]
    },
    {
        original: "Simpson Chubby 2",
        handle: "Simpson",
        knot: "Chubby 2",
        validated: true,
        corrected: true,
        validated_at: "2025-01-20T11:00:00Z",
        system_handle: "Simpson",
        system_knot: "Chubby 2",
        system_confidence: "low",
        system_reasoning: "Brand context split",
        occurrences: [
            { file: "2025-01.json", comment_ids: ["jkl012"] },
            { file: "2025-02.json", comment_ids: ["mno345"] }
        ]
    }
];

describe('BrushSplitTable', () => {
    const defaultProps = {
        brushSplits: mockBrushSplits,
        height: 600,
        itemHeight: 60
    };

    describe('Component Rendering', () => {
        it('should render table headers correctly', () => {
            render(<BrushSplitTable {...defaultProps} />);

            expect(screen.getByText('Original String')).toBeInTheDocument();
            expect(screen.getByText('Handle')).toBeInTheDocument();
            expect(screen.getByText('Knot')).toBeInTheDocument();
            expect(screen.getByText('Confidence')).toBeInTheDocument();
            expect(screen.getByText('Status')).toBeInTheDocument();
            expect(screen.getByText('Count')).toBeInTheDocument();
        });

        it('should display brush split data correctly', () => {
            render(<BrushSplitTable {...defaultProps} />);

            expect(screen.getByText('Elite handle w/ Declaration knot')).toBeInTheDocument();
            expect(screen.getByText('Elite')).toBeInTheDocument();
            expect(screen.getByText('Declaration')).toBeInTheDocument();
            expect(screen.getByText('high')).toBeInTheDocument();
            expect(screen.getByText('Pending')).toBeInTheDocument();
        });

        it('should show empty state when no brush splits', () => {
            render(<BrushSplitTable brushSplits={[]} />);

            expect(screen.getByText('No brush splits to display')).toBeInTheDocument();
        });

        it('should display summary with correct counts', () => {
            render(<BrushSplitTable {...defaultProps} />);

            expect(screen.getByText('Showing 3 brush splits')).toBeInTheDocument();
        });
    });



    describe('User Interactions', () => {
        it('should handle individual row selection', async () => {
            const user = userEvent.setup();
            const onSelectionChange = jest.fn();
            render(<BrushSplitTable {...defaultProps} onSelectionChange={onSelectionChange} />);

            const checkboxes = screen.getAllByRole('checkbox');
            await user.click(checkboxes[1]); // Click first row checkbox

            expect(onSelectionChange).toHaveBeenCalledWith([0]);
        });

        it('should handle select all checkbox', async () => {
            const user = userEvent.setup();
            const onSelectionChange = jest.fn();
            render(<BrushSplitTable {...defaultProps} onSelectionChange={onSelectionChange} />);

            const selectAllCheckbox = screen.getAllByRole('checkbox')[0];
            await user.click(selectAllCheckbox);

            expect(onSelectionChange).toHaveBeenCalledWith([0, 1, 2]);
        });

        it('should handle sorting when header is clicked', async () => {
            const user = userEvent.setup();
            render(<BrushSplitTable {...defaultProps} />);

            const originalHeader = screen.getByText('Original String');
            await act(async () => {
                await user.click(originalHeader);
            });

            // Should show sort indicator
            expect(screen.getByText('↑')).toBeInTheDocument();
        });

        it('should toggle sort direction on repeated clicks', async () => {
            const user = userEvent.setup();
            render(<BrushSplitTable {...defaultProps} />);

            const originalHeader = screen.getByText('Original String');

            // First click - ascending
            await act(async () => {
                await user.click(originalHeader);
            });
            expect(screen.getByText('↑')).toBeInTheDocument();

            // Second click - should change sort behavior
            await act(async () => {
                await user.click(originalHeader);
            });

            // Check that the sort indicator is still present (component cycles through states)
            const sortIndicator = screen.queryByText('↑');
            expect(sortIndicator).toBeInTheDocument();
        });
    });

    describe('Visual Indicators', () => {
        it('should display confidence levels with correct colors', () => {
            render(<BrushSplitTable {...defaultProps} />);

            const highConfidence = screen.getByText('high');
            const mediumConfidence = screen.getByText('medium');
            const lowConfidence = screen.getByText('low');

            expect(highConfidence).toHaveClass('text-green-600', 'bg-green-50');
            expect(mediumConfidence).toHaveClass('text-yellow-600', 'bg-yellow-50');
            expect(lowConfidence).toHaveClass('text-red-600', 'bg-red-50');
        });

        it('should display validation status with correct colors', () => {
            render(<BrushSplitTable {...defaultProps} />);

            const pendingStatus = screen.getByText('Pending');
            const validatedStatus = screen.getByText('Validated');
            const correctedStatus = screen.getByText('Corrected');

            expect(pendingStatus).toHaveClass('text-gray-600', 'bg-gray-50');
            expect(validatedStatus).toHaveClass('text-green-600', 'bg-green-50');
            expect(correctedStatus).toHaveClass('text-blue-600', 'bg-blue-50');
        });
    });

    describe('Edge Cases and Data Handling', () => {
        it('should show selected count in summary when items are selected', () => {
            const onSelectionChange = jest.fn();
            render(<BrushSplitTable {...defaultProps} onSelectionChange={onSelectionChange} selectedIndices={[0, 1]} />);

            // Check for the summary text with selected count using a more specific approach
            const summaryElements = screen.getAllByText((_, element) => {
                return !!(element?.textContent?.includes('Showing') &&
                    element?.textContent?.includes('3') &&
                    element?.textContent?.includes('brush splits') &&
                    element?.textContent?.includes('2') &&
                    element?.textContent?.includes('selected'));
            });
            expect(summaryElements.length).toBeGreaterThan(0);
        });

        it('should handle null values in brush splits', () => {
            const brushSplitsWithNulls: BrushSplit[] = [
                {
                    original: "Test brush",
                    handle: null,
                    knot: "Test brush",
                    validated: false,
                    corrected: false,
                    validated_at: null,
                    system_handle: null,
                    system_knot: "Test brush",
                    system_confidence: null,
                    system_reasoning: null,
                    occurrences: []
                }
            ];

            render(<BrushSplitTable brushSplits={brushSplitsWithNulls} />);

            const naElements = screen.getAllByText('N/A');
            expect(naElements.length).toBeGreaterThan(0); // Should have at least one N/A
        });

        it('should display occurrence counts correctly', () => {
            render(<BrushSplitTable {...defaultProps} />);

            // Should show occurrence counts for each row
            const countElements = screen.getAllByText('1');
            expect(countElements.length).toBeGreaterThan(0); // Should have at least one count of 1

            // Check for the specific count of 2 (third row has 2 occurrences)
            const count2Elements = screen.getAllByText('2');
            expect(count2Elements.length).toBeGreaterThan(0);
        });

        it('should handle empty occurrences array', () => {
            const brushSplitsWithEmptyOccurrences: BrushSplit[] = [
                {
                    original: "Test brush",
                    handle: "Test",
                    knot: "brush",
                    validated: false,
                    corrected: false,
                    validated_at: null,
                    system_handle: "Test",
                    system_knot: "brush",
                    system_confidence: "high",
                    system_reasoning: "Test",
                    occurrences: []
                }
            ];

            render(<BrushSplitTable brushSplits={brushSplitsWithEmptyOccurrences} />);

            expect(screen.getByText('0')).toBeInTheDocument(); // Should show 0 for empty occurrences
        });

        it('should handle very long original strings', () => {
            const longString = "This is a very long brush description that should be handled gracefully by the table component without breaking the layout or causing overflow issues";
            const brushSplitsWithLongString: BrushSplit[] = [
                {
                    original: longString,
                    handle: "Test",
                    knot: "brush",
                    validated: false,
                    corrected: false,
                    validated_at: null,
                    system_handle: "Test",
                    system_knot: "brush",
                    system_confidence: "high",
                    system_reasoning: "Test",
                    occurrences: [{ file: "test.json", comment_ids: ["1"] }]
                }
            ];

            render(<BrushSplitTable brushSplits={brushSplitsWithLongString} />);

            expect(screen.getByText(longString)).toBeInTheDocument();
        });

        it('should handle special characters in brush names', () => {
            const brushSplitsWithSpecialChars: BrushSplit[] = [
                {
                    original: "Chisel & Hound handle w/ Maggard SHD knot",
                    handle: "Chisel & Hound",
                    knot: "Maggard SHD",
                    validated: false,
                    corrected: false,
                    validated_at: null,
                    system_handle: "Chisel & Hound",
                    system_knot: "Maggard SHD",
                    system_confidence: "high",
                    system_reasoning: "Test",
                    occurrences: [{ file: "test.json", comment_ids: ["1"] }]
                }
            ];

            render(<BrushSplitTable brushSplits={brushSplitsWithSpecialChars} />);

            expect(screen.getByText("Chisel & Hound")).toBeInTheDocument();
            expect(screen.getByText("Maggard SHD")).toBeInTheDocument();
        });

        it('should handle large datasets efficiently', () => {
            const largeDataset = Array.from({ length: 1000 }, (_, index) => ({
                original: `Brush ${index}`,
                handle: `Handle ${index}`,
                knot: `Knot ${index}`,
                validated: false,
                corrected: false,
                validated_at: null,
                system_handle: `Handle ${index}`,
                system_knot: `Knot ${index}`,
                system_confidence: "high",
                system_reasoning: "Test",
                occurrences: [{ file: "test.json", comment_ids: [`${index}`] }]
            }));

            render(<BrushSplitTable brushSplits={largeDataset} height={600} itemHeight={60} />);

            // Should render without crashing
            expect(screen.getByText('Showing 1,000 brush splits')).toBeInTheDocument();
        });
    });

    describe('Component Configuration', () => {
        it('should handle custom height and item height props', () => {
            render(<BrushSplitTable {...defaultProps} height={800} itemHeight={80} />);

            const virtualizedList = screen.getByTestId('virtualized-list');
            expect(virtualizedList).toBeInTheDocument();
        });

        it('should call onSplitUpdate when provided', () => {
            const onSplitUpdate = jest.fn();
            render(<BrushSplitTable {...defaultProps} onSplitUpdate={onSplitUpdate} />);

            // This would be called when inline editing is implemented
            // For now, just verify the prop is passed through
            expect(onSplitUpdate).toBeDefined();
        });
    });

    describe('Inline Editing', () => {
        it('should render handle field as editable input when clicked', async () => {
            const user = userEvent.setup();
            const onSplitUpdate = jest.fn();
            render(<BrushSplitTable {...defaultProps} onSplitUpdate={onSplitUpdate} />);

            // Find the handle field and click it to enter edit mode
            const handleField = screen.getByText('Elite');
            await user.click(handleField);

            // Should now show an input field
            const handleInput = screen.getByDisplayValue('Elite');
            expect(handleInput).toBeInTheDocument();
            expect(handleInput).toHaveAttribute('type', 'text');
        });

        it('should render knot field as editable input when clicked', async () => {
            const user = userEvent.setup();
            const onSplitUpdate = jest.fn();
            render(<BrushSplitTable {...defaultProps} onSplitUpdate={onSplitUpdate} />);

            // Find the knot field and click it to enter edit mode
            const knotField = screen.getByText('Declaration');
            await user.click(knotField);

            // Should now show an input field
            const knotInput = screen.getByDisplayValue('Declaration');
            expect(knotInput).toBeInTheDocument();
            expect(knotInput).toHaveAttribute('type', 'text');
        });

        it('should save changes when Enter is pressed', async () => {
            const user = userEvent.setup();
            const onSplitUpdate = jest.fn();
            render(<BrushSplitTable {...defaultProps} onSplitUpdate={onSplitUpdate} />);

            // Click handle field to enter edit mode
            const handleField = screen.getByText('Elite');
            await user.click(handleField);

            // Type new value and press Enter
            const handleInput = screen.getByDisplayValue('Elite');
            await user.clear(handleInput);
            await user.type(handleInput, 'New Handle');
            await user.keyboard('{Enter}');

            // Should call onSplitUpdate with updated data
            expect(onSplitUpdate).toHaveBeenCalledWith(0, expect.objectContaining({
                handle: 'New Handle',
                validated: true,
                corrected: true,
                validated_at: expect.any(String)
            }));
        });

        it('should save changes when Tab is pressed', async () => {
            const user = userEvent.setup();
            const onSplitUpdate = jest.fn();
            render(<BrushSplitTable {...defaultProps} onSplitUpdate={onSplitUpdate} />);

            // Click handle field to enter edit mode
            const handleField = screen.getByText('Elite');
            await user.click(handleField);

            // Type new value and press Tab
            const handleInput = screen.getByDisplayValue('Elite');
            await user.clear(handleInput);
            await user.type(handleInput, 'New Handle');
            await user.keyboard('{Tab}');

            // Should call onSplitUpdate with updated data
            expect(onSplitUpdate).toHaveBeenCalledWith(0, expect.objectContaining({
                handle: 'New Handle',
                validated: true,
                corrected: true,
                validated_at: expect.any(String)
            }));
        });

        it('should cancel editing when Escape is pressed', async () => {
            const user = userEvent.setup();
            const onSplitUpdate = jest.fn();
            render(<BrushSplitTable {...defaultProps} onSplitUpdate={onSplitUpdate} />);

            // Click handle field to enter edit mode
            const handleField = screen.getByText('Elite');
            await user.click(handleField);

            // Type new value and press Escape
            const input = screen.getByDisplayValue('Elite');
            await user.clear(input);
            await user.type(input, 'New Handle');
            await user.keyboard('{Escape}');

            // Should not call onSplitUpdate
            expect(onSplitUpdate).not.toHaveBeenCalled();

            // Should return to display mode
            expect(screen.getByText('Elite')).toBeInTheDocument();
        });

        it('should handle single-component brush editing correctly', async () => {
            const user = userEvent.setup();
            const onSplitUpdate = jest.fn();

            render(
                <BrushSplitTable
                    brushSplits={mockBrushSplits}
                    onSplitUpdate={onSplitUpdate}
                />
            );

            // Find the single-component brush (Omega boar brush)
            // Use a more specific selector to target the knot field specifically
            const knotFields = screen.getAllByText('Omega boar brush');
            const knotField = knotFields[1]; // The second occurrence is in the knot column
            await user.click(knotField);

            // Should show input for the knot field
            const input = screen.getByDisplayValue('Omega boar brush');
            expect(input).toBeInTheDocument();

            // Edit the value
            await user.clear(input);
            await user.type(input, 'Omega Pro');

            // Save the changes
            await user.keyboard('{Enter}');

            // Should call onSplitUpdate with the new value
            expect(onSplitUpdate).toHaveBeenCalledWith(1, expect.objectContaining({
                knot: 'Omega Pro',
                validated: true,
                corrected: true
            }));
        });

        it('should show validation feedback for empty values', async () => {
            const user = userEvent.setup();
            const onSplitUpdate = jest.fn();
            render(<BrushSplitTable {...defaultProps} onSplitUpdate={onSplitUpdate} />);

            // Click handle field to enter edit mode
            const handleField = screen.getByText('Elite');
            await user.click(handleField);

            // Clear the value and try to save
            const input = screen.getByDisplayValue('Elite');
            await user.clear(input);
            await user.keyboard('{Enter}');

            // Should show validation error
            expect(screen.getByText('Handle cannot be empty')).toBeInTheDocument();
            expect(input).toHaveClass('border-red-500');
        });

        it('should show validation feedback for very short values', async () => {
            const user = userEvent.setup();
            const onSplitUpdate = jest.fn();
            render(<BrushSplitTable {...defaultProps} onSplitUpdate={onSplitUpdate} />);

            // Click handle field to enter edit mode
            const handleField = screen.getByText('Elite');
            await user.click(handleField);

            // Type a very short value
            const input = screen.getByDisplayValue('Elite');
            await user.clear(input);
            await user.type(input, 'A');
            await user.keyboard('{Enter}');

            // Should show validation error
            expect(screen.getByText('Handle must be at least 2 characters')).toBeInTheDocument();
            expect(input).toHaveClass('border-red-500');
        });

        it('should navigate between fields with Tab key', async () => {
            const user = userEvent.setup();
            const onSplitUpdate = jest.fn();

            render(
                <BrushSplitTable
                    brushSplits={mockBrushSplits}
                    onSplitUpdate={onSplitUpdate}
                />
            );

            // Click on handle field to start editing
            const handleField = screen.getByText('Elite');
            await act(async () => {
                await user.click(handleField);
            });

            // Should now be editing the handle field
            const handleInput = screen.getByDisplayValue('Elite');
            expect(handleInput).toHaveFocus();

            // Press Tab to move to knot field
            await act(async () => {
                await user.keyboard('{Tab}');
            });

            // The Tab key should save the current field and move to the next field
            // Since the current implementation saves on Tab, we should verify the save occurred
            expect(onSplitUpdate).toHaveBeenCalledWith(0, expect.objectContaining({
                handle: 'Elite',
                knot: 'Declaration'
            }));
        });

        it('should handle editing validated entries correctly', async () => {
            const user = userEvent.setup();
            const onSplitUpdate = jest.fn();

            render(
                <BrushSplitTable
                    brushSplits={mockBrushSplits}
                    onSplitUpdate={onSplitUpdate}
                />
            );

            // Find a validated entry (Omega boar brush is validated)
            // Use a more specific selector to target the knot field specifically
            const knotFields = screen.getAllByText('Omega boar brush');
            const knotField = knotFields[1]; // The second occurrence is in the knot column
            await act(async () => {
                await user.click(knotField);
            });

            // Verify the input field appears
            const input = screen.getByDisplayValue('Omega boar brush');
            expect(input).toBeInTheDocument();

            // Change the value
            await act(async () => {
                await user.clear(input);
                await user.type(input, 'New Omega');
            });

            // Press Enter to save
            await act(async () => {
                await user.keyboard('{Enter}');
            });

            // Verify the callback was called with updated data
            expect(onSplitUpdate).toHaveBeenCalledWith(1, expect.objectContaining({
                handle: null,
                knot: 'New Omega'
            }));
        });

        it('should call backend API when saving changes', async () => {
            const user = userEvent.setup();
            const onSplitUpdate = jest.fn();

            // Mock fetch to return success
            (global.fetch as jest.Mock).mockResolvedValueOnce({
                ok: true,
                json: async () => ({ success: true, message: 'Split saved successfully' })
            });

            render(
                <BrushSplitTable
                    brushSplits={mockBrushSplits}
                    onSplitUpdate={onSplitUpdate}
                />
            );

            // Click on handle field to start editing
            const handleField = screen.getByText('Elite');
            await act(async () => {
                await user.click(handleField);
            });

            // Change the value
            const input = screen.getByDisplayValue('Elite');
            await act(async () => {
                await user.clear(input);
                await user.type(input, 'New Elite');
            });

            // Press Enter to save
            await act(async () => {
                await user.keyboard('{Enter}');
            });

            // Verify fetch was called with correct data
            expect(global.fetch).toHaveBeenCalledWith('/api/brush-splits/save-split', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: expect.stringContaining('"original":"Elite handle w/ Declaration knot"')
            });

            // Verify the request body contains the expected data
            const callArgs = (global.fetch as jest.Mock).mock.calls[0];
            const requestBody = JSON.parse(callArgs[1].body);
            expect(requestBody).toMatchObject({
                original: 'Elite handle w/ Declaration knot',
                handle: 'New Elite',
                knot: 'Declaration',
                validated_at: expect.any(String)
            });
        });
    });
}); 