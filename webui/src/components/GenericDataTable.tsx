import React from 'react';

export interface DataTableColumn<T = any> {
    key: string;
    header: string;
    width?: number;
    render?: (value: any, row: T) => React.ReactNode;
}

export interface GenericDataTableProps<T = any> {
    data: T[];
    columns: DataTableColumn<T>[];
    onRowClick?: (row: T) => void;
    onSort?: (column: string) => void;
    sortColumn?: string;
    sortDirection?: 'asc' | 'desc';
    emptyMessage?: string;
    loading?: boolean;
    testId?: string;
    className?: string;
}

export function GenericDataTable<T = any>({
    data,
    columns,
    onRowClick,
    onSort,
    sortColumn,
    sortDirection,
    emptyMessage = 'No data available',
    loading = false,
    testId = 'generic-data-table',
    className = ''
}: GenericDataTableProps<T>) {
    return (
        <div data-testid={testId} className={className}>
            <table className="w-full border-collapse">
                <thead>
                    <tr>
                        {columns.map(column => (
                            <th
                                key={column.key}
                                onClick={() => onSort?.(column.key)}
                                style={{
                                    cursor: onSort ? 'pointer' : 'default',
                                    width: column.width,
                                    userSelect: 'none'
                                }}
                                className="border-b border-gray-200 px-4 py-2 text-left font-medium text-gray-700 bg-gray-50"
                            >
                                <div className="flex items-center justify-between">
                                    <span>{column.header}</span>
                                    {sortColumn === column.key && (
                                        <span className="ml-1 text-gray-500">
                                            {sortDirection === 'asc' ? '↑' : '↓'}
                                        </span>
                                    )}
                                </div>
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {loading ? (
                        <tr>
                            <td
                                colSpan={columns.length}
                                className="px-4 py-8 text-center text-gray-500"
                            >
                                Loading...
                            </td>
                        </tr>
                    ) : data.length === 0 ? (
                        <tr>
                            <td
                                colSpan={columns.length}
                                className="px-4 py-8 text-center text-gray-500"
                            >
                                {emptyMessage}
                            </td>
                        </tr>
                    ) : (
                        data.map((row, index) => (
                            <tr
                                key={index}
                                onClick={() => onRowClick?.(row)}
                                style={{ cursor: onRowClick ? 'pointer' : 'default' }}
                                className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
                            >
                                {columns.map(column => (
                                    <td
                                        key={column.key}
                                        className="px-4 py-2"
                                        style={{ width: column.width }}
                                    >
                                        {column.render
                                            ? column.render(row[column.key as keyof T], row)
                                            : String(row[column.key as keyof T] || '')
                                        }
                                    </td>
                                ))}
                            </tr>
                        ))
                    )}
                </tbody>
            </table>
        </div>
    );
} 