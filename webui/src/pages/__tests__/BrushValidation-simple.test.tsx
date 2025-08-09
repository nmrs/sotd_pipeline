/**
 * Simple tests for BrushValidation page component.
 * Tests core functionality and component structure.
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import BrushValidation from '../BrushValidation';

// Mock the API functions
jest.mock('../../services/api', () => ({
    getBrushValidationData: jest.fn(),
    getBrushValidationStatistics: jest.fn(),
    recordBrushValidationAction: jest.fn(),
    getAvailableMonths: jest.fn().mockResolvedValue(['2025-07', '2025-08', '2025-09']),
    handleApiError: jest.fn((err) => err.message || 'API Error'),
}));

describe('BrushValidation - Core Functionality', () => {
    it('renders page title and main structure', () => {
        render(<BrushValidation />);

        // Page title should be present
        expect(screen.getByText('Brush Validation')).toBeInTheDocument();

        // Badge should be present
        expect(screen.getByText('Multi-System Validation Interface')).toBeInTheDocument();

        // Month selection section should be present
        expect(screen.getByText('Month Selection')).toBeInTheDocument();

        // Initial state message should be present
        expect(screen.getByText('Please select a month to begin validation.')).toBeInTheDocument();
    });

    it('renders without crashing', () => {
        render(<BrushValidation />);
        // If component renders without throwing, test passes
    });

    it('shows month selector', () => {
        render(<BrushValidation />);

        // Should show the month selection card
        expect(screen.getByText('Month Selection')).toBeInTheDocument();

        // Should show month selector button
        expect(screen.getByText('Select Months')).toBeInTheDocument();
    });

    it('displays appropriate empty state', () => {
        render(<BrushValidation />);

        // Should show empty state when no month is selected
        expect(screen.getByText('Please select a month to begin validation.')).toBeInTheDocument();
    });
});
