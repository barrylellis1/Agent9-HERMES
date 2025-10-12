import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Grid,
  Button,
  Badge,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
  LinearProgress,
  Modal,
  Backdrop,
  Fade,
  Paper,
  Tooltip,
  Chip,
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  CheckCircle,
  Error,
  Info,
  Business,
  Timeline as TimelineIcon,
  Assessment,
  CompareArrows,
} from '@mui/icons-material';
import { InnovationTeam } from './agents/InnovationTeam';
import { InnovationCatalyst } from './agents/InnovationCatalyst';
import { SolutionArchitect } from './agents/SolutionArchitect';
import { ImpactAnalysisAgent } from './agents/ImpactAnalysisAgent';
import { ImplementationValidator } from './agents/ImplementationValidator';
import { UXValidator } from './agents/UXValidator';
import { MarketAnalysisAgent } from './agents/MarketAnalysisAgent';

const InnovationDashboard = () => {
  const [currentIdea, setCurrentIdea] = useState(null);
  const [ideas, setIdeas] = useState([]);
  const [agents, setAgents] = useState([]);
  const [selectedIdea, setSelectedIdea] = useState(null);
  const [showDetails, setShowDetails] = useState(false);
  const [compareIdea, setCompareIdea] = useState(null);
  const [showComparison, setShowComparison] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  // Initialize innovation team
  const innovationTeam = new InnovationTeam([
    new InnovationCatalyst(),
    new SolutionArchitect(),
    new ImpactAnalysisAgent(),
    new ImplementationValidator(),
    new UXValidator(),
    new MarketAnalysisAgent()
  ]);

  useEffect(() => {
    // Initialize agents
    const agents = [
      { name: 'Innovation Catalyst', type: 'idea', color: 'primary' },
      { name: 'Solution Architect', type: 'tech', color: 'info' },
      { name: 'Impact Analysis', type: 'business', color: 'success' },
      { name: 'Implementation', type: 'tech', color: 'warning' },
      { name: 'UX', type: 'design', color: 'error' },
      { name: 'Market', type: 'market', color: 'secondary' }
    ];
    setAgents(agents);
  }, []);

  const generateIdeas = async () => {
    try {
      const problemStatement = {
        domain: 'situation-awareness',
        context: {
          current_state: 'Current system has limited real-time monitoring capabilities',
          challenges: [
            'Delayed situation detection',
            'Limited contextual information',
            'Poor user engagement'
          ],
          requirements: [
            'Real-time updates',
            'Context-aware visualization',
            'User-friendly interface',
            'Scalable architecture'
          ],
          constraints: {
            latency: '200ms',
            throughput: '1000 req/s',
            memory: '512MB',
            budget: 50000
          }
        }
      };

      const generatedIdeas = await innovationTeam.generateIdeas(problemStatement);
      setIdeas(generatedIdeas);
      setCurrentIdea(generatedIdeas[0]);
    } catch (error) {
      console.error('Error generating ideas:', error);
    }
  };

  const calculateRiskLevel = (idea) => {
    const riskFactors = [
      idea.scoring?.riskFactors?.technical || 0,
      idea.scoring?.riskFactors?.implementation || 0,
      idea.scoring?.riskFactors?.market || 0,
      idea.scoring?.riskFactors?.business || 0,
      idea.scoring?.riskFactors?.timeline || 0
    ];
    const avgRisk = riskFactors.reduce((a, b) => a + b, 0) / riskFactors.length;
    return avgRisk;
  };

  const getRiskColor = (riskLevel) => {
    if (riskLevel < 0.3) return 'success';
    if (riskLevel < 0.6) return 'warning';
    return 'error';
  };

  const AgentOpinionCard = ({ agent, score, idea }) => {
    const riskLevel = calculateRiskLevel(idea);
    const riskColor = getRiskColor(riskLevel);

    return (
      <Card>
        <CardHeader
          title={agent.name}
          titleTypographyProps={{ variant: 'h6' }}
          sx={{
            backgroundColor: `var(--mui-palette-${agent.color}-light)`,
            color: 'common.white',
          }}
        />
        <CardContent>
          <Box sx={{ mb: 2 }}>
            <LinearProgress
              variant="determinate"
              value={score}
              color={agent.color}
            />
          </Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="subtitle2" color="text.secondary">
              Score: {score.toFixed(2)}
            </Typography>
            <Tooltip title="Risk Level">
              <Chip
                label={riskLevel.toFixed(2)}
                color={riskColor}
                size="small"
                sx={{ ml: 1 }}
              />
            </Tooltip>
          </Box>
        </CardContent>
      </Card>
    );
  };

  const IdeaComparisonDialog = ({ open, onClose, idea1, idea2 }) => {
    if (!idea1 || !idea2) return null;

    return (
      <Dialog
        open={open}
        onClose={onClose}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          Idea Comparison
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardHeader title={idea1.title} />
                <CardContent>
                  <Typography paragraph>{idea1.description}</Typography>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="h6">Scoring Breakdown</Typography>
                  <List>
                    {agents.map((agent) => (
                      <ListItem key={agent.name}>
                        <ListItemText
                          primary={agent.name}
                          secondary={`Score: ${idea1.scoring?.baseScores?.[agent.name.toLowerCase()]?.toFixed(2)}`}
                        />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardHeader title={idea2.title} />
                <CardContent>
                  <Typography paragraph>{idea2.description}</Typography>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="h6">Scoring Breakdown</Typography>
                  <List>
                    {agents.map((agent) => (
                      <ListItem key={agent.name}>
                        <ListItemText
                          primary={agent.name}
                          secondary={`Score: ${idea2.scoring?.baseScores?.[agent.name.toLowerCase()]?.toFixed(2)}`}
                        />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Close</Button>
        </DialogActions>
      </Dialog>
    );
  };

  return (
    <Box sx={{ p: 2 }}>
      <Card>
        <CardHeader
          title="Innovation Dashboard"
          action={
            <Button
              variant="contained"
              color="primary"
              onClick={generateIdeas}
              startIcon={<TrendingUp />}
            >
              Generate Ideas
            </Button>
          }
        />
        <CardContent>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Idea Generation
              </Typography>
              <Paper sx={{ p: 2 }}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Idea Title</TableCell>
                      <TableCell>Score</TableCell>
                      <TableCell>Risk</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {ideas.map((idea, index) => (
                      <TableRow key={index}>
                        <TableCell>{idea.title}</TableCell>
                        <TableCell>
                          <Badge color="success">
                            {idea.scoring?.finalScore?.toFixed(2) || 'N/A'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={calculateRiskLevel(idea).toFixed(2)}
                            color={getRiskColor(calculateRiskLevel(idea))}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <IconButton
                            color="info"
                            onClick={() => viewIdeaDetails(idea)}
                          >
                            <Info />
                          </IconButton>
                          {index > 0 && (
                            <IconButton
                              color="primary"
                              onClick={() => {
                                setCompareIdea(idea);
                                setShowComparison(true);
                              }}
                            >
                              <CompareArrows />
                            </IconButton>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </Paper>
            </Grid>

            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Current Idea Analysis
              </Typography>
              {currentIdea && (
                <Box>
                  <Typography variant="h5" gutterBottom>
                    {currentIdea.title}
                  </Typography>
                  <Typography paragraph>{currentIdea.description}</Typography>
                  <Divider sx={{ my: 2 }} />
                  
                  <Grid container spacing={2}>
                    {agents.map((agent) => (
                      <Grid item xs={12} sm={6} md={4} key={agent.name}>
                        <AgentOpinionCard
                          agent={agent}
                          score={currentIdea.scoring?.baseScores?.[agent.name.toLowerCase()] || 0}
                          idea={currentIdea}
                        />
                      </Grid>
                    ))}
                  </Grid>
                </Box>
              )}
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Modal
        aria-labelledby="transition-modal-title"
        aria-describedby="transition-modal-description"
        open={showDetails}
        onClose={closeDetails}
        closeAfterTransition
        BackdropComponent={Backdrop}
        BackdropProps={{
          timeout: 500,
        }}
      >
        <Fade in={showDetails}>
          <Box sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: isMobile ? '90%' : '80%',
            bgcolor: 'background.paper',
            border: '2px solid #000',
            boxShadow: 24,
            p: 4,
          }}>
            <Typography variant="h5" gutterBottom>
              Idea Details: {selectedIdea.title}
            </Typography>
            <Typography paragraph>{selectedIdea.description}</Typography>
            <Divider sx={{ my: 2 }} />
            
            <Typography variant="h6" gutterBottom>
              Benefits
            </Typography>
            <List>
              {selectedIdea.benefits.map((benefit, index) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    <CheckCircle color="success" />
                  </ListItemIcon>
                  <ListItemText primary={benefit} />
                </ListItem>
              ))}
            </List>

            <Divider sx={{ my: 2 }} />
            
            <Typography variant="h6" gutterBottom>
              Scoring Timeline
            </Typography>
            <Timeline>
              {agents.map((agent, index) => (
                <TimelineItem key={agent.name}>
                  <TimelineSeparator>
                    <TimelineDot color={agent.color}>
                      <Assessment />
                    </TimelineDot>
                    {index < agents.length - 1 && (
                      <TimelineConnector />
                    )}
                  </TimelineSeparator>
                  <TimelineContent>
                    <Paper elevation={3} sx={{ p: 2 }}>
                      <Typography variant="subtitle2">
                        {agent.name}
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={selectedIdea.scoring?.baseScores?.[agent.name.toLowerCase()] || 0}
                        color={agent.color}
                      />
                    </Paper>
                  </TimelineContent>
                </TimelineItem>
              ))}
            </Timeline>
          </Box>
        </Fade>
      </Modal>

      <IdeaComparisonDialog
        open={showComparison}
        onClose={() => setShowComparison(false)}
        idea1={ideas[0]}
        idea2={compareIdea}
      />
    </Box>
  );
};

export default InnovationDashboard;
