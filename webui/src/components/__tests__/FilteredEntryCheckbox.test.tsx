// import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import FilteredEntryCheckbox from '../forms/FilteredEntryCheckbox';

describe('FilteredEntryCheckbox', () => {
  const mockOnStatusChange = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('should render checkbox with correct initial state', () => {
    render(
      <FilteredEntryCheckbox
        itemName='test-item'
        commentIds={['comment1', 'comment2']}
        isFiltered={false}
        onStatusChange={mockOnStatusChange}
      />
    );

    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).toBeInTheDocument();
    expect(checkbox).not.toBeChecked();
  });

  test('should render checked checkbox when isFiltered is true', () => {
    render(
      <FilteredEntryCheckbox
        itemName='test-item'
        commentIds={['comment1', 'comment2']}
        isFiltered={true}
        onStatusChange={mockOnStatusChange}
      />
    );

    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).toBeChecked();
  });

  test('should call onStatusChange when checkbox is clicked', () => {
    render(
      <FilteredEntryCheckbox
        itemName='test-item'
        commentIds={['comment1', 'comment2']}
        isFiltered={false}
        onStatusChange={mockOnStatusChange}
      />
    );

    const checkbox = screen.getByRole('checkbox');
    fireEvent.click(checkbox);

    expect(mockOnStatusChange).toHaveBeenCalledWith(true);
  });

  test('should call onStatusChange with false when checked checkbox is clicked', () => {
    render(
      <FilteredEntryCheckbox
        itemName='test-item'
        commentIds={['comment1', 'comment2']}
        isFiltered={true}
        onStatusChange={mockOnStatusChange}
      />
    );

    const checkbox = screen.getByRole('checkbox');
    fireEvent.click(checkbox);

    expect(mockOnStatusChange).toHaveBeenCalledWith(false);
  });

  test('should be disabled when disabled prop is true', () => {
    render(
      <FilteredEntryCheckbox
        itemName='test-item'
        commentIds={['comment1', 'comment2']}
        isFiltered={false}
        onStatusChange={mockOnStatusChange}
        disabled={true}
      />
    );

    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).toBeDisabled();
  });

  test('should be disabled when commentIds is empty', () => {
    render(
      <FilteredEntryCheckbox
        itemName='test-item'
        commentIds={[]}
        isFiltered={false}
        onStatusChange={mockOnStatusChange}
      />
    );

    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).toBeDisabled();
  });

  test('should not call onStatusChange when disabled', () => {
    render(
      <FilteredEntryCheckbox
        itemName='test-item'
        commentIds={['comment1', 'comment2']}
        isFiltered={false}
        onStatusChange={mockOnStatusChange}
        disabled={true}
      />
    );

    const checkbox = screen.getByRole('checkbox');
    fireEvent.click(checkbox);

    expect(mockOnStatusChange).not.toHaveBeenCalled();
  });
});
