export class UXValidator {
  async generateIdeas(problemStatement) {
    return [
      {
        title: 'User-Centric Interface Design',
        description: 'Design an intuitive and user-friendly interface for situation awareness',
        benefits: [
          'Improved user experience',
          'Better user engagement',
          'Reduced training time'
        ],
        scoring: {
          baseScores: {
            'innovation_catalyst': 80,
            'solution_architect': 85,
            'impact_analysis': 85,
            'implementation': 80,
            'ux': 95,
            'market': 90
          },
          riskFactors: {
            technical: 20,
            implementation: 25,
            market: 15,
            business: 10,
            timeline: 20
          }
        }
      }
    ];
  }
}
