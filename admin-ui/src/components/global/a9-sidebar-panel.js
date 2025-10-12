import React from 'react';
import { Drawer, List, ListItem, ListItemIcon, ListItemText } from '@mui/material';
import { Dashboard, People, Settings, ExitToApp, Search } from '@mui/icons-material';
import { Link } from 'react-router-dom';

const menuItems = [
  { text: 'Dashboard', icon: <Dashboard />, path: '/' },
  { text: 'NLQ SQL Preview', icon: <Search />, path: '/nlq-sql-preview' },
  { text: 'Agents', icon: <People />, path: '/agents' },
  { text: 'Settings', icon: <Settings />, path: '/settings' },
  { text: 'Logout', icon: <ExitToApp />, path: '/logout' },
];

function Navigation_Sidebar() {
  return (
    <Drawer variant="permanent" anchor="left">
      <List>
        {menuItems.map((item) => (
          <ListItem button key={item.text} component={Link} to={item.path}>
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.text} />
          </ListItem>
        ))}
      </List>
    </Drawer>
  );
}

export default Navigation_Sidebar;
