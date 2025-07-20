import React, { useState, useMemo } from 'react';
import { FixedSizeList as List } from 'react-window';

interface BrushSplit {
    original: string;
    handle: string;
    knot: string;
}

interface BrushSplitTableProps {
    brushSplits?: BrushSplit[];
    onSelectionChange?: (selectedIndices: number[]) => void;
    onSave?: (index: number, updatedData: BrushSplit) => void;
    isLoading?: boolean;
    hasError?: boolean;
    height?: number;
}

const BrushSplitTable: React.FC<BrushSplitTableProps> = ({
    brushSplits = [],
    onSelectionChange,
    onSave,
    isLoading = false,
    hasError = false,
    height = 400
}) => {
    const [selectedIndices, setSelectedIndices] = useState<number[]>([]);
    const [editingHandle, setEditingHandle] = useState<number | null>(null);
    const [editedHandleValue, setEditedHandleValue] = useState('');
    const [editingKnot, setEditingKnot] = useState<number | null>(null);
    const [editedKnotValue, setEditedKnotValue] = useState('');
    const [searchTerm, setSearchTerm] = useState('');

    const filteredBrushSplits = useMemo(() => {
        if (!searchTerm) return brushSplits;
        return brushSplits.filter(split =>
            split.original.toLowerCase().includes(searchTerm.toLowerCase()) ||
            split.handle.toLowerCase().includes(searchTerm.toLowerCase()) ||
            split.knot.toLowerCase().includes(searchTerm.toLowerCase())
        );
    }, [brushSplits, searchTerm]);

    const shouldUseVirtualization = filteredBrushSplits.length > 100;

    const handleCheckboxChange = (idx: number) => {
        let newSelected: number[];
        if (selectedIndices.includes(idx)) {
            newSelected = selectedIndices.filter(i => i !== idx);
        } else {
            newSelected = [...selectedIndices, idx];
        }
        setSelectedIndices(newSelected);
        if (onSelectionChange) onSelectionChange(newSelected);
    };

    const handleHandleClick = (idx: number, currentValue: string) => {
        setEditingHandle(idx);
        setEditedHandleValue(currentValue);
    };

    const handleKnotClick = (idx: number, currentValue: string) => {
        setEditingKnot(idx);
        setEditedKnotValue(currentValue);
    };

    const handleSave = (idx: number, field: 'handle' | 'knot') => {
        if (onSave) {
            const updatedData = { ...brushSplits[idx] };
            if (field === 'handle') {
                updatedData.handle = editedHandleValue;
                setEditingHandle(null);
            } else {
                updatedData.knot = editedKnotValue;
                setEditingKnot(null);
            }
            onSave(idx, updatedData);
        }
    };

    const handleKeyDown = (idx: number, field: 'handle' | 'knot', e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            handleSave(idx, field);
        }
    };

    const handleSpanKeyDown = (idx: number, field: 'handle' | 'knot', currentValue: string, e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            if (field === 'handle') {
                handleHandleClick(idx, currentValue);
            } else {
                handleKnotClick(idx, currentValue);
            }
        }
    };

    if (isLoading) {
        return (
            <div data-testid="brush-split-table">
                <div>Loading...</div>
            </div>
        );
    }

    if (hasError) {
        return (
            <div data-testid="brush-split-table">
                <div>Error loading data</div>
            </div>
        );
    }

    const renderRow = (split: BrushSplit, idx: number) => (
        <div key={idx}>
            <input
                type="checkbox"
                role="checkbox"
                tabIndex={0}
                checked={selectedIndices.includes(idx)}
                onChange={() => handleCheckboxChange(idx)}
            />
            <span>{split.original}</span>
            {editingHandle === idx ? (
                <input
                    value={editedHandleValue}
                    onChange={(e) => setEditedHandleValue(e.target.value)}
                    onKeyDown={(e) => handleKeyDown(idx, 'handle', e)}
                />
            ) : (
                <span
                    tabIndex={0}
                    onClick={() => handleHandleClick(idx, split.handle)}
                    onKeyDown={(e) => handleSpanKeyDown(idx, 'handle', split.handle, e)}
                >
                    {split.handle}
                </span>
            )}
            {editingKnot === idx ? (
                <input
                    value={editedKnotValue}
                    onChange={(e) => setEditedKnotValue(e.target.value)}
                    onKeyDown={(e) => handleKeyDown(idx, 'knot', e)}
                />
            ) : (
                <span
                    tabIndex={0}
                    onClick={() => handleKnotClick(idx, split.knot)}
                    onKeyDown={(e) => handleSpanKeyDown(idx, 'knot', split.knot, e)}
                >
                    {split.knot}
                </span>
            )}
        </div>
    );

    return (
        <div data-testid="brush-split-table">
            <input
                type="text"
                placeholder="Search..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
            />
            {shouldUseVirtualization ? (
                <List
                    height={height}
                    itemCount={filteredBrushSplits.length}
                    itemSize={50}
                    width="100%"
                >
                    {({ index, style }) => (
                        <div style={style}>
                            {renderRow(filteredBrushSplits[index], index)}
                        </div>
                    )}
                </List>
            ) : (
                filteredBrushSplits.map((split, idx) => renderRow(split, idx))
            )}
        </div>
    );
};

export default BrushSplitTable;
export type { BrushSplit }; 