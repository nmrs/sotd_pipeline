import React, { useMemo, useState, useCallback } from 'react';
import { ColumnDef, Row, SortingState } from '@tanstack/react-table';
import { DataTable } from '@/components/ui/data-table';
import { CommentList } from '../domain/CommentList';
import { MismatchItem } from '../../services/api';
import EnrichPhaseModal from '../ui/EnrichPhaseModal';
import HeaderFilter, { HeaderFilterOption } from '../ui/header-filter';

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

  return parts.length > 0 ? parts.join(' - ') : 'N/A';
};

// Helper function to check if brush was split into handle/knot components
const isBrushSplit = (matched: Record<string, unknown>): boolean => {
  if (!matched || typeof matched !== 'object') return false;

  // If top-level brand and model are null/undefined, it's a split brush
  const hasTopLevelBrand = matched.brand && matched.brand !== null && matched.brand !== undefined;
  const hasTopLevelModel = matched.model && matched.model !== null && matched.model !== undefined;

  // If both brand and model are missing at top level, it's a split brush
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

  // Composite: no top-level brand/model, but has handle/knot sections
  if (!hasTopLevelBrand && !hasTopLevelModel && hasHandle && hasKnot) {
    // Check if handle and knot brands are the same
    if (handleBrand && knotBrand && handleBrand === knotBrand) {
      // ERROR: Same brands but no top-level brand/model - this is a pipeline error
      return {
        type: 'ERROR',
        isValid: false,
        error: `Pipeline error: handle and knot have same brand (${handleBrand}) but no top-level brand/model`,
      };
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
  data: MismatchItem[];
  field: string; // Add field prop
  onCommentClick?: (commentId: string, allCommentIds?: string[]) => void;
  commentLoading?: boolean;
  selectedItems?: Set<string>;
  onItemSelection?: (itemKey: string, selected: boolean) => void;
  isItemConfirmed?: (item: MismatchItem) => boolean;
  onVisibleRowsChange?: (visibleRows: MismatchItem[]) => void;
  matched_data_map?: Record<string, Record<string, any>>;
  onBrushSplitClick?: (item: MismatchItem) => void;
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

  // Sorting state
  const [sorting, setSorting] = useState<SortingState>([]);

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

      return true;
    });
  }, [data, matchTypeFilter, brushTypeFilter, field]);

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
        // Check if this is a split brush or complete brush
        if (isBrushSplit(matchedObj)) {
          // For split brushes, show handle and knot components
          const handleText = formatBrushComponent(matchedObj, 'handle');
          const knotText = formatBrushComponent(matchedObj, 'knot');

          if (handleText !== 'N/A' || knotText !== 'N/A') {
            const parts = [];
            if (handleText !== 'N/A') parts.push(`Handle: ${handleText}`);
            if (knotText !== 'N/A') parts.push(`Knot: ${knotText}`);
            return parts.join('\n');
          }
        } else {
          // For complete brushes, show brand and model like other products
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

  // Helper function to check if there are enrich-phase changes
  const hasEnrichPhaseChanges = (
    matchedData: Record<string, any>,
    enrichedData: Record<string, any>
  ): boolean => {
    if (!matchedData || !enrichedData) return false;

    // For brush field, check the enriched data against matched data
    if (field === 'brush') {
      // Check fiber changes (enriched data overrides matched)
      const matchedKnotFiber = matchedData?.knot?.fiber;
      const enrichedFiber = enrichedData?.fiber;
      
      // Only consider it a change if both values exist and are different
      if (matchedKnotFiber !== undefined && enrichedFiber !== undefined && matchedKnotFiber !== enrichedFiber) {
        return true;
      }

      // Check knot size changes
      const matchedKnotSize = matchedData?.knot?.knot_size_mm;
      const enrichedKnotSize = enrichedData?.knot_size_mm;
      
      // Consider it a change if:
      // 1. Both values exist and are different, OR
      // 2. One value exists and the other is null/undefined (indicating a change from no data to data or vice versa)
      if (matchedKnotSize !== undefined && enrichedKnotSize !== undefined && matchedKnotSize !== enrichedKnotSize) {
        return true;
      }
      if ((matchedKnotSize === null || matchedKnotSize === undefined) && enrichedKnotSize !== undefined && enrichedKnotSize !== null) {
        return true;
      }
      if ((enrichedKnotSize === null || enrichedKnotSize === undefined) && matchedKnotSize !== undefined && matchedKnotSize !== null) {
        return true;
      }

      // For brush enrichment, only fiber and knot_size_mm can change
      // Brand, model, handle_maker, etc. should remain the same from match phase
      // Don't check other fields as they shouldn't change during brush enrichment

      // No changes detected for fiber or knot size
      return false;
    } else {
      // For other fields, check top-level fields
      const fieldsToCheck = ['fiber', 'knot_size_mm', 'handle_maker', 'brand', 'model'];

      return fieldsToCheck.some(field => {
        const original = matchedData[field];
        const enriched = enrichedData[field];
        // Only consider it a change if both values exist and are different
        return original !== undefined && enriched !== undefined && original !== enriched;
      });
    }

    return false;
  };

  const columns = useMemo(() => {
    const baseColumns: ColumnDef<MismatchItem>[] = [
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
            cell: ({ row }: { row: Row<MismatchItem> }) => {
              const item = row.original;
              // Since backend groups by case-insensitive original text, use that as the key
              const itemKey = `${field}:${item.original.toLowerCase()}`;
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
            cell: ({ row }: { row: Row<MismatchItem> }) => {
              const item = row.original;
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
        cell: ({ row }: { row: Row<MismatchItem> }) => {
          const item = row.original;
          return (
            <span className='inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800'>
              {item.count || 1}
            </span>
          );
        },
      },
      {
        accessorKey: 'mismatch_type',
        header: 'Type',
        cell: ({ row }: { row: Row<MismatchItem> }) => {
          const item = row.original;
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
        accessorKey: 'original',
        header: 'Original',
        cell: ({ row }: { row: Row<MismatchItem> }) => {
          const item = row.original;

          // For brush field, add click-to-edit functionality
          if (field === 'brush' && onBrushSplitClick) {
            return (
              <div
                className='text-sm text-gray-900 max-w-xs whitespace-pre-wrap cursor-pointer hover:bg-blue-50 hover:text-blue-700 p-1 rounded border border-transparent hover:border-blue-200 transition-colors'
                onClick={() => onBrushSplitClick(item)}
                title="Click to edit brush split"
              >
                ✏️ {item.original}
              </div>
            );
          }

          return (
            <div className='text-sm text-gray-900 max-w-xs whitespace-pre-wrap'>
              {item.original}
            </div>
          );
        },
      },
      {
        accessorKey: 'matched',
        header: 'Matched',
        sortingFn: (rowA, rowB) => {
          const a = formatMatchedData(rowA.original.matched, field);
          const b = formatMatchedData(rowB.original.matched, field);
          return a.localeCompare(b);
        },
        cell: ({ row }: { row: Row<MismatchItem> }) => {
          const item = row.original;
          const formattedData = formatMatchedData(item.matched, field);

          // Check if there are enrich-phase changes using the enriched data from the API response
          const hasChanges =
            item.enriched &&
            hasEnrichPhaseChanges(
              item.matched as Record<string, any>,
              item.enriched as Record<string, any>
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
                className={`text-sm text-gray-900 max-w-xs ${hasChanges ? 'border-l-4 border-blue-500 pl-2 bg-blue-50 cursor-pointer hover:bg-blue-100' : ''}`}
                onClick={hasChanges ? handleEnrichClick : undefined}
              >
                {hasChanges && <span className='text-blue-600 text-xs mr-1'>🔄</span>}
                {formattedData.split('\n').map((line, index) => (
                  <div key={index} className={index > 0 ? 'mt-1' : ''}>
                    {truncateText(line, 60)}
                  </div>
                ))}
              </div>
            );

            return content;
          }

          // For other fields, use the original rendering
          const content = (
            <div
              className={`text-sm text-gray-900 max-w-xs ${hasChanges ? 'border-l-4 border-blue-500 pl-2 bg-blue-50 cursor-pointer hover:bg-blue-100' : ''}`}
              onClick={hasChanges ? handleEnrichClick : undefined}
            >
              {hasChanges && <span className='text-blue-600 text-xs mr-1'>🔄</span>}
              <span>{truncateText(formattedData, 60)}</span>
            </div>
          );

          return content;
        },
      },
      {
        accessorKey: 'match_type',
        header: () => (
          <HeaderFilter
            title="Match Type"
            options={matchTypeOptions}
            selectedValues={matchTypeFilter}
            onSelectionChange={setMatchTypeFilter}
            searchPlaceholder="Search match types..."
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
        cell: ({ row }: { row: Row<MismatchItem> }) => {
          const item = row.original;
          return (
            <span className='inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800'>
              {item.match_type}
            </span>
          );
        },
      },
    ];

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
            title="Brush Type"
            options={brushTypeOptions}
            selectedValues={brushTypeFilter}
            onSelectionChange={setBrushTypeFilter}
            searchPlaceholder="Search brush types..."
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
        cell: ({ row }: { row: Row<MismatchItem> }) => {
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

      // Always show brush pattern column
      baseColumns.push({
        id: 'brush_pattern',
        accessorFn: row => {
          const isSplitBrush = row.is_split_brush === true;
          if (isSplitBrush) {
            const handleText = row.handle_component || 'N/A';
            const knotText = row.knot_component || 'N/A';
            return `split handle: ${handleText} knot: ${knotText}`;
          } else {
            return row.pattern || '';
          }
        },
        header: 'Brush Pattern',
        cell: ({ row }: { row: Row<MismatchItem> }) => {
          const item = row.original;
          const isSplitBrush = item.is_split_brush === true;

          if (isSplitBrush) {
            // For split brushes, show the split format
            const handleText = item.handle_component || 'N/A';
            const knotText = item.knot_component || 'N/A';
            return (
              <div className='text-sm text-gray-500 max-w-xs font-mono relative'>
                🔗 split
                <br />
                handle: {truncateText(handleText, 30)}
                <br />
                knot: {truncateText(knotText, 30)}
              </div>
            );
          } else {
            // For complete brushes, show the pattern
            const patternText = item.pattern || '';
            return (
              <div className='text-sm text-gray-500 max-w-xs font-mono relative'>
                {truncateText(patternText, 40)}
              </div>
            );
          }
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
          cell: ({ row }: { row: Row<MismatchItem> }) => {
            const item = row.original;
            // For split brushes, show the matched handle data
            const handleText = formatBrushComponent(item.matched, 'handle');
            return (
              <div className='text-sm text-gray-900 max-w-xs relative'>
                {truncateText(handleText, 50)}
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
          cell: ({ row }: { row: Row<MismatchItem> }) => {
            const item = row.original;
            return (
              <div className='text-sm text-gray-500 max-w-xs font-mono relative'>
                {truncateText(getBrushComponentPattern(item.matched, 'handle'), 40)}
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
          cell: ({ row }: { row: Row<MismatchItem> }) => {
            const item = row.original;
            // For split brushes, show the matched knot data
            const knotText = formatBrushComponent(item.matched, 'knot');
            return (
              <div className='text-sm text-gray-900 max-w-xs'>{truncateText(knotText, 50)}</div>
            );
          },
        },
        {
          id: 'knot_pattern',
          accessorFn: row => {
            return getBrushComponentPattern(row.matched, 'knot');
          },
          header: 'Knot Pattern',
          cell: ({ row }: { row: Row<MismatchItem> }) => {
            const item = row.original;
            return (
              <div className='text-sm text-gray-500 max-w-xs font-mono'>
                {truncateText(getBrushComponentPattern(item.matched, 'knot'), 40)}
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
        cell: ({ row }: { row: Row<MismatchItem> }) => {
          const item = row.original;
          return (
            <div className='text-sm text-gray-500 max-w-xs font-mono'>
              {truncateText(item.pattern, 40)}
            </div>
          );
        },
      });
    }

    // Add common columns
    baseColumns.push(
      {
        accessorKey: 'confidence',
        header: 'Confidence',
        cell: ({ row }: { row: Row<MismatchItem> }) => {
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
        cell: ({ row }: { row: Row<MismatchItem> }) => {
          const item = row.original;
          const commentIds = item.comment_ids || [];

          return (
            <CommentList
              commentIds={commentIds}
              onCommentClick={onCommentClick || (() => { })}
              commentLoading={commentLoading}
              maxDisplay={3}
              aria-label={`${commentIds.length} comment${commentIds.length !== 1 ? 's' : ''} available`}
            />
          );
        },
      }
    );

    return baseColumns;
  }, [onCommentClick, commentLoading, selectedItems, onItemSelection, isItemConfirmed, field, onBrushSplitClick]);

  return (
    <div className='space-y-4'>
      <DataTable
        key={`mismatch-table-${filteredData.length}-${matchTypeFilter.size}-${brushTypeFilter.size}-${sorting.length}`} // Force re-render when data, filters, or sorting change
        columns={columns}
        data={filteredData}
        showPagination={true}
        resizable={true}
        sortable={true}
        showColumnVisibility={true}
        searchKey='original'
        initialPageSize={50}
        onVisibleRowsChange={onVisibleRowsChange}
        sorting={sorting}
        onSortingChange={setSorting}
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
