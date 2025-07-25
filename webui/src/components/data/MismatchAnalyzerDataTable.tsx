import React, { useMemo } from 'react';
import { ColumnDef } from '@tanstack/react-table';
import { DataTable } from '@/components/ui/data-table';
import { Button } from '@/components/ui/button';
import { MismatchItem } from '../../services/api';

interface MismatchAnalyzerDataTableProps {
  data: MismatchItem[];
  onCommentClick?: (commentId: string) => void;
  commentLoading?: boolean;
}

const MismatchAnalyzerDataTable: React.FC<MismatchAnalyzerDataTableProps> = ({
  data,
  onCommentClick,
  commentLoading,
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

          if (commentIds.length === 0) {
            return (
              <span
                className='text-gray-400 text-xs'
                role='cell'
                aria-label='No comments available'
              >
                No comments
              </span>
            );
          }

          return (
            <div
              className='space-y-1'
              role='cell'
              aria-label={`${commentIds.length} comment${commentIds.length !== 1 ? 's' : ''} available`}
            >
              {commentIds.slice(0, 3).map((commentId, index) => (
                <Button
                  key={commentId}
                  onClick={() => onCommentClick?.(commentId)}
                  disabled={commentLoading}
                  className='block w-full text-left text-xs text-blue-600 hover:text-blue-800 hover:bg-blue-50 px-2 py-1 rounded'
                  aria-label={`View comment ${index + 1} of ${commentIds.length}`}
                >
                  {commentId}
                </Button>
              ))}
              {commentIds.length > 3 && (
                <span className='text-xs text-gray-500'>+{commentIds.length - 3} more</span>
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
