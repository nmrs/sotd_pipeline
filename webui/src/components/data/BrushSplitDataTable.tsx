'use client';

import React, { useCallback, useMemo, useState, memo, useRef, useEffect } from 'react';
import { flushSync } from 'react-dom';
import { ColumnDef } from '@tanstack/react-table';
import { DataTable } from '@/components/ui/data-table';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { BrushSplit, BrushSplitValidationStatus } from '@/types/brushSplit';

interface BrushSplitDataTableProps {
  brushSplits: BrushSplit[];
  onSave: (data: BrushSplit[]) => void;
  onSelectionChange?: (selectedRows: BrushSplit[]) => void;
  customControls?: React.ReactNode;
  onCommentClick?: (commentId: string) => void;
  commentLoading?: boolean;
}

// Extended type for table data with index
type BrushSplitWithIndex = BrushSplit & { index: number };

// Memoized input component to prevent unnecessary re-renders
const MemoizedInput = memo<{
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  'aria-label': string;
}>(({ value, onChange, placeholder, 'aria-label': ariaLabel }) => (
  <Input
    value={value}
    onChange={e => onChange(e.target.value)}
    placeholder={placeholder}
    aria-label={ariaLabel}
    className='w-full'
  />
));

MemoizedInput.displayName = 'MemoizedInput';

