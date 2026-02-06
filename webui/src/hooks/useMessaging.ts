import { useState, useCallback, useEffect } from 'react';

export interface Message {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  timestamp: number;
  autoHide?: boolean;
  retryAction?: () => void;
  /** When set, new messages with the same dedupeKey update this message and increment count instead of adding a new toast */
  dedupeKey?: string;
  count?: number;
  baseMessage?: string;
}

interface UseMessagingOptions {
  autoHideDelay?: number;
  maxMessages?: number;
}

export interface AddSuccessMessageOptions {
  autoHide?: boolean;
  /** When set, coalesce with existing message with this key and show an incrementing count */
  dedupeKey?: string;
}

interface UseMessagingReturn {
  messages: Message[];
  addSuccessMessage: (message: string, options?: boolean | AddSuccessMessageOptions) => void;
  addErrorMessage: (message: string, retryAction?: () => void) => void;
  addWarningMessage: (message: string, autoHide?: boolean) => void;
  addInfoMessage: (message: string, autoHide?: boolean) => void;
  removeMessage: (id: string) => void;
  clearMessages: () => void;
  clearSuccessMessages: () => void;
  clearErrorMessages: () => void;
}

export const useMessaging = (options: UseMessagingOptions = {}): UseMessagingReturn => {
  const { autoHideDelay = 3000, maxMessages = 10 } = options;
  const [messages, setMessages] = useState<Message[]>([]);

  const removeMessage = useCallback((id: string) => {
    setMessages(prev => prev.filter(msg => msg.id !== id));
  }, []);

  // Auto-hide messages
  useEffect(() => {
    const timeouts: ReturnType<typeof setTimeout>[] = [];

    messages.forEach(message => {
      if (message.autoHide && message.type === 'success') {
        const timeout = setTimeout(() => {
          removeMessage(message.id);
        }, autoHideDelay);
        timeouts.push(timeout);
      }
    });

    return () => {
      timeouts.forEach(clearTimeout);
    };
  }, [messages, autoHideDelay, removeMessage]);

  const addMessage = useCallback(
    (
      type: 'success' | 'error' | 'warning' | 'info',
      message: string,
      autoHide?: boolean,
      retryAction?: () => void
    ) => {
      const newMessage: Message = {
        id: `${type}-${Date.now()}-${Math.random()}`,
        type,
        message,
        timestamp: Date.now(),
        autoHide,
        retryAction,
      };

      setMessages(prev => {
        const updated = [newMessage, ...prev];
        // Keep only the most recent messages
        return updated.slice(0, maxMessages);
      });
    },
    [maxMessages]
  );

  const addSuccessMessage = useCallback(
    (message: string, options?: boolean | AddSuccessMessageOptions) => {
      const autoHide = typeof options === 'boolean' ? options : options?.autoHide ?? true;
      const dedupeKey = typeof options === 'object' && options?.dedupeKey;

      if (dedupeKey) {
        setMessages(prev => {
          const existing = prev.find(m => m.dedupeKey === dedupeKey);
          if (existing) {
            const count = (existing.count ?? 1) + 1;
            const baseMessage = existing.baseMessage ?? existing.message;
            const displayMessage =
              count > 1 ? `${baseMessage} (×${count})` : baseMessage;
            return prev.map(m =>
              m.dedupeKey === dedupeKey
                ? {
                    ...m,
                    message: displayMessage,
                    count,
                    baseMessage,
                    timestamp: Date.now(),
                  }
                : m
            );
          }
          return [
            {
              id: `success-${Date.now()}-${Math.random()}`,
              type: 'success' as const,
              message,
              timestamp: Date.now(),
              autoHide,
              dedupeKey,
              count: 1,
              baseMessage: message,
            },
            ...prev,
          ].slice(0, maxMessages);
        });
        return;
      }
      addMessage('success', message, autoHide);
    },
    [addMessage, maxMessages]
  );

  const addErrorMessage = useCallback(
    (message: string, retryAction?: () => void) => {
      addMessage('error', message, false, retryAction);
    },
    [addMessage]
  );

  const addWarningMessage = useCallback(
    (message: string, autoHide: boolean = true) => {
      addMessage('warning', message, autoHide);
    },
    [addMessage]
  );

  const addInfoMessage = useCallback(
    (message: string, autoHide: boolean = true) => {
      addMessage('info', message, autoHide);
    },
    [addMessage]
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  const clearSuccessMessages = useCallback(() => {
    setMessages(prev => prev.filter(msg => msg.type !== 'success'));
  }, []);

  const clearErrorMessages = useCallback(() => {
    setMessages(prev => prev.filter(msg => msg.type !== 'error'));
  }, []);

  return {
    messages,
    addSuccessMessage,
    addErrorMessage,
    addWarningMessage,
    addInfoMessage,
    removeMessage,
    clearMessages,
    clearSuccessMessages,
    clearErrorMessages,
  };
};
