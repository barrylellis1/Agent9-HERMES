import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  useTheme
} from '@mui/material';
import ChatInterface from './ChatInterface';
import { mockResponses } from './mockResponses';

const DemoPage = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const theme = useTheme();

  const handleContinue = () => {
    setIsLoading(true);
    // Simulate agent response delay
    setTimeout(() => {
      setCurrentStep(prev => prev + 1);
      setIsLoading(false);
    }, 1500);
  };

  const handleSendEmail = () => {
    setIsLoading(true);
    // Simulate email sending
    setTimeout(() => {
      setIsLoading(false);
      // In a real implementation, this would send an email
      console.log('Email sent');
    }, 2000);
  };

  const handleMessageSent = (message) => {
    setIsLoading(true);
    // Simulate agent response
    setTimeout(() => {
      setIsLoading(false);
      // Add agent response based on current step
      setCurrentStep(prev => prev + 1);
    }, 1500);
  };

  return (
    <Box sx={{ p: 3 }} role="main">
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Agent9 Demo
        </Typography>
        <Typography variant="body1" color="textSecondary">
          Interact with Agent9's multi-agent system through this chat interface.
        </Typography>
      </Paper>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2, height: '100%' }} role="region" aria-label="Chat Interface">
            <ChatInterface
              onContinue={handleContinue}
              onSendEmail={handleSendEmail}
              onMessageSent={handleMessageSent}
            />
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, height: '100%' }} role="region" aria-label="Agent Orchestration">
            <Typography variant="h6" gutterBottom>
              Agent Orchestration
            </Typography>
            <Typography variant="body1" color="textSecondary">
              This area will show agent debate and solution visualization.
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default DemoPage;
