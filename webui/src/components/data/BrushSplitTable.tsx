'use client';

import React from 'react';
import { BrushSplitDataTable } from './BrushSplitDataTable';
import { BrushSplit } from '@/types/brushSplit';

interface BrushSplitTableProps {
  brushSplits: BrushSplit[];
  onSave?: (data: BrushSplit[]) => void;
  onSelectionChange?: (selectedRows: BrushSplit[]) => void;
}

export function BrushSplitTable({
  brushSplits,
  onSave = () => { },
  onSelectionChange,
}: BrushSplitTableProps) {
  const handleSave = (updatedData: BrushSplit[]) => {
    // Pass the updated data array to the parent onSave callback
    onSave(updatedData);
  };

  return (
    <div className='w-full' data-testid="brush-split-table">
      <BrushSplitDataTable
        brushSplits={brushSplits}
        onSave={handleSave}
        onSelectionChange={onSelectionChange}
      />
    </div>
  );
}
