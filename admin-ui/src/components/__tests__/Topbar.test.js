import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import Topbar from '../Topbar';

// Mock Material-UI components
jest.mock('@mui/material', () => ({
  AppBar: ({ children }) => <div>{children}</div>,
  Toolbar: ({ children }) => <div>{children}</div>,
  Typography: ({ children }) => <span>{children}</span>,
  IconButton: ({ children }) => <button>{children}</button>,
  Badge: ({ children }) => <span>{children}</span>,
  Menu: ({ children }) => <div>{children}</div>,
  MenuItem: ({ children }) => <div>{children}</div>
}));

// Mock icons
jest.mock('@mui/icons-material', () => ({
  Menu: () => <span>Menu</span>,
  Notifications: () => <span>Notifications</span>,
  AccountCircle: () => <span>Account</span>
}));

describe('Topbar', () => {
  test('renders with basic structure', () => {
    render(<Topbar />);

    // Check for app bar
    const appBar = screen.getByRole('banner');
    expect(appBar).toBeInTheDocument();

    // Check for title
    expect(screen.getByText('Material Admin Pro')).toBeInTheDocument();

    // Check for menu button
    const menuButton = screen.getByRole('button', { name: /menu/i });
    expect(menuButton).toBeInTheDocument();

    // Check for notification button
    const notificationButton = screen.getByRole('button', { name: /notifications/i });
    expect(notificationButton).toBeInTheDocument();

    // Check for user menu button
    const userMenuButton = screen.getByRole('button', { name: /account/i });
    expect(userMenuButton).toBeInTheDocument();
  });

  test('handles menu button click', () => {
    const { getByRole } = render(<Topbar />);
    const menuButton = getByRole('button', { name: /menu/i });

    fireEvent.click(menuButton);

    // Check if menu is opened
    expect(screen.getByRole('menu')).toBeInTheDocument();
  });

  test('handles user menu click', () => {
    const { getByRole } = render(<Topbar />);
    const userMenuButton = getByRole('button', { name: /account/i });

    fireEvent.click(userMenuButton);

    // Check if user menu is opened
    expect(screen.getByRole('menu')).toBeInTheDocument();
  });

  test('renders notifications badge', () => {
    render(<Topbar />);

    // Check for notifications badge
    const notifications = screen.getByRole('button', { name: /notifications/i });
    expect(notifications).toContainElement(screen.getByRole('badge'));
  });
});
