import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

interface DeltaMonthsInfoPanelProps {
  selectedMonths: string[];
  deltaMonths: string[];
  variant?: 'default' | 'card';
}

/**
 * DeltaMonthsInfoPanel displays information about primary and delta months for historical comparison.
 * When delta months are enabled, selectedMonths already contains all months (primary + delta).
 */
export const DeltaMonthsInfoPanel: React.FC<DeltaMonthsInfoPanelProps> = ({
  selectedMonths,
  deltaMonths,
  variant = 'default',
}) => {
  // Don't render if no delta months
  if (deltaMonths.length === 0) {
    return null;
  }

  // Calculate primary months by filtering out delta months from selectedMonths
  // When delta months are enabled, selectedMonths contains all months (primary + delta)
  const primaryMonths = selectedMonths.filter(month => !deltaMonths.includes(month));
  const totalMonths = selectedMonths.length; // selectedMonths already contains all months

  const content = (
    <>
      <p className={variant === 'card' ? 'mb-2' : 'mb-2'}>
        <strong>Historical Comparison:</strong> Including delta months for comprehensive analysis:
      </p>
      <ul className='list-disc list-inside ml-4 space-y-1'>
        <li>
          <strong>Primary months:</strong> {primaryMonths.join(', ')}
        </li>
        <li>
          <strong>Delta months:</strong> {deltaMonths.join(', ')}
        </li>
        <li>
          <strong>Total months:</strong> {totalMonths}
        </li>
      </ul>
      <p className='mt-2'>
        <strong>Delta months include:</strong> month-1, month-1year, month-5years for each selected
        month. This provides the same comprehensive view as the CLI <code>--delta</code> flag.
      </p>
    </>
  );

  if (variant === 'card') {
    return (
      <Card>
        <CardHeader>
          <CardTitle className='text-blue-900'>📊 Delta Months Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className='text-sm text-blue-700 space-y-1'>{content}</div>
        </CardContent>
      </Card>
    );
  }

  // Default variant (div-based)
  return (
    <div className='bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4'>
      <div className='flex items-start'>
        <div className='flex-shrink-0'>
          <svg className='h-5 w-5 text-blue-400' fill='currentColor' viewBox='0 0 20 20'>
            <path
              fillRule='evenodd'
              d='M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z'
              clipRule='evenodd'
            />
          </svg>
        </div>
        <div className='ml-3'>
          <h3 className='text-sm font-medium text-blue-800'>📊 Delta Months Analysis</h3>
          <div className='mt-2 text-sm text-blue-700'>{content}</div>
        </div>
      </div>
    </div>
  );
};

export default DeltaMonthsInfoPanel;

