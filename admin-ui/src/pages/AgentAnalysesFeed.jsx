import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardContent, List, ListItem, Chip, Box, Typography, Divider, Tooltip } from '@mui/material';
import agentSituations from './Dashboard/__mocks__/agent_situations.json';

const agentColors = {
  DataProductAgent: 'primary',
  SituationAppraisalAgent: 'secondary',
  SolutionEvolutionAgent: 'success',
  MarketAnalysisAgent: 'warning',
  ImplementationValidator: 'info',
  UXValidator: 'error',
  ImpactAnalysisAgent: 'default',
};

const A9_agent_analyses_feed = () => {
  const [analyses, setAnalyses] = useState([]);

  useEffect(() => {
    setAnalyses(agentSituations);
  }, []);

  return (
    <Card sx={{ mt: 3, border: '2px solid #388e3c' }}>
      <CardHeader title="Agent Analyses Feed" subheader="Deep analysis results from all agents" />
      <CardContent>
        <Typography variant="caption" color="success.main">[Agent Analyses Feed is Active]</Typography>
        <List>
          {analyses.map((item) => (
            <React.Fragment key={item.id}>
              <ListItem alignItems="flex-start" divider>
                <Box sx={{ width: '100%' }}>
                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Typography variant="subtitle1" fontWeight="bold">
                      {item.title}
                    </Typography>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Tooltip title={item.agent} arrow>
                        <Chip label={item.agent.replace('Agent', '')} color={agentColors[item.agent] || 'default'} size="small" />
                      </Tooltip>
                      {item.current_state && (
                        <Chip label={item.current_state} color="info" size="small" />
                      )}
                    </Box>
                  </Box>
                  <Typography variant="body2" color="textSecondary" sx={{ mb: 0.5 }}>
                    {item.analysis}
                  </Typography>
                  <Box display="flex" flexWrap="wrap" gap={1} sx={{ my: 1 }}>
                    {item.metrics && Object.entries(item.metrics).map(([key, value]) => (
                      <Chip key={key} label={`${key}: ${value}`} size="small" variant="outlined" />
                    ))}
                  </Box>
                  {item.anomalies && item.anomalies.length > 0 && (
                    <Box sx={{ mt: 0.5 }}>
                      <Typography variant="caption" color="error">Anomalies:</Typography>
                      {item.anomalies.map((anomaly, idx) => (
                        <Chip key={idx} label={`${anomaly.type}: ${anomaly.detail}`} color="error" size="small" sx={{ ml: 1 }} />
                      ))}
                    </Box>
                  )}
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

export default A9_agent_analyses_feed;
