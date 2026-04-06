# A9_PIB_Agent — Agent Card

**Version:** 1.0  
**Phase:** 9C  
**Status:** Operational

## Purpose

Composes and delivers Principal Intelligence Briefings (PIBs) — structured email summaries of enterprise assessment findings delivered to C-suite principals. Handles secure one-click action tokens for deep links and delegation flows.

## Entrypoints

| Method | Description |
|--------|-------------|
| `generate_and_send(config: BriefingConfig)` | Compose and email a PIB for a principal+client. Returns `BriefingRun`. |

## Inputs

- `BriefingConfig` — principal_id, client_id, email_to (optional override), format, dry_run

## Outputs

- `BriefingRun` — run record with status, email_to, new_situation_count, error_message

## Content Sections

1. **New Situations** — DETECTED KPI assessments from latest assessment run, with Investigate and Delegate one-click tokens
2. **Urgency Flags** — Situations open > N days without action
3. **Solutions in Progress** — VA-tracked approved solutions with expected impact
4. **Managed Situations** — Actions already taken (delegated / snoozed) with resolved principal names

## Key Dependencies

- `AssessmentStore` — reads latest `assessment_runs` + `kpi_assessments` from Supabase
- `BriefingStore` — persists `briefing_runs` + `briefing_tokens` to Supabase
- `A9_Principal_Context_Agent` — resolves principal names and email addresses
- Jinja2 — renders `src/templates/pib_briefing.html`
- aiosmtplib — sends via SMTP (Gmail App Password supported)

## Configuration (env vars)

| Var | Purpose |
|-----|---------|
| `SMTP_HOST` | SMTP server (e.g. smtp.gmail.com) |
| `SMTP_PORT` | SMTP port (587 for STARTTLS) |
| `SMTP_USER` | SMTP username |
| `SMTP_PASSWORD` | SMTP password / App Password |
| `SMTP_FROM` | From address |
| `DECISION_STUDIO_URL` | Base URL for deep links (default: http://localhost:5173) |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key |
