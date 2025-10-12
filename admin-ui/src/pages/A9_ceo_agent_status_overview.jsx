import React, { useMemo } from 'react';
import { Card, CardHeader, CardContent, Typography, Box, Chip, List, ListItem, Divider } from '@mui/material';
import ceoSituations from './Dashboard/__mocks__/ceo_situations.json';

// Helper: Identify escalations/blockers (e.g., high urgency, "Awaiting Action")
const getEscalations = (situations) => {
  return situations.filter(item =>
    (item.urgency === 'High' || item.current_state === 'Awaiting Action')
  );
};

const getStatusHeadline = (escalations, total) => {
  if (escalations.length === 0) {
    return {
      headline: `Agent9 is actively managing ${total} situations. No escalations at this time.`,
      color: 'success',
      emoji: '✅'
    };
  } else {
    return {
      headline: `Agent9: ${escalations.length} urgent situation${escalations.length > 1 ? 's' : ''} require${escalations.length > 1 ? '' : 's'} CEO review.`,
      color: 'error',
      emoji: '⚠️'
    };
  }
};

const A9_ceo_agent_status_overview = () => {
  const escalations = useMemo(() => getEscalations(ceoSituations), []);
  const status = useMemo(() => getStatusHeadline(escalations, ceoSituations.length), [escalations]);

  return (
    <Card sx={{ mb: 3, border: '2px solid #1976d2', background: '#f5faff' }}>
      <CardHeader title="Agent9 Status Overview" subheader="Principal-centric, escalation-focused" />
      <CardContent>
        <Box display="flex" alignItems="center" gap={2}>
          <Typography variant="h6" color={status.color + '.main'}>
            {status.emoji} {status.headline}
          </Typography>
        </Box>
        {escalations.length > 0 && (
          <List sx={{ mt: 2 }}>
            {escalations.slice(0, 3).map(item => (
              <React.Fragment key={item.id}>
                <ListItem alignItems="flex-start">
                  <Box>
                    <Typography variant="subtitle1" fontWeight="bold">
                      {item.title}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      {item.description}
                    </Typography>
                    <Box display="flex" gap={1} mt={1}>
                      <Chip label={item.urgency} color={item.urgency === 'High' ? 'error' : item.urgency === 'Medium' ? 'warning' : 'default'} size="small" />
                      <Chip label={item.current_state} color="info" size="small" />
                    </Box>
                  </Box>
                </ListItem>
                <Divider component="li" />
              </React.Fragment>
            ))}
            {escalations.length > 3 && (
              <ListItem>
                <Typography variant="caption" color="textSecondary">
                  ...and {escalations.length - 3} more urgent situations.
                </Typography>
              </ListItem>
            )}
          </List>
        )}
      </CardContent>
    </Card>
  );
};

export default A9_ceo_agent_status_overview;
