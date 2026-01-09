import { useEffect, useState, useRef } from 'react';
import { getOperationStatus, OperationStatus } from '@/services/api';

const POLL_INTERVAL = 500; // Poll every 500ms
const MAX_POLL_TIME = 60000; // Stop polling after 60 seconds

export const useOperationStatus = (operationId: string | null | undefined) => {
  const [status, setStatus] = useState<OperationStatus | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number | null>(null);

  useEffect(() => {
    if (!operationId) {
      setStatus(null);
      setError(null);
      setIsPolling(false);
      return;
    }

    // Reset state when operation ID changes
    setStatus(null);
    setError(null);
    setIsPolling(true);
    startTimeRef.current = Date.now();

    const poll = async () => {
      try {
        const operationStatus = await getOperationStatus(operationId);
        setStatus(operationStatus);
        setError(null);

        // Stop polling if operation is complete or failed
        if (operationStatus.status === 'completed' || operationStatus.status === 'failed') {
          setIsPolling(false);
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
        }
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Failed to get operation status');
        setError(error);
        // Continue polling on error (might be transient)
      }
    };

    // Initial poll
    poll();

    // Set up polling interval
    pollIntervalRef.current = setInterval(poll, POLL_INTERVAL);

    // Cleanup function
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };
  }, [operationId]);

  // Stop polling if we've exceeded max time
  useEffect(() => {
    if (!isPolling || !startTimeRef.current) {
      return;
    }

    const checkMaxTime = () => {
      const elapsed = Date.now() - startTimeRef.current!;
      if (elapsed > MAX_POLL_TIME) {
        setIsPolling(false);
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
        setError(new Error('Operation status polling timeout'));
      }
    };

    const timeoutId = setInterval(checkMaxTime, 1000);
    return () => clearInterval(timeoutId);
  }, [isPolling]);

  return { status, error, isPolling };
};
