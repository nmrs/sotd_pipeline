import { useState, useCallback, useEffect } from 'react';

export interface Message {
    id: string;
    type: 'success' | 'error';
    message: string;
    timestamp: number;
    autoHide?: boolean;
    retryAction?: () => void;
}

interface UseMessagingOptions {
    autoHideDelay?: number;
    maxMessages?: number;
}

interface UseMessagingReturn {
    messages: Message[];
    addSuccessMessage: (message: string, autoHide?: boolean) => void;
    addErrorMessage: (message: string, retryAction?: () => void) => void;
    removeMessage: (id: string) => void;
    clearMessages: () => void;
    clearSuccessMessages: () => void;
    clearErrorMessages: () => void;
}

export const useMessaging = (options: UseMessagingOptions = {}): UseMessagingReturn => {
    const { autoHideDelay = 3000, maxMessages = 10 } = options;
    const [messages, setMessages] = useState<Message[]>([]);

    // Auto-hide messages
    useEffect(() => {
        const timeouts: number[] = [];

        messages.forEach((message) => {
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
    }, [messages, autoHideDelay]);

    const addMessage = useCallback((type: 'success' | 'error', message: string, autoHide?: boolean, retryAction?: () => void) => {
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
    }, [maxMessages]);

    const addSuccessMessage = useCallback((message: string, autoHide: boolean = true) => {
        addMessage('success', message, autoHide);
    }, [addMessage]);

    const addErrorMessage = useCallback((message: string, retryAction?: () => void) => {
        addMessage('error', message, false, retryAction);
    }, [addMessage]);

    const removeMessage = useCallback((id: string) => {
        setMessages(prev => prev.filter(msg => msg.id !== id));
    }, []);

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
        removeMessage,
        clearMessages,
        clearSuccessMessages,
        clearErrorMessages,
    };
}; 