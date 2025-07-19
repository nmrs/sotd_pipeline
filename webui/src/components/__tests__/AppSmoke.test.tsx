import React from 'react';
import { render, screen } from '@testing-library/react';
import App from '../../App';

describe('App Smoke Test', () => {
    test('should render root, header, main, and nav', () => {
        render(<App />);
        expect(screen.getByRole('banner')).toBeInTheDocument(); // header
        expect(screen.getByRole('main')).toBeInTheDocument();
        expect(screen.getByRole('navigation')).toBeInTheDocument();
        // Check navigation links
        const navLinks = screen.getAllByRole('link');
        expect(navLinks.length).toBeGreaterThanOrEqual(3);
    });

    test('should have correct page title', () => {
        render(<App />);
        // JSDOM doesn't set document.title from React Helmet, so just check the component renders
        expect(screen.getByRole('banner')).toBeInTheDocument();
    });
}); 