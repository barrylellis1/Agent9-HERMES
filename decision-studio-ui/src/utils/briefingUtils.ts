export const buildExecutiveBriefing = (situation: any, analysis: any, sol: any) => {
    const kpiName = situation?.kpi_name || analysis?.kpi_name || sol?.problem_reframe?.situation || 'KPI'
    const topOptions = Array.isArray(sol?.options_ranked) ? sol.options_ranked : []

    const urgency = situation?.severity ? String(situation.severity) : 'High Priority'
    
    // Build comprehensive executive summary
    const executiveSummaryParts: string[] = []
    if (sol?.problem_reframe?.situation) executiveSummaryParts.push(String(sol.problem_reframe.situation))
    if (sol?.problem_reframe?.complication) executiveSummaryParts.push(String(sol.problem_reframe.complication))
    if (sol?.problem_reframe?.question) executiveSummaryParts.push(`Key Question: ${String(sol.problem_reframe.question)}`)
    if (sol?.recommendation?.title) executiveSummaryParts.push(`Recommended Action: ${sol.recommendation.title}`)
    const executiveSummary = executiveSummaryParts.filter(Boolean).join("\n\n") || `A variance was detected in ${kpiName}. Review the options and approve a response.`

    // Extract variance percentage for financial impact (unused currently)
    // const varianceMatch = situation?.description?.match(/(\d+\.?\d*)%/)
    // const variancePct = varianceMatch ? varianceMatch[1] + '%' : null
    
    // Derive time sensitivity from severity
    const timeSensitivityMap: Record<string, string> = {
      'critical': 'Immediate (24-48 hrs)',
      'high': 'Urgent (1 week)',
      'medium': 'Standard (2-4 weeks)',
      'low': 'Monitor'
    }
    const timeSensitivity = timeSensitivityMap[situation?.severity?.toLowerCase()] || 'Review Required'
    
    // Calculate confidence from analysis completeness
    const hasChangePoints = analysis?.change_points?.length > 0
    const hasKtAnalysis = analysis?.kt_is_is_not?.where_is?.length > 0
    const hasSolutions = topOptions.length > 0
    const confidenceScore = [hasChangePoints, hasKtAnalysis, hasSolutions].filter(Boolean).length
    const confidenceMap = ['Low', 'Medium', 'High', 'Very High']
    const confidence = confidenceMap[confidenceScore] || 'Medium'
    
    // Decision deadline based on severity
    const deadlineMap: Record<string, string> = {
      'critical': 'End of Day',
      'high': 'This Week',
      'medium': 'This Month',
      'low': 'Next Quarter'
    }
    const decisionDeadline = deadlineMap[situation?.severity?.toLowerCase()] || 'TBD'

    // Format snake_case dimension names to human-readable Title Case
    const formatDimLabel = (dim: string): string =>
      String(dim || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())

    // Format a delta value at the appropriate scale (no unit assumption)
    const formatDelta = (delta: number | undefined | null): string => {
      if (delta == null || delta === 0) return 'Significant'
      const abs = Math.abs(delta)
      const sign = delta > 0 ? '+' : ''
      if (abs >= 1_000_000) return `${sign}${(delta / 1_000_000).toFixed(1)}M`
      if (abs >= 1_000)     return `${sign}${(delta / 1_000).toFixed(1)}K`
      return `${sign}${delta.toFixed(2)}`
    }

    // Extract root causes from Deep Analysis
    const rootCauses: any[] = []
    const whereIs = analysis?.kt_is_is_not?.where_is || []
    whereIs.slice(0, 5).forEach((item: any) => {
      if (item?.dimension && item?.key) {
        rootCauses.push({
          driver: `${formatDimLabel(item.dimension)}: ${item.key}`,
          evidence: item?.text || `Current: ${item?.current?.toLocaleString() || 'N/A'}`,
          impact: `Δ ${formatDelta(item?.delta)}`
        })
      }
    })

    // Map risk level from option scores
    const riskLevelMap = (risk: number) => {
      if (risk >= 0.7) return 'High'
      if (risk >= 0.4) return 'Medium'
      return 'Low'
    }
    
    // Map investment effort from cost score (qualitative — avoids fake dollar amounts)
    const investmentMap = (cost: number) => {
      if (cost >= 0.7) return 'High Effort'
      if (cost >= 0.4) return 'Moderate Effort'
      return 'Low Effort'
    }

    // Map impact potential from impact score (qualitative — avoids fake % projections)
    const roiMap = (impact: number) => {
      if (impact >= 0.7) return 'High Impact Potential'
      if (impact >= 0.4) return 'Moderate Impact Potential'
      return 'Incremental Impact'
    }

    const options = topOptions.slice(0, 3).map((opt: any, idx: number) => ({
      title: opt?.title || 'Option',
      subtitle: opt?.time_to_value ? `Time to value: ${opt.time_to_value}` : 'Operational intervention',
      description: opt?.description || opt?.rationale || '',
      roi: roiMap(opt?.expected_impact || 0.5),
      investment: investmentMap(opt?.cost || 0.5),
      timeline: opt?.time_to_value || '3-6 months',
      riskLevel: riskLevelMap(opt?.risk || 0.5),
      reversibility: opt?.reversibility || 'medium',
      recommended: idx === 0 || ((sol?.recommendation?.id && opt?.id) ? sol.recommendation.id === opt.id : false),
      prosDetailed: Array.isArray(opt?.perspectives?.[0]?.arguments_for)
        ? opt.perspectives[0].arguments_for.slice(0, 3).map((p: string) => ({ point: p, detail: '' }))
        : [],
      consDetailed: Array.isArray(opt?.perspectives?.[0]?.arguments_against)
        ? opt.perspectives[0].arguments_against.slice(0, 3).map((c: string) => ({ point: c, detail: '' }))
        : [],
      perspectives: Array.isArray(opt?.perspectives)
        ? opt.perspectives.slice(0, 3).map((p: any) => ({ role: p?.lens || 'Perspective', view: (p?.key_questions || []).join(' ') }))
        : [],
      prerequisites: opt?.prerequisites || [],
      implementation_triggers: opt?.implementation_triggers || [],
    }))

    // CRITICAL: Use situation.description as authoritative source for title, NOT LLM's problem_reframe
    // The LLM may hallucinate the wrong direction (e.g., "increased" when it actually "decreased")
    const title = situation?.description 
      ? `Decision Briefing: ${String(situation.description)}`
      : (sol?.problem_reframe?.situation 
          ? `Decision Briefing: ${String(sol.problem_reframe.situation)}`
          : `Decision Briefing: ${kpiName}`)

    // Build implementation roadmap from recommended option
    const roadmap: any[] = []
    if (options[0]?.prerequisites?.length > 0) {
      roadmap.push({ phase: 'Phase 1: Prerequisites', items: options[0].prerequisites, timeline: 'Week 1-2' })
    }
    if (options[0]?.implementation_triggers?.length > 0) {
      roadmap.push({ phase: 'Phase 2: Implementation', items: options[0].implementation_triggers, timeline: 'Week 3-8' })
    }
    roadmap.push({ phase: 'Phase 3: Monitor & Adjust', items: ['Track KPI recovery', 'Weekly progress reviews', 'Adjust tactics as needed'], timeline: 'Ongoing' })

    // Build risk matrix from blind spots and tensions
    const risks: any[] = []
    sol?.blind_spots?.slice(0, 3).forEach((bs: string) => {
      risks.push({ risk: bs, likelihood: 'Medium', impact: 'Medium', mitigation: 'Monitor and reassess quarterly' })
    })
    sol?.unresolved_tensions?.slice(0, 2).forEach((t: any) => {
      risks.push({ risk: t?.tension || 'Strategic tension', likelihood: 'High', impact: 'High', mitigation: t?.requires || 'Stakeholder alignment needed' })
    })

    const transformed = {
      title,
      urgency,
      metrics: {
        financialImpact: situation?.description || `${kpiName} variance detected`,
        timeSensitivity,
        confidence,
        decisionDeadline,
      },
      executiveSummary,
      situation: {
        currentState: situation?.description || `Context for ${kpiName}.`,
        problem: sol?.problem_reframe?.complication || `Variance detected in ${kpiName}.`,
        rootCauses,
        keyQuestion: sol?.problem_reframe?.question || null,
        assumptions: sol?.problem_reframe?.key_assumptions || [],
      },
      options,
      roadmap,
      risks,
      recommendation: {
        headline: sol?.recommendation?.title 
          ? `Proceed with: ${sol.recommendation.title}` 
          : (options[0]?.title ? `Proceed with: ${options[0].title}` : 'Review options and approve next steps'),
        rationale: sol?.recommendation_rationale || options[0]?.description || '',
        nextSteps: Array.isArray(sol?.next_steps) && sol.next_steps.length > 0 
          ? sol.next_steps 
          : ['Review and approve recommended option', 'Assign implementation owner', 'Schedule kickoff meeting'],
        decisionOwner: 'Finance Leadership',
        deadline: decisionDeadline,
      },
      // Hybrid Council artifacts - 3-stage debate
      stage_1_hypotheses: sol?.stage_1_hypotheses || null,
      cross_review: sol?.cross_review || null,
      blind_spots: sol?.blind_spots || [],
      unresolved_tensions: sol?.unresolved_tensions || [],
    }
    
    return transformed
  }
