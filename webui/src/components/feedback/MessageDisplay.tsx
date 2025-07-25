import React from 'react';
import { Message } from '../../hooks/useMessaging';

interface MessageDisplayProps {
  messages: Message[];
  onRemoveMessage: (id: string) => void;
}

const MessageDisplay: React.FC<MessageDisplayProps> = ({ messages, onRemoveMessage }) => {
  if (messages.length === 0) {
    return null;
  }

  return (
    <div className='fixed top-4 right-4 z-50 space-y-2 max-w-md'>
      {messages.map(message => (
        <div
          key={message.id}
          className={`rounded-lg shadow-lg p-4 border-l-4 ${
            message.type === 'success'
              ? 'bg-green-50 border-green-400 text-green-800'
              : 'bg-red-50 border-red-400 text-red-800'
          }`}
        >
          <div className='flex items-start justify-between'>
            <div className='flex items-start space-x-3'>
              <div className='flex-shrink-0'>
                {message.type === 'success' ? (
                  <svg className='h-5 w-5 text-green-400' viewBox='0 0 20 20' fill='currentColor'>
                    <path
                      fillRule='evenodd'
                      d='M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z'
                      clipRule='evenodd'
                    />
                  </svg>
                ) : (
                  <svg className='h-5 w-5 text-red-400' viewBox='0 0 20 20' fill='currentColor'>
                    <path
                      fillRule='evenodd'
                      d='M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z'
                      clipRule='evenodd'
                    />
                  </svg>
                )}
              </div>
              <div className='flex-1'>
                <p className='text-sm font-medium'>{message.message}</p>
                {message.retryAction && (
                  <button
                    onClick={message.retryAction}
                    className='mt-2 text-xs font-medium underline hover:no-underline'
                  >
                    Retry
                  </button>
                )}
              </div>
            </div>
            <button
              onClick={() => onRemoveMessage(message.id)}
              className='flex-shrink-0 ml-3 text-gray-400 hover:text-gray-600'
            >
              <svg className='h-4 w-4' viewBox='0 0 20 20' fill='currentColor'>
                <path
                  fillRule='evenodd'
                  d='M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z'
                  clipRule='evenodd'
                />
              </svg>
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default MessageDisplay;
