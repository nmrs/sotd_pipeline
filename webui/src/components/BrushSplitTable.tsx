import React, { useState, useMemo } from 'react';
import { FixedSizeList as List } from 'react-window';

interface BrushSplit {
    original: string;
    handle: string | null;
    knot: string;
    match_type?: string;
    validated?: boolean;
    corrected?: boolean;
    should_not_split?: boolean;
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

    // Track unsaved edits
    const [unsavedEdits, setUnsavedEdits] = useState<Set<number>>(new Set());

    // Filter states
    const [matchTypeFilter, setMatchTypeFilter] = useState<string>('');
    const [statusFilter, setStatusFilter] = useState<string>('');

    const filteredBrushSplits = useMemo(() => {
        let filtered = brushSplits;

        // Text search filter
        if (searchTerm) {
            filtered = filtered.filter(split =>
                split.original.toLowerCase().includes(searchTerm.toLowerCase()) ||
                (split.handle?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
                split.knot.toLowerCase().includes(searchTerm.toLowerCase())
            );
        }

        // Match type filter
        if (matchTypeFilter) {
            filtered = filtered.filter(split =>
                (split.match_type || 'none') === matchTypeFilter
            );
        }

        // Status filter
        if (statusFilter) {
            filtered = filtered.filter(split => {
                const status = !split.handle ? 'unmatched' : 'split';
                return status === statusFilter;
            });
        }

        return filtered;
    }, [brushSplits, searchTerm, matchTypeFilter, statusFilter]);

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

    const handleShouldNotSplitChange = (idx: number, value: boolean) => {
        if (onSave) {
            const updatedData = { ...brushSplits[idx] };
            updatedData.should_not_split = value;
            onSave(idx, updatedData);
            // Clear unsaved edit for this row
            setUnsavedEdits(prev => {
                const newSet = new Set(prev);
                newSet.delete(idx);
                return newSet;
            });
        }
    };

    const handleHandleClick = (idx: number, currentValue: string) => {
        setEditingHandle(idx);
        setEditedHandleValue(currentValue);
        setUnsavedEdits(prev => new Set(prev).add(idx));
    };

    const handleKnotClick = (idx: number, currentValue: string) => {
        setEditingKnot(idx);
        setEditedKnotValue(currentValue);
        setUnsavedEdits(prev => new Set(prev).add(idx));
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
            // Clear unsaved edit for this row
            setUnsavedEdits(prev => {
                const newSet = new Set(prev);
                newSet.delete(idx);
                return newSet;
            });
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

    const renderRow = (split: BrushSplit, idx: number) => {
        const hasUnsavedEdits = unsavedEdits.has(idx);
        return (
            <div key={idx} style={{
                display: 'grid',
                gridTemplateColumns: 'auto auto 1fr 1fr 1fr auto auto',
                gap: '8px',
                alignItems: 'center',
                padding: '4px',
                backgroundColor: hasUnsavedEdits ? '#fff3cd' : 'transparent',
                border: hasUnsavedEdits ? '1px solid #ffc107' : 'none',
                borderRadius: hasUnsavedEdits ? '4px' : '0'
            }}>
                <input
                    type="checkbox"
                    role="checkbox"
                    tabIndex={0}
                    checked={selectedIndices.includes(idx)}
                    onChange={() => handleCheckboxChange(idx)}
                />
                <input
                    type="checkbox"
                    role="checkbox"
                    tabIndex={0}
                    checked={split.should_not_split || false}
                    onChange={() => handleShouldNotSplitChange(idx, !split.should_not_split)}
                    title="Mark as should not split"
                />
                <span title={split.original}>{split.original}</span>
                {editingHandle === idx ? (
                    <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                        <input
                            value={editedHandleValue}
                            onChange={(e) => setEditedHandleValue(e.target.value)}
                            autoFocus
                            style={{ flex: 1 }}
                            disabled={split.should_not_split}
                        />
                        <button
                            onClick={() => handleSave(idx, 'handle')}
                            style={{
                                padding: '2px 6px',
                                fontSize: '12px',
                                backgroundColor: '#28a745',
                                color: 'white',
                                border: 'none',
                                borderRadius: '3px',
                                cursor: 'pointer'
                            }}
                            disabled={split.should_not_split}
                        >
                            Save
                        </button>
                        <button
                            onClick={() => {
                                setEditingHandle(null);
                                setEditedHandleValue('');
                                setUnsavedEdits(prev => {
                                    const newSet = new Set(prev);
                                    newSet.delete(idx);
                                    return newSet;
                                });
                            }}
                            style={{
                                padding: '2px 6px',
                                fontSize: '12px',
                                backgroundColor: '#dc3545',
                                color: 'white',
                                border: 'none',
                                borderRadius: '3px',
                                cursor: 'pointer'
                            }}
                        >
                            Cancel
                        </button>
                    </div>
                ) : (
                    <span
                        tabIndex={0}
                        onClick={() => !split.should_not_split && handleHandleClick(idx, split.handle || '')}
                        onKeyDown={(e) => !split.should_not_split && handleSpanKeyDown(idx, 'handle', split.handle || '', e)}
                        style={{
                            color: split.should_not_split ? '#ccc' : (split.handle ? 'inherit' : '#999'),
                            cursor: split.should_not_split ? 'not-allowed' : 'pointer'
                        }}
                    >
                        {split.should_not_split ? '(disabled)' : (split.handle || '(empty)')}
                    </span>
                )}
                {editingKnot === idx ? (
                    <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                        <input
                            value={editedKnotValue}
                            onChange={(e) => setEditedKnotValue(e.target.value)}
                            autoFocus
                            style={{ flex: 1 }}
                            disabled={split.should_not_split}
                        />
                        <button
                            onClick={() => handleSave(idx, 'knot')}
                            style={{
                                padding: '2px 6px',
                                fontSize: '12px',
                                backgroundColor: '#28a745',
                                color: 'white',
                                border: 'none',
                                borderRadius: '3px',
                                cursor: 'pointer'
                            }}
                            disabled={split.should_not_split}
                        >
                            Save
                        </button>
                        <button
                            onClick={() => {
                                setEditingKnot(null);
                                setEditedKnotValue('');
                                setUnsavedEdits(prev => {
                                    const newSet = new Set(prev);
                                    newSet.delete(idx);
                                    return newSet;
                                });
                            }}
                            style={{
                                padding: '2px 6px',
                                fontSize: '12px',
                                backgroundColor: '#dc3545',
                                color: 'white',
                                border: 'none',
                                borderRadius: '3px',
                                cursor: 'pointer'
                            }}
                        >
                            Cancel
                        </button>
                    </div>
                ) : (
                    <span
                        tabIndex={0}
                        onClick={() => !split.should_not_split && handleKnotClick(idx, split.knot)}
                        onKeyDown={(e) => !split.should_not_split && handleSpanKeyDown(idx, 'knot', split.knot, e)}
                        style={{
                            cursor: split.should_not_split ? 'not-allowed' : 'pointer',
                            color: split.should_not_split ? '#ccc' : 'inherit'
                        }}
                    >
                        {split.should_not_split ? '(disabled)' : split.knot}
                    </span>
                )}
                <span style={{
                    fontSize: '12px',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    backgroundColor: split.match_type === 'exact' ? '#e6f3ff' :
                        split.match_type === 'regex' ? '#fff3e6' :
                            split.match_type === 'alias' ? '#f0e6ff' :
                                split.match_type === 'brand' ? '#e6ffe6' : '#f5f5f5',
                    color: split.match_type === 'exact' ? '#0066cc' :
                        split.match_type === 'regex' ? '#cc6600' :
                            split.match_type === 'alias' ? '#6600cc' :
                                split.match_type === 'brand' ? '#006600' : '#666'
                }}>
                    {split.match_type || 'none'}
                </span>
                <span style={{
                    fontSize: '12px',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    backgroundColor: split.should_not_split ? '#ffe6cc' : (!split.handle ? '#ffe6e6' : '#e6ffe6'),
                    color: split.should_not_split ? '#cc6600' : (!split.handle ? '#cc0000' : '#006600')
                }}>
                    {split.should_not_split ? 'no-split' : (!split.handle ? 'unmatched' : 'split')}
                </span>
            </div>
        );
    };

    return (
        <div data-testid="brush-split-table">
            <input
                type="text"
                placeholder="Search..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{ marginBottom: '8px', width: '100%', padding: '4px' }}
            />
            <div style={{
                display: 'flex',
                gap: '8px',
                marginBottom: '8px'
            }}>
                <button
                    onClick={() => setMatchTypeFilter('')}
                    style={{
                        padding: '4px 8px',
                        fontSize: '12px',
                        backgroundColor: matchTypeFilter ? '#28a745' : '#f8f9fa',
                        color: matchTypeFilter ? 'white' : '#333',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        cursor: 'pointer'
                    }}
                >
                    Filter Match Type
                </button>
                <button
                    onClick={() => setStatusFilter('')}
                    style={{
                        padding: '4px 8px',
                        fontSize: '12px',
                        backgroundColor: statusFilter ? '#28a745' : '#f8f9fa',
                        color: statusFilter ? 'white' : '#333',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        cursor: 'pointer'
                    }}
                >
                    Filter Status
                </button>
            </div>
            <div style={{
                display: 'grid',
                gridTemplateColumns: 'auto auto 1fr 1fr 1fr auto auto',
                gap: '8px',
                alignItems: 'center',
                padding: '4px',
                fontWeight: 'bold',
                borderBottom: '1px solid #ccc',
                marginBottom: '4px'
            }}>
                <span>Select</span>
                <span>Should Not Split</span>
                <span>Original</span>
                <span>Handle</span>
                <span>Knot</span>
                <span>Match Type</span>
                <span>Status</span>
            </div>
            {shouldUseVirtualization ? (
                <List
                    height={height - 60}
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