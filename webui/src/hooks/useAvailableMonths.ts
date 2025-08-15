import { useState, useEffect } from 'react';
import { getAvailableMonths } from '../services/api';

// Global cache for available months
let monthsCache: string[] | null = null;
let cachePromise: Promise<string[]> | null = null;

export const useAvailableMonths = () => {
  const [availableMonths, setAvailableMonths] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMonths = async () => {
      // If we already have cached data, use it
      if (monthsCache !== null) {
        setAvailableMonths(monthsCache);
        setLoading(false);
        return;
      }

      // If there's already a request in progress, wait for it
      if (cachePromise !== null) {
        try {
          const months = await cachePromise;
          if (months && Array.isArray(months)) {
            setAvailableMonths(months);
          } else {
            // Handle case where cached promise resolves with unexpected data
            console.warn('Cached promise returned unexpected data:', months);
            setAvailableMonths([]);
          }
        } catch (err: unknown) {
          const errorMessage =
            err instanceof Error ? err.message : 'Failed to load available months';
          setError(errorMessage);
        } finally {
          setLoading(false);
        }
        return;
      }

      // Start a new request
      try {
        setLoading(true);
        setError(null);

        cachePromise = getAvailableMonths();
        const months = await cachePromise;

        // Cache the result - handle case where months might be undefined
        if (months && Array.isArray(months)) {
          monthsCache = months.sort().reverse(); // Sort newest first
          setAvailableMonths(monthsCache);
        } else {
          // Handle case where API returns unexpected data
          console.warn('getAvailableMonths returned unexpected data:', months);
          monthsCache = [];
          setAvailableMonths([]);
        }
      } catch (err: unknown) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load available months';
        setError(errorMessage);
      } finally {
        setLoading(false);
        cachePromise = null;
      }
    };

    fetchMonths();
  }, []);

  const refreshMonths = async () => {
    // Clear cache and reload
    monthsCache = null;
    cachePromise = null;
    setLoading(true);
    setError(null);

    try {
      const months = await getAvailableMonths();
      if (months && Array.isArray(months)) {
        monthsCache = months.sort().reverse();
        setAvailableMonths(monthsCache);
      } else {
        // Handle case where API returns unexpected data
        console.warn('getAvailableMonths returned unexpected data:', months);
        monthsCache = [];
        setAvailableMonths([]);
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load available months';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return {
    availableMonths,
    loading,
    error,
    refreshMonths,
  };
};
