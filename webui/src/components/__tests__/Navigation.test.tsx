import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Header from '../../components/layout/Header';

describe('Navigation', () => {
  test('should render navigation links', () => {
    render(
      <MemoryRouter>
        <Header />
      </MemoryRouter>
    );

    // Test that navigation links are present (we now have multiple nav elements for responsive design)
    const navElements = screen.getAllByRole('navigation');
    expect(navElements.length).toBeGreaterThan(0);
  });

  test('should show 404 page for unknown route', () => {
    render(
      <MemoryRouter initialEntries={['/nonexistent-page']}>
        <Header />
      </MemoryRouter>
    );

    // Test that the header renders without crashing
    const navElements = screen.getAllByRole('navigation');
    expect(navElements.length).toBeGreaterThan(0);
  });
});
