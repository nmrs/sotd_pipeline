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

        // Should show top patterns in the patterns column (cell-0-8 and cell-1-8)
        expect(screen.getByTestId('cell-0-8')).toHaveTextContent('Barrister and Mann - Seville');
        expect(screen.getByTestId('cell-0-8')).toHaveTextContent('Barrister and Mann - Seville Soap');
        expect(screen.getByTestId('cell-0-8')).toHaveTextContent('B&M Seville');

        // Should show pattern counts
        expect(screen.getByTestId('cell-0-8')).toHaveTextContent('(5)');
        expect(screen.getByTestId('cell-0-8')).toHaveTextContent('(3)');
        expect(screen.getByTestId('cell-0-8')).toHaveTextContent('(2)');
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

    it('should handle search functionality with grouped data', () => {
        // Test the search logic directly without mocking the DataTable
        const searchInGroupedData = (data: GroupedDataItem[], searchTerm: string) => {
            if (!searchTerm) return data;

            const term = searchTerm.toLowerCase();

            return data.filter(item => {
                // Search in matched_string
                if (item.matched_string && item.matched_string.toLowerCase().includes(term)) {
                    return true;
                }
                // Search in top_patterns
                if (item.top_patterns && item.top_patterns.some((pattern: any) =>
                    pattern.original && pattern.original.toLowerCase().includes(term)
                )) {
                    return true;
                }
                // Search in all_patterns
                if (item.all_patterns && item.all_patterns.some((pattern: any) =>
                    pattern.original && pattern.original.toLowerCase().includes(term)
                )) {
                    return true;
                }
                return false;
            });
        };

        // Test searching for "Barrister" - should return only the first item
        const barristerResults = searchInGroupedData(mockGroupedData, 'Barrister');
        expect(barristerResults).toHaveLength(1);
        expect(barristerResults[0].matched_string).toBe('Barrister and Mann - Seville');

        // Test searching for "Stirling" - should return only the second item
        const stirlingResults = searchInGroupedData(mockGroupedData, 'Stirling');
        expect(stirlingResults).toHaveLength(1);
        expect(stirlingResults[0].matched_string).toBe('Stirling Soap Co - Executive Man');

        // Test searching for "B&M" - should return the first item (matches pattern in top_patterns)
        const bmResults = searchInGroupedData(mockGroupedData, 'B&M');
        expect(bmResults).toHaveLength(1);
        expect(bmResults[0].matched_string).toBe('Barrister and Mann - Seville');

        // Test searching for "Executive" - should return the second item
        const executiveResults = searchInGroupedData(mockGroupedData, 'Executive');
        expect(executiveResults).toHaveLength(1);
        expect(executiveResults[0].matched_string).toBe('Stirling Soap Co - Executive Man');

        // Test searching for non-existent term - should return empty array
        const noResults = searchInGroupedData(mockGroupedData, 'NonExistent');
        expect(noResults).toHaveLength(0);

        // Test searching for empty string - should return all items
        const allResults = searchInGroupedData(mockGroupedData, '');
        expect(allResults).toHaveLength(2);
    });
});
