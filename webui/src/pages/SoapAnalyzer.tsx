import React, { useState, useMemo, useCallback } from 'react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Badge } from '../components/ui/badge';

import MonthSelector from '../components/forms/MonthSelector';
import CommentModal from '../components/domain/CommentModal';
import DeltaMonthsInfoPanel from '../components/domain/DeltaMonthsInfoPanel';
import { CommentDisplay } from '../components/domain/CommentDisplay';
import { getCommentDetail, CommentDetail } from '../services/api';
import { calculateDeltaMonths, formatDeltaMonths } from '../utils/deltaMonths';
import { getWsdbSlug, PipelineSoap } from '../utils/wsdbLookup';

interface SoapDuplicateResult {
  text1: string;
  text2: string;
  similarity: number;
  count: number;
  maker1: string;
  scent1: string;
  maker2: string;
  scent2: string;
}

interface SoapPatternSuggestion {
  pattern: string;
  count: number;
  examples: string[];
}

interface WSDBSoap {
  brand: string;
  name: string;
  slug: string;
  scent_notes?: string[];
  collaborators?: string[];
  tags?: string[];
  category?: string;
}

interface SoapNeighborSimilarityResult {
  entry: string;
  similarity_to_next: number | null;
  similarity_to_above: number | null;
  normalized_string: string;
  pattern: string;
  comment_ids: string[];
  count: number;
  match_types?: string[];
  matched?: {
    maker: string;
    scent: string;
    brand?: string;
  };
}

interface NeighborSimilarityApiResponse {
  message: string;
  mode: string;
  results: SoapNeighborSimilarityResult[];
  total_entries: number;
  months_processed: string[];
}

interface NonMatches {
  brand_non_matches: BrandNonMatch[];
  scent_non_matches: ScentNonMatch[];
}

interface BrandNonMatch {
  pipeline_brand: string;
  wsdb_brand: string;
  added_at: string;
}

interface ScentNonMatch {
  pipeline_brand: string;
  pipeline_scent: string;
  wsdb_brand: string;
  wsdb_scent: string;
  added_at: string;
}

interface ApiResponse {
  message: string;
  results: SoapDuplicateResult[] | SoapPatternSuggestion[];
  total_matches: number;
  months_processed: string[];
}

