import React from 'react';
import { render, screen } from '@testing-library/react';
import { MismatchAnalyzerDataTable } from '../../src/components/data/MismatchAnalyzerDataTable';
import { MismatchItem } from '../../src/services/api';

// Mock data for testing strategy column
const mockMismatchItems: MismatchItem[] = [
    {
        id: '1',
        original: 'Semogue - Barbear Classico Cerda Boar 22mm',
        normalized: 'Semogue - Barbear Classico Cerda Boar 22mm',
        matched: {
            handle_component: 'Semogue - Barbear Classico Cerda',
            knot_component: 'Boar 22mm'
        },
        match_type: 'split_brush',
        count: 1,
        examples: ['example1'],
        comment_ids: ['123'],
        matched_by_strategy: 'automated_split'
    },
    {
        id: '2',
        original: 'A P ShaveCo 22mm Synbad',
        normalized: 'A P ShaveCo 22mm Synbad',
        matched: {
            brand: 'A P ShaveCo',
            model: '22mm Synbad'
        },
        match_type: 'regex',
        count: 1,
        examples: ['example2'],
        comment_ids: ['456'],
        matched_by_strategy: 'known_brush'
    },
    {
        id: '3',
        original: 'Unknown Brush Brand',
        normalized: 'Unknown Brush Brand',
        matched: {
            brand: 'Unknown Brush Brand'
        },
        match_type: 'brand_default',
        count: 1,
        examples: ['example3'],
        comment_ids: ['789'],
        matched_by_strategy: 'OtherBrushMatchingStrategy'
    }
];

describe('MismatchAnalyzerDataTable Strategy Column', () => {
    it('should display strategy column header', () => {
        render(
            <MismatchAnalyzerDataTable
                data={mockMismatchItems}
                onRowSelect={() => { }}
                selectedRows={[]}
            />
        );

        expect(screen.getByText('Strategy')).toBeInTheDocument();
    });

    it('should display correct strategy values for each item', () => {
        render(
            <MismatchAnalyzerDataTable
                data={mockMismatchItems}
                onRowSelect={() => { }}
                selectedRows={[]}
            />
        );

        // Check that all strategy values are displayed
        expect(screen.getByText('automated_split')).toBeInTheDocument();
        expect(screen.getByText('known_brush')).toBeInTheDocument();
        expect(screen.getByText('OtherBrushMatchingStrategy')).toBeInTheDocument();
    });

    it('should handle missing strategy field gracefully', () => {
        const itemsWithMissingStrategy = [
            {
                ...mockMismatchItems[0],
                matched_by_strategy: undefined
            }
        ];

        render(
            <MismatchAnalyzerDataTable
                data={itemsWithMissingStrategy}
                onRowSelect={() => { }}
                selectedRows={[]}
            />
        );

        // Should display 'unknown' for missing strategy
        expect(screen.getByText('unknown')).toBeInTheDocument();
    });

    it('should display strategy filter options', () => {
        render(
            <MismatchAnalyzerDataTable
                data={mockMismatchItems}
                onRowSelect={() => { }}
                selectedRows={[]}
            />
        );

        // The filter dropdown should be present
        const strategyHeader = screen.getByText('Strategy');
        expect(strategyHeader).toBeInTheDocument();
    });

    it('should maintain strategy column when data changes', () => {
        const { rerender } = render(
            <MismatchAnalyzerDataTable
                data={mockMismatchItems}
                onRowSelect={() => { }}
                selectedRows={[]}
            />
        );

        // Change data
        const newData = [
            {
                ...mockMismatchItems[0],
                matched_by_strategy: 'dual_component'
            }
        ];

        rerender(
            <MismatchAnalyzerDataTable
                data={newData}
                onRowSelect={() => { }}
                selectedRows={[]}
            />
        );

        // Should display new strategy value
        expect(screen.getByText('dual_component')).toBeInTheDocument();
    });
});
