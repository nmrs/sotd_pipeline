import React from 'react';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { CommentDisplay } from './CommentDisplay';
import type { AlignmentResult, FuzzyMatch } from '../../types/wsdbAlignment';

export type AlignmentDirection = 'pipeline-to-wsdb' | 'wsdb-to-pipeline';

const BORDER_MAP: Record<AlignmentDirection, { default: string; failed: string }> = {
  'pipeline-to-wsdb': { default: 'border-blue-200', failed: 'border-amber-500 bg-amber-100 rounded' },
  'wsdb-to-pipeline': { default: 'border-green-200', failed: 'border-amber-500 bg-amber-100 rounded' },
};

export interface WSDBAlignmentResultExpandedProps {
  result: AlignmentResult;
  nonPendingMatches: FuzzyMatch[];
  hasNonPendingMatches: boolean;
  hasPendingOperations: boolean;
  analysisMode: 'brands' | 'brand_scent';
  direction: AlignmentDirection;
  getMatchKey: (source: AlignmentResult, match: FuzzyMatch) => string;
  getConfidenceColor: (confidence: number) => string;
  getConfidenceLabel: (confidence: number) => string;
  failedItemKeys: Set<string>;
  bulkNoMatchResultKey: string | null;
  onNoMatchesForResult: (
    result: AlignmentResult,
    matches: FuzzyMatch[],
    direction: AlignmentDirection
  ) => void;
  onNotAMatch: (result: AlignmentResult, match: FuzzyMatch) => void;
  onAddScentAlias: (result: AlignmentResult, match: FuzzyMatch) => void;
  dataSource: 'catalog' | 'match_files';
  commentIds: string[] | undefined;
  onCommentClick: (commentId: string, allCommentIds?: string[]) => void;
  commentLoading: boolean;
}

/**
 * Expanded content for one alignment result (matches list + bulk actions + comment refs).
 * Renders without a fragment-in-ternary to avoid TS/JSX parser errors in the parent.
 */
