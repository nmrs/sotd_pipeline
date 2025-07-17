import React, { useState, useEffect } from 'react';
import { analyzeUnmatched, UnmatchedAnalysisResult, handleApiError } from '../services/api';
import MonthSelector from '../components/MonthSelector';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorDisplay from '../components/ErrorDisplay';
import VirtualizedTable from '../components/VirtualizedTable';
import PerformanceMonitor from '../components/PerformanceMonitor';

const UnmatchedAnalyzer: React.FC = () => {
    const [selectedField, setSelectedField] = useState<string>('razor');
    const [selectedMonths, setSelectedMonths] = useState<string[]>([]);
    const [limit, setLimit] = useState<number>(50);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [results, setResults] = useState<UnmatchedAnalysisResult | null>(null);
    const [operationCount, setOperationCount] = useState(0);


    const fieldOptions = [
        { value: 'razor', label: 'Razor' },
        { value: 'blade', label: 'Blade' },
        { value: 'brush', label: 'Brush' },
        { value: 'soap', label: 'Soap' },
    ];

    const handleAnalyze = async () => {
        if (selectedMonths.length === 0) {
            setError('Please select at least one month');
            return;
        }

        try {
            setLoading(true);
            setError(null);
            setResults(null);
            setOperationCount(prev => prev + 1);

            const result = await analyzeUnmatched({
                field: selectedField,
                months: selectedMonths,
                limit,
            });

            // Validate the response structure
            if (result && typeof result === 'object') {
                setResults(result);
            } else {
                throw new Error('Invalid response format from API');
            }
        } catch (err: any) {
            setError(handleApiError(err));
        } finally {
            setLoading(false);
        }
    };

    const formatExamples = (examples: string[]) => {
        if (examples.length === 0) return 'No examples available';
        return examples.slice(0, 3).join(', ') + (examples.length > 3 ? '...' : '');
    };

    useEffect(() => {
        if (results) {
            // eslint-disable-next-line no-console
            console.log('UnmatchedAnalyzer results:', results);
        }
    }, [results]);

    return (
        <div className="max-w-6xl mx-auto p-6">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">Unmatched Item Analyzer</h1>
                <p className="text-gray-600">
                    Analyze unmatched items across selected months to identify patterns and potential catalog additions.
                </p>
            </div>

            {/* Configuration Panel - Compact at top */}
            <div className="mb-8">
                <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="text-xl font-semibold text-gray-900 mb-4">Analysis Configuration</h2>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {/* Field Selection */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Product Field
                            </label>
                            <select
                                value={selectedField}
                                onChange={(e) => setSelectedField(e.target.value)}
                                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            >
                                {fieldOptions.map((option) => (
                                    <option key={option.value} value={option.value}>
                                        {option.label}
                                    </option>
                                ))}
                            </select>
                        </div>

                        {/* Month Selection */}
                        <div>
                            <MonthSelector
                                selectedMonths={selectedMonths}
                                onMonthsChange={setSelectedMonths}
                                label="Select Months to Analyze"
                            />
                        </div>

                        {/* Limit Selection */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Result Limit
                            </label>
                            <input
                                type="number"
                                value={limit}
                                onChange={(e) => setLimit(parseInt(e.target.value) || 50)}
                                min="1"
                                max="1000"
                                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            />
                            <p className="text-xs text-gray-500 mt-1">
                                Maximum number of unmatched items to return (1-1000)
                            </p>
                        </div>
                    </div>

                    {/* Analyze Button and Performance Monitor */}
                    <div className="mt-6 flex items-center justify-between">
                        <button
                            onClick={handleAnalyze}
                            disabled={loading || selectedMonths.length === 0}
                            className="bg-blue-600 text-white py-2 px-6 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? 'Analyzing...' : 'Analyze Unmatched Items'}
                        </button>

                        {/* Performance Monitor */}
                        <PerformanceMonitor
                            dataSize={results?.unmatched_items?.length || 0}
                            operationCount={operationCount}
                        />
                    </div>
                </div>
            </div>

            {/* Results Panel - Full width */}
            <div className="space-y-6">
                {error && (
                    <ErrorDisplay error={error} onRetry={() => setError(null)} />
                )}

                {loading && (
                    <div className="bg-white rounded-lg shadow p-6">
                        <LoadingSpinner message="Analyzing unmatched items..." />
                    </div>
                )}

                {results && (
                    <div className="bg-white rounded-lg shadow">
                        <div className="px-6 py-4 border-b border-gray-200">
                            <h2 className="text-xl font-semibold text-gray-900">Analysis Results</h2>
                            <p className="text-sm text-gray-600 mt-1">
                                Field: {results.field || 'Unknown'} | Months: {results.months?.join(', ') || 'None'} |
                                Total Unmatched: {results.total_unmatched || 0} |
                                Processing Time: {results.processing_time?.toFixed(2) || '0.00'}s
                            </p>
                        </div>

                        <div className="p-6">
                            {Array.isArray(results.unmatched_items) ? (
                                results.unmatched_items.length === 0 ? (
                                    <div className="text-center py-8">
                                        <div className="text-green-600 text-6xl mb-4">✓</div>
                                        <h3 className="text-lg font-medium text-gray-900 mb-2">No Unmatched Items Found</h3>
                                        <p className="text-gray-600">
                                            All {results.field} items in the selected months were successfully matched to the catalog.
                                        </p>
                                    </div>
                                ) : (
                                    <div className="space-y-4">
                                        <h3 className="text-lg font-medium text-gray-900">
                                            Top Unmatched Items ({results.unmatched_items.length})
                                        </h3>
                                        <VirtualizedTable
                                            data={results.unmatched_items}
                                            columns={[
                                                {
                                                    key: 'item',
                                                    header: 'Item',
                                                    width: 300,
                                                    render: (item) => (
                                                        <span className="font-medium text-gray-900">
                                                            {item.item}
                                                        </span>
                                                    ),
                                                },
                                                {
                                                    key: 'count',
                                                    header: 'Count',
                                                    width: 100,
                                                    render: (item) => (
                                                        <span className="text-gray-500">
                                                            {item.count}
                                                        </span>
                                                    ),
                                                },
                                                {
                                                    key: 'examples',
                                                    header: 'Examples',
                                                    width: 400,
                                                    render: (item) => (
                                                        <span className="text-gray-500">
                                                            {formatExamples(item.examples)}
                                                        </span>
                                                    ),
                                                },
                                            ]}
                                            height={400}
                                            rowHeight={48}
                                        />
                                    </div>
                                )
                            ) : (
                                <div className="text-center py-8">
                                    <div className="text-red-600 text-6xl mb-4">!</div>
                                    <h3 className="text-lg font-medium text-gray-900 mb-2">Unexpected API Response</h3>
                                    <p className="text-gray-600">
                                        The analysis API did not return a valid list of unmatched items. Please try again or contact support.
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default UnmatchedAnalyzer; 