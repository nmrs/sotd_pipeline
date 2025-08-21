import React, { useState } from 'react';

interface CommentListProps {
  commentIds: string[];
  onCommentClick: (commentId: string, allCommentIds?: string[]) => void;
  commentLoading?: boolean;
  maxDisplay?: number;
  'aria-label'?: string;
}

export const CommentList: React.FC<CommentListProps> = ({
  commentIds = [],
  onCommentClick,
  commentLoading = false,
  maxDisplay = 3, // Show 3 by default, but allow expansion
  'aria-label': ariaLabel,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  // Handle empty state
  if (!commentIds || commentIds.length === 0) {
    return <span className='text-sm text-gray-500'>No comments</span>;
  }

  // Filter out empty comment IDs
  const validCommentIds = commentIds.filter(id => id && id.trim() !== '');

  if (validCommentIds.length === 0) {
    return <span className='text-sm text-gray-500'>No comments</span>;
  }

  // Determine which comments to show
  const displayCount = isExpanded ? validCommentIds.length : Math.min(maxDisplay, validCommentIds.length);
  const displayComments = validCommentIds.slice(0, displayCount);
  const remainingCount = validCommentIds.length - maxDisplay;
  const canExpand = !isExpanded && remainingCount > 0;

  const handleExpandClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsExpanded(true);
  };

  const handleCollapseClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsExpanded(false);
  };

  return (
    <div className='space-y-1' aria-label={ariaLabel}>
      {displayComments.map((commentId, index) => (
        <button
          key={commentId}
          onClick={() => onCommentClick?.(commentId, validCommentIds)}
          disabled={commentLoading}
          className='block w-full text-left text-xs text-blue-600 hover:text-blue-800 hover:bg-blue-50 px-2 py-1 rounded border-0 bg-transparent cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed'
          aria-label={`View comment ${index + 1} of ${validCommentIds.length}`}
        >
          {commentId}
        </button>
      ))}
      
      {/* Expand/Collapse controls */}
      {canExpand && (
        <button
          onClick={handleExpandClick}
          className='block w-full text-left text-xs text-blue-600 hover:text-blue-800 hover:bg-blue-50 px-2 py-1 rounded border-0 bg-transparent cursor-pointer'
          aria-label={`Show ${remainingCount} more comments`}
        >
          +{remainingCount} more
        </button>
      )}
      
      {isExpanded && remainingCount > 0 && (
        <button
          onClick={handleCollapseClick}
          className='block w-full text-left text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-50 px-2 py-1 rounded border-0 bg-transparent cursor-pointer'
          aria-label='Show fewer comments'
        >
          Show less
        </button>
      )}
    </div>
  );
};
