import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardContent, List, ListItem, Chip, Box, Typography, Divider, Tooltip } from '@mui/material';
import agentSolutions from './Dashboard/__mocks__/agent_solutions.json';

const agentColors = {
  SolutionEvolutionAgent: 'success',
  ImplementationValidator: 'info',
  UXValidator: 'error',
  MarketAnalysisAgent: 'warning',
  ImpactAnalysisAgent: 'default',
};

const stageColors = {
  'Selected': 'success',
  'Evaluated': 'info',
  'Proposed': 'warning',
  'Under Review': 'secondary',
};

const A9_solution_evolution_agent_solutions_feed = () => {
  const [solutions, setSolutions] = useState([]);

  useEffect(() => {
    setSolutions(agentSolutions);
  }, []);

  return (
    <Card sx={{ mt: 3, border: '2px solid #fbc02d' }}>
      <CardHeader title="Agent Solutions Feed" subheader="Proposed and selected solutions from all agents" />
      <CardContent>
        <Typography variant="caption" color="warning.main">[Agent Solutions Feed is Active]</Typography>
        <List>
          {solutions.map((item) => (
            <React.Fragment key={item.id}>
              <ListItem alignItems="flex-start" divider>
                <Box sx={{ width: '100%' }}>
                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Typography variant="subtitle1" fontWeight="bold">
                      {item.solution}
                    </Typography>
                    <Tooltip title={item.agent} arrow>
                      <Chip label={item.agent.replace('Agent', '')} color={agentColors[item.agent] || 'default'} size="small" />
                    </Tooltip>
                    <Chip label={item.stage || item.current_state} color="info" size="small" />
                  </Box>
                  <Typography variant="body2" color="textSecondary" sx={{ mb: 0.5 }}>
                    {item.rationale}
                  </Typography>
                  <Box display="flex" flexWrap="wrap" gap={1} sx={{ my: 1 }}>
                    <Chip label={item.stage} color={stageColors[item.stage] || 'default'} size="small" />
                    {item.selected && <Chip label="Selected" color="success" size="small" />}
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

export default A9_solution_evolution_agent_solutions_feed;
