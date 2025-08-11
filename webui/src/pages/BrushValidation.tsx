import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import {
    ChevronLeft,
    ChevronRight,
    Check,
    RotateCcw,
    Filter,
    SortAsc,
    BarChart3,
    Loader2,
    MessageSquare,
} from 'lucide-react';
import MonthSelector from '../components/forms/MonthSelector';
import ErrorDisplay from '../components/feedback/ErrorDisplay';
import CommentModal from '../components/domain/CommentModal';
import {
    getBrushValidationData,
    getBrushValidationStatistics,
    recordBrushValidationAction,
    getCommentDetail,
    BrushValidationEntry,
    BrushValidationStatistics,
    CommentDetail,
    handleApiError,
} from '../services/api';

type SystemType = 'scoring';
type SortType = 'unvalidated' | 'validated' | 'ambiguity';

interface OverrideState {
    entryIndex: number;
    selectedStrategy: number;
}

/**
 * Brush Validation Component
 * 
 * This component follows match phase rules by:
 * - Displaying original text for human readability
 * - Using normalized text for all matching operations and validation actions
 * - Ensuring case-insensitive matching through normalized field usage
 * - Supporting only the scoring system (no legacy system support)
 * 
 * According to @match-phase rules: ALWAYS use the normalized field for matching operations,
 * not the original field. The original field should be preserved for reference but not used in matching logic.
 */
