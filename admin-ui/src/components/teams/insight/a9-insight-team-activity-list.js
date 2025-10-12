import React from 'react';
import { 
  List, 
  ListItem, 
  ListItemAvatar, 
  ListItemText, 
  Avatar,
  Chip,
  Box,
  Typography,
  IconButton,
} from '@mui/material';
import { 
  Person, 
  Analytics, 
  TrendingUp, 
  MoreVert,
} from '@mui/icons-material';

const activityIcons = {
  agent: <Person />,
  analysis: <Analytics />,
  solution: <TrendingUp />,
};

function A9_Activity_Timeline({ activities }) {
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Recent Activities
      </Typography>
      <List>
        {activities.map((activity, index) => (
          <ListItem
            key={index}
            secondaryAction={
              <IconButton edge="end" aria-label="more">
                <MoreVert />
              </IconButton>
            }
          >
            <ListItemAvatar>
              <Avatar>
                {activityIcons[activity.type]}
              </Avatar>
            </ListItemAvatar>
            <ListItemText
              primary={activity.agent}
              secondary={
                <React.Fragment>
                  <Typography
                    component="span"
                    variant="body2"
                    color="text.primary"
                  >
                    {activity.action}
                  </Typography>
                  <Box sx={{ mt: 1 }}>
                    <Chip
                      label={activity.time}
                      size="small"
                      color={activity.status}
                    />
                  </Box>
                </React.Fragment>
              }
            />
          </ListItem>
        ))}
      </List>
    </Box>
  );
}

export default A9_Activity_Timeline;
