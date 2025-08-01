import React, { useMemo } from 'react';
import { ColumnDef, Row } from '@tanstack/react-table';
import { DataTable } from '@/components/ui/data-table';
import { CommentList } from '../domain/CommentList';
import { MismatchItem } from '../../services/api';
import EnrichPhaseTooltip from '../ui/EnrichPhaseTooltip';

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
  matched_data_map,
}) => {
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
  const hasEnrichPhaseChanges = (originalData: Record<string, any>, enrichedData: Record<string, any>): boolean => {
    if (!originalData || !enrichedData) return false;
    
    // Check for changes in key fields that are commonly adjusted in enrich phase
    const fieldsToCheck = ['fiber', 'knot_size_mm', 'handle_maker', 'brand', 'model'];
    
    return fieldsToCheck.some(field => {
      const original = originalData[field];
      const enriched = enrichedData[field];
      return original !== enriched;
    });
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
          return (
            <div className='text-sm text-gray-900 max-w-xs whitespace-pre-wrap'>{item.original}</div>
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

          // Check if we have matched_data_map and if there are enrich-phase changes
          const hasChanges = matched_data_map && (() => {
            // Create a unique key for this item (using original text as key)
            const itemKey = item.original.toLowerCase();
            const originalData = matched_data_map[itemKey];
            return originalData && hasEnrichPhaseChanges(originalData, item.matched as Record<string, any>);
          })();

          // For brush field, render with line breaks
          if (field === 'brush' && formattedData.includes('\n')) {
            const content = (
              <div className='text-sm text-gray-900 max-w-xs'>
                {formattedData.split('\n').map((line, index) => (
                  <div key={index} className={index > 0 ? 'mt-1' : ''}>
                    {truncateText(line, 60)}
                  </div>
                ))}
              </div>
            );

            if (hasChanges && matched_data_map) {
              const itemKey = item.original.toLowerCase();
              const originalData = matched_data_map[itemKey];
              return (
                <EnrichPhaseTooltip
                  originalData={originalData}
                  enrichedData={item.matched as Record<string, any>}
                  field={field}
                >
                  {content}
                </EnrichPhaseTooltip>
              );
            }

            return content;
          }

          // For other fields, use the original rendering
          const content = (
            <div className='text-sm text-gray-900 max-w-xs'>
              <span>{truncateText(formattedData, 60)}</span>
            </div>
          );

          if (hasChanges && matched_data_map) {
            const itemKey = item.original.toLowerCase();
            const originalData = matched_data_map[itemKey];
            return (
              <EnrichPhaseTooltip
                originalData={originalData}
                enrichedData={item.matched as Record<string, any>}
                field={field}
              >
                {content}
              </EnrichPhaseTooltip>
            );
          }

          return content;
        },
      },
      {
        accessorKey: 'match_type',
        header: 'Match Type',
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

      // Always show brush pattern column
      baseColumns.push({
        accessorKey: 'brush_pattern',
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
                🔗 split<br />
                handle: {truncateText(handleText, 30)}<br />
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
          accessorKey: 'handle',
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
          accessorKey: 'handle_pattern',
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
          accessorKey: 'knot',
          header: 'Knot',
          cell: ({ row }: { row: Row<MismatchItem> }) => {
            const item = row.original;
            // For split brushes, show the matched knot data
            const knotText = formatBrushComponent(item.matched, 'knot');
            return (
              <div className='text-sm text-gray-900 max-w-xs'>
                {truncateText(knotText, 50)}
              </div>
            );
          },
        },
        {
          accessorKey: 'knot_pattern',
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
  }, [
    onCommentClick,
    commentLoading,
    selectedItems,
    onItemSelection,
    isItemConfirmed,
    field,
  ]);

  return (
    <div className='space-y-4'>
      <DataTable
        key={`mismatch-table-${data.length}`} // Force re-render when data changes
        columns={columns}
        data={data}
        showPagination={true}
        resizable={true}
        sortable={true}
        showColumnVisibility={true}
        searchKey='original'
        initialPageSize={50}
        onVisibleRowsChange={onVisibleRowsChange}
      />
    </div>
  );
};

export default MismatchAnalyzerDataTable;
