import React, { useState, useCallback, useMemo } from 'react';
import { FixedSizeList as List } from 'react-window';

// Types for brush split data
interface BrushSplitOccurrence {
    file: string;
    comment_ids: string[];
}

interface BrushSplit {
    original: string;
    handle: string;
    knot: string;
    validated: boolean;
    corrected: boolean;
    validated_at: string;
    system_handle: string;
    system_knot: string;
    system_confidence: string;
    system_reasoning: string;
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

// Search functionality
const useSearchFilter = (brushSplits: BrushSplit[]) => {
    const [searchTerm, setSearchTerm] = useState('');

    const filteredBrushSplits = useMemo(() => {
        if (!searchTerm.trim()) {
            return brushSplits;
        }

        const lowerSearchTerm = searchTerm.toLowerCase();
        return brushSplits.filter(split => {
            // Search across original, handle, and knot fields
            const originalMatch = split.original.toLowerCase().includes(lowerSearchTerm);
            const handleMatch = split.handle?.toLowerCase().includes(lowerSearchTerm) || false;
            const knotMatch = split.knot.toLowerCase().includes(lowerSearchTerm);

            return originalMatch || handleMatch || knotMatch;
        });
    }, [brushSplits, searchTerm]);

    return {
        searchTerm,
        setSearchTerm,
        filteredBrushSplits
    };
};

const EMPTY_SPLIT: BrushSplit = {
    handle: '',
    knot: '',
    original: '',
    occurrences: [],
    system_handle: '',
    system_knot: '',
    system_confidence: '',
    system_reasoning: '',
    validated: false,
    corrected: false,
    validated_at: '',
};

// Row component for the virtualized list
const BrushSplitRow: React.FC<{
    index: number;
    style: React.CSSProperties;
    data: {
        brushSplits: BrushSplit[];
        filteredBrushSplits: BrushSplit[];
        selectedIndices: number[];
        onSelectionChange?: (selectedIndices: number[]) => void;
        onSplitUpdate?: (index: number, updatedSplit: BrushSplit) => void;
        editingState: EditingState | null;
        setEditingState: (state: EditingState | null) => void;
        searchTerm: string;
    };
}> = ({ index, style, data }) => {
    const { brushSplits, filteredBrushSplits, selectedIndices, onSelectionChange, onSplitUpdate, editingState, setEditingState, searchTerm } = data;
    // Always use a split object, even for filtered-out rows
    const split = filteredBrushSplits.find(s => s === brushSplits[index]) || EMPTY_SPLIT;
    const isFilteredOut = split === EMPTY_SPLIT;
    // All hooks must be called with fixed dependencies
    const isSelected = selectedIndices?.includes(index) || false;
    const isEditing = editingState?.rowIndex === index;
    // Use only primitive values in dependencies with stable arrays
    const handleCheckboxChange = useCallback(() => {
        if (!onSelectionChange) return;
        const newSelectedIndices = isSelected
            ? selectedIndices.filter(i => i !== index)
            : [...selectedIndices, index];
        onSelectionChange(newSelectedIndices);
    }, [isSelected, index, selectedIndices?.length || 0, onSelectionChange]);

    // RESTORED WITH STABLE DEPENDENCY ARRAYS
    const handleHandleClick = useCallback(() => {
        setEditingState({ rowIndex: index, field: 'handle', value: split.handle, error: null });
    }, [index, split.handle, setEditingState]);
    const handleKnotClick = useCallback(() => {
        setEditingState({ rowIndex: index, field: 'knot', value: split.knot, error: null });
    }, [index, split.knot, setEditingState]);

    const saveChanges = useCallback(async (newValue: string) => {
        if (!onSplitUpdate || !editingState) return;

        const error = validateField(editingState.field, newValue);
        if (error) {
            setEditingState({ ...editingState, error });
            return;
        }

        const updatedSplit = {
            ...split!,
            [editingState.field]: newValue,
            validated: true,
            corrected: true,
            validated_at: new Date().toISOString()
        };

        await onSplitUpdate(index, updatedSplit);
        setEditingState(null);
    }, [index, editingState?.field || '', editingState?.value || '', onSplitUpdate, split.handle, split.knot]);

    const cancelEdit = useCallback(() => {
        setEditingState(null);
    }, [setEditingState]);

    // Check if this row should be visible (exists in filtered data)
    const shouldShowRow = split && filteredBrushSplits.includes(split);

    // If this row should not be shown, render an empty div to maintain hooks consistency
    if (!shouldShowRow) {
        return <div style={style} data-testid={`virtualized-row-${index}`}></div>;
    }

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

    // RESTORED WITH STABLE DEPENDENCY ARRAYS
    // Handle input key events
    const handleInputKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            saveChanges(e.currentTarget.value);
        } else if (e.key === 'Escape') {
            e.preventDefault();
            cancelEdit();
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
    }, [saveChanges, cancelEdit, editingState?.field || '', index, split.knot]);

    // Handle input change
    const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        setEditingState({
            ...editingState!,
            value: e.target.value,
            error: null
        });
    }, [editingState?.rowIndex || 0, editingState?.field || '', setEditingState]);

    // Handle input blur
    const handleInputBlur = useCallback(() => {
        if (editingState) {
            saveChanges(editingState.value);
        }
    }, [editingState?.value || '', saveChanges]);

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
                        title={split.knot || 'N/A'}
                        onClick={handleKnotClick}
                    >
                        {split.knot || 'N/A'}
                    </div>
                )}
            </div>

            {/* Confidence */}
            <div className="w-24 p-3">
                <span
                    className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getConfidenceColor(split.system_confidence)}`}
                    title={split.system_reasoning || 'No reasoning available'}
                >
                    {split.system_confidence || 'N/A'}
                </span>
            </div>

            {/* Validation Status */}
            <div className="w-32 p-3">
                <span
                    className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getValidationStatusColor(split.validated, split.corrected)}`}
                    title={split.validated ?
                        (split.corrected ?
                            `Corrected on ${new Date(split.validated_at || '').toLocaleDateString()}` :
                            `Validated on ${new Date(split.validated_at || '').toLocaleDateString()}`
                        ) :
                        'Pending validation'
                    }
                >
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

    // Use search filter hook
    const { searchTerm, setSearchTerm, filteredBrushSplits } = useSearchFilter(brushSplits);

    // Sort brush splits based on current sort configuration
    const sortedBrushSplits = useMemo(() => {
        if (!sortConfig) return filteredBrushSplits;

        return [...filteredBrushSplits].sort((a, b) => {
            const aValue = a[sortConfig.key];
            const bValue = b[sortConfig.key];

            if (aValue === null && bValue === null) return 0;
            if (aValue === null) return 1;
            if (bValue === null) return -1;

            const comparison = String(aValue).localeCompare(String(bValue));
            return sortConfig.direction === 'asc' ? comparison : -comparison;
        });
    }, [filteredBrushSplits, sortConfig]);

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

    // Check if we should show empty state
    const showEmptyState = brushSplits.length === 0;
    const showNoResultsState = filteredBrushSplits.length === 0 && searchTerm.trim() !== '';

    return (
        <div className="bg-white rounded-lg shadow">
            {/* Search Input - Always rendered */}
            <div className="p-4 border-b border-gray-200 bg-gray-50">
                <input
                    type="text"
                    placeholder="Search brush splits..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
            </div>

            {/* Empty State */}
            {showEmptyState && (
                <div className="p-8 text-center text-gray-500">
                    <p>No brush splits to display</p>
                </div>
            )}

            {/* No Results State */}
            {showNoResultsState && (
                <div className="p-8 text-center text-gray-500">
                    <p>No brush splits found matching your search.</p>
                </div>
            )}

            {/* Table Header - Always rendered to maintain hooks consistency */}
            <div className="flex items-center border-b border-gray-200 bg-gray-50">
                <div className="w-12 p-3">
                    <input
                        type="checkbox"
                        checked={selectedIndices.length === sortedBrushSplits.length && sortedBrushSplits.length > 0}
                        onChange={(e) => {
                            if (onSelectionChange) {
                                onSelectionChange(e.target.checked ? sortedBrushSplits.map((_, i) => i) : []);
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

            {/* Virtualized List - Always rendered to maintain hooks consistency */}
            <div style={{ height }}>
                <List
                    height={height}
                    width="100%"
                    itemCount={brushSplits.length}
                    itemSize={itemHeight}
                    itemData={{
                        brushSplits, // original, unfiltered
                        filteredBrushSplits: sortedBrushSplits, // filtered/sorted
                        selectedIndices,
                        onSelectionChange,
                        onSplitUpdate,
                        editingState,
                        setEditingState,
                        searchTerm,
                    }}
                >
                    {BrushSplitRow}
                </List>
            </div>

            {/* Summary - Always rendered to maintain hooks consistency */}
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