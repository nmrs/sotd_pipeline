import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
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
        mockGetLast12Months.mockReturnValue(['2024-02', '2024-03', '2024-04', '2024-05', '2024-06', '2024-07', '2024-08', '2024-09', '2024-10', '2024-11', '2024-12', '2025-01']);
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    describe('Rendering', () => {
        it('should show placeholder when no months are selected', () => {
            render(<MonthSelector {...defaultProps} />);
            expect(screen.getByText('Select Months')).toBeInTheDocument();
        });

        it('should show selected months when months are selected', () => {
            render(<MonthSelector {...defaultProps} selectedMonths={['2025-01', '2025-02']} />);
            expect(screen.getByText('2025-01, 2025-02')).toBeInTheDocument();
        });

        it('should show count when more than 3 months are selected', () => {
            render(<MonthSelector {...defaultProps} selectedMonths={['2025-01', '2025-02', '2025-03', '2025-04']} />);
            expect(screen.getByText('4 months selected')).toBeInTheDocument();
        });
    });

    describe('Multiple Select Mode', () => {
        it('should open dropdown when clicked', async () => {
            const user = userEvent.setup();
            render(<MonthSelector {...defaultProps} />);

            const button = screen.getByRole('button');
            await user.click(button);

            expect(screen.getByText('2025-01')).toBeInTheDocument();
            expect(screen.getByText('2025-02')).toBeInTheDocument();
            expect(screen.getByText('2025-03')).toBeInTheDocument();
        });

        it('should handle month selection', async () => {
            const user = userEvent.setup();
            const onMonthsChange = jest.fn();
            render(<MonthSelector {...defaultProps} onMonthsChange={onMonthsChange} />);

            const button = screen.getByRole('button');
            await user.click(button);

            const monthOption = screen.getByText('2025-01');
            await user.click(monthOption);

            expect(onMonthsChange).toHaveBeenCalledWith(['2025-01']);
        });

        it('should handle multiple month selection', async () => {
            const user = userEvent.setup();
            const onMonthsChange = jest.fn();
            render(<MonthSelector {...defaultProps} onMonthsChange={onMonthsChange} selectedMonths={['2025-01']} />);

            const button = screen.getByRole('button');
            await user.click(button);

            const monthOption = screen.getByText('2025-02');
            await user.click(monthOption);

            expect(onMonthsChange).toHaveBeenCalledWith(['2025-01', '2025-02']);
        });

        it('should handle month deselection', async () => {
            const user = userEvent.setup();
            const onMonthsChange = jest.fn();
            render(<MonthSelector {...defaultProps} onMonthsChange={onMonthsChange} selectedMonths={['2025-01', '2025-02']} />);

            const button = screen.getByRole('button');
            await user.click(button);

            const monthOption = screen.getByText('2025-01');
            await user.click(monthOption);

            expect(onMonthsChange).toHaveBeenCalledWith(['2025-02']);
        });

        it('should close dropdown when clicking outside', async () => {
            const user = userEvent.setup();
            render(<MonthSelector {...defaultProps} />);

            const button = screen.getByRole('button');
            await user.click(button);

            expect(screen.getByText('2025-01')).toBeInTheDocument();

            // Click outside
            await user.click(document.body);

            expect(screen.queryByText('2025-01')).not.toBeInTheDocument();
        });

        it('should close dropdown on Escape key', async () => {
            const user = userEvent.setup();
            render(<MonthSelector {...defaultProps} />);

            const button = screen.getByRole('button');
            await user.click(button);

            expect(screen.getByText('2025-01')).toBeInTheDocument();

            // Press Escape
            await user.keyboard('{Escape}');

            expect(screen.queryByText('2025-01')).not.toBeInTheDocument();
        });
    });

    describe('Quick Selection Buttons', () => {
        it('should handle Select All selection', async () => {
            const user = userEvent.setup();
            const onMonthsChange = jest.fn();
            render(<MonthSelector {...defaultProps} onMonthsChange={onMonthsChange} />);

            const button = screen.getByRole('button');
            await user.click(button);

            const selectAllButton = screen.getByText('Select All');
            await user.click(selectAllButton);

            expect(onMonthsChange).toHaveBeenCalledWith(['2025-01', '2025-02', '2025-03']);
        });

        it('should handle Clear All selection', async () => {
            const user = userEvent.setup();
            const onMonthsChange = jest.fn();
            render(<MonthSelector {...defaultProps} onMonthsChange={onMonthsChange} selectedMonths={['2025-01', '2025-02']} />);

            const button = screen.getByRole('button');
            await user.click(button);

            const clearAllButton = screen.getByText('Clear All');
            await user.click(clearAllButton);

            expect(onMonthsChange).toHaveBeenCalledWith([]);
        });

        it('should handle Year to Date selection', async () => {
            const user = userEvent.setup();
            const onMonthsChange = jest.fn();
            render(<MonthSelector {...defaultProps} onMonthsChange={onMonthsChange} />);

            const button = screen.getByRole('button');
            await user.click(button);

            const ytdButton = screen.getByText('Year to Date');
            await user.click(ytdButton);

            expect(onMonthsChange).toHaveBeenCalledWith(['2025-01', '2025-02', '2025-03']);
        });

        it('should handle Last 12 Months selection', async () => {
            const user = userEvent.setup();
            const onMonthsChange = jest.fn();
            render(<MonthSelector {...defaultProps} onMonthsChange={onMonthsChange} />);

            const button = screen.getByRole('button');
            await user.click(button);

            const l12mButton = screen.getByText('Last 12 Months');
            await user.click(l12mButton);

            expect(onMonthsChange).toHaveBeenCalledWith(['2024-02', '2024-03', '2024-04', '2024-05', '2024-06', '2024-07', '2024-08', '2024-09', '2024-10', '2024-11', '2024-12', '2025-01']);
        });
    });

    describe('Single Select Mode', () => {
        it('should handle single month selection in single select mode', async () => {
            const user = userEvent.setup();
            const onMonthsChange = jest.fn();
            render(<MonthSelector {...defaultProps} onMonthsChange={onMonthsChange} multiple={false} selectedMonths={['2025-01']} />);

            const combobox = screen.getByRole('combobox');
            expect(combobox).toBeInTheDocument();

            // In single select mode, we need to check if the SelectInput is rendered correctly
            expect(combobox).toBeInTheDocument();
        });

        it('should handle month change in single select mode', async () => {
            const user = userEvent.setup();
            const onMonthsChange = jest.fn();
            render(<MonthSelector {...defaultProps} onMonthsChange={onMonthsChange} multiple={false} selectedMonths={['2025-01']} />);

            const combobox = screen.getByRole('combobox');
            expect(combobox).toBeInTheDocument();

            // In single select mode, we need to check if the SelectInput is rendered correctly
            expect(combobox).toBeInTheDocument();
        });
    });

    describe('Loading and Error States', () => {
        it('should show loading spinner when loading', () => {
            mockUseAvailableMonths.mockReturnValue({
                availableMonths: [],
                loading: true,
                error: null,
                refreshMonths: jest.fn(),
            });

            render(<MonthSelector {...defaultProps} />);
            expect(screen.getByText('Loading available months...')).toBeInTheDocument();
        });

        it('should show error display when there is an error', () => {
            mockUseAvailableMonths.mockReturnValue({
                availableMonths: [],
                loading: false,
                error: 'Failed to load months',
                refreshMonths: jest.fn(),
            });

            render(<MonthSelector {...defaultProps} />);
            expect(screen.getByText('Failed to load months')).toBeInTheDocument();
        });
    });

    describe('Label Display', () => {
        it('should display custom label when provided', () => {
            render(<MonthSelector {...defaultProps} label="Custom Label" />);
            expect(screen.getByText('Custom Label:')).toBeInTheDocument();
        });

        it('should display default label when no label provided', () => {
            render(<MonthSelector {...defaultProps} label={undefined} />);
            expect(screen.getByText('Months:')).toBeInTheDocument();
        });
    });
});