export function BrushSplitDataTable({
  brushSplits,
  onSave,
  onSelectionChange,
  customControls,
  onCommentClick,
  commentLoading = false,
}: BrushSplitDataTableProps) {
  const [editingData, setEditingData] = useState<Record<number, Partial<BrushSplit>>>({});
  const [selectedRows, setSelectedRows] = useState<Set<number>>(new Set());
  const [clearSelection, setClearSelection] = useState(false);

  // Track original values before "Don't Split" was checked
  const [originalValues, setOriginalValues] = useState<
    Record<number, { handle: string; knot: string; validated: boolean }>
  >({});

  // Initialize row selection based on validation status
  useEffect(() => {
    const validatedIndices = new Set(
      brushSplits
        .map((split, index) => ({ split, index }))
        .filter(({ split }) => split.validated)
        .map(({ index }) => index)
    );
    setSelectedRows(validatedIndices);
  }, [brushSplits]);

  // Handle row selection changes
  const handleSelectionChange = useCallback((selectedRowsData: BrushSplitWithIndex[]) => {
    const selectedIndices = new Set(selectedRowsData.map(row => row.index));
    setSelectedRows(selectedIndices);
    onSelectionChange?.(selectedRowsData);
  }, [onSelectionChange]);

  // Reset clearSelection flag after it's been used
  useEffect(() => {
    if (clearSelection) {
      // Reset the flag after a short delay to ensure the DataTable has processed it
      const timer = setTimeout(() => {
        setClearSelection(false);
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [clearSelection]);

  const handleFieldChange = useCallback(
    (index: number, field: keyof BrushSplit, value: string | boolean) => {
      const originalValue = brushSplits[index][field];

      // If the new value matches the original, clear the change
      if (value === originalValue) {
        setEditingData(prev => {
          const newData = { ...prev };
          if (newData[index]) {
            delete newData[index][field];
            // If no more changes for this row, remove the entire row entry
            if (Object.keys(newData[index]).length === 0) {
              delete newData[index];
            }
          }
          return newData;
        });
      } else {
        // Set the change
        setEditingData(prev => ({
          ...prev,
          [index]: {
            ...prev[index],
            [field]: value,
          },
        }));
      }
    },
    [brushSplits]
  );

  const handleSave = useCallback(() => {
    const updatedData = brushSplits.map((item, index) => {
      const editingChanges = editingData[index] || {};

      return {
        ...item,
        ...editingChanges,
        // Mark as validated if the row is selected
        validated: selectedRows.has(index) || editingChanges.validated || item.validated,
      };
    });
    onSave(updatedData);
    setEditingData({});
    setOriginalValues({});
    setSelectedRows(new Set()); // Clear selection after save
    setClearSelection(true); // Set flag to clear selection
  }, [brushSplits, editingData, selectedRows, onSave]);

  const hasUnsavedChanges = Object.keys(editingData).length > 0 ||
    (selectedRows.size > 0 && selectedRows.size !== brushSplits.filter(split => split.validated).length);

  const columns = useMemo<ColumnDef<BrushSplitWithIndex>[]>(
    () => [
      {
        id: 'select',
        header: ({ table }) => (
          <Checkbox
            checked={
              table.getIsAllPageRowsSelected() ||
              (table.getIsSomePageRowsSelected() && 'indeterminate')
            }
            onCheckedChange={value => table.toggleAllPageRowsSelected(!!value)}
            aria-label='Select all'
          />
        ),
        cell: ({ row }) => (
          <Checkbox
            checked={row.getIsSelected()}
            onCheckedChange={value => row.toggleSelected(!!value)}
            aria-label='Select row'
          />
        ),
        enableSorting: false,
        enableHiding: false,
      },
      {
        accessorKey: 'original',
        header: 'Original',
        cell: ({ row }) => {
          return <span>{row.original.original}</span>;
        },
      },
      {
        accessorKey: 'corrected',
        header: 'Corrected',
        cell: ({ row }) => {
          return <span>{row.original.corrected ? 'Yes' : 'No'}</span>;
        },
      },
      {
        accessorKey: 'handle',
        header: 'Handle',
        cell: ({ row }) => {
          const index = row.original.index;
          const editingValue = editingData[index]?.handle;
          const value = editingValue !== undefined ? editingValue || '' : row.original.handle || '';
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
          const editingValue = editingData[index]?.knot;
          const value = editingValue !== undefined ? editingValue || '' : row.original.knot || '';
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
        accessorKey: 'comment_ids',
        header: 'Comments',
        cell: ({ row }) => {
          // Extract all comment_ids from occurrences
          const allCommentIds = row.original.occurrences.flatMap(occurrence => occurrence.comment_ids);
          const uniqueCommentIds = [...new Set(allCommentIds)];

          if (uniqueCommentIds.length === 0) {
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
              aria-label={`${uniqueCommentIds.length} comment${uniqueCommentIds.length !== 1 ? 's' : ''} available`}
            >
              {uniqueCommentIds.slice(0, 3).map((commentId, index) => (
                <button
                  key={commentId}
                  onClick={() => onCommentClick?.(commentId)}
                  disabled={commentLoading}
                  className='block w-full text-left text-xs text-blue-600 hover:text-blue-800 hover:bg-blue-50 px-2 py-1 rounded'
                  aria-label={`View comment ${index + 1} of ${uniqueCommentIds.length}`}
                >
                  {commentId}
                </button>
              ))}
              {uniqueCommentIds.length > 3 && (
                <span className='text-xs text-gray-500'>+{uniqueCommentIds.length - 3} more</span>
              )}
            </div>
          );
        },
      },
      {
        accessorKey: 'should_not_split',
        header: "Don't Split",
        cell: ({ row }) => {
          const index = row.original.index;
          const editingValue = editingData[index]?.should_not_split;
          const value =
            editingValue !== undefined ? editingValue : row.original.should_not_split || false;

          return (
            <Checkbox
              key={`should_not_split_${index}_${value}`}
              checked={value}
              onCheckedChange={checked => {
                // Handle "Don't Split" specific behavior first
                if (checked) {
                  // When "Don't Split" is checked, save original values and clear fields
                  setOriginalValues(prev => ({
                    ...prev,
                    [index]: {
                      handle: editingData[index]?.handle ?? row.original.handle ?? '',
                      knot: editingData[index]?.knot ?? row.original.knot ?? '',
                      validated: editingData[index]?.validated ?? row.original.validated ?? false,
                    },
                  }));

                  // Set all changes at once
                  setEditingData(prev => ({
                    ...prev,
                    [index]: {
                      ...prev[index],
                      should_not_split: true,
                      handle: '',
                      knot: '',
                    },
                  }));
                } else {
                  // When "Don't Split" is unchecked, restore original values
                  const original = originalValues[index];
                  if (original) {
                    // Restore original values and clear the should_not_split change
                    setEditingData(prev => {
                      const newData = { ...prev };
                      if (newData[index]) {
                        // Restore original values
                        newData[index] = {
                          ...newData[index],
                          handle: original.handle,
                          knot: original.knot,
                        };

                        // Clear the should_not_split change since it's back to original
                        delete newData[index].should_not_split;

                        // If no more changes for this row, remove the entire row entry
                        if (Object.keys(newData[index]).length === 0) {
                          delete newData[index];
                        }
                      }
                      return newData;
                    });

                    // Clean up original values
                    setOriginalValues(prev => {
                      const newValues = { ...prev };
                      delete newValues[index];
                      return newValues;
                    });
                  } else {
                    // No original values saved, just clear the should_not_split change
                    setEditingData(prev => {
                      const newData = { ...prev };
                      if (newData[index]) {
                        delete newData[index].should_not_split;
                        // If no more changes for this row, remove the entire row entry
                        if (Object.keys(newData[index]).length === 0) {
                          delete newData[index];
                        }
                      }
                      return newData;
                    });
                  }
                }
              }}
              aria-label={`Don't split for row ${index + 1}`}
            />
          );
        },
      },
    ],
    [handleFieldChange, editingData]
  );

  const tableData = useMemo<BrushSplitWithIndex[]>(() => {
    return brushSplits.map((item, index) => ({
      ...item,
      index,
    }));
  }, [brushSplits]);

  // Create initial row selection based on validation status
  const initialRowSelection = useMemo(() => {
    const selection: Record<string, boolean> = {};
    brushSplits.forEach((split, index) => {
      if (split.validated) {
        selection[index.toString()] = true;
      }
    });
    return selection;
  }, [brushSplits]);

  // Handle empty data
  if (brushSplits.length === 0) {
    return (
      <div className='space-y-4'>
        <div className='text-center py-8 text-muted-foreground'>No brush splits to display</div>
      </div>
    );
  }

  return (
    <div className='space-y-4'>
      <DataTable
        columns={columns}
        data={tableData}
        showPagination={true}
        resizable={true}
        showColumnVisibility={true}
        searchKey='original'
        customControls={customControls}
        onSelectionChange={handleSelectionChange}
        clearSelection={clearSelection} // Pass the clearSelection state
        initialRowSelection={initialRowSelection} // Pass the initial row selection
      />
      {hasUnsavedChanges && (
        <div className='flex justify-between items-center'>
          <span className='text-sm text-muted-foreground'>
            {Object.keys(editingData).length} unsaved change
            {Object.keys(editingData).length !== 1 ? 's' : ''}
          </span>
          <Button onClick={handleSave}>Save All Changes</Button>
        </div>
      )}
    </div>
  );
}
