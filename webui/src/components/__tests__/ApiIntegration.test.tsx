// Mock the API service using test utilities - must be at the top
import { createMockApi } from '../../utils/testUtils';

jest.mock('../../services/api', () => {
  return createMockApi();
});

import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Dashboard from '../../pages/Dashboard';

// Import the mocked functions
import { getAvailableMonths, checkHealth } from '../../services/api';

describe('API Integration', () => {
  beforeEach(() => {
    // Reset all mocks before each test
    (getAvailableMonths as jest.Mock).mockClear();
    (checkHealth as jest.Mock).mockClear();
  });

  test('should handle API error state', async () => {
    // Mock health check to fail (this will trigger error state)
    (checkHealth as jest.Mock).mockRejectedValue(new Error('Backend connection failed'));

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Error')).toBeInTheDocument();
    });
  });

  test('should handle API timeout', async () => {
    // Mock health check to timeout after 1 second
    (checkHealth as jest.Mock).mockImplementation(
      () => new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 1000))
    );

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    // Should handle timeout gracefully
    await waitFor(
      () => {
        expect(screen.getByText('Error')).toBeInTheDocument();
      },
      { timeout: 3000 }
    );
  });

  test('should handle successful API responses', async () => {
    // Mock health check to pass
    (checkHealth as jest.Mock).mockResolvedValue(true);

    // Mock successful API response
    (getAvailableMonths as jest.Mock).mockResolvedValue(['2024-01', '2024-02', '2024-03']);

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    // Should handle success gracefully
    await waitFor(() => {
      expect(screen.getByText('SOTD Pipeline Analyzer')).toBeInTheDocument();
    });
  });
});
