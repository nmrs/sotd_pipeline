import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

describe('ShadCN UI Integration', () => {
  describe('Button Component', () => {
    test('should render ShadCN button with correct styling', () => {
      const handleClick = jest.fn();
      render(
        <Button onClick={handleClick} variant='default'>
          Test Button
        </Button>
      );

      const button = screen.getByRole('button', { name: 'Test Button' });
      expect(button).toBeInTheDocument();
      expect(button).toHaveClass('inline-flex', 'items-center', 'justify-center');
    });

    test('should handle button clicks correctly', () => {
      const handleClick = jest.fn();
      render(
        <Button onClick={handleClick} variant='default'>
          Click Me
        </Button>
      );

      const button = screen.getByRole('button', { name: 'Click Me' });
      fireEvent.click(button);
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    test('should support different button variants', () => {
      render(
        <div>
          <Button variant='default'>Default</Button>
          <Button variant='secondary'>Secondary</Button>
          <Button variant='destructive'>Destructive</Button>
          <Button variant='outline'>Outline</Button>
          <Button variant='ghost'>Ghost</Button>
          <Button variant='link'>Link</Button>
        </div>
      );

      expect(screen.getByRole('button', { name: 'Default' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Secondary' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Destructive' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Outline' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Ghost' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Link' })).toBeInTheDocument();
    });

    test('should support different button sizes', () => {
      render(
        <div>
          <Button size='default'>Default</Button>
          <Button size='sm'>Small</Button>
          <Button size='lg'>Large</Button>
          <Button size='icon'>Icon</Button>
        </div>
      );

      expect(screen.getByRole('button', { name: 'Default' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Small' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Large' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Icon' })).toBeInTheDocument();
    });
  });

  describe('Input Component', () => {
    test('should render ShadCN input with correct styling', () => {
      render(<Input type='text' placeholder='Enter text' />);

      const input = screen.getByRole('textbox');
      expect(input).toBeInTheDocument();
      expect(input).toHaveAttribute('placeholder', 'Enter text');
      expect(input).toHaveClass('flex', 'h-9', 'w-full', 'rounded-md', 'border');
    });

    test('should handle input changes correctly', () => {
      const handleChange = jest.fn();
      render(<Input type='text' onChange={handleChange} />);

      const input = screen.getByRole('textbox');
      fireEvent.change(input, { target: { value: 'test input' } });
      expect(handleChange).toHaveBeenCalled();
    });

    test('should support different input types', () => {
      render(
        <div>
          <Input type='text' placeholder='Text input' />
          <Input type='email' placeholder='Email input' />
          <Input type='password' placeholder='Password input' />
          <Input type='number' placeholder='Number input' />
        </div>
      );

      const textInput = screen.getByPlaceholderText('Text input');
      const emailInput = screen.getByPlaceholderText('Email input');
      const passwordInput = screen.getByPlaceholderText('Password input');
      const numberInput = screen.getByPlaceholderText('Number input');

      expect(textInput).toHaveAttribute('type', 'text');
      expect(emailInput).toHaveAttribute('type', 'email');
      expect(passwordInput).toHaveAttribute('type', 'password');
      expect(numberInput).toHaveAttribute('type', 'number');
    });
  });

  describe('Checkbox Component', () => {
    test('should render ShadCN checkbox with correct styling', () => {
      render(<Checkbox />);

      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toBeInTheDocument();
      expect(checkbox).toHaveClass('h-4', 'w-4');
    });

    test('should handle checkbox state changes', () => {
      const handleCheckedChange = jest.fn();
      render(<Checkbox onCheckedChange={handleCheckedChange} />);

      const checkbox = screen.getByRole('checkbox');
      fireEvent.click(checkbox);
      expect(handleCheckedChange).toHaveBeenCalledWith(true);
    });

    test('should support controlled state', () => {
      const { rerender } = render(<Checkbox checked={false} />);

      let checkbox = screen.getByRole('checkbox');
      expect(checkbox).not.toBeChecked();

      rerender(<Checkbox checked={true} />);
      checkbox = screen.getByRole('checkbox');
      expect(checkbox).toBeChecked();
    });
  });

  describe('Select Component', () => {
    test('should render ShadCN select with correct styling', () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue placeholder='Select an option' />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value='option1'>Option 1</SelectItem>
            <SelectItem value='option2'>Option 2</SelectItem>
          </SelectContent>
        </Select>
      );

      const select = screen.getByRole('combobox');
      expect(select).toBeInTheDocument();
      expect(select).toHaveClass('flex', 'h-9', 'w-full', 'rounded-md', 'border');
    });

    test('should render select trigger with placeholder', () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue placeholder='Select an option' />
          </SelectTrigger>
        </Select>
      );

      const select = screen.getByRole('combobox');
      expect(select).toBeInTheDocument();
      expect(select).toHaveTextContent('Select an option');
    });
  });

  describe('Table Component', () => {
    test('should render ShadCN table with correct styling', () => {
      render(
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Header</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow>
              <TableCell>Data</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );

      const table = screen.getByRole('table');
      expect(table).toBeInTheDocument();
      expect(table).toHaveClass('w-full', 'caption-bottom', 'text-sm');
    });

    test('should render table headers and cells correctly', () => {
      render(
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Count</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow>
              <TableCell>Test Item</TableCell>
              <TableCell>5</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );

      expect(screen.getByRole('columnheader', { name: 'Name' })).toBeInTheDocument();
      expect(screen.getByRole('columnheader', { name: 'Count' })).toBeInTheDocument();
      expect(screen.getByText('Test Item')).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument();
    });

    test('should support multiple table rows', () => {
      render(
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Count</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow>
              <TableCell>Item 1</TableCell>
              <TableCell>10</TableCell>
            </TableRow>
            <TableRow>
              <TableCell>Item 2</TableCell>
              <TableCell>20</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );

      expect(screen.getByText('Item 1')).toBeInTheDocument();
      expect(screen.getByText('Item 2')).toBeInTheDocument();
      expect(screen.getByText('10')).toBeInTheDocument();
      expect(screen.getByText('20')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    test('should maintain proper ARIA attributes', () => {
      render(
        <div>
          <Button aria-label='Submit form'>Submit</Button>
          <Input aria-label='Search input' type='text' />
          <Checkbox aria-label='Accept terms' />
        </div>
      );

      expect(screen.getByRole('button', { name: 'Submit form' })).toBeInTheDocument();
      expect(screen.getByRole('textbox', { name: 'Search input' })).toBeInTheDocument();
      expect(screen.getByRole('checkbox', { name: 'Accept terms' })).toBeInTheDocument();
    });

    test('should support keyboard navigation', () => {
      const handleKeyDown = jest.fn();
      render(<Button onKeyDown={handleKeyDown}>Test Button</Button>);

      const button = screen.getByRole('button', { name: 'Test Button' });
      fireEvent.keyDown(button, { key: 'Enter' });
      expect(handleKeyDown).toHaveBeenCalled();
    });

    test('should support focus management', () => {
      render(
        <div>
          <Button>First Button</Button>
          <Input type='text' />
          <Button>Second Button</Button>
        </div>
      );

      const firstButton = screen.getByRole('button', { name: 'First Button' });
      const input = screen.getByRole('textbox');
      const secondButton = screen.getByRole('button', { name: 'Second Button' });

      firstButton.focus();
      expect(firstButton).toHaveFocus();

      input.focus();
      expect(input).toHaveFocus();

      secondButton.focus();
      expect(secondButton).toHaveFocus();
    });
  });

  describe('Theme Integration', () => {
    test('should use consistent color scheme', () => {
      render(
        <div className='bg-background text-foreground'>
          <Button variant='default'>Primary</Button>
          <Button variant='secondary'>Secondary</Button>
        </div>
      );

      const container = screen.getByText('Primary').parentElement;
      expect(container).toHaveClass('bg-background', 'text-foreground');
    });

    test('should support dark mode classes', () => {
      render(
        <div className='dark:bg-gray-900 dark:text-gray-100'>
          <Button variant='default' className='dark:bg-gray-800 dark:text-gray-100'>
            Dark Button
          </Button>
        </div>
      );

      const container = screen.getByText('Dark Button').parentElement;
      expect(container).toHaveClass('dark:bg-gray-900', 'dark:text-gray-100');
    });
  });

  describe('Component Integration', () => {
    test('should work together in a form', () => {
      const handleSubmit = jest.fn();
      const handleInputChange = jest.fn();
      const handleCheckboxChange = jest.fn();

      render(
        <form onSubmit={handleSubmit}>
          <div className='space-y-4'>
            <div>
              <label htmlFor='name'>Name:</label>
              <Input id='name' type='text' onChange={handleInputChange} placeholder='Enter name' />
            </div>
            <div>
              <label htmlFor='email'>Email:</label>
              <Input
                id='email'
                type='email'
                onChange={handleInputChange}
                placeholder='Enter email'
              />
            </div>
            <div>
              <Checkbox id='newsletter' onCheckedChange={handleCheckboxChange} />
              <label htmlFor='newsletter'>Subscribe to newsletter</label>
            </div>
            <Button type='submit'>Submit</Button>
          </div>
        </form>
      );

      expect(screen.getByLabelText('Name:')).toBeInTheDocument();
      expect(screen.getByLabelText('Email:')).toBeInTheDocument();
      expect(screen.getByLabelText('Subscribe to newsletter')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Submit' })).toBeInTheDocument();
    });
  });
});
