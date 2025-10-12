import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardContent, List, ListItem, ListItemText, Chip, Box, Typography } from '@mui/material';

// Import the mock CEO situations data
import ceoSituations from './__mocks__/ceo_situations.json';

const CeoSituationsFeed = () => {
  // DEBUG: Log the imported data
  console.log('CeoSituationsFeed loaded. ceoSituations:', ceoSituations);
  const [situations, setSituations] = useState([]);

  useEffect(() => {
    setSituations(ceoSituations);
  }, []);

  return (
    <Card sx={{ mt: 3, border: '2px solid red' }}>
      <CardHeader title="CEO Situational Insights (DEBUG MARKER)" subheader="Executive-level situations and recommendations" />
      <CardContent>
        <Typography variant="caption" color="error">[DEBUG: CeoSituationsFeed rendered]</Typography>
        <List>
          {situations.map((situation) => (
            <ListItem key={situation.id} alignItems="flex-start" divider>
              <Box sx={{ width: '100%' }}>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="subtitle1" fontWeight="bold">
                    {situation.title}
                  </Typography>
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

export default CeoSituationsFeed;
