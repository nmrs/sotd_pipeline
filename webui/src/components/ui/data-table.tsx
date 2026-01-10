'use client';

import * as React from 'react';
import {
  ColumnDef,
  ColumnFiltersState,
  SortingState,
  VisibilityState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
  type Table as TanStackTable,
  type RowSelectionState,
  type Row,
} from '@tanstack/react-table';

import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ChevronDown } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import { SecondaryButton } from '@/components/ui/reusable-buttons';
import { Checkbox } from '@/components/ui/checkbox';

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
  searchKey?: string;
  showColumnVisibility?: boolean;
  showPagination?: boolean;
  showCsvDownload?: boolean;
  resizable?: boolean;
  sortable?: boolean;
  onColumnResize?: (columnId: string, width: number) => void;
  customControls?: React.ReactNode;
  onSelectionChange?: (selectedRows: TData[]) => void;
  onVisibleRowsChange?: (visibleRows: TData[]) => void;
  clearSelection?: boolean;
  initialRowSelection?: Record<string, boolean>;
  initialPageSize?: number;
  sorting?: SortingState;
  onSortingChange?: (sorting: SortingState) => void;
  enableRowClickSelection?: boolean;
  activeRowIndex?: number;
  keyboardNavigationEnabled?: boolean;
  externalRowSelection?: Record<string, boolean>;
  field?: string; // For generating row keys
  totalCount?: number; // Total count from backend for external pagination
}

