import { CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import AgentDashboard from './components/AgentDashboard.jsx';
import Dashboard from './pages/Dashboard.jsx';
import NLQSqlPreview from './pages/NLQSqlPreview.jsx';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <div className="App">
          <h2 style={{ margin: '24px 0' }}>Agent Status Overview</h2>
          <AgentDashboard />
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/nlq-sql-preview" element={<NLQSqlPreview />} />
            <Route path="/*" element={<Dashboard />} />
          </Routes>
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;
