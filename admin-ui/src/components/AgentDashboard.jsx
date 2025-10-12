import React, { useEffect, useState } from 'react';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Grid from '@mui/material/Grid';
import CircularProgress from '@mui/material/CircularProgress';

const STATE_COLORS = {
  idle: 'success',
  processing: 'info',
  waiting: 'warning',
  error: 'error'
};

const AGENT_API_URL = 'http://localhost:8000/agents/state';

function AgentDashboard() {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStates = async () => {
      setLoading(true);
      try {
        const res = await fetch(AGENT_API_URL);
        const data = await res.json();
        setAgents(data);
      } catch (err) {
        setAgents([]);
      }
      setLoading(false);
    };
    fetchStates();
    const interval = setInterval(fetchStates, 3000); // Poll every 3s
    return () => clearInterval(interval);
  }, []);

  if (loading) return <CircularProgress />;

  return (
    <Grid container spacing={2}>
      {agents.map(agent => (
        <Grid key={agent.name} size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="h6">{agent.name}</Typography>
              <Chip
                label={agent.state.toUpperCase()}
                color={STATE_COLORS[agent.state] || 'default'}
                style={{ marginTop: 8, marginBottom: 8 }}
              />
              <Typography variant="body2" color="textSecondary">
                Last activity: {agent.last_activity}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
}

export default AgentDashboard;
