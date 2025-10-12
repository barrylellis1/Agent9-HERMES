import React from 'react';
import {
  Box,
  Container,
  Grid,
  Typography,
  Card,
  CardHeader,
  CardContent,
  AppBar,
  Toolbar,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  CssBaseline,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import {
  Dashboard as DashboardIcon,
  Analytics,
  TrendingUp,
  Person,
} from '@mui/icons-material';
import InnovationDashboard from './components/InnovationDashboard';
import CeoSituationsFeed from './CeoSituationsFeed';

const drawerWidth = 240;

const teamStats = [
  {
    name: 'Insight Team',
    icon: <DashboardIcon color="primary" />,
    agents: 5,
    activeTasks: 8,
    completionRate: 85,
    status: 'Active',
  },
  {
    name: 'Clarity Team',
    icon: <Analytics color="secondary" />,
    agents: 4,
    activeTasks: 6,
    completionRate: 90,
    status: 'Active',
  },
  {
    name: 'Optima Team',
    icon: <TrendingUp color="success" />,
    agents: 3,
    activeTasks: 4,
    completionRate: 95,
    status: 'Active',
  },
];

const recentActivities = [
  {
    agent: 'DataProductAgent',
    team: 'Insight Team',
    action: 'Completed data integration task',
    time: '10 minutes ago',
    status: 'success',
  },
  {
    agent: 'SituationAppraisalAgent',
    team: 'Clarity Team',
    action: 'Started situation analysis',
    time: '30 minutes ago',
    status: 'warning',
  },
  {
    agent: 'SolutionEvolutionAgent',
    team: 'Optima Team',
    action: 'Generated new solution',
    time: '1 hour ago',
    status: 'success',
  },
];

const Dashboard = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [mobileOpen, setMobileOpen] = React.useState(false);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const drawer = (
    <div>
      <Toolbar>
        <Typography variant="h6" noWrap component="div">
          Material Admin Pro
        </Typography>
      </Toolbar>
      <List>
        <ListItem button component="a" href="/" selected>
          <ListItemIcon>
            <MenuIcon />
          </ListItemIcon>
          <ListItemText primary="Dashboard" />
        </ListItem>
      </List>
    </div>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div">
            Innovation Dashboard
          </Typography>
        </Toolbar>
      </AppBar>
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true,
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
            },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
            },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
        }}
      >
        <Toolbar />
        <Container maxWidth="xl">
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h4" gutterBottom>
                Dashboard
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Card elevation={3} sx={{ p: 2, height: '100%' }}>
                <Box display="flex" alignItems="center" gap={2}>
                  <DashboardIcon color="primary" />
                  <Box>
                    <Typography variant="h6" gutterBottom>
                      Team Statistics
                    </Typography>
                    <Typography color="textSecondary">
                      View team performance
                    </Typography>
                  </Box>
                </Box>
                <Grid container spacing={3} mt={2}>
                  {teamStats.map((team, index) => (
                    <Grid item xs={12} sm={6} md={4} key={index}>
                      <Card elevation={3} sx={{ p: 2, height: '100%' }}>
                        <Box display="flex" alignItems="center" gap={2}>
                          {team.icon}
                          <Box>
                            <Typography variant="h6" gutterBottom>
                              {team.name}
                            </Typography>
                            <Typography color="textSecondary">
                              {team.agents} Agents
                            </Typography>
                            <Typography color="textSecondary">
                              {team.activeTasks} Active Tasks
                            </Typography>
                            <Box sx={{ mt: 2 }}>
                              <Typography variant="caption">Completion Rate</Typography>
                              <LinearProgress
                                variant="determinate"
                                value={team.completionRate}
                                sx={{
                                  height: 10,
                                  borderRadius: 2,
                                  bgcolor: 'background.neutral',
                                }}
                              />
                            </Box>
                          </Box>
                        </Box>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={8}>
              <Card>
                <CardHeader
                  title="Quick Actions"
                  subheader="Common tasks"
                />
                <CardContent>
                  <List>
                    <ListItem button>
                      <ListItemIcon>
                        <DashboardIcon color="primary" />
                      </ListItemIcon>
                      <ListItemText primary="Run Analysis" />
                    </ListItem>
                    <ListItem button>
                      <ListItemIcon>
                        <Analytics color="secondary" />
                      </ListItemIcon>
                      <ListItemText primary="View Reports" />
                    </ListItem>
                    <ListItem button>
                      <ListItemIcon>
                        <TrendingUp color="success" />
                      </ListItemIcon>
                      <ListItemText primary="Generate Solutions" />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>
              <Card mt={3}>
                <CardHeader
                  title="Recent Activities"
                  subheader="Latest agent activities"
                />
                <CardContent>
                  <List>
                    {recentActivities.map((activity, index) => (
                      <ListItem key={index}>
                        <Avatar>
                          <Person />
                        </Avatar>
                        <ListItemText
                          primary={activity.agent}
                          secondary={activity.action}
                        />
                        <Box sx={{ ml: 'auto', display: 'flex', alignItems: 'center' }}>
                          <Chip
                            label={activity.time}
                            size="small"
                            color={activity.status}
                          />
                        </Box>
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12}>
              <Card>
                <CardHeader title="Innovation Dashboard" />
                <CardContent>
                  <InnovationDashboard />
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12}>
              <CeoSituationsFeed />
            </Grid>
          </Grid>
        </Container>
      </Box>
    </Box>
  );
};

export default Dashboard;
