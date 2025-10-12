import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Button, TextField } from '@mui/material';

describe('Material-UI Components', () => {
  test('renders Button with proper role', () => {
    render(<Button onClick={() => {}}>Click me</Button>);
    
    const button = screen.getByRole('button', { name: /click me/i });
    expect(button).toBeInTheDocument();
    expect(button).toHaveTextContent('Click me');
  });

  test('handles Button click event', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Submit</Button>);
    
    const button = screen.getByRole('button', { name: /submit/i });
    fireEvent.click(button);
    
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  test('renders TextField with proper role', () => {
    render(<TextField label="Name" placeholder="Enter your name" />);
    
    const input = screen.getByRole('textbox');
    expect(input).toBeInTheDocument();
    
    const label = screen.getByText('Name');
    expect(label).toBeInTheDocument();
  });

  test('handles TextField input', () => {
    render(<TextField label="Email" placeholder="Enter your email" />);
    
    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'test@example.com' } });
    
    expect(input).toHaveValue('test@example.com');
  });
});
