import React, { useMemo } from 'react';
import { DataTable } from '@/components/ui/data-table';
import { Checkbox } from '@/components/ui/checkbox';
import { CommentDisplay } from '../domain/CommentDisplay';

export interface BrushTableProps {
  items: BrushData[];
  onBrushFilter: (itemName: string, isFiltered: boolean) => void;
  onComponentFilter: (componentName: string, isFiltered: boolean) => void;
  filteredStatus?: Record<string, boolean>;
  pendingChanges?: Record<string, boolean>;
  columnWidths?: Record<string, number>;
  onCommentClick?: (commentId: string) => void;
  commentLoading?: boolean;
}

interface BrushData {
  main: {
    brush: string;
    count: number;
    comment_ids?: string[];
    examples?: string[];
  };
  components: {
    handle?: {
      maker: string;
      count: number;
      comment_ids?: string[];
    };
    knot?: {
      maker: string;
      count: number;
      comment_ids?: string[];
    };
  };
}

const flattenBrushData = (
  items: BrushData[],
  filteredStatus: Record<string, boolean> = {}
): Array<{
  main: BrushData['main'];
  components: BrushData['components'];
  type: 'main' | 'handle' | 'knot';
  parentText?: string;
  isParentFiltered?: boolean;
}> => {
  const flattened: Array<{
    main: BrushData['main'];
    components: BrushData['components'];
    type: 'main' | 'handle' | 'knot';
    parentText?: string;
    isParentFiltered?: boolean;
  }> = [];

  items.forEach(item => {
    const isParentFiltered = filteredStatus[item.main.brush] || false;

    // Add main brush row
    flattened.push({
      main: item.main,
      components: item.components,
      type: 'main',
      isParentFiltered,
    });

    // Add handle component row if exists
    if (item.components.handle) {
      flattened.push({
        main: item.main,
        components: item.components,
        type: 'handle',
        parentText: item.main.brush,
        isParentFiltered,
      });
    }

    // Add knot component row if exists
    if (item.components.knot) {
      flattened.push({
        main: item.main,
        components: item.components,
        type: 'knot',
        parentText: item.main.brush,
        isParentFiltered,
      });
    }
  });

  return flattened;
};

const BrushTable: React.FC<BrushTableProps> = ({
  items,
  onBrushFilter,
  onComponentFilter,
  filteredStatus = {},
  onCommentClick,
  commentLoading = false,
}) => {
  const flattenedData = useMemo(
    () => flattenBrushData(items, filteredStatus),
    [items, filteredStatus]
  );

  const columns = useMemo(
    () => [
      {
        accessorKey: 'brush',
        header: 'Brush',
        cell: ({ row }) => {
          const item = row.original;
          const isMain = item.type === 'main';
          const brushName = item.main.brush;
          const isParentFiltered = item.isParentFiltered;

          if (isMain) {
            return (
              <div className='flex items-center space-x-2'>
                <Checkbox
                  checked={filteredStatus[brushName] || false}
                  onCheckedChange={checked => onBrushFilter(brushName, checked as boolean)}
                  className='data-[state=checked]:bg-blue-600 data-[state=checked]:border-blue-600'
                />
                <span className={isParentFiltered ? 'text-gray-400' : ''}>{brushName}</span>
              </div>
            );
          }

          return <div className='ml-6'>-</div>;
        },
      },
      {
        accessorKey: 'handle',
        header: 'Handle',
        cell: ({ row }) => {
          const item = row.original;
          const isHandle = item.type === 'handle';
          const handle = item.components.handle;
          const isParentFiltered = item.isParentFiltered;

          if (isHandle && handle) {
            return (
              <div className='flex items-center space-x-2'>
                <Checkbox
                  checked={filteredStatus[`${item.main.brush}_handle_${handle.maker}`] || false}
                  onCheckedChange={checked =>
                    onComponentFilter(
                      `${item.main.brush}_handle_${handle.maker}`,
                      checked as boolean
                    )
                  }
                  className='data-[state=checked]:bg-blue-600 data-[state=checked]:border-blue-600'
                />
                <span className={isParentFiltered ? 'text-gray-400' : ''}>{handle.maker}</span>
              </div>
            );
          }

          return <div className='ml-6'>-</div>;
        },
      },
      {
        accessorKey: 'knot',
        header: 'Knot',
        cell: ({ row }) => {
          const item = row.original;
          const isKnot = item.type === 'knot';
          const knot = item.components.knot;
          const isParentFiltered = item.isParentFiltered;

          if (isKnot && knot) {
            return (
              <div className='flex items-center space-x-2'>
                <Checkbox
                  checked={filteredStatus[`${item.main.brush}_knot_${knot.maker}`] || false}
                  onCheckedChange={checked =>
                    onComponentFilter(`${item.main.brush}_knot_${knot.maker}`, checked as boolean)
                  }
                  className='data-[state=checked]:bg-blue-600 data-[state=checked]:border-blue-600'
                />
                <span className={isParentFiltered ? 'text-gray-400' : ''}>{knot.maker}</span>
              </div>
            );
          }

          return <div className='ml-6'>-</div>;
        },
      },
      {
        accessorKey: 'count',
        header: 'Count',
        cell: ({ row }) => {
          const item = row.original;
          const isMain = item.type === 'main';
          const count = item.main.count;
          const isParentFiltered = item.isParentFiltered;

          if (isMain) {
            return <div className={isParentFiltered ? 'text-gray-400' : ''}>{count}</div>;
          }

          return <div className='ml-6'>-</div>;
        },
      },
      {
        accessorKey: 'comment_ids',
        header: 'Comment IDs',
        cell: ({ row }) => {
          const item = row.original;
          const isMain = item.type === 'main';
          const commentIds = item.main.comment_ids;
          const isParentFiltered = item.isParentFiltered;

          if (isMain && commentIds && commentIds.length > 0) {
            return (
              <div className={isParentFiltered ? 'text-gray-400' : ''}>
                <CommentDisplay
                  commentIds={commentIds}
                  onCommentClick={onCommentClick}
                  commentLoading={commentLoading}
                  maxDisplay={3}
                />
              </div>
            );
          }

          return <div className='ml-6'>-</div>;
        },
      },
      {
        accessorKey: 'examples',
        header: 'Examples',
        cell: ({ row }) => {
          const item = row.original;
          const isMain = item.type === 'main';
          const examples = item.main.examples;
          const isParentFiltered = item.isParentFiltered;

          if (isMain && examples && examples.length > 0) {
            return (
              <div className={isParentFiltered ? 'text-gray-400' : ''}>
                <div className='text-sm text-gray-600'>
                  {examples.slice(0, 2).join(', ')}
                  {examples.length > 2 && ` +${examples.length - 2} more`}
                </div>
              </div>
            );
          }

          return <div className='ml-6'>-</div>;
        },
      },
    ],
    [filteredStatus, onBrushFilter, onComponentFilter, onCommentClick, commentLoading]
  );

  return (
    <div className='space-y-4'>
      {/* DataTable with ShadCN foundation */}
      <DataTable
        columns={columns}
        data={flattenedData}
        resizable={true}
        showColumnVisibility={true}
        searchKey='brush'
      />
    </div>
  );
};

export default BrushTable;
