import React, { useState } from 'react';
import LoadingSpinner from '../components/layout/LoadingSpinner';
import ErrorDisplay from '../components/feedback/ErrorDisplay';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { AlertTriangle, XCircle, Info } from 'lucide-react';
import {
  validateCatalogAgainstCorrectMatches,
  CatalogValidationResult,
  CatalogValidationIssue,
  handleApiError,
} from '../services/api';

const CatalogValidator: React.FC = () => {
  const [selectedField, setSelectedField] = useState<string>('blade');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<CatalogValidationResult | null>(null);
  const [displayMode, setDisplayMode] = useState<
    'all' | 'mismatches' | 'no_match' | 'format_mismatches'
  >('all');

  // New state for multi-select functionality
  const [selectedIssues, setSelectedIssues] = useState<Set<number>>(new Set());
  const [removing, setRemoving] = useState(false);

  const handleValidate = async () => {
    if (!selectedField) {
      setError('Please select a field to validate');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setResults(null);
      // Clear selection when starting new validation
      setSelectedIssues(new Set());

      const result = await validateCatalogAgainstCorrectMatches({
        field: selectedField,
      });

      setResults(result);
    } catch (err: unknown) {
      setError(handleApiError(err));
    } finally {
      setLoading(false);
    }
  };

  // New functions for multi-select functionality
  const handleIssueSelect = (index: number, selected: boolean) => {
    setSelectedIssues(prev => {
      const newSet = new Set(prev);
      if (selected) {
        newSet.add(index);
      } else {
        newSet.delete(index);
      }
      return newSet;
    });
  };

  const handleRemoveSelected = async () => {
    if (!results || selectedIssues.size === 0) return;

    try {
      setRemoving(true);
      setError(null);

      // Get the selected issues data
      const selectedIssuesData = Array.from(selectedIssues).map(index => {
        const issue = getFilteredIssues()[index];
        return {
          correct_match: issue.correct_match,
          expected_brand: issue.expected_brand,
          expected_model: issue.expected_model,
        };
      });

      // TODO: Implement API call to remove entries
      console.log('Removing entries:', selectedIssuesData);

      // For now, just simulate the removal
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Clear selection after successful removal
      setSelectedIssues(new Set());

      // TODO: Re-validate catalog to refresh results
      // await handleValidate();

      // Show success message (temporary)
      console.log(`Successfully removed ${selectedIssuesData.length} entries`);
    } catch (err: unknown) {
      setError(handleApiError(err));
      // Keep items selected if removal fails
    } finally {
      setRemoving(false);
    }
  };

  const isAnyIssueSelected = selectedIssues.size > 0;

  const getDisplayModeCounts = () => {
    if (!results) {
      return {
        all: 0,
        mismatches: 0,
        no_match: 0,
        format_mismatches: 0,
      };
    }

    const issues = results.issues || [];

    return {
      all: issues.length,
      mismatches: issues.filter(issue => issue.issue_type === 'catalog_pattern_mismatch').length,
      no_match: issues.filter(issue => issue.issue_type === 'catalog_pattern_no_match').length,
      format_mismatches: issues.filter(issue => issue.issue_type === 'format_mismatch').length,
    };
  };

  const getFilteredIssues = () => {
    if (!results?.issues) return [];

    switch (displayMode) {
      case 'mismatches':
        return results.issues.filter(issue => issue.issue_type === 'catalog_pattern_mismatch');
      case 'no_match':
        return results.issues.filter(issue => issue.issue_type === 'catalog_pattern_no_match');
      case 'format_mismatches':
        return results.issues.filter(issue => issue.issue_type === 'format_mismatch');
      default:
        return results.issues;
    }
  };

  const getIssueIcon = (issue: CatalogValidationIssue) => {
    switch (issue.issue_type) {
      case 'catalog_pattern_mismatch':
        return <AlertTriangle className='h-4 w-4 text-orange-500' />;
      case 'catalog_pattern_no_match':
        return <XCircle className='h-4 w-4 text-red-500' />;
      default:
        return <Info className='h-4 w-4 text-blue-500' />;
    }
  };

  const getIssueSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'medium':
        return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'low':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const isFormatMismatch = (issue: CatalogValidationIssue) => {
    return issue.issue_type === 'format_mismatch';
  };

  return (
    <div className='w-full p-4'>
      {/* Controls and Header */}
      <div className='mb-4'>
        <h1 className='text-3xl font-bold text-gray-900 mb-2'>Catalog Validator</h1>
        <p className='text-gray-600 mb-4'>
          Validate that entries in correct_matches.yaml still map to the same brand/model
          combinations using current catalog regex patterns. This helps identify when catalog
          updates have broken existing correct matches.
        </p>

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

          <div className='flex flex-col gap-1'>
            <label className='block text-sm font-medium text-gray-700 mb-1'>Display Mode</label>
            <div className='flex gap-2'>
              <Button
                variant='outline'
                onClick={() => setDisplayMode('all')}
                className={`flex items-center gap-1 text-sm ${displayMode === 'all' ? 'bg-blue-600 text-white' : ''}`}
              >
                All Issues
                <span
                  className={`ml-1 px-1.5 py-0.5 text-xs rounded-full ${
                    displayMode === 'all' ? 'bg-white text-blue-600' : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  {getDisplayModeCounts().all}
                </span>
              </Button>
              <Button
                variant='outline'
                onClick={() => setDisplayMode('mismatches')}
                className={`flex items-center gap-1 text-sm ${displayMode === 'mismatches' ? 'bg-orange-600 text-white' : ''}`}
              >
                Mismatches
                <span
                  className={`ml-1 px-1.5 py-0.5 text-xs rounded-full ${
                    displayMode === 'mismatches'
                      ? 'bg-white text-orange-600'
                      : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  {getDisplayModeCounts().mismatches}
                </span>
              </Button>
              {selectedField === 'blade' && (
                <Button
                  variant='outline'
                  onClick={() => setDisplayMode('format_mismatches')}
                  className={`flex items-center gap-1 text-sm ${displayMode === 'format_mismatches' ? 'bg-purple-600 text-white' : ''}`}
                >
                  Format Mismatches
                  <span
                    className={`ml-1 px-1.5 py-0.5 text-xs rounded-full ${
                      displayMode === 'format_mismatches'
                        ? 'bg-white text-purple-600'
                        : 'bg-gray-100 text-gray-700'
                    }`}
                  >
                    {getDisplayModeCounts().format_mismatches}
                  </span>
                </Button>
              )}
              <Button
                variant='outline'
                onClick={() => setDisplayMode('no_match')}
                className={`flex items-center gap-1 text-sm ${displayMode === 'no_match' ? 'bg-red-600 text-white' : ''}`}
              >
                No Match
                <span
                  className={`ml-1 px-1.5 py-0.5 text-xs rounded-full ${
                    displayMode === 'no_match'
                      ? 'bg-white text-red-600'
                      : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  {getDisplayModeCounts().no_match}
                </span>
              </Button>
            </div>
          </div>

          <button
            onClick={handleValidate}
            disabled={loading || !selectedField}
            className='bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed h-10 mt-6'
          >
            {loading ? 'Validating...' : 'Validate Catalog'}
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
          <LoadingSpinner message='Validating catalog patterns...' />
        </div>
      )}

      {/* Results */}
      {results && (
        <div className='bg-white rounded-lg shadow'>
          <div className='px-6 py-4 border-b border-gray-200'>
            <div className='flex items-center justify-between'>
              <div>
                <h3 className='text-lg font-medium text-gray-900'>Validation Results</h3>
                <div className='mt-2 text-sm text-gray-600 flex flex-wrap gap-6'>
                  <span>
                    Field: <span className='font-medium'>{results.field}</span>
                  </span>
                  <span>
                    Total Entries: <span className='font-medium'>{results.total_entries}</span>
                  </span>
                  <span>
                    Issues Found: <span className='font-medium'>{results.issues.length}</span>
                  </span>
                  <span>
                    Displayed: <span className='font-medium'>{getFilteredIssues().length}</span>
                  </span>
                  <span>
                    Processing Time:{' '}
                    <span className='font-medium'>{results.processing_time.toFixed(2)}s</span>
                  </span>
                  {isAnyIssueSelected && (
                    <span className='text-blue-600 font-medium'>
                      Selected: {selectedIssues.size}
                    </span>
                  )}
                </div>
              </div>

              {/* Remove Selected Button */}
              {isAnyIssueSelected && (
                <div className='flex items-center gap-2'>
                  <Button
                    variant='destructive'
                    onClick={handleRemoveSelected}
                    disabled={removing}
                    className='flex items-center gap-2'
                  >
                    {removing ? 'Removing...' : `Remove Selected (${selectedIssues.size})`}
                  </Button>
                </div>
              )}
            </div>
          </div>

          <div className='p-6'>
            {getFilteredIssues().length > 0 ? (
              <div className='space-y-4'>
                {getFilteredIssues().map((issue, index) => (
                  <div
                    key={index}
                    className={`border rounded-lg p-4 ${getIssueSeverityColor(issue.severity)} ${
                      selectedIssues.has(index) ? 'ring-2 ring-blue-500 bg-blue-50' : ''
                    }`}
                  >
                    <div className='flex items-start gap-3'>
                      {/* Checkbox for selection */}
                      <Checkbox
                        checked={selectedIssues.has(index)}
                        onCheckedChange={checked => handleIssueSelect(index, checked as boolean)}
                        className='mt-1'
                      />

                      {getIssueIcon(issue)}
                      <div className='flex-1'>
                        <div className='flex items-center gap-2 mb-2'>
                          <h4 className='font-medium text-gray-900'>
                            {issue.issue_type === 'format_mismatch'
                              ? 'Format Mismatch'
                              : issue.issue_type === 'catalog_pattern_mismatch'
                                ? 'Pattern Mismatch'
                                : issue.issue_type === 'catalog_pattern_no_match'
                                  ? 'No Match Found'
                                  : 'Validation Issue'}
                          </h4>
                          <span
                            className={`px-2 py-1 text-xs rounded-full ${
                              issue.severity === 'high'
                                ? 'bg-red-100 text-red-800'
                                : issue.severity === 'medium'
                                  ? 'bg-orange-100 text-orange-800'
                                  : 'bg-yellow-100 text-yellow-800'
                            }`}
                          >
                            {issue.severity}
                          </span>
                          {isFormatMismatch(issue) && (
                            <span className='px-2 py-1 text-xs rounded-full bg-purple-100 text-purple-800'>
                              Format Issue
                            </span>
                          )}
                        </div>

                        <div className='mb-3'>
                          <p className='text-sm text-gray-700 mb-2'>
                            <strong>Correct Match:</strong>{' '}
                            <code className='bg-gray-100 px-1 rounded'>{issue.correct_match}</code>
                          </p>

                          {/* Show format information prominently for blade format mismatches */}
                          {selectedField === 'blade' && isFormatMismatch(issue) && (
                            <div className='mb-3 p-3 bg-blue-50 border border-blue-200 rounded-md'>
                              <p className='text-sm font-medium text-blue-800 mb-1'>
                                Format Mismatch Detected:
                              </p>
                              <p className='text-sm text-blue-700'>
                                <strong>Expected Format:</strong> {issue.format || 'Unknown'}
                                <br />
                                <strong>Catalog Format:</strong> {issue.catalog_format || 'Unknown'}
                              </p>
                            </div>
                          )}

                          {issue.issue_type === 'catalog_pattern_mismatch' ? (
                            <div className='grid grid-cols-1 md:grid-cols-2 gap-4 text-sm'>
                              <div>
                                <p className='font-medium text-gray-700'>Currently Placed:</p>
                                <p className='text-gray-600'>
                                  {issue.expected_brand} {issue.expected_model}
                                </p>
                              </div>
                              <div>
                                <p className='font-medium text-gray-700'>Should Be:</p>
                                <p className='text-gray-600'>
                                  {issue.actual_brand} {issue.actual_model}
                                </p>
                              </div>
                            </div>
                          ) : (
                            <div>
                              <p className='font-medium text-gray-700'>Expected Mapping:</p>
                              <p className='text-gray-600'>
                                {issue.expected_brand} {issue.expected_model}
                              </p>
                            </div>
                          )}

                          {/* Show matched pattern for mismatched results */}
                          {issue.matched_pattern && (
                            <div className='mb-3 p-3 bg-yellow-50 border border-yellow-200 rounded-md'>
                              <p className='text-sm font-medium text-yellow-800 mb-1'>
                                Matched Pattern:
                              </p>
                              <code className='text-sm text-yellow-700 bg-yellow-100 px-2 py-1 rounded'>
                                {issue.matched_pattern}
                              </code>
                            </div>
                          )}
                        </div>

                        {/* Show conflicting pattern information */}
                        {issue.issue_type === 'catalog_pattern_mismatch' &&
                          issue.details.includes('Conflicting pattern:') && (
                            <div className='mb-3 p-3 bg-red-50 border border-red-200 rounded-md'>
                              <p className='text-sm font-medium text-red-800 mb-1'>
                                Conflicting Pattern:
                              </p>
                              <code className='text-sm text-red-700 bg-red-100 px-2 py-1 rounded'>
                                {issue.details
                                  .split('Conflicting pattern:')[1]
                                  ?.trim()
                                  .replace(/['"]/g, '') || 'Unknown pattern'}
                              </code>
                            </div>
                          )}

                        <div className='mb-3'>
                          <p className='text-sm font-medium text-gray-700 mb-1'>
                            Suggested Action:
                          </p>
                          <p className='text-sm text-gray-600'>{issue.suggested_action}</p>
                        </div>

                        <div>
                          <p className='text-sm font-medium text-gray-700 mb-1'>Details:</p>
                          <p className='text-sm text-gray-600'>{issue.details}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className='text-center py-8'>
                <div className='text-green-600 text-4xl mb-2'>✅</div>
                <h3 className='text-lg font-medium text-gray-900 mb-2'>No Issues Found</h3>
                <p className='text-gray-600'>
                  All {results.total_entries} entries in correct_matches.yaml are still valid with
                  current catalog patterns.
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
            <h3 className='text-lg font-medium text-gray-900 mb-2'>Ready to Validate</h3>
            <p className='text-gray-600'>
              Select a field and click &quot;Validate Catalog&quot; to check for catalog pattern
              conflicts.
              {selectedField === 'blade' && ' For blades, this will also detect format mismatches.'}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default CatalogValidator;
