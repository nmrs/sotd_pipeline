import { render, screen } from '@testing-library/react';
import ErrorDisplay from '../feedback/ErrorDisplay';
import MessageDisplay from '../feedback/MessageDisplay';

// Test that feedback components work correctly from feedback/ directory
describe('Feedback Components', () => {
  test('should import ErrorDisplay component from feedback directory', () => {
    // This test verifies that ErrorDisplay.tsx can be imported from feedback/
    // and renders correctly
    expect(() => {
      // We'll implement the actual import in the next step
      // For now, just verify the test structure
      expect(ErrorDisplay).toBeDefined();
    }).not.toThrow();
  });

  test('should import MessageDisplay component from feedback directory', () => {
    // This test verifies that MessageDisplay.tsx can be imported from feedback/
    // and renders correctly
    expect(() => {
      // We'll implement the actual import in the next step
      // For now, just verify the test structure
      expect(MessageDisplay).toBeDefined();
    }).not.toThrow();
  });

  test('should render ErrorDisplay component with error message', () => {
    // Test that ErrorDisplay component renders correctly
    render(<ErrorDisplay error='Test error message' onRetry={() => {}} />);

    // Verify error message is displayed
    expect(screen.getByText('Test error message')).toBeInTheDocument();
  });

  test('should render MessageDisplay component with success message', () => {
    // Test that MessageDisplay component renders correctly
    render(
      <MessageDisplay
        messages={[
          {
            id: '1',
            message: 'Success message',
            type: 'success',
            timestamp: Date.now(),
          },
        ]}
        onRemoveMessage={() => {}}
      />
    );

    // Verify success message is displayed
    expect(screen.getByText('Success message')).toBeInTheDocument();
  });
});
