import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react';

export interface DataTableColumn<T = unknown> {
  key: string;
  header: string;
  width?: number;
  render?: (value: unknown, row: T) => React.ReactNode;
}

export interface GenericDataTableProps<T = unknown> {
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
  maxHeight?: string;
  enablePerformanceLogging?: boolean;
}

export function GenericDataTableOptimized<T = unknown>({
  data,
  columns,
  onRowClick,
  onSort,
  sortColumn,
  sortDirection,
  emptyMessage = 'No data available',
  loading = false,
  testId = 'generic-data-table-optimized',
  className = '',
  maxHeight = 'calc(100vh - 200px)',
  enablePerformanceLogging = false,
}: GenericDataTableProps<T>) {
  const [columnWidths, setColumnWidths] = useState<Record<string, number>>({});
  const [isResizing, setIsResizing] = useState<string | null>(null);
  const [startX, setStartX] = useState(0);
  const [startWidth, setStartWidth] = useState(0);
  const tableRef = useRef<HTMLDivElement>(null);
  const resizeStartTime = useRef<number>(0);
  const resizeCount = useRef<number>(0);

  // Memoized column width calculation
  const memoizedColumnWidths = useMemo(() => {
    const start = performance.now();
    const widths: Record<string, number> = {};
    columns.forEach(col => {
      widths[col.key] = columnWidths[col.key] || col.width || 150;
    });
    const end = performance.now();
    if (enablePerformanceLogging && end - start > 1) {
      console.log(`[OPTIMIZED] Column width calculation took ${end - start}ms`);
    }
    return widths;
  }, [columns, columnWidths, enablePerformanceLogging]);

  // Memoized sorting
  const sortedData = useMemo(() => {
    if (!sortColumn || !sortDirection) return data;

    const start = performance.now();
    const result = [...data].sort((a, b) => {
      const aVal = (a as Record<string, unknown>)[sortColumn];
      const bVal = (b as Record<string, unknown>)[sortColumn];

      if (aVal === bVal) return 0;
      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;

      const comparison = aVal < bVal ? -1 : 1;
      return sortDirection === 'asc' ? comparison : -comparison;
    });
    const end = performance.now();
    if (enablePerformanceLogging && end - start > 5) {
      console.log(`[OPTIMIZED] Sorting ${data.length} items took ${end - start}ms`);
    }
    return result;
  }, [data, sortColumn, sortDirection, enablePerformanceLogging]);

  // Memoized event handlers
  const handleHeaderClick = useCallback(
    (columnKey: string) => {
      if (onSort) {
        onSort(columnKey);
      }
    },
    [onSort]
  );

  const handleRowClick = useCallback(
    (row: T) => {
      if (onRowClick) {
        onRowClick(row);
      }
    },
    [onRowClick]
  );

  const handleResizeStart = useCallback(
    (e: React.MouseEvent, columnKey: string) => {
      e.preventDefault();
      const start = performance.now();
      resizeStartTime.current = start;
      resizeCount.current = 0;

      setIsResizing(columnKey);
      setStartX(e.clientX);
      setStartWidth(memoizedColumnWidths[columnKey]);

      if (enablePerformanceLogging) {
        console.log(`[OPTIMIZED] Resize start: ${columnKey}`);
      }
    },
    [memoizedColumnWidths, enablePerformanceLogging]
  );

  const handleResizeMove = useCallback(
    (e: MouseEvent) => {
      if (!isResizing) return;

      resizeCount.current++;
      const deltaX = e.clientX - startX;
      const newWidth = Math.max(50, startWidth + deltaX);

      // Measure resize performance
      const start = performance.now();
      setColumnWidths(prev => ({
        ...prev,
        [isResizing]: newWidth,
      }));
      const end = performance.now();

      // Log every 10th resize operation to avoid spam
      if (enablePerformanceLogging && resizeCount.current % 10 === 0) {
        console.log(`[OPTIMIZED] Resize operation ${resizeCount.current}: ${end - start}ms`);
      }
    },
    [isResizing, startX, startWidth, enablePerformanceLogging]
  );

  const handleResizeEnd = useCallback(() => {
    const totalTime = performance.now() - resizeStartTime.current;
    if (enablePerformanceLogging) {
      console.log(
        `[OPTIMIZED] Resize complete: ${totalTime}ms total, ${resizeCount.current} operations`
      );
    }
    setIsResizing(null);
  }, [enablePerformanceLogging]);

  useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', handleResizeMove);
      document.addEventListener('mouseup', handleResizeEnd);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';

      return () => {
        document.removeEventListener('mousemove', handleResizeMove);
        document.removeEventListener('mouseup', handleResizeEnd);
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
      };
    }
  }, [isResizing, handleResizeMove, handleResizeEnd]);

  // Memoized styles
  const tableStyles = useMemo(
    () => ({
      height: maxHeight,
      overflowY: 'auto' as const,
    }),
    [maxHeight]
  );

  const headerStyles = useMemo(
    () => ({
      position: 'sticky' as const,
      top: 0,
      zIndex: 10,
      backgroundColor: 'white',
    }),
    []
  );

  if (loading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`} data-testid={testId}>
        <div className='text-gray-500'>Loading...</div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`} data-testid={testId}>
        <div className='text-gray-500'>{emptyMessage}</div>
      </div>
    );
  }

  return (
    <div className={`border rounded-lg ${className}`} data-testid={testId} ref={tableRef}>
      <div style={tableStyles}>
        <table className='w-full border-collapse'>
          <thead style={headerStyles}>
            <tr className='border-b'>
              {columns.map((column, index) => (
                <th
                  key={column.key}
                  className='p-3 text-left font-medium text-gray-900 bg-gray-50 border-r last:border-r-0 relative'
                  style={{ width: memoizedColumnWidths[column.key] }}
                >
                  <div className='flex items-center justify-between'>
                    <button
                      className='flex-1 text-left hover:text-blue-600 transition-colors'
                      onClick={() => handleHeaderClick(column.key)}
                    >
                      {column.header}
                      {sortColumn === column.key && (
                        <span className='ml-1'>{sortDirection === 'asc' ? '↑' : '↓'}</span>
                      )}
                    </button>
                    {index < columns.length - 1 && (
                      <div
                        className='absolute right-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-blue-500'
                        onMouseDown={e => handleResizeStart(e, column.key)}
                      />
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sortedData.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                className={`border-b hover:bg-gray-50 ${onRowClick ? 'cursor-pointer' : ''}`}
                onClick={() => handleRowClick(row)}
              >
                {columns.map(column => (
                  <td
                    key={column.key}
                    className='p-3 border-r last:border-r-0'
                    style={{ width: memoizedColumnWidths[column.key] }}
                  >
                    {column.render
                      ? column.render((row as Record<string, unknown>)[column.key], row)
                      : String((row as Record<string, unknown>)[column.key] || '')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
