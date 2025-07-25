import React from 'react';
import { CommentDetail } from '../../services/api';

interface CommentModalProps {
  comment: CommentDetail | null;
  commentId?: string;
  isOpen: boolean;
  onClose: () => void;
}

const CommentModal: React.FC<CommentModalProps> = ({ comment, isOpen, onClose }) => {
  if (!isOpen || !comment) {
    return null;
  }

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  const formatBody = (body: string) => {
    // Convert markdown-style formatting to readable text
    return body
      .replace(/\*\*(.*?)\*\*/g, '$1') // Bold
      .replace(/\*(.*?)\*/g, '$1') // Italic
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // Links
      .replace(/\$([A-Z_]+)/g, '[$1]') // Tags
      .replace(/\n/g, '<br />'); // Line breaks
  };

  return (
    <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50'>
      <div className='bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden'>
        {/* Header */}
        <div className='flex items-center justify-between p-4 border-b border-gray-200'>
          <div>
            <h2 className='text-lg font-semibold text-gray-900'>Comment Details</h2>
            <p className='text-sm text-gray-500'>
              ID: {comment.id} • {formatDate(comment.created_utc)}
            </p>
          </div>
          <button
            onClick={onClose}
            className='text-gray-400 hover:text-gray-600 focus:outline-none focus:text-gray-600'
          >
            <svg className='h-6 w-6' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
              <path
                strokeLinecap='round'
                strokeLinejoin='round'
                strokeWidth={2}
                d='M6 18L18 6M6 6l12 12'
              />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className='p-4 overflow-y-auto max-h-[calc(90vh-120px)]'>
          {/* Comment Info */}
          <div className='mb-4 p-3 bg-gray-50 rounded-lg'>
            <div className='grid grid-cols-1 md:grid-cols-2 gap-3 text-sm'>
              <div>
                <span className='font-medium text-gray-700'>Author:</span>
                <span className='ml-2 text-gray-900'>{comment.author}</span>
              </div>
              <div>
                <span className='font-medium text-gray-700'>Thread:</span>
                <span className='ml-2 text-gray-900'>{comment.thread_title}</span>
              </div>
              <div>
                <span className='font-medium text-gray-700'>Created:</span>
                <span className='ml-2 text-gray-900'>{formatDate(comment.created_utc)}</span>
              </div>
              <div>
                <span className='font-medium text-gray-700'>URL:</span>
                <a
                  href={comment.url}
                  target='_blank'
                  rel='noopener noreferrer'
                  className='ml-2 text-blue-600 hover:text-blue-800 underline'
                >
                  View on Reddit
                </a>
              </div>
            </div>
          </div>

          {/* Comment Body */}
          <div>
            <h3 className='text-sm font-medium text-gray-700 mb-2'>Comment Content:</h3>
            <div
              className='bg-gray-50 p-4 rounded-lg text-sm text-gray-900 whitespace-pre-wrap'
              dangerouslySetInnerHTML={{ __html: formatBody(comment.body) }}
            />
          </div>
        </div>

        {/* Footer */}
        <div className='flex justify-end p-4 border-t border-gray-200'>
          <button
            onClick={onClose}
            className='px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500'
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default CommentModal;
