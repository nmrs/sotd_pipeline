import { useState, useCallback, useMemo } from 'react';
import { updateFilteredEntries, FilteredEntryRequest } from '../services/api';

export interface UseFilteredStateOptions {
  category: string;
  month: string;
  selectedItems: Set<string>;
  items: any[];
  onSuccess?: (message: string) => void;
  onError?: (message: string) => void;
}

export interface FilteredState {
  isUpdating: boolean;
  pendingChanges: Set<string>;
  hasChanges: boolean;
  updateFiltered: () => Promise<void>;
  clearPendingChanges: () => void;
}

export const useFilteredState = ({
  category,
  month,
  selectedItems,
  items,
  onSuccess,
  onError,
}: UseFilteredStateOptions): FilteredState => {
  const [isUpdating, setIsUpdating] = useState(false);
  const [pendingChanges, setPendingChanges] = useState<Set<string>>(new Set());

  // Track changes by comparing selected items with pending changes
  const hasChanges = useMemo(() => {
    return selectedItems.size > 0 || pendingChanges.size > 0;
  }, [selectedItems, pendingChanges]);

  // Prepare entries for bulk update
  const prepareEntries = useCallback(
    (action: 'add' | 'remove') => {
      const entries: Array<{
        name: string;
        action: 'add' | 'remove';
        comment_id?: string;
        source?: string;
        month: string;
      }> = [];

      selectedItems.forEach(itemName => {
        const item = items.find(i => i.item === itemName);
        if (item && item.comment_ids && item.comment_ids.length > 0) {
          // Add all comment IDs for this item
          item.comment_ids.forEach((commentId: string) => {
            entries.push({
              name: itemName,
              action,
              comment_id: commentId,
              source: 'user',
              month, // Add month to each entry
            });
          });
        }
      });

      return entries;
    },
    [selectedItems, items, month]
  );

  // Update filtered entries
  const updateFiltered = useCallback(async () => {
    if (!hasChanges) return;

    try {
      setIsUpdating(true);

      // Prepare entries to add (selected items)
      const addEntries = prepareEntries('add');

      // Prepare entries to remove (pending changes that are no longer selected)
      const removeEntries = Array.from(pendingChanges)
        .filter(itemName => !selectedItems.has(itemName))
        .flatMap(itemName => {
          const item = items.find(i => i.item === itemName);
          if (item && item.comment_ids) {
            return item.comment_ids.map((commentId: string) => ({
              name: itemName,
              action: 'remove' as const,
              comment_id: commentId,
              source: 'user',
              month, // Add month to each entry
            }));
          }
          return [];
        });

      // Combine all operations
      const allEntries = [...addEntries, ...removeEntries];

      if (allEntries.length === 0) {
        onSuccess?.('No changes to apply');
        return;
      }

      const request: FilteredEntryRequest = {
        category,
        entries: allEntries,
      };

      const response = await updateFilteredEntries(request);

      if (response.success) {
        // Clear pending changes and selected items
        setPendingChanges(new Set());

        // Prepare success message
        const messageParts = [];
        if (response.added_count > 0) {
          messageParts.push(`Added ${response.added_count} entries`);
        }
        if (response.removed_count > 0) {
          messageParts.push(`Removed ${response.removed_count} entries`);
        }

        const message = messageParts.join('; ') || 'Updated filtered entries successfully';
        onSuccess?.(message);
      } else {
        const errorMessage =
          response.errors.length > 0
            ? response.errors.join('; ')
            : response.message || 'Failed to update filtered entries';
        onError?.(errorMessage);
      }
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail || error.message || 'Failed to update filtered entries';
      onError?.(errorMessage);
    } finally {
      setIsUpdating(false);
    }
  }, [
    category,
    month,
    selectedItems,
    items,
    pendingChanges,
    hasChanges,
    prepareEntries,
    onSuccess,
    onError,
  ]);

  // Clear pending changes
  const clearPendingChanges = useCallback(() => {
    setPendingChanges(new Set());
  }, []);

  // Update pending changes when selected items change
  useMemo(() => {
    setPendingChanges(prev => {
      const newSet = new Set(prev);
      selectedItems.forEach(item => newSet.add(item));
      return newSet;
    });
  }, [selectedItems]);

  return {
    isUpdating,
    pendingChanges,
    hasChanges,
    updateFiltered,
    clearPendingChanges,
  };
};
