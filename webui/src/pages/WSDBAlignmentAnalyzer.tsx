import React, { useState, useMemo, useCallback } from 'react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Badge } from '../components/ui/badge';
import {
  ChevronDown,
  ChevronRight,
  RefreshCw,
  Search,
  AlertCircle,
  CheckCircle,
} from 'lucide-react';

interface WSDBSoap {
  brand: string;
  name: string;
  slug: string;
  scent_notes: string[];
  collaborators: string[];
  tags: string[];
  category: string;
}

interface PipelineSoap {
  brand: string;
  aliases?: string[];
  scents: Array<{
    name: string;
    patterns: string[];
  }>;
}

interface FuzzyMatch {
  brand: string;
  name: string;
  confidence: number;
  brand_score: number;
  scent_score: number;
  source: string;
  matched_via?: 'canonical' | 'alias';
  details: {
    slug?: string;
    scent_notes?: string[];
    collaborators?: string[];
    tags?: string[];
    category?: string;
    patterns?: string[];
  };
}

interface AlignmentResult {
  source_brand: string;
  source_scent: string;
  matches: FuzzyMatch[];
  expanded?: boolean;
}

const WSDBAlignmentAnalyzer: React.FC = () => {
  const [wsdbSoaps, setWsdbSoaps] = useState<WSDBSoap[]>([]);
  const [pipelineSoaps, setPipelineSoaps] = useState<PipelineSoap[]>([]);
  const [pipelineResults, setPipelineResults] = useState<AlignmentResult[]>([]);
  const [wsdbResults, setWsdbResults] = useState<AlignmentResult[]>([]);
  const [similarityThreshold, setSimilarityThreshold] = useState(0.7);
  const [resultLimit, setResultLimit] = useState(100);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('pipeline-to-wsdb');
  const [filterText, setFilterText] = useState('');
  const [confidenceFilter, setConfidenceFilter] = useState<
    'all' | 'perfect' | 'non_perfect' | 'high' | 'medium' | 'low'
  >('non_perfect');
  const [lastRefreshTime, setLastRefreshTime] = useState<string | null>(null);
  const [analysisMode, setAnalysisMode] = useState<'brands' | 'brand_scent'>('brands');

  // Load data on mount
  React.useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load WSDB soaps
      const wsdbResponse = await fetch('http://localhost:8000/api/wsdb-alignment/load-wsdb');
      if (!wsdbResponse.ok) throw new Error('Failed to load WSDB soaps');
      const wsdbData = await wsdbResponse.json();
      setWsdbSoaps(wsdbData.soaps);

      // Load pipeline soaps
      const pipelineResponse = await fetch('http://localhost:8000/api/wsdb-alignment/load-pipeline');
      if (!pipelineResponse.ok) throw new Error('Failed to load pipeline soaps');
      const pipelineData = await pipelineResponse.json();
      setPipelineSoaps(pipelineData.soaps);

      setSuccessMessage(
        `Loaded ${wsdbData.total_count} WSDB soaps and ${pipelineData.total_brands} pipeline brands`
      );
    } catch (err) {
      console.error('Failed to load data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const refreshWSDBData = async () => {
    try {
      setRefreshing(true);
      setError(null);
      setSuccessMessage(null);

      const response = await fetch('http://localhost:8000/api/wsdb-alignment/refresh-wsdb-data', {
        method: 'POST',
      });

      if (!response.ok) throw new Error('Failed to refresh WSDB data');
      const data = await response.json();

      if (data.success) {
        setSuccessMessage(`WSDB data refreshed: ${data.soap_count} soaps loaded`);
        setLastRefreshTime(new Date(data.updated_at).toLocaleString());
        // Reload data
        await loadData();
      } else {
        setError(data.error || 'Failed to refresh WSDB data');
      }
    } catch (err) {
      console.error('Failed to refresh WSDB data:', err);
      setError(err instanceof Error ? err.message : 'Failed to refresh WSDB data');
    } finally {
      setRefreshing(false);
    }
  };

  const analyzeAlignment = async () => {
    if (pipelineSoaps.length === 0 || wsdbSoaps.length === 0) {
      setError('Please load data first');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setSuccessMessage(null);

      // Use batch analysis endpoint for much better performance
      const response = await fetch(
        `http://localhost:8000/api/wsdb-alignment/batch-analyze?threshold=${similarityThreshold}&limit=${resultLimit}&mode=${analysisMode}`,
        {
          method: 'POST',
        }
      );

      if (!response.ok) throw new Error('Failed to analyze alignment');

      const data = await response.json();
      setPipelineResults(data.pipeline_results || []);
      setWsdbResults(data.wsdb_results || []);

      setSuccessMessage(
        `Analysis complete: ${data.pipeline_results?.length || 0} pipeline results, ${data.wsdb_results?.length || 0} WSDB results`
      );
    } catch (err) {
      console.error('Analysis failed:', err);
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return 'bg-green-100 text-green-800 border-green-300';
    if (confidence >= 60) return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    return 'bg-red-100 text-red-800 border-red-300';
  };

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 80) return 'High';
    if (confidence >= 60) return 'Medium';
    return 'Low';
  };

  const toggleExpanded = (
    result: AlignmentResult,
    setResults: React.Dispatch<React.SetStateAction<AlignmentResult[]>>
  ) => {
    setResults(prev => {
      return prev.map(r => {
        // Match by brand and scent to find the correct result
        if (r.source_brand === result.source_brand && r.source_scent === result.source_scent) {
          return { ...r, expanded: !r.expanded };
        }
        return r;
      });
    });
  };

  // Filter results based on text search and confidence
  const filterResults = useCallback(
    (results: AlignmentResult[]) => {
      let filtered = results;

      // Text filter
      if (filterText.trim()) {
        const searchTerm = filterText.toLowerCase();
        filtered = filtered.filter(
          result =>
            result.source_brand.toLowerCase().includes(searchTerm) ||
            result.source_scent.toLowerCase().includes(searchTerm) ||
            result.matches.some(
              m =>
                m.brand.toLowerCase().includes(searchTerm) ||
                m.name.toLowerCase().includes(searchTerm)
            )
        );
      }

      // Confidence filter
      if (confidenceFilter !== 'all') {
        filtered = filtered.filter(result => {
          if (result.matches.length === 0) return confidenceFilter === 'low';
          const topConfidence = result.matches[0].confidence;
          
          if (confidenceFilter === 'perfect') return topConfidence === 100;
          if (confidenceFilter === 'non_perfect') return topConfidence < 100;
          if (confidenceFilter === 'high') return topConfidence >= 80 && topConfidence < 100;
          if (confidenceFilter === 'medium') return topConfidence >= 60 && topConfidence < 80;
          if (confidenceFilter === 'low') return topConfidence < 60;
          return true;
        });
      }

      return filtered;
    },
    [filterText, confidenceFilter]
  );

  const filteredPipelineResults = useMemo(
    () => filterResults(pipelineResults),
    [pipelineResults, filterResults]
  );

  const filteredWsdbResults = useMemo(() => filterResults(wsdbResults), [wsdbResults, filterResults]);

  // Calculate statistics
  const calculateStats = (results: AlignmentResult[]) => {
    const total = results.length;
    const high = results.filter(r => r.matches.length > 0 && r.matches[0].confidence >= 80).length;
    const medium = results.filter(
      r => r.matches.length > 0 && r.matches[0].confidence >= 60 && r.matches[0].confidence < 80
    ).length;
    const low = results.filter(
      r => r.matches.length === 0 || r.matches[0].confidence < 60
    ).length;

    return { total, high, medium, low };
  };

  const pipelineStats = useMemo(() => calculateStats(filteredPipelineResults), [filteredPipelineResults]);
  const wsdbStats = useMemo(() => calculateStats(filteredWsdbResults), [filteredWsdbResults]);

  return (
    <div className='container mx-auto p-6 space-y-6'>
      <div className='text-center'>
        <h1 className='text-3xl font-bold text-gray-900 mb-2'>🗃️ WSDB Alignment Analyzer</h1>
        <p className='text-gray-600'>
          Align pipeline soap brands and scents with the Wet Shaving Database catalog using fuzzy
          matching.
        </p>
      </div>

      {/* Analysis Controls */}
      <Card>
        <CardHeader>
          <CardTitle className='flex items-center justify-between'>
            <span>Analysis Settings</span>
            <Button
              onClick={refreshWSDBData}
              disabled={refreshing}
              variant='outline'
              size='sm'
              className='flex items-center space-x-2'
            >
              <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
              <span>{refreshing ? 'Refreshing...' : 'Refresh WSDB Data'}</span>
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent className='space-y-4'>
          <div className='grid grid-cols-1 md:grid-cols-3 gap-4'>
            <div>
              <label className='block text-sm font-medium text-gray-700 mb-2'>
                Similarity Threshold
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
                <span className='text-sm font-mono w-12'>{similarityThreshold.toFixed(2)}</span>
              </div>
              <p className='text-xs text-gray-500 mt-1'>
                Minimum confidence score for matches (0.0-1.0)
              </p>
            </div>

            <div>
              <label className='block text-sm font-medium text-gray-700 mb-2'>Result Limit</label>
              <Input
                type='number'
                min='1'
                max='10000'
                value={resultLimit}
                onChange={e => {
                  const value = parseInt(e.target.value);
                  if (value && value >= 1 && value <= 10000) {
                    setResultLimit(value);
                  }
                }}
                className='w-full'
                placeholder='1-10000'
              />
              <p className='text-xs text-gray-500 mt-1'>Maximum items to analyze per view</p>
            </div>

            <div className='flex items-end'>
              <Button
                onClick={analyzeAlignment}
                disabled={loading || pipelineSoaps.length === 0 || wsdbSoaps.length === 0}
                className='w-full'
              >
                {loading ? 'Analyzing...' : 'Analyze Alignment'}
              </Button>
            </div>
          </div>

          {/* Analysis Mode Selection */}
          <div>
            <label className='block text-sm font-medium text-gray-700 mb-2'>
              Analysis Mode
            </label>
            <div className='flex flex-wrap gap-2'>
              <Button
                onClick={() => setAnalysisMode('brands')}
                disabled={loading}
                variant={analysisMode === 'brands' ? 'default' : 'secondary'}
                size='sm'
              >
                Brands Only
              </Button>
              <Button
                onClick={() => setAnalysisMode('brand_scent')}
                disabled={loading}
                variant={analysisMode === 'brand_scent' ? 'default' : 'secondary'}
                size='sm'
              >
                Brand + Scent
              </Button>
            </div>
            <p className='text-xs text-gray-500 mt-1'>
              {analysisMode === 'brands'
                ? 'Match only on brand names (ignores scent in scoring)'
                : 'Match on both brand and scent names (60% brand + 40% scent)'}
            </p>
          </div>

          {lastRefreshTime && (
            <div className='text-sm text-gray-600'>
              <span className='font-medium'>Last WSDB refresh:</span> {lastRefreshTime}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Success/Error Messages */}
      {successMessage && (
        <Alert>
          <CheckCircle className='h-4 w-4' />
          <AlertDescription>{successMessage}</AlertDescription>
        </Alert>
      )}

      {error && (
        <Alert variant='destructive'>
          <AlertCircle className='h-4 w-4' />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent className='space-y-4'>
          <div>
            <label className='block text-sm font-medium text-gray-700 mb-2'>Search</label>
            <div className='relative'>
              <Search className='absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400' />
              <Input
                type='text'
                placeholder='Filter by brand, scent, or any field...'
                value={filterText}
                onChange={e => setFilterText(e.target.value)}
                className='pl-10'
              />
            </div>
          </div>

          <div>
            <label className='block text-sm font-medium text-gray-700 mb-2'>
              Confidence Level
            </label>
            <div className='flex flex-wrap gap-2'>
              <Button
                variant={confidenceFilter === 'all' ? 'default' : 'outline'}
                size='sm'
                onClick={() => setConfidenceFilter('all')}
              >
                All
              </Button>
              <Button
                variant={confidenceFilter === 'perfect' ? 'default' : 'outline'}
                size='sm'
                onClick={() => setConfidenceFilter('perfect')}
                className={confidenceFilter === 'perfect' ? 'bg-blue-600 hover:bg-blue-700' : ''}
              >
                Perfect (100%)
              </Button>
              <Button
                variant={confidenceFilter === 'non_perfect' ? 'default' : 'outline'}
                size='sm'
                onClick={() => setConfidenceFilter('non_perfect')}
                className={confidenceFilter === 'non_perfect' ? 'bg-purple-600 hover:bg-purple-700' : ''}
              >
                Non-Perfect (&lt;100%)
              </Button>
              <Button
                variant={confidenceFilter === 'high' ? 'default' : 'outline'}
                size='sm'
                onClick={() => setConfidenceFilter('high')}
                className={confidenceFilter === 'high' ? 'bg-green-600 hover:bg-green-700' : ''}
              >
                High (80-99%)
              </Button>
              <Button
                variant={confidenceFilter === 'medium' ? 'default' : 'outline'}
                size='sm'
                onClick={() => setConfidenceFilter('medium')}
                className={confidenceFilter === 'medium' ? 'bg-yellow-600 hover:bg-yellow-700' : ''}
              >
                Medium (60-79%)
              </Button>
              <Button
                variant={confidenceFilter === 'low' ? 'default' : 'outline'}
                size='sm'
                onClick={() => setConfidenceFilter('low')}
                className={confidenceFilter === 'low' ? 'bg-red-600 hover:bg-red-700' : ''}
              >
                Low (&lt;60%)
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Results Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className='w-full'>
        <TabsList className='grid w-full grid-cols-2'>
          <TabsTrigger value='pipeline-to-wsdb'>
            Pipeline → WSDB ({filteredPipelineResults.length})
          </TabsTrigger>
          <TabsTrigger value='wsdb-to-pipeline'>
            WSDB → Pipeline ({filteredWsdbResults.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value='pipeline-to-wsdb' className='space-y-4'>
          {/* Statistics */}
          <Card>
            <CardHeader>
              <CardTitle>Statistics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className='flex flex-wrap gap-4'>
                <div className='flex items-center space-x-2'>
                  <span className='text-sm font-medium text-gray-700'>Total:</span>
                  <Badge variant='secondary'>{pipelineStats.total}</Badge>
                </div>
                <div className='flex items-center space-x-2'>
                  <span className='text-sm font-medium text-gray-700'>High Confidence:</span>
                  <Badge className='bg-green-100 text-green-800 border-green-300'>
                    {pipelineStats.high}
                  </Badge>
                </div>
                <div className='flex items-center space-x-2'>
                  <span className='text-sm font-medium text-gray-700'>Medium Confidence:</span>
                  <Badge className='bg-yellow-100 text-yellow-800 border-yellow-300'>
                    {pipelineStats.medium}
                  </Badge>
                </div>
                <div className='flex items-center space-x-2'>
                  <span className='text-sm font-medium text-gray-700'>Low/No Match:</span>
                  <Badge className='bg-red-100 text-red-800 border-red-300'>
                    {pipelineStats.low}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Results */}
          <Card>
            <CardHeader>
              <CardTitle>Pipeline Soaps with WSDB Matches</CardTitle>
            </CardHeader>
            <CardContent>
              {filteredPipelineResults.length > 0 ? (
                <div className='space-y-2'>
                  {filteredPipelineResults.map((result, index) => (
                    <div key={index} className='border rounded-lg p-4'>
                      <div
                        className='flex items-center justify-between cursor-pointer'
                        onClick={() => toggleExpanded(result, setPipelineResults)}
                      >
                        <div className='flex items-center space-x-3 flex-1'>
                          {result.expanded ? (
                            <ChevronDown className='h-5 w-5 text-gray-500' />
                          ) : (
                            <ChevronRight className='h-5 w-5 text-gray-500' />
                          )}
                          <div>
                            <div className='font-medium text-gray-900'>
                              {result.source_brand}
                              {result.source_scent && ` - ${result.source_scent}`}
                              {/* Show aliases if available */}
                              {pipelineSoaps.find(s => s.brand === result.source_brand)?.aliases &&
                                pipelineSoaps.find(s => s.brand === result.source_brand)!.aliases!.length > 0 && (
                                  <span className='text-xs text-gray-500 ml-2'>
                                    (aka {pipelineSoaps.find(s => s.brand === result.source_brand)!.aliases!.join(', ')})
                                  </span>
                                )}
                            </div>
                            <div className='text-sm text-gray-600'>
                              {result.matches.length} match{result.matches.length !== 1 ? 'es' : ''}
                            </div>
                          </div>
                        </div>
                        {result.matches.length > 0 && (
                          <Badge className={getConfidenceColor(result.matches[0].confidence)}>
                            {getConfidenceLabel(result.matches[0].confidence)} (
                            {result.matches[0].confidence.toFixed(1)}%)
                          </Badge>
                        )}
                      </div>

                      {result.expanded && result.matches.length > 0 && (
                        <div className='mt-4 space-y-3 pl-8'>
                          {result.matches.map((match, matchIndex) => (
                            <div key={matchIndex} className='border-l-2 border-blue-200 pl-4'>
                              <div className='flex items-center justify-between mb-2'>
                                <div className='font-medium text-gray-900 flex items-center gap-2'>
                                  <span>
                                    {match.brand}
                                    {match.name && ` - ${match.name}`}
                                  </span>
                                  {/* Highlight if matched via alias */}
                                  {match.matched_via === 'alias' && (
                                    <Badge variant='outline' className='text-xs bg-blue-50 text-blue-700 border-blue-200'>
                                      via alias
                                    </Badge>
                                  )}
                                </div>
                                <Badge className={getConfidenceColor(match.confidence)}>
                                  {match.confidence.toFixed(1)}%
                                </Badge>
                              </div>
                              <div className='text-sm text-gray-600 space-y-1'>
                                <div>
                                  Brand Score: {match.brand_score.toFixed(1)}% | Scent Score:{' '}
                                  {match.scent_score.toFixed(1)}%
                                </div>
                                {match.details.scent_notes && match.details.scent_notes.length > 0 && (
                                  <div>
                                    <span className='font-medium'>Scent Notes:</span>{' '}
                                    {match.details.scent_notes.join(', ')}
                                  </div>
                                )}
                                {match.details.collaborators &&
                                  match.details.collaborators.length > 0 && (
                                    <div>
                                      <span className='font-medium'>Collaborators:</span>{' '}
                                      {match.details.collaborators.join(', ')}
                                    </div>
                                  )}
                                {match.details.tags && match.details.tags.length > 0 && (
                                  <div>
                                    <span className='font-medium'>Tags:</span>{' '}
                                    {match.details.tags.join(', ')}
                                  </div>
                                )}
                                {match.details.category && (
                                  <div>
                                    <span className='font-medium'>Category:</span>{' '}
                                    {match.details.category}
                                  </div>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className='text-center py-8 text-gray-500'>
                  {pipelineResults.length === 0
                    ? 'No results yet. Click "Analyze Alignment" to start.'
                    : 'No results match the current filters.'}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value='wsdb-to-pipeline' className='space-y-4'>
          {/* Statistics */}
          <Card>
            <CardHeader>
              <CardTitle>Statistics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className='flex flex-wrap gap-4'>
                <div className='flex items-center space-x-2'>
                  <span className='text-sm font-medium text-gray-700'>Total:</span>
                  <Badge variant='secondary'>{wsdbStats.total}</Badge>
                </div>
                <div className='flex items-center space-x-2'>
                  <span className='text-sm font-medium text-gray-700'>High Confidence:</span>
                  <Badge className='bg-green-100 text-green-800 border-green-300'>
                    {wsdbStats.high}
                  </Badge>
                </div>
                <div className='flex items-center space-x-2'>
                  <span className='text-sm font-medium text-gray-700'>Medium Confidence:</span>
                  <Badge className='bg-yellow-100 text-yellow-800 border-yellow-300'>
                    {wsdbStats.medium}
                  </Badge>
                </div>
                <div className='flex items-center space-x-2'>
                  <span className='text-sm font-medium text-gray-700'>Low/No Match:</span>
                  <Badge className='bg-red-100 text-red-800 border-red-300'>{wsdbStats.low}</Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Results */}
          <Card>
            <CardHeader>
              <CardTitle>WSDB Soaps with Pipeline Matches</CardTitle>
            </CardHeader>
            <CardContent>
              {filteredWsdbResults.length > 0 ? (
                <div className='space-y-2'>
                  {filteredWsdbResults.map((result, index) => (
                    <div key={index} className='border rounded-lg p-4'>
                      <div
                        className='flex items-center justify-between cursor-pointer'
                        onClick={() => toggleExpanded(result, setWsdbResults)}
                      >
                        <div className='flex items-center space-x-3 flex-1'>
                          {result.expanded ? (
                            <ChevronDown className='h-5 w-5 text-gray-500' />
                          ) : (
                            <ChevronRight className='h-5 w-5 text-gray-500' />
                          )}
                          <div>
                            <div className='font-medium text-gray-900'>
                              {result.source_brand}
                              {result.source_scent && ` - ${result.source_scent}`}
                            </div>
                            <div className='text-sm text-gray-600'>
                              {result.matches.length} match{result.matches.length !== 1 ? 'es' : ''}
                            </div>
                          </div>
                        </div>
                        {result.matches.length > 0 && (
                          <Badge className={getConfidenceColor(result.matches[0].confidence)}>
                            {getConfidenceLabel(result.matches[0].confidence)} (
                            {result.matches[0].confidence.toFixed(1)}%)
                          </Badge>
                        )}
                      </div>

                      {result.expanded && result.matches.length > 0 && (
                        <div className='mt-4 space-y-3 pl-8'>
                          {result.matches.map((match, matchIndex) => (
                            <div key={matchIndex} className='border-l-2 border-green-200 pl-4'>
                              <div className='flex items-center justify-between mb-2'>
                                <div className='font-medium text-gray-900 flex items-center gap-2'>
                                  <span>
                                    {match.brand}
                                    {match.name && ` - ${match.name}`}
                                  </span>
                                  {/* Highlight if matched via alias */}
                                  {match.matched_via === 'alias' && (
                                    <Badge variant='outline' className='text-xs bg-blue-50 text-blue-700 border-blue-200'>
                                      via alias
                                    </Badge>
                                  )}
                                </div>
                                <Badge className={getConfidenceColor(match.confidence)}>
                                  {match.confidence.toFixed(1)}%
                                </Badge>
                              </div>
                              <div className='text-sm text-gray-600 space-y-1'>
                                <div>
                                  Brand Score: {match.brand_score.toFixed(1)}% | Scent Score:{' '}
                                  {match.scent_score.toFixed(1)}%
                                </div>
                                {match.details.patterns && match.details.patterns.length > 0 && (
                                  <div>
                                    <span className='font-medium'>Patterns:</span>{' '}
                                    {match.details.patterns.join(', ')}
                                  </div>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className='text-center py-8 text-gray-500'>
                  {wsdbResults.length === 0
                    ? 'No results yet. Click "Analyze Alignment" to start.'
                    : 'No results match the current filters.'}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default WSDBAlignmentAnalyzer;

