import React, { useState } from 'react';
import MonthSelector from '../components/MonthSelector';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorDisplay from '../components/ErrorDisplay';

const MismatchAnalyzer: React.FC = () => {
    const [selectedMonths, setSelectedMonths] = useState<string[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleAnalyze = async () => {
        if (selectedMonths.length === 0) {
            setError('Please select at least one month');
            return;
        }

        // TODO: Implement mismatch analysis API call
        setError('Mismatch analysis not yet implemented');
    };

    return (
        <div className="max-w-6xl mx-auto p-6">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">Mismatch Analyzer</h1>
                <p className="text-gray-600">
                    Analyze mismatched items to identify potential catalog conflicts and inconsistencies.
                </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Configuration Panel */}
                <div className="space-y-6">
                    <div className="bg-white rounded-lg shadow p-6">
                        <h2 className="text-xl font-semibold text-gray-900 mb-4">Analysis Configuration</h2>

                        {/* Month Selection */}
                        <div className="mb-6">
                            <MonthSelector
                                selectedMonths={selectedMonths}
                                onMonthsChange={setSelectedMonths}
                                label="Select Months to Analyze"
                            />
                        </div>

                        {/* Analyze Button */}
                        <button
                            onClick={handleAnalyze}
                            disabled={loading || selectedMonths.length === 0}
                            className="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? 'Analyzing...' : 'Analyze Mismatches'}
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
                            <LoadingSpinner message="Analyzing mismatches..." />
                        </div>
                    )}

                    {/* Placeholder for future results */}
                    <div className="bg-white rounded-lg shadow p-6">
                        <div className="text-center py-8">
                            <div className="text-gray-400 text-6xl mb-4">🔧</div>
                            <h3 className="text-lg font-medium text-gray-900 mb-2">Coming Soon</h3>
                            <p className="text-gray-600">
                                Mismatch analysis functionality will be implemented in a future update.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default MismatchAnalyzer; 