import React, { useState, useEffect } from 'react';
import { checkFilteredStatus, updateFilteredEntries, FilteredStatusRequest, FilteredEntryRequest } from '../services/api';

interface FilteredEntryCheckboxProps {
    category: string;
    itemName: string;
    commentIds: string[];
    onStatusChange?: (isFiltered: boolean) => void;
    disabled?: boolean;
}

const FilteredEntryCheckbox: React.FC<FilteredEntryCheckboxProps> = ({
    category,
    itemName,
    commentIds,
    onStatusChange,
    disabled = false,
}) => {
    const [isFiltered, setIsFiltered] = useState<boolean>(false);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    // Check initial filtered status
    useEffect(() => {
        const checkStatus = async () => {
            if (!itemName || commentIds.length === 0) return;

            try {
                setIsLoading(true);
                setError(null);

                const request: FilteredStatusRequest = {
                    entries: [{ category, name: itemName }],
                };

                const response = await checkFilteredStatus(request);
                const key = `${category}:${itemName}`;
                const status = response.data[key] || false;
                setIsFiltered(status);
                onStatusChange?.(status);
            } catch (err: any) {
                console.error('Failed to check filtered status:', err);
                setError('Failed to check status');
            } finally {
                setIsLoading(false);
            }
        };

        checkStatus();
    }, [category, itemName, commentIds, onStatusChange]);

    const handleCheckboxChange = async (checked: boolean) => {
        if (!itemName || commentIds.length === 0 || disabled) return;

        try {
            setIsLoading(true);
            setError(null);

            const action = checked ? 'add' : 'remove';
            const entries = commentIds.map(commentId => ({
                name: itemName,
                action: action as 'add' | 'remove',
                comment_id: commentId,
                file_path: `data/comments/${commentId.split('_')[0]}.json`, // Extract month from comment ID
                source: 'user',
            }));

            const request: FilteredEntryRequest = {
                category,
                entries,
            };

            const response = await updateFilteredEntries(request);

            if (response.success) {
                setIsFiltered(checked);
                onStatusChange?.(checked);
            } else {
                setError(response.message || 'Failed to update filtered status');
            }
        } catch (err: any) {
            console.error('Failed to update filtered status:', err);
            setError('Failed to update status');
        } finally {
            setIsLoading(false);
        }
    };

    if (error) {
        return (
            <div className="flex items-center">
                <div className="text-red-500 text-xs" title={error}>
                    Error
                </div>
            </div>
        );
    }

    return (
        <div className="flex items-center">
            <input
                type="checkbox"
                checked={isFiltered}
                onChange={(e) => handleCheckboxChange(e.target.checked)}
                disabled={disabled || isLoading || commentIds.length === 0}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                title={isFiltered ? 'Mark as unfiltered' : 'Mark as intentionally unmatched'}
            />
            {isLoading && (
                <div className="ml-1">
                    <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-blue-600"></div>
                </div>
            )}
        </div>
    );
};

export default FilteredEntryCheckbox; 