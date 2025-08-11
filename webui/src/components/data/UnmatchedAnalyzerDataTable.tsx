'use client';

import React, { useMemo } from 'react';
import { DataTable } from '@/components/ui/data-table';
import { Checkbox } from '@/components/ui/checkbox';
import { CommentList } from '../domain/CommentList';

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
  onCommentClick: (commentId: string, allCommentIds?: string[]) => void;
  commentLoading: boolean;
  fieldType: 'razor' | 'blade' | 'soap' | 'brush';
  /** Enable performance logging */
  enablePerformanceLogging?: boolean;
  /** Test ID for testing */
  testId?: string;
}

const UnmatchedAnalyzerDataTable = React.memo<UnmatchedAnalyzerDataTableProps>(
  ({
    data,
    filteredStatus = {},
    pendingChanges = {},
    onFilteredStatusChange,
    onCommentClick,
    commentLoading,
    fieldType,
    enablePerformanceLogging = false,
    testId = 'unmatched-analyzer-data-table',
  }) => {
    const columns = useMemo(() => {
      const logPerformance = (operation: string, startTime: number) => {
        if (enablePerformanceLogging) {
          const duration = performance.now() - startTime;
          console.log(`${operation}: ${duration.toFixed(2)}ms`);
        }
      };

      const formatExamples = (examples: string[]) => {
        if (!examples || examples.length === 0) {
          return <span className='text-gray-400 text-xs'>No examples</span>;
        }

        return (
          <div className='space-y-1'>
            {examples.slice(0, 3).map((example, index) => (
              <div key={index} className='text-xs text-gray-600 bg-gray-50 px-2 py-1 rounded'>
                {example}
              </div>
            ))}
            {examples.length > 3 && (
              <span className='text-xs text-gray-500'>+{examples.length - 3} more</span>
            )}
          </div>
        );
      };

      return [
        {
          accessorKey: 'filtered',
          header: 'Filtered',
          cell: ({ row }) => {
            const item = row.original;
            const isFiltered = filteredStatus[item.item] || false;
            const isPending = pendingChanges[item.item] || false;

            return (
              <div className='flex items-center space-x-2'>
                <Checkbox
                  checked={isFiltered}
                  onCheckedChange={checked => {
                    const startTime = performance.now();
                    onFilteredStatusChange?.(item.item, checked as boolean);
                    logPerformance('filter change', startTime);
                  }}
                  disabled={isPending}
                  className='data-[state=checked]:bg-blue-600 data-[state=checked]:border-blue-600'
                />
                {isPending && (
                  <div className='w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin' />
                )}
              </div>
            );
          },
        },
        {
          accessorKey: 'item',
          header: 'Item',
          cell: ({ row }) => (
            <div className='text-sm font-medium text-gray-900 max-w-xs'>{row.original.item}</div>
          ),
        },
        {
          accessorKey: 'count',
          header: 'Count',
          cell: ({ row }) => (
            <span className='text-sm text-gray-900 font-medium'>{row.original.count}</span>
          ),
        },
        {
          accessorKey: 'comment_ids',
          header: 'Comments',
          cell: ({ row }) => {
            const item = row.original;
            const commentIds = item.comment_ids || [];

            return (
              <CommentList
                commentIds={commentIds}
                onCommentClick={(commentId, allCommentIds) => {
                  const startTime = performance.now();
                  onCommentClick(commentId, allCommentIds);
                  logPerformance('comment click', startTime);
                }}
                commentLoading={commentLoading}
                maxDisplay={3}
                aria-label={`${commentIds.length} comment${commentIds.length !== 1 ? 's' : ''} available`}
              />
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
      ];
    }, [
      onCommentClick,
      commentLoading,
      filteredStatus,
      onFilteredStatusChange,
      pendingChanges,
      enablePerformanceLogging,
    ]);

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
          sortable={true}
          showColumnVisibility={true}
          searchKey='item'
          showPagination={true}
          initialPageSize={50}
        />
      </div>
    );
  }
);

UnmatchedAnalyzerDataTable.displayName = 'UnmatchedAnalyzerDataTable';

export default UnmatchedAnalyzerDataTable;
