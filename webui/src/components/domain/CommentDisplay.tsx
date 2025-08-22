import React, { useState } from 'react';

interface CommentDisplayProps {
  commentIds: string[];
  onCommentClick: (commentId: string) => void;
  commentLoading?: boolean;
  maxDisplay?: number;
  className?: string;
}

export const CommentDisplay: React.FC<CommentDisplayProps> = ({
  commentIds = [],
  onCommentClick,
  commentLoading = false,
  maxDisplay = 3,
  className = '',
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  // Handle empty state
  if (!commentIds || commentIds.length === 0) {
    return <span className='text-sm text-gray-500'>-</span>;
  }

  // Filter out empty comment IDs
  const validCommentIds = commentIds.filter(id => id && id.trim() !== '');

  if (validCommentIds.length === 0) {
    return <span className='text-sm text-gray-500'>-</span>;
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
    <div className={`space-y-1 ${className}`}>
      {displayComments.map((commentId, index) => (
        <button
          key={commentId}
          onClick={() => onCommentClick(commentId)}
          disabled={commentLoading}
          className='block text-blue-600 hover:text-blue-800 hover:underline cursor-pointer text-left text-sm'
        >
          {commentId}
        </button>
      ))}

      {/* Expand/Collapse controls */}
      {canExpand && (
        <button
          onClick={handleExpandClick}
          className='text-blue-600 hover:text-blue-800 hover:underline cursor-pointer text-sm'
        >
          +{remainingCount} more
        </button>
      )}

      {isExpanded && remainingCount > 0 && (
        <button
          onClick={handleCollapseClick}
          className='text-blue-600 hover:text-blue-800 hover:underline cursor-pointer text-sm'
        >
          Show less
        </button>
      )}
    </div>
  );
};
