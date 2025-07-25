'use client';

import React from 'react';
import { BrushSplitDataTable } from './BrushSplitDataTable';
import { BrushSplit } from '@/types/brushSplit';

interface BrushSplitTableProps {
  brushSplits: BrushSplit[];
  onSave?: (data: BrushSplit[]) => void;
  onSelectionChange?: (selectedRows: BrushSplit[]) => void;
  customControls?: React.ReactNode;
  onCommentClick?: (commentId: string) => void;
  commentLoading?: boolean;
}

export function BrushSplitTable({
  brushSplits,
  onSave = () => {},
  onSelectionChange,
  customControls,
  onCommentClick,
  commentLoading = false,
}: BrushSplitTableProps) {
  const handleSave = (updatedData: BrushSplit[]) => {
    // Pass the updated data array to the parent onSave callback
    onSave(updatedData);
  };

  return (
    <div className='w-full' data-testid='brush-split-table'>
      <BrushSplitDataTable
        brushSplits={brushSplits}
        onSave={handleSave}
        onSelectionChange={onSelectionChange}
        customControls={customControls}
        onCommentClick={onCommentClick}
        commentLoading={commentLoading}
      />
    </div>
  );
}
