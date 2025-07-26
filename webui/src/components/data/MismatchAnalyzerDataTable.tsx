import React, { useMemo } from 'react';
import { ColumnDef } from '@tanstack/react-table';
import { DataTable } from '@/components/ui/data-table';
import { CommentList } from '../domain/CommentList';
import { MismatchItem } from '../../services/api';

interface MismatchAnalyzerDataTableProps {
  data: MismatchItem[];
  onCommentClick?: (commentId: string) => void;
  commentLoading?: boolean;
  selectedItems?: Set<string>;
  onItemSelection?: (itemKey: string, selected: boolean) => void;
  isItemConfirmed?: (item: MismatchItem) => boolean;
}

const MismatchAnalyzerDataTable: React.FC<MismatchAnalyzerDataTableProps> = ({
  data,
  onCommentClick,
  commentLoading,
  selectedItems = new Set(),
  onItemSelection,
  isItemConfirmed,
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
      default:
        return 'text-gray-600';
    }
  };

  const truncateText = (text: string, maxLength: number = 50) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  const formatMatchedData = (matched: unknown) => {
    if (!matched) return 'N/A';

    if (typeof matched === 'string') {
      return matched;
    }

    if (typeof matched === 'object' && matched !== null) {
      const matchedObj = matched as Record<string, unknown>;
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

  const columns = useMemo<ColumnDef<MismatchItem>[]>(
    () => [
      // Selection column
      ...(onItemSelection ? [{
        id: 'selection',
        header: 'Select',
        cell: ({ row }) => {
          const item = row.original;
          const itemKey = `${item.original}|${JSON.stringify(item.matched)}`;
          const isSelected = selectedItems.has(itemKey);

          return (
            <input
              type="checkbox"
              checked={isSelected}
              onChange={(e) => onItemSelection(itemKey, e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
          );
        },
      }] : []),
      // Status column
      ...(isItemConfirmed ? [{
        id: 'status',
        header: 'Status',
        cell: ({ row }) => {
          const item = row.original;
          const isConfirmed = isItemConfirmed(item);

          return (
            <div className="flex items-center">
              {isConfirmed ? (
                <span className="inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                  ✅ Confirmed
                </span>
              ) : (
                <span className="inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">
                  ⚠️ Unconfirmed
                </span>
              )}
            </div>
          );
        },
      }] : []),
      {
        accessorKey: 'count',
        header: 'Count',
        cell: ({ row }) => {
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
        cell: ({ row }) => {
          const item = row.original;
          return (
            <div className='flex items-center'>
              <span className='text-lg mr-2'>{getMismatchTypeIcon(item.mismatch_type)}</span>
              <span className={`text-sm font-medium ${getMismatchTypeColor(item.mismatch_type)}`}>
                {item.mismatch_type?.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) ||
                  'Unknown'}
              </span>
            </div>
          );
        },
      },
      {
        accessorKey: 'original',
        header: 'Original',
        cell: ({ row }) => {
          const item = row.original;
          return (
            <div className='text-sm text-gray-900 max-w-xs'>{truncateText(item.original, 60)}</div>
          );
        },
      },
      {
        accessorKey: 'match_type',
        header: 'Match Type',
        cell: ({ row }) => {
          const item = row.original;
          return (
            <span className='inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800'>
              {item.match_type}
            </span>
          );
        },
      },
      {
        accessorKey: 'matched',
        header: 'Matched',
        cell: ({ row }) => {
          const item = row.original;
          return (
            <div className='text-sm text-gray-900 max-w-xs'>
              {truncateText(formatMatchedData(item.matched), 60)}
            </div>
          );
        },
      },
      {
        accessorKey: 'pattern',
        header: 'Pattern',
        cell: ({ row }) => {
          const item = row.original;
          return (
            <div className='text-sm text-gray-500 max-w-xs font-mono'>
              {truncateText(item.pattern, 40)}
            </div>
          );
        },
      },
      {
        accessorKey: 'confidence',
        header: 'Confidence',
        cell: ({ row }) => {
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
        cell: ({ row }) => {
          const item = row.original;
          const commentIds = item.comment_ids || [];

          return (
            <CommentList
              commentIds={commentIds}
              onCommentClick={onCommentClick}
              commentLoading={commentLoading}
              maxDisplay={3}
              aria-label={`${commentIds.length} comment${commentIds.length !== 1 ? 's' : ''} available`}
            />
          );
        },
      },
    ],
    [onCommentClick, commentLoading, selectedItems, onItemSelection, isItemConfirmed]
  );

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
      />
    </div>
  );
};

export default MismatchAnalyzerDataTable;
