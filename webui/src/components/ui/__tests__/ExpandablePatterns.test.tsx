import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import ExpandablePatterns from '../ExpandablePatterns';

describe('ExpandablePatterns', () => {
  const mockTopPatterns = [
    { original: 'Barrister and Mann - Seville', count: 5 },
    { original: 'Barrister and Mann - Seville Soap', count: 3 },
    { original: 'B&M Seville', count: 2 },
  ];

  const mockAllPatterns = [
    { original: 'Barrister and Mann - Seville', count: 5 },
    { original: 'Barrister and Mann - Seville Soap', count: 3 },
    { original: 'B&M Seville', count: 2 },
    { original: 'Barrister & Mann Seville', count: 1 },
    { original: 'B&M - Seville', count: 1 },
  ];

  it('renders top patterns initially', () => {
    render(
      <ExpandablePatterns
        topPatterns={mockTopPatterns}
        allPatterns={mockAllPatterns}
        remainingCount={2}
      />
    );

    // Should show top 3 patterns
    expect(screen.getByText('Barrister and Mann - Seville')).toBeInTheDocument();
    expect(screen.getByText('Barrister and Mann - Seville Soap')).toBeInTheDocument();
    expect(screen.getByText('B&M Seville')).toBeInTheDocument();

    // Should show count for each pattern
    expect(screen.getByText('(5)')).toBeInTheDocument();
    expect(screen.getByText('(3)')).toBeInTheDocument();
    expect(screen.getByText('(2)')).toBeInTheDocument();

    // Should show "+ n more" button
    expect(screen.getByText('+ 2 more')).toBeInTheDocument();
  });

  it('expands to show all patterns when clicked', () => {
    render(
      <ExpandablePatterns
        topPatterns={mockTopPatterns}
        allPatterns={mockAllPatterns}
        remainingCount={2}
      />
    );

    // Click the expand button
    fireEvent.click(screen.getByText('+ 2 more'));

    // Should now show all patterns
    expect(screen.getByText('Barrister & Mann Seville')).toBeInTheDocument();
    expect(screen.getByText('B&M - Seville')).toBeInTheDocument();

    // Should show "Show fewer" button
    expect(screen.getByText('Show fewer')).toBeInTheDocument();
  });

  it('collapses back to top patterns when "Show fewer" is clicked', () => {
    render(
      <ExpandablePatterns
        topPatterns={mockTopPatterns}
        allPatterns={mockAllPatterns}
        remainingCount={2}
      />
    );

    // Expand first
    fireEvent.click(screen.getByText('+ 2 more'));

    // Then collapse
    fireEvent.click(screen.getByText('Show fewer'));

    // Should be back to top patterns only
    expect(screen.getByText('Barrister and Mann - Seville')).toBeInTheDocument();
    expect(screen.getByText('Barrister and Mann - Seville Soap')).toBeInTheDocument();
    expect(screen.getByText('B&M Seville')).toBeInTheDocument();

    // Should not show the additional patterns
    expect(screen.queryByText('Barrister & Mann Seville')).not.toBeInTheDocument();
    expect(screen.queryByText('B&M - Seville')).not.toBeInTheDocument();

    // Should show "+ n more" button again
    expect(screen.getByText('+ 2 more')).toBeInTheDocument();
  });

  it('does not show expand button when there are no remaining patterns', () => {
    render(
      <ExpandablePatterns
        topPatterns={mockTopPatterns}
        allPatterns={mockTopPatterns}
        remainingCount={0}
      />
    );

    // Should not show expand button
    expect(screen.queryByText('+ 0 more')).not.toBeInTheDocument();
    expect(screen.queryByText('Show fewer')).not.toBeInTheDocument();
  });

  it('handles empty patterns gracefully', () => {
    const { container } = render(
      <ExpandablePatterns
        topPatterns={[]}
        allPatterns={[]}
        remainingCount={0}
      />
    );

    // Should render without errors
    expect(container.firstChild).toBeInTheDocument();
  });
});
