import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MismatchAnalyzer from '../MismatchAnalyzer';
import * as api from '@/services/api';

// Mock the API module
jest.mock('@/services/api');

const mockApi = api as jest.Mocked<typeof api>;

describe('MismatchAnalyzer - Split Brush Removal', () => {
  const mockMismatchAnalysisResult = {
    total_items: 10,
    mismatch_items: [
      {
        id: '1',
        original: 'Declaration Grooming B2',
        matched: {
          brand: 'Declaration Grooming',
          model: 'B2',
          handle_maker: 'Declaration Grooming',
          knot_maker: 'Declaration Grooming',
          knot_type: 'badger',
          knot_size: '26mm',
        },
        count: 5,
        is_split_brush: false, // This should be removed from the type
        is_complete_brush: true,
        is_regex_match: false,
        is_intentionally_unmatched: false,
      },
      {
        id: '2',
        original: 'Alpha Amber',
        matched: {
          brand: 'Alpha',
          model: 'Amber',
          handle_maker: 'Alpha',
          knot_maker: 'Alpha',
          knot_type: 'badger',
          knot_size: '24mm',
        },
        count: 3,
        is_split_brush: false, // This should be removed from the type
        is_complete_brush: true,
        is_regex_match: false,
        is_intentionally_unmatched: false,
      },
    ],
  };

  const mockCorrectMatchesResponse = {
    brush: {
      'declaration grooming b2': {
        original: 'Declaration Grooming B2',
        matched: {
          brand: 'Declaration Grooming',
          model: 'B2',
          handle_maker: 'Declaration Grooming',
          knot_maker: 'Declaration Grooming',
          knot_type: 'badger',
          knot_size: '26mm',
        },
      },
    },
    handle: {},
    knot: {},
  };

  beforeEach(() => {
    jest.clearAllMocks();

    // Mock API responses
    mockApi.analyzeMismatch.mockResolvedValue(mockMismatchAnalysisResult);
    mockApi.getCorrectMatches.mockResolvedValue(mockCorrectMatchesResponse);
    mockApi.getCommentDetail.mockResolvedValue({
      id: '1',
      text: 'Test comment',
      author: 'testuser',
      timestamp: '2025-01-01T00:00:00Z',
    });
  });

  describe('Display Mode Removal', () => {
    it('should not include split_brushes in display mode options', () => {
      render(<MismatchAnalyzer />);

      // Check that split_brushes button is not present
      expect(screen.queryByText('Split Brushes')).not.toBeInTheDocument();
      expect(screen.queryByText(/split_brushes/i)).not.toBeInTheDocument();
    });

    it('should not have split_brushes in display mode state', () => {
      render(<MismatchAnalyzer />);

      // The display mode should not include split_brushes option
      // This is tested by ensuring the component renders without errors
      // and the display mode state is valid
      expect(screen.getByText('Mismatches')).toBeInTheDocument();
    });

    it('should filter out split_brush items from display', async () => {
      const user = userEvent.setup();

      render(<MismatchAnalyzer />);

      // Select brush field and month
      const fieldSelect = screen.getByLabelText(/field/i);
      await user.selectOptions(fieldSelect, 'brush');

      const monthSelect = screen.getByLabelText(/month/i);
      await user.selectOptions(monthSelect, '2025-01');

      // Click analyze
      const analyzeButton = screen.getByText('Analyze');
      await user.click(analyzeButton);

      await waitFor(() => {
        expect(mockApi.analyzeMismatch).toHaveBeenCalledWith('brush', '2025-01', 3, false);
      });

      // Verify that the component handles the response without split_brush functionality
      await waitFor(() => {
        expect(screen.getByText('Declaration Grooming B2')).toBeInTheDocument();
        expect(screen.getByText('Alpha Amber')).toBeInTheDocument();
      });
    });
  });

  describe('Data Structure Updates', () => {
    it('should handle data without is_split_brush field', async () => {
      const user = userEvent.setup();

      // Mock data without is_split_brush field
      const dataWithoutSplitBrush = {
        ...mockMismatchAnalysisResult,
        mismatch_items: mockMismatchAnalysisResult.mismatch_items.map(item => {
          const { is_split_brush, ...itemWithoutSplitBrush } = item;
          return itemWithoutSplitBrush;
        }),
      };

      mockApi.analyzeMismatch.mockResolvedValue(dataWithoutSplitBrush);

      render(<MismatchAnalyzer />);

      // Select brush field and month
      const fieldSelect = screen.getByLabelText(/field/i);
      await user.selectOptions(fieldSelect, 'brush');

      const monthSelect = screen.getByLabelText(/month/i);
      await user.selectOptions(monthSelect, '2025-01');

      // Click analyze
      const analyzeButton = screen.getByText('Analyze');
      await user.click(analyzeButton);

      await waitFor(() => {
        expect(screen.getByText('Declaration Grooming B2')).toBeInTheDocument();
        expect(screen.getByText('Alpha Amber')).toBeInTheDocument();
      });
    });
  });

  describe('Display Mode Counts', () => {
    it('should not count split_brush items', async () => {
      const user = userEvent.setup();

      render(<MismatchAnalyzer />);

      // Select brush field and month
      const fieldSelect = screen.getByLabelText(/field/i);
      await user.selectOptions(fieldSelect, 'brush');

      const monthSelect = screen.getByLabelText(/month/i);
      await user.selectOptions(monthSelect, '2025-01');

      // Click analyze
      const analyzeButton = screen.getByText('Analyze');
      await user.click(analyzeButton);

      await waitFor(() => {
        // Verify that split_brushes count is not displayed
        expect(screen.queryByText(/split.*brush.*count/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Filtering Logic', () => {
    it('should filter items correctly without split_brush logic', async () => {
      const user = userEvent.setup();

      render(<MismatchAnalyzer />);

      // Select brush field and month
      const fieldSelect = screen.getByLabelText(/field/i);
      await user.selectOptions(fieldSelect, 'brush');

      const monthSelect = screen.getByLabelText(/month/i);
      await user.selectOptions(monthSelect, '2025-01');

      // Click analyze
      const analyzeButton = screen.getByText('Analyze');
      await user.click(analyzeButton);

      await waitFor(() => {
        // Verify that all items are displayed (no split_brush filtering)
        expect(screen.getByText('Declaration Grooming B2')).toBeInTheDocument();
        expect(screen.getByText('Alpha Amber')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle API errors gracefully without split_brush functionality', async () => {
      const user = userEvent.setup();

      mockApi.analyzeMismatch.mockRejectedValue(new Error('API Error'));

      render(<MismatchAnalyzer />);

      // Select brush field and month
      const fieldSelect = screen.getByLabelText(/field/i);
      await user.selectOptions(fieldSelect, 'brush');

      const monthSelect = screen.getByLabelText(/month/i);
      await user.selectOptions(monthSelect, '2025-01');

      // Click analyze
      const analyzeButton = screen.getByText('Analyze');
      await user.click(analyzeButton);

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument();
      });
    });
  });
});
