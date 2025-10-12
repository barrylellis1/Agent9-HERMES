export const mockResponses = {
  situationAppraisal: {
    initial: [
      {
        text: "I see you're facing a 25% decline in Q1 sales. Let me analyze the situation...",
        type: 'situation',
        timestamp: new Date().toISOString()
      },
      {
        text: "Key findings: \n1. Price objections: Customers feel our pricing is too high\n2. Competitor issues: Competitors have been aggressive with promotions\n3. Market trends: Industry-wide slowdown in Q1",
        type: 'situation',
        timestamp: new Date().toISOString()
      }
    ]
  },
  deepAnalysis: {
    initial: [
      {
        text: "Let me dive deeper into the root causes...",
        type: 'analysis',
        timestamp: new Date().toISOString()
      },
      {
        text: "Analysis complete. Here are the key insights:\n1. Value Proposition Gap: Our pricing doesn't align with perceived value\n2. Market Position: Competitors have been positioning themselves as more cost-effective\n3. Customer Segments: Different segments have varying price sensitivity",
        type: 'analysis',
        timestamp: new Date().toISOString()
      }
    ]
  },
  solutionEvolution: {
    initial: [
      {
        text: "Let's evolve the solution. Here are some potential approaches:",
        type: 'solution',
        timestamp: new Date().toISOString()
      },
      {
        text: "1. Value-Based Pricing Strategy\n- Realign pricing with value delivered\n- Implement tiered pricing for different segments\n- Add value-added services",
        type: 'solution',
        timestamp: new Date().toISOString()
      },
      {
        text: "2. Market Differentiation\n- Highlight unique value propositions\n- Develop targeted marketing campaigns\n- Create customer success stories",
        type: 'solution',
        timestamp: new Date().toISOString()
      }
    ]
  },
  finalRecommendation: {
    initial: [
      {
        text: "Based on the analysis, here's my final recommendation:",
        type: 'recommendation',
        timestamp: new Date().toISOString()
      },
      {
        text: "1. Implement value-based pricing strategy\n- Adjust pricing tiers based on customer value\n- Add premium support packages\n- Create value-based sales training",
        type: 'recommendation',
        timestamp: new Date().toISOString()
      },
      {
        text: "2. Launch market differentiation campaign\n- Highlight unique features\n- Create segmented marketing materials\n- Develop customer success stories",
        type: 'recommendation',
        timestamp: new Date().toISOString()
      }
    ]
  }
};
