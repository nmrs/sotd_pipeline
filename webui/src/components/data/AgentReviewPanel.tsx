'use client';

import React, { useState, useMemo, useCallback } from 'react';
import {
  ColumnDef,
  SortingState,
  getCoreRowModel,
  getSortedRowModel,
  getPaginationRowModel,
  useReactTable,
  flexRender,
} from '@tanstack/react-table';

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  VerifiedData,
  ProposedData,
  VerificationItem,
  ProposalItem,
  bulkApproveVerified,
  acceptProposal,
  rejectProposal,
} from '@/services/api';

// --- Props ---

interface AgentReviewPanelProps {
  verifiedData: VerifiedData | null;
  proposedData: ProposedData | null;
  loading: boolean;
  month: string;
  onDataRefresh: () => void;
}

// --- Verdict Badge ---

function VerdictBadge({ verdict }: { verdict: VerificationItem['verdict'] }) {
  switch (verdict) {
    case 'verified':
      return <Badge className='bg-green-100 text-green-800 border-green-300'>verified</Badge>;
    case 'needs_review':
      return <Badge className='bg-amber-100 text-amber-800 border-amber-300'>needs review</Badge>;
    case 'incorrect':
      return <Badge className='bg-red-100 text-red-800 border-red-300'>incorrect</Badge>;
    default:
      return <Badge variant='outline'>{verdict}</Badge>;
  }
}

// --- Proposal Type Badge ---

function ProposalTypeBadge({ type }: { type: ProposalItem['type'] }) {
  switch (type) {
    case 'new_scent':
      return <Badge className='bg-blue-100 text-blue-800 border-blue-300'>new scent</Badge>;
    case 'new_pattern':
      return <Badge className='bg-purple-100 text-purple-800 border-purple-300'>new pattern</Badge>;
    case 'new_product':
      return <Badge className='bg-green-100 text-green-800 border-green-300'>new product</Badge>;
    default:
      return <Badge variant='outline'>{type}</Badge>;
  }
}

// --- Proposal Status Badge ---

function ProposalStatusBadge({ item }: { item: ProposalItem }) {
  if (item._status === 'accepted') {
    return <Badge className='bg-green-100 text-green-800 border-green-300'>accepted</Badge>;
  }
  if (item._status === 'rejected') {
    return <Badge className='bg-red-100 text-red-800 border-red-300'>rejected</Badge>;
  }
  return <Badge className='bg-gray-100 text-gray-800 border-gray-300'>pending</Badge>;
}

// --- Expandable Text ---

function ExpandableText({ text, maxLength = 80 }: { text: string; maxLength?: number }) {
  const [expanded, setExpanded] = useState(false);
  if (text.length <= maxLength) return <span>{text}</span>;
  return (
    <span>
      {expanded ? text : text.slice(0, maxLength) + '...'}
      <button
        onClick={() => setExpanded(!expanded)}
        className='ml-1 text-blue-600 hover:text-blue-800 text-xs'
      >
        {expanded ? 'less' : 'more'}
      </button>
    </span>
  );
}

// --- Matched Display Helper ---

function formatMatched(matched: Record<string, unknown>): string {
  const brand = (matched.brand as string) || '';
  const model = (matched.model as string) || (matched.scent as string) || '';
  if (brand && model) return `${brand} ${model}`;
  if (brand) return brand;
  if (model) return model;
  return JSON.stringify(matched);
}

// ==========================================
// Verifications Tab
// ==========================================

interface VerificationsTableProps {
  verifications: VerificationItem[];
  month: string;
  onDataRefresh: () => void;
}

