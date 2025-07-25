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
}>(({ value, onChange, placeholder, 'aria-label': ariaLabel }) => {
  const [localValue, setLocalValue] = useState(value);

  // Update local value when prop changes
  useEffect(() => {
    setLocalValue(value);
  }, [value]);

  return (
    <Input
      value={localValue}
      onChange={e => setLocalValue(e.target.value)}
      onBlur={() => onChange(localValue)}
      placeholder={placeholder}
      aria-label={ariaLabel}
      className='w-full'
    />
  );
});

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

  // Track original values before "Don't Split" was checked
  const [originalValues, setOriginalValues] = useState<
    Record<number, { handle: string; knot: string; validated: boolean }>
  >({});

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

  const columns = useMemo<ColumnDef<BrushSplitWithIndex>[]>(
    () => [
      {
        id: 'validated',
        header: ({ table }) => {
          // Get all rows on current page
          const pageRows = table.getRowModel().rows;
          const checkedRows = pageRows.filter(row => {
            const index = row.original.index;
            const editingValue = editingData[index]?.validated;
            return editingValue !== undefined ? editingValue : row.original.validated || false;
          });

          const isAllChecked = pageRows.length > 0 && checkedRows.length === pageRows.length;
          const isIndeterminate = checkedRows.length > 0 && checkedRows.length < pageRows.length;

          return (
            <div className='flex items-center gap-2'>
              <span>Validated</span>
              <Checkbox
                checked={isAllChecked || (isIndeterminate && 'indeterminate')}
                onCheckedChange={checked => {
                  console.log(`Select all validated clicked:`, { checked });
                  pageRows.forEach(row => {
                    const index = row.original.index;
                    handleFieldChange(index, 'validated', !!checked);
                  });
                }}
                aria-label='Select all validated'
              />
            </div>
          );
        },
        cell: ({ row }) => {
          const index = row.original.index;
          const editingValue = editingData[index]?.validated;
          const value = editingValue !== undefined ? editingValue : row.original.validated || false;

          return (
            <Checkbox
              checked={value}
              onCheckedChange={checked => {
                console.log(`Validated checkbox clicked for row ${index}:`, { checked });
                handleFieldChange(index, 'validated', checked);
              }}
              aria-label={`Validated for row ${index + 1}`}
            />
          );
        },
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
          const allCommentIds = (row.original.occurrences || []).flatMap(
            occurrence => occurrence.comment_ids || []
          );
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
        header: ({ table }) => {
          // Get all rows on current page
          const pageRows = table.getRowModel().rows;
          const checkedRows = pageRows.filter(row => {
            const index = row.original.index;
            const editingValue = editingData[index]?.should_not_split;
            return editingValue !== undefined
              ? editingValue
              : row.original.should_not_split || false;
          });

          const isAllChecked = pageRows.length > 0 && checkedRows.length === pageRows.length;
          const isIndeterminate = checkedRows.length > 0 && checkedRows.length < pageRows.length;

          return (
            <div className='flex items-center gap-2'>
              <span>Don't Split</span>
              <Checkbox
                checked={isAllChecked || (isIndeterminate && 'indeterminate')}
                onCheckedChange={checked => {
                  console.log(`Select all Don't Split clicked:`, { checked });
                  pageRows.forEach(row => {
                    const index = row.original.index;
                    // Use the same logic as individual "Don't Split" checkbox
                    if (checked) {
                      // When "Don't Split" is checked, save original values and clear fields
                      setOriginalValues(prev => ({
                        ...prev,
                        [index]: {
                          handle: editingData[index]?.handle ?? row.original.handle ?? '',
                          knot: editingData[index]?.knot ?? row.original.knot ?? '',
                          validated:
                            editingData[index]?.validated ?? row.original.validated ?? false,
                        },
                      }));

                      // Set all changes at once - auto-check validated when "Don't Split" is checked
                      setEditingData(prev => {
                        const newData = {
                          ...prev,
                          [index]: {
                            ...prev[index],
                            should_not_split: true,
                            handle: '',
                            knot: '',
                            validated: true, // Auto-check validated when "Don't Split" is checked
                          },
                        };
                        console.log(`Updated editing data for row ${index}:`, newData[index]);
                        return newData;
                      });
                    } else {
                      // When "Don't Split" is unchecked, restore original values
                      const original = originalValues[index];
                      if (original) {
                        console.log(`Restoring original values for row ${index}:`, original);

                        // Restore original values and clear the should_not_split change
                        setEditingData(prev => {
                          const newData = { ...prev };
                          if (newData[index]) {
                            // Restore original values including validated state
                            newData[index] = {
                              ...newData[index],
                              handle: original.handle,
                              knot: original.knot,
                              validated: original.validated, // Restore original validated state
                            };

                            // Clear the should_not_split change since it's back to original
                            delete newData[index].should_not_split;

                            // If no more changes for this row, remove the entire row entry
                            if (Object.keys(newData[index]).length === 0) {
                              delete newData[index];
                            }
                          }
                          console.log(`Restored editing data for row ${index}:`, newData[index]);
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
                  });
                }}
                aria-label="Select all Don't Split"
              />
            </div>
          );
        },
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
                console.log(`Don't Split checkbox clicked for row ${index}:`, {
                  checked,
                  original: row.original,
                });

                // Handle "Don't Split" specific behavior first
                if (checked) {
                  console.log(`Setting "Don't Split" to true for row ${index}`);

                  // When "Don't Split" is checked, save original values and clear fields
                  setOriginalValues(prev => ({
                    ...prev,
                    [index]: {
                      handle: editingData[index]?.handle ?? row.original.handle ?? '',
                      knot: editingData[index]?.knot ?? row.original.knot ?? '',
                      validated: editingData[index]?.validated ?? row.original.validated ?? false,
                    },
                  }));

                  // Set all changes at once - auto-check validated when "Don't Split" is checked
                  setEditingData(prev => {
                    const newData = {
                      ...prev,
                      [index]: {
                        ...prev[index],
                        should_not_split: true,
                        handle: '',
                        knot: '',
                        validated: true, // Auto-check validated when "Don't Split" is checked
                      },
                    };
                    console.log(`Updated editing data for row ${index}:`, newData[index]);
                    return newData;
                  });
                } else {
                  console.log(`Setting "Don't Split" to false for row ${index}`);

                  // When "Don't Split" is unchecked, restore original values
                  const original = originalValues[index];
                  if (original) {
                    console.log(`Restoring original values for row ${index}:`, original);

                    // Restore original values and clear the should_not_split change
                    setEditingData(prev => {
                      const newData = { ...prev };
                      if (newData[index]) {
                        // Restore original values including validated state
                        newData[index] = {
                          ...newData[index],
                          handle: original.handle,
                          knot: original.knot,
                          validated: original.validated, // Restore original validated state
                        };

                        // Clear the should_not_split change since it's back to original
                        delete newData[index].should_not_split;

                        // If no more changes for this row, remove the entire row entry
                        if (Object.keys(newData[index]).length === 0) {
                          delete newData[index];
                        }
                      }
                      console.log(`Restored editing data for row ${index}:`, newData[index]);
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
      if (split && split.validated) {
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
