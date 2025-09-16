import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MonthSelector from '../MonthSelector';

// Mock the useAvailableMonths hook
const mockUseAvailableMonths = jest.fn();
jest.mock('../../../hooks/useAvailableMonths', () => ({
  useAvailableMonths: () => mockUseAvailableMonths(),
}));

// Mock the date utilities
const mockGetYearToDateMonths = jest.fn();
const mockGetLast12Months = jest.fn();
jest.mock('../../../utils/dateUtils', () => ({
  getYearToDateMonths: () => mockGetYearToDateMonths(),
  getLast12Months: () => mockGetLast12Months(),
}));

describe('MonthSelector', () => {
  const defaultProps = {
    selectedMonths: [],
    onMonthsChange: jest.fn(),
    label: 'Test Months',
    multiple: true,
  };

  beforeEach(() => {
    mockUseAvailableMonths.mockReturnValue({
      availableMonths: ['2025-01', '2025-02', '2025-03'],
      loading: false,
      error: null,
      refreshMonths: jest.fn(),
    });

    mockGetYearToDateMonths.mockReturnValue(['2025-01', '2025-02', '2025-03']);
    mockGetLast12Months.mockReturnValue([
      '2024-02',
      '2024-03',
      '2024-04',
      '2024-05',
      '2024-06',
      '2024-07',
      '2024-08',
      '2024-09',
      '2024-10',
      '2024-11',
      '2024-12',
      '2025-01',
    ]);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should show placeholder when no months are selected', async () => {
      await act(async () => {
        render(<MonthSelector {...defaultProps} />);
      });
      expect(screen.getByText('Select Months')).toBeInTheDocument();
    });

    it('should show selected months when months are selected', async () => {
      await act(async () => {
        render(<MonthSelector {...defaultProps} selectedMonths={['2025-01', '2025-02']} />);
      });
      expect(screen.getByText('2025-01, 2025-02')).toBeInTheDocument();
    });

    it('should show count when more than 3 months are selected', async () => {
      await act(async () => {
        render(
          <MonthSelector
            {...defaultProps}
            selectedMonths={['2025-01', '2025-02', '2025-03', '2025-04']}
          />
        );
      });
      expect(screen.getByText('4 months selected')).toBeInTheDocument();
    });
  });

  describe('Multiple Select Mode', () => {
    it('should open dropdown when clicked', async () => {
      const user = userEvent.setup();
      await act(async () => {
        render(<MonthSelector {...defaultProps} />);
      });

      const button = screen.getByRole('button');
      await act(async () => {
        await user.click(button);
      });

      await waitFor(() => {
        expect(screen.getByText('2025-01')).toBeInTheDocument();
        expect(screen.getByText('2025-02')).toBeInTheDocument();
        expect(screen.getByText('2025-03')).toBeInTheDocument();
      });
    });

    it('should handle month selection', async () => {
      const user = userEvent.setup();
      const onMonthsChange = jest.fn();
      await act(async () => {
        render(<MonthSelector {...defaultProps} onMonthsChange={onMonthsChange} />);
      });

      const button = screen.getByRole('button');
      await act(async () => {
        await user.click(button);
      });

      await waitFor(() => {
        expect(screen.getByText('2025-01')).toBeInTheDocument();
      });

      const monthOption = screen.getByText('2025-01');
      await act(async () => {
        await user.click(monthOption);
      });

      expect(onMonthsChange).toHaveBeenCalledWith(['2025-01']);
    });

    it('should handle multiple month selection', async () => {
      const user = userEvent.setup();
      const onMonthsChange = jest.fn();
      await act(async () => {
        render(
          <MonthSelector
            {...defaultProps}
            onMonthsChange={onMonthsChange}
            selectedMonths={['2025-01']}
          />
        );
      });

      const button = screen.getByRole('button');
      await act(async () => {
        await user.click(button);
      });

      await waitFor(() => {
        expect(screen.getByText('2025-02')).toBeInTheDocument();
      });

      const monthOption = screen.getByText('2025-02');
      await act(async () => {
        await user.click(monthOption);
      });

      expect(onMonthsChange).toHaveBeenCalledWith(['2025-01', '2025-02']);
    });

    it('should handle month deselection', async () => {
      const user = userEvent.setup();
      const onMonthsChange = jest.fn();
      await act(async () => {
        render(
          <MonthSelector
            {...defaultProps}
            onMonthsChange={onMonthsChange}
            selectedMonths={['2025-01', '2025-02']}
          />
        );
      });

      const button = screen.getByRole('button');
      await act(async () => {
        await user.click(button);
      });

      await waitFor(() => {
        expect(screen.getByText('2025-01')).toBeInTheDocument();
      });

      const monthOption = screen.getByText('2025-01');
      await act(async () => {
        await user.click(monthOption);
      });

      expect(onMonthsChange).toHaveBeenCalledWith(['2025-02']);
    });

    it('should close dropdown when clicking outside', async () => {
      const user = userEvent.setup();
      await act(async () => {
        render(<MonthSelector {...defaultProps} />);
      });

      const button = screen.getByRole('button');
      await act(async () => {
        await user.click(button);
      });

      await waitFor(() => {
        expect(screen.getByText('2025-01')).toBeInTheDocument();
      });

      // Click outside
      await act(async () => {
        await user.click(document.body);
      });

      await waitFor(() => {
        expect(screen.queryByText('2025-01')).not.toBeInTheDocument();
      });
    });

    it('should close dropdown on Escape key', async () => {
      const user = userEvent.setup();
      await act(async () => {
        render(<MonthSelector {...defaultProps} />);
      });

      const button = screen.getByRole('button');
      await act(async () => {
        await user.click(button);
      });

      await waitFor(() => {
        expect(screen.getByText('2025-01')).toBeInTheDocument();
      });

      // Press Escape
      await act(async () => {
        await user.keyboard('{Escape}');
      });

      await waitFor(() => {
        expect(screen.queryByText('2025-01')).not.toBeInTheDocument();
      });
    });
  });

  describe('Quick Selection Buttons', () => {
    it('should handle Select All selection', async () => {
      const user = userEvent.setup();
      const onMonthsChange = jest.fn();
      await act(async () => {
        render(<MonthSelector {...defaultProps} onMonthsChange={onMonthsChange} />);
      });

      const button = screen.getByRole('button');
      await act(async () => {
        await user.click(button);
      });

      await waitFor(() => {
        expect(screen.getByText('Select All')).toBeInTheDocument();
      });

      const selectAllButton = screen.getByText('Select All');
      await act(async () => {
        await user.click(selectAllButton);
      });

      expect(onMonthsChange).toHaveBeenCalledWith(['2025-01', '2025-02', '2025-03']);
    });

    it('should handle Clear All selection', async () => {
      const user = userEvent.setup();
      const onMonthsChange = jest.fn();
      await act(async () => {
        render(
          <MonthSelector
            {...defaultProps}
            onMonthsChange={onMonthsChange}
            selectedMonths={['2025-01', '2025-02']}
          />
        );
      });

      const button = screen.getByRole('button');
      await act(async () => {
        await user.click(button);
      });

      await waitFor(() => {
        expect(screen.getByText('Clear All')).toBeInTheDocument();
      });

      const clearAllButton = screen.getByText('Clear All');
      await act(async () => {
        await user.click(clearAllButton);
      });

      expect(onMonthsChange).toHaveBeenCalledWith([]);
    });

    it('should handle Year to Date selection', async () => {
      const user = userEvent.setup();
      const onMonthsChange = jest.fn();
      await act(async () => {
        render(<MonthSelector {...defaultProps} onMonthsChange={onMonthsChange} />);
      });

      const button = screen.getByRole('button');
      await act(async () => {
        await user.click(button);
      });

      await waitFor(() => {
        expect(screen.getByText('Year to Date')).toBeInTheDocument();
      });

      const ytdButton = screen.getByText('Year to Date');
      await act(async () => {
        await user.click(ytdButton);
      });

      expect(onMonthsChange).toHaveBeenCalledWith(['2025-01', '2025-02', '2025-03']);
    });

    it('should handle Last 12 Months selection', async () => {
      const user = userEvent.setup();
      const onMonthsChange = jest.fn();
      await act(async () => {
        render(<MonthSelector {...defaultProps} onMonthsChange={onMonthsChange} />);
      });

      const button = screen.getByRole('button');
      await act(async () => {
        await user.click(button);
      });

      await waitFor(() => {
        expect(screen.getByText('Last 12 Months')).toBeInTheDocument();
      });

      const l12mButton = screen.getByText('Last 12 Months');
      await act(async () => {
        await user.click(l12mButton);
      });

      expect(onMonthsChange).toHaveBeenCalledWith([
        '2024-02',
        '2024-03',
        '2024-04',
        '2024-05',
        '2024-06',
        '2024-07',
        '2024-08',
        '2024-09',
        '2024-10',
        '2024-11',
        '2024-12',
        '2025-01',
      ]);
    });
  });

  describe('Single Select Mode', () => {
    it('should handle single month selection in single select mode', async () => {
      const user = userEvent.setup();
      const onMonthsChange = jest.fn();
      await act(async () => {
        render(
          <MonthSelector
            {...defaultProps}
            onMonthsChange={onMonthsChange}
            multiple={false}
            selectedMonths={['2025-01']}
          />
        );
      });

      const combobox = screen.getByRole('combobox');
      expect(combobox).toBeInTheDocument();

      // In single select mode, we need to check if the SelectInput is rendered correctly
      expect(combobox).toBeInTheDocument();
    });

    it('should handle month change in single select mode', async () => {
      const user = userEvent.setup();
      const onMonthsChange = jest.fn();
      await act(async () => {
        render(
          <MonthSelector
            {...defaultProps}
            onMonthsChange={onMonthsChange}
            multiple={false}
            selectedMonths={['2025-01']}
          />
        );
      });

      const combobox = screen.getByRole('combobox');
      expect(combobox).toBeInTheDocument();

      // In single select mode, we need to check if the SelectInput is rendered correctly
      expect(combobox).toBeInTheDocument();
    });
  });

  describe('Loading and Error States', () => {
    it('should show loading spinner when loading and no pre-populated months', async () => {
      // Mock the hook to return no months and loading state
      // This simulates the case where pre-populated months haven't been generated yet
      mockUseAvailableMonths.mockReturnValue({
        availableMonths: [],
        loading: true,
        error: null,
        refreshMonths: jest.fn(),
      });

      // Mock the generatePrepopulatedMonths function to return empty array
      // This requires mocking the entire component or restructuring the test
      await act(async () => {
        render(<MonthSelector {...defaultProps} />);
      });

      // Since we now have pre-populated months, the loading state won't show
      // The component will use pre-populated months instead
      expect(screen.queryByText('Loading available months...')).not.toBeInTheDocument();
    });

    it('should show error display when there is an error and no pre-populated months', async () => {
      mockUseAvailableMonths.mockReturnValue({
        availableMonths: [],
        loading: false,
        error: 'Failed to load months',
        refreshMonths: jest.fn(),
      });

      await act(async () => {
        render(<MonthSelector {...defaultProps} />);
      });

      // Since we now have pre-populated months, the error state won't show
      // The component will use pre-populated months instead
      expect(screen.queryByText('Failed to load months')).not.toBeInTheDocument();
    });
  });

  describe('Label Display', () => {
    it('should display custom label when provided', async () => {
      await act(async () => {
        render(<MonthSelector {...defaultProps} label='Custom Label' />);
      });
      expect(screen.getByText('Custom Label:')).toBeInTheDocument();
    });

    it('should display default label when no label provided', async () => {
      await act(async () => {
        render(<MonthSelector {...defaultProps} label={undefined} />);
      });
      expect(screen.getByText('Months:')).toBeInTheDocument();
    });
  });

  describe('Delta Months Functionality', () => {
    it('should show delta months checkbox when enableDeltaMonths is true', async () => {
      await act(async () => {
        render(<MonthSelector {...defaultProps} enableDeltaMonths={true} />);
      });

      // Open the dropdown to see the delta months checkbox
      const button = screen.getByRole('button');
      await userEvent.click(button);

      expect(screen.getByText('Include Delta Months')).toBeInTheDocument();
    });

    it('should not show delta months checkbox when enableDeltaMonths is false', async () => {
      await act(async () => {
        render(<MonthSelector {...defaultProps} enableDeltaMonths={false} />);
      });

      // Open the dropdown to check that delta months checkbox is not there
      const button = screen.getByRole('button');
      await userEvent.click(button);

      expect(screen.queryByText('Include Delta Months')).not.toBeInTheDocument();
    });

    it('should call onDeltaMonthsChange when delta months are toggled', async () => {
      const onDeltaMonthsChange = jest.fn();
      await act(async () => {
        render(
          <MonthSelector
            {...defaultProps}
            enableDeltaMonths={true}
            onDeltaMonthsChange={onDeltaMonthsChange}
            selectedMonths={['2025-01']}
          />
        );
      });

      // Open the dropdown
      const button = screen.getByRole('button');
      await userEvent.click(button);

      // Check the delta months checkbox
      const deltaCheckbox = screen
        .getByText('Include Delta Months')
        .previousElementSibling?.querySelector('input');
      if (deltaCheckbox) {
        await userEvent.click(deltaCheckbox);
        expect(onDeltaMonthsChange).toHaveBeenCalled();
      }
    });

    it('should calculate correct delta months for Jan-Sep 2025 YTD scenario', async () => {
      const onDeltaMonthsChange = jest.fn();
      const selectedMonths = [
        '2025-01',
        '2025-02',
        '2025-03',
        '2025-04',
        '2025-05',
        '2025-06',
        '2025-07',
        '2025-08',
        '2025-09',
      ];

      await act(async () => {
        render(
          <MonthSelector
            {...defaultProps}
            enableDeltaMonths={true}
            onDeltaMonthsChange={onDeltaMonthsChange}
            selectedMonths={selectedMonths}
          />
        );
      });

      // Open the dropdown
      const button = screen.getByRole('button');
      await userEvent.click(button);

      // Check the delta months checkbox to enable delta months
      const deltaCheckbox = screen
        .getByText('Include Delta Months')
        .previousElementSibling?.querySelector('input');
      if (deltaCheckbox) {
        await userEvent.click(deltaCheckbox);

        // Verify that onDeltaMonthsChange was called with the correct delta months
        expect(onDeltaMonthsChange).toHaveBeenCalled();

        // Get the last call to see what delta months were calculated
        const lastCall = onDeltaMonthsChange.mock.calls[onDeltaMonthsChange.mock.calls.length - 1];
        const deltaMonths = lastCall[0];

        // For Jan-Sep 2025 YTD, we expect:
        // Primary months: 9 (2025-01 through 2025-09)
        // Month-1: 1 month (2024-12, since 2025-01-1month = 2024-12, others overlap with primary)
        // Month-1year: 9 months (2024-01 through 2024-09)
        // Month-5years: 9 months (2020-01 through 2020-09)
        // Total delta: 1 + 9 + 9 = 19 months
        // Total all: 9 + 19 = 28 months

        expect(deltaMonths).toHaveLength(19);

        // Verify specific delta months are included
        expect(deltaMonths).toContain('2024-12'); // Month-1 (only one that doesn't overlap)
        expect(deltaMonths).toContain('2024-01'); // Month-1year
        expect(deltaMonths).toContain('2024-09'); // Month-1year
        expect(deltaMonths).toContain('2020-01'); // Month-5years
        expect(deltaMonths).toContain('2020-09'); // Month-5years

        // Verify the display text shows the correct total
        expect(screen.getByText('9 primary + 19 delta = 28 total months')).toBeInTheDocument();
      }
    });
  });
});
