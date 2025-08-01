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
import { useState } from 'react';

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
}

export function DataTable<TData, TValue>({
  columns,
  data,
  searchKey,
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
}: DataTableProps<TData, TValue>) {
  const [internalSorting, setInternalSorting] = useState<SortingState>([]);

  // Use external sorting if provided, otherwise use internal
  const sorting = externalSorting !== undefined ? externalSorting : internalSorting;
  const setSorting = onSortingChange || setInternalSorting;
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({});
  const [rowSelection, setRowSelection] = useState<RowSelectionState>(initialRowSelection);
  const [columnWidths, setColumnWidths] = useState<Record<string, number>>({});
  const [isResizing, setIsResizing] = useState(false);
  const [resizeColumn, setResizeColumn] = useState<string | null>(null);

  const table = useReactTable({
    data,
    columns,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onColumnVisibilityChange: setColumnVisibility,
    onRowSelectionChange: setRowSelection,
    initialState: {
      pagination: {
        pageSize: initialPageSize,
      },
    },
    state: {
      sorting,
      columnFilters,
      columnVisibility,
      rowSelection,
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
          placeholder={`Filter ${searchKey}...`}
          value={(table.getColumn(searchKey || '')?.getFilterValue() as string) ?? ''}
          onChange={event => table.getColumn(searchKey || '')?.setFilterValue(event.target.value)}
          className='max-w-sm'
        />
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
      <div className='rounded-md border overflow-x-auto'>
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
              rows.map(row => (
                <TableRow key={row.id} data-state={row.getIsSelected() && 'selected'}>
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
              ))
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
      {showPagination && <DataTablePagination table={table} />}
    </div>
  );
}

interface DataTablePaginationProps<TData> {
  table: TanStackTable<TData>;
}

export function DataTablePagination<TData>({ table }: DataTablePaginationProps<TData>) {
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
          {`${table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1}-${Math.min((table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize, table.getFilteredRowModel().rows.length)} of ${table.getFilteredRowModel().rows.length}`}
        </div>
        <div className='flex items-center space-x-2'>
          <Button
            variant='outline'
            className='hidden h-8 w-8 p-0 lg:flex'
            onClick={() => table.setPageIndex(0)}
            disabled={!table.getCanPreviousPage()}
          >
            <span className='sr-only'>Go to first page</span>
            <ChevronsLeft className='h-4 w-4' />
          </Button>
          <Button
            variant='outline'
            className='h-8 w-8 p-0'
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            <span className='sr-only'>Go to previous page</span>
            <ChevronLeft className='h-4 w-4' />
          </Button>
          <Button
            variant='outline'
            className='h-8 w-8 p-0'
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            <span className='sr-only'>Go to next page</span>
            <ChevronRight className='h-4 w-4' />
          </Button>
          <Button
            variant='outline'
            className='hidden h-8 w-8 p-0 lg:flex'
            onClick={() => table.setPageIndex(table.getPageCount() - 1)}
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
