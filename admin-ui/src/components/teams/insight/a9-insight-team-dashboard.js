import React from 'react';
import { 
  Card, 
  CardContent, 
  CardHeader, 
  Box, 
  Typography, 
  LinearProgress, 
  Avatar,
  Chip,
} from '@mui/material';
import { TrendingUp, Analytics, Person } from '@mui/icons-material';

const teamIcons = {
  Insight: <TrendingUp color="primary" />,
  Clarity: <Analytics color="secondary" />,
  Optima: <Person color="success" />,
};

function A9_Team_Stats_Panel({ team, stats }) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardHeader
        avatar={teamIcons[team.name]}
        title={team.name}
        subheader={team.description}
      />
      <CardContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Avatar sx={{ bgcolor: 'primary.main' }}>
              <Person />
            </Avatar>
            <Typography variant="h6">
              {stats.agents} Agents
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Avatar sx={{ bgcolor: 'secondary.main' }}>
              <Analytics />
            </Avatar>
            <Typography variant="h6">
              {stats.activeTasks} Active Tasks
            </Typography>
          </Box>
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" gutterBottom>
              Completion Rate
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <LinearProgress
                variant="determinate"
                value={stats.completionRate}
                sx={{
                  height: 10,
                  borderRadius: 2,
                  bgcolor: 'background.neutral',
                  flex: 1,
                }}
              />
              <Chip
                label={`${stats.completionRate}%`}
                color={stats.completionRate >= 90 ? 'success' : 'warning'}
                size="small"
              />
            </Box>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}

export default A9_Team_Stats_Panel;
