'use client';

import React from 'react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

// Primary Action Button - Blue theme
interface PrimaryButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  loading?: boolean;
  className?: string;
  type?: 'button' | 'submit' | 'reset';
}

export const PrimaryButton: React.FC<PrimaryButtonProps> = ({
  children,
  onClick,
  disabled = false,
  loading = false,
  className,
  type = 'button',
}) => {
  return (
    <Button
      variant='default'
      onClick={onClick}
      disabled={disabled || loading}
      className={cn(
        'bg-blue-600 hover:bg-blue-700 text-white font-medium',
        'focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
        'transition-colors duration-200',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        className
      )}
      type={type}
    >
      {loading && (
        <svg className='animate-spin -ml-1 mr-2 h-4 w-4 text-white' fill='none' viewBox='0 0 24 24'>
          <circle
            className='opacity-25'
            cx='12'
            cy='12'
            r='10'
            stroke='currentColor'
            strokeWidth='4'
          />
          <path
            className='opacity-75'
            fill='currentColor'
            d='M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z'
          />
        </svg>
      )}
      {children}
    </Button>
  );
};

// Secondary Action Button - Gray theme
interface SecondaryButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
  type?: 'button' | 'submit' | 'reset';
}

export const SecondaryButton: React.FC<SecondaryButtonProps> = ({
  children,
  onClick,
  disabled = false,
  className,
  type = 'button',
}) => {
  return (
    <Button
      variant='outline'
      onClick={onClick}
      disabled={disabled}
      className={cn(
        'bg-gray-100 hover:bg-gray-200 text-gray-700 border-gray-300',
        'focus:ring-2 focus:ring-gray-500 focus:ring-offset-2',
        'transition-colors duration-200',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        className
      )}
      type={type}
    >
      {children}
    </Button>
  );
};

// Danger Button - Red theme
interface DangerButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  loading?: boolean;
  className?: string;
  type?: 'button' | 'submit' | 'reset';
}

export const DangerButton: React.FC<DangerButtonProps> = ({
  children,
  onClick,
  disabled = false,
  loading = false,
  className,
  type = 'button',
}) => {
  return (
    <Button
      variant='destructive'
      onClick={onClick}
      disabled={disabled || loading}
      className={cn(
        'bg-red-600 hover:bg-red-700 text-white font-medium',
        'focus:ring-2 focus:ring-red-500 focus:ring-offset-2',
        'transition-colors duration-200',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        className
      )}
      type={type}
    >
      {loading && (
        <svg className='animate-spin -ml-1 mr-2 h-4 w-4 text-white' fill='none' viewBox='0 0 24 24'>
          <circle
            className='opacity-25'
            cx='12'
            cy='12'
            r='10'
            stroke='currentColor'
            strokeWidth='4'
          />
          <path
            className='opacity-75'
            fill='currentColor'
            d='M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z'
          />
        </svg>
      )}
      {children}
    </Button>
  );
};

// Success Button - Green theme
interface SuccessButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
  type?: 'button' | 'submit' | 'reset';
}

export const SuccessButton: React.FC<SuccessButtonProps> = ({
  children,
  onClick,
  disabled = false,
  className,
  type = 'button',
}) => {
  return (
    <Button
      variant='outline'
      onClick={onClick}
      disabled={disabled}
      className={cn(
        'bg-green-100 hover:bg-green-200 text-green-700 border-green-300',
        'focus:ring-2 focus:ring-green-500 focus:ring-offset-2',
        'transition-colors duration-200',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        className
      )}
      type={type}
    >
      {children}
    </Button>
  );
};

// Icon Button - For actions with icons
interface IconButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  type?: 'button' | 'submit' | 'reset';
}

export const IconButton: React.FC<IconButtonProps> = ({
  children,
  onClick,
  disabled = false,
  variant = 'ghost',
  size = 'md',
  className,
  type = 'button',
}) => {
  const sizeClasses = {
    sm: 'h-8 w-8 p-1',
    md: 'h-10 w-10 p-2',
    lg: 'h-12 w-12 p-3',
  };

  const variantClasses = {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white',
    secondary: 'bg-gray-100 hover:bg-gray-200 text-gray-700',
    danger: 'bg-red-600 hover:bg-red-700 text-white',
    ghost: 'hover:bg-gray-100 text-gray-600',
  };

  return (
    <Button
      variant='ghost'
      onClick={onClick}
      disabled={disabled}
      className={cn(
        'rounded-full flex items-center justify-center',
        'focus:ring-2 focus:ring-offset-2',
        'transition-colors duration-200',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        sizeClasses[size],
        variantClasses[variant],
        className
      )}
      type={type}
    >
      {children}
    </Button>
  );
};
