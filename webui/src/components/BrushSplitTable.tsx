import React, { useState, useCallback, useMemo } from 'react';
import { FixedSizeList as List } from 'react-window';

// Types for brush split data
interface BrushSplitOccurrence {
    file: string;
    comment_ids: string[];
}

interface BrushSplit {
    original: string;
    handle: string | null;
    knot: string;
    validated: boolean;
    corrected: boolean;
    validated_at: string | null;
    system_handle: string | null;
    system_knot: string | null;
    system_confidence: string | null;
    system_reasoning: string | null;
    occurrences: BrushSplitOccurrence[];
}

interface BrushSplitTableProps {
    brushSplits: BrushSplit[];
    onSplitUpdate?: (index: number, updatedSplit: BrushSplit) => void;
    onSelectionChange?: (selectedIndices: number[]) => void;
    selectedIndices?: number[];
    height?: number;
    itemHeight?: number;
}

// Row component for the virtualized list
const BrushSplitRow: React.FC<{
    index: number;
    style: React.CSSProperties;
    data: {
        brushSplits: BrushSplit[];
        selectedIndices: number[];
        onSelectionChange?: (selectedIndices: number[]) => void;
        onSplitUpdate?: (index: number, updatedSplit: BrushSplit) => void;
    };
}> = ({ index, style, data }) => {
    const { brushSplits, selectedIndices, onSelectionChange } = data;
    const split = brushSplits[index];
    const isSelected = selectedIndices?.includes(index) || false;

    const handleCheckboxChange = useCallback(() => {
        if (!onSelectionChange) return;

        const newSelectedIndices = isSelected
            ? selectedIndices.filter(i => i !== index)
            : [...(selectedIndices || []), index];

        onSelectionChange(newSelectedIndices);
    }, [index, isSelected, selectedIndices, onSelectionChange]);

    const getConfidenceColor = (confidence: string | null) => {
        switch (confidence?.toLowerCase()) {
            case 'high':
                return 'text-green-600 bg-green-50';
            case 'medium':
                return 'text-yellow-600 bg-yellow-50';
            case 'low':
                return 'text-red-600 bg-red-50';
            default:
                return 'text-gray-600 bg-gray-50';
        }
    };

    const getValidationStatusColor = (validated: boolean, corrected: boolean) => {
        if (validated && corrected) return 'text-blue-600 bg-blue-50';
        if (validated) return 'text-green-600 bg-green-50';
        return 'text-gray-600 bg-gray-50';
    };

    return (
        <div
            style={style}
            className={`flex items-center border-b border-gray-200 hover:bg-gray-50 ${isSelected ? 'bg-blue-50' : ''
                }`}
        >
            {/* Checkbox */}
            <div className="w-12 p-3">
                <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={handleCheckboxChange}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
            </div>

            {/* Original String */}
            <div className="flex-1 p-3 min-w-0">
                <div className="text-sm font-medium text-gray-900 truncate" title={split.original}>
                    {split.original}
                </div>
            </div>

            {/* Handle */}
            <div className="w-32 p-3 min-w-0">
                <div className="text-sm text-gray-900 truncate" title={split.handle || 'N/A'}>
                    {split.handle || 'N/A'}
                </div>
            </div>

            {/* Knot */}
            <div className="w-32 p-3 min-w-0">
                <div className="text-sm text-gray-900 truncate" title={split.knot}>
                    {split.knot}
                </div>
            </div>

            {/* Confidence */}
            <div className="w-24 p-3">
                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getConfidenceColor(split.system_confidence)}`}>
                    {split.system_confidence || 'N/A'}
                </span>
            </div>

            {/* Validation Status */}
            <div className="w-32 p-3">
                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getValidationStatusColor(split.validated, split.corrected)}`}>
                    {split.validated ? (split.corrected ? 'Corrected' : 'Validated') : 'Pending'}
                </span>
            </div>

            {/* Occurrences Count */}
            <div className="w-20 p-3 text-right">
                <span className="text-sm text-gray-600">
                    {split.occurrences.length}
                </span>
            </div>
        </div>
    );
};

