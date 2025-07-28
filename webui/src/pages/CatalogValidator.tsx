import React, { useState, useEffect } from 'react';
import LoadingSpinner from '../components/layout/LoadingSpinner';
import ErrorDisplay from '../components/feedback/ErrorDisplay';
import { Button } from '@/components/ui/button';
import { AlertTriangle, CheckCircle, XCircle, Info } from 'lucide-react';
import {
    validateCatalogAgainstCorrectMatches,
    CatalogValidationResult,
    handleApiError,
} from '../services/api';

interface CatalogValidationIssue {
    issue_type: 'catalog_pattern_mismatch' | 'catalog_pattern_no_match';
    field: string;
    correct_match: string;
    expected_brand: string;
    expected_model: string;
    actual_brand: string;
    actual_model: string;
    severity: string;
    suggested_action: string;
    details: string;
}

interface CatalogValidationResponse {
    field: string;
    total_entries: number;
    issues: CatalogValidationIssue[];
    processing_time: number;
}

const CatalogValidator: React.FC = () => {
    const [selectedField, setSelectedField] = useState<string>('blade');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [results, setResults] = useState<CatalogValidationResponse | null>(null);
    const [displayMode, setDisplayMode] = useState<'all' | 'mismatches' | 'no_match'>('all');

    const handleValidate = async () => {
        if (!selectedField) {
            setError('Please select a field to validate');
            return;
        }

        try {
            setLoading(true);
            setError(null);
            setResults(null);

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

    const getDisplayModeCounts = () => {
        if (!results) {
            return {
                all: 0,
                mismatches: 0,
                no_match: 0,
            };
        }

        const issues = results.issues || [];

        return {
            all: issues.length,
            mismatches: issues.filter(issue => issue.issue_type === 'catalog_pattern_mismatch').length,
            no_match: issues.filter(issue => issue.issue_type === 'catalog_pattern_no_match').length,
        };
    };

    const getFilteredIssues = () => {
        if (!results?.issues) return [];

        switch (displayMode) {
            case 'mismatches':
                return results.issues.filter(issue => issue.issue_type === 'catalog_pattern_mismatch');
            case 'no_match':
                return results.issues.filter(issue => issue.issue_type === 'catalog_pattern_no_match');
            default:
                return results.issues;
        }
    };

    const getIssueIcon = (issue: CatalogValidationIssue) => {
        switch (issue.issue_type) {
            case 'catalog_pattern_mismatch':
                return <AlertTriangle className="h-4 w-4 text-orange-500" />;
            case 'catalog_pattern_no_match':
                return <XCircle className="h-4 w-4 text-red-500" />;
            default:
                return <Info className="h-4 w-4 text-blue-500" />;
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

    return (
        <div className="w-full p-4">
            {/* Controls and Header */}
            <div className="mb-4">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">Catalog Validator</h1>
                <p className="text-gray-600 mb-4">
                    Validate that entries in correct_matches.yaml still map to the same brand/model combinations
                    using current catalog regex patterns. This helps identify when catalog updates have broken
                    existing correct matches.
                </p>

                <div className="flex flex-wrap gap-4 items-end mb-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Field</label>
                        <select
                            value={selectedField}
                            onChange={e => setSelectedField(e.target.value)}
                            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="razor">Razor</option>
                            <option value="blade">Blade</option>
                            <option value="brush">Brush</option>
                            <option value="soap">Soap</option>
                        </select>
                    </div>

                    <div className="flex flex-col gap-1">
                        <label className="block text-sm font-medium text-gray-700 mb-1">Display Mode</label>
                        <div className="flex gap-2">
                            <Button
                                variant="outline"
                                onClick={() => setDisplayMode('all')}
                                className={`flex items-center gap-1 text-sm ${displayMode === 'all' ? 'bg-blue-600 text-white' : ''}`}
                            >
                                All Issues
                                <span className={`ml-1 px-1.5 py-0.5 text-xs rounded-full ${displayMode === 'all' ? 'bg-white text-blue-600' : 'bg-gray-100 text-gray-700'
                                    }`}>
                                    {getDisplayModeCounts().all}
                                </span>
                            </Button>
                            <Button
                                variant="outline"
                                onClick={() => setDisplayMode('mismatches')}
                                className={`flex items-center gap-1 text-sm ${displayMode === 'mismatches' ? 'bg-orange-600 text-white' : ''}`}
                            >
                                Mismatches
                                <span className={`ml-1 px-1.5 py-0.5 text-xs rounded-full ${displayMode === 'mismatches' ? 'bg-white text-orange-600' : 'bg-gray-100 text-gray-700'
                                    }`}>
                                    {getDisplayModeCounts().mismatches}
                                </span>
                            </Button>
                            <Button
                                variant="outline"
                                onClick={() => setDisplayMode('no_match')}
                                className={`flex items-center gap-1 text-sm ${displayMode === 'no_match' ? 'bg-red-600 text-white' : ''}`}
                            >
                                No Match
                                <span className={`ml-1 px-1.5 py-0.5 text-xs rounded-full ${displayMode === 'no_match' ? 'bg-white text-red-600' : 'bg-gray-100 text-gray-700'
                                    }`}>
                                    {getDisplayModeCounts().no_match}
                                </span>
                            </Button>
                        </div>
                    </div>

                    <button
                        onClick={handleValidate}
                        disabled={loading || !selectedField}
                        className="bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed h-10 mt-6"
                    >
                        {loading ? 'Validating...' : 'Validate Catalog'}
                    </button>
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
                    <LoadingSpinner message="Validating catalog patterns..." />
                </div>
            )}

            {/* Results */}
            {results && (
                <div className="bg-white rounded-lg shadow">
                    <div className="px-6 py-4 border-b border-gray-200">
                        <div className="flex items-center justify-between">
                            <div>
                                <h3 className="text-lg font-medium text-gray-900">Validation Results</h3>
                                <div className="mt-2 text-sm text-gray-600 flex flex-wrap gap-6">
                                    <span>
                                        Field: <span className="font-medium">{results.field}</span>
                                    </span>
                                    <span>
                                        Total Entries: <span className="font-medium">{results.total_entries}</span>
                                    </span>
                                    <span>
                                        Issues Found: <span className="font-medium">{results.issues.length}</span>
                                    </span>
                                    <span>
                                        Displayed: <span className="font-medium">{getFilteredIssues().length}</span>
                                    </span>
                                    <span>
                                        Processing Time: <span className="font-medium">{results.processing_time.toFixed(2)}s</span>
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="p-6">
                        {getFilteredIssues().length > 0 ? (
                            <div className="space-y-4">
                                {getFilteredIssues().map((issue, index) => (
                                    <div
                                        key={index}
                                        className={`border rounded-lg p-4 ${getIssueSeverityColor(issue.severity)}`}
                                    >
                                        <div className="flex items-start gap-3">
                                            {getIssueIcon(issue)}
                                            <div className="flex-1">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <h4 className="font-medium text-gray-900">
                                                        {issue.issue_type === 'catalog_pattern_mismatch' ? 'Pattern Mismatch' : 'No Match Found'}
                                                    </h4>
                                                    <span className={`px-2 py-1 text-xs rounded-full ${issue.severity === 'high' ? 'bg-red-100 text-red-800' :
                                                        issue.severity === 'medium' ? 'bg-orange-100 text-orange-800' :
                                                            'bg-yellow-100 text-yellow-800'
                                                        }`}>
                                                        {issue.severity}
                                                    </span>
                                                </div>

                                                <div className="mb-3">
                                                    <p className="text-sm text-gray-700 mb-2">
                                                        <strong>Correct Match:</strong> <code className="bg-gray-100 px-1 rounded">{issue.correct_match}</code>
                                                    </p>

                                                    {issue.issue_type === 'catalog_pattern_mismatch' ? (
                                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                                                            <div>
                                                                <p className="font-medium text-gray-700">Expected Mapping:</p>
                                                                <p className="text-gray-600">{issue.expected_brand} {issue.expected_model}</p>
                                                            </div>
                                                            <div>
                                                                <p className="font-medium text-gray-700">Actual Mapping:</p>
                                                                <p className="text-gray-600">{issue.actual_brand} {issue.actual_model}</p>
                                                            </div>
                                                        </div>
                                                    ) : (
                                                        <div>
                                                            <p className="font-medium text-gray-700">Expected Mapping:</p>
                                                            <p className="text-gray-600">{issue.expected_brand} {issue.expected_model}</p>
                                                        </div>
                                                    )}
                                                </div>

                                                {/* Show conflicting pattern information */}
                                                {issue.issue_type === 'catalog_pattern_mismatch' && issue.details.includes('Conflicting pattern:') && (
                                                    <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-md">
                                                        <p className="text-sm font-medium text-red-800 mb-1">Conflicting Pattern:</p>
                                                        <code className="text-sm text-red-700 bg-red-100 px-2 py-1 rounded">
                                                            {issue.details.split('Conflicting pattern:')[1]?.trim().replace(/['"]/g, '') || 'Unknown pattern'}
                                                        </code>
                                                    </div>
                                                )}

                                                <div className="mb-3">
                                                    <p className="text-sm font-medium text-gray-700 mb-1">Suggested Action:</p>
                                                    <p className="text-sm text-gray-600">{issue.suggested_action}</p>
                                                </div>

                                                <div>
                                                    <p className="text-sm font-medium text-gray-700 mb-1">Details:</p>
                                                    <p className="text-sm text-gray-600">{issue.details}</p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-8">
                                <div className="text-green-600 text-4xl mb-2">✅</div>
                                <h3 className="text-lg font-medium text-gray-900 mb-2">No Issues Found</h3>
                                <p className="text-gray-600">
                                    All {results.total_entries} entries in correct_matches.yaml are still valid with current catalog patterns.
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
                        <h3 className="text-lg font-medium text-gray-900 mb-2">Ready to Validate</h3>
                        <p className="text-gray-600">
                            Select a field and click "Validate Catalog" to check for catalog pattern conflicts.
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
};

export default CatalogValidator; 