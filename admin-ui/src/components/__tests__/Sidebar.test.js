import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import Sidebar from '../Sidebar';

// Mock Material-UI components
jest.mock('@mui/material', () => ({
  Drawer: ({ children }) => <div role="complementary">{children}</div>,
  List: ({ children }) => <ul role="list">{children}</ul>,
  ListItem: ({ children, button }) => (
    <li role="listitem" tabIndex={button ? 0 : undefined}>{children}</li>
  ),
  ListItemIcon: ({ children }) => <span role="img">{children}</span>,
  ListItemText: ({ primary }) => <span>{primary}</span>
}));

// Mock icons
jest.mock('@mui/icons-material', () => ({
  Dashboard: () => <span>Dashboard Icon</span>,
  People: () => <span>People Icon</span>,
  Settings: () => <span>Settings Icon</span>,
  ExitToApp: () => <span>Logout Icon</span>
}));

// Mock React Router
jest.mock('react-router-dom', () => ({
  Link: ({ children, to }) => (
    <a href={to} role="link">{children}</a>
  )
}));

describe('Sidebar Component', () => {
  test('renders with proper structure', () => {
    render(<Sidebar />);

    // Check for drawer with proper role
    const drawer = screen.getByRole('complementary');
    expect(drawer).toBeInTheDocument();

    // Check for navigation list
    const navList = screen.getByRole('list');
    expect(navList).toBeInTheDocument();

    // Check for navigation items
    const navItems = screen.getAllByRole('listitem');
    expect(navItems).toHaveLength(4);
  });

  test('renders navigation items with proper labels', () => {
    render(<Sidebar />);

    // Check for each navigation item
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Agents')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
    expect(screen.getByText('Logout')).toBeInTheDocument();

    // Check for icons
    expect(screen.getByText('Dashboard Icon')).toBeInTheDocument();
    expect(screen.getByText('People Icon')).toBeInTheDocument();
    expect(screen.getByText('Settings Icon')).toBeInTheDocument();
    expect(screen.getByText('Logout Icon')).toBeInTheDocument();
  });

  test('navigation items are focusable and clickable', () => {
    render(<Sidebar />);

    // Check if items are focusable
    const navItems = screen.getAllByRole('listitem');
    navItems.forEach(item => {
      expect(item).toHaveAttribute('tabIndex', '0');
    });

    // Check if items are clickable links
    const links = screen.getAllByRole('link');
    expect(links).toHaveLength(4);

    // Check if clicking works
    const dashboardLink = screen.getByRole('link', { name: /dashboard/i });
    fireEvent.click(dashboardLink);
    expect(dashboardLink).toHaveAttribute('href', '/');
  });
});
