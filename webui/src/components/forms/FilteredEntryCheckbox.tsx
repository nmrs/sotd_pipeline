import React from 'react';
import { Checkbox } from '@/components/ui/checkbox';

interface FilteredEntryCheckboxProps {
    itemName: string;
    commentIds: string[];
    isFiltered: boolean;
    onStatusChange?: (filtered: boolean) => void;
    disabled?: boolean;
    uniqueId?: string;
}

const FilteredEntryCheckbox: React.FC<FilteredEntryCheckboxProps> = ({
    itemName,
    commentIds,
    isFiltered,
    onStatusChange,
    disabled = false,
    uniqueId,
}) => {
    const handleCheckboxChange = (checked: boolean) => {
        if (!itemName || commentIds.length === 0 || disabled) return;

        // Update immediately without API call
        onStatusChange?.(checked);
    };

    // Create unique test ID to prevent duplicates
    const testId = uniqueId ? `checkbox-${itemName}-${uniqueId}` : `checkbox-${itemName}`;

    return (
        <div className="flex items-center">
            <Checkbox
                checked={isFiltered}
                onCheckedChange={handleCheckboxChange}
                disabled={disabled || commentIds.length === 0}
                title={isFiltered ? 'Mark as unfiltered' : 'Mark as intentionally unmatched'}
                data-testid={testId}
            />
        </div>
    );
};

export default FilteredEntryCheckbox; 