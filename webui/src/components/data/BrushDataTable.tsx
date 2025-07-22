'use client';

import React, { useState, useCallback } from 'react';
import { ColumnDef } from '@tanstack/react-table';
import { DataTable } from '@/components/ui/data-table';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';

// Interface for brush data with subrows
interface BrushData {
  id: string;
  brand: string;
  model: string;
  handle_maker?: string;
  knot_maker?: string;
  fiber?: string;
  knot_size?: string;
  subrows?: BrushData[];
  expanded?: boolean;
}

interface BrushDataTableProps {
  brushData: BrushData[];
  onRowClick?: (brush: BrushData) => void;
  onSubrowToggle?: (brushId: string, expanded: boolean) => void;
  showSubrows?: boolean;
}

export function BrushDataTable({
  brushData,
  onRowClick,
  onSubrowToggle,
  showSubrows = true,
}: BrushDataTableProps) {
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  // Handle subrow toggle
  const handleSubrowToggle = useCallback(
    (brushId: string) => {
      const newExpanded = new Set(expandedRows);
      if (newExpanded.has(brushId)) {
        newExpanded.delete(brushId);
      } else {
        newExpanded.add(brushId);
      }
      setExpandedRows(newExpanded);

      if (onSubrowToggle) {
        onSubrowToggle(brushId, newExpanded.has(brushId));
      }
    },
    [expandedRows, onSubrowToggle]
  );

  // Handle row click
  const handleRowClick = useCallback(
    (brush: BrushData) => {
      if (onRowClick) {
        onRowClick(brush);
      }
    },
    [onRowClick]
  );

  // Transform data to include expanded state and flatten subrows
  const transformedData = brushData.flatMap(brush => {
    // Skip null or undefined entries
    if (!brush) {
      return [];
    }

    const rows = [{ ...brush, isMainRow: true }];

    if (brush.subrows && expandedRows.has(brush.id)) {
      rows.push(
        ...brush.subrows.map(subrow => ({ ...subrow, isMainRow: false, parentId: brush.id }))
      );
    }

    return rows;
  });

  // Define columns using TanStack Table ColumnDef
  const columns: ColumnDef<BrushData & { isMainRow?: boolean; parentId?: string }>[] = [
    {
      accessorKey: 'brand',
      header: 'Brand',
      cell: ({ row }) => (
        <div
          className='flex items-center space-x-2 cursor-pointer hover:bg-gray-50 p-1 rounded'
          onClick={() => handleRowClick(row.original)}
        >
          {row.original.isMainRow &&
            showSubrows &&
            row.original.subrows &&
            row.original.subrows.length > 0 && (
              <Button
                variant='ghost'
                size='sm'
                onClick={e => {
                  e.stopPropagation();
                  handleSubrowToggle(row.original.id);
                }}
                className='p-0 h-4 w-4'
              >
                {expandedRows.has(row.original.id) ? (
                  <ChevronDown className='h-3 w-3' />
                ) : (
                  <ChevronRight className='h-3 w-3' />
                )}
              </Button>
            )}
          <span className={!row.original.isMainRow ? 'ml-6' : ''}>{row.original.brand}</span>
        </div>
      ),
    },
    {
      accessorKey: 'model',
      header: 'Model',
      cell: ({ row }) => (
        <div
          className={`${!row.original.isMainRow ? 'ml-6' : ''} cursor-pointer hover:bg-gray-50 p-1 rounded`}
          onClick={() => handleRowClick(row.original)}
        >
          {row.original.model}
        </div>
      ),
    },
    {
      accessorKey: 'handle_maker',
      header: 'Handle Maker',
      cell: ({ row }) => (
        <div
          className={`${!row.original.isMainRow ? 'ml-6' : ''} cursor-pointer hover:bg-gray-50 p-1 rounded`}
          onClick={() => handleRowClick(row.original)}
        >
          {row.original.handle_maker || '-'}
        </div>
      ),
    },
    {
      accessorKey: 'knot_maker',
      header: 'Knot Maker',
      cell: ({ row }) => (
        <div
          className={`${!row.original.isMainRow ? 'ml-6' : ''} cursor-pointer hover:bg-gray-50 p-1 rounded`}
          onClick={() => handleRowClick(row.original)}
        >
          {row.original.knot_maker || '-'}
        </div>
      ),
    },
    {
      accessorKey: 'fiber',
      header: 'Fiber',
      cell: ({ row }) => (
        <div
          className={`${!row.original.isMainRow ? 'ml-6' : ''} cursor-pointer hover:bg-gray-50 p-1 rounded`}
          onClick={() => handleRowClick(row.original)}
        >
          {row.original.fiber || '-'}
        </div>
      ),
    },
    {
      accessorKey: 'knot_size',
      header: 'Knot Size',
      cell: ({ row }) => (
        <div
          className={`${!row.original.isMainRow ? 'ml-6' : ''} cursor-pointer hover:bg-gray-50 p-1 rounded`}
          onClick={() => handleRowClick(row.original)}
        >
          {row.original.knot_size || '-'}
        </div>
      ),
    },
  ];

  return (
    <div className='space-y-4'>
      {/* DataTable with ShadCN foundation */}
      <DataTable
        columns={columns}
        data={transformedData}
        height={400}
        itemSize={48}
        resizable={true}
        showColumnVisibility={true}
        searchKey='brand'
      />
    </div>
  );
}
