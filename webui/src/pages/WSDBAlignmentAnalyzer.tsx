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
import { WSDBAlignmentResultExpanded } from '../components/domain/WSDBAlignmentResultExpanded';
import type { AlignmentResult, FuzzyMatch } from '../types/wsdbAlignment';
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
  
  // Ensure all results have matches array initialized
  const ensureMatchesArray = (results: AlignmentResult[]): AlignmentResult[] => {
    return results.map(result => ({
      ...result,
      matches: result.matches || [],
    }));
  };
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
  const [viewMode, setViewMode] = useState<'alignment' | 'slug_finder'>('alignment');
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

  // Track matches that are being processed (optimistic UI)
  const [pendingNonMatches, setPendingNonMatches] = useState<Set<string>>(new Set());
  const [pendingSlugs, setPendingSlugs] = useState<Set<string>>(new Set());
  // Track result key when "No matches" bulk action is in progress (so we can show loading and disable button)
  const [bulkNoMatchResultKey, setBulkNoMatchResultKey] = useState<string | null>(null);

  // Recent per-request errors (same UX as MatchAnalyzer queue errors panel)
  const WSDB_RECENT_ERRORS_LIMIT = 20;
  const [recentErrors, setRecentErrors] = useState<
    Array<{ key: string; message: string; error: string; operation_type: string; completed_at: number }>
  >([]);

  const addRecentError = useCallback(
    (key: string, message: string, error: string, operation_type: string) => {
      setRecentErrors(prev => {
        const next = [
          { key, message, error, operation_type, completed_at: Date.now() / 1000 },
          ...prev,
        ];
        return next.slice(0, WSDB_RECENT_ERRORS_LIMIT);
      });
    },
    []
  );

  const failedItemKeys = useMemo(
    () => new Set(recentErrors.map(e => e.key)),
    [recentErrors]
  );

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
      const pipelineResponse = await fetch('/api/wsdb-alignment/load-pipeline');
      if (!pipelineResponse.ok) throw new Error('Failed to load pipeline soaps');
      const pipelineData = await pipelineResponse.json();
      setPipelineSoaps(pipelineData.soaps);
    } catch (err) {
      console.error('Failed to reload pipeline soaps:', err);
      // Don't show error to user, just log it
    }
  }, []);

  const loadNonMatches = useCallback(async () => {
    try {
      const response = await fetch('/api/wsdb-alignment/non-matches');
      if (response.ok) {
        const data = await response.json();
        setNonMatches(data);
      }
    } catch (err) {
      console.error('Failed to load non-matches:', err);
      // Don't show error to user, non-matches are optional
    }
  }, []);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      setRecentErrors([]);

      // Load WSDB soaps
      const wsdbResponse = await fetch('/api/wsdb-alignment/load-wsdb');
      if (!wsdbResponse.ok) throw new Error('Failed to load WSDB soaps');
      const wsdbData = await wsdbResponse.json();
      setWsdbSoaps(wsdbData.soaps);

      // Load pipeline soaps
      const pipelineResponse = await fetch('/api/wsdb-alignment/load-pipeline');
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
  }, []);

  // Load data on mount and when switching modes
  React.useEffect(() => {
    const loadDataSequentially = async () => {
      if (dataSource === 'catalog') {
        await loadData();
        await loadNonMatches();
      } else {
        // In match files mode, we still need pipeline soaps for slug lookup
        // Load just pipeline soaps (WSDB is loaded by backend in match files mode)
        await reloadPipelineSoaps();
        await loadNonMatches();
      }
    };
    loadDataSequentially();
  }, [dataSource, loadData, loadNonMatches, reloadPipelineSoaps]);

  // Clear results when switching data sources and update sort mode
  React.useEffect(() => {
    setPipelineResults([]);
    setWsdbResults([]);
    setError(null);
    setSuccessMessage(null);
    // Update sort mode based on data source
    setSortMode(dataSource === 'match_files' ? 'count' : 'alphabetical');
  }, [dataSource]);

  const refreshWSDBData = async () => {
    try {
      setRefreshing(true);
      setError(null);
      setSuccessMessage(null);

      const response = await fetch('/api/wsdb-alignment/refresh-wsdb-data', {
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
    const effectiveDataSource = viewMode === 'slug_finder' ? 'catalog' : dataSource;
    const effectiveAnalysisMode = viewMode === 'slug_finder' ? 'brand_scent' : analysisMode;

    if (effectiveDataSource === 'catalog') {
      if (pipelineSoaps.length === 0 || wsdbSoaps.length === 0) {
        setError('Please load data first');
        return;
      }
    } else {
      // Match files mode (alignment only)
      if (selectedMonths.length === 0) {
        setError('Please select at least one month');
        return;
      }
    }

    try {
      setLoading(true);
      setError(null);
      setSuccessMessage(null);
      setRecentErrors([]);

      let response;
      if (effectiveDataSource === 'catalog') {
        // Use batch analysis endpoint for catalog mode (and slug finder uses this with brand_scent)
        response = await fetch(
          `/api/wsdb-alignment/batch-analyze?threshold=${similarityThreshold}&limit=${resultLimit}&mode=${effectiveAnalysisMode}&brand_threshold=0.8`,
          {
            method: 'POST',
          }
        );
      } else {
        // Use match files endpoint (alignment mode only)
        // When delta months are enabled, selectedMonths already contains all months (primary + delta)
        const allMonths = selectedMonths;
        const monthsParam = allMonths.join(',');
        response = await fetch(
          `/api/wsdb-alignment/batch-analyze-match-files?months=${monthsParam}&threshold=${similarityThreshold}&limit=${resultLimit}&mode=${effectiveAnalysisMode}&brand_threshold=0.8&match_type_filter=all`,
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
      
      // Preserve expanded state when updating results
      const preserveExpandedState = (oldResults: AlignmentResult[], newResults: AlignmentResult[]): AlignmentResult[] => {
        const expandedMap = new Map<string, boolean>();
        oldResults.forEach(result => {
          const key = `${result.source_brand}|${result.source_scent || ''}`;
          expandedMap.set(key, result.expanded || false);
        });
        
        return (newResults || []).map(result => {
          const key = `${result.source_brand}|${result.source_scent || ''}`;
          return {
            ...result,
            expanded: expandedMap.get(key) || false,
          };
        });
      };
      
      setPipelineResults(prev => preserveExpandedState(prev, data.pipeline_results || []));
      setWsdbResults(prev => preserveExpandedState(prev, data.wsdb_results || []));

      setSuccessMessage(
        viewMode === 'slug_finder'
          ? `Analysis complete: ${data.pipeline_results?.length || 0} scent suggestions`
          : `Analysis complete: ${data.pipeline_results?.length || 0} pipeline results, ${data.wsdb_results?.length || 0} WSDB results`
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

  // Create unique key for identifying matches
  const getMatchKey = (source: AlignmentResult, match: FuzzyMatch): string => {
    // Create unique key: source_brand|source_scent|wsdb_brand|wsdb_scent
    const sourceKey = `${source.source_brand}|${source.source_scent || ''}`;
    const matchKey = `${match.brand}|${match.name || ''}`;
    return `${sourceKey}|${matchKey}`;
  };

  // Check if a match is pending (being processed)
  const isMatchPending = (source: AlignmentResult, match: FuzzyMatch): boolean => {
    const matchKey = getMatchKey(source, match);
    return pendingNonMatches.has(matchKey);
  };

  // Check if a match has a pending slug being added
  const isSlugPending = (source: AlignmentResult, match: FuzzyMatch): boolean => {
    const matchKey = getMatchKey(source, match);
    return pendingSlugs.has(matchKey);
  };

  // Check if a match is a saved non-match (not just pending)
  // Note: nonMatches.scent_non_matches is actually a nested dict: {brand: {scent_key: [list]}}
  const isNonMatch = (source: AlignmentResult, match: FuzzyMatch): boolean => {
    if (analysisMode === 'brands') {
      // Brand non-matches structure: {brand_key: [list_of_non_matches]}
      const brandNonMatches = nonMatches.brand_non_matches as any || {};
      const sourceBrand = source.source_brand;
      const matchBrand = match.brand;
      
      // Check both directions (canonical keys can be either brand)
      const sourceInKeys = sourceBrand in brandNonMatches;
      const matchInKeys = matchBrand in brandNonMatches;
      
      if (sourceInKeys) {
        const list = brandNonMatches[sourceBrand] || [];
        const matchFound = list.some((nm: string) => 
          nm.toLowerCase().trim() === matchBrand.toLowerCase().trim()
        );
        if (matchFound) {
          return true;
        }
      }
      
      if (matchInKeys) {
        const list = brandNonMatches[matchBrand] || [];
        const sourceFound = list.some((nm: string) => 
          nm.toLowerCase().trim() === sourceBrand.toLowerCase().trim()
        );
        if (sourceFound) {
          return true;
        }
      }
      
      return false;
    } else {
      // Scent non-matches structure: {brand: {scent_key: [list_of_non_matches]}}
      const scentNonMatches = nonMatches.scent_non_matches as any || {};
      const brandData = scentNonMatches[source.source_brand] || {};
      const sourceScent = source.source_scent || '';
      const matchName = match.name || '';
      
      // Check both directions (canonical keys can be either scent)
      const sourceInKeys = sourceScent in brandData;
      const matchInKeys = matchName in brandData;
      
      // Check if source_scent is a key and match_name is in its list
      if (sourceInKeys) {
        const list = brandData[sourceScent] || [];
        const matchFound = list.some((nm: string) => 
          nm.toLowerCase().trim() === matchName.toLowerCase().trim()
        );
        if (matchFound) {
          return true;
        }
      }
      
      // Check if match_name is a key and source_scent is in its list
      if (matchInKeys) {
        const list = brandData[matchName] || [];
        const sourceFound = list.some((nm: string) => 
          nm.toLowerCase().trim() === sourceScent.toLowerCase().trim()
        );
        if (sourceFound) {
          return true;
        }
      }
      
      return false;
    }
  };

  const handleNotAMatch = async (source: AlignmentResult, match: FuzzyMatch) => {
    const matchKey = getMatchKey(source, match);
    
    // Optimistic update: immediately remove from UI
    setPendingNonMatches(prev => new Set(prev).add(matchKey));
    
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

    // Process in background (fire-and-forget)
    fetch('/api/wsdb-alignment/non-matches', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
      .then(async (response) => {
        if (response.ok) {
          const data = await response.json();
          
          if (data.success === false) {
            const msg = data.message || 'Failed to save non-match';
            setPendingNonMatches(prev => {
              const newSet = new Set(prev);
              newSet.delete(matchKey);
              return newSet;
            });
            addRecentError(matchKey, msg, msg, 'non_match');
            setError(msg);
            return;
          }
          
          // Success: reload non-matches and remove from pending set
          // The match will be filtered out on next analysis
          await loadNonMatches();
          // Remove from pending set since it's now saved and will be filtered by backend
          setPendingNonMatches(prev => {
            const newSet = new Set(prev);
            newSet.delete(matchKey);
            return newSet;
          });
          // Don't call analyzeAlignment() here - it causes UI jumping
          // The optimistic update already removed the match from view
          // Use dedupeKey so multiple rapid "not a match" clicks show one toast with incrementing count
          addSuccessMessage(data.message || 'Non-match saved successfully', {
            dedupeKey: 'wsdb-non-match',
          });
        } else {
          const errorData = await response.json().catch(() => ({}));
          const msg = errorData.detail || errorData.message || 'Failed to save non-match';
          setPendingNonMatches(prev => {
            const newSet = new Set(prev);
            newSet.delete(matchKey);
            return newSet;
          });
          addRecentError(matchKey, msg, msg, 'non_match');
          setError(msg);
        }
      })
      .catch((err) => {
        const msg = err instanceof Error ? err.message : 'Error saving non-match';
        setPendingNonMatches(prev => {
          const newSet = new Set(prev);
          newSet.delete(matchKey);
          return newSet;
        });
        addRecentError(matchKey, msg, msg, 'non_match');
        console.error('Error saving non-match:', err);
        setError(msg);
      });
  };

  /** Mark all listed matches for this result as "not a match" in one go. */
  const handleNoMatchesForResult = useCallback(
    async (
      result: AlignmentResult,
      matchesToMark: FuzzyMatch[],
      direction: 'pipeline-to-wsdb' | 'wsdb-to-pipeline'
    ) => {
      if (matchesToMark.length === 0) return;
      const resultKey = `${result.source_brand}|${result.source_scent || ''}`;
      const matchType = analysisMode === 'brands' ? 'brand' : 'scent';

      setBulkNoMatchResultKey(resultKey);
      const matchKeys = matchesToMark.map(m => getMatchKey(result, m));
      setPendingNonMatches(prev => new Set([...prev, ...matchKeys]));

      const buildPayload = (match: FuzzyMatch) => {
        if (direction === 'pipeline-to-wsdb') {
          return {
            match_type: matchType,
            pipeline_brand: result.source_brand,
            wsdb_brand: match.brand,
            ...(matchType === 'scent' && {
              pipeline_scent: result.source_scent,
              wsdb_scent: match.name,
            }),
          };
        }
        return {
          match_type: matchType,
          pipeline_brand: match.brand,
          wsdb_brand: result.source_brand,
          ...(matchType === 'scent' && {
            pipeline_scent: match.name,
            wsdb_scent: result.source_scent,
          }),
        };
      };

      let successCount = 0;
      const failedKeys: string[] = [];

      for (let i = 0; i < matchesToMark.length; i++) {
        const match = matchesToMark[i];
        const key = getMatchKey(result, match);
        try {
          const response = await fetch('/api/wsdb-alignment/non-matches', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(buildPayload(match)),
          });
          const data = await response.json().catch(() => ({}));
          if (response.ok && data.success !== false) {
            successCount += 1;
          } else {
            failedKeys.push(key);
            addRecentError(
              key,
              data.message || data.detail || 'Failed to save non-match',
              data.detail || data.message || 'Failed',
              'non_match'
            );
          }
        } catch (err) {
          failedKeys.push(key);
          const msg = err instanceof Error ? err.message : 'Error saving non-match';
          addRecentError(key, msg, msg, 'non_match');
        }
      }

      setBulkNoMatchResultKey(null);
      setPendingNonMatches(prev => {
        const next = new Set(prev);
        matchKeys.forEach(k => next.delete(k));
        return next;
      });
      if (successCount > 0) {
        await loadNonMatches();
        addSuccessMessage(
          successCount === matchesToMark.length
            ? successCount === 1
              ? 'Non-match saved successfully'
              : `${successCount} non-matches saved successfully`
            : `${successCount} of ${matchesToMark.length} non-matches saved`,
          { dedupeKey: 'wsdb-non-match' }
        );
      }
      if (failedKeys.length > 0) {
        setError(`${failedKeys.length} non-match(s) failed to save. See errors below.`);
      }
    },
    [analysisMode, loadNonMatches, addSuccessMessage, addRecentError]
  );

  const handleAddScentAlias = async (source: AlignmentResult, match: FuzzyMatch) => {
    // Determine which brand and scent to use based on match direction
    // match.source indicates where the match came from ("wsdb" or "pipeline")
    let pipelineBrand: string;
    let pipelineScent: string;
    let wsdbSlug: string | undefined;

    if (match.source === 'wsdb') {
      // Pipeline → WSDB: source is pipeline, match is WSDB
      pipelineBrand = source.source_brand;
      pipelineScent = source.source_scent;
      wsdbSlug = match.details?.slug; // WSDB slug
    } else {
      // WSDB → Pipeline: source is WSDB, match is pipeline
      pipelineBrand = match.brand;
      pipelineScent = match.name;
      // For WSDB → Pipeline, we need the slug from the source (WSDB entry)
      // The source should have the slug in its details
      wsdbSlug = source.matches?.[0]?.details?.slug;
    }

    if (!wsdbSlug) {
      addErrorMessage('No WSDB slug found in match. Cannot add slug to catalog.');
      return;
    }

    const matchKey = getMatchKey(source, match);
    
    // Optimistic update: immediately remove from UI
    setPendingSlugs(prev => new Set(prev).add(matchKey));

    // Process in background (fire-and-forget)
    fetch('/api/wsdb-alignment/add-scent-alias', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pipeline_brand: pipelineBrand,
        pipeline_scent: pipelineScent,
        wsdb_slug: wsdbSlug,
      }),
    })
      .then(async (response) => {
        if (response.ok) {
          const data = await response.json();
          
          if (data.success === false) {
            const msg = data.message || 'Failed to add WSDB slug';
            setPendingSlugs(prev => {
              const newSet = new Set(prev);
              newSet.delete(matchKey);
              return newSet;
            });
            addRecentError(matchKey, msg, msg, 'add_slug');
            addErrorMessage(msg);
            return;
          }
          
          // Success: reload pipeline soaps to get updated slug data, then remove from pending set
          // Remove the result from both lists so the row stays gone (it only exists in one list)
          setPipelineResults(prev =>
            prev.filter(
              r =>
                !(
                  r.source_brand === source.source_brand &&
                  (r.source_scent ?? '') === (source.source_scent ?? '')
                )
            )
          );
          setWsdbResults(prev =>
            prev.filter(
              r =>
                !(
                  r.source_brand === source.source_brand &&
                  (r.source_scent ?? '') === (source.source_scent ?? '')
                )
            )
          );
          await reloadPipelineSoaps();
          setPendingSlugs(prev => {
            const newSet = new Set(prev);
            newSet.delete(matchKey);
            return newSet;
          });
          addSuccessMessage('Added WSDB slug', { dedupeKey: 'wsdb-add-slug' });
        } else {
          const errorData = await response.json().catch(() => ({}));
          let errorMessage = errorData.detail || errorData.message;
          if (response.status === 404) {
            if (errorMessage?.includes('Scent') && errorMessage?.includes('not found')) {
              errorMessage = `Scent '${pipelineScent}' not found in brand '${pipelineBrand}' in catalog. Please add the scent to the catalog first.`;
            } else if (errorMessage?.includes('Brand') && errorMessage?.includes('not found')) {
              errorMessage = `Brand '${pipelineBrand}' not found in catalog. Please add the brand to the catalog first.`;
            } else {
              errorMessage = errorMessage || `Scent '${pipelineScent}' not found in brand '${pipelineBrand}' in catalog. Please add the scent to the catalog first.`;
            }
          } else {
            errorMessage = errorMessage || 'Failed to add WSDB slug';
          }
          setPendingSlugs(prev => {
            const newSet = new Set(prev);
            newSet.delete(matchKey);
            return newSet;
          });
          addRecentError(matchKey, errorMessage, errorMessage, 'add_slug');
          addErrorMessage(errorMessage);
        }
      })
      .catch((err) => {
        const msg = err instanceof Error ? err.message : 'Error adding WSDB slug';
        setPendingSlugs(prev => {
          const newSet = new Set(prev);
          newSet.delete(matchKey);
          return newSet;
        });
        addRecentError(matchKey, msg, msg, 'add_slug');
        console.error('Error adding WSDB slug:', err);
        addErrorMessage(msg);
      });
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
            (result.source_brand && result.source_brand.toLowerCase().includes(searchTerm)) ||
            (result.source_scent && result.source_scent.toLowerCase().includes(searchTerm)) ||
            (result.matches && result.matches.some(
              m =>
                (m.brand && m.brand.toLowerCase().includes(searchTerm)) ||
                (m.name && m.name.toLowerCase().includes(searchTerm))
            )) ||
            // Include original_texts in search for match files mode
            (result.original_texts &&
              result.original_texts.some(original => original && original.toLowerCase().includes(searchTerm))) ||
            // Include match_types in search for match files mode
            (result.match_types &&
              result.match_types.some(mt => mt && mt.toLowerCase().includes(searchTerm)))
        );
      }

      // Confidence filter
      if (confidenceFilter !== 'all') {
        filtered = filtered.filter(result => {
          if (!result.matches || result.matches.length === 0) return confidenceFilter === 'low';
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
      const resultsWithMatches = ensureMatchesArray(pipelineResults);
      const filtered = filterResults(resultsWithMatches);
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
      const resultsWithMatches = ensureMatchesArray(wsdbResults);
      const filtered = filterResults(resultsWithMatches);
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
    const high = results.filter(r => r.matches && r.matches.length > 0 && r.matches[0].confidence >= 80).length;
    const medium = results.filter(
      r => r.matches && r.matches.length > 0 && r.matches[0].confidence >= 60 && r.matches[0].confidence < 80
    ).length;
    const low = results.filter(
      r => !r.matches || r.matches.length === 0 || (r.matches[0] && r.matches[0].confidence < 60)
    ).length;

    return { total, high, medium, low };
  };

  const pipelineStats = useMemo(() => calculateStats(filteredPipelineResults || []), [filteredPipelineResults]);
  const wsdbStats = useMemo(() => calculateStats(filteredWsdbResults || []), [filteredWsdbResults]);

  return (
    <div className='container mx-auto p-6 space-y-6'>
      <div className='text-center'>
        <h1 className='text-3xl font-bold text-gray-900 mb-2'>🗃️ WSDB Alignment Analyzer</h1>
        <p className='text-gray-600'>
          {viewMode === 'slug_finder'
            ? 'Find potential WSDB slugs for each scent in soaps.yaml by matching against the WSDB catalog (software.json).'
            : 'Align pipeline soap brands and scents with the Wet Shaving Database catalog using fuzzy matching.'}
        </p>
        <div className='flex justify-center gap-2 mt-4'>
          <Button
            onClick={() => setViewMode('alignment')}
            variant={viewMode === 'alignment' ? 'default' : 'outline'}
            size='sm'
          >
            Alignment
          </Button>
          <Button
            onClick={() => setViewMode('slug_finder')}
            variant={viewMode === 'slug_finder' ? 'default' : 'outline'}
            size='sm'
          >
            Slug finder
          </Button>
        </div>
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
          {/* Data Source Selector (alignment mode only; slug finder uses catalog only) */}
          {viewMode === 'alignment' && (
            <>
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
            </>
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
                  (viewMode === 'slug_finder' &&
                    ((pipelineSoaps?.length ?? 0) === 0 || (wsdbSoaps?.length ?? 0) === 0)) ||
                  (viewMode === 'alignment' &&
                    dataSource === 'catalog' &&
                    ((pipelineSoaps?.length ?? 0) === 0 || (wsdbSoaps?.length ?? 0) === 0)) ||
                  (viewMode === 'alignment' &&
                    dataSource === 'match_files' &&
                    selectedMonths.length === 0)
                }
                className='w-full'
              >
                {loading
                  ? 'Analyzing...'
                  : viewMode === 'slug_finder'
                    ? 'Find slug suggestions'
                    : 'Analyze Alignment'}
              </Button>
            </div>
          </div>

          {/* Analysis Mode Selection (alignment mode only; slug finder uses brand+scent only) */}
          {viewMode === 'alignment' && (
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
          )}

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

      {/* WSDB alignment errors panel (same UX as MatchAnalyzer queue errors) */}
      {recentErrors.length > 0 && (
        <div className='mb-4 rounded-lg border border-amber-200 bg-amber-50'>
          <details className='group' open={recentErrors.length > 0}>
            <summary className='cursor-pointer list-none px-4 py-2 font-medium text-amber-900'>
              WSDB alignment errors (wsdb_alignment)
            </summary>
            <div className='border-t border-amber-200 px-4 py-3'>
              <ul className='space-y-2 text-sm'>
                {recentErrors.map((e, i) => (
                  <li key={i} className='rounded bg-white/80 p-2'>
                    <span className='font-medium'>{e.operation_type}</span>
                    <span className='ml-1 text-gray-700 break-all'>{e.key}</span>
                    <div className='mt-1 text-red-700'>{e.error || e.message}</div>
                    {e.completed_at > 0 && (
                      <div className='mt-0.5 text-xs text-gray-500'>
                        {new Date(e.completed_at * 1000).toLocaleString()}
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          </details>
        </div>
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

          {/* Sort Mode (only shown in alignment + match files mode) */}
          {viewMode === 'alignment' && dataSource === 'match_files' && (
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

      {/* Results Tabs (single tab for slug finder, two tabs for alignment) */}
      <Tabs
        value={viewMode === 'slug_finder' ? 'pipeline-to-wsdb' : activeTab}
        onValueChange={viewMode === 'slug_finder' ? () => {} : setActiveTab}
        className='w-full'
      >
        <TabsList className={viewMode === 'slug_finder' ? 'grid w-full grid-cols-1' : 'grid w-full grid-cols-2'}>
          <TabsTrigger value='pipeline-to-wsdb'>
            {viewMode === 'slug_finder'
              ? `Slug suggestions (${filteredPipelineResults.length})`
              : `Pipeline → WSDB (${filteredPipelineResults.length})`}
          </TabsTrigger>
          {viewMode === 'alignment' && (
            <TabsTrigger value='wsdb-to-pipeline'>
              WSDB → Pipeline ({filteredWsdbResults.length})
            </TabsTrigger>
          )}
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
                  {filteredPipelineResults
                    .filter(result => {
                      const n = (result.matches || []).filter(
                        m =>
                          !isMatchPending(result, m) &&
                          !isNonMatch(result, m) &&
                          !isSlugPending(result, m)
                      );
                      if (n.length === 0) return false;
                      // When Perfect (100%) filter is on, require at least one displayable 100% match
                      if (confidenceFilter === 'perfect') {
                        return n.some(m => m.confidence === 100);
                      }
                      return true;
                    })
                    .map((result, index) => {
                    // Filter out pending matches, saved non-matches, and pending slugs for this result
                    let nonPendingMatches = (result.matches || []).filter(match =>
                      !isMatchPending(result, match) &&
                      !isNonMatch(result, match) &&
                      !isSlugPending(result, match)
                    );
                    // When showing only Perfect (100%), hide sub-100% matches inside the card
                    if (confidenceFilter === 'perfect') {
                      nonPendingMatches = nonPendingMatches.filter(m => m.confidence === 100);
                    }
                    const hasNonPendingMatches = nonPendingMatches.length > 0;
                    // Check if there are any pending operations for this result
                    const hasPendingOperations = (result.matches || []).some(match => 
                      isMatchPending(result, match) || isSlugPending(result, match)
                    );
                    // Use stable key based on brand+scent to prevent re-rendering
                    const resultKey = `${result.source_brand}|${result.source_scent || ''}`;
                    
                    return (
                    <div key={`${resultKey}-${index}`} className='border rounded-lg p-4'>
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
                              {/* Show aliases (catalog mode only) */}
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
                              {nonPendingMatches.length} match{nonPendingMatches.length !== 1 ? 'es' : ''}
                              {dataSource === 'match_files' && result.original_texts && result.original_texts.length > 0 && (
                                <span className='ml-2 text-xs'>
                                  • Original: {result.original_texts[0]}
                                  {result.original_texts.length > 1 && ` (+${result.original_texts.length - 1} more)`}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                        {hasNonPendingMatches && (
                          <Badge className={getConfidenceColor(nonPendingMatches[0].confidence)}>
                            {getConfidenceLabel(nonPendingMatches[0].confidence)} (
                            {nonPendingMatches[0].confidence.toFixed(1)}%)
                          </Badge>
                        )}
                      </div>

                      {result.expanded && (
                        <div className='mt-4 space-y-3 pl-8'>
                          <WSDBAlignmentResultExpanded
                            result={result}
                            nonPendingMatches={nonPendingMatches}
                            hasNonPendingMatches={hasNonPendingMatches}
                            hasPendingOperations={hasPendingOperations}
                            analysisMode={viewMode === 'slug_finder' ? 'brand_scent' : analysisMode}
                            direction='pipeline-to-wsdb'
                            getMatchKey={getMatchKey}
                            getConfidenceColor={getConfidenceColor}
                            getConfidenceLabel={getConfidenceLabel}
                            failedItemKeys={failedItemKeys}
                            bulkNoMatchResultKey={bulkNoMatchResultKey}
                            onNoMatchesForResult={handleNoMatchesForResult}
                            onNotAMatch={handleNotAMatch}
                            onAddScentAlias={handleAddScentAlias}
                            dataSource={dataSource}
                            commentIds={result.comment_ids}
                            onCommentClick={handleCommentClick}
                            commentLoading={commentLoading}
                          />
                        </div>
                      )}
                    </div>
                  );
                  })}
                </div>
              ) : (
                <div className='text-center py-8 text-gray-500'>
                  {pipelineResults.length === 0
                    ? `No results yet. Click "${viewMode === 'slug_finder' ? 'Find slug suggestions' : 'Analyze Alignment'}" to start.`
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
                  {filteredWsdbResults
                    .filter(result => {
                      const n = (result.matches || []).filter(
                        m =>
                          !isMatchPending(result, m) &&
                          !isNonMatch(result, m) &&
                          !isSlugPending(result, m)
                      );
                      if (n.length === 0) return false;
                      if (confidenceFilter === 'perfect') {
                        return n.some(m => m.confidence === 100);
                      }
                      return true;
                    })
                    .map((result, index) => {
                    // Filter out pending matches, saved non-matches, and pending slugs for this result
                    let nonPendingMatches = (result.matches || []).filter(match =>
                      !isMatchPending(result, match) &&
                      !isNonMatch(result, match) &&
                      !isSlugPending(result, match)
                    );
                    // When showing only Perfect (100%), hide sub-100% matches inside the card
                    if (confidenceFilter === 'perfect') {
                      nonPendingMatches = nonPendingMatches.filter(m => m.confidence === 100);
                    }
                    const hasNonPendingMatches = nonPendingMatches.length > 0;
                    // Check if there are any pending operations for this result
                    const hasPendingOperations = (result.matches || []).some(match => 
                      isMatchPending(result, match) || isSlugPending(result, match)
                    );
                    // Use stable key based on brand+scent to prevent re-rendering
                    const resultKey = `${result.source_brand}|${result.source_scent || ''}`;
                    
                    return (
                    <div key={`${resultKey}-${index}`} className='border rounded-lg p-4'>
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
                              {nonPendingMatches.length} match{nonPendingMatches.length !== 1 ? 'es' : ''}
                              {dataSource === 'match_files' && result.original_texts && result.original_texts.length > 0 && (
                                <span className='ml-2 text-xs'>
                                  • Original: {result.original_texts[0]}
                                  {result.original_texts.length > 1 && ` (+${result.original_texts.length - 1} more)`}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                        {hasNonPendingMatches && (
                          <Badge className={getConfidenceColor(nonPendingMatches[0].confidence)}>
                            {getConfidenceLabel(nonPendingMatches[0].confidence)} (
                            {nonPendingMatches[0].confidence.toFixed(1)}%)
                          </Badge>
                        )}
                      </div>

                      {result.expanded && (
                        <div className='mt-4 space-y-3 pl-8'>
                          <WSDBAlignmentResultExpanded
                            result={result}
                            nonPendingMatches={nonPendingMatches}
                            hasNonPendingMatches={hasNonPendingMatches}
                            hasPendingOperations={hasPendingOperations}
                            analysisMode={viewMode === 'slug_finder' ? 'brand_scent' : analysisMode}
                            direction='wsdb-to-pipeline'
                            getMatchKey={getMatchKey}
                            getConfidenceColor={getConfidenceColor}
                            getConfidenceLabel={getConfidenceLabel}
                            failedItemKeys={failedItemKeys}
                            bulkNoMatchResultKey={bulkNoMatchResultKey}
                            onNoMatchesForResult={handleNoMatchesForResult}
                            onNotAMatch={handleNotAMatch}
                            onAddScentAlias={handleAddScentAlias}
                            dataSource={dataSource}
                            commentIds={result.comment_ids}
                            onCommentClick={handleCommentClick}
                            commentLoading={commentLoading}
                          />
                        </div>
                      )}
                    </div>
                  );
                  })}
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

