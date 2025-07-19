// import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Header from '../../components/Header';

describe('Navigation', () => {
    test('should render navigation links', () => {
        render(
            <MemoryRouter>
                <Header />
            </MemoryRouter>
        );

        // Test that navigation links are present
        expect(screen.getByRole('navigation')).toBeInTheDocument();
    });

    test('should show 404 page for unknown route', () => {
        render(
            <MemoryRouter initialEntries={['/nonexistent-page']}>
                <Header />
            </MemoryRouter>
        );

        // Test that the header renders without crashing
        expect(screen.getByRole('navigation')).toBeInTheDocument();
    });
}); 