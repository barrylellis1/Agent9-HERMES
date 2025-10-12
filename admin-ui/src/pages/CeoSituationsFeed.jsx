import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardContent, List, ListItem, Chip, Box, Typography } from '@mui/material';
import ceoSituations from './Dashboard/__mocks__/ceo_situations.json';

const A9_innovation_catalyst_ceo_situations_feed = () => {
  const [situations, setSituations] = useState([]);

  useEffect(() => {
    setSituations(ceoSituations);
  }, []);

  return (
    <Card sx={{ mt: 3, border: '2px solid #1976d2' }}>
      <CardHeader title="CEO Situational Insights" subheader="Executive-level situations and recommendations" />
      <CardContent>
        <Typography variant="caption" color="primary">[CEO Situations Feed is Active]</Typography>
        <List>
          {situations.map((situation) => (
            <ListItem key={situation.id} alignItems="flex-start" divider>
              <Box sx={{ width: '100%' }}>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="subtitle1" fontWeight="bold">
                      {situation.title}
                    </Typography>
                    {situation.current_state && (
                      <Chip label={situation.current_state} color="info" size="small" />
                    )}
                  </Box>
                  <Chip label={situation.urgency} color={situation.urgency === 'High' ? 'error' : situation.urgency === 'Medium' ? 'warning' : 'default'} size="small" />
                </Box>
                <Typography variant="body2" color="textSecondary" sx={{ mb: 0.5 }}>
                  {situation.description}
                </Typography>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="caption" color="primary">
                    Value: ${situation.business_value.toLocaleString()}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    {new Date(situation.timestamp).toLocaleDateString()}
                  </Typography>
                </Box>
                <Typography variant="body2" sx={{ mt: 0.5 }}>
                  <strong>Recommendation:</strong> {situation.recommendation}
                </Typography>
              </Box>
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
};

export default A9_innovation_catalyst_ceo_situations_feed;
