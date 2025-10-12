import React, { useMemo } from 'react';
import { Card, CardHeader, CardContent, Grid, Typography, Box, Chip } from '@mui/material';
import ceoSituations from './Dashboard/__mocks__/ceo_situations.json';

const getTotals = (situations) => {
  let totalRevenueOpportunities = 0;
  let totalCostReductionOpportunities = 0;
  let totalBusinessValue = 0;
  let opportunityCount = 0;
  let costReductionCount = 0;
  let managedCount = situations.length;

  situations.forEach((item) => {
    totalBusinessValue += item.business_value || 0;
    // Heuristic: Opportunities with "Opportunity" or "Growth" in title
    if (/opportunity|growth/i.test(item.title)) {
      totalRevenueOpportunities += item.business_value || 0;
      opportunityCount++;
    }
    // Heuristic: Cost reduction if recommendation or title mentions "cost", "efficiency", "reduction"
    if (/cost|efficien|reduction|review/i.test(item.recommendation || '') || /cost|efficien|reduction|review/i.test(item.title)) {
      totalCostReductionOpportunities += item.business_value || 0;
      costReductionCount++;
    }
  });

  return {
    managedCount,
    totalBusinessValue,
    totalRevenueOpportunities,
    opportunityCount,
    totalCostReductionOpportunities,
    costReductionCount,
  };
};

const A9_kpi_summary_feed = () => {
  const totals = useMemo(() => getTotals(ceoSituations), []);

  return (
    <Card sx={{ mb: 3, border: '2px solid #43a047', background: '#f9fff9' }}>
      <CardHeader title="Agent9 KPI Summary" subheader="Totals managed by Agent9 (demo)" />
      <CardContent>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={4}>
            <Box>
              <Typography variant="h6" color="primary">Total Situations Managed</Typography>
              <Typography variant="h4" fontWeight="bold">{totals.managedCount}</Typography>
            </Box>
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <Box>
              <Typography variant="h6" color="success.main">Total Revenue Opportunities</Typography>
              <Typography variant="h4" fontWeight="bold">${totals.totalRevenueOpportunities.toLocaleString()}</Typography>
              <Chip label={`${totals.opportunityCount} identified`} color="success" size="small" sx={{ mt: 1 }} />
            </Box>
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <Box>
              <Typography variant="h6" color="error.main">Total Cost Reduction Opportunities</Typography>
              <Typography variant="h4" fontWeight="bold">${totals.totalCostReductionOpportunities.toLocaleString()}</Typography>
              <Chip label={`${totals.costReductionCount} identified`} color="error" size="small" sx={{ mt: 1 }} />
            </Box>
          </Grid>
        </Grid>
        <Box mt={3}>
          <Typography variant="subtitle2" color="textSecondary">
            Total Business Value Managed: <b>${totals.totalBusinessValue.toLocaleString()}</b>
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default A9_kpi_summary_feed;
