/**
 * Executive Briefing fixture - derived from a REAL captured SF payload
 * (live run, 2026-08-07, moderator arm). Not hand-invented: the
 * moderator_grades below are exactly what the pipeline produced, so a
 * rendering regression is caught against the shape the product emits.
 *
 * Regenerate by re-running scripts against a fresh sf-synthesis-payload.json.
 */
export const MODERATOR_BRIEFING = {
  "kpiName": "Gross Margin %",
  "metrics": {
    "financialImpact": "Gross margin declined 610 basis points year-over-year to 30.29%"
  },
  "situation": {
    "currentState": "Gross Margin % is 30.29% vs 36.27% prior year.",
    "problem": "Base oil cost inflation passing through to COGS with a ~1-month lag.",
    "keyQuestion": "How do we restore margin without breaching the anchor-account price lock?",
    "assumptions": []
  },
  "recommendation": {
    "headline": "Proceed with: Accelerated Cost Pass-Through Negotiation with National Auto Parts Chain A",
    "rationale": "Given the CFO's need to stabilize margin within the current planning cycle at the lowest possible cost and risk, opt_1 is the correct first move: it targets 100% of the single largest confirmed driver - National Auto Parts Chain A's -43.24pp decline - through ...",
    "decisionOwner": "Finance Leadership",
    "deadline": "End of Week 2",
    "optionId": "opt_1"
  },
  "options": [
    {
      "title": "Accelerated Cost Pass-Through Negotiation with National Auto Parts Chain A",
      "subtitle": "Time to value: 0-90 days",
      "description": "Launch a 15-day structured commercial negotiation with National Auto Parts Chain A to quantify base oil cost inflation absorbed year-to-date and secure a cost-indexed surcharge or accelerated adjustment effective at the next contractual pricing window (30-45 d...",
      "roi": "+28.5pp to +43.2pp - National Auto Parts Chain A only",
      "impactBasis": "Lower bound assumes 65% cost recovery via negotiation within 45 days (0.65 x 43.24pp); upper bound assumes full pass-through once the next pricing window opens. Sized entirely from the National Auto P...",
      "investment": "Moderate Effort",
      "timeline": "0-90 days",
      "riskLevel": "Medium",
      "reversibility": "high"
    },
    {
      "title": "SKU Mix & Discount Forensic Audit with Contract Renewal Acceleration for Chain A and Synthetic Blend",
      "subtitle": "Time to value: 0-90 days",
      "description": "Execute a 30-90 day forensic audit of National Auto Parts Chain A's invoice-level pricing, SKU mix, and discount depth, deconstructing the -43.24pp delta into COGS-lag, discounting, and mix-shift components, with a parallel audit of the Synthetic Blend Engine ...",
      "roi": "+28.5pp to +43.2pp - National Auto Parts Chain A only",
      "impactBasis": "Conservative recovery assumes 40-70% of the Chain A -43.24pp delta is attributable to COGS lag plus price-lock timing (18pp), rising to 31pp if discounting is confirmed and renegotiated; the Synthetic...",
      "investment": "Moderate Effort",
      "timeline": "0-90 days",
      "riskLevel": "Medium",
      "reversibility": "high"
    },
    {
      "title": "Full Potential Portfolio Reset: SKU Rationalization, Dynamic Pricing Clauses, and Cross-Segment Margin Governance",
      "subtitle": "Time to value: 0-90 days",
      "description": "Undertake a 12-18 month structural transformation covering all three confirmed problem segments - Chain A, Synthetic Blend Engine Oil, and Service Centers Division - combining SKU rationalization (dropping or repricing chronically low-margin lines), dynamic co...",
      "roi": "+28.5pp to +43.2pp - National Auto Parts Chain A only",
      "impactBasis": "Chain A's -43.24pp delta remains the primary lever; a full-potential reset targeting 40-75% recovery via cost pass-through, SKU rationalization, and dynamic pricing yields 18-32pp, with Synthetic Blen...",
      "investment": "Moderate Effort",
      "timeline": "0-90 days",
      "riskLevel": "Medium",
      "reversibility": "high"
    }
  ],
  "cross_review": null,
  "moderator_grades": {
    "opt_1": {
      "constraint_survival": "pass",
      "violated_constraints": [],
      "causal_grounding": "gross_margin_pct <-> cogs (base oil cost-lag mechanism, confirmed, ~1-month lag)",
      "arithmetic_consistency": "pass",
      "arithmetic_note": "",
      "critic_findings_response": [],
      "grade_rationale": "The option's mechanism is explicitly framed as a cost-indexed surcharge deployed at the next contractual window rather than a mid-quarter list price change, consistent with surviving the sole active price-lock constraint; its recovery_range (28.5-43.24pp) does..."
    },
    "opt_2": {
      "constraint_survival": "pass",
      "violated_constraints": [],
      "causal_grounding": "premium_mix_pct <-> gross_margin_pct (template, unconfirmed industry prior) with secondary reliance on the confirmed gross_margin_pct <-> cogs lag for the Synthetic Blend component",
      "arithmetic_consistency": "pass",
      "arithmetic_note": "",
      "critic_findings_response": [],
      "grade_rationale": "Early renewal discussions and audit activity do not constitute a mid-quarter list price change, so the option survives the sole active constraint; its 18-31pp recovery_range stays within the Chain A -43.24pp delta it targets, so arithmetic is consistent. The m..."
    },
    "opt_3": {
      "constraint_survival": "pass",
      "violated_constraints": [],
      "causal_grounding": "premium_mix_pct <-> gross_margin_pct (template, unconfirmed) for the eventual mix-shift lever; gross_margin_pct <-> cogs (confirmed) is invoked by extrapolation to Service Centers Division, which is not directly evidenced",
      "arithmetic_consistency": "pass",
      "arithmetic_note": "",
      "critic_findings_response": [],
      "grade_rationale": "Dynamic pricing clauses and SKU rationalization are structured for future renewal cycles, not mid-quarter list price changes, so the option survives the one active constraint; its 18-32pp recovery_range stays within the Chain A -43.24pp delta, consistent with ..."
    }
  },
  "blind_spots": [
    "Volume response to indexed pricing is unmeasured."
  ],
  "unresolved_tensions": [],
  "market_signals": null
} as const;
