import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardContent, List, ListItem, Chip, Box, Typography, Divider, Tooltip } from '@mui/material';
import agentImplementations from './Dashboard/__mocks__/agent_implementations.json';

const agentColors = {
  ImplementationValidator: 'info',
  SolutionEvolutionAgent: 'success',
  UXValidator: 'error',
  MarketAnalysisAgent: 'warning',
  ImpactAnalysisAgent: 'default',
};

const statusColors = {
  'In Progress': 'info',
  'Completed': 'success',
  'User Testing': 'warning',
  'Active': 'primary',
  'Legal Review': 'secondary',
  'Awaiting Action': 'error',
};

const A9_implementation_validator_agent_implementations_feed = () => {
  const [implementations, setImplementations] = useState([]);

  useEffect(() => {
    setImplementations(agentImplementations);
  }, []);

  return (
    <Card sx={{ mt: 3, border: '2px solid #0288d1' }}>
      <CardHeader title="Agent Implementations Feed" subheader="Implementation status and owner for all agent solutions" />
      <CardContent>
        <Typography variant="caption" color="info.main">[Agent Implementations Feed is Active]</Typography>
        <List>
          {implementations.map((item) => (
            <React.Fragment key={item.id}>
              <ListItem alignItems="flex-start" divider>
                <Box sx={{ width: '100%' }}>
                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Typography variant="subtitle1" fontWeight="bold">
                      {item.implementation}
                    </Typography>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Tooltip title={item.agent} arrow>
                        <Chip label={item.agent.replace('Agent', '')} color={agentColors[item.agent] || 'default'} size="small" />
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

export default A9_implementation_validator_agent_implementations_feed;
