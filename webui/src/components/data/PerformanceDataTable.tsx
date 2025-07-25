'use client';

import React, { useCallback, useMemo, memo } from 'react';
import { ColumnDef } from '@tanstack/react-table';
import { DataTable } from '@/components/ui/data-table';

// Interface for performance test data
interface PerformanceItem {
  id: string;
  name: string;
  email: string;
  status: string;
  date: string;
}

interface PerformanceDataTableProps {
  data: PerformanceItem[];
  /** Enable performance logging */
  enablePerformanceLogging?: boolean;
  /** Callback for sort operations */
  onSort?: (column: string, direction: 'asc' | 'desc') => void;
  /** Test ID for testing */
  testId?: string;
}

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

export const PerformanceDataTable = memo<PerformanceDataTableProps>(
  ({ data, enablePerformanceLogging = false, testId = 'performance-data-table' }) => {
    // Performance logging
    const logPerformance = useCallback(
      (operation: string, startTime: number) => {
        if (enablePerformanceLogging) {
          const endTime = performance.now();
          console.log(`PerformanceDataTable ${operation}: ${endTime - startTime}ms`);
        }
      },
      [enablePerformanceLogging]
    );

    // Memoize columns to prevent unnecessary re-renders
    const columns: ColumnDef<PerformanceItem>[] = useMemo(
      () => [
        {
          accessorKey: 'id',
          header: 'ID',
          cell: ({ row }) => (
            <MemoizedCell
              className='font-mono text-sm text-gray-600'
              aria-label={`ID: ${row.original.id}`}
            >
              {row.original.id}
            </MemoizedCell>
          ),
        },
        {
          accessorKey: 'name',
          header: 'Name',
          cell: ({ row }) => (
            <MemoizedCell
              className='font-medium text-gray-900'
              aria-label={`Name: ${row.original.name}`}
            >
              {row.original.name}
            </MemoizedCell>
          ),
        },
        {
          accessorKey: 'email',
          header: 'Email',
          cell: ({ row }) => (
            <MemoizedCell
              className='text-sm text-gray-600'
              aria-label={`Email: ${row.original.email}`}
            >
              {row.original.email}
            </MemoizedCell>
          ),
        },
        {
          accessorKey: 'status',
          header: 'Status',
          cell: ({ row }) => {
            const status = row.original.status;
            const statusColor =
              status === 'active'
                ? 'text-green-600'
                : status === 'inactive'
                  ? 'text-red-600'
                  : 'text-gray-600';

            return (
              <MemoizedCell
                className={`text-sm font-medium ${statusColor}`}
                aria-label={`Status: ${status}`}
              >
                {status}
              </MemoizedCell>
            );
          },
        },
        {
          accessorKey: 'date',
          header: 'Date',
          cell: ({ row }) => (
            <MemoizedCell
              className='text-sm text-gray-500'
              aria-label={`Date: ${row.original.date}`}
            >
              {row.original.date}
            </MemoizedCell>
          ),
        },
      ],
      []
    );

    // Performance metrics display
    const performanceMetrics = useMemo(() => {
      const startTime = performance.now();

      // Filter out null/undefined items and handle malformed data gracefully
      const validData = data.filter(item => item && typeof item === 'object');

      const metrics = {
        totalRows: validData.length,
        uniqueStatuses: new Set(validData.map(item => item?.status).filter(Boolean)).size,
        activeUsers: validData.filter(item => item?.status === 'active').length,
      };

      logPerformance('metrics calculation', startTime);

      if (!enablePerformanceLogging) return null;

      return (
        <div
          className='mb-4 p-4 bg-gray-50 border border-gray-200 rounded-lg'
          role='region'
          aria-label='Performance metrics'
        >
          <h3 className='text-sm font-medium text-gray-700 mb-2'>Performance Metrics</h3>
          <div className='grid grid-cols-3 gap-4 text-xs'>
            <div>
              <span className='text-gray-500'>Total Rows:</span>
              <span className='ml-1 font-medium'>{metrics.totalRows}</span>
            </div>
            <div>
              <span className='text-gray-500'>Unique Statuses:</span>
              <span className='ml-1 font-medium'>{metrics.uniqueStatuses}</span>
            </div>
            <div>
              <span className='text-gray-500'>Active Users:</span>
              <span className='ml-1 font-medium'>{metrics.activeUsers}</span>
            </div>
          </div>
        </div>
      );
    }, [data, enablePerformanceLogging, logPerformance]);

    // Handle empty data gracefully
    if (!data || data.length === 0) {
      return (
        <div
          className='flex items-center justify-center p-8 text-gray-500'
          role='status'
          aria-live='polite'
          data-testid={testId}
        >
          <p>No performance data to display</p>
        </div>
      );
    }

    return (
      <div
        className='space-y-4'
        data-testid={testId}
        role='region'
        aria-label='Performance data table'
      >
        {/* Performance Metrics */}
        {performanceMetrics}

        {/* DataTable with ShadCN foundation */}
        <DataTable
          columns={columns}
          data={data}
          resizable={true}
          sortable={true}
          showColumnVisibility={true}
          searchKey='name'
        />
      </div>
    );
  }
);

PerformanceDataTable.displayName = 'PerformanceDataTable';
