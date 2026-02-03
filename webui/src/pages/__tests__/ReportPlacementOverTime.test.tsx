import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';

jest.mock('../../services/api', () => ({
  getReportRankingsTables: jest.fn(),
  getReportRankingsItems: jest.fn(),
  getReportRankingsSeries: jest.fn(),
  getReportRankingsPivoted: jest.fn(),
  handleApiError: jest.fn((err: unknown) => (err instanceof Error ? err.message : 'API Error')),
}));

import ReportPlacementOverTime from '../ReportPlacementOverTime';
import * as api from '../../services/api';

const mockGetTables = api.getReportRankingsTables as jest.MockedFunction<
  typeof api.getReportRankingsTables
>;
const mockGetItems = api.getReportRankingsItems as jest.MockedFunction<
  typeof api.getReportRankingsItems
>;
const mockGetSeries = api.getReportRankingsSeries as jest.MockedFunction<
  typeof api.getReportRankingsSeries
>;
const mockGetPivoted = api.getReportRankingsPivoted as jest.MockedFunction<
  typeof api.getReportRankingsPivoted
>;

describe('ReportPlacementOverTime', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockGetTables.mockResolvedValue([
      { id: 'razors', label: 'Razors' },
      { id: 'blades', label: 'Blades' },
    ]);
    mockGetItems.mockResolvedValue(['Razor A', 'Razor B', 'Razor C']);
    mockGetSeries.mockResolvedValue({
      months: ['2025-06', '2025-07'],
      series: [
        { item: 'Razor A', data: [{ month: '2025-06', rank: 1, shaves: 100 }, { month: '2025-07', rank: 2, shaves: 80 }] },
        { item: 'Razor B', data: [{ month: '2025-06', rank: 2, shaves: 80 }, { month: '2025-07', rank: 1, shaves: 90 }] },
      ],
    });
    mockGetPivoted.mockResolvedValue({
      months: ['2025-06', '2025-07'],
      lanes: [
        { rank: 1, points: [{ month: '2025-06', item: 'Razor A', shaves: 100, prev_rank: null }, { month: '2025-07', item: 'Razor B', shaves: 90, prev_rank: 2 }] },
        { rank: 2, points: [{ month: '2025-06', item: 'Razor B', shaves: 80, prev_rank: null }, { month: '2025-07', item: 'Razor A', shaves: 80, prev_rank: 1 }] },
      ],
    });
  });

  it('renders page title and description', async () => {
    render(
      <MemoryRouter>
        <ReportPlacementOverTime />
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByText('Rankings over time')).toBeInTheDocument();
    });
    expect(
      screen.getByText(/see how they ranked month over month/)
    ).toBeInTheDocument();
  });

  it('fetches tables on mount', async () => {
    render(
      <MemoryRouter>
        <ReportPlacementOverTime />
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(mockGetTables).toHaveBeenCalled();
    });
  });

  it('shows empty state when no aggregation selected', async () => {
    render(
      <MemoryRouter>
        <ReportPlacementOverTime />
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(mockGetTables).toHaveBeenCalled();
    });
    expect(
      screen.getByText(/Choose an aggregation and one or more items to see how they placed over time/)
    ).toBeInTheDocument();
  });

  it('shows aggregation dropdown with tables after load', async () => {
    render(
      <MemoryRouter>
        <ReportPlacementOverTime />
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(mockGetTables).toHaveBeenCalled();
    });
    const triggers = screen.getAllByRole('combobox');
    expect(triggers.length).toBeGreaterThanOrEqual(1);
    fireEvent.click(triggers[0]);
    await waitFor(() => {
      expect(screen.getByText('Razors')).toBeInTheDocument();
      expect(screen.getByText('Blades')).toBeInTheDocument();
    });
  });

  it('Load series button is disabled when no aggregation or items selected', async () => {
    render(
      <MemoryRouter>
        <ReportPlacementOverTime />
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(mockGetTables).toHaveBeenCalled();
    });
    const loadButton = screen.getByRole('button', { name: /Load series/i });
    expect(loadButton).toBeDisabled();
  });

  it('renders Controls card with aggregation and Load series button', async () => {
    render(
      <MemoryRouter>
        <ReportPlacementOverTime />
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(mockGetTables).toHaveBeenCalled();
    });
    expect(screen.getByText('Controls')).toBeInTheDocument();
    expect(screen.getByText('Aggregation')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Load series/i })).toBeInTheDocument();
  });

  it('shows View mode toggle (By item / By position) when aggregation selected', async () => {
    render(
      <MemoryRouter>
        <ReportPlacementOverTime />
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(mockGetTables).toHaveBeenCalled();
    });
    const triggers = screen.getAllByRole('combobox');
    fireEvent.click(triggers[0]);
    await waitFor(() => {
      expect(screen.getByText('Razors')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText('Razors'));
    await waitFor(() => {
      expect(screen.getByText('By item')).toBeInTheDocument();
      expect(screen.getByText('By position')).toBeInTheDocument();
    });
  });

  it('fetches pivoted data and shows swim lanes when By position selected', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <ReportPlacementOverTime />
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(mockGetTables).toHaveBeenCalled();
    });
    const aggregationTrigger = screen.getAllByRole('combobox')[0];
    fireEvent.click(aggregationTrigger);
    await waitFor(() => {
      expect(screen.getByText('Razors')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText('Razors'));
    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /By position/i })).toBeInTheDocument();
    });
    await user.click(screen.getByRole('tab', { name: /By position/i }));
    await waitFor(() => {
      expect(mockGetPivoted).toHaveBeenCalledWith('razors');
    });
    await waitFor(
      () => {
        expect(screen.getByText('Swim lanes (top 20)')).toBeInTheDocument();
      },
      { timeout: 3000 }
    );
    expect(screen.getByText('Rank', { selector: 'th' })).toBeInTheDocument();
  });

  it('shows no pivoted data message when pivoted returns empty', async () => {
    mockGetPivoted.mockResolvedValueOnce({ months: [], lanes: [] });
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <ReportPlacementOverTime />
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(mockGetTables).toHaveBeenCalled();
    });
    fireEvent.click(screen.getAllByRole('combobox')[0]);
    await waitFor(() => {
      expect(screen.getByText('Razors')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText('Razors'));
    await user.click(screen.getByRole('tab', { name: /By position/i }));
    await waitFor(() => {
      expect(mockGetPivoted).toHaveBeenCalled();
    });
    await waitFor(() => {
      expect(screen.getByText('No pivoted data for this aggregation.')).toBeInTheDocument();
    });
  });
});
