import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { clearAllCachesComprehensive } from '../../utils/cache';
import { clearValidatorCache } from '../../services/api';
import { useMessaging } from '../../hooks/useMessaging';
import { DangerButton } from '../ui/reusable-buttons';
import { Menu, X, ChevronDown } from 'lucide-react';

const Header: React.FC = () => {
  const location = useLocation();
  const [cacheClearing, setCacheClearing] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);
  const messaging = useMessaging();

  const handleClearCache = async () => {
    try {
      setCacheClearing(true);

      // Clear frontend caches
      clearAllCachesComprehensive();

      // Clear backend validator caches
      await clearValidatorCache();

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

  const navigationGroups = [
    {
      label: 'Analyzers',
      icon: '📊',
      items: [
        { path: '/', label: 'Dashboard', icon: '🏠' },
        { path: '/unmatched-analyzer', label: 'Unmatched', icon: '🔍' },
        { path: '/mismatch', label: 'Match Analyzer', icon: '📊' },
        { path: '/soap-analyzer', label: 'Soap Analyzer', icon: '🧼' },
        { path: '/monthly-user-posts', label: 'Monthly User Posts', icon: '📅' },
      ],
    },
    {
      label: 'Validators',
      icon: '✅',
      items: [
        { path: '/catalog-validator', label: 'Catalog Validator', icon: '✅' },
        { path: '/brush-split-validator', label: 'Brush Validator', icon: '🪒' },
        { path: '/brush-validation', label: 'Brush Validation', icon: '🖊️' },
      ],
    },
    {
      label: 'Tools',
      icon: '🛠️',
      items: [
        { path: '/brush-matching-analyzer', label: 'Brush Matching', icon: '🧹' },
        { path: '/performance-test', label: 'Performance Test', icon: '⚡' },
      ],
    },
  ];

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false);
  };

  const toggleDropdown = (groupLabel: string) => {
    setOpenDropdown(openDropdown === groupLabel ? null : groupLabel);
  };

  const closeDropdown = () => {
    setOpenDropdown(null);
  };

  const renderNavItem = (item: { path: string; label: string; icon: string }) => (
    <Link
      key={item.path}
      to={item.path}
      onClick={closeMobileMenu}
      className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 whitespace-nowrap ${
        location.pathname === item.path
          ? 'bg-blue-100 text-blue-700'
          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
      }`}
    >
      <span>{item.icon}</span>
      <span>{item.label}</span>
    </Link>
  );

  const renderDropdownGroup = (group: (typeof navigationGroups)[0]) => (
    <div key={group.label} className='relative'>
      <button
        onClick={() => toggleDropdown(group.label)}
        onBlur={() => setTimeout(closeDropdown, 150)}
        className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 ${
          location.pathname === group.items.find(item => item.path === location.pathname)?.path
            ? 'bg-blue-100 text-blue-700'
            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
        }`}
      >
        <span>{group.icon}</span>
        <span>{group.label}</span>
        <ChevronDown
          className={`h-4 w-4 transition-transform ${openDropdown === group.label ? 'rotate-180' : ''}`}
        />
      </button>

      {openDropdown === group.label && (
        <div className='absolute top-full left-0 mt-1 w-56 bg-white border border-gray-200 rounded-md shadow-lg z-50'>
          <div className='py-1'>
            {group.items.map(item => (
              <Link
                key={item.path}
                to={item.path}
                onClick={closeDropdown}
                className={`flex items-center space-x-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 ${
                  location.pathname === item.path ? 'bg-blue-50 text-blue-700' : ''
                }`}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  return (
    <header className='bg-white shadow-sm border-b border-gray-200'>
      <div className='max-w-7xl mx-auto px-4'>
        <div className='flex items-center justify-between h-16'>
          {/* Logo and Brand */}
          <div className='flex items-center flex-shrink-0'>
            <Link to='/' className='flex items-center space-x-2'>
              <span className='text-2xl'>🪒</span>
              <span className='text-xl font-bold text-gray-900'>SOTD Analyzer</span>
            </Link>
          </div>

          {/* Desktop Grouped Navigation - Hidden on smaller screens */}
          <nav className='hidden lg:flex items-center space-x-2 flex-1 justify-center'>
            {navigationGroups.map(renderDropdownGroup)}
          </nav>

          {/* Desktop Cache Clear Button - Hidden on smaller screens */}
          <div className='hidden lg:flex items-center flex-shrink-0'>
            <DangerButton
              onClick={handleClearCache}
              disabled={cacheClearing}
              loading={cacheClearing}
              className='flex items-center space-x-2 px-3 py-2 text-sm'
            >
              <span>🗑️</span>
              <span>{cacheClearing ? 'Clearing...' : 'Clear Cache'}</span>
            </DangerButton>
          </div>

          {/* Mobile Menu Button and Cache Button - Always visible below lg */}
          <div className='lg:hidden flex items-center space-x-2'>
            <DangerButton
              onClick={handleClearCache}
              disabled={cacheClearing}
              loading={cacheClearing}
              className='flex items-center space-x-1 px-2 py-2 text-xs'
            >
              <span>🗑️</span>
              <span className='hidden sm:inline'>
                {cacheClearing ? 'Clearing...' : 'Clear Cache'}
              </span>
            </DangerButton>

            <button
              onClick={toggleMobileMenu}
              className='p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              aria-label='Toggle mobile menu'
            >
              {isMobileMenuOpen ? <X className='h-5 w-5' /> : <Menu className='h-5 w-5' />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Menu */}
        {isMobileMenuOpen && (
          <div className='lg:hidden border-t border-gray-200 bg-white'>
            <nav className='px-2 pt-2 pb-3 space-y-1 max-h-96 overflow-y-auto'>
              {navigationGroups.map(group => (
                <div key={group.label}>
                  <div className='px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide'>
                    {group.label}
                  </div>
                  {group.items.map(renderNavItem)}
                </div>
              ))}
            </nav>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;
