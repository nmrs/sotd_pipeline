import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

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
    PieChart,
} from 'lucide-react';
import MonthSelector from '../components/forms/MonthSelector';
import ErrorDisplay from '../components/feedback/ErrorDisplay';
import CommentModal from '../components/domain/CommentModal';
import StrategyDistributionModal from '../components/domain/StrategyDistributionModal';
import {
    getBrushValidationData,
    getBrushValidationStatistics,
    getStrategyDistributionStatistics,
    recordBrushValidationAction,
    undoLastValidationAction,
    getCommentDetail,
    BrushValidationEntry,
    BrushValidationStatistics,
    StrategyDistributionStatistics,
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
 *
 * Note: Entries with strategies "correct_complete_brush" and "correct_split_brush" are automatically
 * filtered out by the backend since these come from correct_matches.yaml and are already validated.
 * Only entries that need user validation are displayed in this interface.
 */
const BrushValidation: React.FC = () => {
    // State management
    const [selectedMonths, setSelectedMonths] = useState<string[]>([]);
    const [selectedSystem] = useState<SystemType>('scoring'); // Only scoring system supported
    const [sortBy, setSortBy] = useState<SortType>('unvalidated');
    const [currentPage, setCurrentPage] = useState(1);
    const [pageSize, setPageSize] = useState(20);
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
    const [totalCount, setTotalCount] = useState<number>(0);

    // UI state
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [overrideState, setOverrideState] = useState<OverrideState | null>(null);
    const [actionInProgress, setActionInProgress] = useState<Set<number>>(new Set());

    // Filter states
    const [showSingleStrategy, setShowSingleStrategy] = useState(true);
    const [showMultipleStrategy, setShowMultipleStrategy] = useState(true);

    // Comment modal state
    const [selectedComment, setSelectedComment] = useState<CommentDetail | null>(null);
    const [commentModalOpen, setCommentModalOpen] = useState(false);
    const [commentLoading, setCommentLoading] = useState(false);
    const [allComments, setAllComments] = useState<CommentDetail[]>([]);
    const [currentCommentIndex, setCurrentCommentIndex] = useState<number>(0);
    const [remainingCommentIds, setRemainingCommentIds] = useState<string[]>([]);

    // Strategy distribution modal state
    const [strategyDistributionModalOpen, setStrategyDistributionModalOpen] = useState(false);
    const [strategyDistributionStatistics, setStrategyDistributionStatistics] =
        useState<StrategyDistributionStatistics | null>(null);

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
        if (!currentMonth) return;

        try {
            setLoading(true);

            // Use backend filtering instead of frontend filtering
            const data = await getBrushValidationData(currentMonth, 'scoring', {
                sortBy,
                page: 1,
                pageSize: 500, // Maximum allowed by backend
                // Pass filter parameters to backend - avoid conflicts
                showValidated: showValidated,
                // Set strategyCount based on filter combination
                strategyCount: (() => {
                    if (showSingleStrategy && !showMultipleStrategy) return 1;
                    if (!showSingleStrategy && showMultipleStrategy) return 2; // Show multiple (2+ strategies)
                    if (showSingleStrategy && showMultipleStrategy) return undefined; // Show all
                    return undefined; // Both false - show nothing
                })(),
                // Don't send conflicting boolean flags
                showSingleStrategy: undefined,
                showMultipleStrategy: undefined
            });

            setEntries(data.entries);
            setPagination(data.pagination);

            // Store the total count from backend for accurate pagination
            if (data.pagination && data.pagination.total) {
                setTotalCount(data.pagination.total);
            } else {
                setTotalCount(data.entries.length);
            }

            // Debug: Log the actual response structure
            console.log('🔍 Backend API Response:', {
                entriesLength: data.entries.length,
                pagination: data.pagination,
                hasPagination: !!data.pagination,
                hasTotal: !!(data.pagination && data.pagination.total),
                totalFromPagination: data.pagination?.total,
                totalCount: data.pagination?.total || data.entries.length,
                responseKeys: Object.keys(data)
            });
        } catch (error) {
            console.error('Error loading validation data:', error);
            setError('Failed to load validation data');
        } finally {
            setLoading(false);
        }
    }, [currentMonth, showValidated, showSingleStrategy, showMultipleStrategy, sortBy]);

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

    // Load strategy distribution statistics
    const loadStrategyDistributionStatistics = useCallback(async () => {
        try {
            setStrategyDistributionStatistics(null);

            const stats = await getStrategyDistributionStatistics(currentMonth);

            setStrategyDistributionStatistics(stats);
        } catch (error) {
            console.error('Error loading strategy distribution statistics:', error);
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
        loadStrategyDistributionStatistics();
    }, [loadStrategyDistributionStatistics]);

    useEffect(() => {
        setCurrentPage(1); // Reset to first page when filters change
    }, [selectedSystem, sortBy]);

    // Reset to page 1 when entries change and current page becomes invalid
    useEffect(() => {
        const totalPages = Math.ceil(entries.length / pageSize);
        if (currentPage > totalPages && totalPages > 0) {
            setCurrentPage(1);
        }
    }, [entries.length, currentPage, pageSize]);

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
        async (entry: BrushValidationEntry) => {
            if (!entry || !currentMonth) return;

            // Find the index in the original entries array for action tracking
            const entryIndex = entries.findIndex(
                e => (e.normalized_text || e.input_text) === (entry.normalized_text || entry.input_text)
            );

            if (entryIndex === -1) return;

            setActionInProgress(prev => new Set(prev).add(entryIndex));

            try {
                // Simplified API call - let the backend handle all the business logic
                await recordBrushValidationAction({
                    input_text: entry.normalized_text || entry.input_text, // Use normalized for operations
                    month: currentMonth,
                    system_used: 'scoring',
                    action: 'validate',
                });

                // Reload data to reflect changes
                await loadValidationData();
                await loadStatistics();
            } catch (err) {
                setError(handleApiError(err));
            } finally {
                setActionInProgress(prev => {
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
        async (entry: BrushValidationEntry, strategyIndex: number) => {
            if (!entry || !currentMonth) return;

            // Find the index in the original entries array for action tracking
            const entryIndex = entries.findIndex(
                e => (e.normalized_text || e.input_text) === (entry.normalized_text || entry.input_text)
            );

            if (entryIndex === -1) return;

            setActionInProgress(prev => new Set(prev).add(entryIndex));

            try {
                // Simplified API call - let the backend handle all the business logic
                await recordBrushValidationAction({
                    input_text: entry.normalized_text || entry.input_text, // Use normalized for operations
                    month: currentMonth,
                    system_used: 'scoring',
                    action: 'override',
                    strategy_index: strategyIndex,
                });

                // Reload data to reflect changes
                await loadValidationData();
                await loadStatistics();
                setOverrideState(null);
            } catch (err) {
                setError(handleApiError(err));
            } finally {
                setActionInProgress(prev => {
                    const newSet = new Set(prev);
                    newSet.delete(entryIndex);
                    return newSet;
                });
            }
        },
        [entries, currentMonth, loadValidationData, loadStatistics]
    );

    // Handle undo action
    const handleUndo = useCallback(async () => {
        if (!currentMonth) return;

        setActionInProgress(prev => new Set(prev).add(-1)); // Use -1 as special index for undo

        try {
            const response = await undoLastValidationAction(currentMonth);

            if (response.success) {
                // Reload data to reflect changes
                await loadValidationData();
                await loadStatistics();
            } else {
                setError(response.message || 'Failed to undo last action');
            }
        } catch (err) {
            setError(handleApiError(err));
        } finally {
            setActionInProgress(prev => {
                const newSet = new Set(prev);
                newSet.delete(-1);
                return newSet;
            });
        }
    }, [currentMonth, loadValidationData, loadStatistics]);

    // Backend is now handling filtering, so we use entries directly
    const displayEntries = entries;

    // Calculate pagination for frontend display
    const totalEntries = totalCount || entries.length; // Use backend total count if available
    const totalPages = Math.ceil(totalEntries / pageSize);
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    const paginatedEntries = entries.slice(startIndex, endIndex);

    // Update pagination state for frontend pagination
    const frontendPagination = {
        page: currentPage,
        page_size: pageSize,
        total: totalEntries,
        pages: totalPages
    };

    // Effect to handle validated filter by changing sort order
    useEffect(() => {
        if (!showValidated && sortBy !== 'unvalidated') {
            setSortBy('unvalidated');
        }
    }, [showValidated, sortBy]);

    if (error) {
        return (
            <div className='w-full p-4'>
                <ErrorDisplay error={error} onRetry={() => loadValidationData()} />
            </div>
        );
    }

    return (
        <div className='w-full p-4 space-y-6'>
            {/* Header */}
            <div className='flex items-center justify-between'>
                <h1 className='text-2xl font-bold'>Brush Validation</h1>
                <Badge variant='outline' className='text-sm'>
                    Scoring System Validation Interface
                </Badge>
            </div>

            {/* Info Note */}
            <Card className='bg-blue-50 border-blue-200'>
                <CardContent className='p-4'>
                    <div className='text-sm text-blue-800'>
                        <strong>Note:</strong> Entries that were automatically matched from{' '}
                        <code className='bg-blue-100 px-1 rounded'>correct_matches.yaml</code> (with strategies{' '}
                        <code className='bg-blue-100 px-1 rounded'>correct_complete_brush</code> or{' '}
                        <code className='bg-blue-100 px-1 rounded'>correct_split_brush</code>) are filtered out{' '}
                        since they are already validated and don't require user review.
                    </div>
                </CardContent>
            </Card>

            {/* Month Selection */}
            <Card>
                <CardHeader>
                    <CardTitle className='text-lg'>Month Selection</CardTitle>
                </CardHeader>
                <CardContent>
                    <MonthSelector
                        selectedMonths={selectedMonths}
                        onMonthsChange={handleMonthsChange}
                        multiple={false}
                    />
                </CardContent>
            </Card>

            {/* Controls */}
            {currentMonth && (
                <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
                    {/* Sort Options */}
                    <Card>
                        <CardHeader>
                            <CardTitle className='text-sm flex items-center gap-2'>
                                <SortAsc className='h-4 w-4' />
                                Sort Order
                            </CardTitle>
                        </CardHeader>
                        <CardContent className='space-y-2'>
                            <Button
                                variant={sortBy === 'unvalidated' ? 'default' : 'outline'}
                                onClick={() => handleSortChange('unvalidated')}
                                className='w-full'
                            >
                                Sort by Unvalidated
                            </Button>
                            <Button
                                variant={sortBy === 'validated' ? 'default' : 'outline'}
                                onClick={() => handleSortChange('validated')}
                                className='w-full'
                            >
                                Sort by Validated
                            </Button>
                            <Button
                                variant={sortBy === 'ambiguity' ? 'default' : 'outline'}
                                onClick={() => handleSortChange('ambiguity')}
                                className='w-full'
                            >
                                Sort by Ambiguity
                            </Button>
                        </CardContent>
                    </Card>

                    {/* Page Size and Statistics */}
                    <div className='space-y-4'>
                        {/* Page Size Selector */}
                        <Card>
                            <CardHeader>
                                <CardTitle className='text-sm flex items-center gap-2'>
                                    <Filter className='h-4 w-4' />
                                    Page Size
                                </CardTitle>
                            </CardHeader>
                            <CardContent className='space-y-2'>
                                <div className='flex gap-2'>
                                    {[10, 20, 50, 100].map((size) => (
                                        <Button
                                            key={size}
                                            variant={pageSize === size ? 'default' : 'outline'}
                                            size='sm'
                                            onClick={() => {
                                                setPageSize(size);
                                                setCurrentPage(1); // Reset to first page when changing page size
                                            }}
                                            className='flex-1'
                                        >
                                            {size}
                                        </Button>
                                    ))}
                                </div>
                                <div className='text-xs text-gray-500'>
                                    Showing {Math.min(pageSize, entries.length)} of {totalEntries} entries
                                </div>
                            </CardContent>
                        </Card>

                        {/* Statistics */}
                        {statistics && (
                            <Card>
                                <CardHeader>
                                    <CardTitle className='text-sm flex items-center gap-2'>
                                        <BarChart3 className='h-4 w-4' />
                                        Statistics
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className='space-y-2'>
                                    <div className='flex items-center gap-4 text-sm text-gray-600'>
                                        <span>
                                            <strong>Total:</strong> {statistics.total_entries}
                                        </span>
                                        <span>
                                            <strong>Validated:</strong> {statistics.validated_count}
                                        </span>
                                        <span>
                                            <strong>Unvalidated:</strong> {statistics.unvalidated_count}
                                        </span>
                                        <span>
                                            <strong>Rate:</strong> {statistics.validation_rate.toFixed(1)}%
                                        </span>
                                    </div>
                                </CardContent>
                            </Card>
                        )}
                    </div>
                </div>
            )}

            {/* Action Buttons */}
            {currentMonth && (
                <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
                    {/* Undo Button */}
                    <Card>
                        <CardHeader>
                            <CardTitle className='text-sm flex items-center gap-2'>
                                <RotateCcw className='h-4 w-4' />
                                Undo Last Action
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <Button
                                variant='outline'
                                onClick={handleUndo}
                                disabled={actionInProgress.has(-1)} // Use -1 as special index for undo
                                className='flex items-center gap-2 text-orange-600 border-orange-200 hover:bg-orange-50'
                            >
                                {actionInProgress.has(-1) ? (
                                    <Loader2 className='h-4 w-4 animate-spin' />
                                ) : (
                                    <RotateCcw className='h-4 w-4' />
                                )}
                                Undo Last Validation
                            </Button>
                            <div className='text-xs text-gray-500 mt-2'>
                                Removes the last validation/override action from both the learning file and
                                correct_matches.yaml
                            </div>
                        </CardContent>
                    </Card>

                    {/* Strategy Distribution Button */}
                    <Card>
                        <CardHeader>
                            <CardTitle className='text-sm flex items-center gap-2'>
                                <PieChart className='h-4 w-4' />
                                Strategy Analysis
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <Button
                                variant='outline'
                                onClick={() => setStrategyDistributionModalOpen(true)}
                                className='flex items-center gap-2 text-blue-600 border-blue-200 hover:bg-blue-50'
                            >
                                <BarChart3 className='h-4 w-4' />
                                View Strategy Distribution
                            </Button>
                            <div className='text-xs text-gray-500 mt-2'>
                                Analyze strategy distribution and debug filter count mismatches
                            </div>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Filter Options */}
            {currentMonth && (
                <>
                    {/* Debug Info */}
                    <Card className='bg-yellow-50 border-yellow-200'>
                        <CardHeader>
                            <CardTitle className='text-sm flex items-center gap-2'>🐛 Debug Info</CardTitle>
                        </CardHeader>
                        <CardContent className='space-y-2'>
                            <div className='text-xs text-yellow-800 space-y-1'>
                                <div>
                                    <strong>Current Filters:</strong>
                                </div>
                                <div>• showValidated: {showValidated ? 'true' : 'false'}</div>
                                <div>• showSingleStrategy: {showSingleStrategy ? 'true' : 'false'}</div>
                                <div>• showMultipleStrategy: {showMultipleStrategy ? 'true' : 'false'}</div>
                                <div>• sortBy: {sortBy}</div>
                                <div>• Total entries loaded: {entries.length}</div>
                                <div>• Filtered entries: {entries.length}</div>
                                {strategyDistributionStatistics && (
                                    <>
                                        <div>• Strategy counts from API:</div>
                                        <div className='ml-4'>
                                            {Object.entries(strategyDistributionStatistics.all_strategies_lengths).map(
                                                ([key, count]) => (
                                                    <div key={key}>
                                                        {' '}
                                                        - {key}: {count}
                                                    </div>
                                                )
                                            )}
                                        </div>
                                    </>
                                )}
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle className='text-sm flex items-center gap-2'>
                                <Filter className='h-4 w-4' />
                                Display Options
                            </CardTitle>
                        </CardHeader>
                        <CardContent className='space-y-3'>
                            <div className='flex flex-wrap gap-2 items-center'>
                                <Button
                                    variant={showValidated ? 'outline' : 'default'}
                                    onClick={() => setShowValidated(!showValidated)}
                                    className='flex items-center gap-2'
                                >
                                    {showValidated ? 'Hide Validated' : 'Show Validated'}
                                    <Badge variant='secondary'>{statistics?.validated_count || 0}</Badge>
                                </Button>

                                <div className='flex flex-col gap-2'>
                                    <label className='text-sm font-medium text-gray-700'>Strategy Count</label>
                                    <div className='flex gap-2'>
                                        <button
                                            type='button'
                                            onClick={() => setShowSingleStrategy(!showSingleStrategy)}
                                            className={`px-3 py-2 text-sm rounded-md transition-colors ${showSingleStrategy
                                                ? 'bg-blue-600 text-white'
                                                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                                                }`}
                                        >
                                            {showSingleStrategy ? 'Hide' : 'Show'} Single Strategy
                                            <span className='ml-2 px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded'>
                                                {(() => {
                                                    const count =
                                                        strategyDistributionStatistics?.all_strategies_lengths['1'] || 0;
                                                    return count;
                                                })()}
                                            </span>
                                        </button>
                                        <button
                                            type='button'
                                            onClick={() => setShowMultipleStrategy(!showMultipleStrategy)}
                                            className={`px-3 py-2 text-sm rounded-md transition-colors ${showMultipleStrategy
                                                ? 'bg-blue-600 text-white'
                                                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                                                }`}
                                        >
                                            {showMultipleStrategy ? 'Hide' : 'Show'} Multiple Strategy
                                            <span className='ml-2 px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded'>
                                                {(() => {
                                                    const count = strategyDistributionStatistics
                                                        ? Object.entries(strategyDistributionStatistics.all_strategies_lengths)
                                                            .filter(([key]) => key !== 'None' && key !== '1')
                                                            .reduce((sum, [, count]) => sum + count, 0)
                                                        : 0;
                                                    return count;
                                                })()}
                                            </span>
                                        </button>
                                    </div>
                                </div>

                                {/* Note about strategy counts */}
                                <div className='text-xs text-gray-500 mt-2'>
                                    Strategy counts show unvalidated entries only.
                                </div>

                                <Button variant='outline' disabled className='flex items-center gap-2'>
                                    Missing Data
                                    <Badge variant='destructive'>
                                        {strategyDistributionStatistics
                                            ? strategyDistributionStatistics.all_strategies_lengths['None'] || 0
                                            : 0}
                                    </Badge>
                                </Button>
                            </div>

                            <div className='text-xs text-gray-500'>
                                <div>
                                    • <strong>Validated:</strong> Entries that have been processed (filtered by
                                    backend)
                                </div>
                                <div>
                                    • <strong>Single Strategy:</strong> Entries with only one matching strategy
                                    (straightforward cases)
                                </div>
                                <div>
                                    • <strong>Multiple Strategies:</strong> Entries with multiple competing strategies
                                    (need validation decisions)
                                </div>
                                <div>
                                    • <strong>Missing Data:</strong> Entries without strategy information (need
                                    investigation)
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </>
            )}

            {/* Loading State */}
            {loading && (
                <Card>
                    <CardContent className='p-6'>
                        <div className='flex items-center justify-center space-x-2'>
                            <Loader2 className='h-4 w-4 animate-spin' />
                            <span>Loading validation data...</span>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Page Info */}
            {!loading && entries.length > 0 && (
                <Card className='bg-gray-50'>
                    <CardContent className='p-4'>
                        <div className='flex items-center justify-between text-sm text-gray-600'>
                            <div>
                                Showing entries {startIndex + 1}-{Math.min(endIndex, entries.length)} of {totalEntries}
                            </div>
                            <div>
                                Page {currentPage} of {totalPages}
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Entries List */}
            {!loading && paginatedEntries.length > 0 && (
                <div className='space-y-4'>
                    {paginatedEntries.map((entry, index) => (
                        <Card key={index} className='relative'>
                            <CardHeader>
                                <div className='flex items-center justify-between'>
                                    <div>
                                        <CardTitle className='text-base'>{entry.input_text}</CardTitle>
                                        {entry.normalized_text && entry.normalized_text !== entry.input_text && (
                                            <div className='text-sm text-gray-500 mt-1'>
                                                Normalized: {entry.normalized_text}
                                            </div>
                                        )}
                                    </div>
                                    <div className='flex items-center gap-2'>
                                        {entry.matched && entry.matched.score && (
                                            <Badge variant='outline'>Score: {entry.matched.score}</Badge>
                                        )}
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent className='space-y-4'>
                                {/* Entry Details */}
                                <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
                                    {/* System Results */}
                                    <div>
                                        <h4 className='font-medium mb-2'>System Result:</h4>
                                        <div className='text-sm space-y-1'>
                                            {entry.matched ? (
                                                <>
                                                    <div>
                                                        <span className='font-medium'>Strategy:</span>{' '}
                                                        {entry.matched.strategy || 'Unknown'}
                                                    </div>
                                                    <div>
                                                        <span className='font-medium'>Score:</span>{' '}
                                                        {entry.matched.score || 'Unknown'}
                                                    </div>
                                                    <div>
                                                        <span className='font-medium'>Brand:</span>{' '}
                                                        {entry.matched?.brand || 'N/A'}
                                                    </div>
                                                    <div>
                                                        <span className='font-medium'>Model:</span>{' '}
                                                        {entry.matched?.model || 'N/A'}
                                                    </div>
                                                    {entry.matched.handle && (
                                                        <div>
                                                            <span className='font-medium'>Handle:</span>{' '}
                                                            {entry.matched.handle.brand} {entry.matched.handle.model}
                                                        </div>
                                                    )}
                                                    {entry.matched.knot && (
                                                        <div>
                                                            <span className='font-medium'>Knot:</span> {entry.matched.knot.brand}{' '}
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
                                    {entry.all_strategies && entry.all_strategies.length > 0 && (
                                        <div>
                                            <h4 className='font-medium mb-2'>Alternative Strategies:</h4>
                                            <div className='text-sm space-y-2 max-h-64 overflow-y-auto'>
                                                {entry.all_strategies
                                                    .filter(strategy => {
                                                        // Filter out the winning strategy - compare result data to identify the winner
                                                        if (!strategy.result || !entry.matched) return true;

                                                        // Extract brand and model for comparison
                                                        const systemBrand = entry.matched?.brand;
                                                        const systemModel = entry.matched?.model;
                                                        const strategyBrand = strategy.result?.brand;
                                                        const strategyModel = strategy.result?.model;

                                                        // Check if this strategy's result matches the winning result
                                                        const isWinner =
                                                            strategyBrand === systemBrand &&
                                                            strategyModel === systemModel &&
                                                            strategy.strategy === entry.matched.strategy &&
                                                            strategy.score === entry.matched.score;

                                                        return !isWinner;
                                                    })
                                                    .map((strategy, strategyIndex) => (
                                                        <div
                                                            key={strategyIndex}
                                                            className={`p-3 rounded border ${overrideState?.entryIndex === index &&
                                                                overrideState?.selectedStrategy === strategyIndex
                                                                ? 'bg-blue-50 border-blue-200'
                                                                : 'bg-gray-50 border-gray-200'
                                                                }`}
                                                        >
                                                            <div className='flex justify-between items-center mb-2'>
                                                                <span className='font-medium capitalize'>
                                                                    {strategy.strategy.replace(/_/g, ' ')}
                                                                </span>
                                                                <Badge variant='outline' className='text-xs'>
                                                                    Score: {strategy.score}
                                                                </Badge>
                                                            </div>
                                                            {strategy.result && (
                                                                <div className='space-y-1 text-gray-700'>
                                                                    <div className='text-xs'>
                                                                        <span className='font-medium'>Brand:</span>{' '}
                                                                        {strategy.result?.brand || 'N/A'}
                                                                    </div>
                                                                    <div className='text-xs'>
                                                                        <span className='font-medium'>Model:</span>{' '}
                                                                        {strategy.result?.model || 'N/A'}
                                                                    </div>
                                                                    {strategy.result.handle && (
                                                                        <div className='text-xs'>
                                                                            <span className='font-medium'>Handle:</span>{' '}
                                                                            {strategy.result.handle.brand} {strategy.result.handle.model}
                                                                        </div>
                                                                    )}
                                                                    {strategy.result.knot && (
                                                                        <div className='text-xs'>
                                                                            <span className='font-medium'>Knot:</span>{' '}
                                                                            {strategy.result.knot.brand} {strategy.result.knot.model}
                                                                            {strategy.result.knot.fiber &&
                                                                                ` (${strategy.result.knot.fiber})`}
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
                                    <div className='border-t pt-4'>
                                        <h4 className='font-medium mb-2 flex items-center gap-2'>
                                            <MessageSquare className='h-4 w-4' />
                                            Comment References ({entry.comment_ids.length})
                                        </h4>
                                        <div className='flex flex-wrap gap-2'>
                                            {entry.comment_ids.map((commentId, commentIndex) => (
                                                <Button
                                                    key={commentIndex}
                                                    variant='outline'
                                                    size='sm'
                                                    onClick={() => handleCommentClick(commentId, entry.comment_ids)}
                                                    disabled={commentLoading}
                                                    className='text-xs h-8 px-2'
                                                >
                                                    {commentLoading ? (
                                                        <Loader2 className='h-3 w-3 animate-spin' />
                                                    ) : (
                                                        <>
                                                            <MessageSquare className='h-3 w-3 mr-1' />
                                                            {commentId}
                                                        </>
                                                    )}
                                                </Button>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Override Strategy Selection */}
                                {overrideState?.entryIndex === index && entry.all_strategies && (
                                    <div className='border-t pt-4'>
                                        <h4 className='font-medium mb-2'>Select Alternative Strategy:</h4>
                                        <div className='space-y-2'>
                                            {entry.all_strategies.map((strategy, strategyIndex) => (
                                                <Button
                                                    key={strategyIndex}
                                                    variant={
                                                        overrideState.selectedStrategy === strategyIndex ? 'default' : 'outline'
                                                    }
                                                    onClick={() =>
                                                        setOverrideState({
                                                            entryIndex: index,
                                                            selectedStrategy: strategyIndex,
                                                        })
                                                    }
                                                    className='w-full justify-between'
                                                >
                                                    <span>
                                                        {strategy.strategy} ({strategy.score})
                                                    </span>
                                                </Button>
                                            ))}
                                        </div>
                                        <div className='flex gap-2 mt-4'>
                                            <Button
                                                onClick={() => handleOverride(entry, overrideState.selectedStrategy)}
                                                disabled={actionInProgress.has(
                                                    entries.findIndex(
                                                        e =>
                                                            (e.normalized_text || e.input_text) ===
                                                            (entry.normalized_text || entry.input_text)
                                                    )
                                                )}
                                                className='flex items-center gap-2'
                                            >
                                                {actionInProgress.has(
                                                    entries.findIndex(
                                                        e =>
                                                            (e.normalized_text || e.input_text) ===
                                                            (entry.normalized_text || entry.input_text)
                                                    )
                                                ) ? (
                                                    <Loader2 className='h-4 w-4 animate-spin' />
                                                ) : (
                                                    <Check className='h-4 w-4' />
                                                )}
                                                Confirm Override
                                            </Button>
                                            <Button variant='outline' onClick={() => setOverrideState(null)}>
                                                Cancel
                                            </Button>
                                        </div>
                                    </div>
                                )}

                                {/* Action Buttons */}
                                {overrideState?.entryIndex !== index && (
                                    <div className='flex gap-2 pt-4 border-t'>
                                        <Button
                                            onClick={() => handleValidate(entry)}
                                            disabled={actionInProgress.has(
                                                entries.findIndex(
                                                    e =>
                                                        (e.normalized_text || e.input_text) ===
                                                        (entry.normalized_text || entry.input_text)
                                                )
                                            )}
                                            className='flex items-center gap-2 bg-green-600 hover:bg-green-700'
                                        >
                                            {actionInProgress.has(
                                                entries.findIndex(
                                                    e =>
                                                        (e.normalized_text || e.input_text) ===
                                                        (entry.normalized_text || entry.input_text)
                                                )
                                            ) ? (
                                                <Loader2 className='h-4 w-4 animate-spin' />
                                            ) : (
                                                <Check className='h-4 w-4' />
                                            )}
                                            Validate
                                        </Button>
                                        {entry.all_strategies && entry.all_strategies.length > 0 && (
                                            <Button
                                                variant='outline'
                                                onClick={() =>
                                                    setOverrideState({
                                                        entryIndex: index,
                                                        selectedStrategy: 0,
                                                    })
                                                }
                                                className='flex items-center gap-2'
                                            >
                                                <RotateCcw className='h-4 w-4' />
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
            {frontendPagination && entries.length > 0 && (
                <Card>
                    <CardContent className='p-4'>
                        <div className='flex items-center justify-between'>
                            <div className='text-sm text-gray-600'>
                                Page {frontendPagination.page} of {frontendPagination.pages} • {frontendPagination.total} total entries
                            </div>
                            <div className='flex items-center space-x-2'>
                                <Button
                                    variant='outline'
                                    size='sm'
                                    onClick={() => handlePageChange(frontendPagination.page - 1)}
                                    disabled={frontendPagination.page <= 1}
                                >
                                    <ChevronLeft className='h-4 w-4' />
                                    Previous
                                </Button>
                                <Button
                                    variant='outline'
                                    size='sm'
                                    onClick={() => handlePageChange(frontendPagination.page + 1)}
                                    disabled={frontendPagination.page >= frontendPagination.pages}
                                >
                                    Next
                                    <ChevronRight className='h-4 w-4' />
                                </Button>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Empty State */}
            {!loading && paginatedEntries.length === 0 && currentMonth && (
                <Card>
                    <CardContent className='p-6 text-center'>
                        <div className='text-gray-500'>
                            {entries.length === 0
                                ? 'No validation data found for the selected month.'
                                : totalPages > 1 && currentPage > totalPages
                                    ? 'Page number exceeds available pages. Please go back to a valid page.'
                                    : 'No entries match the current filter criteria.'}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* No Month Selected State */}
            {!currentMonth && (
                <Card>
                    <CardContent className='p-6 text-center'>
                        <div className='text-gray-500'>Please select a month to begin validation.</div>
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

            {/* Strategy Distribution Modal */}
            {strategyDistributionStatistics && (
                <StrategyDistributionModal
                    isOpen={strategyDistributionModalOpen}
                    onClose={() => setStrategyDistributionModalOpen(false)}
                    statistics={strategyDistributionStatistics}
                    month={currentMonth}
                />
            )}
        </div>
    );
};

export default BrushValidation;
