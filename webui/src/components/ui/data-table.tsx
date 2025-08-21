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
}: DataTableProps<TData, TValue>) {
  const [internalSorting, setInternalSorting] = useState<SortingState>([]);
  const [selectedSearchColumns, setSelectedSearchColumns] = useState<Set<string>>(
    new Set(['original', 'mismatch_type', 'match_type', 'pattern'])
  );
  const [isColumnDropdownOpen, setIsColumnDropdownOpen] = useState(false);
  const columnDropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (columnDropdownRef.current && !columnDropdownRef.current.contains(event.target as Node)) {
        setIsColumnDropdownOpen(false);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isColumnDropdownOpen) {
        setIsColumnDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isColumnDropdownOpen]);

  // Use external sorting if provided, otherwise use internal
  const sorting = externalSorting !== undefined ? externalSorting : internalSorting;

  // Column selection helpers
  const selectAllColumns = () => {
    const allColumnIds = columns.map(col => col.id || (col as any).accessorKey).filter(Boolean);
    setSelectedSearchColumns(new Set(allColumnIds));
  };

  const clearAllColumns = () => {
    setSelectedSearchColumns(new Set());
  };

  const getColumnDisplayText = () => {
    if (selectedSearchColumns.size === 0) return 'No columns';
    if (selectedSearchColumns.size === 1) return '1 column';
    return `${selectedSearchColumns.size} columns`;
  };
  const setSorting = onSortingChange || setInternalSorting;

  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({});
  const [rowSelection, setRowSelection] = useState<RowSelectionState>(initialRowSelection);
  const [columnWidths, setColumnWidths] = useState<Record<string, number>>({});
  const [isResizing, setIsResizing] = useState(false);
  const [resizeColumn, setResizeColumn] = useState<string | null>(null);
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
      const searchTerm = filterValue.toLowerCase();
      const rowData = row.original as Record<string, unknown>;

      // Only search in selected columns
      for (const [key, value] of Object.entries(rowData)) {
        // Skip if this column is not selected for search
        if (!selectedSearchColumns.has(key)) continue;

        if (typeof value === 'string' && value.toLowerCase().includes(searchTerm)) {
          return true;
        }
        if (typeof value === 'number' && value.toString().includes(searchTerm)) {
          return true;
        }
        if (Array.isArray(value) && value.some(v => String(v).toLowerCase().includes(searchTerm))) {
          return true;
        }
        if (value && typeof value === 'object') {
          // Search in nested objects (like matched data)
          for (const [_nestedKey, nestedValue] of Object.entries(
            value as Record<string, unknown>
          )) {
            if (String(nestedValue).toLowerCase().includes(searchTerm)) {
              return true;
            }
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

  return (
    <div className='w-full space-y-4'>
      <div className='flex items-center py-4'>
        <Input
          placeholder='Search all columns...'
          value={(table.getState().globalFilter as string) ?? ''}
          onChange={event => table.setGlobalFilter(event.target.value)}
          className='max-w-sm'
        />

        {/* Column Selection Dropdown */}
        <div className='relative ml-2' ref={columnDropdownRef}>
          <SecondaryButton
            onClick={() => setIsColumnDropdownOpen(!isColumnDropdownOpen)}
            className='min-w-[160px] justify-between'
          >
            <span className='truncate'>{getColumnDisplayText()}</span>
            <svg
              className={`w-4 h-4 ml-2 transition-transform ${isColumnDropdownOpen ? 'rotate-180' : ''}`}
              fill='none'
              stroke='currentColor'
              viewBox='0 0 24 24'
            >
              <path
                strokeLinecap='round'
                strokeLinejoin='round'
                strokeWidth={2}
                d='M19 9l-7 7-7-7'
              />
            </svg>
          </SecondaryButton>

          {isColumnDropdownOpen && (
            <div className='absolute top-full left-0 mt-1 bg-white border border-gray-300 rounded-md shadow-lg z-50 max-h-60 overflow-y-auto min-w-[300px]'>
              <div className='p-2'>
                <div className='flex items-center gap-2 mb-2 pb-2 border-b border-gray-200'>
                  <SecondaryButton onClick={selectAllColumns} className='text-xs'>
                    Select All
                  </SecondaryButton>
                  <SecondaryButton onClick={clearAllColumns} className='text-xs'>
                    Clear All
                  </SecondaryButton>
                </div>

                <div className='space-y-1'>
                  {columns.map(column => {
                    const columnId = column.id || ((column as any).accessorKey as string);
                    if (!columnId) return null;

                    const isSelected = selectedSearchColumns.has(columnId);
                    const columnName = column.header
                      ? typeof column.header === 'string'
                        ? column.header
                        : columnId
                      : columnId;

                    return (
                      <label
                        key={columnId}
                        className='flex items-center space-x-2 py-1 hover:bg-gray-50 rounded px-1 cursor-pointer'
                      >
                        <Checkbox
                          checked={isSelected}
                          onCheckedChange={checked => {
                            setSelectedSearchColumns(prev => {
                              const newSet = new Set(prev);
                              if (checked) {
                                newSet.add(columnId);
                              } else {
                                newSet.delete(columnId);
                              }
                              return newSet;
                            });
                          }}
                        />
                        <span className='text-sm text-gray-700'>{columnName}</span>
                      </label>
                    );
                  })}
                </div>
              </div>
            </div>
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
                              className={`flex items-center gap-1 hover:text-blue-600 transition-colors ${
                                header.column.getCanSort() ? 'cursor-pointer' : 'cursor-default'
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
                    className={`${enableRowClickSelection ? 'cursor-pointer hover:bg-gray-50' : ''} ${
                      keyboardNavigationEnabled && activeRowIndex === index
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
