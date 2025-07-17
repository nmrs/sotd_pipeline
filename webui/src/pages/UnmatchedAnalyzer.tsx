import React, { useState } from 'react';
import { analyzeUnmatched, UnmatchedAnalysisResult, handleApiError } from '../services/api';
import MonthSelector from '../components/MonthSelector';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorDisplay from '../components/ErrorDisplay';

const UnmatchedAnalyzer: React.FC = () => {
    const [selectedField, setSelectedField] = useState<string>('razor');
    const [selectedMonths, setSelectedMonths] = useState<string[]>([]);
    const [limit, setLimit] = useState<number>(50);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [results, setResults] = useState<UnmatchedAnalysisResult | null>(null);

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

            const result = await analyzeUnmatched({
                field: selectedField,
                months: selectedMonths,
                limit,
            });

            setResults(result);
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

    return (
        <div className="max-w-6xl mx-auto p-6">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">Unmatched Item Analyzer</h1>
                <p className="text-gray-600">
                    Analyze unmatched items across selected months to identify patterns and potential catalog additions.
                </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Configuration Panel */}
                <div className="space-y-6">
                    <div className="bg-white rounded-lg shadow p-6">
                        <h2 className="text-xl font-semibold text-gray-900 mb-4">Analysis Configuration</h2>

                        {/* Field Selection */}
                        <div className="mb-6">
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
                        <div className="mb-6">
                            <MonthSelector
                                selectedMonths={selectedMonths}
                                onMonthsChange={setSelectedMonths}
                                label="Select Months to Analyze"
                            />
                        </div>

                        {/* Limit Selection */}
                        <div className="mb-6">
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

                        {/* Analyze Button */}
                        <button
                            onClick={handleAnalyze}
                            disabled={loading || selectedMonths.length === 0}
                            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? 'Analyzing...' : 'Analyze Unmatched Items'}
                        </button>
                    </div>
                </div>

                {/* Results Panel */}
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
                                    Field: {results.field} | Months: {results.months.join(', ')} |
                                    Total Unmatched: {results.total_unmatched} |
                                    Processing Time: {results.processing_time.toFixed(2)}s
                                </p>
                            </div>

                            <div className="p-6">
                                {results.unmatched_items.length === 0 ? (
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
                                        <div className="overflow-x-auto">
                                            <table className="min-w-full divide-y divide-gray-200">
                                                <thead className="bg-gray-50">
                                                    <tr>
                                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                            Item
                                                        </th>
                                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                            Count
                                                        </th>
                                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                            Examples
                                                        </th>
                                                    </tr>
                                                </thead>
                                                <tbody className="bg-white divide-y divide-gray-200">
                                                    {results.unmatched_items.map((item, index) => (
                                                        <tr key={index} className="hover:bg-gray-50">
                                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                                                {item.item}
                                                            </td>
                                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                                {item.count}
                                                            </td>
                                                            <td className="px-6 py-4 text-sm text-gray-500">
                                                                {formatExamples(item.examples)}
                                                            </td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default UnmatchedAnalyzer; 