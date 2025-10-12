import React, { useMemo, useState } from 'react';
import { Card, CardHeader, CardContent, Typography, Box, Chip, Grid, Button, ToggleButtonGroup, ToggleButton, List, ListItem, Divider } from '@mui/material';
import ceoSituations from './Dashboard/__mocks__/ceo_situations.json';

// Helper: Covey quadrant and RACI filtering
const filterSituations = (situations, filter) => {
  return situations.filter(item => {
    // Assume mock data has: owner, accountable, urgency, importance, current_state
    if (filter === 'direct') return item.owner === 'You';
    if (filter === 'accountable') return item.accountable === 'You';
    if (filter === 'all') return item.owner === 'You' || item.accountable === 'You';
    return false;
  });
};

const getQuadrant = (item) => {
  if (item.urgency === 'High' && item.importance === 'High') return 'imperative';
  if (item.urgency !== 'High' && item.importance === 'High') return 'important';
  return 'other';
};

const quadrantLabel = {
  imperative: 'Urgent & Important',
  important: 'Important',
  other: 'Other'
};

const A9_covey_raci_dashboard_view = () => {
  const [filter, setFilter] = useState('direct');

  // Partition by Covey quadrant
  const filtered = useMemo(() => filterSituations(ceoSituations, filter), [filter]);
  const imperative = filtered.filter(item => getQuadrant(item) === 'imperative');
  const important = filtered.filter(item => getQuadrant(item) === 'important');
  const other = filtered.filter(item => getQuadrant(item) === 'other');

  return (
    <Box>
      <Card sx={{ mb: 3, border: '2px solid #6d4aff', background: '#f9f6ff' }}>
        <CardHeader title="Agent9 Covey/RACI Dashboard" subheader="Actions & opportunities by control and importance" />
        <CardContent>
          <Box mb={2}>
            <ToggleButtonGroup
              value={filter}
              exclusive
              onChange={(_, v) => v && setFilter(v)}
              size="small"
            >
              <ToggleButton value="direct">Direct Control</ToggleButton>
              <ToggleButton value="accountable">Accountable</ToggleButton>
              <ToggleButton value="all">All My Items</ToggleButton>
            </ToggleButtonGroup>
          </Box>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Typography variant="h6" color="error.main">Imperative (Urgent & Important)</Typography>
              <List>
                {imperative.length === 0 && (
                  <ListItem><Typography variant="body2" color="textSecondary">No imperative items.</Typography></ListItem>
                )}
                {imperative.map(item => (
                  <React.Fragment key={item.id}>
                    <ListItem alignItems="flex-start">
                      <Box>
                        <Typography variant="subtitle1" fontWeight="bold">{item.title}</Typography>
                        <Typography variant="body2" color="textSecondary">{item.description}</Typography>
                        <Box display="flex" gap={1} mt={1}>
                          <Chip label={item.urgency} color={item.urgency === 'High' ? 'error' : 'warning'} size="small" />
                          <Chip label={item.importance} color={item.importance === 'High' ? 'primary' : 'default'} size="small" />
                          <Chip label={`Owner: ${item.owner}`} size="small" />
                          <Chip label={`Accountable: ${item.accountable}`} size="small" />
                        </Box>
                      </Box>
                    </ListItem>
                    <Divider component="li" />
                  </React.Fragment>
                ))}
              </List>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="h6" color="primary.main">Important (Not Urgent)</Typography>
              <List>
                {important.length === 0 && (
                  <ListItem><Typography variant="body2" color="textSecondary">No important items.</Typography></ListItem>
                )}
                {important.map(item => (
                  <React.Fragment key={item.id}>
                    <ListItem alignItems="flex-start">
                      <Box>
                        <Typography variant="subtitle1" fontWeight="bold">{item.title}</Typography>
                        <Typography variant="body2" color="textSecondary">{item.description}</Typography>
                        <Box display="flex" gap={1} mt={1}>
                          <Chip label={item.urgency} color={item.urgency === 'High' ? 'error' : 'warning'} size="small" />
                          <Chip label={item.importance} color={item.importance === 'High' ? 'primary' : 'default'} size="small" />
                          <Chip label={`Owner: ${item.owner}`} size="small" />
                          <Chip label={`Accountable: ${item.accountable}`} size="small" />
                        </Box>
                      </Box>
                    </ListItem>
                    <Divider component="li" />
                  </React.Fragment>
                ))}
              </List>
            </Grid>
          </Grid>
          <Box mt={4}>
            <Typography variant="subtitle2" color="textSecondary">Other Items</Typography>
            <List>
              {other.length === 0 && (
                <ListItem><Typography variant="body2" color="textSecondary">No other items.</Typography></ListItem>
              )}
              {other.map(item => (
                <React.Fragment key={item.id}>
                  <ListItem alignItems="flex-start">
                    <Box>
                      <Typography variant="subtitle1" fontWeight="bold">{item.title}</Typography>
                      <Typography variant="body2" color="textSecondary">{item.description}</Typography>
                      <Box display="flex" gap={1} mt={1}>
                        <Chip label={item.urgency} color={item.urgency === 'High' ? 'error' : 'warning'} size="small" />
                        <Chip label={item.importance} color={item.importance === 'High' ? 'primary' : 'default'} size="small" />
                        <Chip label={`Owner: ${item.owner}`} size="small" />
                        <Chip label={`Accountable: ${item.accountable}`} size="small" />
                      </Box>
                    </Box>
                  </ListItem>
                  <Divider component="li" />
                </React.Fragment>
              ))}
            </List>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default A9_covey_raci_dashboard_view;
