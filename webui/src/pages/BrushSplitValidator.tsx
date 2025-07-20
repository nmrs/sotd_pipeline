import React, { useState, useCallback } from 'react';
import MonthSelector from '../components/MonthSelector';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorDisplay from '../components/ErrorDisplay';
import BrushSplitTable from '../components/BrushSplitTable';
import { handleApiError } from '../services/api';

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

interface BrushSplitStatistics {
    total: number;
    validated: number;
    corrected: number;
    validation_percentage: number;
    correction_percentage: number;
    split_types: Record<string, number>;
    confidence_breakdown: Record<string, number>;
    month_breakdown: Record<string, number>;
    recent_activity: Record<string, any>;
}

interface LoadResponse {
    brush_splits: BrushSplit[];
    statistics: BrushSplitStatistics;
}

const BrushSplitValidator: React.FC = () => {
    const [selectedMonths, setSelectedMonths] = useState<string[]>([]);
    const [brushSplits, setBrushSplits] = useState<BrushSplit[]>([]);
    const [statistics, setStatistics] = useState<BrushSplitStatistics | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Load brush splits when months are selected
    const loadBrushSplits = useCallback(async (months: string[]) => {
        if (months.length === 0) {
            setBrushSplits([]);
            setStatistics(null);
            return;
        }

        try {
            setLoading(true);
            setError(null);

            // Build query parameters
            const params = new URLSearchParams();
            months.forEach(month => params.append('months', month));

            const response = await fetch(`/api/brush-splits/load?${params.toString()}`);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }

            const data: LoadResponse = await response.json();
            setBrushSplits(data.brush_splits);
            setStatistics(data.statistics);
        } catch (err: any) {
            const errorMessage = handleApiError(err);
            setError(errorMessage);
            console.error('Failed to load brush splits:', err);
        } finally {
            setLoading(false);
        }
    }, []);

    // Handle month selection changes
    const handleMonthsChange = useCallback((months: string[]) => {
        setSelectedMonths(months);
        loadBrushSplits(months);
    }, [loadBrushSplits]);

    // Format statistics for display
    const formatStatistics = (stats: BrushSplitStatistics) => {
        return {
            total: stats.total.toLocaleString(),
            validated: stats.validated.toLocaleString(),
            corrected: stats.corrected.toLocaleString(),
            validationPercentage: stats.validation_percentage.toFixed(1),
            correctionPercentage: stats.correction_percentage.toFixed(1),
            splitTypes: Object.entries(stats.split_types)
                .filter(([_, count]) => count > 0)
                .map(([type, count]) => `${type}: ${count}`)
                .join(', '),
            confidenceBreakdown: Object.entries(stats.confidence_breakdown)
                .filter(([_, count]) => count > 0)
                .map(([level, count]) => `${level}: ${count}`)
                .join(', '),
        };
    };

    return (
        <div className="max-w-6xl mx-auto px-6 py-8">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">
                    Brush Split Validator
                </h1>
                <p className="text-gray-600">
                    Validate and correct brush string splits from matched data. Select months to load brush strings for validation.
                </p>
            </div>

            {/* Month Selector */}
            <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select Months
                </label>
                <MonthSelector
                    selectedMonths={selectedMonths}
                    onMonthsChange={handleMonthsChange}
                    multiple={true}
                />
            </div>

            {/* Loading State */}
            {loading && (
                <div className="flex justify-center py-8">
                    <LoadingSpinner message="Loading brush splits..." />
                </div>
            )}

            {/* Error State */}
            {error && (
                <div className="mb-6">
                    <ErrorDisplay
                        error={error}
                        onRetry={() => loadBrushSplits(selectedMonths)}
                    />
                </div>
            )}

            {/* Statistics Display */}
            {statistics && !loading && (
                <div className="mb-6 bg-white rounded-lg shadow p-6">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">
                        Validation Statistics
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        <div className="bg-blue-50 p-4 rounded-lg">
                            <div className="text-2xl font-bold text-blue-600">
                                {formatStatistics(statistics).total}
                            </div>
                            <div className="text-sm text-blue-700">Total Splits</div>
                        </div>
                        <div className="bg-green-50 p-4 rounded-lg">
                            <div className="text-2xl font-bold text-green-600">
                                {formatStatistics(statistics).validated}
                            </div>
                            <div className="text-sm text-green-700">Validated</div>
                        </div>
                        <div className="bg-yellow-50 p-4 rounded-lg">
                            <div className="text-2xl font-bold text-yellow-600">
                                {formatStatistics(statistics).correctionPercentage}%
                            </div>
                            <div className="text-sm text-yellow-700">Correction Rate</div>
                        </div>
                        <div className="bg-purple-50 p-4 rounded-lg">
                            <div className="text-2xl font-bold text-purple-600">
                                {formatStatistics(statistics).validationPercentage}%
                            </div>
                            <div className="text-sm text-purple-700">Validation Progress</div>
                        </div>
                    </div>

                    {formatStatistics(statistics).splitTypes && (
                        <div className="mt-4">
                            <h3 className="text-sm font-medium text-gray-700 mb-2">Split Types</h3>
                            <p className="text-sm text-gray-600">
                                {formatStatistics(statistics).splitTypes}
                            </p>
                        </div>
                    )}

                    {formatStatistics(statistics).confidenceBreakdown && (
                        <div className="mt-4">
                            <h3 className="text-sm font-medium text-gray-700 mb-2">Confidence Breakdown</h3>
                            <p className="text-sm text-gray-600">
                                {formatStatistics(statistics).confidenceBreakdown}
                            </p>
                        </div>
                    )}
                </div>
            )}

            {/* Brush Splits Table */}
            {brushSplits.length > 0 && !loading && (
                <div className="mb-6">
                    <div className="mb-4">
                        <h2 className="text-lg font-semibold text-gray-900">
                            Brush Splits ({brushSplits.length.toLocaleString()})
                        </h2>
                        <p className="text-sm text-gray-600 mt-1">
                            Virtualized table with sorting and selection capabilities
                        </p>
                    </div>
                    <BrushSplitTable
                        brushSplits={brushSplits}
                        height={600}
                        itemHeight={60}
                        onSelectionChange={(selectedIndices) => {
                            // TODO: Implement batch operations in Step 13
                            console.log('Selected indices:', selectedIndices);
                        }}
                        onSplitUpdate={(index, updatedSplit) => {
                            // TODO: Implement inline editing in Step 11
                            console.log('Updated split:', index, updatedSplit);
                        }}
                    />
                </div>
            )}

            {/* Empty State */}
            {selectedMonths.length > 0 && brushSplits.length === 0 && !loading && !error && (
                <div className="bg-white rounded-lg shadow p-8 text-center">
                    <div className="text-gray-400 mb-4">
                        <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                    </div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No Brush Splits Found</h3>
                    <p className="text-gray-600">
                        No brush strings were found in the selected months. Try selecting different months or check if the data files exist.
                    </p>
                </div>
            )}

            {/* Initial State */}
            {selectedMonths.length === 0 && !loading && (
                <div className="bg-white rounded-lg shadow p-8 text-center">
                    <div className="text-gray-400 mb-4">
                        <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                    </div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Select Months to Begin</h3>
                    <p className="text-gray-600">
                        Choose one or more months from the dropdown above to load brush strings for validation.
                    </p>
                </div>
            )}
        </div>
    );
};

export default BrushSplitValidator; 