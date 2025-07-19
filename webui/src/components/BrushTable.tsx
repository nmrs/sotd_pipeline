import React from 'react';
import { VirtualizedTable } from './VirtualizedTable';
import FilteredEntryCheckbox from './FilteredEntryCheckbox';
import { BrushData } from '../utils/brushDataTransformer';

export interface BrushTableProps {
    items: BrushData[];
    onBrushFilter: (itemName: string, isFiltered: boolean) => void;
    onComponentFilter: (componentName: string, isFiltered: boolean) => void;
    filteredStatus: Record<string, boolean>;
    pendingChanges: Record<string, boolean>;
    columnWidths: {
        filtered: number;
        item: number;
        count: number;
        comment_ids: number;
        examples: number;
    };
}

const BrushTable: React.FC<BrushTableProps> = ({
    items,
    onBrushFilter,
    columnWidths
}) => {
    // Create columns for VirtualizedTable
    const columns = [
        {
            key: 'filtered',
            header: 'Filtered',
            width: columnWidths.filtered,
            render: (item: BrushData) => (
                <FilteredEntryCheckbox
                    category="brush"
                    itemName={item.main.text}
                    commentIds={item.main.comment_ids}
                    onStatusChange={(isFiltered) => onBrushFilter(item.main.text, isFiltered)}
                />
            )
        },
        {
            key: 'item',
            header: 'Brush',
            width: columnWidths.item,
            render: (item: BrushData) => <span>{item.main.text}</span>
        },
        {
            key: 'count',
            header: 'Count',
            width: columnWidths.count,
            render: (item: BrushData) => <span>{item.main.count}</span>
        },
        {
            key: 'comment_ids',
            header: 'Comment IDs',
            width: columnWidths.comment_ids,
            render: (item: BrushData) => <span>{item.main.comment_ids.join(', ')}</span>
        },
        {
            key: 'examples',
            header: 'Examples',
            width: columnWidths.examples,
            render: (item: BrushData) => <span>{item.main.examples.join(', ')}</span>
        }
    ];

    return (
        <div className="brush-table">
            <VirtualizedTable
                data={items}
                columns={columns}
                height={400}
                rowHeight={48}
            />
        </div>
    );
};

export default BrushTable; 