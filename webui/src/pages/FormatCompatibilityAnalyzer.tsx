import React, { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import MonthSelector from '@/components/forms/MonthSelector';
import FormatCompatibilityTable from '@/components/data/FormatCompatibilityTable';
import CommentModal from '@/components/domain/CommentModal';
import DeltaMonthsInfoPanel from '@/components/domain/DeltaMonthsInfoPanel';
import LoadingSpinner from '@/components/layout/LoadingSpinner';
import ErrorDisplay from '@/components/feedback/ErrorDisplay';
import {
  analyzeFormatCompatibility,
  FormatCompatibilityResponse,
  FormatCompatibilityResult,
  getCommentDetail,
  CommentDetail,
} from '@/services/api';
import { calculateDeltaMonths, formatDeltaMonths } from '@/utils/deltaMonths';
import { handleApiError } from '@/services/api';

const FormatCompatibilityAnalyzer: React.FC = () => {
  const [selectedMonths, setSelectedMonths] = useState<string[]>([]);
  const [deltaMonths, setDeltaMonths] = useState<string[]>([]);
  const [severityFilter, setSeverityFilter] = useState<'error' | 'warning' | 'all'>('all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<FormatCompatibilityResponse | null>(null);
  const [selectedComment, setSelectedComment] = useState<CommentDetail | null>(null);
  const [commentModalOpen, setCommentModalOpen] = useState(false);
  const [commentLoading, setCommentLoading] = useState(false);
  const [allComments, setAllComments] = useState<CommentDetail[]>([]);
  const [currentCommentIndex, setCurrentCommentIndex] = useState<number>(0);
  const [remainingCommentIds, setRemainingCommentIds] = useState<string[]>([]);

  // Callback for delta months
  const handleDeltaMonthsChange = useCallback((months: string[]) => {
    setDeltaMonths(months);
  }, []);

  const handleMonthChange = (months: string[]) => {
    setSelectedMonths(months);
  };

  const handleAnalyze = async () => {
    if (selectedMonths.length === 0) {
      setError('Please select at least one month to analyze');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setResults(null);

      // When delta months are enabled, selectedMonths already contains all months (primary + delta)
      const allMonths = selectedMonths;

      const result = await analyzeFormatCompatibility({
        months: allMonths,
        severity: severityFilter,
      });

      setResults(result);
    } catch (err: unknown) {
      setError(handleApiError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleCommentClick = async (commentId: string, allCommentIds?: string[]) => {
    if (!commentId) return;

    try {
      setCommentLoading(true);

      // Always load just the clicked comment initially for fast response
      // When delta months are enabled, selectedMonths already contains all months (primary + delta)
      const allMonths = selectedMonths;
      const comment = await getCommentDetail(commentId, allMonths);
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
          // When delta months are enabled, selectedMonths already contains all months (primary + delta)
          const allMonths = selectedMonths;
          const nextComment = await getCommentDetail(nextCommentId, allMonths);

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

  return (
    <div className="w-full p-4 max-w-full overflow-x-hidden">
      {/* Controls and Header */}
      <div className="mb-4">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Format Compatibility Analyzer</h1>
        <p className="text-gray-600 mb-4">
          Identify incompatible razor and blade format combinations to catch matching errors and
          data quality issues.
        </p>

        {/* Delta Months Info Panel */}
        <DeltaMonthsInfoPanel selectedMonths={selectedMonths} deltaMonths={deltaMonths} />

        {/* Controls Section */}
        <div className="space-y-4 mb-4">
          <div className="flex flex-wrap gap-4 items-end">
            <div className="min-w-0 flex-1 sm:flex-none">
              <label
                htmlFor="month-selector"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Month
              </label>
              <MonthSelector
                selectedMonths={selectedMonths}
                onMonthsChange={handleMonthChange}
                label="Select Month"
                multiple={true}
                enableDeltaMonths={true}
                onDeltaMonthsChange={handleDeltaMonthsChange}
              />
            </div>
            <div className="min-w-0 flex-1 sm:flex-none">
              <label
                htmlFor="severity-filter"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Severity Filter
              </label>
              <select
                id="severity-filter"
                value={severityFilter}
                onChange={e =>
                  setSeverityFilter(e.target.value as 'error' | 'warning' | 'all')
                }
                className="w-full sm:w-auto px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Issues</option>
                <option value="error">Errors Only</option>
                <option value="warning">Warnings Only</option>
              </select>
            </div>
            <div className="min-w-0 flex-1 sm:flex-none">
              <button
                onClick={handleAnalyze}
                disabled={loading || selectedMonths.length === 0}
                className="w-full sm:w-auto bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed h-10"
              >
                {loading ? 'Analyzing...' : 'Analyze'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-4">
          <ErrorDisplay error={error} onRetry={() => setError(null)} />
        </div>
      )}

      {/* Loading Spinner */}
      {loading && (
        <div className="mb-4">
          <LoadingSpinner message="Analyzing format compatibility..." />
        </div>
      )}

      {/* Results Table */}
      {results && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div className="min-w-0 flex-1">
                <h3 className="text-lg font-medium text-gray-900">Analysis Results</h3>
                <div className="mt-2 text-sm text-gray-600 flex flex-wrap gap-4">
                  <span className="whitespace-nowrap">
                    Month{selectedMonths.length > 1 ? 's' : ''}:{' '}
                    <span className="font-medium">
                      {selectedMonths.length > 1 ? 'Multiple' : selectedMonths[0] || ''}
                    </span>
                  </span>
                  <span className="whitespace-nowrap">
                    Total Issues: <span className="font-medium">{results.total_issues}</span>
                  </span>
                  <span className="whitespace-nowrap">
                    Errors: <span className="font-medium text-red-600">{results.errors}</span>
                  </span>
                  <span className="whitespace-nowrap">
                    Warnings:{' '}
                    <span className="font-medium text-yellow-600">{results.warnings}</span>
                  </span>
                  <span className="whitespace-nowrap">
                    Processing Time:{' '}
                    <span className="font-medium">{results.processing_time.toFixed(2)}s</span>
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="p-6">
            {results.results.length > 0 ? (
              <FormatCompatibilityTable
                data={results.results}
                onCommentClick={handleCommentClick}
                commentLoading={commentLoading}
              />
            ) : (
              <div className="text-center py-8">
                <div className="text-green-600 text-4xl mb-2">✅</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Issues Found</h3>
                <p className="text-gray-600">
                  No format compatibility issues found for the selected months and severity filter.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Ready State */}
      {!loading && !results && !error && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-center py-8">
            <div className="text-gray-400 text-6xl mb-4">🔍</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Ready to Analyze</h3>
            <p className="text-gray-600">
              Select a month and severity filter, then click &quot;Analyze&quot; to begin format
              compatibility analysis.
            </p>
          </div>
        </div>
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

export default FormatCompatibilityAnalyzer;

