import React, { useState, useEffect, useRef } from 'react';
import { Checkbox } from '@/components/ui/checkbox';
import { useAvailableMonths } from '../../hooks/useAvailableMonths';
import LoadingSpinner from '../layout/LoadingSpinner';
import ErrorDisplay from '../feedback/ErrorDisplay';
import { SelectInput } from '../ui/reusable-forms';
import { SecondaryButton } from '../ui/reusable-buttons';

interface MonthSelectorProps {
  selectedMonths: string[];
  onMonthsChange: (months: string[]) => void;
  multiple?: boolean;
  label?: string;
}

const MonthSelector: React.FC<MonthSelectorProps> = ({
  selectedMonths,
  onMonthsChange,
  multiple = true,
  label = 'Months',
}) => {
  const { availableMonths, loading, error } = useAvailableMonths();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleMonthChange = (month: string, checked: boolean) => {
    if (multiple) {
      if (checked) {
        onMonthsChange([...selectedMonths, month]);
      } else {
        onMonthsChange(selectedMonths.filter(m => m !== month));
      }
    } else {
      onMonthsChange(checked ? [month] : []);
    }
  };

  const selectAll = () => {
    onMonthsChange([...availableMonths]);
  };

  const clearAll = () => {
    onMonthsChange([]);
  };

  const getDisplayText = () => {
    if (selectedMonths.length === 0) {
      return 'Select Months';
    }
    if (selectedMonths.length === 1) {
      return selectedMonths[0];
    }
    if (selectedMonths.length <= 3) {
      return selectedMonths.join(', ');
    }
    return `${selectedMonths.length} months selected`;
  };

  if (loading) {
    return <LoadingSpinner message='Loading available months...' />;
  }

  if (error) {
    return <ErrorDisplay error={error} onRetry={() => window.location.reload()} />;
  }

  if (!multiple) {
    // Single select mode using reusable SelectInput
    const options = availableMonths.map(month => ({
      value: month,
      label: month,
    }));

    return (
      <SelectInput
        value={selectedMonths[0] || ''}
        onChange={value => onMonthsChange(value ? [value] : [])}
        options={options}
        label={label}
        placeholder='Select a month'
      />
    );
  }

  // Multiple select mode with custom dropdown
  return (
    <div className='relative' ref={dropdownRef}>
      <div className='flex items-center space-x-2'>
        {label && <label className='text-sm font-medium text-gray-700'>{label}:</label>}
        <SecondaryButton
          onClick={() => setIsOpen(!isOpen)}
          className='min-w-[200px] justify-between'
        >
          <span className='truncate'>{getDisplayText()}</span>
          <svg
            className={`w-4 h-4 ml-2 transition-transform ${isOpen ? 'rotate-180' : ''}`}
            fill='none'
            stroke='currentColor'
            viewBox='0 0 24 24'
          >
            <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M19 9l-7 7-7-7' />
          </svg>
        </SecondaryButton>
      </div>

      {isOpen && (
        <div className='absolute top-full left-0 mt-1 w-full bg-white border border-gray-300 rounded-md shadow-lg z-10 max-h-60 overflow-y-auto'>
          <div className='p-2'>
            <div className='flex justify-between items-center mb-2 pb-2 border-b border-gray-200'>
              <SecondaryButton onClick={selectAll} className='text-xs'>
                Select All
              </SecondaryButton>
              <SecondaryButton onClick={clearAll} className='text-xs'>
                Clear All
              </SecondaryButton>
            </div>

            {availableMonths.length === 0 ? (
              <p className='text-gray-500 text-sm py-2'>No months available</p>
            ) : (
              <div className='space-y-1'>
                {availableMonths.map(month => (
                  <label
                    key={month}
                    className='flex items-center space-x-2 py-1 hover:bg-gray-50 rounded px-1 cursor-pointer'
                  >
                    <Checkbox
                      checked={selectedMonths.includes(month)}
                      onCheckedChange={checked => handleMonthChange(month, checked as boolean)}
                    />
                    <span className='text-sm text-gray-700'>{month}</span>
                  </label>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default MonthSelector;
