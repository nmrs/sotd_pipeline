import React, { useMemo } from 'react';
import { VirtualizedTable } from './VirtualizedTable';
import FilteredEntryCheckbox from './FilteredEntryCheckbox';
import { BrushData } from '../utils/brushDataTransformer';

export interface BrushTableProps {
    items: BrushData[];
    onBrushFilter: (itemName: string, isFiltered: boolean) => void;
    onComponentFilter: (componentName: string, isFiltered: boolean) => void;
    filteredStatus?: Record<string, boolean>;
    pendingChanges?: Record<string, boolean>;
    columnWidths: {
        filtered: number;
        brush: number;
        handle: number;
        knot: number;
        count: number;
        comment_ids: number;
        examples: number;
    };
    onCommentClick?: (commentId: string) => void;
    commentLoading?: boolean;
}

// Flatten brush data for VirtualizedTable while preserving component information
const flattenBrushData = (items: BrushData[], filteredStatus: Record<string, boolean> = {}): Array<{
    main: BrushData['main'];
    components: BrushData['components'];
    type: 'main' | 'handle' | 'knot';
    parentText?: string;
    isParentFiltered?: boolean;
}> => {
    const flattened: Array<{
        main: BrushData['main'];
        components: BrushData['components'];
        type: 'main' | 'handle' | 'knot';
        parentText?: string;
        isParentFiltered?: boolean;
    }> = [];

    items.forEach((item) => {
        const isMainFiltered = filteredStatus[item.main.text] || false;

        // Add main brush row
        flattened.push({
            main: item.main,
            components: item.components,
            type: 'main'
        });

        // Always add component sub-rows, but mark them as dimmed if parent is filtered
        if (item.components.handle) {
            flattened.push({
                main: item.main,
                components: item.components,
                type: 'handle',
                parentText: item.main.text,
                isParentFiltered: isMainFiltered
            });
        }
        if (item.components.knot) {
            flattened.push({
                main: item.main,
                components: item.components,
                type: 'knot',
                parentText: item.main.text,
                isParentFiltered: isMainFiltered
            });
        }
    });

    return flattened;
};

