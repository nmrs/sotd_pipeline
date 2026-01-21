import React, { useMemo, useState, useCallback } from 'react';
import { ColumnDef, Row, SortingState } from '@tanstack/react-table';
import { DataTable } from '@/components/ui/data-table';
import { GroupedDataItem, AnalyzerDataItem, isGroupedDataItem } from '../../services/api';
import ExpandablePatterns from '../ui/ExpandablePatterns';

interface GroupedDataTableProps {
  data: GroupedDataItem[];
  field: string;
  onCommentClick?: (commentId: string) => void;
  commentLoading?: boolean;
  selectedItems?: Set<string>;
  onItemSelection?: (itemId: string, selected: boolean) => void;
  isItemConfirmed?: (itemId: string) => boolean;
  onVisibleRowsChange?: (rows: AnalyzerDataItem[]) => void;
  onBrushSplitClick?: (item: any) => void;
  activeRowIndex?: number;
  keyboardNavigationEnabled?: boolean;
  sorting?: SortingState;
  onSortingChange?: (sorting: SortingState) => void;
  globalFilter?: string;
  onGlobalFilterChange?: (value: string) => void;
  useRegexMode?: boolean;
  onUseRegexModeChange?: (value: boolean) => void;
}

const GroupedDataTable: React.FC<GroupedDataTableProps> = ({
  data,
  field,
  onCommentClick,
  commentLoading,
  selectedItems = new Set(),
  onItemSelection,
  isItemConfirmed,
  onVisibleRowsChange,
  onBrushSplitClick,
  activeRowIndex = -1,
  keyboardNavigationEnabled = false,
  sorting: externalSorting,
  onSortingChange,
  globalFilter: externalGlobalFilter,
  onGlobalFilterChange,
  useRegexMode: externalUseRegexMode,
  onUseRegexModeChange,
}) => {
  // Sorting state - use external if provided, otherwise internal
  const [internalSorting, setInternalSorting] = useState<SortingState>([]);
  const sorting = externalSorting !== undefined ? externalSorting : internalSorting;
  const setSorting = onSortingChange || setInternalSorting;

  const columns = useMemo(() => {
    const baseColumns: ColumnDef<GroupedDataItem>[] = [
      // Selection column
      {
        id: 'select',
        header: ({ table }) => (
          <input
            type="checkbox"
            checked={table.getIsAllPageRowsSelected()}
            onChange={e => table.toggleAllPageRowsSelected(!!e.target.checked)}
            className="rounded border-gray-300"
          />
        ),
        cell: ({ row }) => {
          const item = row.original;
          // Generate key using same logic as MatchAnalyzer
          const itemKey = `${field}:${item.matched_string?.toLowerCase() || 'unknown'}`;
          const isSelected = selectedItems.has(itemKey);
          return (
            <input
              type="checkbox"
              checked={isSelected}
              onChange={e => {
                onItemSelection?.(itemKey, e.target.checked);
              }}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
          );
        },
        enableSorting: false,
        enableHiding: false,
      },
      // Matched String column (the group key)
      {
        id: 'matched_string',
        header: 'Matched',
        accessorKey: 'matched_string',
        sortingFn: (rowA, rowB) => {
          const a = rowA.original.matched_string;
          const b = rowB.original.matched_string;
          return a.localeCompare(b);
        },
        cell: ({ row }: { row: Row<GroupedDataItem> }) => {
          const item = row.original;
          const isNonCountable = item.countable === false;
          
          return (
            <div className="font-medium text-gray-900 flex items-center gap-2">
              <span>{item.matched_string || 'N/A'}</span>
              {isNonCountable && (
                <span
                  className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800 border border-amber-200"
                  title="This scent does not count toward distinct scent aggregation (mashup/mix)"
                >
                  <svg
                    className="w-3 h-3 mr-1"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                    />
                  </svg>
                  Mashup
                </span>
              )}
            </div>
          );
        },
      },
      // Total Count column
      {
        id: 'total_count',
        header: 'Count',
        accessorKey: 'total_count',
        sortingFn: (rowA, rowB) => {
          const a = rowA.original.total_count;
          const b = rowB.original.total_count;
          return a - b;
        },
        cell: ({ row }: { row: Row<GroupedDataItem> }) => {
          const item = row.original;
          return (
            <div className="text-center font-medium text-gray-900">
              {item.total_count ?? 0}
            </div>
          );
        },
      },
      // Pattern Count column
      {
        id: 'pattern_count',
        header: 'Patterns',
        accessorKey: 'pattern_count',
        sortingFn: (rowA, rowB) => {
          const a = rowA.original.pattern_count;
          const b = rowB.original.pattern_count;
          return a - b;
        },
        cell: ({ row }: { row: Row<GroupedDataItem> }) => {
          const item = row.original;
          return (
            <div className="text-center text-gray-600">
              {item.pattern_count ?? 0}
            </div>
          );
        },
      },
      // Top Patterns column
      {
        id: 'top_patterns',
        header: 'Top Patterns',
        cell: ({ row }: { row: Row<GroupedDataItem> }) => {
          const item = row.original;
          try {
            return (
              <ExpandablePatterns
                topPatterns={item.top_patterns || []}
                allPatterns={item.all_patterns || []}
                remainingCount={item.remaining_count || 0}
              />
            );
          } catch (error) {
            return <div className="text-red-500">Error rendering patterns</div>;
          }
        },
        enableSorting: false,
      },
    ];

    return baseColumns;
  }, [field, selectedItems, onItemSelection]);

  // Convert GroupedDataItem[] to AnalyzerDataItem[] for compatibility
  const compatibleData = useMemo(() => {
    return data.map(item => ({
      ...item,
      is_grouped: true,
    })) as AnalyzerDataItem[];
  }, [data]);

  return (
    <DataTable
      data={compatibleData}
      columns={columns}
      searchKey="search"
      onVisibleRowsChange={onVisibleRowsChange}
      sorting={sorting}
      onSortingChange={setSorting}
      keyboardNavigationEnabled={keyboardNavigationEnabled}
      activeRowIndex={activeRowIndex}
      showPagination={true}
      globalFilter={externalGlobalFilter}
      onGlobalFilterChange={onGlobalFilterChange}
      useRegexMode={externalUseRegexMode}
      onUseRegexModeChange={onUseRegexModeChange}
    />
  );
};

export default GroupedDataTable;
