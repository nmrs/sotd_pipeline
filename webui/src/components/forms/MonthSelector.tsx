import React, { useState, useEffect, useRef } from 'react';
import { Checkbox } from '@/components/ui/checkbox';
import { useAvailableMonths } from '../../hooks/useAvailableMonths';
import LoadingSpinner from '../layout/LoadingSpinner';
import ErrorDisplay from '../feedback/ErrorDisplay';
import { SelectInput } from '../ui/reusable-forms';
import { SecondaryButton } from '../ui/reusable-buttons';
import { getYearToDateMonths, getLast12Months } from '../../utils/dateUtils';
import { calculateDeltaMonths, formatDeltaMonths } from '../../utils/deltaMonths';

interface MonthSelectorProps {
  selectedMonths: string[];
  onMonthsChange: (months: string[]) => void;
  multiple?: boolean;
  label?: string;
  enableDeltaMonths?: boolean;
  onDeltaMonthsChange?: (deltaMonths: string[]) => void;
}

const MonthSelector: React.FC<MonthSelectorProps> = ({
  selectedMonths,
  onMonthsChange,
  multiple = true,
  label = 'Months',
  enableDeltaMonths = false,
  onDeltaMonthsChange,
}) => {
  const { availableMonths, loading, error } = useAvailableMonths();
  const [isOpen, setIsOpen] = useState(false);
  const [deltaMonthsEnabled, setDeltaMonthsEnabled] = useState(false);
  const [primaryMonths, setPrimaryMonths] = useState<string[]>(selectedMonths);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Sync primaryMonths when selectedMonths prop changes externally
  useEffect(() => {
    // Only update if delta is not enabled, or if the change doesn't match our internal state
    if (!deltaMonthsEnabled) {
      setPrimaryMonths(selectedMonths);
    }
  }, [selectedMonths, deltaMonthsEnabled]);

  // Calculate delta months from primary months when enabled
  const deltaCalculation = deltaMonthsEnabled ? calculateDeltaMonths(primaryMonths) : null;
  // Note: effectiveSelectedMonths is only used for display, not for filtering delta months
  const effectiveSelectedMonths =
    deltaMonthsEnabled && deltaCalculation ? deltaCalculation.allMonths : selectedMonths;

  // Generate months from 2016-05 to current month
  const generatePrepopulatedMonths = (): string[] => {
    const months: string[] = [];
    const startDate = new Date(2016, 4, 1); // May 2016 (month is 0-indexed)
    const currentDate = new Date();

    const current = new Date(startDate);
    while (current <= currentDate) {
      const year = current.getFullYear();
      const month = String(current.getMonth() + 1).padStart(2, '0');
      months.push(`${year}-${month}`);

      // Move to next month
      current.setMonth(current.getMonth() + 1);
    }

    // Ensure current month is included (in case the loop logic missed it)
    const currentYear = currentDate.getFullYear();
    const currentMonth = String(currentDate.getMonth() + 1).padStart(2, '0');
    const currentMonthStr = `${currentYear}-${currentMonth}`;

    if (!months.includes(currentMonthStr)) {
      months.push(currentMonthStr);
    }

    // Sort in descending order (newest first)
    return months.sort((a, b) => b.localeCompare(a));
  };

  // Use pre-populated months initially, then merge with API results
  const [prepopulatedMonths] = useState<string[]>(generatePrepopulatedMonths());
  const effectiveAvailableMonths =
    availableMonths.length > 0 ? availableMonths : prepopulatedMonths;

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen]);

  const handleMonthChange = (month: string, checked: boolean) => {
    if (checked) {
      // Adding a month
      if (deltaMonthsEnabled && deltaCalculation) {
        // Check if this is a delta month being manually re-checked
        const isDelta = deltaCalculation.deltaMonths.includes(month);
        if (isDelta) {
          // It's a delta month, just add it back to selectedMonths
          const newSelectedMonths = [...selectedMonths, month];
          onMonthsChange(newSelectedMonths);
          return;
        }
      }

      // It's a primary month being added
      let newPrimaryMonths: string[];
      if (multiple) {
        newPrimaryMonths = [...primaryMonths, month];
      } else {
        newPrimaryMonths = [month];
      }

      setPrimaryMonths(newPrimaryMonths);

      // If delta is enabled, recalculate delta and merge
      if (deltaMonthsEnabled) {
        const newDeltaCalc = calculateDeltaMonths(newPrimaryMonths);
        if (newDeltaCalc) {
          const allMonths = [...new Set([...newPrimaryMonths, ...newDeltaCalc.deltaMonths])];
          updateMonthsAndDelta(allMonths, newPrimaryMonths);
        } else {
          updateMonthsAndDelta(newPrimaryMonths, newPrimaryMonths);
        }
      } else {
        // Delta not enabled, just update selectedMonths
        const newSelectedMonths = multiple ? [...selectedMonths, month] : [month];
        updateMonthsAndDelta(newSelectedMonths, newPrimaryMonths);
      }
    } else {
      // Removing a month
      if (deltaMonthsEnabled && deltaCalculation) {
        // Check if this is a delta month
        const isDelta = deltaCalculation.deltaMonths.includes(month);
        if (isDelta) {
          // Remove delta month and disable delta checkbox
          const newSelectedMonths = selectedMonths.filter(m => m !== month);
          setDeltaMonthsEnabled(false);
          if (onDeltaMonthsChange) {
            onDeltaMonthsChange([]);
          }
          onMonthsChange(newSelectedMonths);
          return;
        }
      }

      // It's a primary month being removed
      let newPrimaryMonths = primaryMonths.filter(m => m !== month);
      setPrimaryMonths(newPrimaryMonths);

      if (deltaMonthsEnabled) {
        // Recalculate delta months from updated primary months
        const newDeltaCalc = calculateDeltaMonths(newPrimaryMonths);
        if (newDeltaCalc) {
          const allMonths = [...new Set([...newPrimaryMonths, ...newDeltaCalc.deltaMonths])];
          updateMonthsAndDelta(allMonths, newPrimaryMonths);
        } else {
          updateMonthsAndDelta(newPrimaryMonths, newPrimaryMonths);
        }
      } else {
        // Delta not enabled, just remove from selectedMonths
        const newSelectedMonths = multiple
          ? selectedMonths.filter(m => m !== month)
          : [];
        if (!multiple) {
          newPrimaryMonths = [];
        }
        updateMonthsAndDelta(newSelectedMonths, newPrimaryMonths);
      }
    }
  };

  const handleDeltaMonthsToggle = (enabled: boolean) => {
    if (enabled) {
      // Store current selectedMonths as primary months
      setPrimaryMonths(selectedMonths);
      // Calculate delta months from primary months
      const newDeltaCalculation = calculateDeltaMonths(selectedMonths);
      if (newDeltaCalculation) {
        // Merge primary + delta months into selectedMonths
        const allMonths = [...new Set([...selectedMonths, ...newDeltaCalculation.deltaMonths])];
        onMonthsChange(allMonths);
        if (onDeltaMonthsChange) {
          onDeltaMonthsChange(newDeltaCalculation.deltaMonths);
        }
      }
      setDeltaMonthsEnabled(true);
    } else {
      // Filter out all delta months, keep only primary months
      if (deltaCalculation) {
        onMonthsChange(primaryMonths);
      } else {
        onMonthsChange(selectedMonths);
      }
      if (onDeltaMonthsChange) {
        onDeltaMonthsChange([]);
      }
      setDeltaMonthsEnabled(false);
    }
  };

  const updateMonthsAndDelta = (newMonths: string[], newPrimaryMonths?: string[]) => {
    onMonthsChange(newMonths);

    // Update primary months if provided
    if (newPrimaryMonths !== undefined) {
      setPrimaryMonths(newPrimaryMonths);
    }

    // Update delta months if enabled
    if (deltaMonthsEnabled && onDeltaMonthsChange) {
      const primaryForDelta = newPrimaryMonths !== undefined ? newPrimaryMonths : primaryMonths;
      const newDeltaCalculation = calculateDeltaMonths(primaryForDelta);
      if (newDeltaCalculation) {
        onDeltaMonthsChange(newDeltaCalculation.deltaMonths);
      }
    }
  };

  const selectAll = () => {
    const allMonths = [...effectiveAvailableMonths];
    setPrimaryMonths(allMonths);
    if (deltaMonthsEnabled) {
      const deltaCalc = calculateDeltaMonths(allMonths);
      if (deltaCalc) {
        const allWithDelta = [...new Set([...allMonths, ...deltaCalc.deltaMonths])];
        updateMonthsAndDelta(allWithDelta, allMonths);
      } else {
        updateMonthsAndDelta(allMonths, allMonths);
      }
    } else {
      updateMonthsAndDelta(allMonths, allMonths);
    }
  };

  const clearAll = () => {
    setPrimaryMonths([]);
    updateMonthsAndDelta([], []);
  };

  const selectYearToDate = () => {
    const ytdMonths = getYearToDateMonths();
    // Only select months that are available in the system
    const availableYtdMonths = ytdMonths.filter(month => effectiveAvailableMonths.includes(month));
    setPrimaryMonths(availableYtdMonths);
    if (deltaMonthsEnabled) {
      const deltaCalc = calculateDeltaMonths(availableYtdMonths);
      if (deltaCalc) {
        const allWithDelta = [...new Set([...availableYtdMonths, ...deltaCalc.deltaMonths])];
        updateMonthsAndDelta(allWithDelta, availableYtdMonths);
      } else {
        updateMonthsAndDelta(availableYtdMonths, availableYtdMonths);
      }
    } else {
      updateMonthsAndDelta(availableYtdMonths, availableYtdMonths);
    }
  };

  const selectLast12Months = () => {
    const last12Months = getLast12Months();
    setPrimaryMonths(last12Months);
    if (deltaMonthsEnabled) {
      const deltaCalc = calculateDeltaMonths(last12Months);
      if (deltaCalc) {
        const allWithDelta = [...new Set([...last12Months, ...deltaCalc.deltaMonths])];
        updateMonthsAndDelta(allWithDelta, last12Months);
      } else {
        updateMonthsAndDelta(last12Months, last12Months);
      }
    } else {
      updateMonthsAndDelta(last12Months, last12Months);
    }
  };

  const isDeltaMonth = (month: string): boolean => {
    if (!deltaMonthsEnabled || !deltaCalculation) return false;
    return deltaCalculation.deltaMonths.includes(month);
  };

  const getDisplayText = () => {
    if (effectiveSelectedMonths.length === 0) {
      return 'Select Months';
    }
    if (effectiveSelectedMonths.length === 1) {
      return effectiveSelectedMonths[0];
    }
    if (effectiveSelectedMonths.length <= 3) {
      return effectiveSelectedMonths.join(', ');
    }

    // Only show delta months count if they're actually enabled and available
    if (deltaMonthsEnabled && deltaCalculation && deltaCalculation.deltaMonths.length > 0) {
      return formatDeltaMonths(deltaCalculation);
    }

    return `${effectiveSelectedMonths.length} months selected`;
  };

  // Show loading spinner only if we have no pre-populated months and API is still loading
  if (loading && prepopulatedMonths.length === 0) {
    return <LoadingSpinner message='Loading available months...' />;
  }

  if (error && prepopulatedMonths.length === 0) {
    return <ErrorDisplay error={error} onRetry={() => window.location.reload()} />;
  }

  if (!multiple) {
    // Single select mode using reusable SelectInput
    const options = effectiveAvailableMonths.map(month => ({
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
        <div className='absolute top-full left-0 mt-1 bg-white border border-gray-300 rounded-md shadow-lg z-10 max-h-60 overflow-y-auto min-w-[300px]'>
          <div className='p-2'>
            <div className='flex items-center gap-2 mb-2 pb-2 border-b border-gray-200'>
              <SecondaryButton onClick={selectAll} className='text-xs'>
                Select All
              </SecondaryButton>
              <SecondaryButton onClick={selectYearToDate} className='text-xs'>
                Year to Date
              </SecondaryButton>
              <SecondaryButton onClick={selectLast12Months} className='text-xs'>
                Last 12 Months
              </SecondaryButton>
              <SecondaryButton onClick={clearAll} className='text-xs'>
                Clear All
              </SecondaryButton>
            </div>

            {enableDeltaMonths && (
              <div className='flex items-center gap-2 mb-2 pb-2 border-b border-gray-200'>
                <label className='flex items-center space-x-2 text-xs text-gray-700'>
                  <Checkbox
                    checked={deltaMonthsEnabled}
                    onCheckedChange={handleDeltaMonthsToggle}
                  />
                  <span>Include Delta Months</span>
                </label>
                {deltaMonthsEnabled && deltaCalculation && (
                  <span className='text-xs text-gray-500'>
                    +{deltaCalculation.deltaMonths.length} historical months
                  </span>
                )}
                {!deltaMonthsEnabled && (
                  <span className='text-xs text-gray-400'>
                    Check to include historical comparison months
                  </span>
                )}
              </div>
            )}

            {effectiveAvailableMonths.length === 0 ? (
              <p className='text-gray-500 text-sm py-2'>No months available</p>
            ) : (
              <div className='space-y-1'>
                {effectiveAvailableMonths.map(month => {
                  const isDelta = isDeltaMonth(month);
                  return (
                    <label
                      key={month}
                      className='flex items-center space-x-2 py-1 hover:bg-gray-50 rounded px-1 cursor-pointer'
                    >
                      <Checkbox
                        checked={selectedMonths.includes(month)}
                        onCheckedChange={checked => handleMonthChange(month, checked as boolean)}
                      />
                      <span
                        className={`text-sm ${isDelta ? 'text-gray-500 italic' : 'text-gray-700'}`}
                      >
                        {month}
                        {isDelta && <span className='ml-1 text-xs'>(delta)</span>}
                      </span>
                    </label>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default MonthSelector;
