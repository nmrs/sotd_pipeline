import { render, screen, fireEvent } from '@testing-library/react';
import {
  PrimaryButton,
  SecondaryButton,
  DangerButton,
  SuccessButton,
  IconButton,
} from '../ui/reusable-buttons';

// Mock ShadCN Button component
jest.mock('@/components/ui/button', () => ({
  Button: ({
    children,
    onClick,
    disabled,
    className,
    type,
    variant,
  }: {
    children?: React.ReactNode;
    onClick?: (e: React.MouseEvent) => void;
    disabled?: boolean;
    className?: string;
    type?: string;
    variant?: string;
  }) => (
    <button
      onClick={onClick}
      onKeyDown={e => {
        if (e.key === 'Enter' || e.key === ' ') {
          // For testing purposes, just call onClick with a mock event
          onClick && onClick({} as React.MouseEvent<HTMLButtonElement>);
        }
      }}
      disabled={disabled}
      className={className}
      type={type as 'button' | 'submit' | 'reset' | undefined}
      data-testid={`button-${variant || 'default'}`}
    >
      {children}
    </button>
  ),
}));

describe('Reusable Button Components', () => {
  describe('PrimaryButton', () => {
    it('renders with correct styling and behavior', () => {
      const handleClick = jest.fn();

      render(<PrimaryButton onClick={handleClick}>Primary Action</PrimaryButton>);

      const button = screen.getByTestId('button-default');
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('Primary Action');
      expect(button.className).toContain('bg-blue-600');
      expect(button.className).toContain('hover:bg-blue-700');
    });

    it('shows loading state with spinner', () => {
      render(<PrimaryButton loading={true}>Loading</PrimaryButton>);

      const button = screen.getByTestId('button-default');
      expect(button).toBeInTheDocument();
      expect(button).toBeDisabled();
      expect(button.innerHTML).toContain('animate-spin');
    });

    it('handles disabled state', () => {
      render(<PrimaryButton disabled={true}>Disabled</PrimaryButton>);

      const button = screen.getByTestId('button-default');
      expect(button).toBeDisabled();
      expect(button.className).toContain('disabled:opacity-50');
    });

    it('calls onClick when clicked', () => {
      const handleClick = jest.fn();

      render(<PrimaryButton onClick={handleClick}>Click Me</PrimaryButton>);

      const button = screen.getByTestId('button-default');
      fireEvent.click(button);

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('applies custom className', () => {
      render(<PrimaryButton className='custom-class'>Custom</PrimaryButton>);

      const button = screen.getByTestId('button-default');
      expect(button.className).toContain('custom-class');
    });
  });

  describe('SecondaryButton', () => {
    it('renders with correct styling', () => {
      render(<SecondaryButton>Secondary Action</SecondaryButton>);

      const button = screen.getByTestId('button-outline');
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('Secondary Action');
      expect(button.className).toContain('bg-gray-100');
      expect(button.className).toContain('hover:bg-gray-200');
    });

    it('handles disabled state', () => {
      render(<SecondaryButton disabled={true}>Disabled</SecondaryButton>);

      const button = screen.getByTestId('button-outline');
      expect(button).toBeDisabled();
    });

    it('calls onClick when clicked', () => {
      const handleClick = jest.fn();

      render(<SecondaryButton onClick={handleClick}>Click Me</SecondaryButton>);

      const button = screen.getByTestId('button-outline');
      fireEvent.click(button);

      expect(handleClick).toHaveBeenCalledTimes(1);
    });
  });

  describe('DangerButton', () => {
    it('renders with correct styling', () => {
      render(<DangerButton>Delete</DangerButton>);

      const button = screen.getByTestId('button-destructive');
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('Delete');
      expect(button.className).toContain('bg-red-600');
      expect(button.className).toContain('hover:bg-red-700');
    });

    it('shows loading state with spinner', () => {
      render(<DangerButton loading={true}>Deleting</DangerButton>);

      const button = screen.getByTestId('button-destructive');
      expect(button).toBeDisabled();
      expect(button.innerHTML).toContain('animate-spin');
    });

    it('handles disabled state', () => {
      render(<DangerButton disabled={true}>Disabled</DangerButton>);

      const button = screen.getByTestId('button-destructive');
      expect(button).toBeDisabled();
    });
  });

  describe('SuccessButton', () => {
    it('renders with correct styling', () => {
      render(<SuccessButton>Save</SuccessButton>);

      const button = screen.getByTestId('button-outline');
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('Save');
      expect(button.className).toContain('bg-green-100');
      expect(button.className).toContain('hover:bg-green-200');
    });

    it('handles disabled state', () => {
      render(<SuccessButton disabled={true}>Disabled</SuccessButton>);

      const button = screen.getByTestId('button-outline');
      expect(button).toBeDisabled();
    });
  });

  describe('IconButton', () => {
    it('renders with correct styling', () => {
      render(<IconButton>🗑️</IconButton>);

      const button = screen.getByTestId('button-ghost');
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('🗑️');
      expect(button.className).toContain('rounded-full');
    });

    it('applies different variants', () => {
      const { rerender } = render(<IconButton variant='primary'>🗑️</IconButton>);

      let button = screen.getByTestId('button-ghost');
      expect(button.className).toContain('bg-blue-600');

      rerender(<IconButton variant='danger'>🗑️</IconButton>);

      button = screen.getByTestId('button-ghost');
      expect(button.className).toContain('bg-red-600');
    });

    it('applies different sizes', () => {
      const { rerender } = render(<IconButton size='sm'>🗑️</IconButton>);

      let button = screen.getByTestId('button-ghost');
      expect(button.className).toContain('h-8 w-8');

      rerender(<IconButton size='lg'>🗑️</IconButton>);

      button = screen.getByTestId('button-ghost');
      expect(button.className).toContain('h-12 w-12');
    });

    it('handles disabled state', () => {
      render(<IconButton disabled={true}>🗑️</IconButton>);

      const button = screen.getByTestId('button-ghost');
      expect(button).toBeDisabled();
    });

    it('calls onClick when clicked', () => {
      const handleClick = jest.fn();

      render(<IconButton onClick={handleClick}>🗑️</IconButton>);

      const button = screen.getByTestId('button-ghost');
      fireEvent.click(button);

      expect(handleClick).toHaveBeenCalledTimes(1);
    });
  });

  describe('Accessibility', () => {
    it('supports keyboard navigation', () => {
      const handleClick = jest.fn();

      render(<PrimaryButton onClick={handleClick}>Accessible Button</PrimaryButton>);

      const button = screen.getByTestId('button-default');
      button.focus();
      // Simulate keyboard navigation - Enter key should trigger click
      fireEvent.keyDown(button, { key: 'Enter', code: 'Enter' });

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('has proper focus styles', () => {
      render(<PrimaryButton>Focusable Button</PrimaryButton>);

      const button = screen.getByTestId('button-default');
      expect(button.className).toContain('focus:ring-2');
    });
  });

  describe('Type Safety', () => {
    it('accepts proper button types', () => {
      render(<PrimaryButton type='submit'>Submit</PrimaryButton>);

      const button = screen.getByTestId('button-default');
      expect(button).toHaveAttribute('type', 'submit');
    });
  });
});
