import React, { useEffect, useState } from 'react';

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
    occurrences: any[];
}

interface LoadResponse {
    brush_splits: BrushSplit[];
    statistics: any;
}

const BrushSplitValidator: React.FC = () => {
    const [brushSplits, setBrushSplits] = useState<BrushSplit[]>([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedRows, setSelectedRows] = useState<Set<number>>(new Set());
    const [editingIndex, setEditingIndex] = useState<number | null>(null);
    const [editingField, setEditingField] = useState<'handle' | 'knot' | null>(null);
    const [editValue, setEditValue] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        setLoading(true);
        setError(null);
        fetch('/api/brush-splits/load')
            .then(response => response.json())
            .then((data: LoadResponse) => {
                setBrushSplits(data.brush_splits);
                setLoading(false);
            })
            .catch(error => {
                console.error('Failed to load brush splits:', error);
                setError('Error loading brush splits');
                setLoading(false);
            });
    }, []);

    const filteredSplits = brushSplits.filter(split =>
        split.original.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (split.handle && split.handle.toLowerCase().includes(searchTerm.toLowerCase())) ||
        split.knot.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const handleRowSelection = (index: number) => {
        const newSelectedRows = new Set(selectedRows);
        if (newSelectedRows.has(index)) {
            newSelectedRows.delete(index);
        } else {
            newSelectedRows.add(index);
        }
        setSelectedRows(newSelectedRows);
    };

    const handleCellClick = (index: number, field: 'handle' | 'knot') => {
        setEditingIndex(index);
        setEditingField(field);
        setEditValue(field === 'handle' ? (filteredSplits[index].handle || '') : filteredSplits[index].knot);
    };

    const handleEditChange = (value: string) => {
        setEditValue(value);
    };

    const handleEditBlur = () => {
        if (editingIndex !== null && editingField) {
            const newSplits = [...brushSplits];
            const originalIndex = brushSplits.findIndex(split => split === filteredSplits[editingIndex]);
            if (originalIndex !== -1) {
                if (editingField === 'handle') {
                    newSplits[originalIndex] = { ...newSplits[originalIndex], handle: editValue };
                } else {
                    newSplits[originalIndex] = { ...newSplits[originalIndex], knot: editValue };
                }
                setBrushSplits(newSplits);
            }
        }
        setEditingIndex(null);
        setEditingField(null);
        setEditValue('');
    };

    const renderCell = (split: BrushSplit, index: number, field: 'handle' | 'knot') => {
        const isEditing = editingIndex === index && editingField === field;
        const value = field === 'handle' ? (split.handle || '') : split.knot;

        if (isEditing) {
            return (
                <input
                    type="text"
                    value={editValue}
                    onChange={(e) => handleEditChange(e.target.value)}
                    onBlur={handleEditBlur}
                    autoFocus
                />
            );
        }

        return (
            <span onClick={() => handleCellClick(index, field)} style={{ cursor: 'pointer' }}>
                {value}
            </span>
        );
    };

    return (
        <div data-testid="brush-split-validator">
            <div>Brush Split Validator</div>
            {loading ? (
                <div>Loading...</div>
            ) : error ? (
                <div>{error}</div>
            ) : (
                <>
                    <input
                        type="text"
                        placeholder="Search brush splits..."
                        data-testid="search-input"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                    <table>
                        <thead>
                            <tr>
                                <th>Select</th>
                                <th>Handle</th>
                                <th>Knot</th>
                                <th>Original</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredSplits.map((split, index) => (
                                <tr key={index}>
                                    <td>
                                        <input
                                            type="checkbox"
                                            checked={selectedRows.has(index)}
                                            onChange={() => handleRowSelection(index)}
                                        />
                                    </td>
                                    <td>{renderCell(split, index, 'handle')}</td>
                                    <td>{renderCell(split, index, 'knot')}</td>
                                    <td>{split.original}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </>
            )}
        </div>
    );
};

export default BrushSplitValidator; 