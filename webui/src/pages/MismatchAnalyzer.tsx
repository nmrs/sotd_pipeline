import React, { useState, useEffect } from 'react';
import MonthSelector from '../components/forms/MonthSelector';
import LoadingSpinner from '../components/layout/LoadingSpinner';
import ErrorDisplay from '../components/feedback/ErrorDisplay';
import MismatchAnalyzerDataTable from '../components/data/MismatchAnalyzerDataTable';
import CommentModal from '../components/domain/CommentModal';
import {
  analyzeMismatch,
  MismatchAnalysisResult,
  handleApiError,
  getCommentDetail,
  CommentDetail,
  getCorrectMatches,
  markMatchesAsCorrect,
  clearCorrectMatchesByField,
  clearAllCorrectMatches,
  CorrectMatchesResponse,
} from '../services/api';

const MismatchAnalyzer: React.FC = () => {
  const [selectedField, setSelectedField] = useState<string>('razor');
  const [selectedMonth, setSelectedMonth] = useState<string>('');
  const [threshold, setThreshold] = useState<number>(3);
  const [limit, setLimit] = useState<number>(50);
  const [showAll, setShowAll] = useState<boolean>(false);
  const [showUnconfirmed, setShowUnconfirmed] = useState<boolean>(false);
  const [showRegexMatches, setShowRegexMatches] = useState<boolean>(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<MismatchAnalysisResult | null>(null);
  const [selectedComment, setSelectedComment] = useState<CommentDetail | null>(null);
  const [commentModalOpen, setCommentModalOpen] = useState(false);
  const [commentLoading, setCommentLoading] = useState(false);

  // Correct matches state
  const [correctMatches, setCorrectMatches] = useState<CorrectMatchesResponse | null>(null);
  const [loadingCorrectMatches, setLoadingCorrectMatches] = useState(false);
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  const [markingCorrect, setMarkingCorrect] = useState(false);

  // Load correct matches when field changes
  useEffect(() => {
    if (selectedField) {
      loadCorrectMatches();
    }
  }, [selectedField]);

  const loadCorrectMatches = async () => {
    try {
      setLoadingCorrectMatches(true);
      const data = await getCorrectMatches(selectedField);
      setCorrectMatches(data);
    } catch (err: unknown) {
      console.warn('Failed to load correct matches:', err);
      // Don't show error to user, just log it
    } finally {
      setLoadingCorrectMatches(false);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedMonth) {
      setError('Please select a month to analyze');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setResults(null);
      setSelectedItems(new Set()); // Clear selections

      const result = await analyzeMismatch({
        field: selectedField,
        month: selectedMonth,
        threshold,
        limit,
        show_all: showAll,
        show_unconfirmed: showUnconfirmed,
        show_regex_matches: showRegexMatches,
      });

      setResults(result);
    } catch (err: unknown) {
      setError(handleApiError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleCommentClick = async (commentId: string) => {
    if (!commentId) return;

    try {
      setCommentLoading(true);
      const comment = await getCommentDetail(commentId, [selectedMonth]);
      setSelectedComment(comment);
      setCommentModalOpen(true);
    } catch (err: unknown) {
      setError(handleApiError(err));
    } finally {
      setCommentLoading(false);
    }
  };

  const handleMonthChange = (months: string[]) => {
    setSelectedMonth(months[0] || '');
  };

  const handleItemSelection = (itemKey: string, selected: boolean) => {
    const newSelected = new Set(selectedItems);
    if (selected) {
      newSelected.add(itemKey);
    } else {
      newSelected.delete(itemKey);
    }
    setSelectedItems(newSelected);
  };

  const handleSelectAll = () => {
    if (!results?.mismatch_items) return;

    const allKeys = results.mismatch_items.map(item =>
      `${item.original}|${JSON.stringify(item.matched)}`
    );
    setSelectedItems(new Set(allKeys));
  };

  const handleClearSelection = () => {
    setSelectedItems(new Set());
  };

  const handleMarkAsCorrect = async () => {
    if (selectedItems.size === 0) {
      setError('Please select items to mark as correct');
      return;
    }

    if (!results?.mismatch_items) return;

    try {
      setMarkingCorrect(true);

      // Convert selected items to match format
      const matches = results.mismatch_items
        .filter(item => {
          const itemKey = `${item.original}|${JSON.stringify(item.matched)}`;
          return selectedItems.has(itemKey);
        })
        .map(item => ({
          original: item.original,
          matched: item.matched,
        }));

      const response = await markMatchesAsCorrect({
        field: selectedField,
        matches,
        force: true,
      });

      if (response.success) {
        // Reload correct matches and clear selection
        await loadCorrectMatches();
        setSelectedItems(new Set());
        setError(null);

        // Show success message
        alert(`Successfully marked ${response.marked_count} items as correct`);
      } else {
        setError(`Failed to mark items as correct: ${response.message}`);
      }
    } catch (err: unknown) {
      setError(handleApiError(err));
    } finally {
      setMarkingCorrect(false);
    }
  };

  const handleClearCorrectMatches = async () => {
    if (!confirm(`Are you sure you want to clear all correct matches for ${selectedField}?`)) {
      return;
    }

    try {
      await clearCorrectMatchesByField(selectedField);
      await loadCorrectMatches();
      setError(null);
      alert('Correct matches cleared successfully');
    } catch (err: unknown) {
      setError(handleApiError(err));
    }
  };

  const isItemConfirmed = (item: any) => {
    if (!correctMatches?.entries) return false;

    // Check if this item is in the correct matches
    const normalizedOriginal = item.original.toLowerCase().trim();

    // Search through correct matches structure
    for (const [brand, brandData] of Object.entries(correctMatches.entries)) {
      if (typeof brandData === 'object' && brandData !== null) {
        for (const [model, strings] of Object.entries(brandData)) {
          if (Array.isArray(strings)) {
            for (const correctString of strings) {
              if (correctString.toLowerCase().trim() === normalizedOriginal) {
                return true;
              }
            }
          }
        }
      }
    }

    return false;
  };

  return (
    <div className='container mx-auto p-4'>
      {/* Controls and Header */}
      <div className='mb-4'>
        <h1 className='text-3xl font-bold text-gray-900 mb-2'>Mismatch Analyzer</h1>
        <p className='text-gray-600 mb-4'>
          Analyze mismatched items to identify potential catalog conflicts and inconsistencies.
        </p>

        {/* Correct Matches Summary */}
        {correctMatches && (
          <div className='bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4'>
            <div className='flex items-center justify-between'>
              <div>
                <h3 className='text-lg font-medium text-blue-900'>Correct Matches</h3>
                <p className='text-blue-700'>
                  {correctMatches.total_entries} confirmed matches for {selectedField}
                </p>
              </div>
              <button
                onClick={handleClearCorrectMatches}
                className='px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500'
              >
                Clear All
              </button>
            </div>
          </div>
        )}

        <div className='flex flex-wrap gap-4 items-end mb-4'>
          <div>
            <label className='block text-sm font-medium text-gray-700 mb-1'>Field</label>
            <select
              value={selectedField}
              onChange={e => setSelectedField(e.target.value)}
              className='px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            >
              <option value='razor'>Razor</option>
              <option value='blade'>Blade</option>
              <option value='brush'>Brush</option>
              <option value='soap'>Soap</option>
            </select>
          </div>
          <div>
            <label className='block text-sm font-medium text-gray-700 mb-1'>Month</label>
            <MonthSelector
              selectedMonths={selectedMonth ? [selectedMonth] : []}
              onMonthsChange={handleMonthChange}
              label='Select Month'
              multiple={false}
            />
          </div>
          <div>
            <label className='block text-sm font-medium text-gray-700 mb-1'>
              Levenshtein Threshold
            </label>
            <input
              type='number'
              min='1'
              max='10'
              value={threshold}
              onChange={e => setThreshold(Number(e.target.value))}
              className='px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 w-24'
            />
          </div>
          <div>
            <label className='block text-sm font-medium text-gray-700 mb-1'>Result Limit</label>
            <input
              type='number'
              min='1'
              max='1000'
              value={limit}
              onChange={e => setLimit(Number(e.target.value))}
              className='px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 w-28'
            />
          </div>
          <div className='flex flex-col gap-1'>
            <label className='block text-sm font-medium text-gray-700 mb-1'>Options</label>
            <div className='flex gap-2'>
              <label className='flex items-center gap-1 text-sm'>
                <input
                  type='checkbox'
                  checked={showAll}
                  onChange={e => setShowAll(e.target.checked)}
                  className='rounded border-gray-300 text-blue-600 focus:ring-blue-500'
                />
                Show all
              </label>
              <label className='flex items-center gap-1 text-sm'>
                <input
                  type='checkbox'
                  checked={showUnconfirmed}
                  onChange={e => setShowUnconfirmed(e.target.checked)}
                  className='rounded border-gray-300 text-blue-600 focus:ring-blue-500'
                />
                Unconfirmed
              </label>
              <label className='flex items-center gap-1 text-sm'>
                <input
                  type='checkbox'
                  checked={showRegexMatches}
                  onChange={e => setShowRegexMatches(e.target.checked)}
                  className='rounded border-gray-300 text-blue-600 focus:ring-blue-500'
                />
                Regex
              </label>
            </div>
          </div>
          <button
            onClick={handleAnalyze}
            disabled={loading || !selectedMonth}
            className='bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed h-10 mt-6'
          >
            {loading ? 'Analyzing...' : 'Analyze'}
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className='mb-4'>
          <ErrorDisplay error={error} onRetry={() => setError(null)} />
        </div>
      )}

      {/* Loading Spinner */}
      {loading && (
        <div className='mb-4'>
          <LoadingSpinner message='Analyzing mismatches...' />
        </div>
      )}

      {/* Results Table */}
      {results && (
        <div className='bg-white rounded-lg shadow'>
          <div className='px-6 py-4 border-b border-gray-200'>
            <div className='flex items-center justify-between'>
              <div>
                <h3 className='text-lg font-medium text-gray-900'>Analysis Results</h3>
                <div className='mt-2 text-sm text-gray-600 flex flex-wrap gap-6'>
                  <span>
                    Field: <span className='font-medium'>{results.field}</span>
                  </span>
                  <span>
                    Month: <span className='font-medium'>{results.month}</span>
                  </span>
                  <span>
                    Total Matches: <span className='font-medium'>{results.total_matches}</span>
                  </span>
                  <span>
                    Total Mismatches: <span className='font-medium'>{results.total_mismatches}</span>
                  </span>
                  <span>
                    Processing Time:{' '}
                    <span className='font-medium'>{results.processing_time.toFixed(2)}s</span>
                  </span>
                </div>
              </div>

              {/* Bulk Actions */}
              {results.mismatch_items.length > 0 && (
                <div className='flex gap-2'>
                  <button
                    onClick={handleSelectAll}
                    className='px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500'
                  >
                    Select All
                  </button>
                  <button
                    onClick={handleClearSelection}
                    className='px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500'
                  >
                    Clear Selection
                  </button>
                  <button
                    onClick={handleMarkAsCorrect}
                    disabled={selectedItems.size === 0 || markingCorrect}
                    className='px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed'
                  >
                    {markingCorrect ? 'Marking...' : `Mark ${selectedItems.size} as Correct`}
                  </button>
                </div>
              )}
            </div>
          </div>
          <div className='p-6'>
            {results.mismatch_items.length > 0 ? (
              <MismatchAnalyzerDataTable
                data={results.mismatch_items}
                onCommentClick={handleCommentClick}
                commentLoading={commentLoading}
                selectedItems={selectedItems}
                onItemSelection={handleItemSelection}
                isItemConfirmed={isItemConfirmed}
              />
            ) : (
              <div className='text-center py-8'>
                <div className='text-green-600 text-4xl mb-2'>✅</div>
                <h3 className='text-lg font-medium text-gray-900 mb-2'>No Mismatches Found</h3>
                <p className='text-gray-600'>
                  No mismatches were detected for the selected criteria.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Ready State */}
      {!loading && !results && !error && (
        <div className='bg-white rounded-lg shadow p-6'>
          <div className='text-center py-8'>
            <div className='text-gray-400 text-6xl mb-4'>🔍</div>
            <h3 className='text-lg font-medium text-gray-900 mb-2'>Ready to Analyze</h3>
            <p className='text-gray-600'>
              Select a month and field, then click &quot;Analyze&quot; to begin.
            </p>
          </div>
        </div>
      )}

      {/* Comment Modal */}
      {selectedComment && (
        <CommentModal
          comment={selectedComment}
          isOpen={commentModalOpen}
          onClose={() => {
            setCommentModalOpen(false);
            setSelectedComment(null);
          }}
        />
      )}
    </div>
  );
};

export default MismatchAnalyzer;
