import React, { useState } from 'react';
import { Box, Button, TextField, Typography, Paper, CircularProgress } from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';

// NOTE: This version uses a mock NLQ-to-params mapping for demonstration.
const MOCK_NLQ_MAP = {
  'Show total revenue by customer for 2024': {
    product_id: 'dp_fi_20250516_001',
    columns: 'customerid,value',
    groupby: 'customer',
    filter: 'year:2024',
  },
  'Show profit by gl_account': {
    product_id: 'dp_fi_20250516_001',
    columns: 'gl_account,value',
    groupby: 'gl_account',
  },
};

const MCP_API_BASE = (typeof process !== 'undefined' && process.env && process.env.REACT_APP_MCP_API_BASE)
  ? process.env.REACT_APP_MCP_API_BASE
  : 'http://127.0.0.1:8000';

const NLQSqlPreview = () => {
  const [nlq, setNlq] = useState('');
  const [sql, setSql] = useState('');
  const [params, setParams] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handlePreviewSql = async () => {
    setError('');
    setSql('');
    setParams(null);
    setLoading(true);
    try {
      const mapped = MOCK_NLQ_MAP[nlq.trim()];
      if (!mapped) {
        setError('No mapping found for this NLQ. Try a supported example.');
        setLoading(false);
        return;
      }
      const query = [];
      if (mapped.columns) query.push(`columns=${encodeURIComponent(mapped.columns)}`);
      if (mapped.groupby) query.push(`groupby=${encodeURIComponent(mapped.groupby)}`);
      if (mapped.filter) query.push(`filter=${encodeURIComponent(mapped.filter)}`);
      const url = `${MCP_API_BASE}/data-product/${mapped.product_id}/generate-sql${query.length ? '?' + query.join('&') : ''}`;
      const resp = await fetch(url);
      if (!resp.ok) {
        throw new Error(`Server error: ${resp.status}`);
      }
      const data = await resp.json();
      setSql(data.sql || '');
      setParams(data.builder_params || null);
    } catch (err) {
      setError(err.message || 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ maxWidth: 700, mx: 'auto', mt: 5 }}>
      <Typography variant="h5" gutterBottom>
        <SearchIcon sx={{ verticalAlign: 'middle', mr: 1 }} /> NLQ to SQL Preview
      </Typography>
      <TextField
        label="Natural Language Query"
        fullWidth
        value={nlq}
        onChange={e => setNlq(e.target.value)}
        placeholder="e.g. Show total revenue by customer for 2024"
        sx={{ mb: 2 }}
      />
      <Button variant="contained" onClick={handlePreviewSql} disabled={loading || !nlq.trim()}>
        Preview SQL
      </Button>
      {loading && <CircularProgress size={28} sx={{ ml: 2 }} />}
      {error && (
        <Typography color="error" sx={{ mt: 2 }}>{error}</Typography>
      )}
      {sql && (
        <Paper sx={{ mt: 4, p: 2, background: '#f5f5f5' }}>
          <Typography variant="subtitle1">Generated SQL:</Typography>
          <Box component="pre" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', fontSize: 14 }}>
            {sql}
          </Box>
          {params && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2">Builder Params:</Typography>
              <Box component="pre" sx={{ fontSize: 13, color: '#555' }}>{JSON.stringify(params, null, 2)}</Box>
            </Box>
          )}
        </Paper>
      )}
      <Box sx={{ mt: 3 }}>
        <Typography variant="body2" color="text.secondary">
          <b>Supported NLQ examples for demo:</b>
          <ul style={{ marginTop: 4 }}>
            <li>Show total revenue by customer for 2024</li>
            <li>Show profit by gl_account</li>
          </ul>
        </Typography>
      </Box>
    </Box>
  );
};

export default NLQSqlPreview;