export const WSDBAlignmentResultExpanded: React.FC<WSDBAlignmentResultExpandedProps> = (props) => {
  const {
    result,
    nonPendingMatches,
    hasNonPendingMatches,
    hasPendingOperations,
    analysisMode,
    direction,
    getMatchKey,
    getConfidenceColor,
    getConfidenceLabel,
    failedItemKeys,
    bulkNoMatchResultKey,
    onNoMatchesForResult,
    onNotAMatch,
    onAddScentAlias,
    dataSource,
    commentIds,
    onCommentClick,
    commentLoading,
  } = props;

  const resultKey = `${result.source_brand}|${result.source_scent || ''}`;
  const borders = BORDER_MAP[direction];

  if (hasPendingOperations) {
    return (
      <div className='text-sm text-gray-500 italic'>
        All matches are being processed...
      </div>
    );
  }

  if (!hasNonPendingMatches) {
    return <div className='text-sm text-gray-500 italic'>No matches found</div>;
  }

  return (
    <div className='space-y-3'>
      <div className='flex items-center gap-2 pb-2 border-b border-gray-200'>
        <Button
          variant='outline'
          size='sm'
          onClick={(e) => {
            e.stopPropagation();
            const targets =
              analysisMode === 'brands'
                ? Object.values(
                    nonPendingMatches.reduce((acc, m) => {
                      if (!acc[m.brand]) acc[m.brand] = [];
                      acc[m.brand].push(m);
                      return acc;
                    }, {} as Record<string, FuzzyMatch[]>)
                  ).map(ms => ms[0])
                : nonPendingMatches;
            onNoMatchesForResult(result, targets, direction);
          }}
          disabled={bulkNoMatchResultKey === resultKey}
          className='text-red-600 hover:bg-red-50 hover:text-red-700'
        >
          {bulkNoMatchResultKey === resultKey
            ? 'Marking…'
            : `No matches — mark all ${nonPendingMatches.length} as not a match`}
        </Button>
      </div>

      {analysisMode === 'brands' ? (
        (() => {
          const brandGroups = nonPendingMatches.reduce((acc, match) => {
            if (!acc[match.brand]) acc[match.brand] = [];
            acc[match.brand].push(match);
            return acc;
          }, {} as Record<string, FuzzyMatch[]>);
          return Object.entries(brandGroups).map(([brand, brandMatches]) => {
            const rowKey = getMatchKey(result, brandMatches[0]);
            const isFailed = failedItemKeys.has(rowKey);
            return (
              <div
                key={brand}
                className={`border-l-2 pl-4 space-y-2 ${isFailed ? borders.failed : borders.default}`}
              >
                <div className='flex items-center justify-between mb-2'>
                  <div className='font-semibold text-gray-900 flex items-center gap-2'>
                    <span>{brand}</span>
                    {brandMatches[0].matched_via === 'alias' && (
                      <Badge
                        variant='outline'
                        className='text-xs bg-blue-50 text-blue-700 border-blue-200'
                      >
                        via alias
                      </Badge>
                    )}
                    {isFailed && (
                      <span className='text-xs text-amber-700'>Failed – see errors</span>
                    )}
                  </div>
                  <div className='flex items-center gap-2'>
                    <Badge className={getConfidenceColor(brandMatches[0].confidence)}>
                      {brandMatches[0].confidence.toFixed(1)}%
                    </Badge>
                    <Button
                      variant='outline'
                      size='sm'
                      onClick={(e) => {
                        e.stopPropagation();
                        onNotAMatch(result, brandMatches[0]);
                      }}
                      className='text-red-600 hover:bg-red-50 hover:text-red-700'
                    >
                      ✕ Not a Match
                    </Button>
                  </div>
                </div>
                <div className='pl-4 space-y-1'>
                  {brandMatches.map((match, idx) => {
                    const slug = match.details?.slug;
                    const scentName = match.name || '(no scent name)';
                    const formatType = match.details?.type;
                    return (
                      <div key={idx} className='text-sm text-gray-700 flex items-center gap-2'>
                        <span>•</span>
                        {slug ? (
                          <a
                            href={`https://www.wetshavingdatabase.com/software/${slug}/`}
                            target='_blank'
                            rel='noopener noreferrer'
                            className='text-blue-600 hover:text-blue-800 hover:underline'
                          >
                            {scentName}
                          </a>
                        ) : (
                          <span>{scentName}</span>
                        )}
                        {formatType && (
                          <Badge variant='secondary' className='text-xs font-normal'>
                            {formatType}
                          </Badge>
                        )}
                      </div>
                    );
                  })}
                </div>
                {direction === 'pipeline-to-wsdb' &&
                  brandMatches[0].details.collaborators &&
                  brandMatches[0].details.collaborators.length > 0 && (
                    <div className='text-sm text-gray-600 pl-4'>
                      <span className='font-medium'>Collaborators:</span>{' '}
                      {brandMatches[0].details.collaborators.join(', ')}
                    </div>
                  )}
                {direction === 'wsdb-to-pipeline' &&
                  brandMatches[0].details.patterns &&
                  brandMatches[0].details.patterns.length > 0 && (
                    <div className='text-sm text-gray-600 pl-4'>
                      <span className='font-medium'>Patterns:</span>{' '}
                      {brandMatches[0].details.patterns.join(', ')}
                    </div>
                  )}
              </div>
            );
          });
        })()
      ) : (
        nonPendingMatches.map((match, matchIndex) => {
          const rowKey = getMatchKey(result, match);
          const isFailed = failedItemKeys.has(rowKey);
          return (
            <div
              key={`${match.brand}-${match.name}-${matchIndex}`}
              className={`border-l-2 pl-4 ${isFailed ? borders.failed : borders.default}`}
            >
              <div className='flex items-center justify-between mb-2'>
                <div className='font-medium text-gray-900 flex items-center gap-2'>
                  {match.details?.slug ? (
                    <a
                      href={`https://www.wetshavingdatabase.com/software/${match.details.slug}/`}
                      target='_blank'
                      rel='noopener noreferrer'
                      className='text-blue-600 hover:text-blue-800 hover:underline'
                    >
                      {match.brand}
                      {match.name && ` - ${match.name}`}
                    </a>
                  ) : (
                    <span>
                      {match.brand}
                      {match.name && ` - ${match.name}`}
                    </span>
                  )}
                  {match.details?.type && (
                    <Badge variant='secondary' className='text-xs font-normal'>
                      {match.details.type}
                    </Badge>
                  )}
                  {isFailed && (
                    <span className='text-xs text-amber-700'>Failed – see errors</span>
                  )}
                  {match.matched_via === 'alias' && (
                    <Badge
                      variant='outline'
                      className='text-xs bg-blue-50 text-blue-700 border-blue-200'
                    >
                      via alias
                    </Badge>
                  )}
                  {match.scent_matched_via === 'alias' && (
                    <Badge
                      variant='outline'
                      className='text-xs bg-blue-50 text-blue-700 border-blue-200'
                    >
                      scent via alias
                    </Badge>
                  )}
                </div>
                <div className='flex items-center gap-2'>
                  <Badge className={getConfidenceColor(match.confidence)}>
                    {match.confidence.toFixed(1)}%
                  </Badge>
                  <Button
                    variant='outline'
                    size='sm'
                    onClick={(e) => {
                      e.stopPropagation();
                      onAddScentAlias(result, match);
                    }}
                    className='text-green-600 hover:bg-green-50 hover:text-green-700'
                  >
                    + Add Slug
                  </Button>
                  <Button
                    variant='outline'
                    size='sm'
                    onClick={(e) => {
                      e.stopPropagation();
                      onNotAMatch(result, match);
                    }}
                    className='text-red-600 hover:bg-red-50 hover:text-red-700'
                  >
                    ✕ Not a Match
                  </Button>
                </div>
              </div>
              <div className='text-sm text-gray-600 space-y-1'>
                <div>
                  Brand Score: {match.brand_score.toFixed(1)}% | Scent Score:{' '}
                  {match.scent_score.toFixed(1)}%
                </div>
                {direction === 'pipeline-to-wsdb' && (
                  <>
                    {match.details.scent_notes && match.details.scent_notes.length > 0 && (
                      <div>
                        <span className='font-medium'>Scent Notes:</span>{' '}
                        {match.details.scent_notes.join(', ')}
                      </div>
                    )}
                    {match.details.collaborators && match.details.collaborators.length > 0 && (
                      <div>
                        <span className='font-medium'>Collaborators:</span>{' '}
                        {match.details.collaborators.join(', ')}
                      </div>
                    )}
                    {match.details.tags && match.details.tags.length > 0 && (
                      <div>
                        <span className='font-medium'>Tags:</span>{' '}
                        {match.details.tags.join(', ')}
                      </div>
                    )}
                  </>
                )}
                {direction === 'wsdb-to-pipeline' &&
                  match.details.patterns &&
                  match.details.patterns.length > 0 && (
                    <div>
                      <span className='font-medium'>Patterns:</span>{' '}
                      {match.details.patterns.join(', ')}
                    </div>
                  )}
              </div>
            </div>
          );
        })
      )}

      {dataSource === 'match_files' && commentIds && commentIds.length > 0 && (
        <div className='mt-4 pt-4 border-t'>
          <div className='text-sm font-medium text-gray-700 mb-2'>
            Comment References ({commentIds.length})
          </div>
          <CommentDisplay
            commentIds={commentIds}
            onCommentClick={(id) => onCommentClick(id, commentIds)}
            commentLoading={commentLoading}
            maxDisplay={5}
            className='flex flex-wrap gap-2'
          />
        </div>
      )}
    </div>
  );
};
