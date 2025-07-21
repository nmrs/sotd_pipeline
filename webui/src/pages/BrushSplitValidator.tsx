import React, { useState, useEffect } from 'react';
import MonthSelector from '../components/MonthSelector';
import BrushSplitTable from '../components/BrushSplitTable';

interface BrushSplit {
    original: string;
    handle: string | null;
    knot: string;
    match_type?: string;
    validated?: boolean;
    corrected?: boolean;
    validated_at?: string | null;
    system_handle?: string | null;
    system_knot?: string | null;
    system_confidence?: string | null;
    system_reasoning?: string | null;
    occurrences?: any[];
}

interface LoadResponse {
    brush_splits: BrushSplit[];
    statistics: any;
}

const BrushSplitValidator: React.FC = () => {
    const [brushSplits, setBrushSplits] = useState<BrushSplit[]>([]);
    const [selectedRows, setSelectedRows] = useState<Set<number>>(new Set());
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [selectedMonths, setSelectedMonths] = useState<string[]>([]);

    useEffect(() => {
        if (selectedMonths.length === 0) {
            setBrushSplits([]);
            setError(null);
            return;
        }

        setLoading(true);
        setError(null);

        // Build query parameters for the API call
        const queryParams = selectedMonths.map(month => `months=${encodeURIComponent(month)}`).join('&');

        fetch(`/api/brush-splits/load?${queryParams}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then((data: LoadResponse) => {
                setBrushSplits(data.brush_splits);
                setLoading(false);
            })
            .catch(error => {
                console.error('Failed to load brush splits:', error);
                setError('Error loading brush splits');
                setLoading(false);
            });
    }, [selectedMonths]);

    return (
        <div data-testid="brush-split-validator">
            <div>Brush Split Validator</div>

            {/* Month Selection */}
            <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select Months to Analyze:
                </label>
                <MonthSelector
                    selectedMonths={selectedMonths}
                    onMonthsChange={setSelectedMonths}
                    multiple={true}
                />
            </div>

            {loading ? (
                <div>Loading...</div>
            ) : error ? (
                <div>{error}</div>
            ) : selectedMonths.length === 0 ? (
                <div>Please select at least one month to analyze brush splits.</div>
            ) : (
                <>
                    <BrushSplitTable
                        brushSplits={brushSplits}
                        onSelectionChange={(selectedIndices) => {
                            setSelectedRows(new Set(selectedIndices));
                        }}
                        onSave={(index, updatedData) => {
                            const newSplits = [...brushSplits];
                            newSplits[index] = { ...newSplits[index], ...updatedData };
                            setBrushSplits(newSplits);
                        }}
                        isLoading={loading}
                        hasError={!!error}
                        height={600}
                    />

                    <div className="mt-4">
                        <p>Total brush splits: {brushSplits.length}</p>
                        <p>Selected months: {selectedMonths.join(', ')}</p>
                    </div>
                </>
            )}
        </div>
    );
};

export default BrushSplitValidator; 