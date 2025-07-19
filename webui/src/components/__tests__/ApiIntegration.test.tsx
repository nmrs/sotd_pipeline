import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Dashboard from '../../pages/Dashboard';

// Mock the API service
jest.mock('../../services/api', () => ({
    getAvailableMonths: jest.fn(),
    getMonthData: jest.fn(),
    getCatalogs: jest.fn(),
    checkHealth: jest.fn(),
}));

// Import the mocked function
import { getAvailableMonths, checkHealth } from '../../services/api';

describe('API Integration', () => {
    beforeEach(() => {
        (getAvailableMonths as jest.Mock).mockClear();
        (checkHealth as jest.Mock).mockClear();
    });

    test('should handle API error state', async () => {
        // Mock health check to pass
        (checkHealth as jest.Mock).mockResolvedValue(true);

        // Mock API error
        (getAvailableMonths as jest.Mock).mockRejectedValue(new Error('API Error'));

        render(
            <MemoryRouter>
                <Dashboard />
            </MemoryRouter>
        );

        await waitFor(() => {
            expect(screen.getByText(/error/i)).toBeInTheDocument();
        });
    });

    test('should handle API timeout', async () => {
        // Mock health check to pass
        (checkHealth as jest.Mock).mockResolvedValue(true);

        // Mock a timeout scenario
        (getAvailableMonths as jest.Mock).mockImplementation(() =>
            new Promise(resolve => setTimeout(() => resolve(['2024-01', '2024-02']), 10000))
        );

        render(
            <MemoryRouter>
                <Dashboard />
            </MemoryRouter>
        );

        // Should handle timeout gracefully
        await waitFor(() => {
            expect(screen.getByText(/timeout|error/i)).toBeInTheDocument();
        }, { timeout: 2000 });
    });
}); 