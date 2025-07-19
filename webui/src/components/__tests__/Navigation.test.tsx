import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from '../../App';

describe('Navigation', () => {
    test('should render navigation links', () => {
        render(
            <MemoryRouter>
                <App />
            </MemoryRouter>
        );
        const navLinks = screen.getAllByRole('link');
        expect(navLinks.length).toBeGreaterThanOrEqual(3);
    });

    test('should show 404 page for unknown route', () => {
        render(
            <MemoryRouter initialEntries={['/nonexistent-page']}>
                <App />
            </MemoryRouter>
        );
        // Check for a 404 or not found message
        expect(screen.getByText(/not found|404/i)).toBeInTheDocument();
    });
}); 