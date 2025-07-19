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
                    setAvailableMonths(months);
                } catch (err: any) {
                    setError(err.message || 'Failed to load available months');
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

                // Cache the result
                monthsCache = months.sort().reverse(); // Sort newest first
                setAvailableMonths(monthsCache);
            } catch (err: any) {
                setError(err.message || 'Failed to load available months');
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
            monthsCache = months.sort().reverse();
            setAvailableMonths(monthsCache);
        } catch (err: any) {
            setError(err.message || 'Failed to load available months');
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