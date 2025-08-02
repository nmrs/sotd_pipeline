import React, { useState, useMemo } from 'react';
import { ChevronDown, Filter, X, ChevronUp, ChevronsUpDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuCheckboxItem,
  DropdownMenuLabel,
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';

export interface HeaderFilterOption {
  value: string;
  label: string;
  count: number;
}

export interface HeaderFilterProps {
  title: string;
  options: HeaderFilterOption[];
  selectedValues: Set<string>;
  onSelectionChange: (selectedValues: Set<string>) => void;
  searchPlaceholder?: string;
  showCounts?: boolean;
  maxHeight?: string;
  onSort?: () => void;
  sortDirection?: 'asc' | 'desc' | null;
  showSortIndicator?: boolean;
}

export const HeaderFilter: React.FC<HeaderFilterProps> = ({
  title,
  options,
  selectedValues,
  onSelectionChange,
  searchPlaceholder = 'Search...',
  showCounts = true,
  maxHeight = '300px',
  onSort,
  sortDirection = null,
  showSortIndicator = true,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // Filter options based on search term
  const filteredOptions = useMemo(() => {
    if (!searchTerm.trim()) return options;

    return options.filter(
      option =>
        option.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
        option.value.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [options, searchTerm]);

  // Handle individual option selection
  const handleOptionToggle = (value: string) => {
    const newSelected = new Set(selectedValues);
    if (newSelected.has(value)) {
      newSelected.delete(value);
    } else {
      newSelected.add(value);
    }
    onSelectionChange(newSelected);
  };

  // Handle select all
  const handleSelectAll = () => {
    const allValues = new Set(filteredOptions.map(option => option.value));
    onSelectionChange(allValues);
  };

  // Handle clear all
  const handleClearAll = () => {
    onSelectionChange(new Set());
  };

  // Handle select visible
  const handleSelectVisible = () => {
    const visibleValues = new Set(filteredOptions.map(option => option.value));
    onSelectionChange(visibleValues);
  };

  // Get display text for the filter button
  const getDisplayText = () => {
    if (selectedValues.size === 0) {
      return title;
    }

    if (selectedValues.size === options.length) {
      return `${title} (All)`;
    }

    if (selectedValues.size <= 2) {
      const selectedLabels = options
        .filter(option => selectedValues.has(option.value))
        .map(option => option.label);
      return `${title}: ${selectedLabels.join(', ')}`;
    }

    return `${title} (${selectedValues.size})`;
  };

  const hasActiveFilter = selectedValues.size > 0 && selectedValues.size < options.length;

  // Get sort indicator icon
  const getSortIcon = () => {
    if (!showSortIndicator || !onSort) return null;

    switch (sortDirection) {
      case 'asc':
        return <ChevronUp className='h-3 w-3 opacity-70' />;
      case 'desc':
        return <ChevronDown className='h-3 w-3 opacity-70' />;
      default:
        return <ChevronsUpDown className='h-3 w-3 opacity-50' />;
    }
  };

  return (
    <div className='flex items-center gap-1'>
      {/* Sortable title */}
      {onSort && (
        <div
          onClick={onSort}
          className='flex items-center gap-1 text-xs font-medium hover:text-accent-foreground transition-colors cursor-pointer'
        >
          <span>{title}</span>
          {getSortIcon()}
        </div>
      )}

      {/* Filter dropdown */}
      <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
        <DropdownMenuTrigger asChild>
          <div
            className={`h-6 w-6 p-0.5 text-xs font-medium relative group cursor-pointer flex items-center justify-center rounded border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground transition-colors ${
              hasActiveFilter ? 'bg-blue-50 text-blue-700 border-blue-200' : ''
            }`}
            title={`Filter ${title}`}
          >
            <Filter className='h-3 w-3' />
            {hasActiveFilter && (
              <Badge
                variant='secondary'
                className='absolute -top-1 -right-1 h-3 w-3 p-0 text-xs flex items-center justify-center'
              >
                {selectedValues.size}
              </Badge>
            )}
          </div>
        </DropdownMenuTrigger>

        <DropdownMenuContent align='start' className='w-64'>
          <DropdownMenuLabel className='flex items-center justify-between'>
            <span className='text-sm font-medium'>{title} Filter</span>
            {hasActiveFilter && (
              <Button
                variant='ghost'
                size='sm'
                onClick={handleClearAll}
                className='h-6 px-2 text-xs'
              >
                <X className='h-3 w-3' />
              </Button>
            )}
          </DropdownMenuLabel>

          <DropdownMenuSeparator />

          {/* Search input */}
          <div className='p-2'>
            <Input
              placeholder={searchPlaceholder}
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className='h-8 text-xs'
            />
          </div>

          <DropdownMenuSeparator />

          {/* Action buttons */}
          <div className='flex gap-1 p-2'>
            <Button
              variant='outline'
              size='sm'
              onClick={handleSelectAll}
              className='flex-1 h-6 text-xs'
            >
              Select All
            </Button>
            <Button
              variant='outline'
              size='sm'
              onClick={handleSelectVisible}
              className='flex-1 h-6 text-xs'
            >
              Select Visible
            </Button>
            <Button
              variant='outline'
              size='sm'
              onClick={handleClearAll}
              className='flex-1 h-6 text-xs'
            >
              Clear
            </Button>
          </div>

          <DropdownMenuSeparator />

          {/* Options list */}
          <div className='max-h-64 overflow-y-auto'>
            {filteredOptions.length === 0 ? (
              <div className='p-2 text-xs text-gray-500 text-center'>No options found</div>
            ) : (
              filteredOptions.map(option => (
                <DropdownMenuCheckboxItem
                  key={option.value}
                  checked={selectedValues.has(option.value)}
                  onCheckedChange={() => handleOptionToggle(option.value)}
                  className='text-xs'
                >
                  <div className='flex items-center justify-between w-full'>
                    <span className='truncate flex-1'>{option.label}</span>
                    {showCounts && (
                      <Badge variant='outline' className='ml-2 h-4 px-1 text-xs'>
                        {option.count}
                      </Badge>
                    )}
                  </div>
                </DropdownMenuCheckboxItem>
              ))
            )}
          </div>

          {/* Summary */}
          {hasActiveFilter && (
            <>
              <DropdownMenuSeparator />
              <div className='p-2 text-xs text-gray-500'>
                Showing {selectedValues.size} of {options.length} options
              </div>
            </>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
};

export default HeaderFilter;
