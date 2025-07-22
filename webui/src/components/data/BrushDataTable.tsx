'use client';

import React, { useState, useCallback, useMemo, memo } from 'react';
import { ColumnDef } from '@tanstack/react-table';
import { DataTable } from '@/components/ui/data-table';
import { Button } from '@/components/ui/button';
import { ChevronDownIcon, ChevronRightIcon } from '@heroicons/react/24/outline';

// Interface for brush data with subrows
interface BrushData {
  brand: string;
  model: string;
  handle_maker?: string;
  knot_maker?: string;
  fiber?: string;
  knot_size?: string;
  subrows?: BrushData[];
}

interface BrushDataTableProps {
  brushData: BrushData[];
  /** Enable performance logging */
  enablePerformanceLogging?: boolean;
  /** Test ID for testing */
  testId?: string;
}

// Memoized expand/collapse button component
const MemoizedExpandButton = memo<{
  isExpanded: boolean;
  onClick: () => void;
  hasSubrows: boolean;
  'aria-label': string;
}>(({ isExpanded, onClick, hasSubrows, 'aria-label': ariaLabel }) => {
  if (!hasSubrows) return null;

  return (
    <Button
      variant='ghost'
      size='sm'
      onClick={onClick}
      className='p-1 h-6 w-6'
      aria-label={ariaLabel}
    >
      {isExpanded ? (
        <ChevronDownIcon className='h-4 w-4' />
      ) : (
        <ChevronRightIcon className='h-4 w-4' />
      )}
    </Button>
  );
});

MemoizedExpandButton.displayName = 'MemoizedExpandButton';

// Memoized cell component for better performance
const MemoizedCell = memo<{
  children: React.ReactNode;
  className?: string;
  'aria-label'?: string;
}>(({ children, className, 'aria-label': ariaLabel }) => (
  <div className={className} role='cell' aria-label={ariaLabel}>
    {children}
  </div>
));

MemoizedCell.displayName = 'MemoizedCell';

export const BrushDataTable = memo<BrushDataTableProps>(
  ({ brushData, enablePerformanceLogging = false, testId = 'brush-data-table' }) => {
    const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

    // Performance logging
    const logPerformance = useCallback(
      (operation: string, startTime: number) => {
        if (enablePerformanceLogging) {
          const endTime = performance.now();
          console.log(`BrushDataTable ${operation}: ${endTime - startTime}ms`);
        }
      },
      [enablePerformanceLogging]
    );

    // Handle row toggle with performance logging
    const handleRowToggle = useCallback(
      (rowId: string) => {
        const startTime = performance.now();

        setExpandedRows(prev => {
          const newSet = new Set(prev);
          if (newSet.has(rowId)) {
            newSet.delete(rowId);
          } else {
            newSet.add(rowId);
          }
          return newSet;
        });

        logPerformance('row toggle', startTime);
      },
      [logPerformance]
    );

    // Memoize flattened data with subrows
    const flattenedData = useMemo(() => {
      const startTime = performance.now();

      const flattenData = (
        data: BrushData[],
        level = 0
      ): Array<BrushData & { level: number; rowId: string; hasSubrows: boolean }> => {
        const result: Array<BrushData & { level: number; rowId: string; hasSubrows: boolean }> = [];

        data.forEach((item, index) => {
          // Skip null or undefined items
          if (!item) return;

          const rowId = `${level}-${index}`;
          const hasSubrows = !!(item.subrows && item.subrows.length > 0);

          result.push({
            ...item,
            level,
            rowId,
            hasSubrows,
          });

          // Add subrows if expanded
          if (hasSubrows && expandedRows.has(rowId)) {
            const subrows = flattenData(item.subrows!, level + 1);
            result.push(...subrows);
          }
        });

        return result;
      };

      const result = flattenData(brushData);
      logPerformance('data flattening', startTime);
      return result;
    }, [brushData, expandedRows, logPerformance]);

    // Memoize columns to prevent unnecessary re-renders
    const columns: ColumnDef<BrushData & { level: number; rowId: string; hasSubrows: boolean }>[] =
      useMemo(
        () => [
          {
            accessorKey: 'expand',
            header: '',
            cell: ({ row }) => {
              const { rowId, hasSubrows, level } = row.original;
              const isExpanded = expandedRows.has(rowId);

              return (
                <div className='flex items-center'>
                  <div style={{ marginLeft: `${level * 20}px` }} />
                  <MemoizedExpandButton
                    isExpanded={isExpanded}
                    onClick={() => handleRowToggle(rowId)}
                    hasSubrows={hasSubrows}
                    aria-label={isExpanded ? 'Collapse row' : 'Expand row'}
                  />
                </div>
              );
            },
          },
          {
            accessorKey: 'brand',
            header: 'Brand',
            cell: ({ row }) => (
              <MemoizedCell
                className='font-medium text-gray-900'
                aria-label={`Brand: ${row.original.brand}`}
              >
                {row.original.brand}
              </MemoizedCell>
            ),
          },
          {
            accessorKey: 'model',
            header: 'Model',
            cell: ({ row }) => (
              <MemoizedCell
                className='text-sm text-gray-600'
                aria-label={`Model: ${row.original.model}`}
              >
                {row.original.model}
              </MemoizedCell>
            ),
          },
          {
            accessorKey: 'handle_maker',
            header: 'Handle Maker',
            cell: ({ row }) => (
              <MemoizedCell
                className='text-sm text-gray-600'
                aria-label={`Handle maker: ${row.original.handle_maker || 'Not specified'}`}
              >
                {row.original.handle_maker || 'N/A'}
              </MemoizedCell>
            ),
          },
          {
            accessorKey: 'knot_maker',
            header: 'Knot Maker',
            cell: ({ row }) => (
              <MemoizedCell
                className='text-sm text-gray-600'
                aria-label={`Knot maker: ${row.original.knot_maker || 'Not specified'}`}
              >
                {row.original.knot_maker || 'N/A'}
              </MemoizedCell>
            ),
          },
          {
            accessorKey: 'fiber',
            header: 'Fiber',
            cell: ({ row }) => (
              <MemoizedCell
                className='text-sm text-gray-600'
                aria-label={`Fiber: ${row.original.fiber || 'Not specified'}`}
              >
                {row.original.fiber || 'N/A'}
              </MemoizedCell>
            ),
          },
          {
            accessorKey: 'knot_size',
            header: 'Knot Size',
            cell: ({ row }) => (
              <MemoizedCell
                className='text-sm text-gray-600'
                aria-label={`Knot size: ${row.original.knot_size || 'Not specified'}`}
              >
                {row.original.knot_size || 'N/A'}
              </MemoizedCell>
            ),
          },
        ],
        [expandedRows, handleRowToggle]
      );

    // Handle empty data gracefully
    if (!brushData || brushData.length === 0) {
      return (
        <div
          className='flex items-center justify-center p-8 text-gray-500'
          role='status'
          aria-live='polite'
          data-testid={testId}
        >
          <p>No brush data to display</p>
        </div>
      );
    }

    return (
      <div
        className='space-y-4'
        data-testid={testId}
        role='region'
        aria-label='Brush data table with hierarchical structure'
      >
        {/* DataTable with ShadCN foundation */}
        <DataTable
          columns={columns}
          data={flattenedData}
          height={400}
          itemSize={48}
          resizable={true}
          showColumnVisibility={true}
          searchKey='brand'
        />
      </div>
    );
  }
);

BrushDataTable.displayName = 'BrushDataTable';
