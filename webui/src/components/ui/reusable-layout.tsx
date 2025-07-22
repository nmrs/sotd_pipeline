'use client';

import React from 'react';
import { cn } from '@/lib/utils';

// Page Layout - Main page container
interface PageLayoutProps {
  children: React.ReactNode;
  className?: string;
}

export const PageLayout: React.FC<PageLayoutProps> = ({ children, className }) => {
  return (
    <div className={cn('min-h-screen bg-gray-50', className)}>
      <div className='max-w-6xl mx-auto p-6'>{children}</div>
    </div>
  );
};

// Card Layout - Content container with shadow and border
interface CardLayoutProps {
  children: React.ReactNode;
  className?: string;
  padding?: 'sm' | 'md' | 'lg';
}

export const CardLayout: React.FC<CardLayoutProps> = ({ children, className, padding = 'md' }) => {
  const paddingClasses = {
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };

  return (
    <div
      className={cn(
        'bg-white rounded-lg border border-gray-200 shadow-sm',
        paddingClasses[padding],
        className
      )}
    >
      {children}
    </div>
  );
};

// Section Layout - Content section with title
interface SectionLayoutProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  className?: string;
}

export const SectionLayout: React.FC<SectionLayoutProps> = ({
  children,
  title,
  subtitle,
  className,
}) => {
  return (
    <section className={cn('space-y-4', className)}>
      {(title || subtitle) && (
        <div className='space-y-2'>
          {title && <h2 className='text-xl font-semibold text-gray-900'>{title}</h2>}
          {subtitle && <p className='text-gray-600'>{subtitle}</p>}
        </div>
      )}
      {children}
    </section>
  );
};

// Grid Layout - Responsive grid container
interface GridLayoutProps {
  children: React.ReactNode;
  cols?: 1 | 2 | 3 | 4 | 6;
  gap?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const GridLayout: React.FC<GridLayoutProps> = ({
  children,
  cols = 1,
  gap = 'md',
  className,
}) => {
  const gridCols = {
    1: 'grid-cols-1',
    2: 'grid-cols-1 md:grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4',
    6: 'grid-cols-2 md:grid-cols-3 lg:grid-cols-6',
  };

  const gapClasses = {
    sm: 'gap-3',
    md: 'gap-4',
    lg: 'gap-6',
  };

  return <div className={cn('grid', gridCols[cols], gapClasses[gap], className)}>{children}</div>;
};

// Flex Layout - Flexible container
interface FlexLayoutProps {
  children: React.ReactNode;
  direction?: 'row' | 'col';
  justify?: 'start' | 'end' | 'center' | 'between' | 'around' | 'evenly';
  align?: 'start' | 'end' | 'center' | 'baseline' | 'stretch';
  gap?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const FlexLayout: React.FC<FlexLayoutProps> = ({
  children,
  direction = 'row',
  justify = 'start',
  align = 'start',
  gap = 'md',
  className,
}) => {
  const directionClasses = {
    row: 'flex-row',
    col: 'flex-col',
  };

  const justifyClasses = {
    start: 'justify-start',
    end: 'justify-end',
    center: 'justify-center',
    between: 'justify-between',
    around: 'justify-around',
    evenly: 'justify-evenly',
  };

  const alignClasses = {
    start: 'items-start',
    end: 'items-end',
    center: 'items-center',
    baseline: 'items-baseline',
    stretch: 'items-stretch',
  };

  const gapClasses = {
    sm: 'gap-2',
    md: 'gap-4',
    lg: 'gap-6',
  };

  return (
    <div
      className={cn(
        'flex',
        directionClasses[direction],
        justifyClasses[justify],
        alignClasses[align],
        gapClasses[gap],
        className
      )}
    >
      {children}
    </div>
  );
};

// Status Card - For displaying status information
interface StatusCardProps {
  title: string;
  value: string | number;
  status?: 'success' | 'warning' | 'error' | 'info';
  icon?: React.ReactNode;
  className?: string;
}

export const StatusCard: React.FC<StatusCardProps> = ({
  title,
  value,
  status = 'info',
  icon,
  className,
}) => {
  const statusClasses = {
    success: 'border-green-500 bg-green-50',
    warning: 'border-yellow-500 bg-yellow-50',
    error: 'border-red-500 bg-red-50',
    info: 'border-blue-500 bg-blue-50',
  };

  const statusTextClasses = {
    success: 'text-green-700',
    warning: 'text-yellow-700',
    error: 'text-red-700',
    info: 'text-blue-700',
  };

  return (
    <CardLayout className={cn('border-l-4', statusClasses[status], className)}>
      <div className='flex items-center justify-between'>
        <div>
          <p className='text-sm font-medium text-gray-600'>{title}</p>
          <p className={cn('text-2xl font-bold', statusTextClasses[status])}>{value}</p>
        </div>
        {icon && <div className='text-2xl'>{icon}</div>}
      </div>
    </CardLayout>
  );
};

// Loading Container - For loading states
interface LoadingContainerProps {
  children: React.ReactNode;
  loading: boolean;
  message?: string;
  className?: string;
}

export const LoadingContainer: React.FC<LoadingContainerProps> = ({
  children,
  loading,
  message = 'Loading...',
  className,
}) => {
  if (loading) {
    return (
      <div className={cn('flex items-center justify-center p-8', className)}>
        <div className='text-center'>
          <div className='animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2'></div>
          <p className='text-gray-600'>{message}</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};

// Empty State - For when there's no data
interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon,
  action,
  className,
}) => {
  return (
    <div className={cn('text-center py-12', className)}>
      {icon && <div className='mx-auto h-12 w-12 text-gray-400 mb-4'>{icon}</div>}
      <h3 className='text-lg font-medium text-gray-900 mb-2'>{title}</h3>
      {description && <p className='text-gray-600 mb-4'>{description}</p>}
      {action && <div className='mt-6'>{action}</div>}
    </div>
  );
};
