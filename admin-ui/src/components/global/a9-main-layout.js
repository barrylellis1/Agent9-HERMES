import React from 'react';
import { ThemeProvider, CssBaseline, Box } from '@mui/material';
import theme from '../theme';
import Sidebar from '../components/Sidebar';
import Topbar from '../components/Topbar';

function Main_Layout({ children }) {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', minHeight: '100vh' }}>
        <Sidebar />
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            p: 3,
            width: { sm: `calc(100% - 240px)` },
            marginLeft: { sm: 240 },
            position: 'relative',
            top: 64,
          }}
        >
          {children}
        </Box>
      </Box>
      <Topbar sx={{ position: 'fixed', top: 0, left: 0, right: 0, zIndex: 1000 }} />
    </ThemeProvider>
  );
}

export default Main_Layout;
