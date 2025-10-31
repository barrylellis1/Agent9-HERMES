import React, { useState } from 'react';
import AgentDashboard from '../components/AgentDashboard';
import A9_innovation_catalyst_ceo_situations_feed from './CeoSituationsFeed';
import A9_kpi_summary_feed from './A9_kpi_summary_feed';
import A9_ceo_agent_status_overview from './A9_ceo_agent_status_overview';
import A9_covey_raci_dashboard_view from './A9_covey_raci_dashboard_view';
import A9_agent_analyses_feed from './AgentAnalysesFeed';
import A9_solution_evolution_agent_solutions_feed from './A9_solution_evolution_agent_solutions_feed';
import A9_implementation_validator_agent_implementations_feed from './A9_implementation_validator_agent_implementations_feed';
import A9_change_management_agent_feed from './A9_change_management_agent_feed';
import { 
  Grid, 
  Box,
  Typography,
  Card,
  CardContent,
  CardHeader,
} from '@mui/material';
import A9_Team_Stats_Panel from '../components/A9_Team_Stats_Panel';
import A9_Activity_Timeline from '../components/A9_Activity_Timeline';
import A9_Quick_Actions_Panel from '../components/A9_Quick_Actions_Panel';

const teamStats = [
  {
    name: 'Insight',
    description: 'Data integration and analytics',
    stats: {
      agents: 5,
      activeTasks: 8,
      completionRate: 85,
    }
  },
  {
    name: 'Clarity',
    description: 'Situation appraisal and analysis',
    stats: {
      agents: 4,
      activeTasks: 6,
      completionRate: 90,
    }
  },
  {
    name: 'Optima',
    description: 'Solution evolution and debate',
    stats: {
      agents: 3,
      activeTasks: 4,
      completionRate: 95,
    }
  },
];

const recentActivities = [
  {
    agent: 'DataProductAgent',
    team: 'Insight',
    action: 'Completed data integration task',
    time: '10 minutes ago',
    status: 'success',
    type: 'agent'
  },
  {
    agent: 'SituationAppraisalAgent',
    team: 'Clarity',
    action: 'Started situation analysis',
    time: '30 minutes ago',
    status: 'warning',
    type: 'analysis'
  },
  {
    agent: 'SolutionEvolutionAgent',
    team: 'Optima',
    action: 'Generated new solution',
    time: '1 hour ago',
    status: 'success',
    type: 'solution'
  },
];


function A9_Dashboard_Page() {
  const [coveyView, setCoveyView] = useState(false);
  return (
    <Box sx={{ p: 3 }}>
      <Box display="flex" justifyContent="flex-end" mb={2}>
        <button
          style={{ padding: '8px 16px', borderRadius: 4, border: '1px solid #6d4aff', background: coveyView ? '#f9f6ff' : '#6d4aff', color: coveyView ? '#6d4aff' : '#fff', cursor: 'pointer' }}
          onClick={() => setCoveyView(v => !v)}
        >
          {coveyView ? 'Show Classic Dashboard' : 'Show Covey/RACI View'}
        </button>
      </Box>
      {coveyView ? (
        <A9_covey_raci_dashboard_view />
      ) : (
        <>
          <Typography variant="h4" gutterBottom>
            Dashboard
          </Typography>

          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 8 }}>
          <Card>
            <CardHeader
              title="Team Overview"
              subheader="Current status of all agent teams"
            />
            <CardContent>
              <Grid container spacing={3}>
                {teamStats.map((team, index) => (
                  <Grid key={index} size={{ xs: 12, sm: 6, md: 4 }}>
                    <A9_Team_Stats_Panel team={team} stats={team.stats} />
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 4 }}>
          <A9_Quick_Actions_Panel />
        </Grid>
      </Grid>

      <Grid container spacing={3} mt={4}>
        <Grid size={12}>
          <Card>
            <CardContent>
              <Typography variant="h5" style={{marginBottom: 16}}>Agent Status Overview</Typography>
              <AgentDashboard />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3} mt={4}>
        <Grid size={12}>
          <A9_ceo_agent_status_overview />
        </Grid>
      </Grid>

      <Grid container spacing={3} mt={4}>
        <Grid size={12}>
          <A9_innovation_catalyst_ceo_situations_feed />
        </Grid>
      </Grid>

      <Grid container spacing={3} mt={4}>
        <Grid size={12}>
          <A9_agent_analyses_feed />
        </Grid>
      </Grid>

      <Grid container spacing={3} mt={4}>
        <Grid size={12}>
          <A9_solution_evolution_agent_solutions_feed />
        </Grid>
      </Grid>

      <Grid container spacing={3} mt={4}>
        <Grid size={12}>
          <A9_implementation_validator_agent_implementations_feed />
        </Grid>
      </Grid>

      <Grid container spacing={3} mt={4}>
        <Grid size={12}>
          <A9_change_management_agent_feed />
        </Grid>
      </Grid>

      <Grid container spacing={3} mt={4}>
        <Grid size={12}>
          <A9_Activity_Timeline activities={recentActivities} />
        </Grid>
      </Grid>
        </>
      )}
    </Box>
  );
}

export default A9_Dashboard_Page;
