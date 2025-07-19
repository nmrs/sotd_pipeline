import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Simple test component
const SimpleComponent: React.FC<{ title: string; onClick?: () => void }> = ({ title, onClick }) => {
    return (
        <div>
            <h1>{title}</h1>
            <button onClick={onClick}>Click me</button>
        </div>
    );
};

describe('SimpleComponent', () => {
    test('should render title correctly', () => {
        render(<SimpleComponent title="Test Title" />);

        expect(screen.getByText('Test Title')).toBeInTheDocument();
        expect(screen.getByRole('button')).toBeInTheDocument();
    });

    test('should handle click events', async () => {
        const mockOnClick = jest.fn();
        const user = userEvent.setup();

        render(<SimpleComponent title="Test Title" onClick={mockOnClick} />);

        const button = screen.getByRole('button');
        await user.click(button);

        expect(mockOnClick).toHaveBeenCalledTimes(1);
    });

    test('should render without onClick prop', () => {
        render(<SimpleComponent title="Test Title" />);

        expect(screen.getByText('Test Title')).toBeInTheDocument();
        expect(screen.getByRole('button')).toBeInTheDocument();
    });
}); 