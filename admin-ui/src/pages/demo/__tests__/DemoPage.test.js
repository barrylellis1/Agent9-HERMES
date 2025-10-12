import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import DemoPage from '../DemoPage';

describe('Demo Page', () => {
  test('renders basic structure', () => {
    render(<DemoPage />);

    // Check for main headings
    expect(screen.getByText('Agent9 Demo')).toBeInTheDocument();
    expect(screen.getByText('Chat Interface')).toBeInTheDocument();
    expect(screen.getByText('Agent Orchestration')).toBeInTheDocument();

    // Check for layout containers
    const mainContainer = screen.getByRole('main');
    expect(mainContainer).toBeInTheDocument();

    const chatContainer = screen.getByRole('region', { name: /chat interface/i });
    expect(chatContainer).toBeInTheDocument();

    const orchestrationContainer = screen.getByRole('region', { name: /agent orchestration/i });
    expect(orchestrationContainer).toBeInTheDocument();
  });
});
