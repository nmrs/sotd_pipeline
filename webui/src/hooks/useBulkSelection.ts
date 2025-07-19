import { useState, useCallback, useMemo } from 'react';

export interface BulkSelectionState {
    selectedItems: Set<string>;
    selectAll: boolean;
    indeterminate: boolean;
    totalItems: number;
    visibleItems: string[];
}

export interface UseBulkSelectionOptions {
    items: Array<{ item: string;[key: string]: any }>;
    filteredStatus: Record<string, boolean>;
    onSelectionChange?: (selectedItems: Set<string>) => void;
}

export const useBulkSelection = ({
    items,
    filteredStatus,
    onSelectionChange,
}: UseBulkSelectionOptions) => {
    const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());

    // Get visible items (not filtered out)
    const visibleItems = useMemo(() => {
        return items
            .map(item => item.item)
            .filter(itemName => !filteredStatus[itemName]);
    }, [items, filteredStatus]);

    // Calculate select all state
    const selectAll = useMemo(() => {
        if (visibleItems.length === 0) return false;
        return visibleItems.every(item => selectedItems.has(item));
    }, [visibleItems, selectedItems]);

    // Calculate indeterminate state (some but not all selected)
    const indeterminate = useMemo(() => {
        if (visibleItems.length === 0) return false;
        const selectedVisibleCount = visibleItems.filter(item => selectedItems.has(item)).length;
        return selectedVisibleCount > 0 && selectedVisibleCount < visibleItems.length;
    }, [visibleItems, selectedItems]);

    // Handle individual item selection
    const toggleItem = useCallback((itemName: string) => {
        setSelectedItems(prev => {
            const newSet = new Set(prev);
            if (newSet.has(itemName)) {
                newSet.delete(itemName);
            } else {
                newSet.add(itemName);
            }
            onSelectionChange?.(newSet);
            return newSet;
        });
    }, [onSelectionChange]);

    // Handle select all toggle
    const toggleSelectAll = useCallback(() => {
        setSelectedItems(prev => {
            const newSet = new Set(prev);
            if (selectAll) {
                // Deselect all visible items
                visibleItems.forEach(item => newSet.delete(item));
            } else {
                // Select all visible items
                visibleItems.forEach(item => newSet.add(item));
            }
            onSelectionChange?.(newSet);
            return newSet;
        });
    }, [selectAll, visibleItems, onSelectionChange]);

    // Clear all selections
    const clearSelection = useCallback(() => {
        setSelectedItems(new Set());
        onSelectionChange?.(new Set());
    }, [onSelectionChange]);

    // Get selected items that are currently visible
    const selectedVisibleItems = useMemo(() => {
        return visibleItems.filter(item => selectedItems.has(item));
    }, [visibleItems, selectedItems]);

    // Get all selected items (including filtered ones)
    const allSelectedItems = useMemo(() => {
        return Array.from(selectedItems);
    }, [selectedItems]);

    return {
        selectedItems,
        selectAll,
        indeterminate,
        totalItems: visibleItems.length,
        visibleItems,
        selectedVisibleItems,
        allSelectedItems,
        toggleItem,
        toggleSelectAll,
        clearSelection,
    };
}; 