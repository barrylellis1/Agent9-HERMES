import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

describe('Basic Test', () => {
  test('renders simple component', () => {
    const TestComponent = () => (
      <div>
        <h1>Test Component</h1>
        <p>This is a test component</p>
      </div>
    );

    render(<TestComponent />);
    expect(screen.getByText('Test Component')).toBeInTheDocument();
    expect(screen.getByText('This is a test component')).toBeInTheDocument();
  });
});
