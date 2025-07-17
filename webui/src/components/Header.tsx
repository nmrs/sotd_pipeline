import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const Header: React.FC = () => {
    const location = useLocation();

    const navItems = [
        { path: '/', label: 'Dashboard', icon: '🏠' },
        { path: '/unmatched', label: 'Unmatched', icon: '🔍' },
        { path: '/mismatch', label: 'Mismatch', icon: '⚠️' },
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
                    </nav>
                </div>
            </div>
        </header>
    );
};

export default Header; 