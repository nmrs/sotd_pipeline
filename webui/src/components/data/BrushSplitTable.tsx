import React, { useState, useMemo, useCallback } from 'react';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { BrushSplit } from '../../types/brushSplit';

// Extended interface for table data
interface BrushSplitTableData extends BrushSplit {
  index: number;
  should_not_split?: boolean;
}

// Extended interface for editing data
interface EditingData {
  handle?: string | null;
  knot?: string;
  should_not_split?: boolean;
}

interface BrushSplitTableProps {
  brushSplits: BrushSplit[];
  onSave?: (index: number, updatedSplit: BrushSplit) => void;
  onSelectionChange?: (selectedIndices: number[]) => void;
  selectedIndices?: number[];
}

const BrushSplitTable: React.FC<BrushSplitTableProps> = ({
  brushSplits,
  onSave,
  onSelectionChange,
  selectedIndices = [],
}) => {
  const [editingData, setEditingData] = useState<Record<number, EditingData>>({});

  // Memoize table data to prevent unnecessary re-renders
  const tableData = useMemo(() => {
    return brushSplits.map((split, index) => ({
      ...split,
      index,
      should_not_split: false, // Default value since it's not in the original interface
    }));
  }, [brushSplits]);

  // Memoize unsaved changes count
  const unsavedChangesCount = useMemo(() => {
    return Object.keys(editingData).length;
  }, [editingData]);

  // Memoize handle selection change
  const handleSelectionChange = useCallback(
    (indices: number[]) => {
      if (onSelectionChange) {
        onSelectionChange(indices);
      }
    },
    [onSelectionChange]
  );

  // Memoize handle save all changes
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

  // Memoize handle field change
  const handleFieldChange = useCallback((index: number, field: keyof EditingData, value: any) => {
    setEditingData(prev => ({
      ...prev,
      [index]: {
        ...prev[index],
        [field]: value,
      },
    }));
  }, []);

  return (
    <div className='space-y-4' data-testid='brush-split-table'>
      {unsavedChangesCount > 0 && (
        <div className='flex justify-between items-center p-4 bg-blue-50 border border-blue-200 rounded-lg'>
          <span className='text-blue-800'>
            {unsavedChangesCount} unsaved change{unsavedChangesCount !== 1 ? 's' : ''}
          </span>
          <Button
            onClick={handleSaveAllChanges}
            className='bg-blue-600 hover:bg-blue-700 text-white'
          >
            Save All Changes
          </Button>
        </div>
      )}

      <div className='rounded-md border'>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className='w-12'></TableHead>
              <TableHead>Original</TableHead>
              <TableHead>Handle</TableHead>
              <TableHead>Knot</TableHead>
              <TableHead>Should Not Split</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {tableData.map(item => {
              const isEditing = editingData[item.index];
              const handleDisplayValue =
                isEditing?.handle !== undefined ? isEditing.handle : item.handle;
              const knotDisplayValue = isEditing?.knot !== undefined ? isEditing.knot : item.knot;
              const shouldNotSplitValue =
                isEditing?.should_not_split !== undefined
                  ? isEditing.should_not_split
                  : item.should_not_split;

              return (
                <TableRow key={item.index}>
                  <TableCell>
                    <Checkbox
                      checked={selectedIndices.includes(item.index)}
                      onCheckedChange={checked => {
                        const newSelected = checked
                          ? [...selectedIndices, item.index]
                          : selectedIndices.filter(i => i !== item.index);
                        handleSelectionChange(newSelected);
                      }}
                    />
                  </TableCell>
                  <TableCell>
                    <div className='text-sm text-gray-600 max-w-xs truncate' title={item.original}>
                      {item.original}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Input
                      value={handleDisplayValue || ''}
                      placeholder='Click to edit'
                      onChange={e => handleFieldChange(item.index, 'handle', e.target.value)}
                      className='text-sm'
                    />
                  </TableCell>
                  <TableCell>
                    <Input
                      value={knotDisplayValue || ''}
                      placeholder='Click to edit'
                      onChange={e => handleFieldChange(item.index, 'knot', e.target.value)}
                      className='text-sm'
                    />
                  </TableCell>
                  <TableCell>
                    <Checkbox
                      checked={shouldNotSplitValue}
                      onCheckedChange={checked =>
                        handleFieldChange(item.index, 'should_not_split', checked)
                      }
                    />
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};

BrushSplitTable.displayName = 'BrushSplitTable';

export default BrushSplitTable;
