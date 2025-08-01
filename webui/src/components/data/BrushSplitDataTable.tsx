'use client';

import React, { useCallback, useMemo, useState, memo, useEffect, useRef } from 'react';
import { ColumnDef } from '@tanstack/react-table';
import { DataTable } from '@/components/ui/data-table';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { BrushSplit } from '@/types/brushSplit';

interface BrushSplitDataTableProps {
  brushSplits: BrushSplit[];
  onSave: (data: BrushSplit[]) => void;
  onSelectionChange?: (selectedRows: BrushSplit[]) => void;
  onCommentClick?: (commentId: string) => void;
  customControls?: React.ReactNode;
  commentLoading?: boolean;
  onUnsavedChangesChange?: (hasChanges: boolean) => void;
}

// Extended type for table data with index
type BrushSplitWithIndex = BrushSplit & { index: number };

// Memoized input component to prevent unnecessary re-renders
const MemoizedInput = memo<{
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  'aria-label': string;
  className?: string;
  disabled?: boolean;
}>(({ value, onChange, placeholder, 'aria-label': ariaLabel, className, disabled }) => {
  const [localValue, setLocalValue] = useState(value);

  // Update local value when prop changes
  useEffect(() => {
    setLocalValue(value);
  }, [value]);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setLocalValue(e.target.value);
  }, []);

  const handleBlur = useCallback(() => {
    onChange(localValue);
  }, [onChange, localValue]);

  return (
    <Input
      value={localValue}
      onChange={handleChange}
      onBlur={handleBlur}
      placeholder={placeholder}
      aria-label={ariaLabel}
      className={className}
      disabled={disabled}
    />
  );
});

MemoizedInput.displayName = 'MemoizedInput';

