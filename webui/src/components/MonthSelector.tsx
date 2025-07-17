import React, { useState, useEffect } from 'react';
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

    if (loading) {
        return <LoadingSpinner message="Loading available months..." />;
    }

    if (error) {
        return <ErrorDisplay error={error} onRetry={() => window.location.reload()} />;
    }

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <label className="block text-sm font-medium text-gray-700">
                    {label}
                </label>
                {multiple && (
                    <div className="space-x-2">
                        <button
                            type="button"
                            onClick={selectAll}
                            className="text-sm text-blue-600 hover:text-blue-800"
                        >
                            Select All
                        </button>
                        <button
                            type="button"
                            onClick={clearAll}
                            className="text-sm text-gray-600 hover:text-gray-800"
                        >
                            Clear All
                        </button>
                    </div>
                )}
            </div>

            <div className="max-h-60 overflow-y-auto border border-gray-300 rounded-md p-2">
                {availableMonths.length === 0 ? (
                    <p className="text-gray-500 text-sm py-2">No months available</p>
                ) : (
                    <div className="space-y-1">
                        {availableMonths.map((month) => (
                            <label key={month} className="flex items-center space-x-2 py-1 hover:bg-gray-50 rounded px-1">
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

            {selectedMonths.length > 0 && (
                <div className="text-sm text-gray-600">
                    Selected: {selectedMonths.length} month{selectedMonths.length !== 1 ? 's' : ''}
                </div>
            )}
        </div>
    );
};

export default MonthSelector; 