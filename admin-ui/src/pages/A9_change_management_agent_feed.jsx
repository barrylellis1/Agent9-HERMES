import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardContent, List, ListItem, Chip, Box, Typography, Divider, Tooltip } from '@mui/material';
import agentChangeManagement from './Dashboard/__mocks__/agent_change_management.json';

const statusColors = {
  'Awaiting Action': 'error',
  'In Process': 'info',
  'Completed': 'success',
  'Scheduled': 'warning',
  'Pending': 'secondary',
};

const A9_change_management_agent_feed = () => {
  const [changeTasks, setChangeTasks] = useState([]);

  useEffect(() => {
    setChangeTasks(agentChangeManagement);
  }, []);

  return (
    <Card sx={{ mt: 3, border: '2px solid #8e24aa' }}>
      <CardHeader title="Change Management Feed" subheader="Change management tasks and status by agent" />
      <CardContent>
        <Typography variant="caption" color="secondary.main">[Change Management Feed is Active]</Typography>
        <List>
          {changeTasks.map((item) => (
            <React.Fragment key={item.id}>
              <ListItem alignItems="flex-start" divider>
                <Box sx={{ width: '100%' }}>
                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Typography variant="subtitle1" fontWeight="bold">
                      {item.change_task}
                    </Typography>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Tooltip title={item.agent} arrow>
                        <Chip label={item.agent.replace('Agent', '')} color="secondary" size="small" />
                      </Tooltip>
                      <Chip label={item.current_state} color={statusColors[item.current_state] || 'default'} size="small" />
                    </Box>
                  </Box>
                  <Typography variant="body2" color="textSecondary" sx={{ mb: 0.5 }}>
                    Owner: {item.owner}
                  </Typography>
                  <Box display="flex" flexWrap="wrap" gap={1} sx={{ my: 1 }}>
                    <Chip label={item.status} color={statusColors[item.status] || 'default'} size="small" />
                  </Box>
                  <Typography variant="caption" color="textSecondary" sx={{ float: 'right' }}>
                    {new Date(item.timestamp).toLocaleDateString()}
                  </Typography>
                </Box>
              </ListItem>
              <Divider component="li" />
            </React.Fragment>
          ))}
        </List>
      </CardContent>
    </Card>
  );
};

export default A9_change_management_agent_feed;
