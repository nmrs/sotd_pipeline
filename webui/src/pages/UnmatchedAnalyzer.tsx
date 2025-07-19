import React, { useState, useEffect, useMemo } from 'react';
import { analyzeUnmatched, UnmatchedAnalysisResult, handleApiError, runMatchPhase, MatchPhaseRequest, getCommentDetail, CommentDetail } from '../services/api';
import MonthSelector from '../components/MonthSelector';
import LoadingSpinner from '../components/LoadingSpinner';
import VirtualizedTable from '../components/VirtualizedTable';
import PerformanceMonitor from '../components/PerformanceMonitor';
import CommentModal from '../components/CommentModal';



import { useViewState } from '../hooks/useViewState';
import { useSearchSort } from '../hooks/useSearchSort';
import { useMessaging } from '../hooks/useMessaging';
import MessageDisplay from '../components/MessageDisplay';

// Hook to get screen width
const useScreenWidth = () => {
    const [screenWidth, setScreenWidth] = useState(window.innerWidth);

    useEffect(() => {
        const handleResize = () => {
            setScreenWidth(window.innerWidth);
        };

        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    return screenWidth;
};

const UnmatchedAnalyzer: React.FC = () => {
    const [selectedField, setSelectedField] = useState<string>('razor');
    const [selectedMonths, setSelectedMonths] = useState<string[]>([]);
    const [limit, setLimit] = useState<number>(50);
    const [loading, setLoading] = useState(false);
    const [matchPhaseOutput, setMatchPhaseOutput] = useState<string | null>(null);
    const [results, setResults] = useState<UnmatchedAnalysisResult | null>(null);
    const [operationCount, setOperationCount] = useState(0);
    const [matchPhaseLoading, setMatchPhaseLoading] = useState(false);
    const [forceMatch, setForceMatch] = useState(true);
    const [selectedComment, setSelectedComment] = useState<CommentDetail | null>(null);
    const [commentModalOpen, setCommentModalOpen] = useState(false);
    const [commentLoading, setCommentLoading] = useState(false);
    const [filteredStatus, setFilteredStatus] = useState<Record<string, boolean>>({});
    const [pendingChanges, setPendingChanges] = useState<Record<string, boolean>>({});

    // View state hook
    const viewState = useViewState();

    // Search and sort hook
    const searchSort = useSearchSort({
        items: results?.unmatched_items || [],
        showFiltered: viewState.showFiltered,
        filteredStatus,
    });

    // Messaging hook
    const messaging = useMessaging();

    // Screen width hook for dynamic column sizing
    const screenWidth = useScreenWidth();



    const fieldOptions = [
        { value: 'razor', label: 'Razor' },
        { value: 'blade', label: 'Blade' },
        { value: 'brush', label: 'Brush' },
        { value: 'soap', label: 'Soap' },
    ];

    const handleAnalyze = async () => {
        if (selectedMonths.length === 0) {
            messaging.addErrorMessage('Please select at least one month');
            return;
        }

        try {
            setLoading(true);
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
            messaging.addErrorMessage(handleApiError(err));
        } finally {
            setLoading(false);
        }
    };

    const formatExamples = (examples: string[]) => {
        if (examples.length === 0) return 'No examples available';
        return examples.slice(0, 3).join(', ') + (examples.length > 3 ? '...' : '');
    };

    // Calculate dynamic column widths based on screen size
    const columnWidths = useMemo(() => {
        // Account for padding and margins (roughly 100px total)
        const availableWidth = Math.max(screenWidth - 100, 800); // Minimum 800px

        // Define column proportions (total should be 100%)
        const proportions = {
            filtered: 8,    // 8%
            item: 35,       // 35%
            count: 8,       // 8%
            comment_ids: 35, // 35%
            examples: 14,   // 14%
        };

        return {
            filtered: Math.floor(availableWidth * proportions.filtered / 100),
            item: Math.floor(availableWidth * proportions.item / 100),
            count: Math.floor(availableWidth * proportions.count / 100),
            comment_ids: Math.floor(availableWidth * proportions.comment_ids / 100),
            examples: Math.floor(availableWidth * proportions.examples / 100),
        };
    }, [screenWidth]);

    const handleCommentClick = async (commentId: string) => {
        try {
            setCommentLoading(true);
            const comment = await getCommentDetail(commentId, selectedMonths);
            setSelectedComment(comment);
            setCommentModalOpen(true);
        } catch (err: any) {
            messaging.addErrorMessage(handleApiError(err));
        } finally {
            setCommentLoading(false);
        }
    };

    const handleFilteredStatusChange = (itemName: string, isFiltered: boolean) => {
        const currentStatus = filteredStatus[itemName] || false;

        setPendingChanges(prev => {
            const newChanges = { ...prev };

            if (isFiltered === currentStatus) {
                // If the new value matches the current status, remove from pending changes
                delete newChanges[itemName];
            } else {
                // If the new value is different, add to pending changes
                newChanges[itemName] = isFiltered;
            }

            return newChanges;
        });
    };

    const handleApplyFilteredChanges = async () => {
        if (Object.keys(pendingChanges).length === 0) {
            messaging.addSuccessMessage('No changes to apply');
            return;
        }

        try {
            setLoading(true);

            // Prepare a single entries array, each with its own month
            const allEntries: Array<{
                name: string;
                action: 'add' | 'remove';
                comment_id: string;
                source: string;
                month: string;
            }> = [];

            Object.entries(pendingChanges).forEach(([itemName, shouldBeFiltered]) => {
                const item = results?.unmatched_items?.find(i => i.item === itemName);
                if (item && item.comment_ids && item.examples) {
                    // Get the month from the first example file
                    const month = item.examples[0]?.replace('.json', '') || selectedMonths[0];
                    item.comment_ids.forEach(commentId => {
                        allEntries.push({
                            name: itemName,
                            action: shouldBeFiltered ? 'add' : 'remove',
                            comment_id: commentId,
                            source: 'user',
                            month,
                        });
                    });
                }
            });

            if (allEntries.length === 0) {
                messaging.addSuccessMessage('No changes to apply');
                return;
            }

            // Import the API function
            const { updateFilteredEntries } = await import('../services/api');

            const response = await updateFilteredEntries({
                category: selectedField,
                entries: allEntries,
            });

            if (!response.success) {
                messaging.addErrorMessage(response.message || 'Failed to update filtered entries');
                return;
            }

            // Update the filtered status with pending changes
            setFilteredStatus(prev => ({
                ...prev,
                ...pendingChanges,
            }));

            // Clear pending changes
            setPendingChanges({});

            messaging.addSuccessMessage(`Updated ${Object.keys(pendingChanges).length} entries successfully`);
        } catch (err: any) {
            messaging.addErrorMessage(err.message || 'Failed to update filtered entries');
        } finally {
            setLoading(false);
        }
    };

    const handleRunMatchPhase = async () => {
        if (selectedMonths.length === 0) {
            messaging.addErrorMessage('Please select at least one month');
            return;
        }

        try {
            setMatchPhaseLoading(true);
            setMatchPhaseOutput(null); // Clear previous output before writing new content

            const request: MatchPhaseRequest = {
                months: selectedMonths,
                force: forceMatch,
            };

            const result = await runMatchPhase(request);

            // Store the output for display
            setMatchPhaseOutput(result.error_details || null);

            if (result.success) {
                messaging.addSuccessMessage(result.message);
                // Optionally refresh the analysis after successful match phase
                if (results) {
                    handleAnalyze();
                }
            } else {
                // Display both the message and error details if available
                const errorMessage = result.error_details
                    ? `${result.message}\n\nError Details:\n${result.error_details}`
                    : result.message;
                messaging.addErrorMessage(errorMessage);
            }
        } catch (err: any) {
            messaging.addErrorMessage(handleApiError(err));
        } finally {
            setMatchPhaseLoading(false);
        }
    };



    useEffect(() => {
        if (results) {
            // eslint-disable-next-line no-console
            console.log('UnmatchedAnalyzer results:', results);
            console.log('showFiltered state:', viewState.showFiltered);
        }
    }, [results, viewState.showFiltered]);

    return (
        <div className="max-w-full mx-auto p-6">
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
                                        <div className="flex items-center justify-between mb-3">
                                            <div className="flex items-center space-x-4">
                                                <div>
                                                    <h3 className="text-base font-medium text-gray-900">
                                                        Top Unmatched Items ({searchSort.searchResultsCount} of {searchSort.totalItemsCount})
                                                    </h3>
                                                    <p className="text-xs text-gray-500">
                                                        Screen: {screenWidth}px | Available: {Math.max(screenWidth - 100, 800)}px |
                                                        Item: {columnWidths.item}px | Comments: {columnWidths.comment_ids}px
                                                    </p>
                                                </div>
                                                <div className="flex items-center space-x-2">
                                                    <button
                                                        onClick={viewState.toggleShowFiltered}
                                                        className={`px-3 py-1 rounded text-sm font-medium transition-colors ${viewState.showFiltered
                                                            ? 'bg-gray-600 text-white hover:bg-gray-700'
                                                            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                                                            }`}
                                                    >
                                                        {viewState.showFiltered ? 'Hide Filtered' : 'Show Filtered'}
                                                    </button>
                                                </div>
                                            </div>
                                            <div className="flex items-center justify-between">
                                                {/* Apply Changes Button - Compact and inline */}
                                                {(() => {
                                                    // Calculate only visible changes
                                                    const visibleItems = searchSort.filteredAndSortedItems.map(item => item.item);
                                                    const visibleChanges = Object.keys(pendingChanges).filter(itemName =>
                                                        visibleItems.includes(itemName)
                                                    );
                                                    const visibleChangesCount = visibleChanges.length;

                                                    return visibleChangesCount > 0 && (
                                                        <div className="flex items-center space-x-2">
                                                            <button
                                                                onClick={handleApplyFilteredChanges}
                                                                disabled={loading}
                                                                className={`py-1 px-3 rounded text-sm focus:outline-none focus:ring-1 disabled:cursor-not-allowed ${loading
                                                                    ? 'bg-gray-400 text-gray-600 cursor-not-allowed'
                                                                    : 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500'
                                                                    }`}
                                                            >
                                                                {loading ? 'Applying...' : `Apply (${visibleChangesCount})`}
                                                            </button>
                                                        </div>
                                                    );
                                                })()}

                                                {/* Search Box */}
                                                <div className="flex items-center space-x-2">
                                                    <input
                                                        type="text"
                                                        placeholder="Search items..."
                                                        value={searchSort.searchTerm}
                                                        onChange={(e) => searchSort.setSearchTerm(e.target.value)}
                                                        className="px-3 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                                                    />
                                                    {searchSort.searchTerm && (
                                                        <button
                                                            onClick={searchSort.clearSearch}
                                                            className="text-gray-400 hover:text-gray-600"
                                                        >
                                                            <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                                                                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                                                            </svg>
                                                        </button>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                        <VirtualizedTable
                                            data={searchSort.filteredAndSortedItems}
                                            columns={[
                                                {
                                                    key: 'filtered',
                                                    header: 'Filtered',
                                                    width: columnWidths.filtered,
                                                    render: (item) => {
                                                        const isCurrentlyFiltered = filteredStatus[item.item] || false;
                                                        const hasPendingChange = item.item in pendingChanges;
                                                        const pendingValue = pendingChanges[item.item];
                                                        const displayValue = hasPendingChange ? pendingValue : isCurrentlyFiltered;

                                                        return (
                                                            <div className="flex items-center">
                                                                <input
                                                                    type="checkbox"
                                                                    checked={displayValue}
                                                                    onChange={(e) => handleFilteredStatusChange(item.item, e.target.checked)}
                                                                    disabled={commentLoading}
                                                                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                                                                    title={displayValue ? 'Mark as unfiltered' : 'Mark as intentionally unmatched'}
                                                                />
                                                                {hasPendingChange && (
                                                                    <div className="ml-1">
                                                                        <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                                                                    </div>
                                                                )}
                                                            </div>
                                                        );
                                                    },
                                                },
                                                {
                                                    key: 'item',
                                                    header: 'Item',
                                                    width: columnWidths.item,
                                                    render: (item) => (
                                                        <span className={`font-medium text-sm ${filteredStatus[item.item]
                                                            ? 'text-gray-400 line-through'
                                                            : 'text-gray-900'
                                                            }`}>
                                                            {item.item}
                                                            {filteredStatus[item.item] && (
                                                                <span className="ml-2 text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                                                                    Filtered
                                                                </span>
                                                            )}
                                                        </span>
                                                    ),
                                                },
                                                {
                                                    key: 'count',
                                                    header: 'Count',
                                                    width: columnWidths.count,
                                                    render: (item) => (
                                                        <span className="text-gray-500 text-sm">
                                                            {item.count}
                                                        </span>
                                                    ),
                                                },
                                                {
                                                    key: 'comment_ids',
                                                    header: 'Comment IDs',
                                                    width: columnWidths.comment_ids,
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
                                                    width: columnWidths.examples,
                                                    render: (item) => (
                                                        <span className="text-gray-500 text-sm">
                                                            {formatExamples(item.examples || [])}
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

            {/* Message Display */}
            <MessageDisplay
                messages={messaging.messages}
                onRemoveMessage={messaging.removeMessage}
            />
        </div>
    );
};

export default UnmatchedAnalyzer; 