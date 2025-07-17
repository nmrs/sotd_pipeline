import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { checkHealth, getAvailableMonths, getCatalogs } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorDisplay from '../components/ErrorDisplay';

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
                    getAvailableMonths().then(months => months.length).catch(() => 0),
                    getCatalogs().then(catalogs => catalogs.length).catch(() => 0),
                ]);

                setStatus({
                    backend: backendHealth,
                    months,
                    catalogs,
                });
            } catch (err: any) {
                setError(err.message || 'Failed to check system status');
            } finally {
                setLoading(false);
            }
        };

        checkSystemStatus();
    }, []);

    const analyzerCards = [
        {
            title: 'Unmatched Analyzer',
            description: 'Identify unmatched items across selected months to find potential catalog additions.',
            icon: '🔍',
            color: 'blue',
            path: '/unmatched',
        },
        {
            title: 'Mismatch Analyzer',
            description: 'Analyze mismatched items to identify potential catalog conflicts and inconsistencies.',
            icon: '⚠️',
            color: 'green',
            path: '/mismatch',
        },
    ];

    if (loading) {
        return (
            <div className="max-w-6xl mx-auto p-6">
                <LoadingSpinner message="Checking system status..." />
            </div>
        );
    }

    if (error) {
        return (
            <div className="max-w-6xl mx-auto p-6">
                <ErrorDisplay error={error} onRetry={() => window.location.reload()} />
            </div>
        );
    }

    return (
        <div className="max-w-6xl mx-auto p-6">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">SOTD Pipeline Analyzer</h1>
                <p className="text-gray-600">
                    Web-based analysis tools for the Shave of the Day data processing pipeline.
                </p>
            </div>

            {/* System Status */}
            {status && (
                <div className="mb-8">
                    <h2 className="text-xl font-semibold text-gray-900 mb-4">System Status</h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className={`bg-white rounded-lg shadow p-4 border-l-4 ${status.backend ? 'border-green-500' : 'border-red-500'
                            }`}>
                            <div className="flex items-center">
                                <div className={`w-3 h-3 rounded-full mr-3 ${status.backend ? 'bg-green-500' : 'bg-red-500'
                                    }`}></div>
                                <div>
                                    <p className="text-sm font-medium text-gray-900">Backend API</p>
                                    <p className="text-xs text-gray-500">
                                        {status.backend ? 'Connected' : 'Disconnected'}
                                    </p>
                                </div>
                            </div>
                        </div>

                        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-blue-500">
                            <div className="flex items-center">
                                <div className="w-3 h-3 rounded-full bg-blue-500 mr-3"></div>
                                <div>
                                    <p className="text-sm font-medium text-gray-900">Available Months</p>
                                    <p className="text-xs text-gray-500">{status.months} months</p>
                                </div>
                            </div>
                        </div>

                        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-purple-500">
                            <div className="flex items-center">
                                <div className="w-3 h-3 rounded-full bg-purple-500 mr-3"></div>
                                <div>
                                    <p className="text-sm font-medium text-gray-900">Product Catalogs</p>
                                    <p className="text-xs text-gray-500">{status.catalogs} catalogs</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Analyzer Cards */}
            <div className="mb-8">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Analysis Tools</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {analyzerCards.map((card) => (
                        <Link
                            key={card.path}
                            to={card.path}
                            className="block bg-white rounded-lg shadow hover:shadow-lg transition-shadow duration-200"
                        >
                            <div className="p-6">
                                <div className="flex items-center mb-4">
                                    <span className="text-3xl mr-3">{card.icon}</span>
                                    <h3 className="text-lg font-semibold text-gray-900">{card.title}</h3>
                                </div>
                                <p className="text-gray-600 text-sm">{card.description}</p>
                                <div className="mt-4 flex items-center text-blue-600 text-sm font-medium">
                                    Open Tool
                                    <svg className="ml-1 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                    </svg>
                                </div>
                            </div>
                        </Link>
                    ))}
                </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-gray-50 rounded-lg p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
                <div className="space-y-3">
                    <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Check backend health</span>
                        <button
                            onClick={() => window.location.reload()}
                            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                        >
                            Refresh Status
                        </button>
                    </div>
                    <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">View available data</span>
                        <span className="text-sm text-gray-500">{status?.months || 0} months available</span>
                    </div>
                    <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Product catalogs</span>
                        <span className="text-sm text-gray-500">{status?.catalogs || 0} catalogs loaded</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard; 