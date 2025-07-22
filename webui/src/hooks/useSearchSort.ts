import { useState, useMemo, useCallback } from 'react';

export type SortField = 'item' | 'count' | 'comment_ids' | 'examples';
export type SortDirection = 'asc' | 'desc';

interface UseSearchSortOptions {
  items: Array<{
    item: string;
    count: number;
    comment_ids?: string[];
    examples?: string[];
    [key: string]: any;
  }>;
  defaultSortField?: SortField;
  defaultSortDirection?: SortDirection;
  showFiltered?: boolean;
  filteredStatus?: Record<string, boolean>;
}

interface UseSearchSortReturn {
  searchTerm: string;
  setSearchTerm: (term: string) => void;
  sortField: SortField;
  setSortField: (field: SortField) => void;
  sortDirection: SortDirection;
  setSortDirection: (direction: SortDirection) => void;
  toggleSortDirection: () => void;
  filteredAndSortedItems: Array<{
    item: string;
    count: number;
    comment_ids?: string[];
    examples?: string[];
    [key: string]: any;
  }>;
  searchResultsCount: number;
  totalItemsCount: number;
  clearSearch: () => void;
}

export const useSearchSort = ({
  items,
  defaultSortField = 'count',
  defaultSortDirection = 'desc',
  showFiltered = true,
  filteredStatus = {},
}: UseSearchSortOptions): UseSearchSortReturn => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState<SortField>(defaultSortField);
  const [sortDirection, setSortDirection] = useState<SortDirection>(defaultSortDirection);

  // Filter items based on search term and filtered status
  const filteredItems = useMemo(() => {
    let filtered = items;

    // Filter out items that are marked as filtered when showFiltered is false
    if (!showFiltered) {
      filtered = filtered.filter(item => !filteredStatus[item.item]);
    }

    // Filter by search term
    if (!searchTerm.trim()) {
      return filtered;
    }

    const term = searchTerm.toLowerCase();
    return filtered.filter(item => {
      // Search in item name
      if (item.item.toLowerCase().includes(term)) {
        return true;
      }

      // Search in examples
      if (item.examples && item.examples.some(example => example.toLowerCase().includes(term))) {
        return true;
      }

      // Search in comment IDs
      if (item.comment_ids && item.comment_ids.some(id => id.toLowerCase().includes(term))) {
        return true;
      }

      return false;
    });
  }, [items, searchTerm, showFiltered, filteredStatus]);

  // Sort filtered items
  const filteredAndSortedItems = useMemo(() => {
    const sorted = [...filteredItems].sort((a, b) => {
      let aValue: any;
      let bValue: any;

      switch (sortField) {
        case 'item':
          aValue = a.item.toLowerCase();
          bValue = b.item.toLowerCase();
          break;
        case 'count':
          aValue = a.count;
          bValue = b.count;
          break;
        case 'comment_ids':
          aValue = a.comment_ids?.length || 0;
          bValue = b.comment_ids?.length || 0;
          break;
        case 'examples':
          aValue = a.examples?.length || 0;
          bValue = b.examples?.length || 0;
          break;
        default:
          aValue = a[sortField];
          bValue = b[sortField];
      }

      // Handle null/undefined values
      if (aValue == null && bValue == null) return 0;
      if (aValue == null) return 1;
      if (bValue == null) return -1;

      // Compare values
      if (aValue < bValue) {
        return sortDirection === 'asc' ? -1 : 1;
      }
      if (aValue > bValue) {
        return sortDirection === 'asc' ? 1 : -1;
      }
      return 0;
    });

    return sorted;
  }, [filteredItems, sortField, sortDirection]);

  const toggleSortDirection = useCallback(() => {
    setSortDirection(prev => (prev === 'asc' ? 'desc' : 'asc'));
  }, []);

  const clearSearch = useCallback(() => {
    setSearchTerm('');
  }, []);

  return {
    searchTerm,
    setSearchTerm,
    sortField,
    setSortField,
    sortDirection,
    setSortDirection,
    toggleSortDirection,
    filteredAndSortedItems,
    searchResultsCount: filteredItems.length,
    totalItemsCount: items.length,
    clearSearch,
  };
};
