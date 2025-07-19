import React from 'react';

interface FilteredEntryCheckboxProps {
    itemName: string;
    commentIds: string[];
    isFiltered: boolean;
    onStatusChange?: (isFiltered: boolean) => void;
    disabled?: boolean;
}

const FilteredEntryCheckbox: React.FC<FilteredEntryCheckboxProps> = ({
    itemName,
    commentIds,
    isFiltered,
    onStatusChange,
    disabled = false,
}) => {
    const handleCheckboxChange = (checked: boolean) => {
        if (!itemName || commentIds.length === 0 || disabled) return;

        // Update immediately without API call
        onStatusChange?.(checked);
    };

    return (
        <div className="flex items-center">
            <input
                type="checkbox"
                checked={isFiltered}
                onChange={(e) => handleCheckboxChange(e.target.checked)}
                disabled={disabled || commentIds.length === 0}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                title={isFiltered ? 'Mark as unfiltered' : 'Mark as intentionally unmatched'}
            />
        </div>
    );
};

export default FilteredEntryCheckbox; 