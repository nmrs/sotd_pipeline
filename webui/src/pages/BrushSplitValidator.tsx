import React, { useState, useEffect } from 'react';
import MonthSelector from '../components/forms/MonthSelector';
import { BrushSplitTable } from '../components/data/BrushSplitTable';
import { BrushSplit } from '../types/brushSplit';

interface LoadResponse {
  brush_splits: BrushSplit[];
  statistics: any;
}

const BrushSplitValidator: React.FC = () => {
  const [brushSplits, setBrushSplits] = useState<BrushSplit[]>([]);
  const [selectedRows, setSelectedRows] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedMonths, setSelectedMonths] = useState<string[]>([]);

  useEffect(() => {
    if (selectedMonths.length === 0) {
      setBrushSplits([]);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);

    // Build query parameters for the API call
    const queryParams = selectedMonths
      .map(month => `months=${encodeURIComponent(month)}`)
      .join('&');

    fetch(`/api/brush-splits/load?${queryParams}`)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
      })
      .then((data: LoadResponse) => {
        setBrushSplits(data.brush_splits);
        setLoading(false);
      })
      .catch(error => {
        console.error('Failed to load brush splits:', error);
        setError('Error loading brush splits');
        setLoading(false);
      });
  }, [selectedMonths]);

  return (
    <div data-testid='brush-split-validator' className='h-screen flex flex-col'>
      {/* Sticky Header */}
      <div className='sticky top-0 z-20 bg-white border-b border-gray-200 p-4 shadow-sm'>
        <h1 className='text-2xl font-bold text-gray-900 mb-4'>Brush Split Validator</h1>

        {/* Month Selection */}
        <div className='mb-4'>
          <label className='block text-sm font-medium text-gray-700 mb-2'>
            Select Months to Analyze:
          </label>
          <MonthSelector
            selectedMonths={selectedMonths}
            onMonthsChange={setSelectedMonths}
            multiple={true}
          />
        </div>

        {/* Status Information */}
        {selectedMonths.length > 0 && (
          <div className='text-sm text-gray-600'>
            <p>Total brush splits: {brushSplits.length}</p>
            <p>Selected months: {selectedMonths.join(', ')}</p>
          </div>
        )}
      </div>

      {/* Scrollable Content */}
      <div className='flex-1 overflow-hidden'>
        {loading ? (
          <div className='flex items-center justify-center h-full'>
            <div className='text-lg text-gray-600'>Loading...</div>
          </div>
        ) : error ? (
          <div className='flex items-center justify-center h-full'>
            <div className='text-lg text-red-600'>{error}</div>
          </div>
        ) : selectedMonths.length === 0 ? (
          <div className='flex items-center justify-center h-full'>
            <div className='text-lg text-gray-600'>
              Please select at least one month to analyze brush splits.
            </div>
          </div>
        ) : (
          <div className='h-full p-4'>
            <BrushSplitTable
              brushSplits={brushSplits}
              onSelectionChange={selectedIndices => {
                setSelectedRows(new Set(selectedIndices));
              }}
              onSave={(index, updatedData) => {
                const newSplits = [...brushSplits];
                newSplits[index] = { ...newSplits[index], ...updatedData };
                setBrushSplits(newSplits);
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default BrushSplitValidator;
