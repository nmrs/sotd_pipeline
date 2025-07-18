import React, { useState, useEffect } from 'react';
import { analyzeUnmatched, UnmatchedAnalysisResult, handleApiError, runMatchPhase, MatchPhaseRequest, getCommentDetail, CommentDetail } from '../services/api';
import MonthSelector from '../components/MonthSelector';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorDisplay from '../components/ErrorDisplay';
import VirtualizedTable from '../components/VirtualizedTable';
import PerformanceMonitor from '../components/PerformanceMonitor';
import CommentModal from '../components/CommentModal';

const UnmatchedAnalyzer: React.FC = () => {
    const [selectedField, setSelectedField] = useState<string>('razor');
    const [selectedMonths, setSelectedMonths] = useState<string[]>([]);
    const [limit, setLimit] = useState<number>(50);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const [matchPhaseOutput, setMatchPhaseOutput] = useState<string | null>(null);
    const [results, setResults] = useState<UnmatchedAnalysisResult | null>(null);
    const [operationCount, setOperationCount] = useState(0);
    const [matchPhaseLoading, setMatchPhaseLoading] = useState(false);
    const [forceMatch, setForceMatch] = useState(true);
    const [selectedComment, setSelectedComment] = useState<CommentDetail | null>(null);
    const [commentModalOpen, setCommentModalOpen] = useState(false);
    const [commentLoading, setCommentLoading] = useState(false);

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
            setSuccessMessage(null);
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

    const formatCommentIds = (commentIds: string[]) => {
        if (commentIds.length === 0) return 'No comment IDs available';
        return commentIds.slice(0, 3).join(', ') + (commentIds.length > 3 ? '...' : '');
    };

    const handleCommentClick = async (commentId: string) => {
        try {
            setCommentLoading(true);
            const comment = await getCommentDetail(commentId, selectedMonths);
            setSelectedComment(comment);
            setCommentModalOpen(true);
        } catch (err: any) {
            setError(handleApiError(err));
        } finally {
            setCommentLoading(false);
        }
    };

    const handleRunMatchPhase = async () => {
        if (selectedMonths.length === 0) {
            setError('Please select at least one month');
            return;
        }

        try {
            setMatchPhaseLoading(true);
            setError(null);
            setSuccessMessage(null);

            const request: MatchPhaseRequest = {
                months: selectedMonths,
                force: forceMatch,
            };

            const result = await runMatchPhase(request);

            // Store the output for display
            setMatchPhaseOutput(result.error_details || null);

            if (result.success) {
                setError(null);
                setSuccessMessage(result.message);
                // Optionally refresh the analysis after successful match phase
                if (results) {
                    handleAnalyze();
                }
            } else {
                // Display both the message and error details if available
                const errorMessage = result.error_details
                    ? `${result.message}\n\nError Details:\n${result.error_details}`
                    : result.message;
                setError(errorMessage);
                setSuccessMessage(null);
            }
        } catch (err: any) {
            setError(handleApiError(err));
        } finally {
            setMatchPhaseLoading(false);
        }
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

            {/* Compact Configuration Panel */}
            <div className="mb-4">
                <div className="bg-white rounded-lg shadow p-4">
                    <div className="flex flex-wrap items-center gap-4">
                        {/* Field Selection */}
                        <div className="flex items-center space-x-2">
                            <label className="text-sm font-medium text-gray-700">Field:</label>
                            <select
                                value={selectedField}
                                onChange={(e) => setSelectedField(e.target.value)}
                                className="border border-gray-300 rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                            >
                                {fieldOptions.map((option) => (
                                    <option key={option.value} value={option.value}>
                                        {option.label}
                                    </option>
                                ))}
                            </select>
                        </div>

                        {/* Month Selection - Compact */}
                        <div className="flex items-center space-x-2">
                            <label className="text-sm font-medium text-gray-700">Months:</label>
                            <div className="flex-1 min-w-0">
                                <MonthSelector
                                    selectedMonths={selectedMonths}
                                    onMonthsChange={setSelectedMonths}
                                    label=""
                                />
                            </div>
                        </div>

                        {/* Limit Selection */}
                        <div className="flex items-center space-x-2">
                            <label className="text-sm font-medium text-gray-700">Limit:</label>
                            <input
                                type="number"
                                value={limit}
                                onChange={(e) => setLimit(parseInt(e.target.value) || 50)}
                                min="1"
                                max="1000"
                                className="w-20 border border-gray-300 rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                            />
                        </div>

                        {/* Action Buttons */}
                        <div className="flex items-center space-x-2">
                            <button
                                onClick={handleAnalyze}
                                disabled={loading || selectedMonths.length === 0}
                                className="bg-blue-600 text-white py-1 px-3 rounded text-sm hover:bg-blue-700 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {loading ? 'Analyzing...' : 'Analyze'}
                            </button>

                            <button
                                onClick={handleRunMatchPhase}
                                disabled={matchPhaseLoading || selectedMonths.length === 0}
                                className="bg-green-600 text-white py-1 px-3 rounded text-sm hover:bg-green-700 focus:outline-none focus:ring-1 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {matchPhaseLoading ? 'Running...' : 'Match Phase'}
                            </button>

                            <div className="flex items-center space-x-1">
                                <input
                                    type="checkbox"
                                    id="force-match"
                                    checked={forceMatch}
                                    onChange={(e) => setForceMatch(e.target.checked)}
                                    className="rounded border-gray-300 text-green-600 focus:ring-green-500"
                                />
                                <label htmlFor="force-match" className="text-xs text-gray-700">
                                    Force
                                </label>
                            </div>
                        </div>

                        {/* Performance Monitor - Compact */}
                        <div className="ml-auto">
                            <PerformanceMonitor
                                dataSize={results?.unmatched_items?.length || 0}
                                operationCount={operationCount}
                            />
                        </div>
                    </div>
                </div>
            </div>

            {/* Results Panel - Full width */}
            <div className="space-y-6">
                {error && (
                    <ErrorDisplay error={error} onRetry={() => setError(null)} />
                )}

                {successMessage && (
                    <div className="bg-green-50 border border-green-200 rounded-md p-4">
                        <div className="flex">
                            <div className="flex-shrink-0">
                                <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                </svg>
                            </div>
                            <div className="ml-3">
                                <p className="text-sm text-green-800">{successMessage}</p>
                            </div>
                            <div className="ml-auto pl-3">
                                <div className="-mx-1.5 -my-1.5">
                                    <button
                                        onClick={() => setSuccessMessage(null)}
                                        className="inline-flex rounded-md bg-green-50 p-1.5 text-green-500 hover:bg-green-100 focus:outline-none focus:ring-2 focus:ring-green-600 focus:ring-offset-2 focus:ring-offset-green-50"
                                    >
                                        <span className="sr-only">Dismiss</span>
                                        <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                                        </svg>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {matchPhaseOutput && (
                    <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
                        <div className="flex items-center justify-between mb-2">
                            <h3 className="text-sm font-medium text-gray-900">Match Phase Output</h3>
                            <button
                                onClick={() => setMatchPhaseOutput(null)}
                                className="text-gray-400 hover:text-gray-600"
                            >
                                <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                                </svg>
                            </button>
                        </div>
                        <pre className="text-xs text-gray-700 bg-white p-3 rounded border overflow-x-auto whitespace-pre-wrap">
                            {matchPhaseOutput}
                        </pre>
                    </div>
                )}

                {loading && (
                    <div className="bg-white rounded-lg shadow p-6">
                        <LoadingSpinner message="Analyzing unmatched items..." />
                    </div>
                )}

                {results && (
                    <div className="bg-white rounded-lg shadow">
                        <div className="px-4 py-3 border-b border-gray-200">
                            <div className="flex items-center justify-between">
                                <h2 className="text-lg font-semibold text-gray-900">Results</h2>
                                <div className="text-xs text-gray-500">
                                    {results.field} | {results.months?.join(', ')} | {results.total_unmatched || 0} items | {results.processing_time?.toFixed(2) || '0.00'}s
                                </div>
                            </div>
                        </div>

                        <div className="p-4">
                            {Array.isArray(results.unmatched_items) ? (
                                results.unmatched_items.length === 0 ? (
                                    <div className="text-center py-6">
                                        <div className="text-green-600 text-4xl mb-2">✓</div>
                                        <h3 className="text-base font-medium text-gray-900 mb-1">No Unmatched Items</h3>
                                        <p className="text-sm text-gray-600">
                                            All {results.field} items were successfully matched.
                                        </p>
                                    </div>
                                ) : (
                                    <div>
                                        <h3 className="text-base font-medium text-gray-900 mb-3">
                                            Top Unmatched Items ({results.unmatched_items.length})
                                        </h3>
                                        <VirtualizedTable
                                            data={results.unmatched_items}
                                            columns={[
                                                {
                                                    key: 'item',
                                                    header: 'Item',
                                                    width: 250,
                                                    render: (item) => (
                                                        <span className="font-medium text-gray-900 text-sm">
                                                            {item.item}
                                                        </span>
                                                    ),
                                                },
                                                {
                                                    key: 'count',
                                                    header: 'Count',
                                                    width: 80,
                                                    render: (item) => (
                                                        <span className="text-gray-500 text-sm">
                                                            {item.count}
                                                        </span>
                                                    ),
                                                },
                                                {
                                                    key: 'comment_ids',
                                                    header: 'Comment IDs',
                                                    width: 300,
                                                    render: (item) => (
                                                        <div className="text-sm">
                                                            {item.comment_ids && item.comment_ids.length > 0 ? (
                                                                <div className="flex flex-wrap gap-1">
                                                                    {item.comment_ids.slice(0, 3).map((commentId, index) => (
                                                                        <button
                                                                            key={index}
                                                                            onClick={() => handleCommentClick(commentId)}
                                                                            disabled={commentLoading}
                                                                            className="text-blue-600 hover:text-blue-800 underline text-xs bg-blue-50 px-2 py-1 rounded hover:bg-blue-100 disabled:opacity-50 disabled:cursor-not-allowed"
                                                                        >
                                                                            {commentLoading ? 'Loading...' : commentId}
                                                                        </button>
                                                                    ))}
                                                                    {item.comment_ids.length > 3 && (
                                                                        <span className="text-gray-500 text-xs">
                                                                            +{item.comment_ids.length - 3} more
                                                                        </span>
                                                                    )}
                                                                </div>
                                                            ) : (
                                                                <span className="text-gray-400 text-xs">No comment IDs</span>
                                                            )}
                                                        </div>
                                                    ),
                                                },
                                                {
                                                    key: 'examples',
                                                    header: 'Examples',
                                                    width: 200,
                                                    render: (item) => (
                                                        <span className="text-gray-500 text-sm">
                                                            {formatExamples(item.examples)}
                                                        </span>
                                                    ),
                                                },
                                            ]}
                                            height={350}
                                            rowHeight={40}
                                        />
                                    </div>
                                )
                            ) : (
                                <div className="text-center py-6">
                                    <div className="text-red-600 text-4xl mb-2">!</div>
                                    <h3 className="text-base font-medium text-gray-900 mb-1">Invalid Response</h3>
                                    <p className="text-sm text-gray-600">
                                        The API did not return valid data. Please try again.
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>

            {/* Comment Modal */}
            <CommentModal
                comment={selectedComment}
                isOpen={commentModalOpen}
                onClose={() => {
                    setCommentModalOpen(false);
                    setSelectedComment(null);
                }}
            />
        </div>
    );
};

export default UnmatchedAnalyzer; 