import React, { useMemo } from 'react';
import { DataTable } from '@/components/ui/data-table';
import { CommentDisplay } from '@/components/domain/CommentDisplay';
import { FormatCompatibilityResult } from '@/services/api';

interface FormatCompatibilityTableProps {
  data: FormatCompatibilityResult[];
  onCommentClick: (commentId: string, allCommentIds?: string[]) => void;
  commentLoading?: boolean;
}

const FormatCompatibilityTable: React.FC<FormatCompatibilityTableProps> = ({
  data,
  onCommentClick,
  commentLoading = false,
}) => {
  const columns = useMemo(() => {
    return [
      {
        accessorKey: 'razor',
        header: 'Razor',
        cell: ({ row }: { row: { original: FormatCompatibilityResult } }) => {
          const item = row.original;
          const razorParts = [];
          if (item.razor_matched.brand) razorParts.push(item.razor_matched.brand);
          if (item.razor_matched.model) razorParts.push(item.razor_matched.model);
          
          // Use enriched format if available, otherwise matched format
          const razorFormat = item.razor_enriched?.format || item.razor_matched.format || '';
          if (razorFormat) razorParts.push(razorFormat);

          return (
            <div className="space-y-1">
              <div className="text-sm text-gray-900 font-medium">{item.razor_original}</div>
              <div className="text-xs text-gray-600">
                {razorParts.length > 0 ? razorParts.join(' - ') : 'N/A'}
              </div>
            </div>
          );
        },
      },
      {
        accessorKey: 'blade',
        header: 'Blade',
        cell: ({ row }: { row: { original: FormatCompatibilityResult } }) => {
          const item = row.original;
          const bladeParts = [];
          if (item.blade_matched.brand) bladeParts.push(item.blade_matched.brand);
          if (item.blade_matched.model) bladeParts.push(item.blade_matched.model);
          if (item.blade_matched.format) bladeParts.push(item.blade_matched.format);

          return (
            <div className="space-y-1">
              <div className="text-sm text-gray-900 font-medium">{item.blade_original}</div>
              <div className="text-xs text-gray-600">
                {bladeParts.length > 0 ? bladeParts.join(' - ') : 'N/A'}
              </div>
            </div>
          );
        },
      },
      {
        accessorKey: 'issue',
        header: 'Issue',
        cell: ({ row }: { row: { original: FormatCompatibilityResult } }) => {
          const item = row.original;
          const severityClass =
            item.severity === 'error'
              ? 'bg-red-100 text-red-800 border-red-200'
              : 'bg-yellow-100 text-yellow-800 border-yellow-200';

          return (
            <div className="space-y-1">
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${severityClass}`}
              >
                {item.severity === 'error' ? 'Error' : 'Warning'}
              </span>
              <div className="text-sm text-gray-900">{item.issue_type}</div>
            </div>
          );
        },
      },
      {
        accessorKey: 'count',
        header: 'Count',
        cell: ({ row }: { row: { original: FormatCompatibilityResult } }) => {
          return (
            <span className="text-sm text-gray-900 font-medium">{row.original.count}</span>
          );
        },
      },
      {
        accessorKey: 'comment_ids',
        header: 'Comments',
        cell: ({ row }: { row: { original: FormatCompatibilityResult } }) => {
          const item = row.original;
          return (
            <CommentDisplay
              commentIds={item.comment_ids}
              onCommentClick={(commentId) => onCommentClick(commentId, item.comment_ids)}
              commentLoading={commentLoading}
            />
          );
        },
      },
    ];
  }, [onCommentClick, commentLoading]);

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center p-8 text-gray-500">
        <p>No format compatibility issues found</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <DataTable
        columns={columns}
        data={data}
        resizable={true}
        sortable={true}
        showColumnVisibility={true}
        searchKey="razor_original"
        showPagination={true}
        initialPageSize={50}
      />
    </div>
  );
};

export default FormatCompatibilityTable;

