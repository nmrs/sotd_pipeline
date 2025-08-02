import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MismatchAnalyzerDataTable from '@/components/data/MismatchAnalyzerDataTable';
import { MismatchItem } from '@/services/api';

// Mock the BrushSplitModal component
jest.mock('@/components/forms/BrushSplitModal', () => {
    return function MockBrushSplitModal({ isOpen, onClose, original, onSave }: any) {
        if (!isOpen) return null;

        return (
            <div data-testid="brush-split-modal">
                <div>Brush Split Modal</div>
                <div>Original: {original}</div>
                <button onClick={() => onSave({ handle: 'Test Handle', knot: 'Test Knot' })}>
                    Save Split
                </button>
                <button onClick={onClose}>Close</button>
            </div>
        );
    };
});

describe('MismatchAnalyzerDataTable Brush Split Functionality', () => {
    const mockBrushItem: MismatchItem = {
        original: 'Declaration Grooming B2 Badger',
        matched: {},
        mismatch_type: 'no_match',
        count: 1,
        comment_ids: [],
    };

    const mockOnBrushSplitClick = jest.fn();

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('should show edit icon for brush field items', () => {
        render(
            <MismatchAnalyzerDataTable
                data={[mockBrushItem]}
                field="brush"
                onBrushSplitClick={mockOnBrushSplitClick}
            />
        );

        // Should show edit icon for brush items
        expect(screen.getByText('✏️ Declaration Grooming B2 Badger')).toBeInTheDocument();
    });

    it('should not show edit icon for non-brush field items', () => {
        render(
            <MismatchAnalyzerDataTable
                data={[mockBrushItem]}
                field="razor"
                onBrushSplitClick={mockOnBrushSplitClick}
            />
        );

        // Should not show edit icon for non-brush items
        expect(screen.queryByText('✏️ Declaration Grooming B2 Badger')).not.toBeInTheDocument();
        expect(screen.getByText('Declaration Grooming B2 Badger')).toBeInTheDocument();
    });

    it('should call onBrushSplitClick when clicking on brush item', async () => {
        const user = userEvent.setup();

        render(
            <MismatchAnalyzerDataTable
                data={[mockBrushItem]}
                field="brush"
                onBrushSplitClick={mockOnBrushSplitClick}
            />
        );

        // Click on the brush item
        const brushText = screen.getByText('✏️ Declaration Grooming B2 Badger');
        await user.click(brushText);

        // Should call the click handler
        expect(mockOnBrushSplitClick).toHaveBeenCalledWith(mockBrushItem);
    });
}); 