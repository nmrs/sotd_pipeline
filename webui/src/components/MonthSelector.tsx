import React, { useState, useEffect, useRef } from 'react';
import { getAvailableMonths } from '../services/api';
import LoadingSpinner from './LoadingSpinner';
import ErrorDisplay from './ErrorDisplay';

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
    label = 'Select Months'
}) => {
    const [availableMonths, setAvailableMonths] = useState<string[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const fetchMonths = async () => {
            try {
                setLoading(true);
                setError(null);
                const months = await getAvailableMonths();
                setAvailableMonths(months.sort().reverse()); // Sort newest first
            } catch (err: any) {
                setError(err.message || 'Failed to load available months');
            } finally {
                setLoading(false);
            }
        };

        fetchMonths();
    }, []);

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
        return <LoadingSpinner message="Loading available months..." />;
    }

    if (error) {
        return <ErrorDisplay error={error} onRetry={() => window.location.reload()} />;
    }

    return (
        <div className="relative" ref={dropdownRef}>
            <button
                type="button"
                onClick={() => setIsOpen(!isOpen)}
                className="w-full flex items-center justify-between px-3 py-2 text-sm border border-gray-300 rounded-md bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
                <span className="text-gray-700">{getDisplayText()}</span>
                <svg
                    className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
            </button>

            {isOpen && (
                <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-y-auto">
                    <div className="p-2">
                        {multiple && (
                            <div className="flex items-center justify-between mb-2 pb-2 border-b border-gray-200">
                                <span className="text-xs font-medium text-gray-700">Quick Actions</span>
                                <div className="space-x-2">
                                    <button
                                        type="button"
                                        onClick={selectAll}
                                        className="text-xs text-blue-600 hover:text-blue-800"
                                    >
                                        Select All
                                    </button>
                                    <button
                                        type="button"
                                        onClick={clearAll}
                                        className="text-xs text-gray-600 hover:text-gray-800"
                                    >
                                        Clear All
                                    </button>
                                </div>
                            </div>
                        )}

                        {availableMonths.length === 0 ? (
                            <p className="text-gray-500 text-sm py-2">No months available</p>
                        ) : (
                            <div className="space-y-1">
                                {availableMonths.map((month) => (
                                    <label key={month} className="flex items-center space-x-2 py-1 hover:bg-gray-50 rounded px-1 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={selectedMonths.includes(month)}
                                            onChange={(e) => handleMonthChange(month, e.target.checked)}
                                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                        />
                                        <span className="text-sm text-gray-700">{month}</span>
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