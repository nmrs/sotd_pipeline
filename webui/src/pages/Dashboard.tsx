import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { checkHealth, getAvailableMonths, getCatalogs } from '../services/api';
import ErrorDisplay from '../components/feedback/ErrorDisplay';
import {
  PageLayout,
  SectionLayout,
  GridLayout,
  StatusCard,
  LoadingContainer,
} from '../components/ui/reusable-layout';

interface SystemStatus {
  backend: boolean;
  months: number;
  catalogs: number;
}

const Dashboard: React.FC = () => {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const checkSystemStatus = async () => {
      try {
        setLoading(true);
        setError(null);

        const [backendHealth, months, catalogs] = await Promise.all([
          checkHealth(),
          getAvailableMonths()
            .then(months => months.length)
            .catch(() => 0),
          getCatalogs()
            .then(catalogs => catalogs.length)
            .catch(() => 0),
        ]);

        setStatus({
          backend: backendHealth,
          months,
          catalogs,
        });
      } catch (err: unknown) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to check system status';
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    checkSystemStatus();
  }, []);

  const analyzerCards = [
    {
      title: 'Unmatched Analyzer',
      description:
        'Identify unmatched items across selected months to find potential catalog additions.',
      icon: '🔍',
      color: 'blue',
      path: '/unmatched',
    },
    {
      title: 'Mismatch Analyzer',
      description:
        'Analyze mismatched items to identify potential catalog conflicts and inconsistencies.',
      icon: '⚠️',
      color: 'green',
      path: '/mismatch',
    },
    {
      title: 'Soap Analyzer',
      description:
        'Analyze soap matches for duplicates and pattern suggestions to improve data quality.',
      icon: '🧼',
      color: 'purple',
      path: '/soap-analyzer',
    },
  ];

  if (error) {
    return (
      <PageLayout>
        <ErrorDisplay error={error} onRetry={() => window.location.reload()} />
      </PageLayout>
    );
  }

  return (
    <PageLayout>
      <LoadingContainer loading={loading} message='Checking system status...'>
        <SectionLayout
          title='SOTD Pipeline Analyzer'
          subtitle='Web-based analysis tools for the Shave of the Day data processing pipeline.'
        >
          {/* System Status */}
          {status && (
            <SectionLayout title='System Status'>
              <GridLayout cols={3}>
                <StatusCard
                  title='Backend Health'
                  value={status.backend ? 'Online' : 'Offline'}
                  status={status.backend ? 'success' : 'error'}
                  icon={status.backend ? '🟢' : '🔴'}
                />
                <StatusCard
                  title='Available Months'
                  value={status.months.toString()}
                  status='info'
                  icon='📅'
                />
                <StatusCard
                  title='Product Catalogs'
                  value={status.catalogs.toString()}
                  status='info'
                  icon='📚'
                />
              </GridLayout>
            </SectionLayout>
          )}

          {/* Analyzer Cards */}
          <SectionLayout title='Analysis Tools'>
            <GridLayout cols={4}>
              {analyzerCards.map(card => (
                <div
                  key={card.path}
                  className='bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow duration-200'
                >
                  <div className='flex items-center space-x-3 mb-4'>
                    <span className='text-2xl'>{card.icon}</span>
                    <h3 className='text-lg font-semibold text-gray-900'>{card.title}</h3>
                  </div>
                  <p className='text-gray-600 mb-4'>{card.description}</p>
                  <Link
                    to={card.path}
                    className={`inline-flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors duration-200 ${card.color === 'blue'
                      ? 'bg-blue-600 text-white hover:bg-blue-700'
                      : card.color === 'green'
                        ? 'bg-green-600 text-white hover:bg-green-700'
                        : card.color === 'purple'
                          ? 'bg-purple-600 text-white hover:bg-purple-700'
                          : 'bg-gray-600 text-white hover:bg-gray-700'
                      }`}
                  >
                    Open Tool
                    <svg
                      className='ml-2 h-4 w-4'
                      fill='none'
                      stroke='currentColor'
                      viewBox='0 0 24 24'
                    >
                      <path
                        strokeLinecap='round'
                        strokeLinejoin='round'
                        strokeWidth={2}
                        d='M9 5l7 7-7 7'
                      />
                    </svg>
                  </Link>
                </div>
              ))}
            </GridLayout>
          </SectionLayout>

          {/* Quick Actions */}
          <SectionLayout title='Quick Actions'>
            <div className='space-y-4'>
              <div className='bg-blue-50 border border-blue-200 rounded-lg p-4'>
                <h4 className='font-semibold text-blue-900 mb-2'>Getting Started</h4>
                <p className='text-blue-800 text-sm'>
                  Use the analysis tools above to examine your SOTD data. Start with the Unmatched
                  Analyzer to identify potential catalog additions.
                </p>
              </div>
              <div className='bg-green-50 border border-green-200 rounded-lg p-4'>
                <h4 className='font-semibold text-green-900 mb-2'>Data Management</h4>
                <p className='text-green-800 text-sm'>
                  All data is cached locally for performance. Use the &quot;Clear Cache&quot; button
                  in the header to refresh data after pipeline runs.
                </p>
              </div>
            </div>
          </SectionLayout>
        </SectionLayout>
      </LoadingContainer>
    </PageLayout>
  );
};

export default Dashboard;