const SoapAnalyzer: React.FC = () => {
  const [selectedMonths, setSelectedMonths] = useState<string[]>([]);
  const [deltaMonths, setDeltaMonths] = useState<string[]>([]);
  const [similarityThreshold, setSimilarityThreshold] = useState(0.8);
  const [limit, setLimit] = useState(10);
  const [duplicatesResult, setDuplicatesResult] = useState<ApiResponse | null>(null);
  const [patternsResult, setPatternsResult] = useState<ApiResponse | null>(null);
  const [neighborSimilarityResult, setNeighborSimilarityResult] =
    useState<NeighborSimilarityApiResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('duplicates');
  const [wsdbSoaps, setWsdbSoaps] = useState<WSDBSoap[]>([]);
  const [pipelineSoaps, setPipelineSoaps] = useState<PipelineSoap[]>([]);

  // Comment modal state
  const [selectedComment, setSelectedComment] = useState<CommentDetail | null>(null);
  const [commentModalOpen, setCommentModalOpen] = useState(false);
  const [commentLoading, setCommentLoading] = useState(false);

  // Filter state
  const [filterText, setFilterText] = useState<string>('');

  // Non-matches state (for consistency with WSDBAlignmentAnalyzer)
  const [nonMatches, setNonMatches] = useState<NonMatches>({
    brand_non_matches: [],
    scent_non_matches: [],
  });

  // Load WSDB data, pipeline soaps, and non-matches on mount
  React.useEffect(() => {
    const loadWSDBData = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/wsdb-alignment/load-wsdb');
        if (response.ok) {
          const data = await response.json();
          setWsdbSoaps(data.soaps || []);
        }
      } catch (err) {
        console.error('Failed to load WSDB data:', err);
        // Don't show error to user, just fail silently - links will simply not work
      }
    };

    const loadPipelineSoaps = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/wsdb-alignment/load-pipeline');
        if (response.ok) {
          const data = await response.json();
          setPipelineSoaps(data.soaps || []);
        }
      } catch (err) {
        console.error('Failed to load pipeline soaps:', err);
        // Don't show error to user, just fail silently - alias lookup will be disabled
      }
    };

    const loadNonMatches = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/wsdb-alignment/non-matches');
        if (response.ok) {
          const data = await response.json();
          setNonMatches(data);
        }
      } catch (err) {
        console.error('Failed to load non-matches:', err);
        // Don't show error to user, non-matches are optional - filtering happens server-side
      }
    };

    loadWSDBData();
    loadPipelineSoaps();
    loadNonMatches();
  }, []);

  // Lookup function to find WSDB slug by brand and scent (using shared utility with alias support)
  const getWsdbSlugForDisplay = useCallback(
    (brand: string, scent: string): string | null => {
      if (!brand || !scent || wsdbSoaps.length === 0) {
        return null;
      }
      return getWsdbSlug(brand, scent, wsdbSoaps, pipelineSoaps);
    },
    [wsdbSoaps, pipelineSoaps]
  );

  // Callback for delta months
  const handleDeltaMonthsChange = useCallback((months: string[]) => {
    setDeltaMonths(months);
  }, []);

  const analyzeDuplicates = async () => {
    if (selectedMonths.length === 0) {
      setError('Please select at least one month');
      return;
    }

    // Validate limit parameter
    if (limit < 1 || limit > 100) {
      setError('Result limit must be between 1 and 100');
      return;
    }

    // Validate similarity threshold
    if (similarityThreshold < 0.0 || similarityThreshold > 1.0) {
      setError('Similarity threshold must be between 0.0 and 1.0');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // When delta months are enabled, selectedMonths already contains all months (primary + delta)
      const allMonths = selectedMonths;
      const monthsParam = allMonths.join(',');
      const url = `http://localhost:8000/api/soaps/duplicates?months=${monthsParam}&similarity_threshold=${similarityThreshold}&limit=${limit}`;

      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        setDuplicatesResult(data);
        setActiveTab('duplicates');
      } else {
        const errorData = await response.json();
        // Handle different error response formats
        let errorMessage = 'Failed to analyze duplicates';
        if (errorData.detail) {
          if (Array.isArray(errorData.detail)) {
            // Handle validation errors array
            errorMessage = errorData.detail
              .map((err: any) => err.msg || err.message || 'Validation error')
              .join(', ');
          } else if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
          } else if (errorData.detail.msg) {
            errorMessage = errorData.detail.msg;
          }
        }
        setError(errorMessage);
      }
    } catch (err) {
      console.error('Error analyzing duplicates:', err);
      setError('Failed to analyze duplicates');
    } finally {
      setLoading(false);
    }
  };

  const analyzeNeighborSimilarity = async (mode: 'brands' | 'brand_scent' | 'scents') => {
    if (selectedMonths.length === 0) {
      setError('Please select at least one month');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // When delta months are enabled, selectedMonths already contains all months (primary + delta)
      const allMonths = selectedMonths;
      const monthsParam = allMonths.join(',');
      const url = `http://localhost:8000/api/soaps/neighbor-similarity?months=${monthsParam}&mode=${mode}&similarity_threshold=${similarityThreshold}`;

      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        setNeighborSimilarityResult(data);
        setActiveTab(`neighbor-${mode}`);
      } else {
        const errorData = await response.json();
        // Handle different error response formats
        let errorMessage = 'Failed to analyze neighbor similarity';
        if (errorData.detail) {
          if (Array.isArray(errorData.detail)) {
            // Handle validation errors array
            errorMessage = errorData.detail
              .map((err: any) => err.msg || err.message || 'Validation error')
              .join(', ');
          } else if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
          } else if (errorData.detail.msg) {
            errorMessage = errorData.detail.msg;
          }
        }
        setError(errorMessage);
      }
    } catch (err) {
      console.error('Error analyzing neighbor similarity:', err);
      setError('Failed to analyze neighbor similarity');
    } finally {
      setLoading(false);
    }
  };

  const analyzePatterns = async () => {
    if (selectedMonths.length === 0) {
      setError('Please select at least one month');
      return;
    }

    // Validate limit parameter
    if (limit < 1 || limit > 100) {
      setError('Result limit must be between 1 and 100');
      return;
    }

    // Validate similarity threshold
    if (similarityThreshold < 0.0 || similarityThreshold > 1.0) {
      setError('Similarity threshold must be between 0.0 and 1.0');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // When delta months are enabled, selectedMonths already contains all months (primary + delta)
      const allMonths = selectedMonths;
      const monthsParam = allMonths.join(',');
      const url = `http://localhost:8000/api/soaps/pattern-suggestions?months=${monthsParam}&limit=${limit}`;

      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        setPatternsResult(data);
        setActiveTab('patterns');
      } else {
        const errorData = await response.json();
        // Handle different error response formats
        let errorMessage = 'Failed to analyze patterns';
        if (errorData.detail) {
          if (Array.isArray(errorData.detail)) {
            // Handle validation errors array
            errorMessage = errorData.detail
              .map((err: any) => err.msg || err.message || 'Validation error')
              .join(', ');
          } else if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
          } else if (errorData.detail.msg) {
            errorMessage = errorData.detail.msg;
          }
        }
        setError(errorMessage);
      }
    } catch (err) {
      console.error('Error analyzing patterns:', err);
      setError('Failed to analyze patterns');
    } finally {
      setLoading(false);
    }
  };

  const getSimilarityColor = (similarity: number) => {
    if (similarity >= 0.9) return 'bg-red-100 text-red-800';
    if (similarity >= 0.8) return 'bg-orange-100 text-orange-800';
    if (similarity >= 0.7) return 'bg-yellow-100 text-yellow-800';
    return 'bg-green-100 text-green-800';
  };

  const getNeighborSimilarityColor = (similarity: number) => {
    // For neighbor similarity: red = very similar (potential grouping issue), green = very different (good separation)
    if (similarity >= 0.9) return 'bg-red-100 text-red-800'; // Very similar - potential issue
    if (similarity >= 0.8) return 'bg-orange-100 text-orange-800'; // Similar - review needed
    if (similarity >= 0.7) return 'bg-yellow-100 text-yellow-800'; // Somewhat similar - monitor
    return 'bg-green-100 text-green-800'; // Different - good separation
  };

  const getMatchTypeColor = (matchType: string) => {
    switch (matchType) {
      case 'exact':
        return 'bg-green-100 text-green-800';
      case 'regex':
        return 'bg-blue-100 text-blue-800';
      case 'brand':
        return 'bg-orange-100 text-orange-800';
      case 'dash_split':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // Comment handling functions
  const handleCommentClick = async (commentId: string) => {
    if (!commentId) return;

    try {
      setCommentLoading(true);
      // When delta months are enabled, selectedMonths already contains all months (primary + delta)
      const allMonths = selectedMonths;
      const comment = await getCommentDetail(commentId, allMonths);
      setSelectedComment(comment);
      setCommentModalOpen(true);
    } catch (err) {
      console.error('Failed to load comment:', err);
      setError('Failed to load comment details');
    } finally {
      setCommentLoading(false);
    }
  };

  const handleCloseCommentModal = () => {
    setCommentModalOpen(false);
    setSelectedComment(null);
  };

  const handleNotAMatch = async (
    entry1: SoapNeighborSimilarityResult,
    entry2: SoapNeighborSimilarityResult,
    mode: 'brands' | 'brand_scent' | 'scents'
  ) => {
    try {
      setLoading(true);
      setError(null);

      // Extract brand and scent from entries based on mode
      const getBrandScent = (entry: SoapNeighborSimilarityResult) => {
        // Prefer matched data if available (most reliable)
        if (entry.matched) {
          const brand = entry.matched.brand || entry.matched.maker || '';
          const scent = entry.matched.scent || '';
          
          if (mode === 'brands') {
            return { brand, scent: '' };
          } else if (mode === 'brand_scent') {
            return { brand, scent };
          } else {
            // scents mode
            return { brand, scent };
          }
        }
        
        // Fallback: parse from entry string
        if (mode === 'brands') {
          return { brand: entry.entry, scent: '' };
        } else if (mode === 'brand_scent') {
          const parts = entry.entry.split(' - ');
          return { brand: parts[0] || '', scent: parts.slice(1).join(' - ') || '' };
        } else {
          // scents mode - entry.entry is the scent, need brand from matched data
          // In scents mode, matched data should always be available, but if not, we can't extract brand
          // The validation below will catch this case
          return { brand: '', scent: entry.entry };
        }
      };

      const entry1Data = getBrandScent(entry1);
      const entry2Data = getBrandScent(entry2);

      // Validate required fields
      if (!entry1Data.brand || !entry2Data.brand) {
        setError('Missing brand information for one or both entries');
        return;
      }

      if ((mode === 'brand_scent' || mode === 'scents') && (!entry1Data.scent || !entry2Data.scent)) {
        setError('Missing scent information for one or both entries');
        return;
      }

      const requestBody = {
        mode: mode,
        entry1_brand: entry1Data.brand,
        entry1_scent: entry1Data.scent || null,
        entry2_brand: entry2Data.brand,
        entry2_scent: entry2Data.scent || null,
      };

      // Call API to save non-match
      const response = await fetch('http://localhost:8000/api/soaps/non-matches', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        setError(errorData.detail || errorData.message || 'Failed to save non-match');
        return;
      }

      const data = await response.json();
      if (data.success === false) {
        setError(data.message || 'Failed to save non-match');
        return;
      }

      // Reload non-matches
      try {
        const nonMatchesResponse = await fetch('http://localhost:8000/api/wsdb-alignment/non-matches');
        if (nonMatchesResponse.ok) {
          const nonMatchesData = await nonMatchesResponse.json();
          setNonMatches(nonMatchesData);
        }
      } catch (err) {
        console.error('Failed to reload non-matches:', err);
      }

      // Re-run analysis to see updated results
      if (neighborSimilarityResult) {
        const currentMode = neighborSimilarityResult.mode as 'brands' | 'brand_scent' | 'scents';
        await analyzeNeighborSimilarity(currentMode);
      }

      // Show success message (optional, could use a toast notification)
      console.log('Non-match saved successfully');
    } catch (err) {
      console.error('Error saving non-match:', err);
      setError(err instanceof Error ? err.message : 'Error saving non-match');
    } finally {
      setLoading(false);
    }
  };

  // Filtered results for neighbor similarity (text search only - similarity filtering is now server-side)
  const filteredNeighborResults = useMemo(() => {
    if (!neighborSimilarityResult?.results) {
      return [];
    }

    let results = neighborSimilarityResult.results;

    // Apply text search filtering if there's filter text
    if (filterText.trim()) {
      const searchTerm = filterText.toLowerCase();
      results = results.filter(
        result =>
          result.entry.toLowerCase().includes(searchTerm) ||
          (result.matched?.brand && result.matched.brand.toLowerCase().includes(searchTerm)) ||
          (result.matched?.scent && result.matched.scent.toLowerCase().includes(searchTerm)) ||
          (result.normalized_string &&
            result.normalized_string.toLowerCase().includes(searchTerm)) ||
          (result.pattern && result.pattern.toLowerCase().includes(searchTerm)) ||
          (result.match_types &&
            result.match_types.some(mt => mt.toLowerCase().includes(searchTerm))) ||
          (result.comment_ids &&
            result.comment_ids.some(id => id.toLowerCase().includes(searchTerm)))
      );
    }

    return results;
  }, [neighborSimilarityResult, filterText]);

  return (
    <div className='container mx-auto p-6 space-y-6'>
      <div className='text-center'>
        <h1 className='text-3xl font-bold text-gray-900 mb-2'>🧼 Soap Analyzer</h1>
        <p className='text-gray-600'>
          Analyze soap matches for duplicates and pattern suggestions to improve data quality.
        </p>
      </div>

      {/* Month Selection */}
      <Card>
        <CardHeader>
          <CardTitle>Select Months</CardTitle>
        </CardHeader>
        <CardContent>
          <MonthSelector
            selectedMonths={selectedMonths}
            onMonthsChange={setSelectedMonths}
            multiple={true}
            label='Analysis Months'
            enableDeltaMonths={true}
            onDeltaMonthsChange={handleDeltaMonthsChange}
          />
        </CardContent>
      </Card>

      {/* Delta Months Info Panel */}
      <DeltaMonthsInfoPanel
        selectedMonths={selectedMonths}
        deltaMonths={deltaMonths}
        variant='card'
      />

      {/* Analysis Controls */}
      <Card>
        <CardHeader>
          <CardTitle>Analysis Settings</CardTitle>
        </CardHeader>
        <CardContent className='space-y-4'>
          <div className='grid grid-cols-1 md:grid-cols-3 gap-4'>
            <div>
              <label className='block text-sm font-medium text-gray-700 mb-2'>
                Similarity Threshold (Duplicates & Neighbor Analysis)
              </label>
              <div className='flex items-center space-x-2'>
                <input
                  type='range'
                  min='0.0'
                  max='1.0'
                  step='0.01'
                  value={similarityThreshold}
                  onChange={e => setSimilarityThreshold(parseFloat(e.target.value))}
                  className='flex-1'
                />
                <span className='text-sm font-mono w-12'>{similarityThreshold}</span>
              </div>
              <p className='text-xs text-gray-500 mt-1'>
                For neighbor analysis: Controls server-side filtering. Only entries meeting this
                threshold are returned.
              </p>
            </div>

            <div>
              <label className='block text-sm font-medium text-gray-700 mb-2'>Result Limit</label>
              <Input
                type='number'
                min='1'
                max='100'
                value={limit}
                onChange={e => {
                  const value = parseInt(e.target.value);
                  if (value && value >= 1 && value <= 100) {
                    setLimit(value);
                  }
                }}
                className='w-full'
                placeholder='1-100'
              />
              <p className='text-xs text-gray-500 mt-1'>Maximum 100 results</p>
            </div>

            <div className='flex items-end space-x-2'>
              <Button
                onClick={analyzeDuplicates}
                disabled={loading || selectedMonths.length === 0}
                className='flex-1'
              >
                {loading ? 'Analyzing...' : 'Analyze Duplicates'}
              </Button>
              <Button
                onClick={analyzePatterns}
                disabled={loading || selectedMonths.length === 0}
                variant='outline'
                className='flex-1'
              >
                {loading ? 'Analyzing...' : 'Analyze Patterns'}
              </Button>
            </div>

            {/* Neighbor Similarity Analysis */}
            <div className='col-span-full'>
              <label className='block text-sm font-medium text-gray-700 mb-2'>
                Neighbor Similarity Analysis
              </label>
              <div className='flex flex-wrap gap-2'>
                <Button
                  onClick={() => analyzeNeighborSimilarity('brands')}
                  disabled={loading || selectedMonths.length === 0}
                  variant='secondary'
                  size='sm'
                >
                  {loading ? 'Analyzing...' : 'Brands Only'}
                </Button>
                <Button
                  onClick={() => analyzeNeighborSimilarity('brand_scent')}
                  disabled={loading || selectedMonths.length === 0}
                  variant='secondary'
                  size='sm'
                >
                  {loading ? 'Analyzing...' : 'Brand + Scent'}
                </Button>
                <Button
                  onClick={() => analyzeNeighborSimilarity('scents')}
                  disabled={loading || selectedMonths.length === 0}
                  variant='secondary'
                  size='sm'
                >
                  {loading ? 'Analyzing...' : 'Scents Only'}
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Alert variant='destructive'>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Results */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className='w-full'>
        <TabsList className='grid w-full grid-cols-5'>
          <TabsTrigger value='duplicates'>Duplicates</TabsTrigger>
          <TabsTrigger value='patterns'>Patterns</TabsTrigger>
          <TabsTrigger value='neighbor-brands'>Brands</TabsTrigger>
          <TabsTrigger value='neighbor-brand_scent'>Brand+Scent</TabsTrigger>
          <TabsTrigger value='neighbor-scents'>Scents</TabsTrigger>
        </TabsList>

        <TabsContent value='duplicates' className='space-y-4'>
          {duplicatesResult && (
            <Card>
              <CardHeader>
                <CardTitle className='flex items-center justify-between'>
                  Duplicates Found
                  <Badge variant='secondary'>{duplicatesResult.results.length} results</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className='text-sm text-gray-600 mb-4'>
                  {duplicatesResult.message} • {duplicatesResult.total_matches} total matches •
                  Months: {duplicatesResult.months_processed.join(', ')}
                </div>

                {duplicatesResult.results.length > 0 ? (
                  <div className='space-y-4'>
                    {(duplicatesResult.results as SoapDuplicateResult[]).map((result, index) => (
                      <div key={index} className='border rounded-lg p-4 space-y-2'>
                        <div className='flex items-center justify-between'>
                          <div className='flex items-center space-x-2'>
                            <Badge className={getSimilarityColor(result.similarity)}>
                              {result.similarity}
                            </Badge>
                            <span className='text-sm text-gray-500'>Count: {result.count}</span>
                          </div>
                        </div>

                        <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
                          <div>
                            <div className='font-medium text-gray-900'>{result.text1}</div>
                            <div className='text-sm text-gray-600'>
                              Maker: {result.maker1} • Scent: {result.scent1}
                            </div>
                          </div>
                          <div>
                            <div className='font-medium text-gray-900'>{result.text2}</div>
                            <div className='text-sm text-gray-600'>
                              Maker: {result.maker2} • Scent: {result.scent2}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className='text-center py-8 text-gray-500'>
                    No duplicates found with the current similarity threshold.
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value='patterns' className='space-y-4'>
          {patternsResult && (
            <Card>
              <CardHeader>
                <CardTitle className='flex items-center justify-between'>
                  Pattern Suggestions
                  <Badge variant='secondary'>{patternsResult.results.length} results</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className='text-sm text-gray-600 mb-4'>
                  {patternsResult.message} • {patternsResult.total_matches} total matches • Months:{' '}
                  {patternsResult.months_processed.join(', ')}
                </div>

                {patternsResult.results.length > 0 ? (
                  <div className='space-y-4'>
                    {(patternsResult.results as SoapPatternSuggestion[]).map((result, index) => (
                      <div key={index} className='border rounded-lg p-4 space-y-3'>
                        <div className='flex items-center justify-between'>
                          <h4 className='text-lg font-medium text-gray-900'>{result.pattern}</h4>
                          <Badge variant='outline'>{result.count} occurrences</Badge>
                        </div>

                        {result.examples.length > 0 && (
                          <div>
                            <div className='text-sm font-medium text-gray-700 mb-2'>Examples:</div>
                            <div className='space-y-1'>
                              {result.examples.map((example, idx) => (
                                <div
                                  key={idx}
                                  className='text-sm text-gray-600 bg-gray-50 px-3 py-2 rounded'
                                >
                                  {example}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className='text-center py-8 text-gray-500'>
                    No patterns found for the selected months.
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Neighbor Similarity Analysis Tabs */}
        <TabsContent value='neighbor-brands' className='space-y-4'>
          {neighborSimilarityResult && neighborSimilarityResult.mode === 'brands' && (
            <Card>
              <CardHeader>
                <CardTitle className='flex items-center justify-between'>
                  Brands Neighbor Similarity
                  <Badge variant='secondary'>{filteredNeighborResults.length} results</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className='text-sm text-gray-600 mb-4'>
                  {neighborSimilarityResult.message} • {neighborSimilarityResult.total_entries}{' '}
                  total entries • Months: {neighborSimilarityResult.months_processed.join(', ')}
                </div>

                {/* Color Legend */}
                <div className='mb-4 p-3 bg-gray-50 rounded-md'>
                  <div className='text-sm font-medium text-gray-700 mb-2'>Color Legend:</div>
                  <div className='grid grid-cols-2 gap-4 text-xs text-gray-600'>
                    <div className='flex items-center space-x-2'>
                      <div className='w-4 h-4 bg-red-100 border border-red-300 rounded'></div>
                      <span>Red: Very similar (≥0.9) - potential grouping issue</span>
                    </div>
                    <div className='flex items-center space-x-2'>
                      <div className='w-4 h-4 bg-orange-100 border border-orange-300 rounded'></div>
                      <span>Orange: Similar (≥0.8) - review needed</span>
                    </div>
                    <div className='flex items-center space-x-2'>
                      <div className='w-4 h-4 bg-yellow-100 border border-yellow-300 rounded'></div>
                      <span>Yellow: Somewhat similar (≥0.7) - monitor</span>
                    </div>
                    <div className='flex items-center space-x-2'>
                      <div className='w-4 h-4 bg-green-100 border border-green-300 rounded'></div>
                      <span>Green: Different (below 0.7) - good separation</span>
                    </div>
                  </div>
                </div>

                {/* Filter Text Box */}
                <div className='mb-4'>
                  <div className='mb-2 text-xs text-gray-500'>
                    Note: Results are filtered server-side by similarity threshold. Only entries
                    meeting the threshold are shown.
                  </div>
                  <label
                    htmlFor='filter-input'
                    className='block text-sm font-medium text-gray-700 mb-2'
                  >
                    Filter Results
                  </label>
                  <Input
                    id='filter-input'
                    type='text'
                    placeholder='Filter by brand, scent, pattern, or comment ID...'
                    value={filterText}
                    onChange={e => setFilterText(e.target.value)}
                    className='w-full'
                  />
                </div>

                {filteredNeighborResults.length > 0 ? (
                  <div className='overflow-x-auto'>
                    <table className='w-full border-collapse border border-gray-300'>
                      <thead>
                        <tr className='bg-gray-50'>
                          <th className='border border-gray-300 px-3 py-2 text-left font-medium'>
                            Brand
                          </th>
                          <th className='border border-gray-300 px-3 py-2 text-left font-medium'>
                            Similarity to Above
                          </th>
                          <th className='border border-gray-300 px-3 py-2 text-left font-medium'>
                            Similarity to Below
                          </th>
                          <th className='border border-gray-300 px-3 py-2 text-left font-medium'>
                            Normalized String
                          </th>
                          <th className='border border-gray-300 px-3 py-2 text-left font-medium'>
                            Pattern
                          </th>
                          <th className='border border-gray-300 px-3 py-2 text-left font-medium'>
                            Match Type
                          </th>
                          <th className='border border-gray-300 px-3 py-2 text-left font-medium'>
                            Comment IDs
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredNeighborResults.map((result, index) => (
                          <tr key={index} className='hover:bg-gray-50'>
                            <td className='border border-gray-300 px-3 py-2 font-medium'>
                              {result.entry}
                            </td>
                            <td className='border border-gray-300 px-3 py-2'>
                              {index > 0 ? (
                                <div className='flex items-center gap-2'>
                                  <Badge
                                    className={getNeighborSimilarityColor(
                                      result.similarity_to_above || 0
                                    )}
                                  >
                                    {(result.similarity_to_above || 0).toFixed(3)}
                                  </Badge>
                                  <Button
                                    variant='outline'
                                    size='sm'
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      const aboveEntry = filteredNeighborResults[index - 1];
                                      handleNotAMatch(result, aboveEntry, 'brands');
                                    }}
                                    className='text-red-600 hover:bg-red-50 hover:text-red-700 text-xs px-2 py-1 h-6'
                                    disabled={loading}
                                  >
                                    ✕
                                  </Button>
                                </div>
                              ) : (
                                <span className='text-gray-400'>-</span>
                              )}
                            </td>
                            <td className='border border-gray-300 px-3 py-2'>
                              {result.similarity_to_next !== null ? (
                                <div className='flex items-center gap-2'>
                                  <Badge
                                    className={getNeighborSimilarityColor(result.similarity_to_next)}
                                  >
                                    {result.similarity_to_next.toFixed(3)}
                                  </Badge>
                                  <Button
                                    variant='outline'
                                    size='sm'
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      const belowEntry = filteredNeighborResults[index + 1];
                                      handleNotAMatch(result, belowEntry, 'brands');
                                    }}
                                    className='text-red-600 hover:bg-red-50 hover:text-red-700 text-xs px-2 py-1 h-6'
                                    disabled={loading}
                                  >
                                    ✕
                                  </Button>
                                </div>
                              ) : (
                                <span className='text-gray-400'>-</span>
                              )}
                            </td>
                            <td className='border border-gray-300 px-3 py-2 text-sm text-gray-600'>
                              {result.normalized_string || result.entry.toLowerCase()}
                            </td>
                            <td className='border border-gray-300 px-3 py-2 text-sm text-gray-600'>
                              {result.pattern || '-'}
                            </td>
                            <td className='border border-gray-300 px-3 py-2 text-sm text-gray-600'>
                              <div className='flex flex-wrap gap-1'>
                                {(result.match_types || ['unknown']).map((matchType, idx) => (
                                  <span
                                    key={idx}
                                    className={`inline-flex items-center px-1.5 py-0.5 text-xs font-semibold rounded-full ${getMatchTypeColor(matchType)}`}
                                  >
                                    {matchType}
                                  </span>
                                ))}
                              </div>
                            </td>
                            <td className='border border-gray-300 px-3 py-2 text-sm text-gray-600'>
                              <CommentDisplay
                                commentIds={result.comment_ids}
                                onCommentClick={handleCommentClick}
                                commentLoading={commentLoading}
                              />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className='text-center py-8 text-gray-500'>
                    {filterText.trim()
                      ? 'No results match the filter criteria.'
                      : 'No brands found for the selected months.'}
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value='neighbor-brand_scent' className='space-y-4'>
          {neighborSimilarityResult && neighborSimilarityResult.mode === 'brand_scent' && (
            <Card>
              <CardHeader>
                <CardTitle className='flex items-center justify-between'>
                  Brand + Scent Neighbor Similarity
                  <Badge variant='secondary'>{filteredNeighborResults.length} results</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className='text-sm text-gray-600 mb-4'>
                  {neighborSimilarityResult.message} • {neighborSimilarityResult.total_entries}{' '}
                  total entries • Months: {neighborSimilarityResult.months_processed.join(', ')}
                </div>

                {/* Color Legend */}
                <div className='mb-4 p-3 bg-gray-50 rounded-md'>
                  <div className='text-sm font-medium text-gray-700 mb-2'>Color Legend:</div>
                  <div className='grid grid-cols-2 gap-4 text-xs text-gray-600'>
                    <div className='flex items-center space-x-2'>
                      <div className='w-4 h-4 bg-red-100 border border-red-300 rounded'></div>
                      <span>Red: Very similar (≥0.9) - potential grouping issue</span>
                    </div>
                    <div className='flex items-center space-x-2'>
                      <div className='w-4 h-4 bg-orange-100 border border-orange-300 rounded'></div>
                      <span>Orange: Similar (≥0.8) - review needed</span>
                    </div>
                    <div className='flex items-center space-x-2'>
                      <div className='w-4 h-4 bg-yellow-100 border border-yellow-300 rounded'></div>
                      <span>Yellow: Somewhat similar (≥0.7) - monitor</span>
                    </div>
                    <div className='flex items-center space-x-2'>
                      <div className='w-4 h-4 bg-green-100 border border-green-300 rounded'></div>
                      <span>Green: Different (below 0.7) - good separation</span>
                    </div>
                  </div>
                </div>

                {/* Filter Text Box */}
                <div className='mb-4'>
                  <div className='mb-2 text-xs text-gray-500'>
                    Note: Results are filtered server-side by similarity threshold. Only entries
                    meeting the threshold are shown.
                  </div>
                  <label
                    htmlFor='filter-input-brand-scent'
                    className='block text-sm font-medium text-gray-700 mb-2'
                  >
                    Filter Results
                  </label>
                  <Input
                    id='filter-input-brand-scent'
                    type='text'
                    placeholder='Filter by brand, scent, pattern, or comment ID...'
                    value={filterText}
                    onChange={e => setFilterText(e.target.value)}
                    className='w-full'
                  />
                </div>

                {filteredNeighborResults.length > 0 ? (
                  <div className='overflow-x-auto'>
                    <table className='w-full border-collapse border border-gray-300'>
                      <thead>
                        <tr className='bg-gray-50'>
                          <th className='border border-gray-300 px-3 py-2 text-left font-medium'>
                            Brand
                          </th>
                          <th className='border border-gray-300 px-3 py-2 text-left font-medium'>
                            Scent
                          </th>
                          <th className='border border-gray-300 px-3 py-2 text-left font-medium'>
                            Similarity to Above
                          </th>
                          <th className='border border-gray-300 px-3 py-2 text-left font-medium'>
                            Similarity to Below
                          </th>
                          <th className='border border-gray-300 px-3 py-2 text-left font-medium'>
                            Normalized String
                          </th>
                          <th className='border border-gray-300 px-3 py-2 text-left font-medium'>
                            Pattern
                          </th>
                          <th className='border border-gray-300 px-3 py-2 text-left font-medium'>
                            Match Type
                          </th>
                          <th className='border border-gray-300 px-3 py-2 text-left font-medium'>
                            Comment IDs
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredNeighborResults.map((result, index) => {
                          // Parse maker and scent from the entry
                          const parts = result.entry.split(' - ');
                          const maker = parts[0] || '';
                          const scent = parts.slice(1).join(' - ') || '';
                          const slug = getWsdbSlugForDisplay(maker, scent);

                          return (
                            <tr key={index} className='hover:bg-gray-50'>
                              <td className='border border-gray-300 px-3 py-2 font-medium'>
                                {maker}
                              </td>
                              <td className='border border-gray-300 px-3 py-2'>
                                {slug ? (
                                  <a
                                    href={`https://www.wetshavingdatabase.com/software/${slug}/`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-blue-600 hover:text-blue-800 hover:underline"
                                  >
                                    {scent}
                                  </a>
                                ) : (
                                  <span>{scent}</span>
                                )}
                              </td>
                              <td className='border border-gray-300 px-3 py-2'>
                                {index > 0 ? (
                                  <div className='flex items-center gap-2'>
                                    <Badge
                                      className={getNeighborSimilarityColor(
                                        result.similarity_to_above || 0
                                      )}
                                    >
                                      {(result.similarity_to_above || 0).toFixed(3)}
                                    </Badge>
                                    <Button
                                      variant='outline'
                                      size='sm'
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        const aboveEntry = filteredNeighborResults[index - 1];
                                        handleNotAMatch(result, aboveEntry, 'brand_scent');
                                      }}
                                      className='text-red-600 hover:bg-red-50 hover:text-red-700 text-xs px-2 py-1 h-6'
                                      disabled={loading}
                                    >
                                      ✕
                                    </Button>
                                  </div>
                                ) : (
                                  <span className='text-gray-400'>-</span>
                                )}
                              </td>
                              <td className='border border-gray-300 px-3 py-2'>
                                {result.similarity_to_next !== null ? (
                                  <div className='flex items-center gap-2'>
                                    <Badge
                                      className={getNeighborSimilarityColor(
                                        result.similarity_to_next
                                      )}
                                    >
                                      {result.similarity_to_next.toFixed(3)}
                                    </Badge>
                                    <Button
                                      variant='outline'
                                      size='sm'
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        const belowEntry = filteredNeighborResults[index + 1];
                                        handleNotAMatch(result, belowEntry, 'brand_scent');
                                      }}
                                      className='text-red-600 hover:bg-red-50 hover:text-red-700 text-xs px-2 py-1 h-6'
                                      disabled={loading}
                                    >
                                      ✕
                                    </Button>
                                  </div>
                                ) : (
                                  <span className='text-gray-400'>-</span>
                                )}
                              </td>
                              <td className='border border-gray-300 px-3 py-2 text-sm text-gray-600'>
                                {result.normalized_string || result.entry.toLowerCase()}
                              </td>
                              <td className='border border-gray-300 px-3 py-2 text-sm text-gray-600'>
                                {result.pattern || '-'}
                              </td>
                              <td className='border border-gray-300 px-3 py-2 text-sm text-gray-600'>
                                <div className='flex flex-wrap gap-1'>
                                  {(result.match_types || ['unknown']).map((matchType, idx) => (
                                    <span
                                      key={idx}
                                      className={`inline-flex items-center px-1.5 py-0.5 text-xs font-semibold rounded-full ${getMatchTypeColor(matchType)}`}
                                    >
                                      {matchType}
                                    </span>
                                  ))}
                                </div>
                              </td>
                              <td className='border border-gray-300 px-3 py-2 text-sm text-gray-600'>
                                <CommentDisplay
                                  commentIds={result.comment_ids}
                                  onCommentClick={handleCommentClick}
                                  commentLoading={commentLoading}
                                />
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className='text-center py-8 text-gray-500'>
                    {filterText.trim()
                      ? 'No results match the filter criteria.'
                      : 'No brand-scent combinations found for the selected months.'}
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value='neighbor-scents' className='space-y-4'>
          {neighborSimilarityResult && neighborSimilarityResult.mode === 'scents' && (
            <Card>
              <CardHeader>
                <CardTitle className='flex items-center justify-between'>
                  Scents Neighbor Similarity
                  <Badge variant='secondary'>{filteredNeighborResults.length} results</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className='text-sm text-gray-600 mb-4'>
                  {neighborSimilarityResult.message} • {neighborSimilarityResult.total_entries}{' '}
                  total entries • Months: {neighborSimilarityResult.months_processed.join(', ')}
                </div>

                {/* Color Legend */}
                <div className='mb-4 p-3 bg-gray-50 rounded-md'>
                  <div className='text-sm font-medium text-gray-700 mb-2'>Color Legend:</div>
                  <div className='grid grid-cols-2 gap-4 text-xs text-gray-600'>
                    <div className='flex items-center space-x-2'>
                      <div className='w-4 h-4 bg-red-100 border border-red-300 rounded'></div>
                      <span>Red: Very similar (≥0.9) - potential grouping issue</span>
                    </div>
                    <div className='flex items-center space-x-2'>
                      <div className='w-4 h-4 bg-orange-100 border border-orange-300 rounded'></div>
                      <span>Orange: Similar (≥0.8) - review needed</span>
                    </div>
                    <div className='flex items-center space-x-2'>
                      <div className='w-4 h-4 bg-yellow-100 border border-yellow-300 rounded'></div>
                      <span>Yellow: Somewhat similar (≥0.7) - monitor</span>
                    </div>
                    <div className='flex items-center space-x-2'>
                      <div className='w-4 h-4 bg-green-100 border border-green-300 rounded'></div>
                      <span>Green: Different (below 0.7) - good separation</span>
                    </div>
                  </div>
                </div>

                {/* Filter Text Box */}
                <div className='mb-4'>
                  <div className='mb-2 text-xs text-gray-500'>
                    Note: Results are filtered server-side by similarity threshold. Only entries
                    meeting the threshold are shown.
                  </div>
                  <label
                    htmlFor='filter-input-scents'
                    className='block text-sm font-medium text-gray-700 mb-2'
                  >
                    Filter Results
                  </label>
                  <Input
                    id='filter-input-scents'
                    type='text'
                    placeholder='Filter by brand, scent, pattern, or comment ID...'
                    value={filterText}
                    onChange={e => setFilterText(e.target.value)}
                    className='w-full'
                  />
                </div>

                {filteredNeighborResults.length > 0 ? (
                  <div className='overflow-x-auto'>
                    <table className='w-full border-collapse border border-gray-300'>
                      <thead>
                        <tr className='bg-gray-50'>
                          <th className='border border-gray-300 px-3 py-2 text-left font-medium'>
                            Brand
                          </th>
                          <th className='border border-gray-300 px-3 py-2 text-left font-medium'>
                            Scent
                          </th>
                          <th className='border border-gray-300 px-3 py-2 text-left font-medium'>
                            Similarity to Above
                          </th>
                          <th className='border border-gray-300 px-3 py-2 text-left font-medium'>
                            Similarity to Below
                          </th>
                          <th className='border border-gray-300 px-3 py-2 text-left font-medium'>
                            Normalized String
                          </th>
                          <th className='border border-gray-300 px-3 py-2 text-left font-medium'>
                            Pattern
                          </th>
                          <th className='border border-gray-300 px-3 py-2 text-left font-medium'>
                            Match Type
                          </th>
                          <th className='border border-gray-300 px-3 py-2 text-left font-medium'>
                            Comment IDs
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredNeighborResults.map((result, index) => {
                          // Use the matched data from the API (brand and scent are already parsed)
                          const brand = result.matched?.brand || result.matched?.maker || '-';
                          const scent = result.matched?.scent || result.entry;
                          const slug = getWsdbSlugForDisplay(brand, scent);

                          return (
                            <tr key={index} className='hover:bg-gray-50'>
                              <td className='border border-gray-300 px-3 py-2 font-medium'>
                                {brand}
                              </td>
                              <td className='border border-gray-300 px-3 py-2'>
                                {slug ? (
                                  <a
                                    href={`https://www.wetshavingdatabase.com/software/${slug}/`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-blue-600 hover:text-blue-800 hover:underline"
                                  >
                                    {scent}
                                  </a>
                                ) : (
                                  <span>{scent}</span>
                                )}
                              </td>
                              <td className='border border-gray-300 px-3 py-2'>
                                {index > 0 ? (
                                  <div className='flex items-center gap-2'>
                                    <Badge
                                      className={getNeighborSimilarityColor(
                                        result.similarity_to_above || 0
                                      )}
                                    >
                                      {(result.similarity_to_above || 0).toFixed(3)}
                                    </Badge>
                                    <Button
                                      variant='outline'
                                      size='sm'
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        const aboveEntry = filteredNeighborResults[index - 1];
                                        handleNotAMatch(result, aboveEntry, 'scents');
                                      }}
                                      className='text-red-600 hover:bg-red-50 hover:text-red-700 text-xs px-2 py-1 h-6'
                                      disabled={loading}
                                    >
                                      ✕
                                    </Button>
                                  </div>
                                ) : (
                                  <span className='text-gray-400'>-</span>
                                )}
                              </td>
                              <td className='border border-gray-300 px-3 py-2'>
                                {result.similarity_to_next !== null ? (
                                  <div className='flex items-center gap-2'>
                                    <Badge
                                      className={getNeighborSimilarityColor(
                                        result.similarity_to_next
                                      )}
                                    >
                                      {result.similarity_to_next.toFixed(3)}
                                    </Badge>
                                    <Button
                                      variant='outline'
                                      size='sm'
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        const belowEntry = filteredNeighborResults[index + 1];
                                        handleNotAMatch(result, belowEntry, 'scents');
                                      }}
                                      className='text-red-600 hover:bg-red-50 hover:text-red-700 text-xs px-2 py-1 h-6'
                                      disabled={loading}
                                    >
                                      ✕
                                    </Button>
                                  </div>
                                ) : (
                                  <span className='text-gray-400'>-</span>
                                )}
                              </td>
                              <td className='border border-gray-300 px-3 py-2 text-sm text-gray-600'>
                                {result.normalized_string || result.entry.toLowerCase()}
                              </td>
                              <td className='border border-gray-300 px-3 py-2 text-sm text-gray-600'>
                                {result.pattern || '-'}
                              </td>
                              <td className='border border-gray-300 px-3 py-2 text-sm text-gray-600'>
                                <div className='flex flex-wrap gap-1'>
                                  {(result.match_types || ['unknown']).map((matchType, idx) => (
                                    <span
                                      key={idx}
                                      className={`inline-flex items-center px-1.5 py-0.5 text-xs font-semibold rounded-full ${getMatchTypeColor(matchType)}`}
                                    >
                                      {matchType}
                                    </span>
                                  ))}
                                </div>
                              </td>
                              <td className='border border-gray-300 px-3 py-2 text-sm text-gray-600'>
                                <CommentDisplay
                                  commentIds={result.comment_ids}
                                  onCommentClick={handleCommentClick}
                                  commentLoading={commentLoading}
                                />
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className='text-center py-8 text-gray-500'>
                    {filterText.trim()
                      ? 'No results match the filter criteria.'
                      : 'No scents found for the selected months.'}
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Comment Modal */}
      {selectedComment && (
        <CommentModal
          comment={selectedComment}
          isOpen={commentModalOpen}
          onClose={handleCloseCommentModal}
          comments={[selectedComment]}
          currentIndex={0}
          onNavigate={async () => { }} // No navigation needed for single comment
          remainingCommentIds={[]}
        />
      )}
    </div>
  );
};

export default SoapAnalyzer;
