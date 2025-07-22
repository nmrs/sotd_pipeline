import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { clearAllCachesComprehensive } from '../../utils/cache';
import { useMessaging } from '../../hooks/useMessaging';

const Header: React.FC = () => {
    const location = useLocation();
    const [cacheClearing, setCacheClearing] = useState(false);
    const messaging = useMessaging();

    const handleClearCache = async () => {
        try {
            setCacheClearing(true);
            clearAllCachesComprehensive();
            messaging.addSuccessMessage('All caches cleared successfully', true);

            // Refresh the page to show fresh data
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } catch (error) {
            messaging.addErrorMessage('Failed to clear caches');
        } finally {
            setCacheClearing(false);
        }
    };

    const navItems = [
        { path: '/', label: 'Dashboard', icon: '🏠' },
        { path: '/unmatched-analyzer', label: 'Unmatched', icon: '🔍' },
        { path: '/brush-split-validator', label: 'Brush Validator', icon: '🪒' },
        { path: '/performance-test', label: 'Performance Test', icon: '⚡' },
    ];

    return (
        <header className="bg-white shadow-sm border-b border-gray-200">
            <div className="max-w-6xl mx-auto px-6">
                <div className="flex items-center justify-between h-16">
                    <div className="flex items-center">
                        <Link to="/" className="flex items-center space-x-2">
                            <span className="text-2xl">🪒</span>
                            <span className="text-xl font-bold text-gray-900">SOTD Analyzer</span>
                        </Link>
                    </div>

                    <nav className="flex space-x-8">
                        {navItems.map((item) => (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={`flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 ${location.pathname === item.path
                                    ? 'bg-blue-100 text-blue-700'
                                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                                    }`}
                            >
                                <span>{item.icon}</span>
                                <span>{item.label}</span>
                            </Link>
                        ))}

                        {/* Cache Expiration Button */}
                        <button
                            onClick={handleClearCache}
                            disabled={cacheClearing}
                            className="flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 text-red-600 hover:text-red-700 hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed"
                            title="Clear all caches (useful after pipeline reruns)"
                        >
                            <span>🗑️</span>
                            <span>{cacheClearing ? 'Clearing...' : 'Clear Cache'}</span>
                        </button>
                    </nav>
                </div>
            </div>
        </header>
    );
};

export default Header; 