function VerificationsTable({ verifications, month: _month, onDataRefresh }: VerificationsTableProps) {
  const [sorting, setSorting] = useState<SortingState>([
    { id: 'confidence', desc: false },
  ]);
  const [verdictFilter, setVerdictFilter] = useState<string>('all');
  const [fieldFilter, setFieldFilter] = useState<string>('all');
  const [rowSelection, setRowSelection] = useState<Record<string, boolean>>({});
  const [bulkApproving, setBulkApproving] = useState(false);
  const [approveError, setApproveError] = useState<string | null>(null);

  // Compute summary stats
  const stats = useMemo(() => {
    const verified = verifications.filter(v => v.verdict === 'verified').length;
    const needsReview = verifications.filter(v => v.verdict === 'needs_review').length;
    const incorrect = verifications.filter(v => v.verdict === 'incorrect').length;
    return { verified, needsReview, incorrect, total: verifications.length };
  }, [verifications]);

  // Filter data
  const filteredData = useMemo(() => {
    let data = verifications;
    if (verdictFilter !== 'all') {
      data = data.filter(v => v.verdict === verdictFilter);
    }
    if (fieldFilter !== 'all') {
      data = data.filter(v => v.field === fieldFilter);
    }
    return data;
  }, [verifications, verdictFilter, fieldFilter]);

  // Available fields for filter
  const availableFields = useMemo(() => {
    return [...new Set(verifications.map(v => v.field))].sort();
  }, [verifications]);

  // Column definitions
  const columns = useMemo<ColumnDef<VerificationItem>[]>(
    () => [
      {
        id: 'select',
        header: ({ table }) => (
          <Checkbox
            checked={table.getIsAllPageRowsSelected()}
            onCheckedChange={value => table.toggleAllPageRowsSelected(!!value)}
          />
        ),
        cell: ({ row }) => (
          <Checkbox
            checked={row.getIsSelected()}
            onCheckedChange={value => row.toggleSelected(!!value)}
          />
        ),
        enableSorting: false,
      },
      {
        accessorKey: 'field',
        header: 'Field',
        cell: ({ getValue }) => (
          <span className='capitalize font-medium'>{getValue<string>()}</span>
        ),
      },
      {
        accessorKey: 'original',
        header: 'Original',
        cell: ({ getValue }) => (
          <span className='text-sm font-mono'>{getValue<string>()}</span>
        ),
      },
      {
        id: 'matched_display',
        header: 'Matched',
        accessorFn: row => formatMatched(row.matched),
        cell: ({ getValue }) => (
          <span className='text-sm'>{getValue<string>()}</span>
        ),
      },
      {
        accessorKey: 'match_type',
        header: 'Match Type',
        cell: ({ getValue }) => (
          <Badge variant='outline' className='text-xs'>
            {getValue<string>()}
          </Badge>
        ),
      },
      {
        accessorKey: 'verdict',
        header: 'Verdict',
        cell: ({ getValue }) => <VerdictBadge verdict={getValue<VerificationItem['verdict']>()} />,
      },
      {
        accessorKey: 'confidence',
        header: 'Confidence',
        cell: ({ getValue }) => {
          const val = getValue<number>();
          return <span className='text-sm tabular-nums'>{val.toFixed(2)}</span>;
        },
      },
      {
        accessorKey: 'reasoning',
        header: 'Reasoning',
        cell: ({ getValue }) => <ExpandableText text={getValue<string>()} />,
        enableSorting: false,
      },
    ],
    []
  );

  const table = useReactTable({
    data: filteredData,
    columns,
    state: { sorting, rowSelection },
    onSortingChange: setSorting,
    onRowSelectionChange: setRowSelection,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    enableRowSelection: true,
    initialState: { pagination: { pageSize: 50 } },
  });

  // Bulk approve handler
  const selectedRows = table.getSelectedRowModel().rows;
  const selectedVerified = selectedRows.filter(r => r.original.verdict === 'verified');

  const handleBulkApprove = useCallback(async () => {
    if (selectedVerified.length === 0) return;
    setBulkApproving(true);
    setApproveError(null);

    // Group by field
    const byField: Record<string, Array<{ original: string; matched: Record<string, unknown> }>> = {};
    for (const row of selectedVerified) {
      const item = row.original;
      if (!byField[item.field]) byField[item.field] = [];
      byField[item.field].push({ original: item.original, matched: item.matched });
    }

    try {
      for (const [field, matches] of Object.entries(byField)) {
        await bulkApproveVerified(field, matches);
      }
      setRowSelection({});
      onDataRefresh();
    } catch (err) {
      setApproveError(err instanceof Error ? err.message : 'Failed to approve');
    } finally {
      setBulkApproving(false);
    }
  }, [selectedVerified, onDataRefresh]);

  return (
    <div className='space-y-4'>
      {/* Summary Stats */}
      <div className='flex flex-wrap gap-3 items-center'>
        <span className='text-sm text-gray-600'>
          <span className='font-semibold text-green-700'>{stats.verified}</span> verified
        </span>
        <span className='text-sm text-gray-600'>
          <span className='font-semibold text-amber-700'>{stats.needsReview}</span> need review
        </span>
        <span className='text-sm text-gray-600'>
          <span className='font-semibold text-red-700'>{stats.incorrect}</span> incorrect
        </span>
        <span className='text-sm text-gray-400'>({stats.total} total)</span>
      </div>

      {/* Filters + Actions */}
      <div className='flex flex-wrap gap-3 items-center'>
        <Select value={verdictFilter} onValueChange={setVerdictFilter}>
          <SelectTrigger className='w-[160px]'>
            <SelectValue placeholder='Filter verdict' />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value='all'>All verdicts</SelectItem>
            <SelectItem value='verified'>Verified</SelectItem>
            <SelectItem value='needs_review'>Needs review</SelectItem>
            <SelectItem value='incorrect'>Incorrect</SelectItem>
          </SelectContent>
        </Select>

        <Select value={fieldFilter} onValueChange={setFieldFilter}>
          <SelectTrigger className='w-[140px]'>
            <SelectValue placeholder='Filter field' />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value='all'>All fields</SelectItem>
            {availableFields.map(f => (
              <SelectItem key={f} value={f}>
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {selectedVerified.length > 0 && (
          <Button
            onClick={handleBulkApprove}
            disabled={bulkApproving}
            className='bg-green-600 hover:bg-green-700 text-white'
          >
            {bulkApproving
              ? 'Approving...'
              : `Approve ${selectedVerified.length} verified`}
          </Button>
        )}
        {selectedRows.length > 0 && selectedRows.length !== selectedVerified.length && (
          <span className='text-xs text-amber-600'>
            {selectedRows.length - selectedVerified.length} non-verified item(s) excluded from bulk approve
          </span>
        )}
        {approveError && (
          <span className='text-xs text-red-600'>{approveError}</span>
        )}
      </div>

      {/* Table */}
      <div className='rounded-md border overflow-x-auto'>
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map(headerGroup => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map(header => (
                  <TableHead key={header.id}>
                    {header.isPlaceholder ? null : (
                      <button
                        className={`flex items-center gap-1 ${
                          header.column.getCanSort()
                            ? 'cursor-pointer hover:text-blue-600'
                            : 'cursor-default'
                        }`}
                        onClick={header.column.getToggleSortingHandler()}
                        disabled={!header.column.getCanSort()}
                      >
                        {flexRender(header.column.columnDef.header, header.getContext())}
                        {header.column.getCanSort() && (
                          <span className='ml-1'>
                            {{ asc: '\u2191', desc: '\u2193' }[
                              header.column.getIsSorted() as string
                            ] ?? '\u2195'}
                          </span>
                        )}
                      </button>
                    )}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows.length ? (
              table.getRowModel().rows.map(row => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() && 'selected'}
                >
                  {row.getVisibleCells().map(cell => (
                    <TableCell key={cell.id}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length} className='h-24 text-center'>
                  No verifications match the current filters.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      <div className='flex items-center justify-between'>
        <span className='text-sm text-muted-foreground'>
          {table.getFilteredSelectedRowModel().rows.length} of{' '}
          {table.getFilteredRowModel().rows.length} selected
        </span>
        <div className='flex items-center gap-2'>
          <Button
            variant='outline'
            size='sm'
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            Previous
          </Button>
          <span className='text-sm'>
            Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}
          </span>
          <Button
            variant='outline'
            size='sm'
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  );
}

// ==========================================
// Proposals Tab
// ==========================================

interface ProposalsTableProps {
  proposals: ProposalItem[];
  month: string;
  onDataRefresh: () => void;
}

function ProposalsTable({ proposals, month, onDataRefresh }: ProposalsTableProps) {
  const [showAll, setShowAll] = useState(false);
  const [rejectingIndex, setRejectingIndex] = useState<number | null>(null);
  const [rejectReason, setRejectReason] = useState('');
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  // Filter out already-acted-on proposals unless showAll
  const filteredProposals = useMemo(() => {
    if (showAll) return proposals;
    return proposals.filter(p => !p._status);
  }, [proposals, showAll]);

  const pendingCount = useMemo(
    () => proposals.filter(p => !p._status).length,
    [proposals]
  );

  const handleAccept = useCallback(
    async (proposalIndex: number) => {
      setActionLoading(proposalIndex);
      setActionError(null);
      try {
        await acceptProposal(month, proposalIndex);
        onDataRefresh();
      } catch (err) {
        setActionError(err instanceof Error ? err.message : 'Failed to accept');
      } finally {
        setActionLoading(null);
      }
    },
    [month, onDataRefresh]
  );

  const handleReject = useCallback(
    async (proposalIndex: number) => {
      setActionLoading(proposalIndex);
      setActionError(null);
      try {
        await rejectProposal(month, proposalIndex, rejectReason || undefined);
        setRejectingIndex(null);
        setRejectReason('');
        onDataRefresh();
      } catch (err) {
        setActionError(err instanceof Error ? err.message : 'Failed to reject');
      } finally {
        setActionLoading(null);
      }
    },
    [month, rejectReason, onDataRefresh]
  );

  return (
    <div className='space-y-4'>
      {/* Summary + toggle */}
      <div className='flex flex-wrap gap-3 items-center'>
        <span className='text-sm text-gray-600'>
          <span className='font-semibold'>{pendingCount}</span> pending proposal{pendingCount !== 1 ? 's' : ''}
        </span>
        <span className='text-sm text-gray-400'>({proposals.length} total)</span>
        <label className='flex items-center gap-1 text-sm text-gray-600 ml-auto cursor-pointer'>
          <Checkbox
            checked={showAll}
            onCheckedChange={v => setShowAll(!!v)}
            className='h-4 w-4'
          />
          Show accepted/rejected
        </label>
      </div>

      {actionError && (
        <div className='text-sm text-red-600 bg-red-50 px-3 py-2 rounded'>{actionError}</div>
      )}

      {/* Proposals list */}
      <div className='space-y-3'>
        {filteredProposals.length === 0 ? (
          <div className='text-center py-8 text-gray-500'>
            {proposals.length === 0
              ? 'No proposals generated.'
              : 'All proposals have been reviewed.'}
          </div>
        ) : (
          filteredProposals.map((proposal, _idx) => {
            // Find the real index in the original proposals array
            const realIndex = proposals.indexOf(proposal);
            return (
              <ProposalCard
                key={realIndex}
                proposal={proposal}
                index={realIndex}
                onAccept={handleAccept}
                onReject={handleReject}
                rejectingIndex={rejectingIndex}
                setRejectingIndex={setRejectingIndex}
                rejectReason={rejectReason}
                setRejectReason={setRejectReason}
                actionLoading={actionLoading}
              />
            );
          })
        )}
      </div>
    </div>
  );
}

// --- Proposal Card ---

interface ProposalCardProps {
  proposal: ProposalItem;
  index: number;
  onAccept: (index: number) => void;
  onReject: (index: number) => void;
  rejectingIndex: number | null;
  setRejectingIndex: (index: number | null) => void;
  rejectReason: string;
  setRejectReason: (reason: string) => void;
  actionLoading: number | null;
}

function ProposalCard({
  proposal,
  index,
  onAccept,
  onReject,
  rejectingIndex,
  setRejectingIndex,
  rejectReason,
  setRejectReason,
  actionLoading,
}: ProposalCardProps) {
  const isActedOn = !!proposal._status;
  const isLoading = actionLoading === index;

  return (
    <div
      className={`border rounded-lg p-4 ${
        isActedOn ? 'bg-gray-50 opacity-75' : 'bg-white'
      }`}
    >
      <div className='flex flex-wrap gap-2 items-center mb-2'>
        <ProposalTypeBadge type={proposal.type} />
        <span className='capitalize text-sm font-medium text-gray-700'>{proposal.field}</span>
        <ProposalStatusBadge item={proposal} />
        <span className='text-sm text-gray-500 ml-auto tabular-nums'>
          Confidence: {proposal.confidence.toFixed(2)}
        </span>
      </div>

      <div className='grid grid-cols-1 md:grid-cols-2 gap-3 text-sm'>
        <div>
          <span className='text-gray-500'>Brand:</span>{' '}
          <span className='font-medium'>{proposal.brand}</span>
        </div>
        <div>
          <span className='text-gray-500'>Model/Scent:</span>{' '}
          <span className='font-medium'>{proposal.model}</span>
        </div>
        {proposal.suggested_pattern && (
          <div className='md:col-span-2'>
            <span className='text-gray-500'>Suggested pattern:</span>{' '}
            <code className='bg-gray-100 px-2 py-0.5 rounded text-xs font-mono'>
              {proposal.suggested_pattern}
            </code>
          </div>
        )}
        {proposal.research && (
          <div className='md:col-span-2'>
            <span className='text-gray-500'>Research:</span>{' '}
            <ExpandableText text={proposal.research} maxLength={120} />
          </div>
        )}
        {proposal.source_url && (
          <div className='md:col-span-2'>
            <span className='text-gray-500'>Source:</span>{' '}
            <a
              href={proposal.source_url}
              target='_blank'
              rel='noopener noreferrer'
              className='text-blue-600 hover:text-blue-800 underline text-xs'
            >
              {proposal.source_url}
            </a>
          </div>
        )}
        {proposal.evidence.length > 0 && (
          <div className='md:col-span-2'>
            <span className='text-gray-500'>Evidence ({proposal.evidence.length}):</span>
            <EvidenceList evidence={proposal.evidence} />
          </div>
        )}
      </div>

      {/* Actions */}
      {!isActedOn && (
        <div className='mt-3 flex flex-wrap gap-2 items-center'>
          <Button
            size='sm'
            className='bg-green-600 hover:bg-green-700 text-white'
            onClick={() => onAccept(index)}
            disabled={isLoading}
          >
            {isLoading ? 'Accepting...' : 'Accept'}
          </Button>

          {rejectingIndex === index ? (
            <div className='flex items-center gap-2'>
              <Input
                placeholder='Reason (optional)'
                value={rejectReason}
                onChange={e => setRejectReason(e.target.value)}
                className='w-48 h-8 text-sm'
              />
              <Button
                size='sm'
                variant='destructive'
                onClick={() => onReject(index)}
                disabled={isLoading}
              >
                {isLoading ? 'Rejecting...' : 'Confirm'}
              </Button>
              <Button
                size='sm'
                variant='ghost'
                onClick={() => {
                  setRejectingIndex(null);
                  setRejectReason('');
                }}
              >
                Cancel
              </Button>
            </div>
          ) : (
            <Button
              size='sm'
              variant='outline'
              className='text-red-600 border-red-300 hover:bg-red-50'
              onClick={() => setRejectingIndex(index)}
              disabled={isLoading}
            >
              Reject
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

// --- Evidence List ---

function EvidenceList({ evidence }: { evidence: string[] }) {
  const [expanded, setExpanded] = useState(false);
  const limit = 3;
  const items = expanded ? evidence : evidence.slice(0, limit);

  return (
    <ul className='mt-1 space-y-1'>
      {items.map((e, i) => (
        <li key={i} className='text-xs text-gray-600 bg-gray-50 px-2 py-1 rounded font-mono'>
          {e}
        </li>
      ))}
      {evidence.length > limit && (
        <button
          className='text-xs text-blue-600 hover:text-blue-800'
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? 'Show less' : `+${evidence.length - limit} more`}
        </button>
      )}
    </ul>
  );
}

// ==========================================
// Main Panel
// ==========================================

const AgentReviewPanel: React.FC<AgentReviewPanelProps> = ({
  verifiedData,
  proposedData,
  loading,
  month,
  onDataRefresh,
}) => {
  if (loading) {
    return (
      <div className='bg-white rounded-lg shadow p-8 text-center'>
        <div className='text-gray-400 text-4xl mb-4'>...</div>
        <p className='text-gray-600'>Loading agent validation data...</p>
      </div>
    );
  }

  if (!verifiedData && !proposedData) {
    return (
      <div className='bg-white rounded-lg shadow p-8 text-center'>
        <p className='text-gray-500'>
          No agent validation data found. Run <code>/validate-matches</code> first.
        </p>
      </div>
    );
  }

  const verificationCount = verifiedData?.verifications?.length ?? 0;
  const proposalCount = proposedData?.proposals?.length ?? 0;
  const pendingProposals = proposedData?.proposals?.filter(p => !p._status).length ?? 0;

  return (
    <div className='bg-white rounded-lg shadow'>
      <div className='px-6 py-4 border-b border-gray-200'>
        <h3 className='text-lg font-medium text-gray-900'>Agent Review</h3>
        <p className='text-sm text-gray-500 mt-1'>
          Month: <span className='font-medium'>{month}</span>
          {verifiedData?.metadata.processed_at && (
            <>
              {' '} | Processed:{' '}
              <span className='font-medium'>
                {new Date(verifiedData.metadata.processed_at).toLocaleString()}
              </span>
            </>
          )}
        </p>
      </div>

      <div className='p-6'>
        <Tabs defaultValue='verifications'>
          <TabsList>
            <TabsTrigger value='verifications'>
              Verifications ({verificationCount})
            </TabsTrigger>
            <TabsTrigger value='proposals'>
              Proposals ({pendingProposals > 0 ? `${pendingProposals} pending` : proposalCount})
            </TabsTrigger>
          </TabsList>

          <TabsContent value='verifications'>
            {verifiedData ? (
              <VerificationsTable
                verifications={verifiedData.verifications}
                month={month}
                onDataRefresh={onDataRefresh}
              />
            ) : (
              <p className='text-gray-500 py-4'>No verification data available.</p>
            )}
          </TabsContent>

          <TabsContent value='proposals'>
            {proposedData ? (
              <ProposalsTable
                proposals={proposedData.proposals}
                month={month}
                onDataRefresh={onDataRefresh}
              />
            ) : (
              <p className='text-gray-500 py-4'>No proposal data available.</p>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default AgentReviewPanel;