export function DataTable<TData, TValue>({
  columns,
  data,
  showColumnVisibility = true,
  showPagination = false,
  showCsvDownload = true,
  resizable = false,
  sortable = true,
  onColumnResize,
  customControls,
  onSelectionChange,
  onVisibleRowsChange,
  clearSelection = false,
  initialRowSelection = {},
  initialPageSize = 10,
  sorting: externalSorting,
  onSortingChange,
  enableRowClickSelection = false,
  activeRowIndex = -1,
  keyboardNavigationEnabled = false,
  externalRowSelection,
  totalCount,
  field,
}: DataTableProps<TData, TValue>) {
  const [internalSorting, setInternalSorting] = useState<SortingState>([]);
  // Simple search - no column selection needed


  // Use external sorting if provided, otherwise use internal
  const sorting = externalSorting !== undefined ? externalSorting : internalSorting;

  // Simple search - no column selection needed
  const setSorting = onSortingChange || setInternalSorting;

  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({});
  const [rowSelection, setRowSelection] = useState<RowSelectionState>(initialRowSelection);
  const [columnWidths, setColumnWidths] = useState<Record<string, number>>({});
  const [isResizing, setIsResizing] = useState(false);
  const [resizeColumn, setResizeColumn] = useState<string | null>(null);
  const [useRegexMode, setUseRegexMode] = useState<boolean>(false);
  const [regexError, setRegexError] = useState<string | null>(null);
  const tableRef = React.useRef<HTMLDivElement>(null);

  // Use external row selection if provided, otherwise use internal
  const effectiveRowSelection =
    externalRowSelection !== undefined ? externalRowSelection : rowSelection;
  const setEffectiveRowSelection =
    externalRowSelection !== undefined
      ? (updater: RowSelectionState | ((prev: RowSelectionState) => RowSelectionState)) => {
        // When using external selection, we need to call onSelectionChange directly
        // since the table's internal state won't be updated
        const newSelection =
          typeof updater === 'function' ? updater(effectiveRowSelection) : updater;
        if (onSelectionChange) {
          const selectedRows = data.filter((_, index) => newSelection[index.toString()]);
          onSelectionChange(selectedRows);
        }
        // Also update the internal state so the UI reflects the change immediately
        setRowSelection(newSelection);
      }
      : setRowSelection;

  const table = useReactTable({
    data,
    columns,
    onSortingChange: updater => {
      const newSorting = typeof updater === 'function' ? updater(sorting) : updater;
      setSorting(newSorting);
    },
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onColumnVisibilityChange: setColumnVisibility,
    onRowSelectionChange: setEffectiveRowSelection,
    enableRowSelection: true,
    enableSorting: sortable,
    enableColumnFilters: true,
    enableColumnResizing: resizable,
    enableMultiSort: true,
    enableSortingRemoval: true,
    enableGlobalFilter: true,
    globalFilterFn: (row, _columnId, filterValue) => {
      const searchTerm = filterValue as string;
      const rowData = row.original as Record<string, unknown>;

      // If search is empty, show all rows
      if (!searchTerm || searchTerm.trim() === '') {
        return true;
      }

      // Regex mode
      if (useRegexMode) {
        try {
          // Make regex case-insensitive by default (add 'i' flag) to match user expectations
          const regex = new RegExp(searchTerm, 'i');
          
          // Search in the most important string fields
          const searchableFields = ['original', 'matched_string', 'brand', 'model', 'match_type', 'mismatch_type'];
          
          for (const field of searchableFields) {
            const value = rowData[field];
            if (value && typeof value === 'string' && regex.test(value)) {
              return true;
            }
          }

          // Search in matched object if it exists
          if (rowData.matched && typeof rowData.matched === 'object') {
            const matched = rowData.matched as Record<string, unknown>;
            for (const [key, value] of Object.entries(matched)) {
              if (value && typeof value === 'string' && regex.test(value)) {
                return true;
              }
            }
          }

          return false;
        } catch (error) {
          // Invalid regex - return false to show no matches
          return false;
        }
      }

      // Normal text search (case-insensitive substring matching)
      const searchTermLower = searchTerm.toLowerCase();
      const searchableFields = ['original', 'matched_string', 'brand', 'model', 'match_type', 'mismatch_type'];
      
      for (const field of searchableFields) {
        const value = rowData[field];
        if (value && typeof value === 'string' && value.toLowerCase().includes(searchTermLower)) {
          return true;
        }
      }

      // Search in matched object if it exists
      if (rowData.matched && typeof rowData.matched === 'object') {
        const matched = rowData.matched as Record<string, unknown>;
        for (const [key, value] of Object.entries(matched)) {
          if (value && typeof value === 'string' && value.toLowerCase().includes(searchTermLower)) {
            return true;
          }
        }
      }

      return false;
    },
    state: {
      sorting,
      columnFilters,
      columnVisibility,
      rowSelection: effectiveRowSelection,
    },
    initialState: {
      pagination: {
        pageSize: initialPageSize,
      },
      rowSelection: initialRowSelection,
    },
  });

  const { rows } = table.getRowModel();

  // Call onSelectionChange when row selection changes
  React.useEffect(() => {
    if (onSelectionChange) {
      const selectedRows = rows.filter(row => row.getIsSelected()).map(row => row.original);
      onSelectionChange(selectedRows);
    }
  }, [rowSelection, rows, onSelectionChange]);

  // Call onVisibleRowsChange when visible rows change (pagination, filtering, sorting)
  React.useEffect(() => {
    if (onVisibleRowsChange) {
      const visibleRows = rows.map(row => row.original);
      onVisibleRowsChange(visibleRows);
    }
  }, [rows, onVisibleRowsChange]);

  // Clear selection when clearSelection prop is true
  React.useEffect(() => {
    if (clearSelection) {
      setRowSelection({});
    }
  }, [clearSelection]);

  // Update row selection when initialRowSelection changes
  React.useEffect(() => {
    const hasInitialSelection = initialRowSelection && Object.keys(initialRowSelection).length > 0;
    if (hasInitialSelection) {
      setRowSelection(initialRowSelection);
    }
  }, [initialRowSelection]);

  // Update row selection when externalRowSelection changes
  React.useEffect(() => {
    if (externalRowSelection !== undefined) {
      setRowSelection(externalRowSelection);
    }
  }, [externalRowSelection]);

  // Scroll to active row when it changes
  React.useEffect(() => {
    if (keyboardNavigationEnabled && activeRowIndex >= 0 && tableRef.current) {
      // Get the active row by index
      const activeRow = rows[activeRowIndex];

      if (activeRow) {
        // Scroll the row into view
        const rowElement = tableRef.current.querySelector(`[data-row-id="${activeRow.id}"]`);
        if (rowElement) {
          rowElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }
    }
  }, [keyboardNavigationEnabled, activeRowIndex, rows]);

  // Column resizing handlers
  const handleMouseDown = (columnId: string, e: React.MouseEvent) => {
    if (!resizable) return;

    setIsResizing(true);
    setResizeColumn(columnId);
    e.preventDefault();
  };

  const handleMouseMove = React.useCallback(
    (e: MouseEvent) => {
      if (!isResizing || !resizeColumn) return;

      // Calculate the new width based on the mouse position
      // Use a simpler approach - calculate relative to the viewport
      const newWidth = Math.max(50, e.clientX - 50); // Minimum width of 50px

      setColumnWidths(prev => ({ ...prev, [resizeColumn]: newWidth }));
      onColumnResize?.(resizeColumn, newWidth);
    },
    [isResizing, resizeColumn, onColumnResize]
  );

  const handleMouseUp = React.useCallback(() => {
    setIsResizing(false);
    setResizeColumn(null);
  }, []);

  // Row click handler for selection
  const handleRowClick = React.useCallback(
    (row: Row<TData>, event: React.MouseEvent) => {
      if (!enableRowClickSelection) return;

      // Check if the click target is an interactive element
      const target = event.target as HTMLElement;
      const isInteractive = target.closest(
        'button, a, input[type="checkbox"], input[type="radio"], select, textarea, [role="button"], [tabindex]'
      );

      if (isInteractive) {
        return; // Don't toggle selection for interactive elements
      }

      // Toggle row selection
      row.toggleSelected(!row.getIsSelected());
    },
    [enableRowClickSelection]
  );

  React.useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isResizing, handleMouseMove, handleMouseUp]);

  // CSV export helper functions
  const generateCSV = (rows: Row<TData>[], columns: ColumnDef<TData, TValue>[]) => {
    // Get visible columns only
    const visibleColumns = columns.filter(col => {
      const columnId = col.id || (col as any).accessorKey;
      return columnId && table.getColumn(columnId)?.getIsVisible() !== false;
    });

    // Generate header row
    const headers = visibleColumns.map(col => {
      const columnId = col.id || (col as any).accessorKey;
      const header = col.header;
      return typeof header === 'string' ? header : columnId;
    });

    // Generate data rows
    const dataRows = rows.map(row => {
      return visibleColumns.map(col => {
        const columnId = col.id || (col as any).accessorKey;
        if (!columnId) return '';

        const cellValue = row.getValue(columnId);
        // Convert cell value to string, handling null/undefined
        if (cellValue == null) return '';
        if (typeof cellValue === 'object') {
          // For complex objects, try to get a meaningful string representation
          if (cellValue.hasOwnProperty('toString')) {
            return cellValue.toString();
          }
          return JSON.stringify(cellValue);
        }
        return String(cellValue);
      });
    });

    // Combine headers and data
    const csvRows = [headers, ...dataRows];

    // Convert to CSV format (handle commas and quotes properly)
    return csvRows
      .map(row =>
        row
          .map(cell => {
            const cellStr = String(cell);
            // If cell contains comma, quote, or newline, wrap in quotes and escape internal quotes
            if (cellStr.includes(',') || cellStr.includes('"') || cellStr.includes('\n')) {
              return `"${cellStr.replace(/"/g, '""')}"`;
            }
            return cellStr;
          })
          .join(',')
      )
      .join('\n');
  };

  const downloadCSV = (csvContent: string, filename: string) => {
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Validate regex pattern and update error state
  const validateRegex = (pattern: string): boolean => {
    if (!useRegexMode || !pattern || pattern.trim() === '') {
      setRegexError(null);
      return true;
    }

    try {
      new RegExp(pattern);
      setRegexError(null);
      return true;
    } catch (error) {
      setRegexError('Invalid regex pattern');
      return false;
    }
  };

  // Handle search input change
  const handleSearchChange = (value: string) => {
    table.setGlobalFilter(value);
    if (useRegexMode) {
      validateRegex(value);
    } else {
      setRegexError(null);
    }
  };

  // Handle regex mode toggle
  const handleRegexModeToggle = (checked: boolean) => {
    setUseRegexMode(checked);
    const currentFilter = (table.getState().globalFilter as string) ?? '';
    if (checked) {
      validateRegex(currentFilter);
    } else {
      setRegexError(null);
    }
  };

  return (
    <div className='w-full space-y-4'>
      <div className='flex items-center py-4 gap-2'>
        <div className='flex items-center gap-2 flex-1'>
          <Input
            placeholder={useRegexMode ? 'Enter regex pattern...' : 'Search all columns...'}
            value={(table.getState().globalFilter as string) ?? ''}
            onChange={event => handleSearchChange(event.target.value)}
            className={`max-w-sm ${regexError ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}`}
          />
          <div className='flex items-center gap-2'>
            <Checkbox
              id='regex-mode'
              checked={useRegexMode}
              onCheckedChange={handleRegexModeToggle}
              className='h-4 w-4'
            />
            <label
              htmlFor='regex-mode'
              className='text-sm text-gray-700 cursor-pointer'
              title='Enable regex pattern matching'
            >
              Regex
            </label>
          </div>
          {regexError && (
            <span className='text-sm text-red-600' title={regexError}>
              Invalid regex
            </span>
          )}
        </div>


        {customControls}
        {showColumnVisibility && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant='outline' className='ml-auto'>
                Columns <ChevronDown className='ml-2 h-4 w-4' />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align='end'>
              {table
                .getAllColumns()
                .filter(column => column.getCanHide())
                .map(column => {
                  return (
                    <DropdownMenuCheckboxItem
                      key={column.id}
                      className='capitalize'
                      checked={column.getIsVisible()}
                      onCheckedChange={value => column.toggleVisibility(!!value)}
                    >
                      {column.id}
                    </DropdownMenuCheckboxItem>
                  );
                })}
            </DropdownMenuContent>
          </DropdownMenu>
        )}

        {showCsvDownload && (
          <Button
            variant='outline'
            onClick={() => {
              const csvContent = generateCSV(table.getFilteredRowModel().rows, columns);
              const filename = field ? `${field}-data.csv` : 'table-data.csv';
              downloadCSV(csvContent, filename);
            }}
            className='ml-2'
            title='Download data as CSV'
          >
            📥 CSV
          </Button>
        )}
      </div>
      <div ref={tableRef} className='rounded-md border overflow-x-auto max-w-full'>
        <Table data-table>
          <TableHeader>
            {table.getHeaderGroups().map(headerGroup => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map(header => {
                  return (
                    <TableHead
                      key={header.id}
                      className='relative'
                      style={
                        columnWidths[header.column.id]
                          ? { width: columnWidths[header.column.id] }
                          : undefined
                      }
                    >
                      {header.isPlaceholder ? null : (
                        <div className='flex items-center justify-between'>
                          {sortable ? (
                            <button
                              className={`flex items-center gap-1 hover:text-blue-600 transition-colors ${header.column.getCanSort() ? 'cursor-pointer' : 'cursor-default'
                                }`}
                              onClick={header.column.getToggleSortingHandler()}
                              disabled={!header.column.getCanSort()}
                            >
                              {flexRender(header.column.columnDef.header, header.getContext())}
                              {header.column.getCanSort() && (
                                <span className='ml-1'>
                                  {{
                                    asc: '↑',
                                    desc: '↓',
                                  }[header.column.getIsSorted() as string] ?? '↕'}
                                </span>
                              )}
                            </button>
                          ) : (
                            <div className='flex items-center gap-1'>
                              {flexRender(header.column.columnDef.header, header.getContext())}
                            </div>
                          )}
                          {resizable && (
                            <div
                              className='absolute right-0 top-0 h-full w-2 cursor-col-resize bg-transparent hover:bg-gray-300 z-20'
                              onMouseDown={e => handleMouseDown(header.column.id, e)}
                              style={{ touchAction: 'none' }}
                            />
                          )}
                        </div>
                      )}
                    </TableHead>
                  );
                })}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {rows.length ? (
              rows.map((row, index) => {
                return (
                  <TableRow
                    key={row.id}
                    data-row-id={row.id}
                    data-state={row.getIsSelected() && 'selected'}
                    onClick={enableRowClickSelection ? e => handleRowClick(row, e) : undefined}
                    className={`${enableRowClickSelection ? 'cursor-pointer hover:bg-gray-50' : ''} ${keyboardNavigationEnabled && activeRowIndex === index
                      ? 'bg-blue-50 border-l-4 border-l-blue-500'
                      : ''
                      }`}
                  >
                    {row.getVisibleCells().map(cell => (
                      <TableCell
                        key={cell.id}
                        style={
                          columnWidths[cell.column.id]
                            ? { width: columnWidths[cell.column.id] }
                            : undefined
                        }
                      >
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </TableCell>
                    ))}
                  </TableRow>
                );
              })
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length} className='h-24 text-center'>
                  No results.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      {showPagination && <DataTablePagination table={table} totalCount={totalCount} />}
    </div>
  );
}

interface DataTablePaginationProps<TData> {
  table: TanStackTable<TData>;
  totalCount?: number; // Total count from backend for external pagination
}

export function DataTablePagination<TData>({ table, totalCount }: DataTablePaginationProps<TData>) {
  return (
    <div className='flex items-center justify-between px-2'>
      <div className='flex-1 text-sm text-muted-foreground'>
        {table.getFilteredSelectedRowModel().rows.length} of{' '}
        {table.getFilteredRowModel().rows.length} row(s) selected.
      </div>
      <div className='flex items-center space-x-6 lg:space-x-8'>
        <div className='flex items-center space-x-2'>
          <p className='text-sm font-medium'>Rows per page</p>
          <Select
            value={`${table.getState().pagination.pageSize}`}
            onValueChange={value => {
              table.setPageSize(Number(value));
            }}
          >
            <SelectTrigger className='h-8 w-[70px]'>
              <SelectValue placeholder={table.getState().pagination.pageSize} />
            </SelectTrigger>
            <SelectContent side='top'>
              {[10, 25, 50, 100, 200, 500].map(pageSize => (
                <SelectItem key={pageSize} value={`${pageSize}`}>
                  {pageSize}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className='flex w-[100px] items-center justify-center text-sm font-medium'>
          {`${table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1}-${Math.min((table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize, table.getFilteredRowModel().rows.length)} of ${totalCount !== undefined ? totalCount : table.getFilteredRowModel().rows.length}`}
        </div>
        <div className='flex items-center space-x-2'>
          <Button
            variant='outline'
            className='hidden h-8 w-8 p-0 lg:flex'
            onClick={() => {
              table.setPageIndex(0);
            }}
            disabled={!table.getCanPreviousPage()}
          >
            <span className='sr-only'>Go to first page</span>
            <ChevronsLeft className='h-4 w-4' />
          </Button>
          <Button
            variant='outline'
            className='h-8 w-8 p-0'
            onClick={() => {
              table.previousPage();
            }}
            disabled={!table.getCanPreviousPage()}
          >
            <span className='sr-only'>Go to previous page</span>
            <ChevronLeft className='h-4 w-4' />
          </Button>
          <Button
            variant='outline'
            className='h-8 w-8 p-0'
            onClick={() => {
              table.nextPage();
            }}
            disabled={!table.getCanNextPage()}
          >
            <span className='sr-only'>Go to next page</span>
            <ChevronRight className='h-4 w-4' />
          </Button>
          <Button
            variant='outline'
            className='hidden h-8 w-8 p-0 lg:flex'
            onClick={() => {
              table.setPageIndex(table.getPageCount() - 1);
            }}
            disabled={!table.getCanNextPage()}
          >
            <span className='sr-only'>Go to last page</span>
            <ChevronsRight className='h-4 w-4' />
          </Button>
        </div>
      </div>
    </div>
  );
}
