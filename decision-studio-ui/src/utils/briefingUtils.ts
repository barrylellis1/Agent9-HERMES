export const buildExecutiveBriefing = (situation: any, analysis: any, sol: any) => {
    const kpiName = situation?.kpi_name || analysis?.kpi_name || sol?.problem_reframe?.situation || 'KPI'
    const kpiUnit: string = situation?.kpi_value?.unit || ''
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
        // Build clean evidence string from structured fields; avoid raw snake_case item.text
        const currVal = item?.current ?? item?.current_value
        const prevVal = item?.previous ?? item?.previous_value
        const evidenceStr = currVal != null
          ? `Current: ${formatDelta(currVal)}${prevVal != null ? ` | Prior: ${formatDelta(prevVal)}` : ''}`
          : (item?.text
              ? String(item.text).replace(/^[a-z][a-z0-9_]*:\s*/i, '').trim()
              : 'N/A')
        rootCauses.push({
          driver: String(item.key),
          dimension: formatDimLabel(item.dimension),
          evidence: evidenceStr,
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
      return 'Strategic (Long Horizon)'
    }

    // Format impact_estimate from LLM into a display string
    // Falls back to qualitative roiMap label if LLM did not populate impact_estimate
    const formatImpactEstimate = (opt: any, optIdx: number = 0): string => {
      const ie = opt?.impact_estimate
      if (ie && typeof ie === 'object') {
        const rawUnit = ie.unit || kpiUnit || ''
        // Percentage KPIs recover in percentage points (pp), not raw %
        const displayUnit = rawUnit === '%' ? 'pp' : rawUnit
        const low = ie.recovery_range?.low
        const high = ie.recovery_range?.high
        if (low != null && high != null && (low !== 0 || high !== 0)) {
          const fmt = (v: number) => {
            const abs = Math.abs(v)
            const sign = v > 0 ? '+' : ''
            if (rawUnit === '$') {
              if (abs >= 1_000_000) return `${sign}$${(v / 1_000_000).toFixed(1)}M`
              if (abs >= 1_000)     return `${sign}$${(v / 1_000).toFixed(0)}K`
              return `${sign}$${v.toFixed(0)}`
            }
            return `${sign}${v.toFixed(1)}${displayUnit}`
          }
          return `${fmt(low)} to ${fmt(high)}`
        }
      }
      // Last-resort fallback: attempt rough estimate from primary root cause delta
      try {
        const primaryImpact = rootCauses[0]?.impact  // e.g., "Δ -30.6" or "Δ +1.5K"
        if (primaryImpact) {
          const numMatch = primaryImpact.match(/Δ\s*([+-]?\d+\.?\d*)([KMkm]?)/)
          if (numMatch) {
            const raw = parseFloat(numMatch[1])
            const scale = numMatch[2].toUpperCase()
            const multiplier = scale === 'M' ? 1_000_000 : scale === 'K' ? 1_000 : 1
            const delta = Math.abs(raw * multiplier)
            if (delta > 0) {
              // Different recovery fractions per option tier (opt_1 is fastest/partial, opt_3 is strategic/lower near-term)
              const fractionsByTier = [[0.3, 0.5], [0.45, 0.7], [0.2, 0.35]]
              const [lowFrac, highFrac] = fractionsByTier[Math.min(optIdx, 2)]
              const low = delta * lowFrac
              const high = delta * highFrac
              const fallbackUnit = kpiUnit === '%' ? 'pp' : kpiUnit === '$' ? '' : kpiUnit
              const fmtNum = (v: number) => {
                if (kpiUnit === '$') return v >= 1_000_000 ? `$${(v/1_000_000).toFixed(1)}M` : v >= 1_000 ? `$${(v/1_000).toFixed(0)}K` : `$${v.toFixed(0)}`
                return v >= 1_000_000 ? `${(v/1_000_000).toFixed(1)}M${fallbackUnit}` : v >= 1_000 ? `${(v/1_000).toFixed(0)}K${fallbackUnit}` : `${v.toFixed(1)}${fallbackUnit}`
              }
              return `~+${fmtNum(low)} to +${fmtNum(high)} (est.)`
            }
          }
        }
      } catch { /* ignore parse errors */ }
      return roiMap(opt?.expected_impact || 0.5)
    }

    const options = topOptions.slice(0, 3).map((opt: any, idx: number) => ({
      title: opt?.title || 'Option',
      subtitle: opt?.time_to_value ? `Time to value: ${opt.time_to_value}` : 'Operational intervention',
      description: opt?.description || opt?.rationale || '',
      roi: formatImpactEstimate(opt, idx),
      impactBasis: opt?.impact_estimate?.basis || null,
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

    const buildTitle = (): string => {
      // Prefer LLM problem_reframe.situation — written for humans, not machines
      if (sol?.problem_reframe?.situation) {
        const rawSit = String(sol.problem_reframe.situation)
        const sentence = (rawSit.match(/^[^.]*(?:\.\d[^.]*)*(?=\.\s+[A-Z]|$)/)?.[0] ?? rawSit).trim()
        if (sentence.length >= 20) {
          const capped = sentence.length > 90
            ? sentence.substring(0, 87).replace(/\s+\S*$/, '') + '...'
            : sentence
          return `Decision Briefing: ${capped}`
        }
      }
      // Fallback: clean the raw situation.description
      if (situation?.description) {
        const cleaned = String(situation.description)
          .replace(/\s*\(threshold=\w+\)/gi, '')
          .replace(/\s+/g, ' ')
          .trim()
        return `Decision Briefing: ${cleaned}`
      }
      return `Decision Briefing: ${kpiName}`
    }
    const title = buildTitle()

    // Build implementation roadmap from recommended option
    const roadmap: any[] = []
    if (options[0]?.prerequisites?.length > 0) {
      roadmap.push({ phase: 'Phase 1: Prerequisites', items: options[0].prerequisites, timeline: 'Week 1-2' })
    }
    // Phase 2: derive implementation steps from the option itself (not escalation triggers)
    if (options[0]) {
      const phase2Items: string[] = [
        options[0]?.title
          ? `Execute primary intervention: ${options[0].title}`
          : 'Activate primary intervention per approved plan',
        options[0]?.description
          ? (() => {
              const s = (String(options[0].description).match(/^[^.]*(?:\.\d[^.]*)*(?=\.\s+[A-Z]|$)/)?.[0] ?? String(options[0].description)).trim()
              return s.length > 250 ? s.substring(0, 247).replace(/\s+\S*$/, '') + '...' : s
            })()
          : 'Implement the approved operational changes',
        `Brief all stakeholders and assign task owners by name`,
        `Week 4 checkpoint: compare early actuals against expected recovery trajectory`,
      ]
      roadmap.push({ phase: 'Phase 2: Implementation', items: phase2Items, timeline: 'Week 3-8' })
    }
    const monitorItems = [
      `Finance Controller to track ${kpiName} recovery weekly — target: restore to prior baseline`,
      options[0]?.implementation_triggers?.[0]
        ? `Escalation trigger: ${options[0].implementation_triggers[0]}`
        : `Escalate to leadership if no improvement by day 30`,
      `Monthly executive review: compare actuals vs. expected recovery range`,
      `At 90 days: assess whether to proceed with secondary option based on results`,
    ]
    roadmap.push({ phase: 'Phase 3: Monitor & Adjust', items: monitorItems, timeline: 'Ongoing' })

    // Build risk matrix from blind spots and tensions
    const risks: any[] = []
    sol?.blind_spots?.slice(0, 3).forEach((bs: string) => {
      const bsText = String(bs).toLowerCase()
      const mitigation = /data|information|unknown|unclear|unavailable/i.test(bsText)
        ? `Commission targeted analysis to close this information gap before implementation`
        : /timing|sequence|when|order|before/i.test(bsText)
        ? `Build a decision gate at Week 4 to validate timing assumptions before proceeding`
        : /competitor|market|external|pricing/i.test(bsText)
        ? `Conduct competitive pricing benchmarking (assign to strategy team, Week 1-2)`
        : `Add to implementation risk register; review at each phase gate`
      risks.push({ risk: bs, likelihood: 'Medium', impact: 'Medium', mitigation })
    })
    sol?.unresolved_tensions?.slice(0, 2).forEach((t: any) => {
      risks.push({ risk: t?.tension || 'Strategic tension', likelihood: 'High', impact: 'High', mitigation: t?.requires || 'Stakeholder alignment needed' })
    })

    // Aggregate next steps from all available sources for a rich Section 6
    const aggregatedNextSteps: string[] = []
    // 1. LLM-generated next_steps (filter out generic boilerplate)
    if (Array.isArray(sol?.next_steps) && sol.next_steps.length > 0) {
      sol.next_steps.forEach((s: string) => {
        const lower = (s || '').toLowerCase()
        const isBoilerplate = ['review and approve', 'assign implementation owner', 'schedule kickoff'].some(g => lower.includes(g))
        if (s && !isBoilerplate) aggregatedNextSteps.push(s)
      })
    }
    // 2. Option prerequisites as concrete first actions
    if (options[0]?.prerequisites?.length > 0) {
      options[0].prerequisites.slice(0, 2).forEach((p: string) => {
        const alreadyIncluded = aggregatedNextSteps.some(s => s.includes(String(p).substring(0, 30)))
        if (!alreadyIncluded) aggregatedNextSteps.push(`Complete prerequisite: ${p}`)
      })
    }
    // 3. KPI-specific tracking step
    aggregatedNextSteps.push(`Assign ${kpiName} recovery tracking to Finance team with weekly reporting starting immediately`)
    // 4. Implementation trigger as escalation watchpoint
    if (options[0]?.implementation_triggers?.[0]) {
      aggregatedNextSteps.push(`Monitor escalation trigger: ${options[0].implementation_triggers[0]}`)
    }
    // 5. Leadership reporting
    aggregatedNextSteps.push(`Report initial results at next leadership review — decision owner accountable for progress`)
    // Final: ensure minimum 4, maximum 6
    const nextSteps = aggregatedNextSteps.length >= 4
      ? aggregatedNextSteps.slice(0, 6)
      : [
          options[0]?.prerequisites?.[0]
            ? `Complete prerequisite: ${options[0].prerequisites[0]}`
            : `Assign implementation owner for "${options[0]?.title || 'recommended option'}"`,
          `Establish ${kpiName} recovery target and weekly tracking cadence with Finance team`,
          `Schedule executive kick-off within 48 hours to confirm resource allocation`,
          `Report initial progress at next leadership review`,
        ]

    const rawRationale = sol?.recommendation_rationale || options[0]?.description || ''
    const isBoilerplateRationale = /options generated via/i.test(rawRationale) || /based on our analysis/i.test(rawRationale) || rawRationale.trim().length < 30
    const rationale = isBoilerplateRationale
      ? `${options[0]?.title || 'The recommended action'} was selected based on the analysis: it targets the primary identified driver (${rootCauses[0]?.driver || kpiName + ' variance'}) with the most favourable balance of speed, reversibility, and impact relative to the structural alternatives.`
      : rawRationale

    const transformed = {
      title,
      urgency,
      metrics: {
        financialImpact: situation?.description
          ? String(situation.description).replace(/\s*\(threshold=\w+\)/gi, '').trim()
          : `${kpiName} variance detected`,
        timeSensitivity,
        confidence,
        decisionDeadline,
      },
      executiveSummary,
      situation: {
        currentState: situation?.description ? String(situation.description).replace(/\s*\(threshold=\w+\)/gi, '').trim() : `Context for ${kpiName}.`,
        problem: sol?.problem_reframe?.complication || `Variance detected in ${kpiName}.`,
        rootCauses,
        keyQuestion: sol?.problem_reframe?.question || null,
        assumptions: (sol?.problem_reframe?.key_assumptions || []).filter(
        (a: string) => !/situation_metadata/i.test(a) && !/^\s*null\s*$/i.test(a)
      ),
      },
      options,
      roadmap,
      risks,
      recommendation: {
        headline: sol?.recommendation?.title
          ? `Proceed with: ${sol.recommendation.title}`
          : (options[0]?.title ? `Proceed with: ${options[0].title}` : 'Review options and approve next steps'),
        rationale,
        nextSteps,
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
