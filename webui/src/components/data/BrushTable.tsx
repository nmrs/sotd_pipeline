import React, { useMemo } from 'react';
import { ColumnDef } from '@tanstack/react-table';
import { DataTable } from '@/components/ui/data-table';
import FilteredEntryCheckbox from '../forms/FilteredEntryCheckbox';
import { BrushData } from '../../utils/brushDataTransformer';

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

// Flatten brush data for DataTable while preserving component information
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
    const isMainFiltered = filteredStatus[item.main.text] || false;

    // Add main brush row
    flattened.push({
      main: item.main,
      components: item.components,
      type: 'main',
    });

    // Always add component sub-rows, but mark them as dimmed if parent is filtered
    if (item.components.handle) {
      flattened.push({
        main: item.main,
        components: item.components,
        type: 'handle',
        parentText: item.main.text,
        isParentFiltered: isMainFiltered,
      });
    }
    if (item.components.knot) {
      flattened.push({
        main: item.main,
        components: item.components,
        type: 'knot',
        parentText: item.main.text,
        isParentFiltered: isMainFiltered,
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
  // Handle null/undefined items gracefully
  const safeItems = useMemo(() => items || [], [items]);

  // Flatten brush data for DataTable
  const flattenedData = useMemo(() => {
    return flattenBrushData(safeItems, filteredStatus);
  }, [safeItems, filteredStatus]);

  // Create columns for DataTable using TanStack Table ColumnDef
  const columns: ColumnDef<ReturnType<typeof flattenBrushData>[0]>[] = useMemo(
    () => [
      {
        accessorKey: 'filtered',
        header: 'Filtered',
        cell: ({ row }) => {
          const item = row.original;
          const isMain = item.type === 'main';
          const text = isMain ? item.main.text : item.parentText || '';
          const isFiltered = filteredStatus[text] || false;

          return (
            <div className='flex items-center justify-center'>
              <FilteredEntryCheckbox
                itemName={text}
                commentIds={item.main.comment_ids || []}
                isFiltered={isFiltered}
                onStatusChange={checked => {
                  if (isMain) {
                    onBrushFilter(text, checked);
                  } else {
                    onComponentFilter(text, checked);
                  }
                }}
                uniqueId={isMain ? 'main' : item.type}
              />
            </div>
          );
        },
      },
      {
        accessorKey: 'brush',
        header: 'Brush',
        cell: ({ row }) => {
          const item = row.original;
          const isMain = item.type === 'main';
          const text = isMain ? item.main.text : item.parentText || '';
          const isParentFiltered = item.isParentFiltered;

          return (
            <div className={`${isParentFiltered ? 'text-gray-400' : ''} ${!isMain ? 'ml-6' : ''}`}>
              {text}
            </div>
          );
        },
      },
      {
        accessorKey: 'handle',
        header: 'Handle',
        cell: ({ row }) => {
          const item = row.original;
          const isMain = item.type === 'main';
          const handle = item.components.handle;
          const isParentFiltered = item.isParentFiltered;

          if (isMain) {
            return (
              <div className={isParentFiltered ? 'text-gray-400' : ''}>
                {typeof handle === 'string' ? handle : handle?.text || '-'}
              </div>
            );
          }

          if (item.type === 'handle') {
            return (
              <div className={`${isParentFiltered ? 'text-gray-400' : ''} ml-6`}>
                {typeof handle === 'string' ? handle : handle?.text || '-'}
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
          const isMain = item.type === 'main';
          const knot = item.components.knot;
          const isParentFiltered = item.isParentFiltered;

          if (isMain) {
            return (
              <div className={isParentFiltered ? 'text-gray-400' : ''}>
                {typeof knot === 'string' ? knot : knot?.text || '-'}
              </div>
            );
          }

          if (item.type === 'knot') {
            return (
              <div className={`${isParentFiltered ? 'text-gray-400' : ''} ml-6`}>
                {typeof knot === 'string' ? knot : knot?.text || '-'}
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
                <div className='flex flex-wrap gap-1'>
                  {commentIds.slice(0, 3).map(id => (
                    <button
                      key={id}
                      onClick={() => onCommentClick?.(id)}
                      disabled={commentLoading}
                      className='px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded hover:bg-blue-200 disabled:opacity-50'
                    >
                      {id}
                    </button>
                  ))}
                  {commentIds.length > 3 && (
                    <span className='text-xs text-gray-500'>+{commentIds.length - 3} more</span>
                  )}
                </div>
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
