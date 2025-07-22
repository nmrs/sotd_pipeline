'use client';

import React, { useState, useCallback } from 'react';
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
  filteredStatus: Record<string, boolean>;
  pendingChanges: Record<string, boolean>;
  onFilteredStatusChange: (itemName: string, isFiltered: boolean) => void;
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
}

export function UnmatchedAnalyzerDataTable({
  data,
  filteredStatus,
  pendingChanges,
  onFilteredStatusChange,
  onCommentClick,
  commentLoading,
  fieldType,
  columnWidths,
}: UnmatchedAnalyzerDataTableProps) {
  // Format examples for display
  const formatExamples = (examples: string[]) => {
    if (!examples || examples.length === 0) {
      return <span className='text-gray-400 text-xs'>No examples</span>;
    }
    return (
      <span className='text-sm text-gray-600'>
        {examples.slice(0, 2).join(', ')}
        {examples.length > 2 && ` +${examples.length - 2} more`}
      </span>
    );
  };

  // Define columns using TanStack Table ColumnDef
  const columns: ColumnDef<UnmatchedItem>[] = [
    {
      accessorKey: 'filtered',
      header: 'Filtered',
      cell: ({ row }) => {
        const item = row.original;
        const isCurrentlyFiltered = filteredStatus[item.item] || false;
        const hasPendingChange = item.item in pendingChanges;
        const pendingValue = pendingChanges[item.item];
        const displayValue = hasPendingChange ? pendingValue : isCurrentlyFiltered;

        return (
          <div className='flex items-center'>
            <Checkbox
              checked={displayValue}
              onCheckedChange={checked => onFilteredStatusChange(item.item, !!checked)}
              disabled={commentLoading}
              className='rounded border-gray-300 text-blue-600 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed'
              title={displayValue ? 'Mark as unfiltered' : 'Mark as intentionally unmatched'}
            />
            {hasPendingChange && (
              <div className='ml-1'>
                <div className='w-2 h-2 bg-blue-600 rounded-full'></div>
              </div>
            )}
          </div>
        );
      },
    },
    {
      accessorKey: 'item',
      header: fieldType.charAt(0).toUpperCase() + fieldType.slice(1),
      cell: ({ row }) => {
        const item = row.original;
        return (
          <span
            className={`font-medium text-sm ${
              filteredStatus[item.item] ? 'text-gray-400 line-through' : 'text-gray-900'
            }`}
          >
            {item.item}
            {filteredStatus[item.item] && (
              <span className='ml-2 text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded'>
                Filtered
              </span>
            )}
          </span>
        );
      },
    },
    {
      accessorKey: 'count',
      header: 'Count',
      cell: ({ row }) => <span className='text-gray-500 text-sm'>{row.original.count}</span>,
    },
    {
      accessorKey: 'comment_ids',
      header: 'Comment IDs',
      cell: ({ row }) => {
        const item = row.original;
        return (
          <div className='text-sm'>
            {item.comment_ids && item.comment_ids.length > 0 ? (
              <div className='flex flex-wrap gap-1'>
                {item.comment_ids.slice(0, 3).map((commentId, index) => (
                  <Button
                    key={index}
                    variant='outline'
                    size='sm'
                    onClick={() => onCommentClick(commentId)}
                    disabled={commentLoading}
                    className='text-blue-600 hover:text-blue-800 underline text-xs bg-blue-50 px-2 py-1 rounded hover:bg-blue-100 disabled:opacity-50 disabled:cursor-not-allowed'
                  >
                    {commentLoading ? 'Loading...' : commentId}
                  </Button>
                ))}
                {item.comment_ids.length > 3 && (
                  <span className='text-gray-500 text-xs'>+{item.comment_ids.length - 3} more</span>
                )}
              </div>
            ) : (
              <span className='text-gray-400 text-xs'>No comment IDs</span>
            )}
          </div>
        );
      },
    },
    {
      accessorKey: 'examples',
      header: 'Examples',
      cell: ({ row }) => {
        const item = row.original;
        return formatExamples(item.examples || []);
      },
    },
  ];

  return (
    <div className='space-y-4'>
      {/* DataTable with ShadCN foundation */}
      <DataTable
        columns={columns}
        data={data}
        height={350}
        itemSize={40}
        resizable={true}
        showColumnVisibility={true}
        searchKey='item'
      />
    </div>
  );
}
