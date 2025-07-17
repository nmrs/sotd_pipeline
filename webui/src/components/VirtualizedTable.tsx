import React, { useState, useMemo, useCallback, useRef } from 'react';
import { FixedSizeList as List } from 'react-window';
import AutoSizer from 'react-virtualized-auto-sizer';

interface VirtualizedTableProps<T> {
    data: T[];
    columns: {
        key: string;
        header: string;
        width: number;
        render: (item: T) => React.ReactNode;
    }[];
    height?: number;
    rowHeight?: number;
    onRowClick?: (item: T, index: number) => void;
    selectedRows?: Set<number>;
    onRowSelect?: (index: number, selected: boolean) => void;
    showCheckboxes?: boolean;
    resizable?: boolean;
}

interface RowProps {
    index: number;
    style: React.CSSProperties;
    data: {
        items: any[];
        columns: any[];
        columnWidths: number[];
        rowHeight: number;
        onRowClick?: (item: any, index: number) => void;
        selectedRows?: Set<number>;
        onRowSelect?: (index: number, selected: boolean) => void;
        showCheckboxes?: boolean;
    };
}

const Row: React.FC<RowProps> = ({ index, style, data }) => {
    const { items, columns, columnWidths, onRowClick, selectedRows, onRowSelect, showCheckboxes } = data;
    const item = items[index];
    const isSelected = selectedRows?.has(index) || false;

    const handleRowClick = () => {
        onRowClick?.(item, index);
    };

    const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        e.stopPropagation();
        onRowSelect?.(index, e.target.checked);
    };

    return (
        <div
            style={{
                ...style,
                display: 'flex',
                alignItems: 'center',
                borderBottom: '1px solid #e5e7eb',
                backgroundColor: isSelected ? '#f3f4f6' : 'white',
                cursor: onRowClick ? 'pointer' : 'default',
            }}
            onClick={handleRowClick}
            className="hover:bg-gray-50"
        >
            {showCheckboxes && (
                <div style={{ width: 40, padding: '0 8px' }}>
                    <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={handleCheckboxChange}
                        className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                </div>
            )}
            {columns.map((column, columnIndex) => (
                <div
                    key={column.key}
                    style={{
                        width: columnWidths[columnIndex],
                        padding: '8px 12px',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                    }}
                >
                    {column.render(item)}
                </div>
            ))}
        </div>
    );
};

