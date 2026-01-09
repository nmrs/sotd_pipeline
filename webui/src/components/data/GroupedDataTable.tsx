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
}) => {
  // Sorting state
  const [sorting, setSorting] = useState<SortingState>([]);

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
          return (
            <div className="font-medium text-gray-900">
              {item.matched_string || 'N/A'}
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
    />
  );
};

export default GroupedDataTable;
