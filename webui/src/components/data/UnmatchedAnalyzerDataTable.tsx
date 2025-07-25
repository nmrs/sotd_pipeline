'use client';

import React, { useCallback, useMemo, memo } from 'react';
import { ColumnDef } from '@tanstack/react-table';
import { DataTable } from '@/components/ui/data-table';
import { Checkbox } from '@/components/ui/checkbox';
import { Button } from '@/components/ui/button';

// Interface for unmatched analyzer data
interface UnmatchedItem {
  item: string;
  count: number;
  comment_ids?: string[];
  examples?: string[];
}

interface UnmatchedAnalyzerDataTableProps {
  data: UnmatchedItem[];
  filteredStatus?: Record<string, boolean>;
  pendingChanges?: Record<string, boolean>;
  onFilteredStatusChange?: (itemName: string, isFiltered: boolean) => void;
  onCommentClick: (commentId: string) => void;
  commentLoading: boolean;
  fieldType: 'razor' | 'blade' | 'soap' | 'brush';
  columnWidths: {
    filtered: number;
    item: number;
    count: number;
    comment_ids: number;
    examples: number;
  };
  /** Enable performance logging */
  enablePerformanceLogging?: boolean;
  /** Test ID for testing */
  testId?: string;
}

// Memoized checkbox component for better performance
const MemoizedCheckbox = memo<{
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  disabled: boolean;
  title: string;
  hasPendingChange: boolean;
}>(({ checked, onCheckedChange, disabled, title, hasPendingChange }) => (
  <div className='flex items-center'>
    <Checkbox
      checked={checked}
      onCheckedChange={onCheckedChange}
      disabled={disabled}
      className='rounded border-gray-300 text-blue-600 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed'
      title={title}
      aria-label={title}
    />
    {hasPendingChange && (
      <div className='ml-1'>
        <div
          className='w-2 h-2 bg-blue-600 rounded-full'
          aria-label='Pending change indicator'
        ></div>
      </div>
    )}
  </div>
));

MemoizedCheckbox.displayName = 'MemoizedCheckbox';

// Memoized button component for better performance
const MemoizedButton = memo<{
  onClick: () => void;
  disabled: boolean;
  children: React.ReactNode;
  className: string;
  'aria-label': string;
}>(({ onClick, disabled, children, className, 'aria-label': ariaLabel }) => (
  <Button onClick={onClick} disabled={disabled} className={className} aria-label={ariaLabel}>
    {children}
  </Button>
));

MemoizedButton.displayName = 'MemoizedButton';

export const UnmatchedAnalyzerDataTable = memo<UnmatchedAnalyzerDataTableProps>(
  ({
    data,
    onCommentClick,
    commentLoading,
    fieldType,
    enablePerformanceLogging = false,
    testId = 'unmatched-analyzer-data-table',
  }) => {
    // Performance logging
    const logPerformance = useCallback(
      (operation: string, startTime: number) => {
        if (enablePerformanceLogging) {
          const endTime = performance.now();
          console.log(`UnmatchedAnalyzerDataTable ${operation}: ${endTime - startTime}ms`);
        }
      },
      [enablePerformanceLogging]
    );

    // Memoize format examples function
    const formatExamples = useCallback((examples: string[]) => {
      if (!examples || examples.length === 0) {
        return <span className='text-gray-400 text-xs'>No examples</span>;
      }
      return (
        <span className='text-sm text-gray-600'>
          {examples.slice(0, 2).join(', ')}
          {examples.length > 2 && ` +${examples.length - 2} more`}
        </span>
      );
    }, []);

    // Memoize columns to prevent unnecessary re-renders
    const columns: ColumnDef<UnmatchedItem>[] = useMemo(
      () => [
        {
          accessorKey: 'item',
          header: 'Item',
          cell: ({ row }) => {
            const item = row.original;
            return (
              <div className='font-medium text-gray-900' data-testid='item-cell'>
                {item.item}
              </div>
            );
          },
        },
        {
          accessorKey: 'count',
          header: 'Count',
          cell: ({ row }) => (
            <span
              className='text-sm text-gray-600'
              role='cell'
              aria-label={`Count: ${row.original.count}`}
            >
              {row.original.count}
            </span>
          ),
        },
        {
          accessorKey: 'comment_ids',
          header: 'Comments',
          cell: ({ row }) => {
            const item = row.original;
            const commentIds = item.comment_ids || [];

            if (commentIds.length === 0) {
              return (
                <span
                  className='text-gray-400 text-xs'
                  role='cell'
                  aria-label='No comments available'
                >
                  No comments
                </span>
              );
            }

            return (
              <div
                className='space-y-1'
                role='cell'
                aria-label={`${commentIds.length} comment${commentIds.length !== 1 ? 's' : ''} available`}
              >
                {commentIds.slice(0, 3).map((commentId, index) => (
                  <MemoizedButton
                    key={commentId}
                    onClick={() => {
                      const startTime = performance.now();
                      onCommentClick(commentId);
                      logPerformance('comment click', startTime);
                    }}
                    disabled={commentLoading}
                    className='block w-full text-left text-xs text-blue-600 hover:text-blue-800 hover:bg-blue-50 px-2 py-1 rounded'
                    aria-label={`View comment ${index + 1} of ${commentIds.length}`}
                  >
                    {commentId}
                  </MemoizedButton>
                ))}
                {commentIds.length > 3 && (
                  <span className='text-xs text-gray-500'>+{commentIds.length - 3} more</span>
                )}
              </div>
            );
          },
        },
        {
          accessorKey: 'examples',
          header: 'Examples',
          cell: ({ row }) => (
            <div role='cell' aria-label={`Examples for ${row.original.item}`}>
              {formatExamples(row.original.examples || [])}
            </div>
          ),
        },
      ],
      [onCommentClick, commentLoading, formatExamples, logPerformance]
    );

    // Handle empty data gracefully
    if (!data || data.length === 0) {
      return (
        <div
          className='flex items-center justify-center p-8 text-gray-500'
          role='status'
          aria-live='polite'
          data-testid={testId}
        >
          <p>No unmatched items to display</p>
        </div>
      );
    }

    return (
      <div
        className='space-y-4'
        data-testid={testId}
        role='region'
        aria-label={`Unmatched ${fieldType} analyzer data table`}
      >
        {/* DataTable with ShadCN foundation */}
        <DataTable
          columns={columns}
          data={data}
          resizable={true}
          showColumnVisibility={true}
          searchKey='item'
        />
      </div>
    );
  }
);

UnmatchedAnalyzerDataTable.displayName = 'UnmatchedAnalyzerDataTable';
