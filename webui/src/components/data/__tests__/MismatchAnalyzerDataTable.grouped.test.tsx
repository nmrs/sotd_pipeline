import React from 'react';
import { render, screen } from '@testing-library/react';
import MismatchAnalyzerDataTable from '../MismatchAnalyzerDataTable';
import { GroupedDataItem } from '../../../services/api';

// Mock the DataTable component to avoid complex table rendering in tests
jest.mock('@/components/ui/data-table', () => {
    return {
        DataTable: ({ data, columns }: { data: any[]; columns: any[] }) => (
            <div data-testid="data-table">
                {data.map((item, index) => (
                    <div key={index} data-testid={`row-${index}`}>
                        {columns.map((col, colIndex) => (
                            <div key={colIndex} data-testid={`cell-${index}-${colIndex}`}>
                                {col.cell ? col.cell({ row: { original: item } }) : item[col.accessorKey]}
                            </div>
                        ))}
                    </div>
                ))}
            </div>
        ),
    };
});

describe('MismatchAnalyzerDataTable with Grouped Data', () => {
    const mockGroupedData: GroupedDataItem[] = [
        {
            matched_string: 'Barrister and Mann - Seville',
            total_count: 10,
            top_patterns: [
                { original: 'Barrister and Mann - Seville', count: 5 },
                { original: 'Barrister and Mann - Seville Soap', count: 3 },
                { original: 'B&M Seville', count: 2 },
            ],
            remaining_count: 2,
            all_patterns: [
                { original: 'Barrister and Mann - Seville', count: 5 },
                { original: 'Barrister and Mann - Seville Soap', count: 3 },
                { original: 'B&M Seville', count: 2 },
                { original: 'Barrister & Mann Seville', count: 1 },
                { original: 'B&M - Seville', count: 1 },
            ],
            pattern_count: 5,
            is_grouped: true,
        },
        {
            matched_string: 'Stirling Soap Co - Executive Man',
            total_count: 8,
            top_patterns: [
                { original: 'Stirling Executive Man', count: 4 },
                { original: 'Stirling - Executive Man', count: 3 },
                { original: 'Stirling Soap Co Executive Man', count: 1 },
            ],
            remaining_count: 0,
            all_patterns: [
                { original: 'Stirling Executive Man', count: 4 },
                { original: 'Stirling - Executive Man', count: 3 },
                { original: 'Stirling Soap Co Executive Man', count: 1 },
            ],
            pattern_count: 3,
            is_grouped: true,
        },
    ];

    it('renders grouped data correctly', () => {
        render(
            <MismatchAnalyzerDataTable
                data={mockGroupedData}
                field="soap"
                selectedItems={new Set()}
                onItemSelection={() => { }}
            />
        );

        // Should render the data table
        expect(screen.getByTestId('data-table')).toBeInTheDocument();

        // Should render rows for each grouped item
        expect(screen.getByTestId('row-0')).toBeInTheDocument();
        expect(screen.getByTestId('row-1')).toBeInTheDocument();
    });

    it('displays matched string in original column for grouped data', () => {
        render(
            <MismatchAnalyzerDataTable
                data={mockGroupedData}
                field="soap"
                selectedItems={new Set()}
                onItemSelection={() => { }}
            />
        );

        // Should show matched string in the original column (cell-0-3 and cell-1-3)
        expect(screen.getByTestId('cell-0-3')).toHaveTextContent('Barrister and Mann - Seville');
        expect(screen.getByTestId('cell-1-3')).toHaveTextContent('Stirling Soap Co - Executive Man');
    });

    it('displays total count for grouped data', () => {
        render(
            <MismatchAnalyzerDataTable
                data={mockGroupedData}
                field="soap"
                selectedItems={new Set()}
                onItemSelection={() => { }}
            />
        );

        // Should show total count
        expect(screen.getByText('10')).toBeInTheDocument();
        expect(screen.getByText('8')).toBeInTheDocument();
    });

    it('displays grouped type indicator', () => {
        render(
            <MismatchAnalyzerDataTable
                data={mockGroupedData}
                field="soap"
                selectedItems={new Set()}
                onItemSelection={() => { }}
            />
        );

        // Should show "Grouped" type with icon in the type column (cell-0-2 and cell-1-2)
        expect(screen.getByTestId('cell-0-2')).toHaveTextContent('Grouped');
        expect(screen.getByTestId('cell-1-2')).toHaveTextContent('Grouped');
    });

    it('displays original patterns for grouped data', () => {
        render(
            <MismatchAnalyzerDataTable
                data={mockGroupedData}
                field="soap"
                selectedItems={new Set()}
                onItemSelection={() => { }}
            />
        );

        // Should show top patterns in the patterns column (cell-0-9 and cell-1-9)
        expect(screen.getByTestId('cell-0-9')).toHaveTextContent('Barrister and Mann - Seville');
        expect(screen.getByTestId('cell-0-9')).toHaveTextContent('Barrister and Mann - Seville Soap');
        expect(screen.getByTestId('cell-0-9')).toHaveTextContent('B&M Seville');

        // Should show pattern counts
        expect(screen.getByTestId('cell-0-9')).toHaveTextContent('(5)');
        expect(screen.getByTestId('cell-0-9')).toHaveTextContent('(3)');
        expect(screen.getByTestId('cell-0-9')).toHaveTextContent('(2)');
    });

    it('shows expandable patterns for items with remaining patterns', () => {
        render(
            <MismatchAnalyzerDataTable
                data={mockGroupedData}
                field="soap"
                selectedItems={new Set()}
                onItemSelection={() => { }}
            />
        );

        // Should show "+ n more" for first item (has remaining patterns)
        expect(screen.getByText('+ 2 more')).toBeInTheDocument();

        // Should not show "+ n more" for second item (no remaining patterns)
        expect(screen.queryByText('+ 0 more')).not.toBeInTheDocument();
    });
});
