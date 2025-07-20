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

    useEffect(() => {
        fetch('/api/brush-splits/load')
            .then(response => response.json())
            .then((data: LoadResponse) => {
                setBrushSplits(data.brush_splits);
            })
            .catch(error => {
                console.error('Failed to load brush splits:', error);
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

    return (
        <div data-testid="brush-split-validator">
            <div>Brush Split Validator</div>
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
                            <td>{split.handle}</td>
                            <td>{split.knot}</td>
                            <td>{split.original}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default BrushSplitValidator; 