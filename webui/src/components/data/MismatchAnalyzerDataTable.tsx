import React, { useMemo } from 'react';
import { ColumnDef } from '@tanstack/react-table';
import { DataTable } from '@/components/ui/data-table';
import { MismatchItem } from '../../services/api';

interface MismatchAnalyzerDataTableProps {
  data: MismatchItem[];
  onCommentClick?: (commentId: string) => void;
  commentLoading?: boolean;
}

const MismatchAnalyzerDataTable: React.FC<MismatchAnalyzerDataTableProps> = ({
  data,
  onCommentClick,
  commentLoading = false,
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

  const formatMatchedData = (matched: any) => {
    if (!matched) return 'N/A';

    if (typeof matched === 'string') {
      return matched;
    }

    if (typeof matched === 'object') {
      const parts = [];
      if (matched.brand) parts.push(matched.brand);
      if (matched.model) parts.push(matched.model);
      if (matched.format) parts.push(matched.format);
      if (matched.maker) parts.push(matched.maker);
      if (matched.scent) parts.push(matched.scent);

      return parts.length > 0 ? parts.join(' - ') : JSON.stringify(matched);
    }

    return String(matched);
  };

  const columns = useMemo<ColumnDef<MismatchItem>[]>(
    () => [
      {
        accessorKey: 'mismatch_type',
        header: 'Type',
        cell: ({ row }) => {
          const item = row.original;
          return (
            <div className='flex items-center'>
              <span className='text-lg mr-2'>{getMismatchTypeIcon(item.mismatch_type)}</span>
              <span
                className={`text-sm font-medium ${getMismatchTypeColor(item.mismatch_type)}`}
              >
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
            <div className='text-sm text-gray-900 max-w-xs'>
              {truncateText(item.original, 60)}
            </div>
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
        accessorKey: 'count',
        header: 'Count',
        cell: ({ row }) => {
          const item = row.original;
          return <span className='text-sm text-gray-900'>{item.count}</span>;
        },
      },
      {
        accessorKey: 'examples',
        header: 'Examples',
        cell: ({ row }) => {
          const item = row.original;
          return (
            <div className='text-sm text-gray-900'>
              {item.examples.length > 0 && (
                <button
                  onClick={() => onCommentClick?.(item.comment_ids[0])}
                  disabled={commentLoading}
                  className='text-blue-600 hover:text-blue-800 underline disabled:opacity-50'
                >
                  {commentLoading ? 'Loading...' : 'View'}
                </button>
              )}
            </div>
          );
        },
      },
    ],
    [onCommentClick, commentLoading]
  );

  return (
    <div className='space-y-4'>
      <DataTable
        columns={columns}
        data={data}
        showPagination={true}
        resizable={true}
        showColumnVisibility={true}
        searchKey='original'
      />
    </div>
  );
};

export default MismatchAnalyzerDataTable;
