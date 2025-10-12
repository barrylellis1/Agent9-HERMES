import React from 'react';
import { AppBar, Toolbar, Typography, Box, IconButton } from '@mui/material';
import { Menu, Notifications, Search } from '@mui/icons-material';
import { Link } from 'react-router-dom';

function Navigation_Topbar() {
  return (
    <AppBar position="fixed">
      <Toolbar>
        <IconButton edge="start" color="inherit" aria-label="menu">
          <Menu />
        </IconButton>
        <Typography variant="h6" component={Link} to="/" sx={{ flexGrow: 1, textDecoration: 'none', color: 'inherit' }}>
          Agent9
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <IconButton color="inherit">
            <Search />
          </IconButton>
          <IconButton color="inherit">
            <Notifications />
          </IconButton>
        </Box>
      </Toolbar>
    </AppBar>
  );
}

export default Navigation_Topbar;
