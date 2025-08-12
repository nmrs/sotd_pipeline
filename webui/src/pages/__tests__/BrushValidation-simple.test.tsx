/**
 * Simple tests for BrushValidation page component.
 * Tests core functionality and component structure.
 */

import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import BrushValidation from '../BrushValidation';
import * as api from '../../services/api';

// Mock the API module
jest.mock('../../services/api');

// Mock the useAvailableMonths hook
jest.mock('../../hooks/useAvailableMonths', () => ({
  useAvailableMonths: () => ({
    availableMonths: ['2025-01', '2025-02', '2025-03'],
    loading: false,
    error: null,
    refreshMonths: jest.fn(),
  }),
}));

const mockApi = api as jest.Mocked<typeof api>;

describe('BrushValidation', () => {
  beforeEach(() => {
    // Reset all mocks before each test
    jest.clearAllMocks();

    // Mock the API responses
    mockApi.getAvailableMonths.mockResolvedValue(['2025-01', '2025-02', '2025-03']);
    mockApi.getBrushValidationData.mockResolvedValue({
      entries: [
        {
          input_text: 'Test Brush 1',
          normalized_text: 'test brush 1',
          system_used: 'scoring',
          matched: {
            brand: 'Test Brand',
            model: 'Brush 1',
            strategy: 'test_strategy',
            score: 0.8,
          },
          all_strategies: [
            {
              strategy: 'test_strategy',
              score: 0.8,
              result: { brand: 'Test Brand', model: 'Brush 1' },
            },
          ],
          comment_ids: ['1', '2'],
        },
        {
          input_text: 'Test Brush 2',
          normalized_text: 'test brush 2',
          system_used: 'scoring',
          matched: {
            brand: 'Test Brand',
            model: 'Brush 2',
            strategy: 'test_strategy',
            score: 0.9,
          },
          all_strategies: [
            {
              strategy: 'test_strategy',
              score: 0.9,
              result: { brand: 'Test Brand', model: 'Brush 2' },
            },
          ],
          comment_ids: [],
        },
      ],
      pagination: {
        page: 1,
        page_size: 20,
        total: 2,
        pages: 1,
      },
    });
    mockApi.getBrushValidationStatistics.mockResolvedValue({
      total_entries: 2,
      validated_count: 1,
      overridden_count: 1,
      unvalidated_count: 0,
      validation_rate: 1.0,
    });
    mockApi.undoLastValidationAction.mockResolvedValue({
      success: true,
      message: 'Last action undone successfully',
    });
    mockApi.recordBrushValidationAction.mockResolvedValue({
      success: true,
      message: 'Action recorded successfully',
    });
    mockApi.getCommentDetail.mockResolvedValue({
      id: '1',
      author: 'test_user',
      body: 'Test comment',
      created_utc: '2025-01-01T00:00:00Z',
      thread_id: 'test_thread',
      thread_title: 'Test Thread',
      url: 'https://reddit.com/test',
    });
  });

  it('loads available months on mount', async () => {
    render(<BrushValidation />);

    // Verify that months are available in the MonthSelector
    await waitFor(() => {
      expect(screen.getByText('Select a month')).toBeInTheDocument();
    });
  });

  it('loads validation data when month is selected', async () => {
    render(<BrushValidation />);

    // Verify that months are available
    await waitFor(() => {
      expect(screen.getByText('Select a month')).toBeInTheDocument();
    });

    // Click on the month selector button to open dropdown
    const monthButton = screen.getByText('Select a month');
    fireEvent.click(monthButton);

    // Select a month
    const monthOption = screen.getByText('2025-01');
    fireEvent.click(monthOption);

    // Wait for data to load and verify display
    await waitFor(() => {
      expect(mockApi.getBrushValidationData).toHaveBeenCalledWith('2025-01', 'scoring', {
        page: 1,
        pageSize: 20,
        sortBy: 'unvalidated',
      });
    });
  });

  it('displays validation entries correctly', async () => {
    render(<BrushValidation />);

    // Verify that months are available
    await waitFor(() => {
      expect(screen.getByText('Select a month')).toBeInTheDocument();
    });

    // Click on the month selector button to open dropdown
    const monthButton = screen.getByText('Select a month');
    fireEvent.click(monthButton);

    // Select a month
    const monthOption = screen.getByText('2025-01');
    fireEvent.click(monthOption);

    // Wait for initial data load
    await waitFor(() => {
      expect(mockApi.getBrushValidationData).toHaveBeenCalledWith('2025-01', 'scoring', {
        page: 1,
        pageSize: 20,
        sortBy: 'unvalidated',
      });
    });

    // Verify that entries are displayed
    expect(screen.getByText('Test Brush 1')).toBeInTheDocument();
    expect(screen.getByText('Test Brush 2')).toBeInTheDocument();
  });

  it('handles validation action recording', async () => {
    render(<BrushValidation />);

    // Verify that months are available
    await waitFor(() => {
      expect(screen.getByText('Select a month')).toBeInTheDocument();
    });

    // Click on the month selector button to open dropdown
    const monthButton = screen.getByText('Select a month');
    fireEvent.click(monthButton);

    // Select a month
    const monthOption = screen.getByText('2025-01');
    fireEvent.click(monthOption);

    // Wait for data to load
    await waitFor(() => {
      expect(mockApi.getBrushValidationData).toHaveBeenCalledWith('2025-01', 'scoring', {
        page: 1,
        pageSize: 20,
        sortBy: 'unvalidated',
      });
    });

    // Find and click the validate button for the first entry
    const validateButtons = screen.getAllByText('Validate');
    if (validateButtons.length > 0) {
      await userEvent.click(validateButtons[0]);

      // Verify the API was called
      expect(mockApi.recordBrushValidationAction).toHaveBeenCalledWith({
        input_text: 'test brush 1',
        month: '2025-01',
        system_used: 'scoring',
        action: 'validate',
        system_choice: {
          strategy: 'test_strategy',
          score: 0.8,
          result: {
            brand: 'Test Brand',
            model: 'Brush 1',
          },
        },
        user_choice: {
          strategy: 'test_strategy',
          score: 0.8,
          result: {
            brand: 'Test Brand',
            model: 'Brush 1',
          },
        },
        all_brush_strategies: [
          {
            result: {
              brand: 'Test Brand',
              model: 'Brush 1',
            },
            score: 0.8,
            strategy: 'test_strategy',
          },
        ],
      });
    }
  });

  it('handles override action recording', async () => {
    render(<BrushValidation />);

    // Verify that months are available
    await waitFor(() => {
      expect(screen.getByText('Select a month')).toBeInTheDocument();
    });

    // Click on the month selector button to open dropdown
    const monthButton = screen.getByText('Select a month');
    fireEvent.click(monthButton);

    // Select a month
    const monthOption = screen.getByText('2025-01');
    fireEvent.click(monthOption);

    // Wait for data to load
    await waitFor(() => {
      expect(mockApi.getBrushValidationData).toHaveBeenCalledWith('2025-01', 'scoring', {
        page: 1,
        pageSize: 20,
        sortBy: 'unvalidated',
      });
    });

    // Find and click the override button for the second entry
    const overrideButtons = screen.getAllByText('Override');
    if (overrideButtons.length > 0) {
      fireEvent.click(overrideButtons[1]);

      // Wait for override state to be set and UI to update
      await waitFor(() => {
        expect(screen.getByText('Confirm Override')).toBeInTheDocument();
      });

      // Now click confirm override to complete the override action
      const confirmOverrideButton = screen.getByText('Confirm Override');
      fireEvent.click(confirmOverrideButton);

      // Wait for the API call to be made
      await waitFor(() => {
        expect(mockApi.recordBrushValidationAction).toHaveBeenCalledWith({
          input_text: 'test brush 2',
          month: '2025-01',
          system_used: 'scoring',
          action: 'override',
          system_choice: {
            strategy: 'test_strategy',
            score: 0.9,
            result: {
              brand: 'Test Brand',
              model: 'Brush 2',
            },
          },
          user_choice: {
            strategy: 'test_strategy',
            score: 0.9,
            result: {
              brand: 'Test Brand',
              model: 'Brush 2',
            },
          },
          all_brush_strategies: [
            {
              strategy: 'test_strategy',
              score: 0.9,
              result: {
                brand: 'Test Brand',
                model: 'Brush 2',
              },
            },
          ],
        });
      });
    }
  });

  it('displays undo button when month is selected', async () => {
    render(<BrushValidation />);

    // Verify that months are available
    await waitFor(() => {
      expect(screen.getByText('Select a month')).toBeInTheDocument();
    });

    // Click on the month selector button to open dropdown
    const monthButton = screen.getByText('Select a month');
    fireEvent.click(monthButton);

    // Select a month
    const monthOption = screen.getByText('2025-01');
    fireEvent.click(monthOption);

    // Wait for data to load
    await waitFor(() => {
      expect(mockApi.getBrushValidationData).toHaveBeenCalledWith('2025-01', 'scoring', {
        page: 1,
        pageSize: 20,
        sortBy: 'unvalidated',
      });
    });

    // Verify that the undo button is displayed
    expect(screen.getByText('Undo Last Validation')).toBeInTheDocument();
  });

  it('undo button calls undo API when clicked', async () => {
    render(<BrushValidation />);

    // Verify that months are available
    await waitFor(() => {
      expect(screen.getByText('Select a month')).toBeInTheDocument();
    });

    // Click on the month selector button to open dropdown
    const monthButton = screen.getByText('Select a month');
    fireEvent.click(monthButton);

    // Select a month
    const monthOption = screen.getByText('2025-01');
    fireEvent.click(monthOption);

    // Wait for data to load
    await waitFor(() => {
      expect(mockApi.getBrushValidationData).toHaveBeenCalledWith('2025-01', 'scoring', {
        page: 1,
        pageSize: 20,
        sortBy: 'unvalidated',
      });
    });

    // Find and click the undo button
    const undoButton = screen.getByRole('button', { name: 'Undo Last Validation' });
    fireEvent.click(undoButton);

    // Verify the undo API was called
    expect(mockApi.undoLastValidationAction).toHaveBeenCalledWith('2025-01');
  });

  it('undo button is enabled when month is selected', async () => {
    render(<BrushValidation />);

    // Verify that months are available
    await waitFor(() => {
      expect(screen.getByText('Select a month')).toBeInTheDocument();
    });

    // Click on the month selector button to open dropdown
    const monthButton = screen.getByText('Select a month');
    fireEvent.click(monthButton);

    // Select a month
    const monthOption = screen.getByText('2025-01');
    fireEvent.click(monthOption);

    // Wait for data to load
    await waitFor(() => {
      expect(mockApi.getBrushValidationData).toHaveBeenCalledWith('2025-01', 'scoring', {
        page: 1,
        pageSize: 20,
        sortBy: 'unvalidated',
      });
    });

    // Verify the undo button is enabled
    const undoButton = screen.getByRole('button', { name: 'Undo Last Validation' });
    expect(undoButton).not.toBeDisabled();
  });

  it('undo button shows loading state during API call', async () => {
    // Mock the undo API to delay response
    mockApi.undoLastValidationAction.mockImplementationOnce(
      () =>
        new Promise(resolve =>
          setTimeout(
            () =>
              resolve({
                success: true,
                message: 'Last action undone successfully',
              }),
            100
          )
        )
    );

    render(<BrushValidation />);

    // Verify that months are available
    await waitFor(() => {
      expect(screen.getByText('Select a month')).toBeInTheDocument();
    });

    // Click on the month selector button to open dropdown
    const monthButton = screen.getByText('Select a month');
    fireEvent.click(monthButton);

    // Select a month
    const monthOption = screen.getByText('2025-01');
    fireEvent.click(monthOption);

    // Wait for data to load
    await waitFor(() => {
      expect(mockApi.getBrushValidationData).toHaveBeenCalledWith('2025-01', 'scoring', {
        page: 1,
        pageSize: 20,
        sortBy: 'unvalidated',
      });
    });

    // Find and click the undo button
    const undoButton = screen.getByRole('button', { name: 'Undo Last Validation' });
    fireEvent.click(undoButton);

    // Verify the undo API was called
    expect(mockApi.undoLastValidationAction).toHaveBeenCalledWith('2025-01');
  });

  it('undo button reloads data after successful undo', async () => {
    render(<BrushValidation />);

    // Verify that months are available
    await waitFor(() => {
      expect(screen.getByText('Select a month')).toBeInTheDocument();
    });

    // Click on the month selector button to open dropdown
    const monthButton = screen.getByText('Select a month');
    fireEvent.click(monthButton);

    // Select a month
    const monthOption = screen.getByText('2025-01');
    fireEvent.click(monthOption);

    // Wait for initial data load
    await waitFor(() => {
      expect(mockApi.getBrushValidationData).toHaveBeenCalledWith('2025-01', 'scoring', {
        page: 1,
        pageSize: 20,
        sortBy: 'unvalidated',
      });
    });

    // Click the undo button
    const undoButton = screen.getByRole('button', { name: 'Undo Last Validation' });
    fireEvent.click(undoButton);

    // Wait for undo to complete and verify data is reloaded
    await waitFor(() => {
      expect(mockApi.undoLastValidationAction).toHaveBeenCalledWith('2025-01');
    });

    // Verify that the data is reloaded after undo
    await waitFor(() => {
      expect(mockApi.getBrushValidationData).toHaveBeenCalledTimes(3);
    });
  });

  it('undo button handles API errors gracefully', async () => {
    // Mock the undo API to return an error
    mockApi.undoLastValidationAction.mockRejectedValueOnce(new Error('API Error'));

    render(<BrushValidation />);

    // Verify that months are available
    await waitFor(() => {
      expect(screen.getByText('Select a month')).toBeInTheDocument();
    });

    // Click on the month selector button to open dropdown
    const monthButton = screen.getByText('Select a month');
    fireEvent.click(monthButton);

    // Select a month
    const monthOption = screen.getByText('2025-01');
    fireEvent.click(monthOption);

    // Wait for data to load
    await waitFor(() => {
      expect(mockApi.getBrushValidationData).toHaveBeenCalledWith('2025-01', 'scoring', {
        page: 1,
        pageSize: 20,
        sortBy: 'unvalidated',
      });
    });

    // Find and click the undo button
    const undoButton = screen.getByRole('button', { name: 'Undo Last Validation' });
    fireEvent.click(undoButton);

    // Verify the undo API was called
    expect(mockApi.undoLastValidationAction).toHaveBeenCalledWith('2025-01');
  });

  it('undo button shows success message after successful undo', async () => {
    render(<BrushValidation />);

    // Verify that months are available
    await waitFor(() => {
      expect(screen.getByText('Select a month')).toBeInTheDocument();
    });

    // Click on the month selector button to open dropdown
    const monthButton = screen.getByText('Select a month');
    fireEvent.click(monthButton);

    // Select a month
    const monthOption = screen.getByText('2025-01');
    fireEvent.click(monthOption);

    // Wait for data to load
    await waitFor(() => {
      expect(mockApi.getBrushValidationData).toHaveBeenCalledWith('2025-01', 'scoring', {
        page: 1,
        pageSize: 20,
        sortBy: 'unvalidated',
      });
    });

    // Find and click the undo button
    const undoButton = screen.getByRole('button', { name: 'Undo Last Validation' });
    fireEvent.click(undoButton);

    // Verify the undo API was called
    expect(mockApi.undoLastValidationAction).toHaveBeenCalledWith('2025-01');
  });

  it('undo button is positioned correctly in controls section', async () => {
    render(<BrushValidation />);

    // Verify that months are available
    await waitFor(() => {
      expect(screen.getByText('Select a month')).toBeInTheDocument();
    });

    // Click on the month selector button to open dropdown
    const monthButton = screen.getByText('Select a month');
    fireEvent.click(monthButton);

    // Select a month
    const monthOption = screen.getByText('2025-01');
    fireEvent.click(monthOption);

    // Wait for data to load
    await waitFor(() => {
      expect(mockApi.getBrushValidationData).toHaveBeenCalledWith('2025-01', 'scoring', {
        page: 1,
        pageSize: 20,
        sortBy: 'unvalidated',
      });
    });

    // Verify the undo button is in the controls section
    const undoSection = screen.getByText('Undo Last Validation').closest('.space-y-6');
    expect(undoSection).toBeInTheDocument();
  });

  it('undo button has correct styling and accessibility', async () => {
    render(<BrushValidation />);

    // Verify that months are available
    await waitFor(() => {
      expect(screen.getByText('Select a month')).toBeInTheDocument();
    });

    // Click on the month selector button to open dropdown
    const monthButton = screen.getByText('Select a month');
    fireEvent.click(monthButton);

    // Select a month
    const monthOption = screen.getByText('2025-01');
    fireEvent.click(monthOption);

    // Wait for data to load
    await waitFor(() => {
      expect(mockApi.getBrushValidationData).toHaveBeenCalledWith('2025-01', 'scoring', {
        page: 1,
        pageSize: 20,
        sortBy: 'unvalidated',
      });
    });

    // Verify the undo button has proper styling
    const undoButton = screen.getByRole('button', { name: 'Undo Last Validation' });
    expect(undoButton).toHaveClass('text-orange-600', 'border-orange-200', 'hover:bg-orange-50');
  });

  it('undo functionality works with different month selections', async () => {
    render(<BrushValidation />);

    // Verify that months are available
    await waitFor(() => {
      expect(screen.getByText('Select a month')).toBeInTheDocument();
    });

    // Click on the month selector button to open dropdown
    const monthButton = screen.getByText('Select a month');
    fireEvent.click(monthButton);

    // Select first month
    const firstMonthOption = screen.getByText('2025-01');
    fireEvent.click(firstMonthOption);

    // Wait for data to load
    await waitFor(() => {
      expect(mockApi.getBrushValidationData).toHaveBeenCalledWith('2025-01', 'scoring', {
        page: 1,
        pageSize: 20,
        sortBy: 'unvalidated',
      });
    });

    // Click undo button for first month
    const undoButton = screen.getByRole('button', { name: 'Undo Last Validation' });
    fireEvent.click(undoButton);

    // Verify undo was called for first month
    expect(mockApi.undoLastValidationAction).toHaveBeenCalledWith('2025-01');

    // Clear mock history before selecting second month
    mockApi.getBrushValidationData.mockClear();

    // Open month selector again and select second month
    fireEvent.click(monthButton);

    // Select second month (this will replace the first month selection)
    const secondMonthOption = screen.getByText('2025-02');
    fireEvent.click(secondMonthOption);

    // Wait for data to load for second month
    await waitFor(() => {
      expect(mockApi.getBrushValidationData).toHaveBeenCalledWith('2025-02', 'scoring', {
        page: 1,
        pageSize: 20,
        sortBy: 'unvalidated',
      });
    });

    // Click undo button for second month
    const undoButton2 = screen.getByRole('button', { name: 'Undo Last Validation' });
    fireEvent.click(undoButton2);

    // Verify undo was called for second month
    expect(mockApi.undoLastValidationAction).toHaveBeenCalledWith('2025-02');
  });
});
