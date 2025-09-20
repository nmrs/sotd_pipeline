import React, { useMemo, useState, useCallback } from 'react';
import { ColumnDef, Row, SortingState } from '@tanstack/react-table';
import { DataTable } from '@/components/ui/data-table';
import { CommentDisplay } from '../domain/CommentDisplay';
import { MismatchItem, BrushMatchedData, isBrushMatchedData, AnalyzerDataItem, isGroupedDataItem } from '../../services/api';
import EnrichPhaseModal from '../ui/EnrichPhaseModal';
import HeaderFilter, { HeaderFilterOption } from '../ui/header-filter';
import { hasEnrichPhaseChanges } from '../../utils/enrichPhaseUtils';
import ExpandablePatterns from '../ui/ExpandablePatterns';

// Helper function to extract brush component patterns
const getBrushComponentPattern = (
  matched: Record<string, unknown>,
  component: 'handle' | 'knot'
): string => {
  if (!matched || typeof matched !== 'object') return 'N/A';

  const componentData = matched[component] as Record<string, unknown>;
  if (!componentData || typeof componentData !== 'object') return 'N/A';

  return (componentData._pattern as string) || 'N/A';
};

// Helper function to format brush component data
const formatBrushComponent = (
  matched: Record<string, unknown>,
  component: 'handle' | 'knot'
): string => {
  if (!matched || typeof matched !== 'object') return 'N/A';

  const componentData = matched[component] as Record<string, unknown>;
  if (!componentData || typeof componentData !== 'object') return 'N/A';

  const parts = [];
  if (componentData.brand) parts.push(String(componentData.brand));
  if (componentData.model) parts.push(String(componentData.model));

  // Add fiber and size for knots
  if (component === 'knot') {
    if (componentData.fiber) parts.push(String(componentData.fiber));
    if (componentData.knot_size_mm) parts.push(`${componentData.knot_size_mm}mm`);
  }

  // If no brand/model/fiber/size, try to use source_text (for automated splits and known_split)
  if (parts.length === 0 && componentData.source_text) {
    return String(componentData.source_text);
  }

  return parts.length > 0 ? parts.join(' - ') : 'N/A';
};

// Helper function to check if brush was split into handle/knot components
const isBrushSplit = (matched: Record<string, unknown>): boolean => {
  if (!matched || typeof matched !== 'object') return false;

  // Check if it has handle/knot components (this is the key indicator)
  const hasHandle = matched.handle && typeof matched.handle === 'object' && matched.handle !== null;
  const hasKnot = matched.knot && typeof matched.knot === 'object' && matched.knot !== null;

  // If it has both handle and knot components, it's a split brush
  if (hasHandle && hasKnot) return true;

  // Fallback: if top-level brand and model are missing, it's likely a split brush
  const hasTopLevelBrand = matched.brand && matched.brand !== null && matched.brand !== undefined;
  const hasTopLevelModel = matched.model && matched.model !== null && matched.model !== undefined;

  return !hasTopLevelBrand && !hasTopLevelModel;
};

// Helper function to determine brush type
const getBrushType = (
  matched: Record<string, unknown>
): { type: string; isValid: boolean; error?: string } => {
  if (!matched || typeof matched !== 'object') {
    return { type: 'Unknown', isValid: false, error: 'No matched data' };
  }

  const hasTopLevelBrand = matched.brand && matched.brand !== null && matched.brand !== undefined;
  const hasTopLevelModel = matched.model && matched.model !== null && matched.model !== undefined;
  const hasHandle = matched.handle && typeof matched.handle === 'object' && matched.handle !== null;
  const hasKnot = matched.knot && typeof matched.knot === 'object' && matched.knot !== null;

  // Get handle and knot brands for validation
  const handleBrand = hasHandle ? (matched.handle as Record<string, unknown>).brand : null;
  const knotBrand = hasKnot ? (matched.knot as Record<string, unknown>).brand : null;

  // Complete brush: has top-level brand and model
  if (hasTopLevelBrand && hasTopLevelModel) {
    return { type: 'Complete', isValid: true };
  }

  // Single maker: has top-level brand (model can be null), and handle/knot brands match main brand
  if (hasTopLevelBrand && hasHandle && hasKnot) {
    const mainBrand = String(matched.brand);
    const handleBrandStr = handleBrand ? String(handleBrand) : null;
    const knotBrandStr = knotBrand ? String(knotBrand) : null;

    if (handleBrandStr === mainBrand && knotBrandStr === mainBrand) {
      return { type: 'Single Maker', isValid: true };
    } else if (handleBrandStr === mainBrand || knotBrandStr === mainBrand) {
      // Partial match - this is a validation error
      return {
        type: 'Single Maker',
        isValid: false,
        error: `Brand mismatch: main=${mainBrand}, handle=${handleBrandStr}, knot=${knotBrandStr}`,
      };
    }
  }

  // Single component: has top-level model but no brand (fiber detection)
  if (!hasTopLevelBrand && hasTopLevelModel) {
    return { type: 'Unknown Maker', isValid: true };
  }

  // Composite: no top-level brand/model, but has handle/knot sections
  if (!hasTopLevelBrand && !hasTopLevelModel && hasHandle && hasKnot) {
    // Check if handle and knot brands are the same
    if (handleBrand && knotBrand && handleBrand === knotBrand) {
      // Business rule: When handle and knot have the same brand,
      // the backend should automatically set that brand at the top level
      // This is now handled correctly in the backend, so treat as valid
      return { type: 'Composite (Same Brand)', isValid: true };
    } else if (handleBrand && knotBrand && handleBrand !== knotBrand) {
      // Valid composite: different brands
      return { type: 'Composite', isValid: true };
    }
    return { type: 'Composite', isValid: true };
  }

  // Fallback for other cases
  return { type: 'Unknown', isValid: false, error: 'Invalid brush structure' };
};

