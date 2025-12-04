import React, { useState, useMemo } from 'react';
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
  removeCatalogValidationEntries,
} from '../services/api';

const CatalogValidator: React.FC = () => {
  const [selectedField, setSelectedField] = useState<string>('blade');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<CatalogValidationResult | null>(null);
  const [displayMode, setDisplayMode] = useState<
    'all' | 'mismatches' | 'no_match' | 'format_mismatches' | 'data_mismatch' | 'structural_change' | 'duplicate_string' | 'cross_section_conflict'
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

  // Helper function to get filtered issues
  const getFilteredIssues = () => {
    if (!results?.issues) return [];

    switch (displayMode) {
      case 'mismatches':
        return results.issues.filter(issue =>
          issue.issue_type === 'catalog_pattern_mismatch' || issue.issue_type === 'data_mismatch'
        );
      case 'no_match':
        return results.issues.filter(issue =>
          issue.issue_type === 'catalog_pattern_no_match' || issue.issue_type === 'no_match'
        );
      case 'format_mismatches':
        return results.issues.filter(issue => issue.issue_type === 'format_mismatch');
      case 'data_mismatch':
        return results.issues.filter(issue => issue.issue_type === 'data_mismatch');
      case 'structural_change':
        return results.issues.filter(issue => issue.issue_type === 'structural_change');
      case 'duplicate_string':
        return results.issues.filter(issue => issue.issue_type === 'duplicate_string');
      case 'cross_section_conflict':
        return results.issues.filter(issue => issue.issue_type === 'cross_section_conflict');
      default:
        return results.issues;
    }
  };

  // Memoized filtered issues
  const filteredIssues = useMemo(() => getFilteredIssues(), [results, displayMode]);
  const areAllSelected = useMemo(
    () => filteredIssues.length > 0 && filteredIssues.every((_, index) => selectedIssues.has(index)),
    [filteredIssues, selectedIssues]
  );

  // New functions for multi-select functionality
  const handleRemoveSelected = async () => {
    if (!results || selectedIssues.size === 0) return;

    try {
      setRemoving(true);
      setError(null);

      // Get the selected issues data
      const selectedIssuesData = Array.from(selectedIssues).map(index => {
        const issue = filteredIssues[index];
        return {
          correct_match: issue.correct_match,
          expected_brand: issue.expected_brand,
          expected_model: issue.expected_model,
          issue_type: issue.issue_type,
        };
      });

      // Call the API to remove entries
      const response = await removeCatalogValidationEntries({
        field: selectedField,
        entries: selectedIssuesData,
      });

      if (response.success) {
        // Clear selection after successful removal
        setSelectedIssues(new Set());

        // Re-validate catalog to refresh results
        await handleValidate();

        // Show success message
        console.log(`Successfully removed ${response.removed_count} entries`);
      } else {
        // Show error message
        setError(`Failed to remove entries: ${response.message}`);
        if (response.errors.length > 0) {
          console.error('Removal errors:', response.errors);
        }
      }
    } catch (err: unknown) {
      setError(handleApiError(err));
      // Keep items selected if removal fails
    } finally {
      setRemoving(false);
    }
  };

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

  const handleSelectAll = () => {
    if (filteredIssues.length === 0) return;

    if (areAllSelected) {
      // Deselect all
      setSelectedIssues(new Set());
    } else {
      // Select all
      const allIndices = new Set(Array.from({ length: filteredIssues.length }, (_, i) => i));
      setSelectedIssues(allIndices);
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
        data_mismatch: 0,
        structural_change: 0,
        duplicate_string: 0,
        cross_section_conflict: 0,
      };
    }

    const issues = results.issues || [];

    return {
      all: issues.length,
      mismatches: issues.filter(issue =>
        issue.issue_type === 'catalog_pattern_mismatch' || issue.issue_type === 'data_mismatch'
      ).length,
      no_match: issues.filter(issue =>
        issue.issue_type === 'catalog_pattern_no_match' || issue.issue_type === 'no_match'
      ).length,
      format_mismatches: issues.filter(issue => issue.issue_type === 'format_mismatch').length,
      data_mismatch: issues.filter(issue => issue.issue_type === 'data_mismatch').length,
      structural_change: issues.filter(issue => issue.issue_type === 'structural_change').length,
      duplicate_string: issues.filter(issue => issue.issue_type === 'duplicate_string').length,
      cross_section_conflict: issues.filter(issue => issue.issue_type === 'cross_section_conflict').length,
    };
  };

  const getIssueIcon = (issue: CatalogValidationIssue) => {
    switch (issue.issue_type) {
      case 'catalog_pattern_mismatch':
      case 'data_mismatch':
        return <AlertTriangle className='h-4 w-4 text-orange-500' />;
      case 'catalog_pattern_no_match':
      case 'no_match':
        return <XCircle className='h-4 w-4 text-red-500' />;
      case 'structural_change':
        return <AlertTriangle className='h-4 w-4 text-purple-500' />;
      case 'duplicate_string':
      case 'cross_section_conflict':
        return <Info className='h-4 w-4 text-yellow-500' />;
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

  // Helper function to get file name from field
  const getFileName = (field: string): string => {
    const fieldToFile: Record<string, string> = {
      razor: 'razor.yaml',
      blade: 'blade.yaml',
      brush: 'brush.yaml',
      soap: 'soap.yaml',
      handle: 'handle.yaml',
      knot: 'knot.yaml',
    };
    return fieldToFile[field] || `${field}.yaml`;
  };

  // Helper function to parse sections from details for duplicate/conflict issues
  const parseSectionsFromDetails = (details: string): string[] => {
    const sections: string[] = [];
    
    // Check for explicit section mentions (case-insensitive, whole word matching)
    const sectionKeywords: Record<string, string> = {
      brush: 'brush',
      handle: 'handle',
      knot: 'knot',
      razor: 'razor',
      blade: 'blade',
      soap: 'soap',
    };
    
    // Use word boundaries to avoid false matches
    for (const [key, value] of Object.entries(sectionKeywords)) {
      const regex = new RegExp(`\\b${key}\\b`, 'i');
      if (regex.test(details) && !sections.includes(value)) {
        sections.push(value);
      }
    }
    
    return sections;
  };

  return (
    <div className='w-full p-4'>
      {/* Controls and Header */}
      <div className='mb-4'>
        <h1 className='text-3xl font-bold text-gray-900 mb-2'>Catalog Validator</h1>
        <p className='text-gray-600 mb-4'>
          Validate that entries in correct_matches directory still map to the same brand/model
          combinations using current catalog regex patterns. This helps identify when catalog
          updates have broken existing correct matches. The validator tests each pattern from
          correct_matches directory against the current matchers to see if they still produce the
          expected brand/model results.
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
                  className={`ml-1 px-1.5 py-0.5 text-xs rounded-full ${displayMode === 'all' ? 'bg-white text-blue-600' : 'bg-gray-100 text-gray-700'
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
                  className={`ml-1 px-1.5 py-0.5 text-xs rounded-full ${displayMode === 'mismatches'
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
                    className={`ml-1 px-1.5 py-0.5 text-xs rounded-full ${displayMode === 'format_mismatches'
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
                  className={`ml-1 px-1.5 py-0.5 text-xs rounded-full ${displayMode === 'no_match'
                    ? 'bg-white text-red-600'
                    : 'bg-gray-100 text-gray-700'
                    }`}
                >
                  {getDisplayModeCounts().no_match}
                </span>
              </Button>
              <Button
                variant='outline'
                onClick={() => setDisplayMode('data_mismatch')}
                className={`flex items-center gap-1 text-sm ${displayMode === 'data_mismatch' ? 'bg-orange-600 text-white' : ''}`}
              >
                Data Mismatch
                <span
                  className={`ml-1 px-1.5 py-0.5 text-xs rounded-full ${displayMode === 'data_mismatch'
                    ? 'bg-white text-orange-600'
                    : 'bg-gray-100 text-gray-700'
                    }`}
                >
                  {getDisplayModeCounts().data_mismatch}
                </span>
              </Button>
              <Button
                variant='outline'
                onClick={() => setDisplayMode('structural_change')}
                className={`flex items-center gap-1 text-sm ${displayMode === 'structural_change' ? 'bg-purple-600 text-white' : ''}`}
              >
                Structural Change
                <span
                  className={`ml-1 px-1.5 py-0.5 text-xs rounded-full ${displayMode === 'structural_change'
                    ? 'bg-white text-purple-600'
                    : 'bg-gray-100 text-gray-700'
                    }`}
                >
                  {getDisplayModeCounts().structural_change}
                </span>
              </Button>
              <Button
                variant='outline'
                onClick={() => setDisplayMode('duplicate_string')}
                className={`flex items-center gap-1 text-sm ${displayMode === 'duplicate_string' ? 'bg-yellow-600 text-white' : ''}`}
              >
                Duplicates
                <span
                  className={`ml-1 px-1.5 py-0.5 text-xs rounded-full ${displayMode === 'duplicate_string'
                    ? 'bg-white text-yellow-600'
                    : 'bg-gray-100 text-gray-700'
                    }`}
                >
                  {getDisplayModeCounts().duplicate_string}
                </span>
              </Button>
              <Button
                variant='outline'
                onClick={() => setDisplayMode('cross_section_conflict')}
                className={`flex items-center gap-1 text-sm ${displayMode === 'cross_section_conflict' ? 'bg-yellow-600 text-white' : ''}`}
              >
                Conflicts
                <span
                  className={`ml-1 px-1.5 py-0.5 text-xs rounded-full ${displayMode === 'cross_section_conflict'
                    ? 'bg-white text-yellow-600'
                    : 'bg-gray-100 text-gray-700'
                    }`}
                >
                  {getDisplayModeCounts().cross_section_conflict}
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
          <LoadingSpinner message='Running actual matching validation...' />
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
                    Displayed: <span className='font-medium'>{filteredIssues.length}</span>
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

              {/* Select All and Remove Selected Buttons */}
              <div className='flex items-center gap-2'>
                {filteredIssues.length > 0 && (
                  <Button
                    variant='outline'
                    onClick={handleSelectAll}
                    className='flex items-center gap-2'
                  >
                    {areAllSelected ? 'Deselect All' : 'Select All'}
                  </Button>
                )}
                {isAnyIssueSelected && (
                  <Button
                    variant='destructive'
                    onClick={handleRemoveSelected}
                    disabled={removing}
                    className='flex items-center gap-2'
                  >
                    {removing ? 'Removing...' : `Remove Selected (${selectedIssues.size})`}
                  </Button>
                )}
              </div>
            </div>
          </div>

          <div className='p-6'>
            {filteredIssues.length > 0 ? (
              <div className='space-y-4'>
                {filteredIssues.map((issue, index) => (
                  <div
                    key={index}
                    className={`border rounded-lg p-4 ${getIssueSeverityColor(issue.severity)} ${selectedIssues.has(index) ? 'ring-2 ring-blue-500 bg-blue-50' : ''
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
                                  : issue.issue_type === 'data_mismatch'
                                    ? 'Data Mismatch'
                                    : issue.issue_type === 'structural_change'
                                      ? 'Structural Change'
                                      : issue.issue_type === 'duplicate_string'
                                        ? 'Duplicate String'
                                        : issue.issue_type === 'cross_section_conflict'
                                          ? 'Cross-Section Conflict'
                                          : issue.issue_type === 'no_match'
                                            ? 'No Match Found'
                                            : 'Validation Issue'}
                          </h4>
                          <span
                            className={`px-2 py-1 text-xs rounded-full ${issue.severity === 'high'
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
                            <strong>Pattern Being Tested:</strong>{' '}
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

                          {issue.issue_type === 'catalog_pattern_mismatch' || issue.issue_type === 'data_mismatch' ? (
                            <div className='grid grid-cols-1 md:grid-cols-2 gap-4 text-sm'>
                              <div>
                                <p className='font-medium text-gray-700'>Currently Stored Under:</p>
                                <p className='text-gray-600'>
                                  {issue.expected_brand} {issue.expected_model}
                                </p>
                                <p className='text-xs text-gray-500 mt-1'>
                                  (in correct_matches directory)
                                </p>
                              </div>
                              <div>
                                <p className='font-medium text-gray-700'>Matcher Suggests:</p>
                                <p className='text-gray-600'>
                                  {issue.actual_brand} {issue.actual_model}
                                </p>
                                <p className='text-xs text-gray-500 mt-1'>
                                  (based on current matching system)
                                </p>
                                {issue.matched_pattern && (
                                  <div className='mt-2 p-2 bg-blue-50 border border-blue-200 rounded-md'>
                                    <p className='text-xs font-medium text-blue-800 mb-1'>
                                      Matched Regex Pattern:
                                    </p>
                                    <code className='text-xs text-blue-700 bg-blue-100 px-1.5 py-0.5 rounded break-all'>
                                      {issue.matched_pattern}
                                    </code>
                                  </div>
                                )}
                              </div>
                            </div>
                          ) : issue.issue_type === 'structural_change' ? (
                            <div className='grid grid-cols-1 md:grid-cols-2 gap-4 text-sm'>
                              <div className='p-3 bg-gray-50 rounded border border-gray-200'>
                                <p className='font-medium text-gray-700 mb-2'>Currently Matched As (Brush):</p>
                                {issue.current_match_details ? (
                                  <div className='space-y-1'>
                                    <p className='text-gray-600'>
                                      <span className='font-medium'>Brand:</span> {issue.current_match_details.brand || 'Unknown'}
                                    </p>
                                    <p className='text-gray-600'>
                                      <span className='font-medium'>Model:</span> {issue.current_match_details.model || 'Unknown'}
                                    </p>
                                    {issue.current_match_details.fiber && (
                                      <p className='text-gray-600'>
                                        <span className='font-medium'>Fiber:</span> {issue.current_match_details.fiber}
                                      </p>
                                    )}
                                    {issue.current_match_details.knot_size_mm && (
                                      <p className='text-gray-600'>
                                        <span className='font-medium'>Knot Size:</span> {issue.current_match_details.knot_size_mm}mm
                                      </p>
                                    )}
                                  </div>
                                ) : (
                                  <p className='text-gray-600'>{issue.expected_brand} {issue.expected_model}</p>
                                )}
                                <p className='text-xs text-gray-500 mt-2'>(in correct_matches.yaml)</p>
                              </div>
                              
                              <div className='p-3 bg-blue-50 rounded border border-blue-200'>
                                <p className='font-medium text-blue-800 mb-2'>Should Match As (Handle + Knot):</p>
                                <div className='space-y-2'>
                                  {issue.expected_handle_match && (
                                    <div className='bg-white p-2 rounded border border-blue-100'>
                                      <p className='text-xs font-semibold text-blue-700 mb-1'>HANDLE:</p>
                                      <p className='text-sm text-gray-700'>
                                        {issue.expected_handle_match.brand} {issue.expected_handle_match.model}
                                      </p>
                                    </div>
                                  )}
                                  {issue.expected_knot_match && (
                                    <div className='bg-white p-2 rounded border border-blue-100'>
                                      <p className='text-xs font-semibold text-blue-700 mb-1'>KNOT:</p>
                                      <p className='text-sm text-gray-700'>
                                        {issue.expected_knot_match.brand} {issue.expected_knot_match.model}
                                      </p>
                                      {issue.expected_knot_match.fiber && (
                                        <p className='text-xs text-gray-600 mt-1'>
                                          Fiber: {issue.expected_knot_match.fiber}
                                        </p>
                                      )}
                                      {issue.expected_knot_match.knot_size_mm && (
                                        <p className='text-xs text-gray-600'>
                                          Size: {issue.expected_knot_match.knot_size_mm}mm
                                        </p>
                                      )}
                                    </div>
                                  )}
                                </div>
                                <p className='text-xs text-blue-600 mt-2'>(based on current matching system)</p>
                              </div>
                            </div>
                          ) : issue.issue_type === 'duplicate_string' || issue.issue_type === 'cross_section_conflict' ? (
                            <div className='space-y-3'>
                              <div>
                                <p className='font-medium text-gray-700'>Issue Type:</p>
                                <p className='text-gray-600'>
                                  {issue.issue_type === 'duplicate_string' ? 'Duplicate string found' : 'Cross-section conflict detected'}
                                </p>
                                <p className='text-xs text-gray-500 mt-1'>
                                  (data structure validation)
                                </p>
                              </div>
                              
                              {/* Show file and section information */}
                              <div className='p-3 bg-blue-50 border border-blue-200 rounded-md'>
                                <p className='text-sm font-medium text-blue-800 mb-2'>Location:</p>
                                <div className='space-y-1'>
                                  {issue.issue_type === 'duplicate_string' ? (
                                    <>
                                      {(() => {
                                        const sections = parseSectionsFromDetails(issue.details);
                                        // Check if details mention "across multiple sections" or specific sections
                                        const isCrossSection = issue.details.includes('across multiple sections') || sections.length > 1;
                                        
                                        if (isCrossSection) {
                                          // Cross-section duplicate - show all detected files
                                          const allSections = sections.length > 0 ? sections : [issue.field];
                                          
                                          return (
                                            <>
                                              <p className='text-sm text-gray-700 mb-2'>
                                                <strong>Files Containing Duplicate:</strong>
                                              </p>
                                              <div className='space-y-1'>
                                                {allSections.map(section => {
                                                  const lineNums = issue.line_numbers?.[section];
                                                  return (
                                                    <p key={section} className='text-sm text-gray-700'>
                                                      • <code className='bg-white px-1.5 py-0.5 rounded text-xs'>
                                                        data/correct_matches/{getFileName(section)}
                                                      </code>
                                                      {lineNums && lineNums.length > 0 && (
                                                        <span className='text-xs text-gray-600 ml-2'>
                                                          (line{lineNums.length > 1 ? 's' : ''}: {lineNums.join(', ')})
                                                        </span>
                                                      )}
                                                    </p>
                                                  );
                                                })}
                                                {sections.length === 0 && (
                                                  <p className='text-xs text-gray-500 italic mt-1'>
                                                    Note: This duplicate appears across multiple field files. Check razor.yaml, brush.yaml, blade.yaml, and soap.yaml files.
                                                  </p>
                                                )}
                                              </div>
                                              <p className='text-xs text-gray-600 mt-2'>
                                                This string appears in multiple files. Remove it from all but one appropriate location.
                                              </p>
                                            </>
                                          );
                                        } else {
                                          // Within same file/section duplicate
                                          return (
                                            <>
                                              <p className='text-sm text-gray-700'>
                                                <strong>File:</strong>{' '}
                                                <code className='bg-white px-1.5 py-0.5 rounded text-xs'>
                                                  data/correct_matches/{getFileName(issue.field)}
                                                </code>
                                                {issue.line_numbers?.[issue.field] && issue.line_numbers[issue.field].length > 0 && (
                                                  <span className='text-xs text-gray-600 ml-2'>
                                                    (line{issue.line_numbers[issue.field].length > 1 ? 's' : ''}: {issue.line_numbers[issue.field].join(', ')})
                                                  </span>
                                                )}
                                              </p>
                                              <p className='text-xs text-gray-600 mt-1'>
                                                This string appears multiple times in this file. Remove duplicate entries.
                                              </p>
                                            </>
                                          );
                                        }
                                      })()}
                                    </>
                                  ) : (
                                    <>
                                      <p className='text-sm text-gray-700 mb-2'>
                                        <strong>Conflicting Files:</strong>
                                      </p>
                                      {(() => {
                                        const sections = parseSectionsFromDetails(issue.details);
                                        if (sections.length > 0) {
                                          return (
                                              <div className='space-y-1'>
                                                {sections.map(section => {
                                                  const lineNums = issue.line_numbers?.[section];
                                                  return (
                                                    <p key={section} className='text-sm text-gray-700'>
                                                      • <code className='bg-white px-1.5 py-0.5 rounded text-xs'>
                                                        data/correct_matches/{getFileName(section)}
                                                      </code>
                                                      {lineNums && lineNums.length > 0 && (
                                                        <span className='text-xs text-gray-600 ml-2'>
                                                          (line{lineNums.length > 1 ? 's' : ''}: {lineNums.join(', ')})
                                                        </span>
                                                      )}
                                                    </p>
                                                  );
                                                })}
                                              </div>
                                          );
                                        } else {
                                          // Fallback: show current field and mention it's a cross-section conflict
                                          return (
                                            <div className='space-y-1'>
                                              <p className='text-sm text-gray-700'>
                                                • <code className='bg-white px-1.5 py-0.5 rounded text-xs'>
                                                  data/correct_matches/{getFileName(issue.field)}
                                                </code>
                                              </p>
                                              <p className='text-xs text-gray-600 mt-1'>
                                                (and other section files - see details)
                                              </p>
                                            </div>
                                          );
                                        }
                                      })()}
                                    </>
                                  )}
                                </div>
                              </div>
                            </div>
                          ) : (
                            <div>
                              <p className='font-medium text-gray-700'>Currently Stored Under:</p>
                              <p className='text-gray-600'>
                                {issue.expected_brand} {issue.expected_model}
                              </p>
                              <p className='text-xs text-gray-500 mt-1'>
                                (in correct_matches directory)
                              </p>
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
                          <p className='text-sm text-gray-600'>
                            {issue.issue_type === 'catalog_pattern_mismatch' || issue.issue_type === 'data_mismatch'
                              ? `Update correct_matches directory to reflect new brand/model: '${issue.actual_brand} ${issue.actual_model}'`
                              : issue.issue_type === 'structural_change'
                                ? `Update correct_matches directory structure: move from '${issue.expected_section}' section to '${issue.actual_section}' section`
                                : issue.issue_type === 'duplicate_string'
                                  ? `Remove duplicate entry for '${issue.correct_match}' from correct_matches directory`
                                  : issue.issue_type === 'cross_section_conflict'
                                    ? `Resolve cross-section conflict for '${issue.correct_match}' in correct_matches directory`
                                    : issue.suggested_action
                            }
                          </p>
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
                  All {results.total_entries} entries in correct_matches directory are still valid with
                  the current matching system.
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
