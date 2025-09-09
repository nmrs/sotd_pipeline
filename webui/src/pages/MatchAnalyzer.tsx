import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Filter, Eye, EyeOff } from 'lucide-react';
import MismatchAnalyzerDataTable from '@/components/data/MismatchAnalyzerDataTable';
import {
  analyzeMismatch,
  MismatchAnalysisResult,
  CommentDetail,
  CorrectMatchesResponse,
  getCommentDetail,
  getCorrectMatches,
  markMatchesAsCorrect,
  removeMatchesFromCorrect,
  updateFilteredEntries,
  handleApiError,
  saveBrushSplit,
  loadYamlBrushSplits,
} from '@/services/api';

import LoadingSpinner from '@/components/layout/LoadingSpinner';
import ErrorDisplay from '@/components/feedback/ErrorDisplay';
import MonthSelector from '@/components/forms/MonthSelector';
import CommentModal from '@/components/domain/CommentModal';
import BrushSplitModal from '@/components/forms/BrushSplitModal';
import { BrushSplit } from '@/types/brushSplit';
import { structureBrushDataForAPI } from '@/utils/brushDataUtils';

const MatchAnalyzer: React.FC = () => {
  const [selectedField, setSelectedField] = useState<string>('razor');
  const [selectedMonths, setSelectedMonths] = useState<string[]>([]);
  const [threshold, setThreshold] = useState<number>(3);
  const [useEnrichedData, setUseEnrichedData] = useState<boolean>(false);
  const [displayMode, setDisplayMode] = useState<
    | 'mismatches'
    | 'all'
    | 'unconfirmed'
    | 'regex'
    | 'intentionally_unmatched'
    | 'complete_brushes'
    | 'matches'
  >('mismatches');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<MismatchAnalysisResult | null>(null);
  const [selectedComment, setSelectedComment] = useState<CommentDetail | null>(null);
  const [commentModalOpen, setCommentModalOpen] = useState(false);
  const [commentLoading, setCommentLoading] = useState(false);
  // Multi-comment navigation state
  const [allComments, setAllComments] = useState<CommentDetail[]>([]);
  const [currentCommentIndex, setCurrentCommentIndex] = useState<number>(0);
  const [remainingCommentIds, setRemainingCommentIds] = useState<string[]>([]);

  // Correct matches state
  const [correctMatches, setCorrectMatches] = useState<CorrectMatchesResponse | null>(null);
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  const [markingCorrect, setMarkingCorrect] = useState(false);
  const [removingCorrect, setRemovingCorrect] = useState(false);
  const [visibleRows, setVisibleRows] = useState<MismatchAnalysisResult['mismatch_items']>([]);

  // Reason for marking as unmatched
  const [reasonText, setReasonText] = useState<string>('');
  const [updatingFiltered, setUpdatingFiltered] = useState(false);

  // Brush split modal state
  const [brushSplitModalOpen, setBrushSplitModalOpen] = useState(false);
  const [selectedBrushItem, setSelectedBrushItem] = useState<
    MismatchAnalysisResult['mismatch_items'][0] | null
  >(null);
  const [existingBrushSplit, setExistingBrushSplit] = useState<BrushSplit | undefined>(undefined);
  const [savingBrushSplit, setSavingBrushSplit] = useState(false);

  // YAML brush splits state for lookup
  const [yamlBrushSplits, setYamlBrushSplits] = useState<BrushSplit[]>([]);

  // Keyboard navigation state
  const [activeRowIndex, setActiveRowIndex] = useState<number>(-1);
  const [keyboardNavigationEnabled, setKeyboardNavigationEnabled] = useState<boolean>(false);

  // Clear selections on component mount to ensure clean state
  useEffect(() => {
    setSelectedItems(new Set());
  }, []);

  const loadCorrectMatches = useCallback(async () => {
    try {
      const data = await getCorrectMatches(selectedField);
      console.log('🔍 DEBUG: loadCorrectMatches loaded data:', {
        field: selectedField,
        totalEntries: data.total_entries,
        hasData: !!data,
        dataKeys: data ? Object.keys(data) : [],
      });
      setCorrectMatches(data);
    } catch (err: unknown) {
      console.warn('Failed to load correct matches:', err);
      // Don't show error to user, just log it
    }
  }, [selectedField]);

  const loadYamlBrushSplitsData = useCallback(async () => {
    try {
      const data = await loadYamlBrushSplits();
      setYamlBrushSplits(data.brush_splits);
    } catch (err: unknown) {
      console.warn('Failed to load YAML brush splits:', err);
      // Don't show error to user, just log it
    }
  }, []);

  // Load correct matches when field changes
  useEffect(() => {
    if (selectedField) {
      loadCorrectMatches();
      // Clear selections when field changes to avoid key format mismatches
      setSelectedItems(new Set());
    }
  }, [selectedField, loadCorrectMatches]);

  // Load YAML brush splits on component mount
  useEffect(() => {
    loadYamlBrushSplitsData();
  }, [loadYamlBrushSplitsData]);

  const handleAnalyze = async () => {
    if (selectedMonths.length === 0) {
      setError('Please select at least one month to analyze');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setResults(null);
      setSelectedItems(new Set()); // Clear selections

      const result = await analyzeMismatch({
        field: selectedField,
        months: selectedMonths, // Pass full months array instead of just first month
        threshold,
        use_enriched_data: useEnrichedData,
        display_mode: displayMode,
      });

      // console.log('🔍 DEBUG: handleAnalyze returned result:', {
      //   field: result.field,
      //   totalItems: result.mismatch_items?.length || 0,
      //   hasData: !!result.mismatch_items,
      //   sampleItems: result.mismatch_items?.slice(0, 3).map(item => ({
      //     original: item.original,
      //     match_type: item.match_type,
      //     mismatch_type: item.mismatch_type,
      //     is_confirmed: item.is_confirmed,
      //   })) || [],
      // });

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
      const comment = await getCommentDetail(commentId, selectedMonths);
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
          const nextComment = await getCommentDetail(nextCommentId, selectedMonths);

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

  // Brush split handlers
  const handleBrushSplitClick = (item: MismatchAnalysisResult['mismatch_items'][0]) => {
    setSelectedBrushItem(item);

    // Convert comment_ids to proper occurrence format using comment_sources
    const occurrences: Array<{ file: string; comment_ids: string[] }> = [];

    if (item.comment_ids && item.comment_ids.length > 0) {
      if (item.comment_sources) {
        // Group comment_ids by source file
        const fileGroups: Record<string, string[]> = {};
        for (const commentId of item.comment_ids) {
          const sourceFile = item.comment_sources[commentId];
          if (sourceFile) {
            if (!fileGroups[sourceFile]) {
              fileGroups[sourceFile] = [];
            }
            fileGroups[sourceFile].push(commentId);
          } else {
            // Fallback to current month if no source file mapping
            const fallbackFile = `${selectedMonths[0]}.json`;
            if (!fileGroups[fallbackFile]) {
              fileGroups[fallbackFile] = [];
            }
            fileGroups[fallbackFile].push(commentId);
          }
        }

        // Convert to occurrences format
        for (const [file, commentIds] of Object.entries(fileGroups)) {
          occurrences.push({ file, comment_ids: commentIds });
        }
      } else {
        // Fallback: use current month for all comment_ids
        occurrences.push({
          file: `${selectedMonths[0]}.json`,
          comment_ids: item.comment_ids,
        });
      }
    }

    // Look up existing split from YAML data
    const existingYamlSplit = yamlBrushSplits.find(split => split.original === item.original);

    // Create existing split data if available
    let existingSplit: BrushSplit | undefined = undefined;

    if (existingYamlSplit) {
      // Use existing YAML split data
      existingSplit = {
        ...existingYamlSplit,
        occurrences: occurrences, // Use current occurrences
      };
    } else if (
      (item as any).is_split_brush &&
      ((item as any).handle_component || (item as any).knot_component)
    ) {
      // Use split data from the item itself
      existingSplit = {
        original: item.original,
        handle: (item as any).handle_component || null,
        knot: (item as any).knot_component || null,
        corrected: false,
        validated_at: null,
        should_not_split: false,
        occurrences: occurrences,
      };
    } else {
      // For new splits, create a template with occurrences
      existingSplit = {
        original: item.original,
        handle: null,
        knot: null,
        corrected: false,
        validated_at: null,
        should_not_split: false,
        occurrences: occurrences,
      };
    }
    setExistingBrushSplit(existingSplit);
    setBrushSplitModalOpen(true);
  };

  const handleBrushSplitClose = () => {
    setBrushSplitModalOpen(false);
    setSelectedBrushItem(null);
    setExistingBrushSplit(undefined);
  };

  const handleBrushSplitSave = async (split: BrushSplit) => {
    if (!selectedBrushItem) return;

    try {
      setSavingBrushSplit(true);

      // Call the API to save the brush split
      const response = await saveBrushSplit({
        original: split.original,
        handle: split.handle,
        knot: split.knot || split.original, // Use original as knot if knot is null
        should_not_split: split.should_not_split,
        occurrences: split.occurrences,
      });

      if (response.success) {
        // Close modal after successful save
        handleBrushSplitClose();

        // Refresh YAML brush splits data
        await loadYamlBrushSplitsData();

        // Re-run analysis to get updated data
        if (selectedMonths.length > 0) {
          await handleAnalyze();
        }
      } else {
        setError(`Failed to save brush split: ${response.message}`);
      }
    } catch (error) {
      console.error('Failed to save brush split:', error);
      setError(handleApiError(error));
    } finally {
      setSavingBrushSplit(false);
    }
  };

  const handleMonthChange = (months: string[]) => {
    setSelectedMonths(months);
  };

  const handleItemSelection = useCallback((itemKey: string, selected: boolean) => {
    setSelectedItems(prevSelected => {
      const newSelected = new Set(prevSelected);
      if (selected) {
        newSelected.add(itemKey);
      } else {
        newSelected.delete(itemKey);
      }
      return newSelected;
    });
  }, []);

  const handleSelectAll = useCallback(() => {
    if (!visibleRows.length) return;

    const allKeys = visibleRows.map(item => {
      // Since backend groups by case-insensitive original text, use that as the key
      return `${selectedField}:${item.original.toLowerCase()}`;
    });
    setSelectedItems(new Set(allKeys));
  }, [visibleRows, selectedField]);

  const handleClearSelection = useCallback(() => {
    setSelectedItems(new Set());
  }, []);

  const handleVisibleRowsChange = useCallback((rows: MismatchAnalysisResult['mismatch_items']) => {
    setVisibleRows(rows);
    // Reset active row index when visible rows change
    setActiveRowIndex(-1);
  }, []);

  // Memoize item keys to avoid repeated operations
  const visibleItemKeys = useMemo(() => {
    return visibleRows.map(item => {
      // Since backend groups by case-insensitive original text, use that as the key
      return `${selectedField}:${item.original.toLowerCase()}`;
    });
  }, [visibleRows, selectedField]);

  // Count selected items that are currently visible on the page
  const visibleSelectedCount = useMemo(() => {
    if (!visibleRows.length) return 0;

    return visibleItemKeys.filter(key => selectedItems.has(key)).length;
  }, [visibleItemKeys, selectedItems]);

  const handleMarkAsCorrect = async () => {
    if (selectedItems.size === 0) {
      setError('Please select items to mark as correct');
      return;
    }

    if (!results?.mismatch_items) return;

    try {
      setMarkingCorrect(true);

      // Send the complete match data directly
      const matches = results.mismatch_items
        .filter(item => {
          const itemKey = `${selectedField}:${item.original.toLowerCase()}`;
          return selectedItems.has(itemKey);
        })
        .map(item => {
          // For brush field, use the shared utility to structure data correctly
          if (selectedField === 'brush' && item.matched) {
            const { data } = structureBrushDataForAPI(item.matched, item.original);
            return {
              original: item.original,
              matched: data,
            };
          }

          // For blade field, include razor format context for correct section placement
          if (selectedField === 'blade' && item.matched) {
            // Ensure the format field is present for correct section placement in correct_matches.yaml
            // The backend expects a 'format' field to determine which section to place the entry in
            const bladeData = {
              ...item.matched,
              // Use existing format field, but warn if it's missing
              format:
                item.matched.format ||
                (() => {
                  console.warn(
                    `Blade match missing format field for "${item.original}". This may cause incorrect placement in correct_matches.yaml.`
                  );
                  // Try to infer format from other fields or use a more specific default
                  if (item.matched.brand && item.matched.model) {
                    // Check if we can infer the format from the brand/model combination
                    console.warn(
                      `Attempting to infer format from brand: ${item.matched.brand}, model: ${item.matched.model}`
                    );
                  }
                  // For now, use 'DE' as fallback, but this should be fixed in the backend
                  return 'DE';
                })(),
            };

            // Debug logging for blade format handling
            console.log('Blade match data:', {
              original: item.original,
              originalMatched: item.matched,
              processedMatched: bladeData,
              format: bladeData.format,
              hasFormatField: 'format' in item.matched,
              formatFieldValue: item.matched.format,
            });

            return {
              original: item.original,
              matched: bladeData,
            };
          }

          // For non-brush fields, return as-is
          return {
            original: item.original,
            matched: item.matched,
          };
        });

      const response = await markMatchesAsCorrect({
        field: selectedField,
        matches,
        force: true,
      });

      if (response.success) {
        // Reload correct matches and re-analyze to get fresh data
        await loadCorrectMatches();
        setSelectedItems(new Set());
        setError(null);

        // Re-run analysis to get updated mismatch data
        if (selectedMonths.length > 0) {
          await handleAnalyze();
        }
      } else {
        setError(`Failed to mark items as correct: ${response.message}`);
      }
    } catch (err: unknown) {
      setError(handleApiError(err));
    } finally {
      setMarkingCorrect(false);
    }
  };

  const handleRemoveFromCorrect = async () => {
    if (selectedItems.size === 0) {
      setError('Please select items to remove from correct matches');
      return;
    }

    if (!results?.mismatch_items) return;

    try {
      setRemovingCorrect(true);

      // Send the complete match data directly
      const matches = results.mismatch_items
        .filter(item => {
          const itemKey = `${selectedField}:${item.original.toLowerCase()}`;
          return selectedItems.has(itemKey);
        })
        .map(item => {
          // For brush field, use the shared utility to structure data correctly
          if (selectedField === 'brush' && item.matched) {
            const { data } = structureBrushDataForAPI(item.matched, item.original);
            return {
              original: item.original,
              matched: data,
            };
          }

          // For blade field, include razor format context for correct section placement
          if (selectedField === 'blade' && item.matched) {
            // Ensure the format field is present for correct section placement in correct_matches.yaml
            // The backend expects a 'format' field to determine which section to place the entry in
            const bladeData = {
              ...item.matched,
              // Use existing format field, but warn if it's missing
              format:
                item.matched.format ||
                (() => {
                  console.warn(
                    `Blade match missing format field for "${item.original}" (remove). This may cause incorrect placement in correct_matches.yaml.`
                  );
                  // Try to infer format from other fields or use a more specific default
                  if (item.matched.brand && item.matched.model) {
                    // Check if we can infer the format from the brand/model combination
                    console.warn(
                      `Attempting to infer format from brand: ${item.matched.brand}, model: ${item.matched.model}`
                    );
                  }
                  // For now, use 'DE' as fallback, but this should be fixed in the backend
                  return 'DE';
                })(),
            };

            // Debug logging for blade format handling
            console.log('Blade match data (remove):', {
              original: item.original,
              originalMatched: item.matched,
              processedMatched: bladeData,
              format: bladeData.format,
              hasFormatField: 'format' in item.matched,
              formatFieldValue: item.matched.format,
            });

            return {
              original: item.original,
              matched: bladeData,
            };
          }

          // For non-brush fields, return as-is
          return {
            original: item.original,
            matched: item.matched,
          };
        });

      const response = await removeMatchesFromCorrect({
        field: selectedField,
        matches,
        force: true,
      });

      if (response.success) {
        // Reload correct matches and re-analyze to get fresh data
        await loadCorrectMatches();
        setSelectedItems(new Set());
        setError(null);

        // Re-run analysis to get updated mismatch data
        if (selectedMonths.length > 0) {
          await handleAnalyze();
        }
      } else {
        setError(`Failed to remove items from correct matches: ${response.message}`);
      }
    } catch (err: unknown) {
      setError(handleApiError(err));
    } finally {
      setRemovingCorrect(false);
    }
  };

  const handleMarkAsIntentionallyUnmatched = async () => {
    if (selectedItems.size === 0) {
      setError('Please select items to mark as intentionally unmatched');
      return;
    }

    try {
      setUpdatingFiltered(true);

      // Convert selected items to filtered entries format
      const allEntries: Array<{
        name: string;
        action: 'add' | 'remove';
        comment_id: string;
        source: string;
        month: string;
      }> = [];

      if (!results?.mismatch_items) return;

      results.mismatch_items
        .filter(item => {
          const itemKey = `${selectedField}:${item.original.toLowerCase()}`;
          return selectedItems.has(itemKey);
        })
        .forEach(item => {
          if (item.comment_ids && item.comment_ids.length > 0) {
            // Use the first comment_id as representative
            const firstCommentId = item.comment_ids[0];
            if (firstCommentId) {
              // Determine action based on current mismatch_type
              const action = item.mismatch_type === 'intentionally_unmatched' ? 'remove' : 'add';

              allEntries.push({
                name: item.original,
                action,
                comment_id: firstCommentId,
                source: 'user',
                month: selectedMonths[0], // Use first month for backward compatibility
              });
            }
          }
        });

      if (allEntries.length === 0) {
        setError('No valid entries to update');
        return;
      }

      const response = await updateFilteredEntries({
        category: selectedField,
        entries: allEntries,
        reason: reasonText.trim() || undefined,
      });

      if (response.success) {
        // Clear selections and reason
        setSelectedItems(new Set());
        setReasonText('');
        setError(null);

        // Re-run analysis to get updated data
        if (selectedMonths.length > 0) {
          await handleAnalyze();
        }
      } else {
        setError(`Failed to update filtered entries: ${response.message}`);
      }
    } catch (err: unknown) {
      setError(handleApiError(err));
    } finally {
      setUpdatingFiltered(false);
    }
  };

  const handleMarkAsIncorrect = async () => {
    if (selectedItems.size === 0) {
      setError('Please select items to mark as incorrect');
      return;
    }

    if (!results?.mismatch_items) return;

    try {
      // Send the complete match data directly
      const matches = results.mismatch_items
        .filter(item => {
          const itemKey = `${selectedField}:${item.original.toLowerCase()}`;
          return selectedItems.has(itemKey);
        })
        .map(item => {
          // For brush field, use the shared utility to structure data correctly
          if (selectedField === 'brush' && item.matched) {
            const { data } = structureBrushDataForAPI(item.matched, item.original);
            return {
              original: item.original,
              matched: data,
            };
          }

          // For blade field, include razor format context for correct section placement
          if (selectedField === 'blade' && item.matched) {
            // Ensure the format field is present for correct section placement in correct_matches.yaml
            // The backend expects a 'format' field to determine which section to place the entry in
            const bladeData = {
              ...item.matched,
              // Use existing format field, but warn if it's missing
              format:
                item.matched.format ||
                (() => {
                  console.warn(
                    `Blade match missing format field for "${item.original}" (incorrect). This may cause incorrect placement in correct_matches.yaml.`
                  );
                  // Try to infer format from other fields or use a more specific default
                  if (item.matched.brand && item.matched.model) {
                    // Check if we can infer the format from the brand/model combination
                    console.warn(
                      `Attempting to infer format from brand: ${item.matched.brand}, model: ${item.matched.model}`
                    );
                  }
                  // For now, use 'DE' as fallback, but this should be fixed in the backend
                  return 'DE';
                })(),
            };

            // Debug logging for blade format handling
            console.log('Blade match data (incorrect):', {
              original: item.original,
              originalMatched: item.matched,
              processedMatched: bladeData,
              format: bladeData.format,
              hasFormatField: 'format' in item.matched,
              formatFieldValue: item.matched.format,
            });

            return {
              original: item.original,
              matched: bladeData,
            };
          }

          // For non-brush fields, return as-is
          return {
            original: item.original,
            matched: item.matched,
          };
        });

      const response = await removeMatchesFromCorrect({
        field: selectedField,
        matches,
        force: true,
      });

      if (response.success) {
        // Reload correct matches and re-analyze to get fresh data
        await loadCorrectMatches();
        setSelectedItems(new Set());
        setError(null);

        // Re-run analysis to get updated mismatch data
        if (selectedMonths.length > 0) {
          await handleAnalyze();
        }
      } else {
        setError(`Failed to mark items as incorrect: ${response.message}`);
      }
    } catch (err: unknown) {
      setError(handleApiError(err));
    }
  };

  const isItemConfirmed = useCallback((item: MismatchAnalysisResult['mismatch_items'][0]) => {
    // Use the is_confirmed field from the backend
    return item.is_confirmed || false;
  }, []);

  // Memoized filtered results for performance
  const filteredResults = useMemo(() => {
    if (!results?.mismatch_items) return [];

    switch (displayMode) {
      case 'mismatches':
        // Show only potential mismatches (default behavior)
        return results.mismatch_items.filter(
          item =>
            item.mismatch_type &&
            item.mismatch_type !== 'good_match' &&
            item.mismatch_type !== 'exact_matches' &&
            item.mismatch_type !== 'intentionally_unmatched' &&
            !isItemConfirmed(item)
        );

      case 'all':
        // Show all matches (both good and problematic)
        return results.mismatch_items;

      case 'unconfirmed':
        // Show only unconfirmed matches (not exact or previously confirmed)
        return results.mismatch_items.filter(item => !isItemConfirmed(item));

      case 'regex':
        // Show only regex matches that need confirmation
        return results.mismatch_items.filter(
          item => item.match_type === 'regex' && !isItemConfirmed(item)
        );

      case 'intentionally_unmatched':
        // Show only intentionally unmatched items
        return results.mismatch_items.filter(
          item => item.mismatch_type === 'intentionally_unmatched'
        );

      case 'complete_brushes':
        // Show only complete brush items (when field is brush)
        return results.mismatch_items.filter(item => (item as any).is_complete_brush === true);

      case 'matches':
        // Show only confirmed matches (exact and manually confirmed)
        return results.mismatch_items.filter(item => isItemConfirmed(item));

      default:
        return results.mismatch_items;
    }
  }, [results?.mismatch_items, displayMode, isItemConfirmed]);

  // Keyboard navigation handlers

  // Container ref for keyboard navigation
  const containerRef = useRef<HTMLDivElement>(null);

  // Enable keyboard navigation when component mounts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Don't handle keyboard navigation if focus is on an input field
      const activeElement = document.activeElement;

      if (activeElement) {
        const tagName = activeElement.tagName.toLowerCase();
        const isInput = tagName === 'input' || tagName === 'textarea' || tagName === 'select';
        const isContentEditable = activeElement.getAttribute('contenteditable') === 'true';

        if (isInput || isContentEditable) {
          // If we're in an input field, let it handle all events including space bar
          return; // Let the input field handle all events
        }
      }

      // Only handle keyboard navigation if enabled
      if (!keyboardNavigationEnabled) {
        return;
      }

      switch (event.key) {
        case 'ArrowUp':
          event.preventDefault();
          if (activeRowIndex > 0) {
            setActiveRowIndex(activeRowIndex - 1);
          } else if (visibleRows.length > 0) {
            setActiveRowIndex(0);
          }
          break;
        case 'ArrowDown':
          event.preventDefault();
          if (activeRowIndex >= 0 && activeRowIndex < visibleRows.length - 1) {
            setActiveRowIndex(activeRowIndex + 1);
          } else if (visibleRows.length > 0 && activeRowIndex === -1) {
            setActiveRowIndex(0);
          }
          break;
        case ' ':
          event.preventDefault();
          if (activeRowIndex >= 0 && activeRowIndex < visibleRows.length) {
            const item = visibleRows[activeRowIndex];
            const itemKey = `${selectedField}:${item.original.toLowerCase()}`;
            const isCurrentlySelected = selectedItems.has(itemKey);
            handleItemSelection(itemKey, !isCurrentlySelected);
          }
          break;
        case 'Escape':
          setActiveRowIndex(-1);
          setKeyboardNavigationEnabled(false);
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [
    keyboardNavigationEnabled,
    activeRowIndex,
    visibleRows,
    selectedField,
    selectedItems,
    handleItemSelection,
  ]);

  // Reset active row when data changes
  useEffect(() => {
    setActiveRowIndex(-1);
  }, [filteredResults]);

  // Enable keyboard navigation when results are available
  useEffect(() => {
    if (results && filteredResults.length > 0) {
      setKeyboardNavigationEnabled(true);
    } else {
      setKeyboardNavigationEnabled(false);
    }
  }, [results, filteredResults.length]);

  const getDisplayModeCounts = () => {
    if (!results)
      return {
        mismatches: 0,
        all: 0,
        unconfirmed: 0,
        regex: 0,
        intentionally_unmatched: 0,
        matches: 0,
        complete_brushes: 0,
      };

    // We always have the full dataset now, so calculate from the returned items
    const returnedItems = results.mismatch_items || [];

    // Debug logging to understand the data structure
    // console.log('Debug: Analyzing data for counts:', {
    //   totalItems: returnedItems.length,
    //   field: results.field,
    //   months: results.months,
    //   sampleItems: returnedItems.slice(0, 3).map(item => ({
    //     original: item.original,
    //     match_type: item.match_type,
    //     mismatch_type: item.mismatch_type,
    //     is_confirmed: item.is_confirmed,
    //     pattern: item.pattern,
    //   })),
    // });

    // Count regex matches specifically
    const regexMatches = returnedItems.filter(item => item.match_type === 'regex');
    const unconfirmedRegexMatches = returnedItems.filter(
      item => item.match_type === 'regex' && !isItemConfirmed(item)
    );

    // console.log('Debug: Regex analysis:', {
    //   totalRegexMatches: regexMatches.length,
    //   unconfirmedRegexMatches: unconfirmedRegexMatches.length,
    //   regexMatchTypes: regexMatches.map(item => ({
    //     original: item.original,
    //     match_type: item.match_type,
    //     is_confirmed: item.is_confirmed,
    //     pattern: item.pattern,
    //   })),
    // });

    // Calculate all counts with detailed logging
    const mismatchesCount = returnedItems.filter(
      item =>
        item.mismatch_type !== 'good_match' &&
        item.mismatch_type !== 'exact_matches' &&
        item.mismatch_type !== 'intentionally_unmatched' &&
        !isItemConfirmed(item)
    ).length;

    const unconfirmedCount = returnedItems.filter(item => !isItemConfirmed(item)).length;
    const intentionallyUnmatchedCount = returnedItems.filter(
      item => item.mismatch_type === 'intentionally_unmatched'
    ).length;
    const matchesCount = returnedItems.filter(item => isItemConfirmed(item)).length;
    const completeBrushesCount = returnedItems.filter(item => (item as any).is_complete_brush === true)
      .length;

    // Debug logging for count calculations
    // console.log('🔍 DEBUG: Display mode count calculations:', {
    //   totalItems: returnedItems.length,
    //   field: results.field,
    //   months: results.months,
    //   calculatedCounts: {
    //     mismatches: mismatchesCount,
    //     all: returnedItems.length,
    //     unconfirmed: unconfirmedCount,
    //     regex: unconfirmedRegexMatches.length,
    //     intentionally_unmatched: intentionallyUnmatchedCount,
    //     matches: matchesCount,
    //     complete_brushes: completeBrushesCount,
    //   },
    //   mismatchTypeBreakdown: returnedItems.reduce((acc, item) => {
    //     acc[item.mismatch_type || 'unknown'] = (acc[item.mismatch_type || 'unknown'] || 0) + 1;
    //     return acc;
    //   }, {} as Record<string, number>),
    //   confirmedBreakdown: {
    //     confirmed: returnedItems.filter(item => item.is_confirmed).length,
    //     unconfirmed: returnedItems.filter(item => !item.is_confirmed).length,
    //   }
    // });

    return {
      mismatches: mismatchesCount,
      all: returnedItems.length, // Use actual returned items count instead of totalMatches
      unconfirmed: unconfirmedCount,
      regex: unconfirmedRegexMatches.length,
      intentionally_unmatched: intentionallyUnmatchedCount,
      matches: matchesCount,
      complete_brushes: completeBrushesCount,
    };
  };

  const getUnmatchedButtonText = useMemo(() => {
    if (visibleSelectedCount === 0) return 'Mark 0 as Unmatched';

    // Count how many visible selected items are already intentionally unmatched
    let addCount = 0;
    let removeCount = 0;

    if (visibleRows.length > 0) {
      visibleRows.forEach((item, index) => {
        const itemKey = visibleItemKeys[index];
        if (selectedItems.has(itemKey)) {
          if (item.mismatch_type === 'intentionally_unmatched') {
            removeCount++;
          } else {
            addCount++;
          }
        }
      });
    }

    if (addCount > 0 && removeCount > 0) {
      return `Add ${addCount}, Remove ${removeCount} from Unmatched`;
    } else if (removeCount > 0) {
      return `Remove ${removeCount} from Unmatched`;
    } else {
      return `Mark ${addCount} as Unmatched`;
    }
  }, [visibleSelectedCount, visibleRows, visibleItemKeys, selectedItems]);

  const shouldShowReasonInput = useMemo(() => {
    if (selectedItems.size === 0) return false;

    // Only show reason input if we're adding items (not removing)
    let hasAddItems = false;

    if (results?.mismatch_items) {
      results.mismatch_items
        .filter((item, index) => {
          const itemKey = `${selectedField}:${index}`;
          return selectedItems.has(itemKey);
        })
        .forEach(item => {
          if (item.mismatch_type !== 'intentionally_unmatched') {
            hasAddItems = true;
          }
        });
    }

    return hasAddItems;
  }, [selectedItems, results?.mismatch_items]);

  return (
    <div ref={containerRef} className='w-full p-4 max-w-full overflow-x-hidden'>
      {/* Controls and Header */}
      <div className='mb-4'>
        <h1 className='text-3xl font-bold text-gray-900 mb-2'>Match Analyzer</h1>
        <p className='text-gray-600 mb-4'>
          Analyze and manage all matches to identify potential catalog conflicts, view confirmed
          entries, and maintain data quality.
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
                onClick={handleRemoveFromCorrect}
                disabled={selectedItems.size === 0 || removingCorrect}
                className='px-3 py-1 text-sm bg-orange-600 text-white rounded hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-orange-500 disabled:opacity-50 disabled:cursor-not-allowed'
              >
                {removingCorrect ? 'Removing...' : `Clear ${visibleSelectedCount} Entry`}
              </button>
            </div>
          </div>
        )}

        {/* Enriched Data Info Panel */}
        {useEnrichedData && (
          <div className='bg-green-50 border border-green-200 rounded-lg p-4 mb-4'>
            <div className='flex items-start'>
              <div className='flex-shrink-0'>
                <svg className='h-5 w-5 text-green-400' fill='currentColor' viewBox='0 0 20 20'>
                  <path
                    fillRule='evenodd'
                    d='M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z'
                    clipRule='evenodd'
                  />
                </svg>
              </div>
              <div className='ml-3'>
                <h3 className='text-sm font-medium text-green-800'>Enriched Data Mode Active</h3>
                <div className='mt-2 text-sm text-green-700'>
                  <p className='mb-2'>
                    You are viewing data from the <strong>enrich phase</strong>, which shows the
                    final results after all refinements have been applied.
                  </p>
                  <p className='mb-2'>
                    <strong>What this means:</strong> Some items that appear as "mismatches" in the
                    match phase are actually correct matches that get refined during the enrich
                    phase. Hover over the "Matched" column to see enrich-phase adjustments.
                  </p>
                  <p>
                    <strong>Tip:</strong> This mode helps distinguish between truly problematic
                    matches and expected enrich-phase corrections.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Controls Section - Made responsive */}
        <div className='space-y-4 mb-4'>
          {/* First row - Basic controls */}
          <div className='flex flex-wrap gap-4 items-end'>
            <div className='min-w-0 flex-1 sm:flex-none'>
              <label
                htmlFor='field-select'
                className='block text-sm font-medium text-gray-700 mb-1'
              >
                Field
              </label>
              <select
                id='field-select'
                value={selectedField}
                onChange={e => setSelectedField(e.target.value)}
                className='w-full sm:w-auto px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
              >
                <option value='razor'>Razor</option>
                <option value='blade'>Blade</option>
                <option value='brush'>Brush</option>
                <option value='soap'>Soap</option>
              </select>
            </div>
            <div className='min-w-0 flex-1 sm:flex-none'>
              <label
                htmlFor='month-selector'
                className='block text-sm font-medium text-gray-700 mb-1'
              >
                Month
              </label>
              <MonthSelector
                selectedMonths={selectedMonths}
                onMonthsChange={handleMonthChange}
                label='Select Month'
                multiple={true}
              />
            </div>
            <div className='min-w-0 flex-1 sm:flex-none'>
              <label
                htmlFor='levenshtein-threshold'
                className='block text-sm font-medium text-gray-700 mb-1'
              >
                Levenshtein Threshold
              </label>
              <input
                id='levenshtein-threshold'
                type='number'
                min='0'
                max='10'
                value={threshold}
                onChange={e => setThreshold(Number(e.target.value))}
                className='w-full sm:w-24 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
              />
            </div>
            <div className='min-w-0 flex-1 sm:flex-none'>
              <div className='flex items-center gap-2'>
                <input
                  type='checkbox'
                  id='useEnrichedData'
                  checked={useEnrichedData}
                  onChange={e => setUseEnrichedData(e.target.checked)}
                  className='h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
                />
                <label htmlFor='useEnrichedData' className='text-sm text-gray-700'>
                  Use Enriched Data
                </label>
                <div className='relative group'>
                  <button
                    type='button'
                    className='ml-1 text-gray-400 hover:text-gray-600 focus:outline-none focus:text-gray-600'
                    title='Learn about Match vs Enrich phases'
                  >
                    <svg className='h-4 w-4' fill='currentColor' viewBox='0 0 20 20'>
                      <path
                        fillRule='evenodd'
                        d='M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z'
                        clipRule='evenodd'
                      />
                    </svg>
                  </button>
                  <div className='absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-10 shadow-sm max-w-xs'>
                    <div className='font-medium mb-1'>Match vs Enrich Phases:</div>
                    <div className='space-y-1'>
                      <div>
                        <strong>Match Phase:</strong> Initial product identification
                      </div>
                      <div>
                        <strong>Enrich Phase:</strong> Refines matches with additional data
                      </div>
                      <div className='text-gray-600'>
                        Some "mismatches" are actually correct enrich-phase adjustments
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className='min-w-0 flex-1 sm:flex-none'>
              <button
                onClick={handleAnalyze}
                disabled={loading || selectedMonths.length === 0}
                className='w-full sm:w-auto bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed h-10'
              >
                {loading ? 'Analyzing...' : 'Analyze'}
              </button>
            </div>
          </div>

          {/* Second row - Display Mode buttons */}
          <div className='min-w-0'>
            <label className='block text-sm font-medium text-gray-700 mb-2'>Display Mode</label>
            <div className='flex flex-wrap gap-2'>
              <Button
                variant='outline'
                onClick={() => setDisplayMode('all')}
                className={`flex items-center gap-1 text-sm relative group ${displayMode === 'all' ? 'bg-blue-600 text-white' : ''}`}
                title='Show all matches with mismatch indicators'
              >
                <Eye className='h-4 w-4' />
                All
                <span
                  className={`ml-1 px-1.5 py-0.5 text-xs rounded-full ${displayMode === 'all' ? 'bg-white text-blue-600' : 'bg-gray-100 text-gray-700'
                    }`}
                >
                  {getDisplayModeCounts().all}
                </span>
                <span className='absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-10 shadow-sm'>
                  Show all matches (both good and problematic)
                </span>
              </Button>
              <Button
                variant='outline'
                onClick={() => setDisplayMode('mismatches')}
                className={`flex items-center gap-1 text-sm relative group ${displayMode === 'mismatches' ? 'bg-blue-600 text-white' : ''}`}
                title='Show only potential mismatches that need review'
              >
                <EyeOff className='h-4 w-4' />
                Mismatches
                <span
                  className={`ml-1 px-1.5 py-0.5 text-xs rounded-full ${displayMode === 'mismatches'
                    ? 'bg-white text-blue-600'
                    : 'bg-gray-100 text-gray-700'
                    }`}
                >
                  {getDisplayModeCounts().mismatches}
                </span>
                <span className='absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-10 shadow-sm'>
                  Show only problematic matches that need review
                </span>
              </Button>
              <Button
                variant='outline'
                onClick={() => setDisplayMode('unconfirmed')}
                className={`flex items-center gap-1 text-sm relative group ${displayMode === 'unconfirmed' ? 'bg-blue-600 text-white' : ''}`}
                title='Show only unconfirmed matches (not exact or previously confirmed)'
              >
                <Filter className='h-4 w-4' />
                Unconfirmed
                <span
                  className={`ml-1 px-1.5 py-0.5 text-xs rounded-full ${displayMode === 'unconfirmed'
                    ? 'bg-white text-blue-600'
                    : 'bg-gray-100 text-gray-700'
                    }`}
                >
                  {getDisplayModeCounts().unconfirmed}
                </span>
                <span className='absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-10 shadow-sm'>
                  Show only unconfirmed matches (not exact or previously confirmed)
                </span>
              </Button>
              <Button
                variant='outline'
                onClick={() => setDisplayMode('regex')}
                className={`flex items-center gap-1 text-sm relative group ${displayMode === 'regex' ? 'bg-blue-600 text-white' : ''}`}
                title='Show only regex matches that need confirmation'
              >
                <Filter className='h-4 w-4' />
                Regex
                <span
                  className={`ml-1 px-1.5 py-0.5 text-xs rounded-full ${displayMode === 'regex' ? 'bg-white text-blue-600' : 'bg-gray-100 text-gray-700'
                    }`}
                >
                  {getDisplayModeCounts().regex}
                </span>
                <span className='absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-10 shadow-sm'>
                  Show only regex matches that need confirmation
                </span>
              </Button>
              <Button
                variant='outline'
                onClick={() => setDisplayMode('intentionally_unmatched')}
                className={`flex items-center gap-1 text-sm relative group ${displayMode === 'intentionally_unmatched' ? 'bg-blue-600 text-white' : ''}`}
                title='Show only intentionally unmatched items'
              >
                <Filter className='h-4 w-4' />
                Intentionally Unmatched
                <span
                  className={`ml-1 px-1.5 py-0.5 text-xs rounded-full ${displayMode === 'intentionally_unmatched'
                    ? 'bg-white text-blue-600'
                    : 'bg-gray-100 text-gray-700'
                    }`}
                >
                  {getDisplayModeCounts().intentionally_unmatched}
                </span>
                <span className='absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-10 shadow-sm'>
                  Show only intentionally unmatched items
                </span>
              </Button>
              {/* Matches filter - show confirmed entries */}
              <Button
                variant='outline'
                onClick={() => setDisplayMode('matches')}
                className={`flex items-center gap-1 text-sm relative group ${displayMode === 'matches' ? 'bg-blue-600 text-white' : ''}`}
                title='Show only confirmed matches (exact and manually confirmed)'
              >
                <Filter className='h-4 w-4' />
                Matches
                <span
                  className={`ml-1 px-1.5 py-0.5 text-xs rounded-full ${displayMode === 'matches'
                    ? 'bg-white text-blue-600'
                    : 'bg-gray-100 text-gray-700'
                    }`}
                >
                  {getDisplayModeCounts().matches}
                </span>
                <span className='absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-10 shadow-sm'>
                  Show only confirmed matches (exact and manually confirmed)
                </span>
              </Button>
              {/* Complete Brushes filter - only show when field is brush */}
              {selectedField === 'brush' && (
                <Button
                  variant='outline'
                  onClick={() => setDisplayMode('complete_brushes')}
                  className={`flex items-center gap-1 text-sm relative group ${displayMode === 'complete_brushes' ? 'bg-blue-600 text-white' : ''}`}
                  title='Show only complete brush items (single products)'
                >
                  <Filter className='h-4 w-4' />
                  Complete Brushes
                  <span
                    className={`ml-1 px-1.5 py-0.5 text-xs rounded-full ${displayMode === 'complete_brushes'
                      ? 'bg-white text-blue-600'
                      : 'bg-gray-100 text-gray-700'
                      }`}
                  >
                    {getDisplayModeCounts().complete_brushes}
                  </span>
                  <span className='absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 text-xs text-gray-700 bg-gray-50 border border-gray-200 rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-10 shadow-sm'>
                    Show only complete brush items (single products)
                  </span>
                </Button>
              )}
            </div>
          </div>
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
              <div className='min-w-0 flex-1'>
                <h3 className='text-lg font-medium text-gray-900'>Analysis Results</h3>
                <div className='mt-2 text-sm text-gray-600 flex flex-wrap gap-4'>
                  <span className='whitespace-nowrap'>
                    Field: <span className='font-medium'>{results.field}</span>
                  </span>
                  <span className='whitespace-nowrap'>
                    Month{results.months.length > 1 ? 's' : ''}:{' '}
                    <span className='font-medium'>{results.months.join(', ')}</span>
                  </span>
                  <span className='whitespace-nowrap'>
                    Total Matches:{' '}
                    <span className='font-medium'>{results.mismatch_items?.length || 0}</span>
                  </span>
                  <span className='whitespace-nowrap'>
                    Total Mismatches:{' '}
                    <span className='font-medium'>
                      {
                        (results.mismatch_items || []).filter(
                          item =>
                            item.mismatch_type !== 'good_match' &&
                            item.mismatch_type !== 'exact_matches' &&
                            item.mismatch_type !== 'intentionally_unmatched'
                        ).length
                      }
                    </span>
                  </span>
                  <span className='whitespace-nowrap'>
                    Displayed: <span className='font-medium'>{filteredResults.length}</span>
                  </span>
                  <span className='whitespace-nowrap'>
                    Processing Time:{' '}
                    <span className='font-medium'>{results.processing_time.toFixed(2)}s</span>
                  </span>
                </div>
                {/* Keyboard Navigation Indicator */}
                {keyboardNavigationEnabled && (
                  <div className='mt-2 text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded border border-blue-200'>
                    ⌨️ Keyboard Navigation Active: Use ↑↓ to navigate, Space to select, Esc to exit
                  </div>
                )}
              </div>

              {/* Bulk Actions */}
              {filteredResults.length > 0 && (
                <div className='flex flex-wrap gap-2 min-w-0'>
                  <button
                    onClick={handleSelectAll}
                    className='px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 whitespace-nowrap'
                  >
                    Select All
                  </button>
                  <button
                    onClick={handleClearSelection}
                    className='px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 whitespace-nowrap'
                  >
                    Clear Selection
                  </button>
                  <button
                    onClick={handleMarkAsCorrect}
                    disabled={selectedItems.size === 0 || markingCorrect}
                    className='px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap'
                  >
                    {markingCorrect ? 'Marking...' : `Mark ${visibleSelectedCount} as Correct`}
                  </button>
                  <button
                    onClick={handleMarkAsIntentionallyUnmatched}
                    disabled={selectedItems.size === 0 || updatingFiltered}
                    className='px-3 py-1 text-sm bg-yellow-600 text-white rounded hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-yellow-500 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap'
                  >
                    {updatingFiltered ? 'Updating...' : getUnmatchedButtonText}
                  </button>
                  {/* Only show Mark as Incorrect when viewing confirmed matches */}
                  {displayMode === 'matches' && (
                    <button
                      onClick={handleMarkAsIncorrect}
                      disabled={selectedItems.size === 0}
                      className='px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap'
                    >
                      Mark {visibleSelectedCount} as Incorrect
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Reason Input for Unmatched - Only show when adding items */}
          {selectedItems.size > 0 && shouldShowReasonInput && (
            <div className='px-6 py-3 bg-gray-50 border-t border-gray-200'>
              <label className='block text-sm font-medium text-gray-700 mb-1'>
                Reason for marking as unmatched (optional)
              </label>
              <input
                type='text'
                value={reasonText}
                onChange={e => setReasonText(e.target.value)}
                placeholder='e.g., not a real product, joke, spam...'
                className='w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm'
              />
            </div>
          )}

          <div className='p-6'>
            {filteredResults.length > 0 ? (
              <MismatchAnalyzerDataTable
                key={`match-${displayMode}-${filteredResults.length}`} // Force re-render when mode changes
                data={filteredResults}
                field={selectedField}
                onCommentClick={handleCommentClick}
                commentLoading={commentLoading}
                selectedItems={selectedItems}
                onItemSelection={handleItemSelection}
                isItemConfirmed={isItemConfirmed}
                onVisibleRowsChange={handleVisibleRowsChange}
                matched_data_map={results?.matched_data_map}
                onBrushSplitClick={handleBrushSplitClick}
                activeRowIndex={activeRowIndex}
                keyboardNavigationEnabled={keyboardNavigationEnabled}
              />
            ) : (
              <div className='text-center py-8'>
                <div className='text-green-600 text-4xl mb-2'>✅</div>
                <h3 className='text-lg font-medium text-gray-900 mb-2'>No Items Found</h3>
                <p className='text-gray-600'>No items match the current display mode criteria.</p>
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
              Select a month and field, then click &quot;Analyze&quot; to begin match analysis.
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

      {/* Brush Split Modal */}
      {selectedBrushItem && (
        <BrushSplitModal
          isOpen={brushSplitModalOpen}
          onClose={handleBrushSplitClose}
          original={selectedBrushItem.original}
          existingSplit={existingBrushSplit}
          onSave={handleBrushSplitSave}
        />
      )}
    </div>
  );
};

export default MatchAnalyzer;
