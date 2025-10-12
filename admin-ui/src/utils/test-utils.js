import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ThemeProvider } from '@mui/material';
import theme from '../theme';
import { BrowserRouter as Router } from 'react-router-dom';

// Custom render function with theme and router
export const customRender = (ui, { route = '/', ...renderOptions } = {}) => {
  window.history.pushState({}, 'Test page', route);
  return render(
    <Router>
      <ThemeProvider theme={theme}>
        {ui}
      </ThemeProvider>
    </Router>,
    renderOptions,
  );
};

// Add custom queries
export const userEvent = {
  click: (element) => fireEvent.click(element),
  type: (element, text) => fireEvent.input(element, { target: { value: text } }),
  select: (element, value) => fireEvent.change(element, { target: { value } }),
};

// Add custom matchers
expect.extend({
  toBeVisible(element) {
    const isVisible = element.style.display !== 'none' && element.style.visibility !== 'hidden';
    return {
      pass: isVisible,
      message: () => `Expected element to be visible but it was ${element.style.display}`,
    };
  },
});

export * from '@testing-library/react';
