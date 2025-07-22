import React from 'react';
import { BrushSplitDataTable } from './BrushSplitDataTable';
import { BrushSplit } from '../../types/brushSplit';

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
  return (
    <div data-testid='brush-split-table'>
      <BrushSplitDataTable
        brushSplits={brushSplits}
        onSave={onSave}
        onSelectionChange={onSelectionChange}
        selectedIndices={selectedIndices}
      />
    </div>
  );
};

BrushSplitTable.displayName = 'BrushSplitTable';

export default BrushSplitTable;
