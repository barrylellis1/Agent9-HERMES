export class InnovationTeam {
  constructor(agents) {
    this.agents = agents;
  }

  async generateIdeas(problemStatement) {
    const ideas = [];
    for (const agent of this.agents) {
      const agentIdeas = await agent.generateIdeas(problemStatement);
      ideas.push(...agentIdeas);
    }
    return ideas;
  }
}