export function VirtualizedTable<T>({
    data,
    columns,
    height = 400,
    rowHeight = 48,
    onRowClick,
    selectedRows,
    onRowSelect,
    showCheckboxes = false,
    resizable = true,
}: VirtualizedTableProps<T>) {
    const [sortConfig, setSortConfig] = useState<{
        key: string;
        direction: 'asc' | 'desc';
    } | null>(null);

    // State for resizable columns
    const [columnWidths, setColumnWidths] = useState<number[]>(() =>
        columns.map(col => col.width)
    );
    const [isResizing, setIsResizing] = useState(false);
    const [resizeStartX, setResizeStartX] = useState(0);
    const [resizeColumnIndex, setResizeColumnIndex] = useState<number | null>(null);

    // Refs to track current resize state
    const isResizingRef = useRef(false);
    const resizeColumnIndexRef = useRef<number | null>(null);
    const resizeStartXRef = useRef(0);
    const columnWidthsRef = useRef(columnWidths);

    // Update refs when state changes
    React.useEffect(() => {
        isResizingRef.current = isResizing;
        resizeColumnIndexRef.current = resizeColumnIndex;
        resizeStartXRef.current = resizeStartX;
        columnWidthsRef.current = columnWidths;
    }, [isResizing, resizeColumnIndex, resizeStartX, columnWidths]);

    const sortedData = useMemo(() => {
        if (!sortConfig) return data;

        return [...data].sort((a, b) => {
            const aValue = (a as any)[sortConfig.key];
            const bValue = (b as any)[sortConfig.key];

            if (aValue < bValue) {
                return sortConfig.direction === 'asc' ? -1 : 1;
            }
            if (aValue > bValue) {
                return sortConfig.direction === 'asc' ? 1 : -1;
            }
            return 0;
        });
    }, [data, sortConfig]);

    const handleSort = (key: string) => {
        setSortConfig((current) => {
            if (current?.key === key) {
                return {
                    key,
                    direction: current.direction === 'asc' ? 'desc' : 'asc',
                };
            }
            return { key, direction: 'asc' };
        });
    };

    // Resize handlers
    const handleResizeStart = useCallback((e: React.MouseEvent, columnIndex: number) => {
        if (!resizable) return;

        e.preventDefault();
        e.stopPropagation();

        setIsResizing(true);
        setResizeStartX(e.clientX);
        setResizeColumnIndex(columnIndex);

        // Update refs immediately
        isResizingRef.current = true;
        resizeColumnIndexRef.current = columnIndex;
        resizeStartXRef.current = e.clientX;

        // Add global event listeners
        const moveHandler = (e: MouseEvent) => handleResizeMove(e);
        const endHandler = () => handleResizeEnd();

        document.addEventListener('mousemove', moveHandler);
        document.addEventListener('mouseup', endHandler);

        // Store handlers for cleanup
        (window as any).__resizeHandlers = { moveHandler, endHandler };
    }, [resizable]);

    const handleResizeMove = useCallback((e: MouseEvent) => {
        // Use ref values to get current state
        if (!isResizingRef.current || resizeColumnIndexRef.current === null) {
            return;
        }

        const deltaX = e.clientX - resizeStartXRef.current;
        const newWidth = Math.max(50, columnWidthsRef.current[resizeColumnIndexRef.current] + deltaX);

        setColumnWidths(prev => {
            const newWidths = [...prev];
            newWidths[resizeColumnIndexRef.current!] = newWidth;
            return newWidths;
        });

        setResizeStartX(e.clientX);
        resizeStartXRef.current = e.clientX;
    }, []);

    // Add visual feedback during resize
    React.useEffect(() => {
        if (isResizing) {
            document.body.style.userSelect = 'none';
            document.body.style.cursor = 'col-resize';
        } else {
            document.body.style.userSelect = '';
            document.body.style.cursor = '';
        }
    }, [isResizing]);

    const handleResizeEnd = useCallback(() => {
        setIsResizing(false);
        setResizeColumnIndex(null);

        // Update refs
        isResizingRef.current = false;
        resizeColumnIndexRef.current = null;

        // Reset cursor
        document.body.style.cursor = 'default';

        // Remove global event listeners using stored handlers
        const handlers = (window as any).__resizeHandlers;
        if (handlers) {
            document.removeEventListener('mousemove', handlers.moveHandler);
            document.removeEventListener('mouseup', handlers.endHandler);
            delete (window as any).__resizeHandlers;
        }
    }, []);

    // Cleanup event listeners on unmount
    React.useEffect(() => {
        return () => {
            const handlers = (window as any).__resizeHandlers;
            if (handlers) {
                document.removeEventListener('mousemove', handlers.moveHandler);
                document.removeEventListener('mouseup', handlers.endHandler);
                delete (window as any).__resizeHandlers;
            }
        };
    }, []);

    return (
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
                {showCheckboxes && (
                    <div style={{ width: 40, padding: '8px' }}>
                        <input
                            type="checkbox"
                            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                            onChange={() => {
                                // Handle select all logic
                            }}
                        />
                    </div>
                )}
                {columns.map((column, columnIndex) => (
                    <div
                        key={column.key}
                        style={{
                            width: columnWidths[columnIndex],
                            padding: '12px',
                            cursor: 'pointer',
                            userSelect: 'none',
                            position: 'relative',
                        }}
                        onClick={() => handleSort(column.key)}
                        className="hover:bg-gray-100"
                    >
                        <div className="flex items-center justify-between">
                            {column.header}
                            {sortConfig?.key === column.key && (
                                <span className="ml-1">
                                    {sortConfig.direction === 'asc' ? '↑' : '↓'}
                                </span>
                            )}
                        </div>

                        {/* Resize handle */}
                        {resizable && (
                            <div
                                style={{
                                    position: 'absolute',
                                    right: -2,
                                    top: 0,
                                    bottom: 0,
                                    width: 8,
                                    cursor: 'col-resize',
                                    backgroundColor: isResizing && resizeColumnIndex === columnIndex
                                        ? '#3b82f6'
                                        : 'transparent',
                                    zIndex: 10,
                                }}
                                onMouseDown={(e) => handleResizeStart(e, columnIndex)}
                                onMouseEnter={() => {
                                    if (!isResizing) {
                                        document.body.style.cursor = 'col-resize';
                                    }
                                }}
                                onMouseLeave={() => {
                                    if (!isResizing) {
                                        document.body.style.cursor = 'default';
                                    }
                                }}
                                className="hover:bg-blue-300"
                            />
                        )}
                    </div>
                ))}
            </div>

            {/* Virtualized List */}
            <div style={{ height }}>
                <AutoSizer>
                    {({ height: autoHeight, width }: { height: number; width: number }) => (
                        <List
                            height={autoHeight}
                            itemCount={sortedData.length}
                            itemSize={rowHeight}
                            width={width}
                            itemData={{
                                items: sortedData,
                                columns,
                                columnWidths,
                                rowHeight,
                                onRowClick,
                                selectedRows,
                                onRowSelect,
                                showCheckboxes,
                            }}
                        >
                            {Row}
                        </List>
                    )}
                </AutoSizer>
            </div>

            {/* Footer with count */}
            <div className="bg-gray-50 px-4 py-2 text-sm text-gray-600 border-t border-gray-200">
                Showing {sortedData.length} of {data.length} items
            </div>
        </div>
    );
}

export default VirtualizedTable; 