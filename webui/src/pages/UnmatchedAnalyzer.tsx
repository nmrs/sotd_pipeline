import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  analyzeUnmatched,
  UnmatchedAnalysisResult,
  handleApiError,
  runMatchPhase,
  MatchPhaseRequest,
  getCommentDetail,
  CommentDetail,
} from '../services/api';
import MonthSelector from '../components/forms/MonthSelector';
import LoadingSpinner from '../components/layout/LoadingSpinner';
import ErrorDisplay from '../components/feedback/ErrorDisplay';
import { UnmatchedAnalyzerDataTable } from '../components/data/UnmatchedAnalyzerDataTable';
import PerformanceMonitor from '../components/domain/PerformanceMonitor';
import CommentModal from '../components/domain/CommentModal';
import BrushTable from '../components/data/BrushTable';

import { BrushData } from '../utils/brushDataTransformer';

import { useViewState } from '../hooks/useViewState';
import { useSearchSort } from '../hooks/useSearchSort';
import { useMessaging } from '../hooks/useMessaging';
import MessageDisplay from '../components/feedback/MessageDisplay';
import { checkFilteredStatus } from '../services/api';

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
  const [reasonText, setReasonText] = useState<string>('');

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

  // Load filtered status from backend
  const loadFilteredStatus = useCallback(async (items: any[], category: string) => {
    if (!items || items.length === 0) return;

    try {
      const entries = items.map(item => ({
        category,
        name: item.item,
      }));

      console.log('Loading filtered status for:', category, 'entries:', entries);
      console.log(
        'Entries being sent to backend:',
        entries.map(e => e.name)
      );
      const response = await checkFilteredStatus({ entries });

      if (response.success) {
        const newFilteredStatus: Record<string, boolean> = {};

        // Parse the response data to extract filtered status
        Object.entries(response.data).forEach(([key, isFiltered]) => {
          // Key format is "category:itemName"
          const itemName = key.split(':')[1];
          if (itemName) {
            newFilteredStatus[itemName] = isFiltered;
          }
        });

        console.log('Loaded filtered status:', newFilteredStatus);
        setFilteredStatus(newFilteredStatus);
      }
    } catch (err: any) {
      console.warn('Failed to load filtered status:', err);
      // Don't show error to user, just log it
    }
  }, []);

  const fieldOptions = [
    { value: 'razor', label: 'Razor' },
    { value: 'blade', label: 'Blade' },
    { value: 'brush', label: 'Brush' },
    { value: 'soap', label: 'Soap' },
  ];

  const handleAnalyze = async (retryCount = 0) => {
    if (selectedMonths.length === 0) {
      messaging.addErrorMessage('Please select at least one month');
      return;
    }

    try {
      setLoading(true);
      setResults(null);
      setOperationCount(prev => prev + 1);

      // Analyze unmatched items
      console.log('Analyzing unmatched items...');

      const result = await analyzeUnmatched({
        field: selectedField,
        months: selectedMonths,
        limit,
      });

      // Validate the response structure
      if (result && typeof result === 'object') {
        console.log(
          'Received API response with items:',
          result.unmatched_items?.map(item => item.item)
        );

        // Check for partial results
        if (result.partial_results) {
          messaging.addWarningMessage(
            `Partial results: ${result.error || 'Some items could not be processed'}. ` +
              'Only available data is shown.'
          );
        }

        setResults(result);
        // Load filtered status after analysis results are loaded
        await loadFilteredStatus(result.unmatched_items || [], selectedField);
      } else {
        throw new Error('Invalid response format from API');
      }
    } catch (err: any) {
      const errorMessage = handleApiError(err);

      // Provide specific recovery suggestions based on error type
      let recoverySuggestion = '';
      if (errorMessage.includes('File not found')) {
        recoverySuggestion =
          'Check if the pipeline has been run for the selected months. Try running the pipeline first.';
      } else if (errorMessage.includes('Network error') || errorMessage.includes('fetch')) {
        recoverySuggestion = 'Check your network connection and try again.';
      } else if (errorMessage.includes('timeout')) {
        recoverySuggestion = 'The request timed out. Try with fewer months or a smaller limit.';
      }

      if (recoverySuggestion) {
        messaging.addErrorMessage(`${errorMessage} ${recoverySuggestion}`);
      } else {
        messaging.addErrorMessage(errorMessage);
      }

      // Implement retry mechanism for transient errors
      if (
        retryCount < 2 &&
        (errorMessage.includes('Network error') || errorMessage.includes('timeout'))
      ) {
        setTimeout(
          () => {
            messaging.addInfoMessage(`Retrying... (attempt ${retryCount + 2}/3)`);
            handleAnalyze(retryCount + 1);
          },
          1000 * (retryCount + 1)
        ); // Exponential backoff
        return;
      }
    } finally {
      setLoading(false);
    }
  };

  const formatExamples = (examples: string[]) => {
    if (examples.length === 0) return 'No examples available';
    return examples.slice(0, 3).join(', ') + (examples.length > 3 ? '...' : '');
  };

  // Transform API response data to BrushTable format
  const transformApiDataToBrushTable = (items: any[]): BrushData[] => {
    const result = items.map(item => {
      const transformed = {
        main: {
          text: item.item,
          count: item.count,
          comment_ids: item.comment_ids || [],
          examples: item.examples || [],
          status: 'Unmatched' as const,
        },
        components: {
          handle: item.unmatched?.handle
            ? {
                text: item.unmatched.handle.text,
                status: 'Unmatched' as const,
                pattern: item.unmatched.handle.pattern,
              }
            : undefined,
          knot: item.unmatched?.knot
            ? {
                text: item.unmatched.knot.text,
                status: 'Unmatched' as const,
                pattern: item.unmatched.knot.pattern,
              }
            : undefined,
        },
      };

      return transformed;
    });

    return result;
  };

  // Memoize the transformed brush data to prevent unnecessary re-renders
  const transformedBrushData = useMemo(() => {
    if (selectedField === 'brush' && searchSort.filteredAndSortedItems) {
      const data = transformApiDataToBrushTable(searchSort.filteredAndSortedItems as any[]);
      return data;
    }
    return [];
  }, [selectedField, searchSort.filteredAndSortedItems]);

  // Column widths for different table types
  const productColumnWidths = {
    filtered: 100,
    item: 200,
    count: 80,
    comment_ids: 150,
    examples: 200,
  };

  const brushColumnWidths = {
    filtered: 100,
    brush: 200,
    handle: 200,
    knot: 200,
    count: 80,
    comment_ids: 150,
    examples: 200,
  };

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

  const handleFilteredStatusChange = useCallback(
    (itemName: string, isFiltered: boolean) => {
      const currentStatus = filteredStatus[itemName] || false;
      console.log(
        'Filtered status change:',
        itemName,
        'isFiltered:',
        isFiltered,
        'currentStatus:',
        currentStatus
      );

      setPendingChanges(prev => {
        const newChanges = { ...prev };

        if (isFiltered === currentStatus) {
          // If the new value matches the current status, remove from pending changes
          delete newChanges[itemName];
        } else {
          // If the new value is different, add to pending changes
          newChanges[itemName] = isFiltered;
        }

        console.log('Updated pending changes:', newChanges);
        return newChanges;
      });
    },
    [filteredStatus]
  );

  const handleApplyFilteredChanges = async () => {
    if (Object.keys(pendingChanges).length === 0) {
      messaging.addSuccessMessage('No changes to apply');
      return;
    }

    // Log reason if provided (for development/debugging)
    if (reasonText.trim()) {
      // Removed debug console.log for performance
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

          // Send one entry per item, not per comment_id
          // Use the first comment_id as representative
          const firstCommentId = item.comment_ids[0];
          if (firstCommentId) {
            allEntries.push({
              name: itemName,
              action: shouldBeFiltered ? 'add' : 'remove',
              comment_id: firstCommentId,
              source: 'user',
              month,
            });
          }
        }
      });

      if (allEntries.length === 0) {
        messaging.addSuccessMessage('No changes to apply');
        return;
      }

      // Debug: Log what we're sending
      // Removed debug console.log for performance

      // Import the API function
      const { updateFilteredEntries } = await import('../services/api');

      const response = await updateFilteredEntries({
        category: selectedField,
        entries: allEntries,
        reason: reasonText.trim() || undefined,
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

      // Clear reason text
      setReasonText('');

      messaging.addSuccessMessage(
        `Updated ${Object.keys(pendingChanges).length} entries successfully`
      );
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
      // Removed debug console.log statements for performance
    }
  }, [results, viewState.showFiltered]);

  // Clear filtered status when field changes
  useEffect(() => {
    setFilteredStatus({});
  }, [selectedField]);

  return (
    <div data-testid='unmatched-analyzer' className='h-screen flex flex-col'>
      {/* Sticky Header */}
      <div className='sticky top-0 z-20 bg-white border-b border-gray-200 p-4 shadow-sm'>
        <h1 className='text-2xl font-bold text-gray-900 mb-4'>Unmatched Item Analyzer</h1>
        <p className='text-gray-600 mb-4'>
          Analyze unmatched items across selected months to identify patterns and potential catalog
          additions.
        </p>

        {/* Configuration Controls */}
        <div className='space-y-4'>
          {/* Row 1: Field, Months, Limit */}
          <div className='flex flex-wrap items-center gap-4'>
            {/* Field Selection */}
            <div className='flex items-center space-x-2'>
              <label className='text-sm font-medium text-gray-700'>Field:</label>
              <select
                value={selectedField}
                onChange={e => setSelectedField(e.target.value)}
                className='border border-gray-300 rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500'
              >
                {fieldOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Month Selection */}
            <div className='flex items-center space-x-2'>
              <label className='text-sm font-medium text-gray-700'>Months:</label>
              <div className='flex-1 min-w-0'>
                <MonthSelector
                  selectedMonths={selectedMonths}
                  onMonthsChange={setSelectedMonths}
                  label=''
                />
              </div>
            </div>

            {/* Limit Selection */}
            <div className='flex items-center space-x-2'>
              <label className='text-sm font-medium text-gray-700'>Limit:</label>
              <input
                type='number'
                value={limit}
                onChange={e => setLimit(parseInt(e.target.value) || 50)}
                min='1'
                max='1000'
                className='w-20 border border-gray-300 rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500'
              />
            </div>

            {/* Performance Monitor */}
            <div className='ml-auto'>
              <PerformanceMonitor
                dataSize={results?.unmatched_items?.length || 0}
                operationCount={operationCount}
              />
            </div>
          </div>

          {/* Row 2: Action Buttons */}
          <div className='flex flex-wrap items-center gap-2'>
            <button
              onClick={() => handleAnalyze()}
              disabled={loading || selectedMonths.length === 0}
              className='bg-blue-600 text-white py-1 px-3 rounded text-sm hover:bg-blue-700 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed'
            >
              {loading ? 'Analyzing...' : 'Analyze'}
            </button>

            <button
              onClick={() => {
                console.log('Manual refresh triggered');
                setResults(null);
                setFilteredStatus({});
                setPendingChanges({});
              }}
              className='bg-gray-600 text-white py-1 px-3 rounded text-sm hover:bg-gray-700 focus:outline-none focus:ring-1 focus:ring-gray-500'
            >
              Clear Cache
            </button>

            <button
              onClick={handleRunMatchPhase}
              disabled={matchPhaseLoading || selectedMonths.length === 0}
              className='bg-green-600 text-white py-1 px-3 rounded text-sm hover:bg-green-700 focus:outline-none focus:ring-1 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed'
            >
              {matchPhaseLoading ? 'Running...' : 'Match Phase'}
            </button>

            <div className='flex items-center space-x-1'>
              <input
                type='checkbox'
                id='force-match'
                checked={forceMatch}
                onChange={e => setForceMatch(e.target.checked)}
                className='rounded border-gray-300 text-green-600 focus:ring-green-500'
              />
              <label htmlFor='force-match' className='text-xs text-gray-700'>
                Force
              </label>
            </div>
          </div>

          {/* Row 3: Status and Controls */}
          {results && (
            <div className='flex items-center justify-between'>
              <div className='text-sm text-gray-600'>
                {results.field} | {results.months?.join(', ')} | {results.total_unmatched || 0}{' '}
                items | {results.processing_time?.toFixed(2) || '0.00'}s
              </div>
              <div className='flex items-center space-x-2'>
                <button
                  onClick={viewState.toggleShowFiltered}
                  className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                    viewState.showFiltered
                      ? 'bg-gray-600 text-white hover:bg-gray-700'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  {viewState.showFiltered ? 'Hide Filtered' : 'Show Filtered'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Scrollable Content */}
      <div className='flex-1 overflow-hidden'>
        {loading ? (
          <div className='flex items-center justify-center h-full'>
            <LoadingSpinner message='Analyzing unmatched items...' />
          </div>
        ) : results ? (
          <div className='h-full p-4'>
            {matchPhaseOutput && (
              <div className='bg-gray-50 border border-gray-200 rounded-md p-4 mb-4'>
                <div className='flex items-center justify-between mb-2'>
                  <h3 className='text-sm font-medium text-gray-900'>Match Phase Output</h3>
                  <button
                    onClick={() => setMatchPhaseOutput(null)}
                    className='text-gray-400 hover:text-gray-600'
                  >
                    <svg className='h-4 w-4' viewBox='0 0 20 20' fill='currentColor'>
                      <path
                        fillRule='evenodd'
                        d='M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z'
                        clipRule='evenodd'
                      />
                    </svg>
                  </button>
                </div>
                <pre className='text-xs text-gray-700 bg-white p-3 rounded border overflow-x-auto whitespace-pre-wrap'>
                  {matchPhaseOutput}
                </pre>
              </div>
            )}

            {Array.isArray(results.unmatched_items) ? (
              results.unmatched_items.length === 0 ? (
                <div className='flex items-center justify-center h-full'>
                  <div className='text-center'>
                    <div className='text-green-600 text-4xl mb-2'>✓</div>
                    <h3 className='text-base font-medium text-gray-900 mb-1'>No Unmatched Items</h3>
                    <p className='text-sm text-gray-600'>
                      All {results.field} items were successfully matched.
                    </p>
                  </div>
                </div>
              ) : (
                <div className='h-full flex flex-col'>
                  {/* Search and Apply Controls */}
                  <div className='flex items-center justify-between mb-4'>
                    <div className='flex items-center space-x-4'>
                      <div>
                        <h3 className='text-base font-medium text-gray-900'>
                          Top Unmatched Items ({searchSort.searchResultsCount} of{' '}
                          {searchSort.totalItemsCount})
                        </h3>
                      </div>
                    </div>
                    <div className='flex items-center space-x-2'>
                      {/* Apply Changes Button */}
                      {(() => {
                        const visibleItems = searchSort.filteredAndSortedItems.map(
                          item => item.item
                        );
                        const visibleChanges = Object.keys(pendingChanges).filter(itemName =>
                          visibleItems.includes(itemName)
                        );
                        const visibleChangesCount = visibleChanges.length;

                        return (
                          <div className='flex items-center space-x-2'>
                            {visibleChangesCount > 0 && (
                              <input
                                type='text'
                                placeholder='Reason (optional)...'
                                value={reasonText}
                                onChange={e => setReasonText(e.target.value)}
                                className='px-3 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 w-48'
                              />
                            )}
                            <button
                              onClick={handleApplyFilteredChanges}
                              disabled={loading || visibleChangesCount === 0}
                              className={`py-1 px-3 rounded text-sm focus:outline-none focus:ring-1 disabled:cursor-not-allowed ${
                                loading || visibleChangesCount === 0
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
                      <div className='flex items-center space-x-2'>
                        <input
                          type='text'
                          placeholder='Search items...'
                          value={searchSort.searchTerm}
                          onChange={e => searchSort.setSearchTerm(e.target.value)}
                          className='px-3 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500'
                        />
                        {searchSort.searchTerm && (
                          <button
                            onClick={searchSort.clearSearch}
                            className='text-gray-400 hover:text-gray-600'
                          >
                            <svg className='h-4 w-4' viewBox='0 0 20 20' fill='currentColor'>
                              <path
                                fillRule='evenodd'
                                d='M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z'
                                clipRule='evenodd'
                              />
                            </svg>
                          </button>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Table Content */}
                  <div className='flex-1 overflow-hidden'>
                    {selectedField === 'brush' ? (
                      <BrushTable
                        items={transformedBrushData}
                        onBrushFilter={handleFilteredStatusChange}
                        onComponentFilter={handleFilteredStatusChange}
                        filteredStatus={filteredStatus}
                        pendingChanges={pendingChanges}
                        columnWidths={brushColumnWidths}
                        onCommentClick={handleCommentClick}
                        commentLoading={commentLoading}
                      />
                    ) : (
                      <UnmatchedAnalyzerDataTable
                        data={searchSort.filteredAndSortedItems}
                        filteredStatus={filteredStatus}
                        pendingChanges={pendingChanges}
                        onFilteredStatusChange={handleFilteredStatusChange}
                        onCommentClick={handleCommentClick}
                        commentLoading={commentLoading}
                        fieldType={selectedField as 'razor' | 'blade' | 'soap'}
                        columnWidths={productColumnWidths}
                      />
                    )}
                  </div>
                </div>
              )
            ) : (
              <div className='flex items-center justify-center h-full'>
                <div className='text-center'>
                  <div className='text-red-600 text-4xl mb-2'>!</div>
                  <h3 className='text-base font-medium text-gray-900 mb-1'>Invalid Response</h3>
                  <p className='text-sm text-gray-600'>
                    The API did not return valid data. Please try again.
                  </p>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className='flex items-center justify-center h-full'>
            <div className='text-lg text-gray-600'>
              Please select months and click "Analyze" to begin.
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
      <MessageDisplay messages={messaging.messages} onRemoveMessage={messaging.removeMessage} />
    </div>
  );
};

export default UnmatchedAnalyzer;
