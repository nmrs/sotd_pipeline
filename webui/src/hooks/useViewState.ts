import { useState, useEffect } from 'react';

interface UseViewStateOptions {
  defaultShowFiltered?: boolean;
  storageKey?: string;
}

interface UseViewStateReturn {
  showFiltered: boolean;
  toggleShowFiltered: () => void;
  setShowFiltered: (show: boolean) => void;
}

export const useViewState = (options: UseViewStateOptions = {}): UseViewStateReturn => {
  const { defaultShowFiltered = false, storageKey = 'unmatched-analyzer-show-filtered' } = options;

  // Initialize state from localStorage or default
  const [showFiltered, setShowFilteredState] = useState<boolean>(() => {
    try {
      const stored = localStorage.getItem(storageKey);
      return stored !== null ? JSON.parse(stored) : defaultShowFiltered;
    } catch (error) {
      console.warn('Failed to load view state from localStorage:', error);
      return defaultShowFiltered;
    }
  });

  // Save to localStorage whenever state changes
  useEffect(() => {
    try {
      localStorage.setItem(storageKey, JSON.stringify(showFiltered));
    } catch (error) {
      console.warn('Failed to save view state to localStorage:', error);
    }
  }, [showFiltered, storageKey]);

  const toggleShowFiltered = () => {
    setShowFilteredState(prev => !prev);
  };

  const setShowFiltered = (show: boolean) => {
    setShowFilteredState(show);
  };

  return {
    showFiltered,
    toggleShowFiltered,
    setShowFiltered,
  };
};
