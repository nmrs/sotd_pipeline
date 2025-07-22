'use client';

import React from 'react';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { cn } from '@/lib/utils';

// Form Field Wrapper - Provides consistent layout and error handling
interface FormFieldProps {
  children: React.ReactNode;
  label?: string;
  error?: string;
  required?: boolean;
  className?: string;
}

export const FormField: React.FC<FormFieldProps> = ({
  children,
  label,
  error,
  required = false,
  className,
}) => {
  return (
    <div className={cn('space-y-2', className)}>
      {label && (
        <label className='block text-sm font-medium text-gray-700'>
          {label}
          {required && <span className='text-red-500 ml-1'>*</span>}
        </label>
      )}
      {children}
      {error && <p className='text-sm text-red-600'>{error}</p>}
    </div>
  );
};

// Text Input with validation
interface TextInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  label?: string;
  error?: string;
  required?: boolean;
  disabled?: boolean;
  className?: string;
  type?: 'text' | 'email' | 'password' | 'number';
}

export const TextInput: React.FC<TextInputProps> = ({
  value,
  onChange,
  placeholder,
  label,
  error,
  required = false,
  disabled = false,
  className,
  type = 'text',
}) => {
  return (
    <FormField label={label} error={error} required={required}>
      <Input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        className={cn(
          'w-full',
          error && 'border-red-300 focus:border-red-500 focus:ring-red-500',
          className
        )}
      />
    </FormField>
  );
};

// Select Input with options
interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

interface SelectInputProps {
  value: string;
  onChange: (value: string) => void;
  options: SelectOption[];
  placeholder?: string;
  label?: string;
  error?: string;
  required?: boolean;
  disabled?: boolean;
  className?: string;
}

export const SelectInput: React.FC<SelectInputProps> = ({
  value,
  onChange,
  options,
  placeholder,
  label,
  error,
  required = false,
  disabled = false,
  className,
}) => {
  return (
    <FormField label={label} error={error} required={required}>
      <Select value={value} onValueChange={onChange} disabled={disabled}>
        <SelectTrigger
          className={cn(
            'w-full',
            error && 'border-red-300 focus:border-red-500 focus:ring-red-500',
            className
          )}
        >
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent>
          {options.map(option => (
            <SelectItem key={option.value} value={option.value} disabled={option.disabled}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </FormField>
  );
};

// Checkbox Input
interface CheckboxInputProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  error?: string;
  disabled?: boolean;
  className?: string;
}

export const CheckboxInput: React.FC<CheckboxInputProps> = ({
  checked,
  onChange,
  label,
  error,
  disabled = false,
  className,
}) => {
  return (
    <FormField error={error}>
      <div className={cn('flex items-center space-x-2', className)}>
        <Checkbox
          checked={checked}
          onCheckedChange={onChange}
          disabled={disabled}
          className={cn(
            error && 'border-red-300',
            'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
          )}
        />
        {label && <label className='text-sm text-gray-700'>{label}</label>}
      </div>
    </FormField>
  );
};

// Form Container - Provides consistent form layout
interface FormContainerProps {
  children: React.ReactNode;
  onSubmit?: (e: React.FormEvent) => void;
  className?: string;
}

export const FormContainer: React.FC<FormContainerProps> = ({ children, onSubmit, className }) => {
  return (
    <form onSubmit={onSubmit} className={cn('space-y-6', className)}>
      {children}
    </form>
  );
};

// Form Actions - Container for form buttons
interface FormActionsProps {
  children: React.ReactNode;
  className?: string;
}

export const FormActions: React.FC<FormActionsProps> = ({ children, className }) => {
  return (
    <div className={cn('flex items-center justify-end space-x-3 pt-4', className)}>{children}</div>
  );
};

// Search Input - Specialized input for search functionality
interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  onClear?: () => void;
  className?: string;
}

export const SearchInput: React.FC<SearchInputProps> = ({
  value,
  onChange,
  placeholder = 'Search...',
  onClear,
  className,
}) => {
  return (
    <div className={cn('relative', className)}>
      <Input
        type='text'
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className='w-full pl-10 pr-10'
      />
      <div className='absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none'>
        <svg
          className='h-5 w-5 text-gray-400'
          fill='none'
          viewBox='0 0 24 24'
          stroke='currentColor'
        >
          <path
            strokeLinecap='round'
            strokeLinejoin='round'
            strokeWidth={2}
            d='M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z'
          />
        </svg>
      </div>
      {value && onClear && (
        <button
          type='button'
          onClick={onClear}
          className='absolute inset-y-0 right-0 pr-3 flex items-center'
        >
          <svg
            className='h-5 w-5 text-gray-400 hover:text-gray-600'
            fill='none'
            viewBox='0 0 24 24'
            stroke='currentColor'
          >
            <path
              strokeLinecap='round'
              strokeLinejoin='round'
              strokeWidth={2}
              d='M6 18L18 6M6 6l12 12'
            />
          </svg>
        </button>
      )}
    </div>
  );
};
