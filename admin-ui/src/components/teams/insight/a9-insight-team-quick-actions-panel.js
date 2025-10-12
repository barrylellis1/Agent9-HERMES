import React from 'react';
import { 
  Grid, 
  Paper, 
  Typography, 
  Box,
  Button,
  Avatar,
  Chip,
} from '@mui/material';
import { 
  Dashboard as DashboardIcon, 
  Analytics,
  TrendingUp,
  Settings,
  Person,
  Search,
  Help,
} from '@mui/icons-material';

const quickActions = [
  {
    icon: <DashboardIcon color="primary" />,
    label: 'Run Analysis',
    description: 'Start a new analysis task',
    onClick: () => console.log('Run Analysis'),
  },
  {
    icon: <Analytics color="secondary" />,
    label: 'View Reports',
    description: 'View recent reports and insights',
    onClick: () => console.log('View Reports'),
  },
  {
    icon: <TrendingUp color="success" />,
    label: 'Generate Solutions',
    description: 'Generate new solutions',
    onClick: () => console.log('Generate Solutions'),
  },
];

function A9_Quick_Actions_Panel() {
  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Quick Actions
      </Typography>
      <Grid container spacing={3}>
        {quickActions.map((action, index) => (
          <Grid item xs={12} sm={4} key={index}>
            <Box
              sx={{
                p: 2,
                display: 'flex',
                alignItems: 'center',
                gap: 2,
                borderRadius: 1,
                bgcolor: 'background.neutral',
                '&:hover': {
                  bgcolor: 'action.hover',
                },
              }}
            >
              <Avatar sx={{ bgcolor: 'primary.main' }}>
                {action.icon}
              </Avatar>
              <Box>
                <Typography variant="h6" gutterBottom>
                  {action.label}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {action.description}
                </Typography>
              </Box>
            </Box>
          </Grid>
        ))}
      </Grid>
    </Paper>
  );
}

export default A9_Quick_Actions_Panel;
