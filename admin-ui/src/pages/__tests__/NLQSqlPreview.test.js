import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import NLQSqlPreview from '../NLQSqlPreview';

// Mock fetch for backend API
beforeEach(() => {
  global.fetch = jest.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve({
        sql: 'SELECT customerid, value FROM ... WHERE year = 2024 GROUP BY customer',
        builder_params: {
          select_fields: ['customerid', 'value'],
          group_by_fields: ['customer'],
          filters: ['year = 2024']
        }
      }),
    })
  );
});

afterEach(() => {
  jest.resetAllMocks();
});

test('shows SQL output for supported NLQ', async () => {
  render(<NLQSqlPreview />);
  const input = screen.getByLabelText(/natural language query/i);

  // Simulate user typing NLQ
  fireEvent.change(input, { target: { value: 'Show total revenue by customer for 2024' } });

  // Click the Preview SQL button
  fireEvent.click(screen.getByText(/preview sql/i));

  // Wait for SQL output to appear
  await waitFor(() => {
    expect(screen.getByText(/generated sql/i)).toBeInTheDocument();
    expect(screen.getByText(/SELECT customerid, value/i)).toBeInTheDocument();
    expect(screen.getByText(/builder params/i)).toBeInTheDocument();
    expect(screen.getAllByText(/customerid/i).length).toBeGreaterThan(0);
  });
});