interface MismatchAnalyzerDataTableProps {
  data: AnalyzerDataItem[];
  field: string; // Add field prop
  onCommentClick?: (commentId: string, allCommentIds?: string[]) => void;
  commentLoading?: boolean;
  selectedItems?: Set<string>;
  onItemSelection?: (itemKey: string, selected: boolean) => void;
  isItemConfirmed?: (item: MismatchItem) => boolean;
  onVisibleRowsChange?: (visibleRows: AnalyzerDataItem[]) => void;
  matched_data_map?: Record<string, Record<string, any>>;
  onBrushSplitClick?: (item: MismatchItem) => void;
  activeRowIndex?: number;
  keyboardNavigationEnabled?: boolean;
}

const MismatchAnalyzerDataTable: React.FC<MismatchAnalyzerDataTableProps> = ({
  data,
  field,
  onCommentClick,
  commentLoading,
  selectedItems = new Set(),
  onItemSelection,
  isItemConfirmed,
  onVisibleRowsChange,
  matched_data_map: _matched_data_map, // Prefix with underscore to indicate intentionally unused
  onBrushSplitClick,
  activeRowIndex = -1,
  keyboardNavigationEnabled = false,
}) => {
  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [modalData, setModalData] = useState<{
    originalData: Record<string, any>;
    enrichedData: Record<string, any>;
    originalText: string;
  } | null>(null);

  // Header filter state
  const [matchTypeFilter, setMatchTypeFilter] = useState<Set<string>>(new Set());
  const [brushTypeFilter, setBrushTypeFilter] = useState<Set<string>>(new Set());
  const [strategyFilter, setStrategyFilter] = useState<Set<string>>(new Set());

  // Sorting state
  const [sorting, setSorting] = useState<SortingState>([]);

  // Helper function to safely get strategy field
  const getStrategyField = (item: MismatchItem): string => {
    // The API now provides the strategy directly at the item level
    return item.matched_by_strategy || 'unknown';
  };

  // Generate filter options from data
  const matchTypeOptions = useMemo((): HeaderFilterOption[] => {
    const typeCounts = new Map<string, number>();

    data.forEach(item => {
      const matchType = item.match_type || 'unknown';
      typeCounts.set(matchType, (typeCounts.get(matchType) || 0) + 1);
    });

    return Array.from(typeCounts.entries()).map(([value, count]) => ({
      value,
      label: value.charAt(0).toUpperCase() + value.slice(1).replace(/_/g, ' '),
      count,
    }));
  }, [data]);

  const brushTypeOptions = useMemo((): HeaderFilterOption[] => {
    if (field !== 'brush') return [];

    const typeCounts = new Map<string, number>();

    data.forEach(item => {
      const brushType = getBrushType(item.matched);
      const type = brushType.type || 'Unknown';
      typeCounts.set(type, (typeCounts.get(type) || 0) + 1);
    });

    return Array.from(typeCounts.entries()).map(([value, count]) => ({
      value,
      label: value,
      count,
    }));
  }, [data, field]);

  const strategyOptions = useMemo((): HeaderFilterOption[] => {
    if (field !== 'brush') return [];

    const strategyCounts = new Map<string, number>();

    data.forEach(item => {
      const strategy = getStrategyField(item);
      strategyCounts.set(strategy, (strategyCounts.get(strategy) || 0) + 1);
    });

    return Array.from(strategyCounts.entries()).map(([value, count]) => ({
      value,
      label: value,
      count,
    }));
  }, [data, field]);

  // Apply filters to data
  const filteredData = useMemo(() => {
    return data.filter(item => {
      // Apply match type filter
      if (matchTypeFilter.size > 0) {
        const matchType = item.match_type || 'unknown';
        if (!matchTypeFilter.has(matchType)) return false;
      }

      // Apply brush type filter (only for brush field)
      if (field === 'brush' && brushTypeFilter.size > 0) {
        const brushType = getBrushType(item.matched);
        if (!brushTypeFilter.has(brushType.type)) return false;
      }

      // Apply strategy filter (only for brush field)
      if (field === 'brush' && strategyFilter.size > 0) {
        const strategy = getStrategyField(item);
        if (!strategyFilter.has(strategy)) return false;
      }

      return true;
    });
  }, [data, matchTypeFilter, brushTypeFilter, strategyFilter, field]);

  const getMismatchTypeIcon = (mismatchType?: string) => {
    switch (mismatchType) {
      case 'multiple_patterns':
        return '🔄';
      case 'levenshtein_distance':
        return '📏';
      case 'low_confidence':
        return '⚠️';
      case 'regex_match':
        return '🔍';
      case 'potential_mismatch':
        return '❌';
      case 'perfect_regex_matches':
        return '✨';
      case 'exact_matches':
        return '✅';
      default:
        return '❓';
    }
  };

  const getMismatchTypeColor = (mismatchType?: string) => {
    switch (mismatchType) {
      case 'multiple_patterns':
        return 'text-blue-600';
      case 'levenshtein_distance':
        return 'text-yellow-600';
      case 'low_confidence':
        return 'text-orange-600';
      case 'regex_match':
        return 'text-green-600';
      case 'potential_mismatch':
        return 'text-red-600';
      case 'perfect_regex_matches':
        return 'text-purple-600';
      case 'exact_matches':
        return 'text-green-600';
      case 'invalid_match_data':
        return 'text-red-600';
      case 'empty_original':
        return 'text-red-600';
      case 'no_match_found':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getMismatchTypeDisplay = (mismatchType?: string) => {
    if (!mismatchType || mismatchType === 'good_match') return 'Good Match';

    switch (mismatchType) {
      case 'invalid_match_data':
        return 'Invalid Match Data';
      case 'empty_original':
        return 'Empty Original';
      case 'no_match_found':
        return 'No Match Found';
      case 'low_confidence':
        return 'Low Confidence';
      case 'multiple_patterns':
        return 'Multiple Patterns';
      case 'levenshtein_distance':
        return 'Levenshtein Distance';
      case 'regex_match':
        return 'Regex Match';
      case 'potential_mismatch':
        return 'Potential Mismatch';
      case 'perfect_regex_matches':
        return 'Perfect Regex Matches';
      case 'exact_matches':
        return 'Exact Match';
      default:
        return mismatchType;
    }
  };

  const truncateText = (text: string, maxLength: number = 50) => {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  const formatMatchedData = (matched: unknown, field?: string) => {
    if (!matched) return 'N/A';

    if (typeof matched === 'string') {
      return matched;
    }

    if (typeof matched === 'object' && matched !== null) {
      const matchedObj = matched as Record<string, unknown>;

      // Special handling for brush field
      if (field === 'brush') {
        // Check if this is a complete brush (has top-level brand AND model)
        const hasTopLevelBrand =
          matchedObj.brand && matchedObj.brand !== null && matchedObj.brand !== undefined;
        const hasTopLevelModel =
          matchedObj.model && matchedObj.model !== null && matchedObj.model !== undefined;
        const hasHandle =
          matchedObj.handle && typeof matchedObj.handle === 'object' && matchedObj.handle !== null;
        const hasKnot =
          matchedObj.knot && typeof matchedObj.knot === 'object' && matchedObj.knot !== null;

        // Complete brush: must have BOTH top-level brand AND model
        if (hasTopLevelBrand && hasTopLevelModel) {
          const parts = [];
          if (matchedObj.brand) parts.push(String(matchedObj.brand));
          if (matchedObj.model) parts.push(String(matchedObj.model));
          if (matchedObj.fiber) parts.push(String(matchedObj.fiber));
          if (matchedObj.knot_size_mm) parts.push(`${matchedObj.knot_size_mm}mm`);
          // Only include handle_maker if it's different from the brand
          if (matchedObj.handle_maker && matchedObj.handle_maker !== matchedObj.brand) {
            parts.push(String(matchedObj.handle_maker));
          }

          return parts.length > 0 ? parts.join(' - ') : JSON.stringify(matched);
        } else if (hasHandle && hasKnot) {
          // Composite brush: has handle/knot components but missing either brand or model
          // This includes cases where there's a top-level brand but no model
          const handleText = formatBrushComponent(matchedObj, 'handle');
          const knotText = formatBrushComponent(matchedObj, 'knot');

          if (handleText !== 'N/A' || knotText !== 'N/A') {
            const parts = [];
            if (handleText !== 'N/A') parts.push(`Handle: ${handleText}`);
            if (knotText !== 'N/A') parts.push(`Knot: ${knotText}`);
            return parts.join('\n');
          }
        } else {
          // Fallback: show whatever data is available
          const parts = [];
          if (matchedObj.brand) parts.push(String(matchedObj.brand));
          if (matchedObj.model) parts.push(String(matchedObj.model));
          if (matchedObj.fiber) parts.push(String(matchedObj.fiber));
          if (matchedObj.knot_size_mm) parts.push(`${matchedObj.knot_size_mm}mm`);
          if (matchedObj.handle_maker) parts.push(String(matchedObj.handle_maker));

          return parts.length > 0 ? parts.join(' - ') : JSON.stringify(matched);
        }
      }

      // For other fields, use the original logic
      const parts = [];
      if (matchedObj.brand) parts.push(String(matchedObj.brand));
      if (matchedObj.model) parts.push(String(matchedObj.model));
      if (matchedObj.format) parts.push(String(matchedObj.format));
      if (matchedObj.maker) parts.push(String(matchedObj.maker));
      if (matchedObj.scent) parts.push(String(matchedObj.scent));

      return parts.length > 0 ? parts.join(' - ') : JSON.stringify(matched);
    }

    return String(matched);
  };

  const handleVisibleRowsChange = useCallback(
    (rows: MismatchItem[]) => {
      onVisibleRowsChange?.(rows);
    },
    [onVisibleRowsChange]
  );

  // Handle row selection changes from DataTable
  const handleSelectionChange = useCallback(
    (selectedRows: MismatchItem[]) => {
      if (!onItemSelection) return;

      // Convert selected rows to item keys
      const selectedKeys = new Set(
        selectedRows.map(item => {
          if (isGroupedDataItem(item)) {
            return `${field}:${item.matched_string?.toLowerCase() || 'unknown'}`;
          } else {
            return `${field}:${item.original?.toLowerCase() || 'unknown'}`;
          }
        })
      );

      // Update all items to match the new selection state
      filteredData.forEach(item => {
        const itemKey = isGroupedDataItem(item)
          ? `${field}:${item.matched_string?.toLowerCase() || 'unknown'}`
          : `${field}:${item.original?.toLowerCase() || 'unknown'}`;
        const shouldBeSelected = selectedKeys.has(itemKey);
        const isCurrentlySelected = selectedItems.has(itemKey);

        if (shouldBeSelected !== isCurrentlySelected) {
          onItemSelection(itemKey, shouldBeSelected);
        }
      });
    },
    [onItemSelection, field, filteredData, selectedItems]
  );

  // Create initial row selection state for DataTable
  const initialRowSelection = useMemo(() => {
    const selection: Record<string, boolean> = {};
    filteredData.forEach((item, index) => {
      // Generate key based on data type
      const itemKey = isGroupedDataItem(item)
        ? `${field}:${item.matched_string?.toLowerCase() || 'unknown'}`
        : `${field}:${item.original?.toLowerCase() || 'unknown'}`;
      if (selectedItems.has(itemKey)) {
        selection[index.toString()] = true;
      }
    });
    return selection;
  }, [filteredData, field, selectedItems]);

  // Create external row selection state for DataTable
  const externalRowSelection = useMemo(() => {
    const selection: Record<string, boolean> = {};
    filteredData.forEach((item, index) => {
      // Generate key based on data type
      const itemKey = isGroupedDataItem(item)
        ? `${field}:${item.matched_string?.toLowerCase() || 'unknown'}`
        : `${field}:${item.original?.toLowerCase() || 'unknown'}`;
      if (selectedItems.has(itemKey)) {
        selection[index.toString()] = true;
      }
    });
    return selection;
  }, [filteredData, field, selectedItems]);

  // Stabilize the data to prevent unnecessary re-renders
  const stableData = useMemo(() => filteredData, [filteredData]);

  const columns = useMemo(() => {
    // Check if any items are grouped to determine header label
    const hasGroupedItems = data.some(item => isGroupedDataItem(item));
    const firstColumnHeader = hasGroupedItems ? 'Matched' : 'Original';

    const baseColumns: ColumnDef<AnalyzerDataItem>[] = [
      // Selection column
      ...(onItemSelection
        ? [
          {
            id: 'selection',
            header: () => {
              // For now, use all data since we can't easily access visible rows from header
              // This will be fixed in a future update when we can pass table context
              return (
                <div className='flex items-center gap-2'>
                  <span>Select</span>
                </div>
              );
            },
            cell: ({ row }: { row: Row<AnalyzerDataItem> }) => {
              const item = row.original;
              // Generate key based on data type
              const itemKey = isGroupedDataItem(item)
                ? `${field}:${item.matched_string?.toLowerCase() || 'unknown'}`
                : `${field}:${item.original?.toLowerCase() || 'unknown'}`;
              const isSelected = selectedItems.has(itemKey);

              return (
                <input
                  type='checkbox'
                  checked={isSelected}
                  onChange={e => onItemSelection?.(itemKey, e.target.checked)}
                  className='rounded border-gray-300 text-blue-600 focus:ring-blue-500'
                />
              );
            },
            enableSorting: false,
          },
        ]
        : []),

      // Status column
      ...(isItemConfirmed
        ? [
          {
            id: 'status',
            header: 'Status',
            cell: ({ row }: { row: Row<AnalyzerDataItem> }) => {
              const item = row.original;
              // Only show status for regular items, not grouped data
              if (isGroupedDataItem(item)) {
                return <span className="text-gray-400">N/A</span>;
              }
              const isConfirmed = isItemConfirmed(item);

              return (
                <div className='flex items-center'>
                  {isConfirmed ? (
                    <span className='inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800'>
                      ✅ Confirmed
                    </span>
                  ) : (
                    <span className='inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800'>
                      ⚠️ Unconfirmed
                    </span>
                  )}
                </div>
              );
            },
          },
        ]
        : []),
      {
        accessorKey: 'count',
        header: 'Count',
        cell: ({ row }: { row: Row<AnalyzerDataItem> }) => {
          const item = row.original;
          const count = isGroupedDataItem(item) ? item.total_count : (item.count || 1);
          return (
            <span className='inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800'>
              {count}
            </span>
          );
        },
      },
      {
        accessorKey: 'mismatch_type',
        header: 'Type',
        cell: ({ row }: { row: Row<AnalyzerDataItem> }) => {
          const item = row.original;
          // For grouped data, show a different icon and text
          if (isGroupedDataItem(item)) {
            return (
              <div className='flex items-center'>
                <span className='text-lg mr-2'>📊</span>
                <span className='text-sm font-medium text-blue-600'>
                  Grouped
                </span>
              </div>
            );
          }
          return (
            <div className='flex items-center'>
              <span className='text-lg mr-2'>{getMismatchTypeIcon(item.mismatch_type)}</span>
              <span className={`text-sm font-medium ${getMismatchTypeColor(item.mismatch_type)}`}>
                {getMismatchTypeDisplay(item.mismatch_type)}
              </span>
            </div>
          );
        },
      },
      {
        id: 'matched_content',
        accessorFn: (row: AnalyzerDataItem) => {
          // For grouped data, use matched_string for sorting
          if (isGroupedDataItem(row)) {
            return row.matched_string;
          }
          // For regular data, use original
          return row.original;
        },
        header: firstColumnHeader,
        cell: ({ row }: { row: Row<AnalyzerDataItem> }) => {
          const item = row.original;
          // For grouped data, show matched_string instead of original
          if (isGroupedDataItem(item)) {
            return (
              <div className='font-medium text-gray-900'>
                {item.matched_string}
              </div>
            );
          }

          // For brush field, add click-to-edit functionality
          if (field === 'brush' && onBrushSplitClick) {
            return (
              <div
                className='text-sm text-gray-900 cursor-pointer hover:bg-blue-50 hover:text-blue-700 p-1 rounded border border-transparent hover:border-blue-200 transition-colors'
                onClick={() => onBrushSplitClick(item)}
                title={item.original}
              >
                ✏️ {item.original}
              </div>
            );
          }

          return (
            <div className='text-sm text-gray-900' title={item.original}>
              {item.original}
            </div>
          );
        },
      },
      // Only show matched column for non-grouped data
      ...(data.some(item => !isGroupedDataItem(item)) ? [{
        accessorKey: 'matched',
        header: 'Matched',
        sortingFn: (rowA, rowB) => {
          const a = formatMatchedData(rowA.original.matched, field);
          const b = formatMatchedData(rowB.original.matched, field);
          return a.localeCompare(b);
        },
        cell: ({ row }: { row: Row<AnalyzerDataItem> }) => {
          const item = row.original;

          // Only show for non-grouped data
          if (isGroupedDataItem(item)) {
            return null;
          }

          const formattedData = formatMatchedData(item.matched, field);

          // Check if there are enrich-phase changes using the enriched data from the API response
          const hasChanges =
            item.enriched &&
            hasEnrichPhaseChanges(
              item.matched as Record<string, any>,
              item.enriched as Record<string, any>,
              field
            );

          const handleEnrichClick = () => {
            if (hasChanges) {
              setModalData({
                originalData: item.matched as Record<string, any>,
                enrichedData: item.enriched as Record<string, any>,
                originalText: item.original,
              });
              setModalOpen(true);
            }
          };

          // For brush field, render with line breaks
          if (field === 'brush' && formattedData.includes('\n')) {
            const content = (
              <div
                className={`text-sm text-gray-900 ${hasChanges ? 'border-l-4 border-blue-500 pl-2 bg-blue-50 cursor-pointer hover:bg-blue-100' : ''}`}
                onClick={hasChanges ? handleEnrichClick : undefined}
                title={formattedData}
              >
                {hasChanges && <span className='text-blue-600 text-xs mr-1'>🔄</span>}
                {formattedData.split('\n').map((line, index) => (
                  <div key={index} className={index > 0 ? 'mt-1' : ''}>
                    {line}
                  </div>
                ))}
              </div>
            );

            return content;
          }

          // For other fields, use the original rendering
          const content = (
            <div
              className={`text-sm text-gray-900 ${hasChanges ? 'border-l-4 border-blue-500 pl-2 bg-blue-50 cursor-pointer hover:bg-blue-100' : ''}`}
              onClick={hasChanges ? handleEnrichClick : undefined}
              title={formattedData}
            >
              {hasChanges && <span className='text-blue-600 text-xs mr-1'>🔄</span>}
              <span>{formattedData}</span>
            </div>
          );

          return content;
        },
      }] : []),
    ];

    // Add format column for blade field to show which format section the entry will be placed in
    if (field === 'blade') {
      baseColumns.push({
        id: 'format',
        accessorFn: (row: MismatchItem) => {
          const matched = row.matched as Record<string, unknown>;
          return matched?.format || 'DE';
        },
        header: () => (
          <div className='flex items-center gap-1 group'>
            <span>Format</span>
            <span
              className='text-gray-400 text-xs cursor-help'
              title='Shows which format section this blade will be placed in when marked as correct (e.g., DE, GEM, AC)'
            >
              ℹ️
            </span>
          </div>
        ),
        cell: ({ row }: { row: Row<AnalyzerDataItem> }) => {
          const item = row.original;
          const matched = item.matched as Record<string, unknown>;
          const format = matched?.format || 'DE';

          // Color-code different formats for better visibility
          const getFormatColor = (fmt: string) => {
            switch (fmt.toUpperCase()) {
              case 'DE':
                return 'bg-blue-100 text-blue-800';
              case 'GEM':
                return 'bg-green-100 text-green-800';
              case 'AC':
                return 'bg-purple-100 text-purple-800';
              case 'INJECTOR':
                return 'bg-orange-100 text-orange-800';
              case 'HAIR SHAPER':
                return 'bg-red-100 text-red-800';
              case 'FHS':
                return 'bg-indigo-100 text-indigo-800';
              case 'A77':
                return 'bg-pink-100 text-pink-800';
              case 'HALF DE':
                return 'bg-yellow-100 text-yellow-800';
              default:
                return 'bg-gray-100 text-gray-800';
            }
          };

          return (
            <div className='text-sm'>
              <span
                className={`inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full ${getFormatColor(format)}`}
                title={`This blade will be placed in the ${format} format section when marked as correct`}
              >
                {format}
              </span>
            </div>
          );
        },
      });
    }

    // Add match_type column
    baseColumns.push({
      accessorKey: 'match_type',
      header: () => (
        <HeaderFilter
          title='Match Type'
          options={matchTypeOptions}
          selectedValues={matchTypeFilter}
          onSelectionChange={setMatchTypeFilter}
          searchPlaceholder='Search match types...'
          onSort={() => {
            const currentSort = sorting.find(s => s.id === 'match_type');
            const newDirection = !currentSort ? 'asc' : currentSort.desc ? null : 'desc';
            setSorting(newDirection ? [{ id: 'match_type', desc: newDirection === 'desc' }] : []);
          }}
          sortDirection={(() => {
            const currentSort = sorting.find(s => s.id === 'match_type');
            if (!currentSort) return null;
            return currentSort.desc ? 'desc' : 'asc';
          })()}
        />
      ),
      cell: ({ row }: { row: Row<AnalyzerDataItem> }) => {
        const item = row.original;
        return (
          <span className='inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800'>
            {item.match_type}
          </span>
        );
      },
    });

    // Add brush-specific columns if field is brush
    if (field === 'brush') {
      // Add brush type column
      baseColumns.push({
        id: 'brush_type',
        accessorFn: row => {
          const brushType = getBrushType(row.matched);
          return brushType.type;
        },
        header: () => (
          <HeaderFilter
            title='Brush Type'
            options={brushTypeOptions}
            selectedValues={brushTypeFilter}
            onSelectionChange={setBrushTypeFilter}
            searchPlaceholder='Search brush types...'
            onSort={() => {
              const currentSort = sorting.find(s => s.id === 'brush_type');
              const newDirection = !currentSort ? 'asc' : currentSort.desc ? null : 'desc';
              setSorting(newDirection ? [{ id: 'brush_type', desc: newDirection === 'desc' }] : []);
            }}
            sortDirection={(() => {
              const currentSort = sorting.find(s => s.id === 'brush_type');
              if (!currentSort) return null;
              return currentSort.desc ? 'desc' : 'asc';
            })()}
          />
        ),
        cell: ({ row }: { row: Row<AnalyzerDataItem> }) => {
          const item = row.original;
          const brushType = getBrushType(item.matched);

          return (
            <div className='text-sm max-w-xs'>
              <span
                className={`inline-flex items-center justify-center text-center px-2 py-1 text-xs font-semibold rounded-full whitespace-normal ${brushType.isValid ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}
              >
                {brushType.type}
              </span>
              {!brushType.isValid && brushType.error && (
                <div className='mt-1 text-xs text-red-600 font-mono'>{brushType.error}</div>
              )}
            </div>
          );
        },
      });

      // Add strategy column for brush field
      baseColumns.push({
        id: 'strategy',
        accessorFn: row => {
          return getStrategyField(row);
        },
        header: () => (
          <HeaderFilter
            title='Strategy'
            options={strategyOptions}
            selectedValues={strategyFilter}
            onSelectionChange={setStrategyFilter}
            searchPlaceholder='Search strategies...'
            onSort={() => {
              const currentSort = sorting.find(s => s.id === 'strategy');
              const newDirection = !currentSort ? 'asc' : currentSort.desc ? null : 'desc';
              setSorting(newDirection ? [{ id: 'strategy', desc: newDirection === 'desc' }] : []);
            }}
            sortDirection={(() => {
              const currentSort = sorting.find(s => s.id === 'strategy');
              if (!currentSort) return null;
              return currentSort.desc ? 'desc' : 'asc';
            })()}
          />
        ),
        cell: ({ row }: { row: Row<AnalyzerDataItem> }) => {
          const item = row.original;
          const strategy = getStrategyField(item);

          // Color-code different strategies for better visibility
          const getStrategyColor = (strat: string) => {
            switch (strat) {
              case 'known_brush':
                return 'bg-blue-100 text-blue-800';
              case 'handle_only':
                return 'bg-green-100 text-green-800';
              case 'knot_only':
                return 'bg-purple-100 text-purple-800';
              case 'split_brush':
                return 'bg-orange-100 text-orange-800';
              case 'FiberFallbackStrategy':
                return 'bg-yellow-100 text-yellow-800';
              case 'KnotSizeFallbackStrategy':
                return 'bg-indigo-100 text-indigo-800';
              case 'unknown':
                return 'bg-gray-100 text-gray-800';
              default:
                return 'bg-gray-100 text-gray-800';
            }
          };

          return (
            <div className='text-sm'>
              <span
                className={`inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full ${getStrategyColor(strategy)}`}
                title={`Matched using strategy: ${strategy}`}
              >
                {strategy}
              </span>
            </div>
          );
        },
      });

      // Always show brush pattern column
      baseColumns.push({
        id: 'brush_pattern',
        accessorFn: row => {
          return row.pattern || '';
        },
        header: 'Brush Pattern',
        cell: ({ row }: { row: Row<AnalyzerDataItem> }) => {
          const item = row.original;
          const patternText = item.pattern || '';
          return (
            <div
              className='text-sm text-gray-500 max-w-xs font-mono relative truncate'
              title={patternText}
            >
              {truncateText(patternText, 40)}
            </div>
          );
        },
      });

      // Always show handle/knot columns for brush fields
      baseColumns.push(
        {
          id: 'handle',
          accessorFn: row => {
            return formatBrushComponent(row.matched, 'handle');
          },
          header: 'Handle',
          cell: ({ row }: { row: Row<AnalyzerDataItem> }) => {
            const item = row.original;
            const handleText = formatBrushComponent(item.matched, 'handle');
            return (
              <div className='text-sm text-gray-900' title={handleText}>
                {handleText}
              </div>
            );
          },
        },
        {
          id: 'handle_pattern',
          accessorFn: row => {
            return getBrushComponentPattern(row.matched, 'handle');
          },
          header: 'Handle Pattern',
          cell: ({ row }: { row: Row<AnalyzerDataItem> }) => {
            const item = row.original;
            const patternText = getBrushComponentPattern(item.matched, 'handle');
            return (
              <div className='text-sm text-gray-500 font-mono' title={patternText}>
                {patternText}
              </div>
            );
          },
        },
        {
          id: 'knot',
          accessorFn: row => {
            return formatBrushComponent(row.matched, 'knot');
          },
          header: 'Knot',
          cell: ({ row }: { row: Row<AnalyzerDataItem> }) => {
            const item = row.original;
            const knotText = formatBrushComponent(item.matched, 'knot');
            return (
              <div className='text-sm text-gray-900' title={knotText}>
                {knotText}
              </div>
            );
          },
        },
        {
          id: 'knot_pattern',
          accessorFn: row => {
            return getBrushComponentPattern(row.matched, 'knot');
          },
          header: 'Knot Pattern',
          cell: ({ row }: { row: Row<AnalyzerDataItem> }) => {
            const item = row.original;
            const patternText = getBrushComponentPattern(item.matched, 'knot');
            return (
              <div className='text-sm text-gray-500 font-mono' title={patternText}>
                {patternText}
              </div>
            );
          },
        }
      );
    } else {
      // For non-brush fields, keep the original pattern column
      baseColumns.push({
        accessorKey: 'pattern',
        header: 'Pattern',
        cell: ({ row }: { row: Row<AnalyzerDataItem> }) => {
          const item = row.original;
          return <div className='text-sm text-gray-500 font-mono'>{item.pattern}</div>;
        },
      });
    }

    // Add common columns
    baseColumns.push(
      {
        accessorKey: 'confidence',
        header: 'Confidence',
        cell: ({ row }: { row: Row<AnalyzerDataItem> }) => {
          const item = row.original;
          return (
            <span className='text-sm text-gray-900'>
              {item.confidence ? `${Math.round(item.confidence * 100)}%` : 'N/A'}
            </span>
          );
        },
      },
      {
        accessorKey: 'comment_ids',
        header: 'Comments',
        cell: ({ row }: { row: Row<AnalyzerDataItem> }) => {
          const item = row.original;
          const commentIds = item.comment_ids || [];

          return (
            <CommentDisplay
              commentIds={commentIds}
              onCommentClick={onCommentClick || (() => { })}
              commentLoading={commentLoading}
            />
          );
        },
      }
    );

    // Add patterns column for grouped data
    baseColumns.push({
      id: 'patterns',
      header: 'Normalized Patterns',
      cell: ({ row }: { row: Row<AnalyzerDataItem> }) => {
        const item = row.original;
        if (!isGroupedDataItem(item)) {
          return <span className="text-gray-400">N/A</span>;
        }

        return (
          <ExpandablePatterns
            topPatterns={item.top_patterns}
            allPatterns={item.all_patterns}
            remainingCount={item.remaining_count}
            maxInitial={3}
          />
        );
      },
      enableSorting: false,
    });

    return baseColumns;
  }, [
    data,
    onCommentClick,
    commentLoading,
    selectedItems,
    onItemSelection,
    isItemConfirmed,
    field,
    onBrushSplitClick,
    brushTypeOptions,
    strategyOptions,
    matchTypeFilter,
    brushTypeFilter,
    strategyFilter,
    sorting,
  ]);

  return (
    <div className='space-y-4'>
      <DataTable
        columns={columns}
        data={stableData}
        showPagination={true}
        resizable={true}
        sortable={true}
        showColumnVisibility={true}
        searchKey=''
        initialPageSize={500}
        onVisibleRowsChange={handleVisibleRowsChange}
        sorting={sorting}
        onSortingChange={setSorting}
        enableRowClickSelection={true}
        onSelectionChange={handleSelectionChange}
        initialRowSelection={initialRowSelection}
        externalRowSelection={externalRowSelection}
        activeRowIndex={activeRowIndex}
        keyboardNavigationEnabled={keyboardNavigationEnabled}
        field={field}
      />

      {/* Enrich Phase Modal */}
      {modalData && (
        <EnrichPhaseModal
          isOpen={modalOpen}
          onClose={() => {
            setModalOpen(false);
            setModalData(null);
          }}
          originalData={modalData.originalData}
          enrichedData={modalData.enrichedData}
          field={field}
          originalText={modalData.originalText}
        />
      )}
    </div>
  );
};

export default MismatchAnalyzerDataTable;