export function BrushSplitDataTable({
  brushSplits,
  onSave,
  customControls,
  commentLoading = false,
  onUnsavedChangesChange,
}: BrushSplitDataTableProps) {
  const [editingData, setEditingData] = useState<Record<number, Partial<BrushSplit>>>({});

  // Track original values before "Don't Split" was checked
  const [originalValues, setOriginalValues] = useState<
    Record<number, { handle: string | null; knot: string; validated: boolean }>
  >({});

  // Use ref to access current brushSplits without causing re-renders
  const brushSplitsRef = useRef(brushSplits);
  brushSplitsRef.current = brushSplits;

  const handleFieldChange = useCallback(
    (index: number, field: keyof BrushSplit, value: string | boolean | null) => {
      const originalValue = brushSplitsRef.current[index][field];

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
    [] // No dependencies needed since we use ref
  );

  const handleSave = useCallback(() => {
    // Only send validated splits to the API
    const validatedData = brushSplits
      .map((item, index) => {
        const editingChanges = editingData[index] || {};
        const isEdited = Object.keys(editingChanges).length > 0;
        const wasValidated = item.validated;

        // Only include splits that are validated (edited or previously validated)
        const isValidated = isEdited || wasValidated;

        if (!isValidated) {
          return null; // Skip unvalidated splits
        }

        return {
          ...item,
          ...editingChanges,
          // Mark as validated if the row is edited
          validated: true,
        };
      })
      .filter(Boolean) as BrushSplit[]; // Remove null entries

    // Only call onSave if there are validated splits to save
    if (validatedData.length > 0) {
      onSave(validatedData);
    }

    setEditingData({});
    setOriginalValues({});
  }, [brushSplits, editingData, onSave]);

  const hasUnsavedChanges = Object.keys(editingData).length > 0;

  // Notify parent component of unsaved changes
  useEffect(() => {
    onUnsavedChangesChange?.(hasUnsavedChanges);
  }, [hasUnsavedChanges, onUnsavedChangesChange]);

  const columns = useMemo<ColumnDef<BrushSplitWithIndex>[]>(
    () => [
      {
        accessorKey: 'original',
        header: 'Original Text',
        size: 300,
        cell: ({ row }) => {
          const item = row.original;
          return (
            <div className='max-w-md'>
              <div className='font-medium'>{item.original}</div>
              {item.occurrences && item.occurrences.length > 0 && (
                <div className='text-sm text-muted-foreground'>
                  {item.occurrences.length} occurrence{item.occurrences.length !== 1 ? 's' : ''}
                </div>
              )}
            </div>
          );
        },
      },
      {
        accessorKey: 'handle',
        header: 'Handle',
        size: 200,
        cell: ({ row }) => {
          const item = row.original;
          const isEditing = editingData[item.index];
          const originalValue = originalValues[item.index];
          const currentValue = isEditing?.handle ?? item.handle;
          const hasChanges = isEditing && isEditing.handle !== item.handle;

          return (
            <div className='flex items-center space-x-2'>
              <MemoizedInput
                value={currentValue || ''}
                onChange={value => handleFieldChange(item.index, 'handle', value)}
                className={`w-full ${hasChanges ? 'border-orange-500 bg-orange-50' : ''} ${
                  originalValue && originalValue.handle !== item.handle
                    ? 'border-blue-500 bg-blue-50'
                    : ''
                }`}
                placeholder='Handle'
                aria-label={`Handle for ${item.original}`}
                disabled={commentLoading}
              />
              {hasChanges && (
                <Button
                  variant='ghost'
                  size='sm'
                  onClick={() => {
                    // Restore original value
                    if (originalValue) {
                      handleFieldChange(item.index, 'handle', originalValue.handle);
                    } else {
                      handleFieldChange(item.index, 'handle', item.handle);
                    }
                  }}
                  className='text-orange-600 hover:text-orange-700'
                >
                  ↺
                </Button>
              )}
            </div>
          );
        },
      },
      {
        accessorKey: 'knot',
        header: 'Knot',
        size: 200,
        cell: ({ row }) => {
          const item = row.original;
          const isEditing = editingData[item.index];
          const originalValue = originalValues[item.index];
          const currentValue = isEditing?.knot ?? item.knot;
          const hasChanges = isEditing && isEditing.knot !== item.knot;

          return (
            <div className='flex items-center space-x-2'>
              <MemoizedInput
                value={currentValue || ''}
                onChange={value => handleFieldChange(item.index, 'knot', value)}
                className={`w-full ${hasChanges ? 'border-orange-500 bg-orange-50' : ''} ${
                  originalValue && originalValue.knot !== item.knot
                    ? 'border-blue-500 bg-blue-50'
                    : ''
                }`}
                placeholder='Knot'
                aria-label={`Knot for ${item.original}`}
                disabled={commentLoading}
              />
              {hasChanges && (
                <Button
                  variant='ghost'
                  size='sm'
                  onClick={() => {
                    // Restore original value
                    if (originalValue) {
                      handleFieldChange(item.index, 'knot', originalValue.knot);
                    } else {
                      handleFieldChange(item.index, 'knot', item.knot);
                    }
                  }}
                  className='text-orange-600 hover:text-orange-700'
                >
                  ↺
                </Button>
              )}
            </div>
          );
        },
      },
      {
        accessorKey: 'validated',
        header: 'Validated',
        size: 120,
        cell: ({ row }) => {
          const item = row.original;
          const isEditing = editingData[item.index];
          const currentValue = isEditing?.validated ?? item.validated;

          return (
            <div className='flex items-center space-x-2'>
              <Checkbox
                checked={currentValue}
                onCheckedChange={checked => {
                  handleFieldChange(item.index, 'validated', checked);
                }}
                disabled={commentLoading}
                aria-label={`Validated for row ${item.index + 1}`}
              />
              <span className='text-sm text-muted-foreground'>{currentValue ? 'Yes' : 'No'}</span>
            </div>
          );
        },
      },
      {
        accessorKey: 'should_not_split',
        header: "Don't Split",
        size: 120,
        cell: ({ row }) => {
          const item = row.original;
          const isEditing = editingData[item.index];
          const currentValue = isEditing?.should_not_split ?? item.should_not_split;

          return (
            <Checkbox
              checked={currentValue}
              onCheckedChange={checked => {
                if (checked) {
                  // When "Don't Split" is checked, save original values and clear handle/knot
                  const original = {
                    handle: item.handle,
                    knot: item.knot,
                    validated: item.validated,
                  };
                  setOriginalValues(prev => ({ ...prev, [item.index]: original }));

                  setEditingData(prev => ({
                    ...prev,
                    [item.index]: {
                      ...prev[item.index],
                      should_not_split: true,
                      handle: null,
                      knot: item.original, // Use original text as knot
                      validated: false, // Reset validation when splitting is disabled
                    },
                  }));
                } else {
                  // When "Don't Split" is unchecked, restore original values
                  const original = originalValues[item.index];
                  if (original) {
                    // Restore original values and clear the should_not_split change
                    setEditingData(prev => {
                      const newData = { ...prev };
                      if (newData[item.index]) {
                        // Restore original values including validated state
                        newData[item.index] = {
                          ...newData[item.index],
                          handle: original.handle,
                          knot: original.knot,
                          validated: original.validated, // Restore original validated state
                        };

                        // Clear the should_not_split change since it's back to original
                        delete newData[item.index].should_not_split;

                        // If no more changes for this row, remove the entire row entry
                        if (Object.keys(newData[item.index]).length === 0) {
                          delete newData[item.index];
                        }
                      }
                      return newData;
                    });

                    // Clean up original values
                    setOriginalValues(prev => {
                      const newValues = { ...prev };
                      delete newValues[item.index];
                      return newValues;
                    });
                  } else {
                    // No original values saved, just clear the should_not_split change
                    setEditingData(prev => {
                      const newData = { ...prev };
                      if (newData[item.index]) {
                        delete newData[item.index].should_not_split;
                        // If no more changes for this row, remove the entire row entry
                        if (Object.keys(newData[item.index]).length === 0) {
                          delete newData[item.index];
                        }
                      }
                      return newData;
                    });
                  }
                }
              }}
              aria-label={`Don't split for row ${item.index + 1}`}
            />
          );
        },
      },
    ],
    [handleFieldChange, editingData, originalValues, commentLoading]
  );

  const tableData = useMemo<BrushSplitWithIndex[]>(() => {
    return brushSplits.map((item, index) => ({
      ...item,
      index,
    }));
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
    <div className='space-y-4 w-full'>
      <DataTable
        columns={columns}
        data={tableData}
        showPagination={true}
        resizable={true}
        sortable={true}
        showColumnVisibility={true}
        searchKey='original'
        customControls={customControls}
        initialPageSize={50}
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