const BrushValidation: React.FC = () => {
    // State management
    const [selectedMonths, setSelectedMonths] = useState<string[]>([]);
    const [selectedSystem] = useState<SystemType>('scoring'); // Only scoring system supported
    const [sortBy, setSortBy] = useState<SortType>('unvalidated');
    const [currentPage, setCurrentPage] = useState(1);
    const [pageSize] = useState(20);
    const [showValidated, setShowValidated] = useState(true);

    // Data state
    const [entries, setEntries] = useState<BrushValidationEntry[]>([]);
    const [statistics, setStatistics] = useState<BrushValidationStatistics | null>(null);
    const [pagination, setPagination] = useState<{
        page: number;
        page_size: number;
        total: number;
        pages: number;
    } | null>(null);

    // UI state
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [overrideState, setOverrideState] = useState<OverrideState | null>(null);
    const [actionInProgress, setActionInProgress] = useState<Set<number>>(new Set());

    // Comment modal state
    const [selectedComment, setSelectedComment] = useState<CommentDetail | null>(null);
    const [commentModalOpen, setCommentModalOpen] = useState(false);
    const [commentLoading, setCommentLoading] = useState(false);
    const [allComments, setAllComments] = useState<CommentDetail[]>([]);
    const [currentCommentIndex, setCurrentCommentIndex] = useState<number>(0);
    const [remainingCommentIds, setRemainingCommentIds] = useState<string[]>([]);

    const currentMonth = selectedMonths[0] || '';

    // Comment handling functions
    const handleCommentClick = async (commentId: string, allCommentIds?: string[]) => {
        if (!commentId) return;

        try {
            setCommentLoading(true);

            // Always load just the clicked comment initially for fast response
            const comment = await getCommentDetail(commentId, [currentMonth]);
            setSelectedComment(comment);
            setCurrentCommentIndex(0);
            setCommentModalOpen(true);

            // Store the comment IDs for potential future loading
            if (allCommentIds && allCommentIds.length > 1) {
                setAllComments([comment]); // Start with just the first comment
                // Store the remaining IDs for lazy loading
                setRemainingCommentIds(allCommentIds.filter(id => id !== commentId));
            } else {
                setAllComments([comment]);
                setRemainingCommentIds([]);
            }
        } catch (err: unknown) {
            setError(handleApiError(err));
        } finally {
            setCommentLoading(false);
        }
    };

    const handleCommentNavigation = async (direction: 'prev' | 'next') => {
        if (allComments.length <= 1 && remainingCommentIds.length === 0) return;

        let newIndex = currentCommentIndex;
        if (direction === 'prev') {
            newIndex = Math.max(0, currentCommentIndex - 1);
            setCurrentCommentIndex(newIndex);
            setSelectedComment(allComments[newIndex]);
        } else {
            // Next - check if we need to load more comments
            if (currentCommentIndex === allComments.length - 1 && remainingCommentIds.length > 0) {
                // Load the next comment
                try {
                    setCommentLoading(true);
                    const nextCommentId = remainingCommentIds[0];
                    const nextComment = await getCommentDetail(nextCommentId, [currentMonth]);

                    setAllComments(prev => [...prev, nextComment]);
                    setRemainingCommentIds(prev => prev.slice(1));
                    setCurrentCommentIndex(allComments.length);
                    setSelectedComment(nextComment);
                } catch (err: unknown) {
                    setError(handleApiError(err));
                } finally {
                    setCommentLoading(false);
                }
            } else {
                // Navigate to existing comment
                newIndex = Math.min(allComments.length - 1, currentCommentIndex + 1);
                setCurrentCommentIndex(newIndex);
                setSelectedComment(allComments[newIndex]);
            }
        }
    };

    const handleCloseCommentModal = () => {
        setCommentModalOpen(false);
        setSelectedComment(null);
        setAllComments([]);
        setCurrentCommentIndex(0);
        setRemainingCommentIds([]);
    };

    // Load validation data
    const loadValidationData = useCallback(async () => {
        if (!currentMonth) {
            setEntries([]);
            setPagination(null);
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const response = await getBrushValidationData(currentMonth, selectedSystem, {
                sortBy,
                page: currentPage,
                pageSize,
            });

            setEntries(response.entries);
            setPagination(response.pagination);
        } catch (err) {
            setError(handleApiError(err));
        } finally {
            setLoading(false);
        }
    }, [currentMonth, selectedSystem, sortBy, currentPage, pageSize]);

    // Load statistics
    const loadStatistics = useCallback(async () => {
        if (!currentMonth) {
            setStatistics(null);
            return;
        }

        try {
            const stats = await getBrushValidationStatistics(currentMonth);
            setStatistics(stats);
        } catch (err) {
            console.error('Error loading statistics:', err);
        }
    }, [currentMonth]);

    // Effects
    useEffect(() => {
        loadValidationData();
    }, [loadValidationData]);

    useEffect(() => {
        loadStatistics();
    }, [loadStatistics]);

    useEffect(() => {
        setCurrentPage(1); // Reset to first page when filters change
    }, [selectedSystem, sortBy]);

    // Handle month selection
    const handleMonthsChange = useCallback((months: string[]) => {
        setSelectedMonths(months);
        setCurrentPage(1);
    }, []);



    // Handle sort change
    const handleSortChange = useCallback((sort: SortType) => {
        setSortBy(sort);
    }, []);

    // Handle pagination
    const handlePageChange = useCallback((page: number) => {
        setCurrentPage(page);
    }, []);

    // Handle validation action
    const handleValidate = useCallback(
        async (entryIndex: number) => {
            const entry = entries[entryIndex];
            if (!entry || !currentMonth) return;

            setActionInProgress((prev) => new Set(prev).add(entryIndex));

            try {
                const systemChoice = {
                    strategy: entry.matched?.strategy || '',
                    score: entry.matched?.score || 0,
                    result: entry.matched || {},
                };

                await recordBrushValidationAction({
                    input_text: entry.normalized_text || entry.input_text, // Use normalized for operations
                    month: currentMonth,
                    system_used: 'scoring',
                    action: 'validate',
                    system_choice: systemChoice,
                    user_choice: systemChoice,
                    all_brush_strategies: entry.all_strategies,
                });

                // Reload data to reflect changes
                await loadValidationData();
                await loadStatistics();
            } catch (err) {
                setError(handleApiError(err));
            } finally {
                setActionInProgress((prev) => {
                    const newSet = new Set(prev);
                    newSet.delete(entryIndex);
                    return newSet;
                });
            }
        },
        [entries, currentMonth, loadValidationData, loadStatistics]
    );

    // Handle override action
    const handleOverride = useCallback(
        async (entryIndex: number, strategyIndex: number) => {
            const entry = entries[entryIndex];
            if (!entry || !currentMonth) return;

            setActionInProgress((prev) => new Set(prev).add(entryIndex));

            try {
                const systemChoice = {
                    strategy: entry.matched?.strategy || '',
                    score: entry.matched?.score || 0,
                    result: entry.matched || {},
                };
                const userChoice = entry.all_strategies[strategyIndex];

                await recordBrushValidationAction({
                    input_text: entry.normalized_text || entry.input_text, // Use normalized for operations
                    month: currentMonth,
                    system_used: 'scoring',
                    action: 'override',
                    system_choice: systemChoice,
                    user_choice: userChoice,
                    all_brush_strategies: entry.all_strategies,
                });

                // Reload data to reflect changes
                await loadValidationData();
                await loadStatistics();
                setOverrideState(null);
            } catch (err) {
                setError(handleApiError(err));
            } finally {
                setActionInProgress((prev) => {
                    const newSet = new Set(prev);
                    newSet.delete(entryIndex);
                    return newSet;
                });
            }
        },
        [entries, currentMonth, loadValidationData, loadStatistics]
    );

    // Memoized filtered entries (for display purposes)
    const filteredEntries = useMemo(() => {
        if (showValidated) return entries;
        // Note: In practice, filtering should be done server-side
        // This is just for UI demonstration
        return entries;
    }, [entries, showValidated]);

    if (error) {
        return (
            <div className="w-full p-4">
                <ErrorDisplay error={error} onRetry={() => loadValidationData()} />
            </div>
        );
    }

    return (
        <div className="w-full p-4 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold">Brush Validation</h1>
                <Badge variant="outline" className="text-sm">
                    Scoring System Validation Interface
                </Badge>
            </div>

            {/* Month Selection */}
            <Card>
                <CardHeader>
                    <CardTitle className="text-lg">Month Selection</CardTitle>
                </CardHeader>
                <CardContent>
                    <MonthSelector selectedMonths={selectedMonths} onMonthsChange={handleMonthsChange} />
                </CardContent>
            </Card>

            {/* Controls */}
            {currentMonth && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">


                    {/* Sort Options */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="text-sm flex items-center gap-2">
                                <SortAsc className="h-4 w-4" />
                                Sort Order
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-2">
                            <Button
                                variant={sortBy === 'unvalidated' ? 'default' : 'outline'}
                                onClick={() => handleSortChange('unvalidated')}
                                className="w-full"
                            >
                                Sort by Unvalidated
                            </Button>
                            <Button
                                variant={sortBy === 'validated' ? 'default' : 'outline'}
                                onClick={() => handleSortChange('validated')}
                                className="w-full"
                            >
                                Sort by Validated
                            </Button>
                            <Button
                                variant={sortBy === 'ambiguity' ? 'default' : 'outline'}
                                onClick={() => handleSortChange('ambiguity')}
                                className="w-full"
                            >
                                Sort by Ambiguity
                            </Button>
                        </CardContent>
                    </Card>

                    {/* Statistics */}
                    {statistics && (
                        <Card>
                            <CardHeader>
                                <CardTitle className="text-sm flex items-center gap-2">
                                    <BarChart3 className="h-4 w-4" />
                                    Statistics
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-2">
                                <div className="text-sm">
                                    <div className="flex justify-between">
                                        <span>Total Entries:</span>
                                        <span className="font-medium">{statistics.total_entries}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span>Validated:</span>
                                        <span className="font-medium text-green-600">{statistics.validated_count}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span>Overridden:</span>
                                        <span className="font-medium text-orange-600">{statistics.overridden_count}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span>Unvalidated:</span>
                                        <span className="font-medium text-red-600">{statistics.unvalidated_count}</span>
                                    </div>
                                    <Separator className="my-2" />
                                    <div className="flex justify-between font-medium">
                                        <span>Validation Rate:</span>
                                        <span>{(statistics.validation_rate * 100).toFixed(1)}%</span>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    )}
                </div>
            )}

            {/* Filter Options */}
            {currentMonth && (
                <Card>
                    <CardHeader>
                        <CardTitle className="text-sm flex items-center gap-2">
                            <Filter className="h-4 w-4" />
                            Display Options
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Button
                            variant={showValidated ? 'outline' : 'default'}
                            onClick={() => setShowValidated(!showValidated)}
                            className="flex items-center gap-2"
                        >
                            {showValidated ? 'Hide Validated' : 'Show Validated'}
                            <Badge variant="secondary">{statistics?.validated_count || 0}</Badge>
                        </Button>
                    </CardContent>
                </Card>
            )}

            {/* Loading State */}
            {loading && (
                <Card>
                    <CardContent className="p-6">
                        <div className="flex items-center justify-center space-x-2">
                            <Loader2 className="h-4 w-4 animate-spin" />
                            <span>Loading validation data...</span>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Entries List */}
            {!loading && filteredEntries.length > 0 && (
                <div className="space-y-4">
                    {filteredEntries.map((entry, index) => (
                        <Card key={index} className="relative">
                            <CardHeader>
                                <div className="flex items-center justify-between">
                                    <div>
                                        <CardTitle className="text-base">{entry.input_text}</CardTitle>
                                        {entry.normalized_text && entry.normalized_text !== entry.input_text && (
                                            <div className="text-sm text-gray-500 mt-1">
                                                Normalized: {entry.normalized_text}
                                            </div>
                                        )}
                                    </div>
                                    <div className="flex items-center gap-2">
                                        {entry.matched && entry.matched.score && (
                                            <Badge variant="outline">Score: {entry.matched.score}</Badge>
                                        )}
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                {/* Entry Details */}
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {/* System Results */}
                                    <div>
                                        <h4 className="font-medium mb-2">System Result:</h4>
                                        <div className="text-sm space-y-1">
                                            {entry.matched ? (
                                                <>
                                                    <div>
                                                        <span className="font-medium">Strategy:</span> {entry.matched.strategy || 'Unknown'}
                                                    </div>
                                                    <div>
                                                        <span className="font-medium">Score:</span> {entry.matched.score || 'Unknown'}
                                                    </div>
                                                    <div>
                                                        <span className="font-medium">Brand:</span> {entry.matched.brand || 'Unknown'}
                                                    </div>
                                                    <div>
                                                        <span className="font-medium">Model:</span> {entry.matched.model || 'Unknown'}
                                                    </div>
                                                    {entry.matched.handle && (
                                                        <div>
                                                            <span className="font-medium">Handle:</span>{' '}
                                                            {entry.matched.handle.brand} {entry.matched.handle.model}
                                                        </div>
                                                    )}
                                                    {entry.matched.knot && (
                                                        <div>
                                                            <span className="font-medium">Knot:</span> {entry.matched.knot.brand}{' '}
                                                            {entry.matched.knot.model}
                                                            {entry.matched.knot.fiber && ` (${entry.matched.knot.fiber})`}
                                                        </div>
                                                    )}
                                                </>
                                            ) : (
                                                <div>No match found</div>
                                            )}
                                        </div>
                                    </div>

                                    {/* Alternative Strategies */}
                                    {entry.all_strategies.length > 0 && (
                                        <div>
                                            <h4 className="font-medium mb-2">Alternative Strategies:</h4>
                                            <div className="text-sm space-y-2 max-h-64 overflow-y-auto">
                                                {entry.all_strategies
                                                    .filter((strategy) => {
                                                        // Filter out the winning strategy - compare result data to identify the winner
                                                        if (!strategy.result || !entry.matched) return true;

                                                        // Check if this strategy's result matches the winning result
                                                        const isWinner =
                                                            strategy.result.brand === entry.matched.brand &&
                                                            strategy.result.model === entry.matched.model &&
                                                            strategy.strategy === entry.matched.strategy &&
                                                            strategy.score === entry.matched.score;

                                                        return !isWinner;
                                                    })
                                                    .map((strategy, strategyIndex) => (
                                                        <div
                                                            key={strategyIndex}
                                                            className={`p-3 rounded border ${overrideState?.entryIndex === index && overrideState?.selectedStrategy === strategyIndex
                                                                ? 'bg-blue-50 border-blue-200'
                                                                : 'bg-gray-50 border-gray-200'
                                                                }`}
                                                        >
                                                            <div className="flex justify-between items-center mb-2">
                                                                <span className="font-medium capitalize">
                                                                    {strategy.strategy.replace(/_/g, ' ')}
                                                                </span>
                                                                <Badge variant="outline" className="text-xs">
                                                                    Score: {strategy.score}
                                                                </Badge>
                                                            </div>
                                                            {strategy.result && (
                                                                <div className="space-y-1 text-gray-700">
                                                                    <div className="text-xs">
                                                                        <span className="font-medium">Brand:</span> {strategy.result.brand || 'N/A'}
                                                                    </div>
                                                                    <div className="text-xs">
                                                                        <span className="font-medium">Model:</span> {strategy.result.model || 'N/A'}
                                                                    </div>
                                                                    {strategy.result.handle && (
                                                                        <div className="text-xs">
                                                                            <span className="font-medium">Handle:</span>{' '}
                                                                            {strategy.result.handle.brand} {strategy.result.handle.model}
                                                                        </div>
                                                                    )}
                                                                    {strategy.result.knot && (
                                                                        <div className="text-xs">
                                                                            <span className="font-medium">Knot:</span> {strategy.result.knot.brand}{' '}
                                                                            {strategy.result.knot.model}
                                                                            {strategy.result.knot.fiber && ` (${strategy.result.knot.fiber})`}
                                                                        </div>
                                                                    )}
                                                                </div>
                                                            )}
                                                        </div>
                                                    ))}
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Comment IDs Section */}
                                {entry.comment_ids && entry.comment_ids.length > 0 && (
                                    <div className="border-t pt-4">
                                        <h4 className="font-medium mb-2 flex items-center gap-2">
                                            <MessageSquare className="h-4 w-4" />
                                            Comment References ({entry.comment_ids.length})
                                        </h4>
                                        <div className="flex flex-wrap gap-2">
                                            {entry.comment_ids.map((commentId, commentIndex) => (
                                                <Button
                                                    key={commentIndex}
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={() => handleCommentClick(commentId, entry.comment_ids)}
                                                    disabled={commentLoading}
                                                    className="text-xs h-8 px-2"
                                                >
                                                    {commentLoading ? (
                                                        <Loader2 className="h-3 w-3 animate-spin" />
                                                    ) : (
                                                        <>
                                                            <MessageSquare className="h-3 w-3 mr-1" />
                                                            {commentId}
                                                        </>
                                                    )}
                                                </Button>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Override Strategy Selection */}
                                {overrideState?.entryIndex === index && (
                                    <div className="border-t pt-4">
                                        <h4 className="font-medium mb-2">Select Alternative Strategy:</h4>
                                        <div className="space-y-2">
                                            {entry.all_strategies.map((strategy, strategyIndex) => (
                                                <Button
                                                    key={strategyIndex}
                                                    variant={overrideState.selectedStrategy === strategyIndex ? 'default' : 'outline'}
                                                    onClick={() =>
                                                        setOverrideState({
                                                            entryIndex: index,
                                                            selectedStrategy: strategyIndex,
                                                        })
                                                    }
                                                    className="w-full justify-between"
                                                >
                                                    <span>
                                                        {strategy.strategy} ({strategy.score})
                                                    </span>
                                                </Button>
                                            ))}
                                        </div>
                                        <div className="flex gap-2 mt-4">
                                            <Button
                                                onClick={() => handleOverride(index, overrideState.selectedStrategy)}
                                                disabled={actionInProgress.has(index)}
                                                className="flex items-center gap-2"
                                            >
                                                {actionInProgress.has(index) ? (
                                                    <Loader2 className="h-4 w-4 animate-spin" />
                                                ) : (
                                                    <Check className="h-4 w-4" />
                                                )}
                                                Confirm Override
                                            </Button>
                                            <Button variant="outline" onClick={() => setOverrideState(null)}>
                                                Cancel
                                            </Button>
                                        </div>
                                    </div>
                                )}

                                {/* Action Buttons */}
                                {overrideState?.entryIndex !== index && (
                                    <div className="flex gap-2 pt-4 border-t">
                                        <Button
                                            onClick={() => handleValidate(index)}
                                            disabled={actionInProgress.has(index)}
                                            className="flex items-center gap-2 bg-green-600 hover:bg-green-700"
                                        >
                                            {actionInProgress.has(index) ? (
                                                <Loader2 className="h-4 w-4 animate-spin" />
                                            ) : (
                                                <Check className="h-4 w-4" />
                                            )}
                                            Validate
                                        </Button>
                                        {entry.all_strategies.length > 0 && (
                                            <Button
                                                variant="outline"
                                                onClick={() =>
                                                    setOverrideState({
                                                        entryIndex: index,
                                                        selectedStrategy: 0,
                                                    })
                                                }
                                                className="flex items-center gap-2"
                                            >
                                                <RotateCcw className="h-4 w-4" />
                                                Override
                                            </Button>
                                        )}
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}

            {/* Pagination */}
            {pagination && pagination.pages > 1 && (
                <Card>
                    <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                            <div className="text-sm text-gray-600">
                                Page {pagination.page} of {pagination.pages} • {pagination.total} total entries
                            </div>
                            <div className="flex items-center space-x-2">
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => handlePageChange(pagination.page - 1)}
                                    disabled={pagination.page <= 1}
                                >
                                    <ChevronLeft className="h-4 w-4" />
                                    Previous
                                </Button>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => handlePageChange(pagination.page + 1)}
                                    disabled={pagination.page >= pagination.pages}
                                >
                                    Next
                                    <ChevronRight className="h-4 w-4" />
                                </Button>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Empty State */}
            {!loading && filteredEntries.length === 0 && currentMonth && (
                <Card>
                    <CardContent className="p-6 text-center">
                        <div className="text-gray-500">
                            {entries.length === 0
                                ? 'No validation data found for the selected month.'
                                : 'No entries match the current filter criteria.'}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* No Month Selected State */}
            {!currentMonth && (
                <Card>
                    <CardContent className="p-6 text-center">
                        <div className="text-gray-500">Please select a month to begin validation.</div>
                    </CardContent>
                </Card>
            )}

            {/* Comment Modal */}
            {selectedComment && (
                <CommentModal
                    comment={selectedComment}
                    isOpen={commentModalOpen}
                    onClose={handleCloseCommentModal}
                    comments={allComments}
                    currentIndex={currentCommentIndex}
                    onNavigate={handleCommentNavigation}
                    remainingCommentIds={remainingCommentIds}
                />
            )}
        </div>
    );
};

export default BrushValidation;
