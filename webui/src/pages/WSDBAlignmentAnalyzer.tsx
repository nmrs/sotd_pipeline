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
import MonthSelector from '../components/forms/MonthSelector';
import DeltaMonthsInfoPanel from '../components/domain/DeltaMonthsInfoPanel';
import CommentModal from '../components/domain/CommentModal';
import { CommentDisplay } from '../components/domain/CommentDisplay';
import { getCommentDetail, CommentDetail } from '../services/api';
import { useMessaging } from '../hooks/useMessaging';
import MessageDisplay from '../components/feedback/MessageDisplay';

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
  scent_matched_via?: 'canonical' | 'alias';
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
  original_texts?: string[];
  match_types?: string[];
  count?: number;
  comment_ids?: string[];
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

interface NonMatches {
  brand_non_matches: BrandNonMatch[];
  scent_non_matches: ScentNonMatch[];
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
  const [nonMatches, setNonMatches] = useState<NonMatches>({
    brand_non_matches: [],
    scent_non_matches: [],
  });
  // Data source and month selection for match files mode
  const [dataSource, setDataSource] = useState<'catalog' | 'match_files'>('catalog');
  const [selectedMonths, setSelectedMonths] = useState<string[]>([]);
  const [deltaMonths, setDeltaMonths] = useState<string[]>([]);
  const [matchTypeFilter, setMatchTypeFilter] = useState<string>('brand');
  // Sort mode state
  const [sortMode, setSortMode] = useState<'count' | 'alphabetical'>('alphabetical');
  // Comment modal state
  const [commentModalOpen, setCommentModalOpen] = useState(false);
  const [selectedComment, setSelectedComment] = useState<CommentDetail | null>(null);
  const [allComments, setAllComments] = useState<CommentDetail[]>([]);
  const [currentCommentIndex, setCurrentCommentIndex] = useState(0);
  const [remainingCommentIds, setRemainingCommentIds] = useState<string[]>([]);
  const [commentLoading, setCommentLoading] = useState(false);

  // Initialize messaging hook for toast notifications
  const { messages, addErrorMessage, addSuccessMessage, removeMessage } = useMessaging();

  // Callback for delta months
  const handleDeltaMonthsChange = useCallback((months: string[]) => {
    setDeltaMonths(months);
  }, []);

