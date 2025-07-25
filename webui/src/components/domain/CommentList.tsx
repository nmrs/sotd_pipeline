import React from 'react';

interface CommentListProps {
  commentIds: string[];
  onCommentClick: (commentId: string) => void;
  commentLoading?: boolean;
  maxDisplay?: number;
  'aria-label'?: string;
}

export const CommentList: React.FC<CommentListProps> = ({
  commentIds = [],
  onCommentClick,
  commentLoading = false,
  maxDisplay = 3,
  'aria-label': ariaLabel,
}) => {
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
  const displayCount = Math.min(maxDisplay, validCommentIds.length);
  const displayComments = validCommentIds.slice(0, displayCount);
  const remainingCount = validCommentIds.length - displayCount;

  return (
    <div className='space-y-1' aria-label={ariaLabel}>
      {displayComments.map((commentId, index) => (
        <button
          key={commentId}
          onClick={() => onCommentClick?.(commentId)}
          disabled={commentLoading}
          className='block w-full text-left text-xs text-blue-600 hover:text-blue-800 hover:bg-blue-50 px-2 py-1 rounded border-0 bg-transparent cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed'
          aria-label={`View comment ${index + 1} of ${validCommentIds.length}`}
        >
          {commentId}
        </button>
      ))}
      {remainingCount > 0 && <span className='text-xs text-gray-500'>+{remainingCount} more</span>}
    </div>
  );
};
