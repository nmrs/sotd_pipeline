/**
 * Simple tests for BrushValidation page component.
 * Tests core functionality and component structure.
 */

import React from 'react';
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
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
      correct_entries: 1,
      user_processed: 1,
      overridden_count: 1,
      total_processed: 2,
      unprocessed_count: 0,
      processing_rate: 1.0,
      // Legacy fields for backward compatibility
      validated_count: 1,
      user_validations: 1,
      unvalidated_count: 0,
      validation_rate: 1.0,
      total_actions: 2,
    });

    mockApi.recordBrushValidationAction.mockResolvedValue({
      success: true,
      message: 'Action recorded successfully',
    });
  });

  it('renders brush validation page', async () => {
    await act(async () => {
      render(<BrushValidation />);
    });

    expect(screen.getByText('Brush Validation')).toBeInTheDocument();
    expect(screen.getByText('Select a month')).toBeInTheDocument();
  });

  it('loads and displays brush validation data', async () => {
    await act(async () => {
      render(<BrushValidation />);
    });

    // Verify that months are available
    await waitFor(() => {
      expect(screen.getByText('Select a month')).toBeInTheDocument();
    });

    // Click on the month selector button to open dropdown
    const monthButton = screen.getByText('Select a month');
    await act(async () => {
      fireEvent.click(monthButton);
    });

    // Select a month
    const monthOption = screen.getByText('2025-01');
    await act(async () => {
      fireEvent.click(monthOption);
    });

    // Wait for data to load
    await waitFor(() => {
      expect(mockApi.getBrushValidationData).toHaveBeenCalledWith('2025-01', 'scoring', {
        page: 1,
        pageSize: 20,
        sortBy: 'unvalidated',
        // New backend filtering parameters (intentional improvement)
        strategyCount: undefined,
        showSingleStrategy: undefined,
        showMultipleStrategy: undefined
      });
    });

    // Verify that the data is displayed
    await waitFor(() => {
      expect(screen.getByText('Test Brush 1')).toBeInTheDocument();
      expect(screen.getByText('Test Brush 2')).toBeInTheDocument();
    });
  });

  it('handles validate action recording', async () => {
    await act(async () => {
      render(<BrushValidation />);
    });

    // Verify that months are available
    await waitFor(() => {
      expect(screen.getByText('Select a month')).toBeInTheDocument();
    });

    // Click on the month selector button to open dropdown
    const monthButton = screen.getByText('Select a month');
    await act(async () => {
      fireEvent.click(monthButton);
    });

    // Select a month
    const monthOption = screen.getByText('2025-01');
    await act(async () => {
      fireEvent.click(monthOption);
    });

    // Wait for data to load
    await waitFor(() => {
      expect(mockApi.getBrushValidationData).toHaveBeenCalledWith('2025-01', 'scoring', {
        page: 1,
        pageSize: 20,
        sortBy: 'unvalidated',
        // New backend filtering parameters (intentional improvement)
        strategyCount: undefined,
        showSingleStrategy: undefined,
        showMultipleStrategy: undefined
      });
    });

    // Find and click the validate button for the first entry
    const validateButtons = screen.getAllByText('Validate');
    if (validateButtons.length > 0) {
      await act(async () => {
        await userEvent.click(validateButtons[0]);
      });

      // Verify the API was called
      expect(mockApi.recordBrushValidationAction).toHaveBeenCalledWith({
        input_text: 'test brush 1',
        month: '2025-01',
        system_used: 'scoring',
        action: 'validate',
      });
    }
  });

  it('handles override action recording', async () => {
    await act(async () => {
      render(<BrushValidation />);
    });

    // Verify that months are available
    await waitFor(() => {
      expect(screen.getByText('Select a month')).toBeInTheDocument();
    });

    // Click on the month selector button to open dropdown
    const monthButton = screen.getByText('Select a month');
    await act(async () => {
      fireEvent.click(monthButton);
    });

    // Select a month
    const monthOption = screen.getByText('2025-01');
    await act(async () => {
      fireEvent.click(monthOption);
    });

    // Wait for data to load
    await waitFor(() => {
      expect(mockApi.getBrushValidationData).toHaveBeenCalledWith('2025-01', 'scoring', {
        page: 1,
        pageSize: 20,
        sortBy: 'unvalidated',
        // New backend filtering parameters (intentional improvement)
        strategyCount: undefined,
        showSingleStrategy: undefined,
        showMultipleStrategy: undefined
      });
    });

    // Find and click the override button for the second entry
    const overrideButtons = screen.getAllByText('Override');
    if (overrideButtons.length > 0) {
      await act(async () => {
        fireEvent.click(overrideButtons[1]);
      });

      // Wait for override state to be set and UI to update
      await waitFor(() => {
        expect(screen.getByText('Confirm Override')).toBeInTheDocument();
      });

      // Now click confirm override to complete the override action
      const confirmOverrideButton = screen.getByText('Confirm Override');
      await act(async () => {
        fireEvent.click(confirmOverrideButton);
      });

      // Wait for the API call to be made
      await waitFor(() => {
        expect(mockApi.recordBrushValidationAction).toHaveBeenCalledWith({
          input_text: 'test brush 2',
          month: '2025-01',
          system_used: 'scoring',
          action: 'override',
          strategy_index: 0,
        });
      });
    }
  });
});
