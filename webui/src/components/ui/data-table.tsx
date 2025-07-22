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
} from '@tanstack/react-table';
import { FixedSizeList as List } from 'react-window';

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
import { ChevronDown, ArrowUpDown } from 'lucide-react';

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
  height?: number;
  itemSize?: number;
  searchKey?: string;
  showColumnVisibility?: boolean;
  showPagination?: boolean;
  resizable?: boolean;
  onColumnResize?: (columnId: string, width: number) => void;
}

export function DataTable<TData, TValue>({
  columns,
  data,
  height = 400,
  itemSize = 50,
  searchKey,
  showColumnVisibility = true,
  showPagination = false,
  resizable = false,
  onColumnResize,
}: DataTableProps<TData, TValue>) {
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([]);
  const [columnVisibility, setColumnVisibility] = React.useState<VisibilityState>({});
  const [rowSelection, setRowSelection] = React.useState({});
  const [columnWidths, setColumnWidths] = React.useState<Record<string, number>>({});
  const [isResizing, setIsResizing] = React.useState(false);
  const [resizeColumn, setResizeColumn] = React.useState<string | null>(null);

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
    state: {
      sorting,
      columnFilters,
      columnVisibility,
      rowSelection,
    },
  });

  const { rows } = table.getRowModel();

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

      const newWidth = Math.max(50, e.clientX - 100); // Minimum width of 50px
      setColumnWidths(prev => ({
        ...prev,
        [resizeColumn]: newWidth,
      }));

      if (onColumnResize) {
        onColumnResize(resizeColumn, newWidth);
      }
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

  // Virtualized row renderer
  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => {
    const row = rows[index];
    if (!row) return null;

    return (
      <div className='flex border-b' style={style}>
        {row.getVisibleCells().map(cell => (
          <div
            key={cell.id}
            className='flex-1 px-4 py-2'
            style={
              columnWidths[cell.column.id] ? { width: columnWidths[cell.column.id] } : undefined
            }
          >
            {flexRender(cell.column.columnDef.cell, cell.getContext())}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className='w-full'>
      {/* Search and Column Visibility */}
      <div className='flex items-center py-4 gap-4'>
        {searchKey && (
          <Input
            placeholder={`Search ${searchKey}...`}
            value={(table.getColumn(searchKey)?.getFilterValue() as string) ?? ''}
            onChange={event => table.getColumn(searchKey)?.setFilterValue(event.target.value)}
            className='max-w-sm'
          />
        )}

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
                      onCheckedChange={(value: boolean) => column.toggleVisibility(!!value)}
                    >
                      {column.id}
                    </DropdownMenuCheckboxItem>
                  );
                })}
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>

      {/* Virtualized Table */}
      <div className='rounded-md border'>
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map(headerGroup => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map(header => {
                  return (
                    <TableHead
                      key={header.id}
                      role='columnheader'
                      style={
                        columnWidths[header.id] ? { width: columnWidths[header.id] } : undefined
                      }
                      className='relative'
                    >
                      {header.isPlaceholder
                        ? null
                        : flexRender(header.column.columnDef.header, header.getContext())}
                      {resizable && (
                        <div
                          className='absolute right-0 top-0 h-full w-1 cursor-col-resize bg-transparent hover:bg-gray-300'
                          onMouseDown={e => handleMouseDown(header.id, e)}
                        />
                      )}
                    </TableHead>
                  );
                })}
              </TableRow>
            ))}
          </TableHeader>
        </Table>

        {/* Virtualized Body - Outside of table to avoid DOM nesting issues */}
        <div className='relative' style={{ height }}>
          <List height={height} itemCount={rows.length} itemSize={itemSize} width='100%'>
            {Row}
          </List>
        </div>
      </div>

      {/* Pagination */}
      {showPagination && (
        <div className='flex items-center justify-end space-x-2 py-4'>
          <div className='flex-1 text-sm text-muted-foreground'>
            {table.getFilteredSelectedRowModel().rows.length} of{' '}
            {table.getFilteredRowModel().rows.length} row(s) selected.
          </div>
          <div className='space-x-2'>
            <Button
              variant='outline'
              size='sm'
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
            >
              Previous
            </Button>
            <Button
              variant='outline'
              size='sm'
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
