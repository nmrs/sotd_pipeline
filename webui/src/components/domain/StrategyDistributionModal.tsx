import React from 'react';
import { Badge } from '../ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { BarChart3, Info } from 'lucide-react';
import { StrategyDistributionStatistics } from '../../services/api';

interface StrategyDistributionModalProps {
  isOpen: boolean;
  onClose: () => void;
  statistics: StrategyDistributionStatistics | null;
  month: string;
}

const StrategyDistributionModal: React.FC<StrategyDistributionModalProps> = ({
  isOpen,
  onClose,
  statistics,
  month,
}) => {
  if (!statistics) {
    return null;
  }

  const formatStrategyName = (strategy: string) => {
    return strategy.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const formatLengthKey = (key: string) => {
    if (key === 'None') return 'Missing all_strategies';
    return `${key} strategy${key === '1' ? '' : 'ies'}`;
  };

  if (!isOpen || !statistics) {
    return null;
  }

  return (
    <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50'>
      <div className='bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto'>
        {/* Header */}
        <div className='flex items-center justify-between p-4 border-b border-gray-200'>
          <div className='flex items-center gap-2'>
            <BarChart3 className='h-5 w-5' />
            <h2 className='text-lg font-semibold text-gray-900'>
              Strategy Distribution Statistics - {month}
            </h2>
          </div>
          <button
            onClick={onClose}
            className='text-gray-400 hover:text-gray-600 transition-colors'
            aria-label='Close modal'
          >
            <svg className='w-6 h-6' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
              <path
                strokeLinecap='round'
                strokeLinejoin='round'
                strokeWidth={2}
                d='M6 18L18 6M6 6l12 12'
              />
            </svg>
          </button>
        </div>

        <div className='space-y-6'>
          {/* Overview Section */}
          <Card>
            <CardHeader>
              <CardTitle className='text-lg'>Overview</CardTitle>
            </CardHeader>
            <CardContent className='space-y-4'>
              <div className='grid grid-cols-1 md:grid-cols-3 gap-4'>
                <div className='text-center p-4 bg-blue-50 rounded-lg'>
                  <div className='text-2xl font-bold text-blue-600'>
                    {statistics.total_brush_records}
                  </div>
                  <div className='text-sm text-blue-800'>Total Brush Records</div>
                </div>
                <div className='text-center p-4 bg-green-50 rounded-lg'>
                  <div className='text-2xl font-bold text-green-600'>
                    {statistics.correct_matches_count}
                  </div>
                  <div className='text-sm text-green-800'>Already Validated</div>
                </div>
                <div className='text-center p-4 bg-orange-50 rounded-lg'>
                  <div className='text-2xl font-bold text-orange-600'>
                    {statistics.remaining_entries}
                  </div>
                  <div className='text-sm text-orange-800'>Need Validation</div>
                </div>
              </div>

              <div className='bg-blue-50 border border-blue-200 rounded-lg p-4'>
                <div className='flex items-start gap-2'>
                  <Info className='h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0' />
                  <div className='text-sm text-blue-800'>
                    <strong>Note:</strong> This data shows the complete distribution of brush
                    entries in the matched data file. The "Already Validated" count includes entries
                    with
                    <code className='bg-blue-100 px-1 rounded'>correct_complete_brush</code> and
                    <code className='bg-blue-100 px-1 rounded'>correct_split_brush</code> strategies
                    that are automatically filtered out of the validation interface.
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Strategy Counts Section */}
          <Card>
            <CardHeader>
              <CardTitle className='text-lg'>Strategy Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <div className='space-y-3'>
                {Object.entries(statistics.strategy_counts)
                  .sort(([, a], [, b]) => b - a) // Sort by count descending
                  .map(([strategy, count]) => (
                    <div
                      key={strategy}
                      className='flex items-center justify-between p-3 bg-gray-50 rounded-lg'
                    >
                      <div className='flex items-center gap-2'>
                        <Badge variant={strategy.includes('correct_') ? 'default' : 'secondary'}>
                          {formatStrategyName(strategy)}
                        </Badge>
                        {strategy.includes('correct_') && (
                          <Badge variant='outline' className='text-xs'>
                            Auto-validated
                          </Badge>
                        )}
                      </div>
                      <span className='font-medium text-lg'>{count}</span>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>

          {/* All Strategies Length Distribution */}
          <Card>
            <CardHeader>
              <CardTitle className='text-lg'>Strategy Array Length Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <div className='space-y-3'>
                {Object.entries(statistics.all_strategies_lengths)
                  .sort(([a], [b]) => {
                    // Sort numerically, with 'None' at the end
                    if (a === 'None') return 1;
                    if (b === 'None') return -1;
                    return parseInt(a) - parseInt(b);
                  })
                  .map(([length, count]) => (
                    <div
                      key={length}
                      className='flex items-center justify-between p-3 bg-gray-50 rounded-lg'
                    >
                      <div className='flex items-center gap-2'>
                        <Badge variant={length === 'None' ? 'destructive' : 'secondary'}>
                          {formatLengthKey(length)}
                        </Badge>
                        {length !== 'None' && (
                          <span className='text-sm text-gray-600'>
                            {parseInt(length) === 1 ? 'Single strategy' : 'Multiple strategies'}
                          </span>
                        )}
                      </div>
                      <span className='font-medium text-lg'>{count}</span>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>

          {/* Filter Count Analysis */}
          <Card>
            <CardHeader>
              <CardTitle className='text-lg'>Filter Count Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <div className='space-y-4'>
                <div className='bg-yellow-50 border border-yellow-200 rounded-lg p-4'>
                  <div className='text-sm text-yellow-800'>
                    <strong>Current Filter Logic:</strong> The frontend filter counts are calculated
                    from the current page's entries, not from the full dataset. This explains why
                    the filter counts don't match the total statistics.
                  </div>
                </div>

                <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
                  <div className='p-4 bg-gray-50 rounded-lg'>
                    <h4 className='font-medium mb-2'>Expected Filter Counts (Full Dataset)</h4>
                    <div className='space-y-2 text-sm'>
                      <div className='flex justify-between'>
                        <span>Single Strategy:</span>
                        <span className='font-medium'>
                          {statistics.all_strategies_lengths['1'] || 0}
                        </span>
                      </div>
                      <div className='flex justify-between'>
                        <span>Multiple Strategies:</span>
                        <span className='font-medium'>
                          {Object.entries(statistics.all_strategies_lengths)
                            .filter(([key]) => key !== 'None' && key !== '1')
                            .reduce((sum, [, count]) => sum + count, 0)}
                        </span>
                      </div>
                      <div className='flex justify-between'>
                        <span>Missing all_strategies:</span>
                        <span className='font-medium'>
                          {statistics.all_strategies_lengths['None'] || 0}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className='p-4 bg-gray-50 rounded-lg'>
                    <h4 className='font-medium mb-2'>Current Frontend Counts</h4>
                    <div className='space-y-2 text-sm'>
                      <div className='flex justify-between'>
                        <span>Single Strategy:</span>
                        <span className='font-medium text-blue-600'>11</span>
                      </div>
                      <div className='flex justify-between'>
                        <span>Multiple Strategies:</span>
                        <span className='font-medium text-blue-600'>9</span>
                      </div>
                      <div className='flex justify-between'>
                        <span>Total Categorized:</span>
                        <span className='font-medium text-blue-600'>20</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default StrategyDistributionModal;