const BrushSplitTable: React.FC<BrushSplitTableProps> = ({
    brushSplits,
    onSplitUpdate,
    onSelectionChange,
    selectedIndices = [],
    height = 600,
    itemHeight = 60
}) => {
    const [sortConfig, setSortConfig] = useState<{
        key: keyof BrushSplit;
        direction: 'asc' | 'desc';
    } | null>(null);

    // Sort brush splits based on current sort configuration
    const sortedBrushSplits = useMemo(() => {
        if (!sortConfig) return brushSplits;

        return [...brushSplits].sort((a, b) => {
            const aValue = a[sortConfig.key];
            const bValue = b[sortConfig.key];

            if (aValue === null && bValue === null) return 0;
            if (aValue === null) return 1;
            if (bValue === null) return -1;

            const comparison = String(aValue).localeCompare(String(bValue));
            return sortConfig.direction === 'asc' ? comparison : -comparison;
        });
    }, [brushSplits, sortConfig]);

    const handleSort = useCallback((key: keyof BrushSplit) => {
        setSortConfig(current => {
            if (current?.key === key) {
                return {
                    key,
                    direction: current.direction === 'asc' ? 'desc' : 'asc'
                };
            }
            return { key, direction: 'asc' };
        });
    }, []);

    const SortableHeader: React.FC<{
        children: React.ReactNode;
        sortKey: keyof BrushSplit;
        className?: string;
    }> = ({ children, sortKey, className = '' }) => (
        <button
            onClick={() => handleSort(sortKey)}
            className={`flex items-center space-x-1 text-left font-medium text-gray-700 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 ${className}`}
        >
            <span>{children}</span>
            {sortConfig?.key === sortKey && (
                <span className="text-gray-400">
                    {sortConfig.direction === 'asc' ? '↑' : '↓'}
                </span>
            )}
        </button>
    );

    if (brushSplits.length === 0) {
        return (
            <div className="bg-white rounded-lg shadow">
                <div className="p-8 text-center text-gray-500">
                    <p>No brush splits to display</p>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-lg shadow">
            {/* Table Header */}
            <div className="flex items-center border-b border-gray-200 bg-gray-50">
                <div className="w-12 p-3">
                    <input
                        type="checkbox"
                        checked={selectedIndices.length === brushSplits.length && brushSplits.length > 0}
                        onChange={(e) => {
                            if (onSelectionChange) {
                                onSelectionChange(e.target.checked ? brushSplits.map((_, i) => i) : []);
                            }
                        }}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                </div>
                <div className="flex-1 p-3">
                    <SortableHeader sortKey="original">Original String</SortableHeader>
                </div>
                <div className="w-32 p-3">
                    <SortableHeader sortKey="handle">Handle</SortableHeader>
                </div>
                <div className="w-32 p-3">
                    <SortableHeader sortKey="knot">Knot</SortableHeader>
                </div>
                <div className="w-24 p-3">
                    <SortableHeader sortKey="system_confidence">Confidence</SortableHeader>
                </div>
                <div className="w-32 p-3">
                    <SortableHeader sortKey="validated">Status</SortableHeader>
                </div>
                <div className="w-20 p-3 text-right">
                    <SortableHeader sortKey="occurrences">Count</SortableHeader>
                </div>
            </div>

            {/* Virtualized List */}
            <div style={{ height }}>
                <List
                    height={height}
                    width="100%"
                    itemCount={sortedBrushSplits.length}
                    itemSize={itemHeight}
                    itemData={{
                        brushSplits: sortedBrushSplits,
                        selectedIndices,
                        onSelectionChange,
                        onSplitUpdate
                    }}
                >
                    {BrushSplitRow}
                </List>
            </div>

            {/* Summary */}
            <div className="px-6 py-3 border-t border-gray-200 bg-gray-50 text-sm text-gray-600">
                Showing {sortedBrushSplits.length.toLocaleString()} brush splits
                {selectedIndices.length > 0 && (
                    <span className="ml-4">
                        ({selectedIndices.length} selected)
                    </span>
                )}
            </div>
        </div>
    );
};

export default BrushSplitTable;
export type { BrushSplit, BrushSplitOccurrence, BrushSplitTableProps }; 