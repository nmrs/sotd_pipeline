'use client';

import React, { useState, useCallback } from 'react';
import { ColumnDef } from '@tanstack/react-table';
import { DataTable } from '@/components/ui/data-table';

// Interface for performance test data
interface TestData {
  id: number;
  name: string;
  email: string;
  status: string;
  date: string;
}

interface PerformanceDataTableProps {
  data: TestData[];
  onSort?: (column: string) => void;
  sortColumn?: string;
  sortDirection?: 'asc' | 'desc';
  enablePerformanceLogging?: boolean;
  testId?: string;
}

export function PerformanceDataTable({
  data,
  onSort,
  sortColumn,
  sortDirection = 'asc',
  enablePerformanceLogging = false,
  testId,
}: PerformanceDataTableProps) {
  // Performance monitoring
  const [performanceMetrics, setPerformanceMetrics] = useState({
    sortOperations: 0,
    totalSortTime: 0,
    averageSortTime: 0,
  });

  // Handle sort with performance monitoring
  const handleSort = useCallback(
    (column: string) => {
      if (!onSort) return;

      const start = performance.now();
      onSort(column);
      const end = performance.now();
      const sortTime = end - start;

      if (enablePerformanceLogging) {
        console.log(`Sort operation on column '${column}' took ${sortTime}ms`);
      }

      setPerformanceMetrics(prev => {
        const newSortOperations = prev.sortOperations + 1;
        const newTotalSortTime = prev.totalSortTime + sortTime;
        const newAverageSortTime = newTotalSortTime / newSortOperations;

        return {
          sortOperations: newSortOperations,
          totalSortTime: newTotalSortTime,
          averageSortTime: newAverageSortTime,
        };
      });
    },
    [onSort, enablePerformanceLogging]
  );

  // Define columns using TanStack Table ColumnDef
  const columns: ColumnDef<TestData>[] = [
    {
      accessorKey: 'id',
      header: 'ID',
      cell: ({ row }) => <div className='text-sm font-medium'>{row.original.id}</div>,
    },
    {
      accessorKey: 'name',
      header: 'Name',
      cell: ({ row }) => <div className='text-sm'>{row.original.name}</div>,
    },
    {
      accessorKey: 'email',
      header: 'Email',
      cell: ({ row }) => <div className='text-sm'>{row.original.email}</div>,
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => (
        <div className='text-sm'>
          <span
            className={`px-2 py-1 rounded text-xs ${
              row.original.status === 'active'
                ? 'bg-green-100 text-green-800'
                : row.original.status === 'inactive'
                  ? 'bg-red-100 text-red-800'
                  : 'bg-yellow-100 text-yellow-800'
            }`}
          >
            {row.original.status}
          </span>
        </div>
      ),
    },
    {
      accessorKey: 'date',
      header: 'Date',
      cell: ({ row }) => (
        <div className='text-sm text-gray-500'>
          {new Date(row.original.date).toLocaleDateString()}
        </div>
      ),
    },
  ];

  return (
    <div className='space-y-4' data-testid={testId}>
      {/* Performance Metrics Display */}
      {enablePerformanceLogging && performanceMetrics.sortOperations > 0 && (
        <div className='bg-blue-50 border border-blue-200 rounded p-3'>
          <h4 className='font-semibold text-blue-900 mb-2'>Performance Metrics:</h4>
          <div className='text-sm text-blue-800 space-y-1'>
            <p>• Sort operations: {performanceMetrics.sortOperations}</p>
            <p>• Total sort time: {performanceMetrics.totalSortTime.toFixed(2)}ms</p>
            <p>• Average sort time: {performanceMetrics.averageSortTime.toFixed(2)}ms</p>
          </div>
        </div>
      )}

      {/* DataTable with ShadCN foundation */}
      <DataTable
        columns={columns}
        data={data}
        height={400}
        itemSize={48}
        resizable={true}
        showColumnVisibility={true}
        searchKey='name'
      />
    </div>
  );
}