const BrushTable: React.FC<BrushTableProps> = ({
    items,
    onBrushFilter,
    onComponentFilter,
    filteredStatus = {},
    pendingChanges = {},
    columnWidths,
    onCommentClick,
    commentLoading = false
}) => {
    // Handle null/undefined items gracefully
    const safeItems = useMemo(() => items || [], [items]);

    // Flatten brush data for virtualization
    const flattenedData = useMemo(() => {
        return flattenBrushData(safeItems, filteredStatus);
    }, [safeItems, filteredStatus]);

    // Create columns for VirtualizedTable
    const columns = useMemo(() => [
        {
            key: 'filtered',
            header: 'Filtered',
            width: columnWidths.filtered,
            render: (item: any) => {
                if (item.type === 'main') {
                    const isCurrentlyFiltered = filteredStatus[item.main.text] || false;
                    const hasPendingChange = item.main.text in pendingChanges;
                    const pendingValue = pendingChanges[item.main.text];
                    const displayValue = hasPendingChange ? pendingValue : isCurrentlyFiltered;

                    return (
                        <FilteredEntryCheckbox
                            itemName={item.main.text}
                            commentIds={item.main.comment_ids}
                            isFiltered={displayValue}
                            onStatusChange={(isFiltered) => onBrushFilter(item.main.text, isFiltered)}
                            uniqueId="main"
                        />
                    );
                } else if (item.type === 'handle' && item.components.handle) {
                    // Hide checkbox if parent is filtered
                    const isMainFiltered = filteredStatus[item.main.text] || false;
                    if (isMainFiltered) {
                        return <div style={{ width: '100%', height: '100%' }}></div>;
                    }

                    const isCurrentlyFiltered = filteredStatus[item.components.handle.text] || false;
                    const hasPendingChange = item.components.handle.text in pendingChanges;
                    const pendingValue = pendingChanges[item.components.handle.text];
                    const displayValue = hasPendingChange ? pendingValue : isCurrentlyFiltered;

                    return (
                        <FilteredEntryCheckbox
                            itemName={item.components.handle.text}
                            commentIds={item.main.comment_ids}
                            isFiltered={displayValue}
                            onStatusChange={(isFiltered) => onComponentFilter(item.components.handle.text, isFiltered)}
                            uniqueId="handle"
                        />
                    );
                } else if (item.type === 'knot' && item.components.knot) {
                    // Hide checkbox if parent is filtered
                    const isMainFiltered = filteredStatus[item.main.text] || false;
                    if (isMainFiltered) {
                        return <div style={{ width: '100%', height: '100%' }}></div>;
                    }

                    const isCurrentlyFiltered = filteredStatus[item.components.knot.text] || false;
                    const hasPendingChange = item.components.knot.text in pendingChanges;
                    const pendingValue = pendingChanges[item.components.knot.text];
                    const displayValue = hasPendingChange ? pendingValue : isCurrentlyFiltered;

                    return (
                        <FilteredEntryCheckbox
                            itemName={item.components.knot.text}
                            commentIds={item.main.comment_ids}
                            isFiltered={displayValue}
                            onStatusChange={(isFiltered) => onComponentFilter(item.components.knot.text, isFiltered)}
                            uniqueId="knot"
                        />
                    );
                }
                return null;
            }
        },
        {
            key: 'brush',
            header: 'Brush',
            width: columnWidths.brush,
            render: (item: any) => {
                const isMainFiltered = filteredStatus[item.main.text] || false;

                if (item.type === 'main') {
                    return (
                        <div className="flex items-center">
                            <span className={`font-medium text-sm ${isMainFiltered ? 'text-gray-400 line-through' : 'text-gray-900'}`}>
                                {item.main.text}
                                {isMainFiltered && (
                                    <span className="ml-2 text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                                        Filtered
                                    </span>
                                )}
                            </span>
                        </div>
                    );
                } else if (item.type === 'handle' && item.components.handle) {
                    const isMainFiltered = filteredStatus[item.main.text] || false;
                    return (
                        <div className="flex items-center pl-4" style={{ opacity: isMainFiltered ? 0.5 : 1 }}>
                            <span className={`text-sm ${item.components.handle.status === 'Matched' ? 'text-gray-400' : 'text-gray-700'}`}>
                                🔧 Handle: {item.components.handle.text}
                                {item.components.handle.status === 'Matched' && (
                                    <span className="ml-2 text-xs text-green-600 bg-green-100 px-2 py-1 rounded">
                                        Matched
                                    </span>
                                )}
                                {item.components.handle.status === 'Unmatched' && (
                                    <span className="ml-2 text-xs text-red-600 bg-red-100 px-2 py-1 rounded">
                                        Unmatched
                                    </span>
                                )}
                            </span>
                        </div>
                    );
                } else if (item.type === 'knot' && item.components.knot) {
                    const isMainFiltered = filteredStatus[item.main.text] || false;
                    return (
                        <div className="flex items-center pl-4" style={{ opacity: isMainFiltered ? 0.5 : 1 }}>
                            <span className={`text-sm ${item.components.knot.status === 'Matched' ? 'text-gray-400' : 'text-gray-700'}`}>
                                🧶 Knot: {item.components.knot.text}
                                {item.components.knot.status === 'Matched' && (
                                    <span className="ml-2 text-xs text-green-600 bg-green-100 px-2 py-1 rounded">
                                        Matched
                                    </span>
                                )}
                                {item.components.knot.status === 'Unmatched' && (
                                    <span className="ml-2 text-xs text-red-600 bg-red-100 px-2 py-1 rounded">
                                        Unmatched
                                    </span>
                                )}
                            </span>
                        </div>
                    );
                }
                return null;
            }
        },
        {
            key: 'count',
            header: 'Count',
            width: columnWidths.count,
            render: (item: any) => {
                if (item.type === 'main') {
                    return <span className="text-gray-500 text-sm">{item.main.count}</span>;
                }
                const isMainFiltered = filteredStatus[item.main.text] || false;
                return <span className="text-gray-400 text-sm" style={{ opacity: isMainFiltered ? 0.5 : 1 }}>-</span>;
            }
        },
        {
            key: 'comment_ids',
            header: 'Comment IDs',
            width: columnWidths.comment_ids,
            render: (item: any) => {
                if (item.type === 'main') {
                    return (
                        <div className="text-sm">
                            {item.main.comment_ids && item.main.comment_ids.length > 0 ? (
                                <div className="flex flex-wrap gap-1">
                                    {item.main.comment_ids.slice(0, 3).map((commentId: string, index: number) => (
                                        <button
                                            key={index}
                                            onClick={() => onCommentClick?.(commentId)}
                                            disabled={commentLoading}
                                            className="text-blue-600 hover:text-blue-800 underline text-xs bg-blue-50 px-2 py-1 rounded hover:bg-blue-100 disabled:opacity-50 disabled:cursor-not-allowed"
                                        >
                                            {commentLoading ? 'Loading...' : commentId}
                                        </button>
                                    ))}
                                    {item.main.comment_ids.length > 3 && (
                                        <span className="text-gray-500 text-xs">
                                            +{item.main.comment_ids.length - 3} more
                                        </span>
                                    )}
                                </div>
                            ) : (
                                <span className="text-gray-400 text-xs">No comment IDs</span>
                            )}
                        </div>
                    );
                }
                const isMainFiltered = filteredStatus[item.main.text] || false;
                return <span className="text-gray-400 text-sm" style={{ opacity: isMainFiltered ? 0.5 : 1 }}>-</span>;
            }
        },
        {
            key: 'examples',
            header: 'Examples',
            width: columnWidths.examples,
            render: (item: any) => {
                if (item.type === 'main') {
                    return <span className="text-gray-500 text-sm">{item.main.examples.join(', ')}</span>;
                }
                const isMainFiltered = filteredStatus[item.main.text] || false;
                return <span className="text-gray-400 text-sm" style={{ opacity: isMainFiltered ? 0.5 : 1 }}>-</span>;
            }
        }
    ], [columnWidths, onBrushFilter, onComponentFilter, filteredStatus, pendingChanges, onCommentClick, commentLoading]);

    return (
        <div className="brush-table">
            {safeItems.length === 0 ? (
                <div className="border border-gray-200 rounded-lg overflow-hidden">
                    {/* Header */}
                    <div
                        style={{
                            display: 'flex',
                            backgroundColor: '#f9fafb',
                            borderBottom: '2px solid #e5e7eb',
                            fontWeight: 600,
                            fontSize: '14px',
                        }}
                    >
                        {columns.map((column) => (
                            <div
                                key={column.key}
                                style={{
                                    width: columnWidths[column.key as keyof typeof columnWidths],
                                    padding: '12px',
                                }}
                            >
                                {column.header}
                            </div>
                        ))}
                    </div>

                    {/* Empty state message */}
                    <div
                        style={{
                            height: 400,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            backgroundColor: '#f9fafb',
                            color: '#6b7280',
                            fontSize: '14px'
                        }}
                    >
                        No unmatched brushes found for the selected criteria.
                    </div>

                    {/* Footer */}
                    <div className="bg-gray-50 px-4 py-2 text-sm text-gray-600 border-t border-gray-200">
                        Showing 0 of 0 items
                    </div>
                </div>
            ) : (
                <VirtualizedTable
                    data={flattenedData}
                    columns={columns}
                    height={400}
                    rowHeight={48}
                    resizable={true}
                />
            )}
        </div>
    );
};

export default BrushTable; 