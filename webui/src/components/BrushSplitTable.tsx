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

// Editing state interface
interface EditingState {
    rowIndex: number;
    field: 'handle' | 'knot';
    value: string;
    error: string | null;
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
        editingState: EditingState | null;
        setEditingState: (state: EditingState | null) => void;
    };
}> = ({ index, style, data }) => {
    const { brushSplits, selectedIndices, onSelectionChange, onSplitUpdate, editingState, setEditingState } = data;
    const split = brushSplits[index];
    const isSelected = selectedIndices?.includes(index) || false;
    const isEditing = editingState?.rowIndex === index;

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

    // Validation functions
    const validateField = (field: 'handle' | 'knot', value: string): string | null => {
        if (value.trim() === '') {
            return `${field === 'handle' ? 'Handle' : 'Knot'} cannot be empty`;
        }
        if (value.trim().length < 2) {
            return `${field === 'handle' ? 'Handle' : 'Knot'} must be at least 2 characters`;
        }
        return null;
    };

    // Handle field editing
    const handleHandleClick = useCallback(() => {
        setEditingState({
            rowIndex: index,
            field: 'handle',
            value: split.handle || '',
            error: null
        });
    }, [index, split.handle, setEditingState]);

    const handleKnotClick = useCallback(() => {
        setEditingState({
            rowIndex: index,
            field: 'knot',
            value: split.knot,
            error: null
        });
    }, [index, split.knot, setEditingState]);

    // Save changes
    const saveChanges = useCallback(async (newValue: string) => {
        if (!onSplitUpdate) return;

        const error = validateField(editingState!.field, newValue);
        if (error) {
            setEditingState({
                ...editingState!,
                value: newValue,
                error
            });
            return;
        }

        const updatedSplit: BrushSplit = {
            ...split,
            [editingState!.field]: editingState!.field === 'handle' ? newValue : newValue,
            validated: true,
            corrected: true,
            validated_at: new Date().toISOString()
        };

        // Call parent callback
        onSplitUpdate(index, updatedSplit);

        // Save to backend
        try {
            const response = await fetch('/api/brush-splits/save-split', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    original: updatedSplit.original,
                    handle: updatedSplit.handle,
                    knot: updatedSplit.knot,
                    validated_at: updatedSplit.validated_at,
                }),
            });

            const result = await response.json();

            if (!response.ok) {
                console.error('Failed to save split:', result.detail || 'Unknown error');
                // Don't throw error to avoid breaking the UI flow
            } else if (result.success) {
                console.log('Split saved successfully:', result.message);
            }
        } catch (error) {
            console.error('Error saving split:', error);
            // Don't throw error to avoid breaking the UI flow
        }

        setEditingState(null);
    }, [editingState, onSplitUpdate, index, split, setEditingState]);

    // Handle input key events
    const handleInputKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            saveChanges(e.currentTarget.value);
        } else if (e.key === 'Escape') {
            e.preventDefault();
            setEditingState(null);
        } else if (e.key === 'Tab') {
            e.preventDefault();
            saveChanges(e.currentTarget.value);
            // Move to next field or row
            if (editingState?.field === 'handle') {
                setEditingState({
                    rowIndex: index,
                    field: 'knot',
                    value: split.knot,
                    error: null
                });
            }
        }
    }, [saveChanges, setEditingState, editingState, index, split.knot]);

    // Handle input change
    const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        setEditingState({
            ...editingState!,
            value: e.target.value,
            error: null
        });
    }, [editingState, setEditingState]);

    // Handle input blur
    const handleInputBlur = useCallback(() => {
        if (editingState) {
            saveChanges(editingState.value);
        }
    }, [editingState, saveChanges]);

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
                {isEditing && editingState?.field === 'handle' ? (
                    <div className="relative">
                        <input
                            type="text"
                            value={editingState.value}
                            onChange={handleInputChange}
                            onKeyDown={handleInputKeyDown}
                            onBlur={handleInputBlur}
                            className={`w-full text-sm px-2 py-1 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 ${editingState.error ? 'border-red-500' : 'border-gray-300'
                                }`}
                            autoFocus
                        />
                        {editingState.error && (
                            <div className="absolute top-full left-0 mt-1 text-xs text-red-600 bg-red-50 px-2 py-1 rounded z-10">
                                {editingState.error}
                            </div>
                        )}
                    </div>
                ) : (
                    <div
                        className="text-sm text-gray-900 truncate cursor-pointer hover:bg-gray-100 px-1 py-1 rounded"
                        title={split.handle || 'N/A'}
                        onClick={handleHandleClick}
                    >
                        {split.handle || 'N/A'}
                    </div>
                )}
            </div>

            {/* Knot */}
            <div className="w-32 p-3 min-w-0">
                {isEditing && editingState?.field === 'knot' ? (
                    <div className="relative">
                        <input
                            type="text"
                            value={editingState.value}
                            onChange={handleInputChange}
                            onKeyDown={handleInputKeyDown}
                            onBlur={handleInputBlur}
                            className={`w-full text-sm px-2 py-1 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 ${editingState.error ? 'border-red-500' : 'border-gray-300'
                                }`}
                            autoFocus
                        />
                        {editingState.error && (
                            <div className="absolute top-full left-0 mt-1 text-xs text-red-600 bg-red-50 px-2 py-1 rounded z-10">
                                {editingState.error}
                            </div>
                        )}
                    </div>
                ) : (
                    <div
                        className="text-sm text-gray-900 truncate cursor-pointer hover:bg-gray-100 px-1 py-1 rounded"
                        title={split.knot}
                        onClick={handleKnotClick}
                    >
                        {split.knot}
                    </div>
                )}
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

    const [editingState, setEditingState] = useState<EditingState | null>(null);

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
                        onSplitUpdate,
                        editingState,
                        setEditingState
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