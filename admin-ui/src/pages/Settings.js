import React from 'react';
import { 
  Grid, 
  Paper, 
  Typography, 
  Box,
  Card,
  CardContent,
  CardHeader,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Switch,
  FormControlLabel,
  FormGroup,
  TextField,
  Slider,
  Select,
  MenuItem,
  Button,
  Chip,
  Alert,
  Divider,
} from '@mui/material';
import { 
  Brightness4 as DarkModeIcon,
  Brightness7 as LightModeIcon,
  Notifications,
  Analytics,
  TrendingUp,
  Person,
} from '@mui/icons-material';

function Settings_Page() {
  const [theme, setTheme] = React.useState('light');
  const [notifications, setNotifications] = React.useState(true);
  const [analytics, setAnalytics] = React.useState(true);
  const [agentResponseTime, setAgentResponseTime] = React.useState(2);
  const [agentPriority, setAgentPriority] = React.useState('normal');

  const handleThemeChange = (event) => {
    setTheme(event.target.value);
  };

  const handleResponseTimeChange = (event, newValue) => {
    setAgentResponseTime(newValue);
  };

  const agentPriorities = [
    { value: 'low', label: 'Low' },
    { value: 'normal', label: 'Normal' },
    { value: 'high', label: 'High' },
  ];

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader
              title="General Settings"
              subheader="Basic application settings"
            />
            <CardContent>
              <FormGroup>
                <FormControlLabel
                  control={
                    <Switch
                      checked={notifications}
                      onChange={(e) => setNotifications(e.target.checked)}
                    />
                  }
                  label="Enable Notifications"
                  labelPlacement="end"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={analytics}
                      onChange={(e) => setAnalytics(e.target.checked)}
                    />
                  }
                  label="Enable Analytics"
                  labelPlacement="end"
                />
              </FormGroup>
              
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle1" gutterBottom>
                  Theme
                </Typography>
                <FormControlLabel
                  control={
                    <Switch
                      checked={theme === 'dark'}
                      onChange={(e) => setTheme(e.target.checked ? 'dark' : 'light')}
                    />
                  }
                  label={theme === 'dark' ? 'Dark Mode' : 'Light Mode'}
                  labelPlacement="end"
                />
              </Box>
            </CardContent>
          </Card>

          <Card sx={{ mt: 3 }}>
            <CardHeader
              title="Agent Settings"
              subheader="Configure agent behavior"
            />
            <CardContent>
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle1" gutterBottom>
                  Agent Response Time
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Typography variant="body2" sx={{ mr: 2 }}>
                    {agentResponseTime}s
                  </Typography>
                  <Slider
                    value={agentResponseTime}
                    onChange={handleResponseTimeChange}
                    min={1}
                    max={10}
                    step={1}
                    marks
                    valueLabelDisplay="auto"
                  />
                </Box>
              </Box>

              <Box>
                <Typography variant="subtitle1" gutterBottom>
                  Agent Priority
                </Typography>
                <Select
                  value={agentPriority}
                  onChange={(e) => setAgentPriority(e.target.value)}
                  fullWidth
                  sx={{ mb: 2 }}
                >
                  {agentPriorities.map((priority) => (
                    <MenuItem key={priority.value} value={priority.value}>
                      {priority.label}
                    </MenuItem>
                  ))}
                </Select>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader
              title="Team Management"
              subheader="Configure agent teams"
            />
            <CardContent>
              <List>
                <ListItem>
                  <ListItemIcon>
                    <Person />
                  </ListItemIcon>
                  <ListItemText
                    primary="Team Members"
                    secondary="Manage team members and permissions"
                  />
                  <Button variant="outlined" size="small">
                    Manage
                  </Button>
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Analytics />
                  </ListItemIcon>
                  <ListItemText
                    primary="Team Analytics"
                    secondary="View team performance metrics"
                  />
                  <Button variant="outlined" size="small">
                    View
                  </Button>
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <TrendingUp />
                  </ListItemIcon>
                  <ListItemText
                    primary="Team Goals"
                    secondary="Set and track team objectives"
                  />
                  <Button variant="outlined" size="small">
                    Set Goals
                  </Button>
                </ListItem>
              </List>
            </CardContent>
          </Card>

          <Card sx={{ mt: 3 }}>
            <CardHeader
              title="System Information"
              subheader="Application version and status"
            />
            <CardContent>
              <Box sx={{ mb: 2 }}>
                <Chip
                  label="Version 1.0.0"
                  color="primary"
                  sx={{ mr: 2 }}
                />
                <Chip
                  label="Status: Running"
                  color="success"
                />
              </Box>
              <Alert severity="info">
                Last system update: 10 minutes ago
              </Alert>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Settings_Page;
