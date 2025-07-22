'use client';

import React, { useState, useCallback } from 'react';
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
}

export function BrushSplitDataTable({
  brushSplits,
  onSave,
  onSelectionChange,
  selectedIndices = [],
}: BrushSplitDataTableProps) {
  const [editingData, setEditingData] = useState<Record<number, EditingData>>({});

  // Memoize unsaved changes count
  const unsavedChangesCount = Object.keys(editingData).length;

  // Handle field change
  const handleFieldChange = useCallback((index: number, field: keyof EditingData, value: any) => {
    setEditingData(prev => ({
      ...prev,
      [index]: {
        ...prev[index],
        [field]: value,
      },
    }));
  }, []);

  // Handle save all changes
  const handleSaveAllChanges = useCallback(() => {
    Object.entries(editingData).forEach(([indexStr, changes]) => {
      const index = parseInt(indexStr);
      const originalSplit = brushSplits[index];
      const updatedSplit = { ...originalSplit, ...changes };

      if (onSave) {
        onSave(index, updatedSplit);
      }
    });
    setEditingData({});
  }, [editingData, brushSplits, onSave]);

  // Handle selection change
  const handleSelectionChange = useCallback(
    (indices: number[]) => {
      if (onSelectionChange) {
        onSelectionChange(indices);
      }
    },
    [onSelectionChange]
  );

  // Define columns using TanStack Table ColumnDef
  const columns: ColumnDef<BrushSplit & { index: number }>[] = [
    {
      accessorKey: 'original',
      header: 'Original',
      cell: ({ row }) => <div className='font-medium'>{row.original.original}</div>,
    },
    {
      accessorKey: 'handle',
      header: 'Handle',
      cell: ({ row }) => {
        const index = row.original.index;
        const value = row.original.handle || '';

        return (
          <Input
            value={value}
            onChange={e => handleFieldChange(index, 'handle', e.target.value)}
            className='w-full'
            placeholder='Enter handle'
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
          <Input
            value={value}
            onChange={e => handleFieldChange(index, 'knot', e.target.value)}
            className='w-full'
            placeholder='Enter knot'
          />
        );
      },
    },
    {
      accessorKey: 'validated',
      header: 'Validated',
      cell: ({ row }) => (
        <Checkbox
          checked={row.original.validated}
          onCheckedChange={checked => {
            const updatedSplit = { ...row.original, validated: !!checked };
            if (onSave) onSave(row.original.index, updatedSplit);
          }}
        />
      ),
    },
    {
      accessorKey: 'corrected',
      header: 'Corrected',
      cell: ({ row }) => (
        <Checkbox
          checked={row.original.corrected}
          onCheckedChange={checked => {
            const updatedSplit = { ...row.original, corrected: !!checked };
            if (onSave) onSave(row.original.index, updatedSplit);
          }}
        />
      ),
    },
  ];

  // Transform data to include index
  const tableData = brushSplits.map((split, index) => ({
    ...split,
    index,
  }));

  return (
    <div className='space-y-4'>
      {/* Unsaved Changes Indicator */}
      {unsavedChangesCount > 0 && (
        <div className='flex justify-between items-center p-4 bg-blue-50 border border-blue-200 rounded-lg'>
          <span className='text-blue-800'>
            {unsavedChangesCount} unsaved change{unsavedChangesCount !== 1 ? 's' : ''}
          </span>
          <Button onClick={handleSaveAllChanges} className='bg-blue-600 hover:bg-blue-700'>
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
