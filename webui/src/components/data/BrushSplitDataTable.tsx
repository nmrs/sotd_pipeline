'use client';

import React, { useState, useCallback, useMemo, memo } from 'react';
import { ColumnDef } from '@tanstack/react-table';
import { DataTable } from '@/components/ui/data-table';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { BrushSplit } from '../../types/brushSplit';

// Extended interface for editing data
interface EditingData {
  handle?: string | null;
  knot?: string;
  should_not_split?: boolean;
}

interface BrushSplitDataTableProps {
  brushSplits: BrushSplit[];
  onSave?: (index: number, updatedSplit: BrushSplit) => void;
  onSelectionChange?: (selectedIndices: number[]) => void;
  selectedIndices?: number[];
  /** Enable performance logging */
  enablePerformanceLogging?: boolean;
  /** Test ID for testing */
  testId?: string;
}

// Memoized input component for better performance
const MemoizedInput = memo<{
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  'aria-label': string;
}>(({ value, onChange, placeholder, 'aria-label': ariaLabel }) => (
  <Input
    value={value}
    onChange={e => onChange(e.target.value)}
    className='w-full'
    placeholder={placeholder}
    aria-label={ariaLabel}
  />
));

MemoizedInput.displayName = 'MemoizedInput';

// Memoized checkbox component for better performance
const MemoizedCheckbox = memo<{
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  'aria-label': string;
}>(({ checked, onCheckedChange, 'aria-label': ariaLabel }) => (
  <Checkbox checked={checked} onCheckedChange={onCheckedChange} aria-label={ariaLabel} />
));

MemoizedCheckbox.displayName = 'MemoizedCheckbox';

export const BrushSplitDataTable = memo<BrushSplitDataTableProps>(
  ({
    brushSplits,
    onSave,
    onSelectionChange,
    selectedIndices = [],
    enablePerformanceLogging = false,
    testId = 'brush-split-data-table',
  }) => {
    const [editingData, setEditingData] = useState<Record<number, EditingData>>({});

    // Memoize unsaved changes count for performance
    const unsavedChangesCount = useMemo(() => Object.keys(editingData).length, [editingData]);

    // Memoize table data transformation
    const tableData = useMemo(
      () =>
        brushSplits.map((split, index) => ({
          ...split,
          index,
        })),
      [brushSplits]
    );

    // Performance logging
    const logPerformance = useCallback(
      (operation: string, startTime: number) => {
        if (enablePerformanceLogging) {
          const endTime = performance.now();
          console.log(`BrushSplitDataTable ${operation}: ${endTime - startTime}ms`);
        }
      },
      [enablePerformanceLogging]
    );

    // Handle field change with performance logging
    const handleFieldChange = useCallback(
      (index: number, field: keyof EditingData, value: any) => {
        const startTime = performance.now();

        setEditingData(prev => ({
          ...prev,
          [index]: {
            ...prev[index],
            [field]: value,
          },
        }));

        logPerformance('field change', startTime);
      },
      [logPerformance]
    );

    // Handle save all changes with performance logging
    const handleSaveAllChanges = useCallback(() => {
      const startTime = performance.now();

      try {
        Object.entries(editingData).forEach(([indexStr, changes]) => {
          const index = parseInt(indexStr);
          const originalSplit = brushSplits[index];

          if (!originalSplit) {
            console.warn(`BrushSplitDataTable: Original split not found for index ${index}`);
            return;
          }

          const updatedSplit = { ...originalSplit, ...changes };

          if (onSave) {
            onSave(index, updatedSplit);
          }
        });
        setEditingData({});

        logPerformance('save all changes', startTime);
      } catch (error) {
        console.error('BrushSplitDataTable: Error saving changes:', error);
        // Re-throw to allow parent component to handle
        throw error;
      }
    }, [editingData, brushSplits, onSave, logPerformance]);

    // Handle selection change with performance logging
    const handleSelectionChange = useCallback(
      (indices: number[]) => {
        const startTime = performance.now();

        if (onSelectionChange) {
          onSelectionChange(indices);
        }

        logPerformance('selection change', startTime);
      },
      [onSelectionChange, logPerformance]
    );

    // Memoize columns to prevent unnecessary re-renders
    const columns: ColumnDef<BrushSplit & { index: number }>[] = useMemo(
      () => [
        {
          accessorKey: 'original',
          header: 'Original',
          cell: ({ row }) => (
            <div
              className='font-medium'
              role='cell'
              aria-label={`Original: ${row.original.original}`}
            >
              {row.original.original}
            </div>
          ),
        },
        {
          accessorKey: 'handle',
          header: 'Handle',
          cell: ({ row }) => {
            const index = row.original.index;
            const value = row.original.handle || '';

            return (
              <MemoizedInput
                value={value}
                onChange={newValue => handleFieldChange(index, 'handle', newValue)}
                placeholder='Enter handle'
                aria-label={`Handle for row ${index + 1}`}
              />
            );
          },
        },
        {
          accessorKey: 'knot',
          header: 'Knot',
          cell: ({ row }) => {
            const index = row.original.index;
            const value = row.original.knot || '';

            return (
              <MemoizedInput
                value={value}
                onChange={newValue => handleFieldChange(index, 'knot', newValue)}
                placeholder='Enter knot'
                aria-label={`Knot for row ${index + 1}`}
              />
            );
          },
        },
        {
          accessorKey: 'validated',
          header: 'Validated',
          cell: ({ row }) => (
            <MemoizedCheckbox
              checked={row.original.validated}
              onCheckedChange={checked => {
                const updatedSplit = { ...row.original, validated: !!checked };
                if (onSave) onSave(row.original.index, updatedSplit);
              }}
              aria-label={`Mark row ${row.original.index + 1} as validated`}
            />
          ),
        },
        {
          accessorKey: 'corrected',
          header: 'Corrected',
          cell: ({ row }) => (
            <MemoizedCheckbox
              checked={row.original.corrected}
              onCheckedChange={checked => {
                const updatedSplit = { ...row.original, corrected: !!checked };
                if (onSave) onSave(row.original.index, updatedSplit);
              }}
              aria-label={`Mark row ${row.original.index + 1} as corrected`}
            />
          ),
        },
      ],
      [handleFieldChange, onSave]
    );

    // Handle empty data gracefully
    if (!brushSplits || brushSplits.length === 0) {
      return (
        <div
          className='flex items-center justify-center p-8 text-gray-500'
          role='status'
          aria-live='polite'
          data-testid={testId}
        >
          <p>No brush splits to display</p>
        </div>
      );
    }

    return (
      <div
        className='space-y-4'
        data-testid={testId}
        role='region'
        aria-label='Brush Split Data Table'
      >
        {/* Unsaved Changes Indicator */}
        {unsavedChangesCount > 0 && (
          <div
            className='flex justify-between items-center p-4 bg-blue-50 border border-blue-200 rounded-lg'
            role='alert'
            aria-live='polite'
          >
            <span className='text-blue-800'>
              {unsavedChangesCount} unsaved change{unsavedChangesCount !== 1 ? 's' : ''}
            </span>
            <Button
              onClick={handleSaveAllChanges}
              className='bg-blue-600 hover:bg-blue-700'
              aria-label={`Save all ${unsavedChangesCount} changes`}
            >
              Save All Changes
            </Button>
          </div>
        )}

        {/* DataTable with ShadCN foundation */}
        <DataTable
          columns={columns}
          data={tableData}
          height={400}
          itemSize={48}
          resizable={true}
          showColumnVisibility={true}
          searchKey='original'
        />
      </div>
    );
  }
);

BrushSplitDataTable.displayName = 'BrushSplitDataTable';
