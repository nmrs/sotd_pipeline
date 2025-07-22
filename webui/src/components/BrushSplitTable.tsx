import React, { useState, useMemo } from 'react';
import { FixedSizeList as List } from 'react-window';
import { GenericDataTable, DataTableColumn } from './GenericDataTable';

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

    // Create columns for GenericDataTable
    const columns: DataTableColumn<BrushSplit & { index: number }>[] = [
        {
            key: 'select',
            header: 'Select',
            width: 60,
            render: (_, row) => (
                <input
                    type="checkbox"
                    role="checkbox"
                    tabIndex={0}
                    checked={selectedIndices.includes(row.index)}
                    onChange={() => handleCheckboxChange(row.index)}
                />
            )
        },
        {
            key: 'should_not_split',
            header: 'Should Not Split',
            width: 120,
            render: (_, row) => (
                <input
                    type="checkbox"
                    role="checkbox"
                    tabIndex={0}
                    checked={row.should_not_split || false}
                    onChange={() => handleShouldNotSplitChange(row.index, !row.should_not_split)}
                    title="Mark as should not split"
                />
            )
        },
        {
            key: 'original',
            header: 'Original',
            render: (value, row) => (
                <span title={value} style={{ color: unsavedEdits.has(row.index) ? '#856404' : 'inherit' }}>
                    {value}
                </span>
            )
        },
        {
            key: 'handle',
            header: 'Handle',
            render: (value, row) => {
                if (editingHandle === row.index) {
                    return (
                        <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                            <input
                                value={editedHandleValue}
                                onChange={(e) => setEditedHandleValue(e.target.value)}
                                autoFocus
                                style={{ flex: 1 }}
                                disabled={row.should_not_split}
                            />
                            <button
                                onClick={() => handleSave(row.index, 'handle')}
                                style={{
                                    padding: '2px 6px',
                                    fontSize: '12px',
                                    backgroundColor: '#28a745',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '3px',
                                    cursor: 'pointer'
                                }}
                                disabled={row.should_not_split}
                            >
                                Save
                            </button>
                            <button
                                onClick={() => {
                                    setEditingHandle(null);
                                    setEditedHandleValue('');
                                    setUnsavedEdits(prev => {
                                        const newSet = new Set(prev);
                                        newSet.delete(row.index);
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
                    );
                }
                return (
                    <span
                        tabIndex={0}
                        onClick={() => !row.should_not_split && handleHandleClick(row.index, value || '')}
                        onKeyDown={(e) => !row.should_not_split && handleSpanKeyDown(row.index, 'handle', value || '', e)}
                        style={{
                            color: row.should_not_split ? '#ccc' : (value ? 'inherit' : '#999'),
                            cursor: row.should_not_split ? 'not-allowed' : 'pointer'
                        }}
                    >
                        {row.should_not_split ? '(disabled)' : (value || '(empty)')}
                    </span>
                );
            }
        },
        {
            key: 'knot',
            header: 'Knot',
            render: (value, row) => {
                if (editingKnot === row.index) {
                    return (
                        <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                            <input
                                value={editedKnotValue}
                                onChange={(e) => setEditedKnotValue(e.target.value)}
                                autoFocus
                                style={{ flex: 1 }}
                                disabled={row.should_not_split}
                            />
                            <button
                                onClick={() => handleSave(row.index, 'knot')}
                                style={{
                                    padding: '2px 6px',
                                    fontSize: '12px',
                                    backgroundColor: '#28a745',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '3px',
                                    cursor: 'pointer'
                                }}
                                disabled={row.should_not_split}
                            >
                                Save
                            </button>
                            <button
                                onClick={() => {
                                    setEditingKnot(null);
                                    setEditedKnotValue('');
                                    setUnsavedEdits(prev => {
                                        const newSet = new Set(prev);
                                        newSet.delete(row.index);
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
                    );
                }
                return (
                    <span
                        tabIndex={0}
                        onClick={() => !row.should_not_split && handleKnotClick(row.index, value)}
                        onKeyDown={(e) => !row.should_not_split && handleSpanKeyDown(row.index, 'knot', value, e)}
                        style={{
                            cursor: row.should_not_split ? 'not-allowed' : 'pointer',
                            color: row.should_not_split ? '#ccc' : 'inherit'
                        }}
                    >
                        {row.should_not_split ? '(disabled)' : value}
                    </span>
                );
            }
        },
        {
            key: 'match_type',
            header: 'Match Type',
            width: 100,
            render: (value, row) => (
                <span style={{
                    fontSize: '12px',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    backgroundColor: value === 'exact' ? '#e6f3ff' :
                        value === 'regex' ? '#fff3e6' :
                            value === 'alias' ? '#f0e6ff' :
                                value === 'brand' ? '#e6ffe6' : '#f5f5f5',
                    color: value === 'exact' ? '#0066cc' :
                        value === 'regex' ? '#cc6600' :
                            value === 'alias' ? '#6600cc' :
                                value === 'brand' ? '#006600' : '#666'
                }}>
                    {value || 'none'}
                </span>
            )
        },
        {
            key: 'status',
            header: 'Status',
            width: 100,
            render: (_, row) => {
                const status = row.should_not_split ? 'no-split' : (!row.handle ? 'unmatched' : 'split');
                return (
                    <span style={{
                        fontSize: '12px',
                        padding: '2px 6px',
                        borderRadius: '4px',
                        backgroundColor: row.should_not_split ? '#ffe6cc' : (!row.handle ? '#ffe6e6' : '#e6ffe6'),
                        color: row.should_not_split ? '#cc6600' : (!row.handle ? '#cc0000' : '#006600')
                    }}>
                        {status}
                    </span>
                );
            }
        }
    ];

    // Prepare data with index for GenericDataTable
    const tableData = filteredBrushSplits.map((split, index) => ({
        ...split,
        index
    }));

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

            {shouldUseVirtualization ? (
                <div style={{ height: height - 60 }}>
                    <List
                        height={height - 60}
                        itemCount={tableData.length}
                        itemSize={50}
                        width="100%"
                    >
                        {({ index, style }) => (
                            <div style={style}>
                                <div style={{
                                    display: 'grid',
                                    gridTemplateColumns: 'auto auto 1fr 1fr 1fr auto auto',
                                    gap: '8px',
                                    alignItems: 'center',
                                    padding: '4px',
                                    backgroundColor: unsavedEdits.has(tableData[index].index) ? '#fff3cd' : 'transparent',
                                    border: unsavedEdits.has(tableData[index].index) ? '1px solid #ffc107' : 'none',
                                    borderRadius: unsavedEdits.has(tableData[index].index) ? '4px' : '0'
                                }}>
                                    {columns.map(column => (
                                        <div key={column.key} style={{ width: column.width }}>
                                            {column.render?.(tableData[index][column.key as keyof (typeof tableData[0])], tableData[index]) ||
                                                String(tableData[index][column.key as keyof (typeof tableData[0])] || '')}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </List>
                </div>
            ) : (
                <>
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
                        {columns.map(column => (
                            <span key={column.key}>{column.header}</span>
                        ))}
                    </div>
                    <div>
                        {tableData.map((row) => (
                            <div key={row.index} style={{
                                display: 'grid',
                                gridTemplateColumns: 'auto auto 1fr 1fr 1fr auto auto',
                                gap: '8px',
                                alignItems: 'center',
                                padding: '4px',
                                backgroundColor: unsavedEdits.has(row.index) ? '#fff3cd' : 'transparent',
                                border: unsavedEdits.has(row.index) ? '1px solid #ffc107' : 'none',
                                borderRadius: unsavedEdits.has(row.index) ? '4px' : '0'
                            }}>
                                {columns.map(column => (
                                    <div key={column.key} style={{ width: column.width }}>
                                        {column.render?.(row[column.key as keyof typeof row], row) ||
                                            String(row[column.key as keyof typeof row] || '')}
                                    </div>
                                ))}
                            </div>
                        ))}
                    </div>
                </>
            )}
        </div>
    );
};

export default BrushSplitTable;
export type { BrushSplit }; 