  // Separate function to reload just pipeline soaps (for alias updates)
  // Defined before useEffect to avoid "Cannot access before initialization" error
  const reloadPipelineSoaps = useCallback(async () => {
    try {
      const pipelineResponse = await fetch('http://localhost:8000/api/wsdb-alignment/load-pipeline');
      if (!pipelineResponse.ok) throw new Error('Failed to load pipeline soaps');
      const pipelineData = await pipelineResponse.json();
      setPipelineSoaps(pipelineData.soaps);
    } catch (err) {
      console.error('Failed to reload pipeline soaps:', err);
      // Don't show error to user, just log it
    }
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

  // Load data on mount and when switching modes
  React.useEffect(() => {
    if (dataSource === 'catalog') {
      loadData();
      loadNonMatches();
    } else {
      // In match files mode, we still need pipeline soaps for alias lookup and Add Alias functionality
      // Load just pipeline soaps (WSDB is loaded by backend in match files mode)
      reloadPipelineSoaps();
      loadNonMatches();
    }
  }, [dataSource, reloadPipelineSoaps]);

  // Clear results when switching data sources and update sort mode
  React.useEffect(() => {
    setPipelineResults([]);
    setWsdbResults([]);
    setError(null);
    setSuccessMessage(null);
    // Update sort mode based on data source
    setSortMode(dataSource === 'match_files' ? 'count' : 'alphabetical');
  }, [dataSource]);

  const loadNonMatches = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/wsdb-alignment/non-matches');
      if (response.ok) {
        const data = await response.json();
        setNonMatches(data);
      }
    } catch (err) {
      console.error('Failed to load non-matches:', err);
      // Don't show error to user, non-matches are optional
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
    if (dataSource === 'catalog') {
      if (pipelineSoaps.length === 0 || wsdbSoaps.length === 0) {
        setError('Please load data first');
        return;
      }
    } else {
      // Match files mode
      if (selectedMonths.length === 0) {
        setError('Please select at least one month');
        return;
      }
    }

    try {
      setLoading(true);
      setError(null);
      setSuccessMessage(null);

      let response;
      if (dataSource === 'catalog') {
        // Use batch analysis endpoint for catalog mode
        response = await fetch(
          `http://localhost:8000/api/wsdb-alignment/batch-analyze?threshold=${similarityThreshold}&limit=${resultLimit}&mode=${analysisMode}&brand_threshold=0.8`,
          {
            method: 'POST',
          }
        );
      } else {
        // Use match files endpoint
        // When delta months are enabled, selectedMonths already contains all months (primary + delta)
        const allMonths = selectedMonths;
        const monthsParam = allMonths.join(',');
        response = await fetch(
          `http://localhost:8000/api/wsdb-alignment/batch-analyze-match-files?months=${monthsParam}&threshold=${similarityThreshold}&limit=${resultLimit}&mode=${analysisMode}&brand_threshold=0.8&match_type_filter=all`,
          {
            method: 'POST',
          }
        );
      }

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Backend error response:', errorText);
        throw new Error(`Failed to analyze alignment: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      console.log('Analysis response received:', {
        pipeline_count: data.pipeline_results?.length || 0,
        wsdb_count: data.wsdb_results?.length || 0,
        mode: data.mode,
      });
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

  // Handler for confidence filter changes - auto-triggers analysis if results exist
  const handleConfidenceFilterChange = (
    filter: 'all' | 'perfect' | 'non_perfect' | 'high' | 'medium' | 'low'
  ) => {
    setConfidenceFilter(filter);
    // Auto-trigger analysis if we have results (user has analyzed before)
    if (pipelineResults.length > 0 || wsdbResults.length > 0) {
      analyzeAlignment();
    }
  };

  const handleNotAMatch = async (source: AlignmentResult, match: FuzzyMatch) => {
    // Determine match type based on current mode
    const matchType = analysisMode === 'brands' ? 'brand' : 'scent';

    // Build request payload
    const payload = {
      match_type: matchType,
      pipeline_brand: source.source_brand,
      wsdb_brand: match.brand,
      ...(matchType === 'scent' && {
        pipeline_scent: source.source_scent,
        wsdb_scent: match.name,
      }),
    };

    try {
      // Auto-save to backend
      const response = await fetch('http://localhost:8000/api/wsdb-alignment/non-matches', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const data = await response.json();
        
        // Check if the backend returned success: false
        if (data.success === false) {
          setError(data.message || 'Failed to save non-match');
          return;
        }

        // Reload non-matches
        await loadNonMatches();

        // Re-run analysis to filter out the new non-match
        await analyzeAlignment();

        // Show success message
        setSuccessMessage(data.message || 'Non-match saved successfully');
      } else {
        const errorData = await response.json().catch(() => ({}));
        setError(errorData.detail || errorData.message || 'Failed to save non-match');
      }
    } catch (err) {
      console.error('Error saving non-match:', err);
      setError(err instanceof Error ? err.message : 'Error saving non-match');
    }
  };

  const handleAddAlias = async (source: AlignmentResult, match: FuzzyMatch) => {
    // Determine which is the pipeline brand and which is the alias to add
    // match.source indicates where the match came from ("wsdb" or "pipeline")
    let pipelineBrand: string;
    let aliasToAdd: string;

    if (match.source === 'wsdb') {
      // Pipeline → WSDB: source is pipeline, match is WSDB
      pipelineBrand = source.source_brand;
      aliasToAdd = match.brand;
    } else {
      // WSDB → Pipeline: source is WSDB, match is pipeline
      pipelineBrand = match.brand;
      aliasToAdd = source.source_brand;
    }

    try {
      // Send request to add alias
      const response = await fetch('http://localhost:8000/api/wsdb-alignment/add-alias', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pipeline_brand: pipelineBrand,
          alias: aliasToAdd,
        }),
      });

      if (response.ok) {
        // Reload pipeline soaps to get updated aliases (works in both modes)
        await reloadPipelineSoaps();

        // Re-run analysis to see updated matches
        await analyzeAlignment();

        // Show success message
        setSuccessMessage(`Added "${aliasToAdd}" as alias for "${pipelineBrand}"`);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to add alias');
      }
    } catch (err) {
      console.error('Error adding alias:', err);
      setError(err instanceof Error ? err.message : 'Error adding alias');
    }
  };

  const handleAddScentAlias = async (source: AlignmentResult, match: FuzzyMatch) => {
    // Determine which brand and scent to use based on match direction
    // match.source indicates where the match came from ("wsdb" or "pipeline")
    let pipelineBrand: string;
    let pipelineScent: string;
    let aliasToAdd: string;

    if (match.source === 'wsdb') {
      // Pipeline → WSDB: source is pipeline, match is WSDB
      pipelineBrand = source.source_brand;
      pipelineScent = source.source_scent;
      aliasToAdd = match.name; // WSDB scent name
    } else {
      // WSDB → Pipeline: source is WSDB, match is pipeline
      pipelineBrand = match.brand;
      pipelineScent = match.name;
      aliasToAdd = source.source_scent; // WSDB scent name
    }

    try {
      // Send request to add scent alias
      const response = await fetch('http://localhost:8000/api/wsdb-alignment/add-scent-alias', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pipeline_brand: pipelineBrand,
          pipeline_scent: pipelineScent,
          alias: aliasToAdd,
        }),
      });

      if (response.ok) {
        // Reload pipeline soaps to get updated aliases (works in both modes)
        await reloadPipelineSoaps();

        // Re-run analysis to see updated matches
        await analyzeAlignment();

        // Show success message as toast
        addSuccessMessage(`Added "${aliasToAdd}" as scent alias for "${pipelineBrand} - ${pipelineScent}"`);
      } else {
        // Handle error response gracefully (may not be JSON)
        const errorData = await response.json().catch(() => ({}));
        
        // Extract error message with context
        let errorMessage = errorData.detail || errorData.message;
        
        // Provide user-friendly error messages for common cases
        if (response.status === 404) {
          if (errorMessage?.includes('Scent') && errorMessage?.includes('not found')) {
            errorMessage = `Scent '${pipelineScent}' not found in brand '${pipelineBrand}' in catalog. Please add the scent to the catalog first.`;
          } else if (errorMessage?.includes('Brand') && errorMessage?.includes('not found')) {
            errorMessage = `Brand '${pipelineBrand}' not found in catalog. Please add the brand to the catalog first.`;
          } else {
            errorMessage = errorMessage || `Scent '${pipelineScent}' not found in brand '${pipelineBrand}' in catalog. Please add the scent to the catalog first.`;
          }
        } else {
          errorMessage = errorMessage || 'Failed to add scent alias';
        }
        
        // Show error message as toast
        addErrorMessage(errorMessage);
      }
    } catch (err) {
      console.error('Error adding scent alias:', err);
      addErrorMessage(err instanceof Error ? err.message : 'Error adding scent alias');
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
    } catch (err) {
      console.error('Error loading comment:', err);
      setError(err instanceof Error ? err.message : 'Error loading comment');
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
        } catch (err) {
          console.error('Error loading next comment:', err);
          setError(err instanceof Error ? err.message : 'Error loading next comment');
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
            ) ||
            // Include original_texts in search for match files mode
            (result.original_texts &&
              result.original_texts.some(original => original.toLowerCase().includes(searchTerm))) ||
            // Include match_types in search for match files mode
            (result.match_types &&
              result.match_types.some(mt => mt.toLowerCase().includes(searchTerm)))
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
    () => {
      const filtered = filterResults(pipelineResults);
      // Sort based on sort mode
      return [...filtered].sort((a, b) => {
        // Count-based sorting (match files mode)
        if (dataSource === 'match_files' && sortMode === 'count') {
          const countA = a.count || 0;
          const countB = b.count || 0;
          if (countB !== countA) return countB - countA; // Descending
          // Always subsort alphabetically when counts are tied
          const brandCompare = (a.source_brand || '').localeCompare(b.source_brand || '', undefined, { sensitivity: 'base' });
          if (brandCompare !== 0) return brandCompare;
          return (a.source_scent || '').localeCompare(b.source_scent || '', undefined, { sensitivity: 'base' });
        }
        // Alphabetical sorting (default)
        const brandCompare = (a.source_brand || '').localeCompare(b.source_brand || '', undefined, { sensitivity: 'base' });
        if (brandCompare !== 0) return brandCompare;
        return (a.source_scent || '').localeCompare(b.source_scent || '', undefined, { sensitivity: 'base' });
      });
    },
    [pipelineResults, filterResults, dataSource, sortMode]
  );

  const filteredWsdbResults = useMemo(
    () => {
      const filtered = filterResults(wsdbResults);
      // Sort based on sort mode
      return [...filtered].sort((a, b) => {
        // Count-based sorting (match files mode)
        if (dataSource === 'match_files' && sortMode === 'count') {
          const countA = a.count || 0;
          const countB = b.count || 0;
          if (countB !== countA) return countB - countA; // Descending
          // Always subsort alphabetically when counts are tied
          const brandCompare = (a.source_brand || '').localeCompare(b.source_brand || '', undefined, { sensitivity: 'base' });
          if (brandCompare !== 0) return brandCompare;
          return (a.source_scent || '').localeCompare(b.source_scent || '', undefined, { sensitivity: 'base' });
        }
        // Alphabetical sorting (default)
        const brandCompare = (a.source_brand || '').localeCompare(b.source_brand || '', undefined, { sensitivity: 'base' });
        if (brandCompare !== 0) return brandCompare;
        return (a.source_scent || '').localeCompare(b.source_scent || '', undefined, { sensitivity: 'base' });
      });
    },
    [wsdbResults, filterResults, dataSource, sortMode]
  );

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
          {/* Data Source Selector */}
          <div>
            <label className='block text-sm font-medium text-gray-700 mb-2'>Data Source</label>
            <div className='flex flex-wrap gap-2'>
              <Button
                onClick={() => setDataSource('catalog')}
                disabled={loading}
                variant={dataSource === 'catalog' ? 'default' : 'secondary'}
                size='sm'
              >
                Catalog
              </Button>
              <Button
                onClick={() => setDataSource('match_files')}
                disabled={loading}
                variant={dataSource === 'match_files' ? 'default' : 'secondary'}
                size='sm'
              >
                Match Files
              </Button>
            </div>
            <p className='text-xs text-gray-500 mt-1'>
              {dataSource === 'catalog'
                ? 'Analyze catalog definitions from soaps.yaml'
                : 'Analyze actual match results from match files'}
            </p>
          </div>

          {/* Month Selector (only shown for match files mode) */}
          {dataSource === 'match_files' && (
            <div>
              <label className='block text-sm font-medium text-gray-700 mb-2'>Select Months</label>
              <MonthSelector
                selectedMonths={selectedMonths}
                onMonthsChange={setSelectedMonths}
                multiple={true}
                label='Analysis Months'
                enableDeltaMonths={true}
                onDeltaMonthsChange={handleDeltaMonthsChange}
              />
            </div>
          )}

          {/* Delta Months Info Panel (only shown for match files mode) */}
          {dataSource === 'match_files' && (
            <DeltaMonthsInfoPanel
              selectedMonths={selectedMonths}
              deltaMonths={deltaMonths}
              variant='card'
            />
          )}


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
                disabled={
                  loading ||
                  (dataSource === 'catalog' && (pipelineSoaps.length === 0 || wsdbSoaps.length === 0)) ||
                  (dataSource === 'match_files' && selectedMonths.length === 0)
                }
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
                onClick={() => handleConfidenceFilterChange('all')}
              >
                All
              </Button>
              <Button
                variant={confidenceFilter === 'perfect' ? 'default' : 'outline'}
                size='sm'
                onClick={() => handleConfidenceFilterChange('perfect')}
                className={confidenceFilter === 'perfect' ? 'bg-blue-600 hover:bg-blue-700' : ''}
              >
                Perfect (100%)
              </Button>
              <Button
                variant={confidenceFilter === 'non_perfect' ? 'default' : 'outline'}
                size='sm'
                onClick={() => handleConfidenceFilterChange('non_perfect')}
                className={confidenceFilter === 'non_perfect' ? 'bg-purple-600 hover:bg-purple-700' : ''}
              >
                Non-Perfect (&lt;100%)
              </Button>
              <Button
                variant={confidenceFilter === 'high' ? 'default' : 'outline'}
                size='sm'
                onClick={() => handleConfidenceFilterChange('high')}
                className={confidenceFilter === 'high' ? 'bg-green-600 hover:bg-green-700' : ''}
              >
                High (80-99%)
              </Button>
              <Button
                variant={confidenceFilter === 'medium' ? 'default' : 'outline'}
                size='sm'
                onClick={() => handleConfidenceFilterChange('medium')}
                className={confidenceFilter === 'medium' ? 'bg-yellow-600 hover:bg-yellow-700' : ''}
              >
                Medium (60-79%)
              </Button>
              <Button
                variant={confidenceFilter === 'low' ? 'default' : 'outline'}
                size='sm'
                onClick={() => handleConfidenceFilterChange('low')}
                className={confidenceFilter === 'low' ? 'bg-red-600 hover:bg-red-700' : ''}
              >
                Low (&lt;60%)
              </Button>
            </div>
          </div>

          {/* Sort Mode (only shown in match files mode) */}
          {dataSource === 'match_files' && (
            <div>
              <label className='block text-sm font-medium text-gray-700 mb-2'>Sort By</label>
              <div className='flex flex-wrap gap-2'>
                <Button
                  variant={sortMode === 'count' ? 'default' : 'outline'}
                  size='sm'
                  onClick={() => setSortMode('count')}
                >
                  Count (High to Low)
                </Button>
                <Button
                  variant={sortMode === 'alphabetical' ? 'default' : 'outline'}
                  size='sm'
                  onClick={() => setSortMode('alphabetical')}
                >
                  Alphabetical
                </Button>
              </div>
            </div>
          )}
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
                              {/* Show aliases if available (catalog mode only) */}
                              {dataSource === 'catalog' &&
                                pipelineSoaps.find(s => s.brand === result.source_brand)?.aliases &&
                                pipelineSoaps.find(s => s.brand === result.source_brand)!.aliases!.length > 0 && (
                                  <span className='text-xs text-gray-500 ml-2'>
                                    (aka {pipelineSoaps.find(s => s.brand === result.source_brand)!.aliases!.join(', ')})
                                  </span>
                                )}
                              {/* Show match count (both modes) */}
                              {result.count && result.count > 1 && (
                                <Badge variant='outline' className='ml-2 text-xs'>
                                  {result.count} occurrences
                                </Badge>
                              )}
                              {dataSource === 'match_files' && result.match_types && result.match_types.length > 0 && (
                                <Badge variant='outline' className='ml-2 text-xs'>
                                  {result.match_types.join(', ')}
                                </Badge>
                              )}
                            </div>
                            <div className='text-sm text-gray-600'>
                              {result.matches.length} match{result.matches.length !== 1 ? 'es' : ''}
                              {dataSource === 'match_files' && result.original_texts && result.original_texts.length > 0 && (
                                <span className='ml-2 text-xs'>
                                  • Original: {result.original_texts[0]}
                                  {result.original_texts.length > 1 && ` (+${result.original_texts.length - 1} more)`}
                                </span>
                              )}
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
                          {analysisMode === 'brands'
                            ? // Group by brand in Brands Only mode
                              (() => {
                                const brandGroups = result.matches.reduce((acc, match) => {
                                  if (!acc[match.brand]) {
                                    acc[match.brand] = [];
                                  }
                                  acc[match.brand].push(match);
                                  return acc;
                                }, {} as Record<string, FuzzyMatch[]>);

                                return Object.entries(brandGroups).map(([brand, brandMatches]) => (
                                  <div key={brand} className='border-l-2 border-blue-200 pl-4 space-y-2'>
                                    {/* Brand-level header with "Not a Match" button */}
                                    <div className='flex items-center justify-between mb-2'>
                                      <div className='font-semibold text-gray-900 flex items-center gap-2'>
                                        <span>{brand}</span>
                                        {/* Highlight if matched via alias */}
                                        {brandMatches[0].matched_via === 'alias' && (
                                          <Badge
                                            variant='outline'
                                            className='text-xs bg-blue-50 text-blue-700 border-blue-200'
                                          >
                                            via alias
                                          </Badge>
                                        )}
                                      </div>
                                      <div className='flex items-center gap-2'>
                                        <Badge className={getConfidenceColor(brandMatches[0].confidence)}>
                                          {brandMatches[0].confidence.toFixed(1)}%
                                        </Badge>
                                        <Button
                                          variant='outline'
                                          size='sm'
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            handleAddAlias(result, brandMatches[0]);
                                          }}
                                          className='text-green-600 hover:bg-green-50 hover:text-green-700'
                                        >
                                          + Add Alias
                                        </Button>
                                        <Button
                                          variant='outline'
                                          size='sm'
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            handleNotAMatch(result, brandMatches[0]);
                                          }}
                                          className='text-red-600 hover:bg-red-50 hover:text-red-700'
                                        >
                                          ✕ Not a Match
                                        </Button>
                                      </div>
                                    </div>
                                    {/* List of scents under this brand */}
                                    <div className='pl-4 space-y-1'>
                                      {brandMatches.map((match, idx) => {
                                        const slug = match.details?.slug;
                                        const scentName = match.name || '(no scent name)';
                                        return (
                                          <div key={idx} className='text-sm text-gray-700'>
                                            •{' '}
                                            {slug ? (
                                              <a
                                                href={`https://www.wetshavingdatabase.com/software/${slug}/`}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-blue-600 hover:text-blue-800 hover:underline"
                                              >
                                                {scentName}
                                              </a>
                                            ) : (
                                              <span>{scentName}</span>
                                            )}
                                          </div>
                                        );
                                      })}
                                    </div>
                                    {/* Brand metadata */}
                                    {brandMatches[0].details.collaborators &&
                                      brandMatches[0].details.collaborators.length > 0 && (
                                        <div className='text-sm text-gray-600 pl-4'>
                                          <span className='font-medium'>Collaborators:</span>{' '}
                                          {brandMatches[0].details.collaborators.join(', ')}
                                        </div>
                                      )}
                                  </div>
                                ));
                              })()
                            : // Show individual scent matches in Brand + Scent mode
                              result.matches.map((match, matchIndex) => (
                                <div key={matchIndex} className='border-l-2 border-blue-200 pl-4'>
                                  <div className='flex items-center justify-between mb-2'>
                                    <div className='font-medium text-gray-900 flex items-center gap-2'>
                                      {match.details?.slug ? (
                                        <a
                                          href={`https://www.wetshavingdatabase.com/software/${match.details.slug}/`}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                          className="text-blue-600 hover:text-blue-800 hover:underline"
                                        >
                                          {match.brand}
                                          {match.name && ` - ${match.name}`}
                                        </a>
                                      ) : (
                                        <span>
                                          {match.brand}
                                          {match.name && ` - ${match.name}`}
                                        </span>
                                      )}
                                      {/* Highlight if matched via alias (brand) */}
                                      {match.matched_via === 'alias' && (
                                        <Badge
                                          variant='outline'
                                          className='text-xs bg-blue-50 text-blue-700 border-blue-200'
                                        >
                                          via alias
                                        </Badge>
                                      )}
                                      {/* Highlight if matched via alias (scent) */}
                                      {match.scent_matched_via === 'alias' && (
                                        <Badge
                                          variant='outline'
                                          className='text-xs bg-blue-50 text-blue-700 border-blue-200'
                                        >
                                          scent via alias
                                        </Badge>
                                      )}
                                    </div>
                                    <div className='flex items-center gap-2'>
                                      <Badge className={getConfidenceColor(match.confidence)}>
                                        {match.confidence.toFixed(1)}%
                                      </Badge>
                                      <Button
                                        variant='outline'
                                        size='sm'
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleAddScentAlias(result, match);
                                        }}
                                        className='text-green-600 hover:bg-green-50 hover:text-green-700'
                                      >
                                        + Add Alias
                                      </Button>
                                      <Button
                                        variant='outline'
                                        size='sm'
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleNotAMatch(result, match);
                                        }}
                                        className='text-red-600 hover:bg-red-50 hover:text-red-700'
                                      >
                                        ✕ Not a Match
                                      </Button>
                                    </div>
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
                                    {match.details.collaborators && match.details.collaborators.length > 0 && (
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
                                  </div>
                                </div>
                              ))}
                          {/* Comment Display (match files mode only) */}
                          {dataSource === 'match_files' && result.comment_ids && result.comment_ids.length > 0 && (
                            <div className='mt-4 pt-4 border-t'>
                              <div className='text-sm font-medium text-gray-700 mb-2'>
                                Comment References ({result.comment_ids.length})
                              </div>
                              <CommentDisplay
                                commentIds={result.comment_ids}
                                onCommentClick={(commentId) => handleCommentClick(commentId, result.comment_ids)}
                                commentLoading={commentLoading}
                                maxDisplay={5}
                                className='flex flex-wrap gap-2'
                              />
                            </div>
                          )}
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
                              {/* Show match count (both modes) */}
                              {result.count && result.count > 1 && (
                                <Badge variant='outline' className='ml-2 text-xs'>
                                  {result.count} occurrences
                                </Badge>
                              )}
                              {dataSource === 'match_files' && result.match_types && result.match_types.length > 0 && (
                                <Badge variant='outline' className='ml-2 text-xs'>
                                  {result.match_types.join(', ')}
                                </Badge>
                              )}
                            </div>
                            <div className='text-sm text-gray-600'>
                              {result.matches.length} match{result.matches.length !== 1 ? 'es' : ''}
                              {dataSource === 'match_files' && result.original_texts && result.original_texts.length > 0 && (
                                <span className='ml-2 text-xs'>
                                  • Original: {result.original_texts[0]}
                                  {result.original_texts.length > 1 && ` (+${result.original_texts.length - 1} more)`}
                                </span>
                              )}
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
                          {analysisMode === 'brands'
                            ? // Group by brand in Brands Only mode
                              (() => {
                                const brandGroups = result.matches.reduce((acc, match) => {
                                  if (!acc[match.brand]) {
                                    acc[match.brand] = [];
                                  }
                                  acc[match.brand].push(match);
                                  return acc;
                                }, {} as Record<string, FuzzyMatch[]>);

                                return Object.entries(brandGroups).map(([brand, brandMatches]) => (
                                  <div key={brand} className='border-l-2 border-green-200 pl-4 space-y-2'>
                                    {/* Brand-level header with "Not a Match" button */}
                                    <div className='flex items-center justify-between mb-2'>
                                      <div className='font-semibold text-gray-900 flex items-center gap-2'>
                                        <span>{brand}</span>
                                        {/* Highlight if matched via alias */}
                                        {brandMatches[0].matched_via === 'alias' && (
                                          <Badge
                                            variant='outline'
                                            className='text-xs bg-blue-50 text-blue-700 border-blue-200'
                                          >
                                            via alias
                                          </Badge>
                                        )}
                                      </div>
                                      <div className='flex items-center gap-2'>
                                        <Badge className={getConfidenceColor(brandMatches[0].confidence)}>
                                          {brandMatches[0].confidence.toFixed(1)}%
                                        </Badge>
                                        <Button
                                          variant='outline'
                                          size='sm'
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            handleAddAlias(result, brandMatches[0]);
                                          }}
                                          className='text-green-600 hover:bg-green-50 hover:text-green-700'
                                        >
                                          + Add Alias
                                        </Button>
                                        <Button
                                          variant='outline'
                                          size='sm'
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            handleNotAMatch(result, brandMatches[0]);
                                          }}
                                          className='text-red-600 hover:bg-red-50 hover:text-red-700'
                                        >
                                          ✕ Not a Match
                                        </Button>
                                      </div>
                                    </div>
                                    {/* List of scents under this brand */}
                                    <div className='pl-4 space-y-1'>
                                      {brandMatches.map((match, idx) => {
                                        const slug = match.details?.slug;
                                        const scentName = match.name || '(no scent name)';
                                        return (
                                          <div key={idx} className='text-sm text-gray-700'>
                                            •{' '}
                                            {slug ? (
                                              <a
                                                href={`https://www.wetshavingdatabase.com/software/${slug}/`}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-blue-600 hover:text-blue-800 hover:underline"
                                              >
                                                {scentName}
                                              </a>
                                            ) : (
                                              <span>{scentName}</span>
                                            )}
                                          </div>
                                        );
                                      })}
                                    </div>
                                    {/* Brand metadata */}
                                    {brandMatches[0].details.patterns &&
                                      brandMatches[0].details.patterns.length > 0 && (
                                        <div className='text-sm text-gray-600 pl-4'>
                                          <span className='font-medium'>Patterns:</span>{' '}
                                          {brandMatches[0].details.patterns.join(', ')}
                                        </div>
                                      )}
                                  </div>
                                ));
                              })()
                            : // Show individual scent matches in Brand + Scent mode
                              result.matches.map((match, matchIndex) => (
                                <div key={matchIndex} className='border-l-2 border-green-200 pl-4'>
                                  <div className='flex items-center justify-between mb-2'>
                                    <div className='font-medium text-gray-900 flex items-center gap-2'>
                                      {match.details?.slug ? (
                                        <a
                                          href={`https://www.wetshavingdatabase.com/software/${match.details.slug}/`}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                          className="text-blue-600 hover:text-blue-800 hover:underline"
                                        >
                                          {match.brand}
                                          {match.name && ` - ${match.name}`}
                                        </a>
                                      ) : (
                                        <span>
                                          {match.brand}
                                          {match.name && ` - ${match.name}`}
                                        </span>
                                      )}
                                      {/* Highlight if matched via alias (brand) */}
                                      {match.matched_via === 'alias' && (
                                        <Badge
                                          variant='outline'
                                          className='text-xs bg-blue-50 text-blue-700 border-blue-200'
                                        >
                                          via alias
                                        </Badge>
                                      )}
                                      {/* Highlight if matched via alias (scent) */}
                                      {match.scent_matched_via === 'alias' && (
                                        <Badge
                                          variant='outline'
                                          className='text-xs bg-blue-50 text-blue-700 border-blue-200'
                                        >
                                          scent via alias
                                        </Badge>
                                      )}
                                    </div>
                                    <div className='flex items-center gap-2'>
                                      <Badge className={getConfidenceColor(match.confidence)}>
                                        {match.confidence.toFixed(1)}%
                                      </Badge>
                                      <Button
                                        variant='outline'
                                        size='sm'
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleAddScentAlias(result, match);
                                        }}
                                        className='text-green-600 hover:bg-green-50 hover:text-green-700'
                                      >
                                        + Add Alias
                                      </Button>
                                      <Button
                                        variant='outline'
                                        size='sm'
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleNotAMatch(result, match);
                                        }}
                                        className='text-red-600 hover:bg-red-50 hover:text-red-700'
                                      >
                                        ✕ Not a Match
                                      </Button>
                                    </div>
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
                          {/* Comment Display (match files mode only) */}
                          {dataSource === 'match_files' && result.comment_ids && result.comment_ids.length > 0 && (
                            <div className='mt-4 pt-4 border-t'>
                              <div className='text-sm font-medium text-gray-700 mb-2'>
                                Comment References ({result.comment_ids.length})
                              </div>
                              <CommentDisplay
                                commentIds={result.comment_ids}
                                onCommentClick={(commentId) => handleCommentClick(commentId, result.comment_ids)}
                                commentLoading={commentLoading}
                                maxDisplay={5}
                                className='flex flex-wrap gap-2'
                              />
                            </div>
                          )}
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

      {/* Toast Notifications */}
      <MessageDisplay messages={messages} onRemoveMessage={removeMessage} />
    </div>
  );
};

export default WSDBAlignmentAnalyzer;

