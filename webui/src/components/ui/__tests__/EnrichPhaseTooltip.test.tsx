import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import EnrichPhaseTooltip from '../EnrichPhaseTooltip';

describe('EnrichPhaseTooltip', () => {
  const mockOriginalData = {
    knot: {
      fiber: 'Synthetic',
      knot_size_mm: 24,
    },
  };

  const mockEnrichedData = {
    fiber: 'Badger',
    knot_size_mm: 26,
    _extraction_source: 'user_override_catalog',
  };

  it('renders children correctly', () => {
    render(
      <EnrichPhaseTooltip
        originalData={mockOriginalData}
        enrichedData={mockEnrichedData}
        field="brush"
      >
        <span>Test Content</span>
      </EnrichPhaseTooltip>
    );

    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('shows tooltip on hover', () => {
    render(
      <EnrichPhaseTooltip
        originalData={mockOriginalData}
        enrichedData={mockEnrichedData}
        field="brush"
      >
        <span>Test Content</span>
      </EnrichPhaseTooltip>
    );

    const trigger = screen.getByText('Test Content');
    fireEvent.mouseEnter(trigger);

    expect(screen.getByText('Enrich Phase Adjustments:')).toBeInTheDocument();
    expect(screen.getByText(/Fiber: Synthetic → Badger/)).toBeInTheDocument();
    expect(screen.getByText(/Knot Size: 24 → 26/)).toBeInTheDocument();
    expect(screen.getByText(/Source: user_override_catalog/)).toBeInTheDocument();
  });

  it('hides tooltip on mouse leave', () => {
    render(
      <EnrichPhaseTooltip
        originalData={mockOriginalData}
        enrichedData={mockEnrichedData}
        field="brush"
      >
        <span>Test Content</span>
      </EnrichPhaseTooltip>
    );

    const trigger = screen.getByText('Test Content');
    fireEvent.mouseEnter(trigger);
    expect(screen.getByText('Enrich Phase Adjustments:')).toBeInTheDocument();

    fireEvent.mouseLeave(trigger);
    expect(screen.queryByText('Enrich Phase Adjustments:')).not.toBeInTheDocument();
  });

  it('shows no changes message when data is identical', () => {
    const identicalData = {
      fiber: 'Synthetic',
      knot_size_mm: 24,
    };

    render(
      <EnrichPhaseTooltip
        originalData={identicalData}
        enrichedData={identicalData}
        field="brush"
      >
        <span>Test Content</span>
      </EnrichPhaseTooltip>
    );

    const trigger = screen.getByText('Test Content');
    fireEvent.mouseEnter(trigger);

    expect(screen.getByText('No enrich-phase changes detected')).toBeInTheDocument();
  });
}); 