import React from 'react';
import { render, screen } from '@testing-library/react';
import { DeltaMonthsInfoPanel } from '../DeltaMonthsInfoPanel';

describe('DeltaMonthsInfoPanel', () => {
  describe('Rendering', () => {
    test('does not render when deltaMonths is empty', () => {
      const { container } = render(
        <DeltaMonthsInfoPanel selectedMonths={['2025-01', '2025-02']} deltaMonths={[]} />
      );
      expect(container.firstChild).toBeNull();
    });

    test('renders when deltaMonths is provided', () => {
      render(
        <DeltaMonthsInfoPanel
          selectedMonths={['2025-01', '2025-02', '2024-01', '2024-02']}
          deltaMonths={['2024-01', '2024-02']}
        />
      );
      expect(screen.getByText('📊 Delta Months Analysis')).toBeInTheDocument();
    });

    test('renders default variant correctly', () => {
      const { container } = render(
        <DeltaMonthsInfoPanel
          selectedMonths={['2025-01', '2025-02', '2024-01', '2024-02']}
          deltaMonths={['2024-01', '2024-02']}
          variant='default'
        />
      );
      // Default variant uses div with bg-blue-50
      const panel = container.querySelector('.bg-blue-50');
      expect(panel).toBeInTheDocument();
    });

    test('renders card variant correctly', () => {
      const { container } = render(
        <DeltaMonthsInfoPanel
          selectedMonths={['2025-01', '2025-02', '2024-01', '2024-02']}
          deltaMonths={['2024-01', '2024-02']}
          variant='card'
        />
      );
      // Card variant uses Card component
      const card = container.querySelector('[class*="rounded-lg"]');
      expect(card).toBeInTheDocument();
    });
  });

  describe('Month Calculations', () => {
    test('correctly calculates primary months by filtering out delta months', () => {
      const selectedMonths = ['2025-01', '2025-02', '2025-03', '2024-01', '2024-02', '2020-01'];
      const deltaMonths = ['2024-01', '2024-02', '2020-01'];
      const expectedPrimary = ['2025-01', '2025-02', '2025-03'];

      render(
        <DeltaMonthsInfoPanel selectedMonths={selectedMonths} deltaMonths={deltaMonths} />
      );

      // Check that primary months are displayed correctly
      const primaryText = screen.getByText(/Primary months:/);
      expect(primaryText).toBeInTheDocument();
      expect(primaryText.textContent).toContain('2025-01');
      expect(primaryText.textContent).toContain('2025-02');
      expect(primaryText.textContent).toContain('2025-03');
      // Should not contain delta months
      expect(primaryText.textContent).not.toContain('2024-01');
      expect(primaryText.textContent).not.toContain('2024-02');
    });

    test('correctly displays delta months', () => {
      const selectedMonths = ['2025-01', '2025-02', '2024-01', '2024-02'];
      const deltaMonths = ['2024-01', '2024-02'];

      render(
        <DeltaMonthsInfoPanel selectedMonths={selectedMonths} deltaMonths={deltaMonths} />
      );

      const deltaText = screen.getByText(/Delta months:/);
      expect(deltaText).toBeInTheDocument();
      expect(deltaText.textContent).toContain('2024-01');
      expect(deltaText.textContent).toContain('2024-02');
    });

    test('correctly calculates total months as selectedMonths.length (not sum)', () => {
      const selectedMonths = ['2025-01', '2025-02', '2025-03', '2024-01', '2024-02', '2020-01'];
      const deltaMonths = ['2024-01', '2024-02', '2020-01'];
      // Total should be 6 (selectedMonths.length), not 9 (selectedMonths.length + deltaMonths.length)

      render(
        <DeltaMonthsInfoPanel selectedMonths={selectedMonths} deltaMonths={deltaMonths} />
      );

      const totalText = screen.getByText(/Total months:/);
      expect(totalText).toBeInTheDocument();
      expect(totalText.textContent).toContain('6');
      expect(totalText.textContent).not.toContain('9');
    });

    test('handles Year to Date scenario correctly (12 primary + 24 delta = 36 total)', () => {
      // Simulate Year to Date: 12 months from 2025-01 to 2025-12
      const primaryMonths = [
        '2025-01',
        '2025-02',
        '2025-03',
        '2025-04',
        '2025-05',
        '2025-06',
        '2025-07',
        '2025-08',
        '2025-09',
        '2025-10',
        '2025-11',
        '2025-12',
      ];
      // Delta months: 2024-01 to 2024-12 (1 year ago) + 2020-01 to 2020-12 (5 years ago)
      const deltaMonths = [
        '2024-01',
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
        '2020-01',
        '2020-02',
        '2020-03',
        '2020-04',
        '2020-05',
        '2020-06',
        '2020-07',
        '2020-08',
        '2020-09',
        '2020-10',
        '2020-11',
        '2020-12',
      ];
      const selectedMonths = [...primaryMonths, ...deltaMonths]; // All 36 months

      render(
        <DeltaMonthsInfoPanel selectedMonths={selectedMonths} deltaMonths={deltaMonths} />
      );

      const totalText = screen.getByText(/Total months:/);
      expect(totalText.textContent).toContain('36');
      expect(totalText.textContent).not.toContain('60'); // Should not be 12 + 24 + 24 = 60
    });
  });

  describe('Content Display', () => {
    test('displays all required text content', () => {
      render(
        <DeltaMonthsInfoPanel
          selectedMonths={['2025-01', '2024-01']}
          deltaMonths={['2024-01']}
        />
      );

      expect(screen.getByText('📊 Delta Months Analysis')).toBeInTheDocument();
      expect(screen.getByText(/Historical Comparison:/)).toBeInTheDocument();
      expect(screen.getByText(/Primary months:/)).toBeInTheDocument();
      expect(screen.getByText(/Delta months:/)).toBeInTheDocument();
      expect(screen.getByText(/Total months:/)).toBeInTheDocument();
      expect(screen.getByText(/Delta months include:/)).toBeInTheDocument();
      expect(screen.getByText(/month-1, month-1year, month-5years/)).toBeInTheDocument();
      expect(screen.getByText(/CLI.*--delta.*flag/)).toBeInTheDocument();
    });

    test('displays months in correct format', () => {
      render(
        <DeltaMonthsInfoPanel
          selectedMonths={['2025-01', '2025-02', '2024-01']}
          deltaMonths={['2024-01']}
        />
      );

      const primaryText = screen.getByText(/Primary months:/);
      expect(primaryText.textContent).toMatch(/2025-01.*2025-02/);
    });
  });

  describe('Edge Cases', () => {
    test('handles empty selectedMonths gracefully', () => {
      const { container } = render(
        <DeltaMonthsInfoPanel selectedMonths={[]} deltaMonths={['2024-01']} />
      );
      // Should still render if deltaMonths is provided
      expect(screen.getByText('📊 Delta Months Analysis')).toBeInTheDocument();
    });

    test('handles all months being delta months', () => {
      const selectedMonths = ['2024-01', '2024-02'];
      const deltaMonths = ['2024-01', '2024-02'];

      render(
        <DeltaMonthsInfoPanel selectedMonths={selectedMonths} deltaMonths={deltaMonths} />
      );

      const primaryText = screen.getByText(/Primary months:/);
      // Primary months should be empty (all are delta)
      expect(primaryText.textContent).toMatch(/Primary months:\s*$/);
    });

    test('handles no overlap between selected and delta months', () => {
      const selectedMonths = ['2025-01', '2025-02'];
      const deltaMonths = ['2024-01', '2024-02'];

      render(
        <DeltaMonthsInfoPanel selectedMonths={selectedMonths} deltaMonths={deltaMonths} />
      );

      // In this case, selectedMonths should equal primaryMonths
      const primaryText = screen.getByText(/Primary months:/);
      expect(primaryText.textContent).toContain('2025-01');
      expect(primaryText.textContent).toContain('2025-02');
    });
  });
});

