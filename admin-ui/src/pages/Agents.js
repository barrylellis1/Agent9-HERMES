import React from 'react';
import { 
  Grid, 
  Paper, 
  Typography, 
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  IconButton,
  Tooltip,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import { 
  People,
  Person,
  Add,
  Edit,
  Delete,
  Info,
  TrendingUp,
  TrendingDown,
} from '@mui/icons-material';

function Agents_Page_Page() {
  const [open, setOpen] = React.useState(false);
  const [selectedAgent, setSelectedAgent] = React.useState(null);

  const agentTeams = [
    {
      name: 'Insight Team',
      description: 'Data integration and analytics',
      icon: <TrendingUp color="primary" />,
      agents: [
        { 
          name: 'DataProductAgent', 
          status: 'Active',
          type: 'Data Integration',
          lastActivity: '10 minutes ago',
          tasks: 8,
          successRate: 95,
        },
        { 
          name: 'DataIntegrationAgent', 
          status: 'Active',
          type: 'Data Processing',
          lastActivity: '30 minutes ago',
          tasks: 6,
          successRate: 90,
        },
      ]
    },
    {
      name: 'Clarity Team',
      description: 'Situation appraisal and analysis',
      icon: <TrendingUp color="secondary" />,
      agents: [
        { 
          name: 'SituationAppraisalAgent', 
          status: 'Active',
          type: 'Analysis',
          lastActivity: '1 hour ago',
          tasks: 4,
          successRate: 92,
        },
        { 
          name: 'DeepAnalysisAgent', 
          status: 'Active',
          type: 'Analysis',
          lastActivity: '2 hours ago',
          tasks: 3,
          successRate: 98,
        },
      ]
    },
    {
      name: 'Optima Team',
      description: 'Solution evolution and debate',
      icon: <TrendingUp color="success" />,
      agents: [
        { 
          name: 'SolutionEvolutionAgent', 
          status: 'Active',
          type: 'Solution Generation',
          lastActivity: '3 hours ago',
          tasks: 5,
          successRate: 97,
        },
        { 
          name: 'TradeoffAnalysisAgent', 
          status: 'Active',
          type: 'Analysis',
          lastActivity: '4 hours ago',
          tasks: 2,
          successRate: 99,
        },
      ]
    }
  ];

  const handleOpen = (agent) => {
    setSelectedAgent(agent);
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Agent Management
      </Typography>

      <Grid container spacing={3}>
        {agentTeams.map((team, teamIndex) => (
          <Grid item xs={12} key={teamIndex}>
            <Paper elevation={3} sx={{ p: 3, mb: 2 }}>
              <Box display="flex" alignItems="center" gap={2} mb={3}>
                {team.icon}
                <Box>
                  <Typography variant="h6">
                    {team.name}
                  </Typography>
                  <Typography color="textSecondary">
                    {team.description}
                  </Typography>
                </Box>
              </Box>

              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Agent</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Last Activity</TableCell>
                      <TableCell>Tasks</TableCell>
                      <TableCell>Success Rate</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {team.agents.map((agent, agentIndex) => (
                      <TableRow key={agentIndex}>
                        <TableCell>{agent.name}</TableCell>
                        <TableCell>{agent.type}</TableCell>
                        <TableCell>
                          <Chip
                            label={agent.status}
                            color={agent.status === 'Active' ? 'success' : 'error'}
                          />
                        </TableCell>
                        <TableCell>{agent.lastActivity}</TableCell>
                        <TableCell>{agent.tasks} active</TableCell>
                        <TableCell>
                          <Chip
                            label={`${agent.successRate}%`}
                            color={agent.successRate >= 90 ? 'success' : 'warning'}
                          />
                        </TableCell>
                        <TableCell>
                          <Box display="flex" gap={1}>
                            <Tooltip title="View Details">
                              <IconButton onClick={() => handleOpen(agent)}>
                                <Info />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Edit">
                              <IconButton>
                                <Edit />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Delete">
                              <IconButton>
                                <Delete />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>

              <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
                <Button
                  variant="contained"
                  startIcon={<Add />}
                  onClick={() => handleOpen(null)}
                >
                  Add Agent
                </Button>
              </Box>
            </Paper>
          </Grid>
        ))}
      </Grid>

      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>
          {selectedAgent ? `Edit ${selectedAgent.name}` : 'Add New Agent'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <TextField
              fullWidth
              label="Agent Name"
              variant="outlined"
              defaultValue={selectedAgent?.name}
              sx={{ mb: 2 }}
            />
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Type</InputLabel>
              <Select defaultValue={selectedAgent?.type}>
                <MenuItem value="Data Integration">Data Integration</MenuItem>
                <MenuItem value="Analysis">Analysis</MenuItem>
                <MenuItem value="Solution Generation">Solution Generation</MenuItem>
              </Select>
            </FormControl>
            <TextField
              fullWidth
              label="Description"
              multiline
              rows={4}
              defaultValue={selectedAgent?.description}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button variant="contained" onClick={handleClose}>
            {selectedAgent ? 'Update' : 'Add'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default Agents_Page;
