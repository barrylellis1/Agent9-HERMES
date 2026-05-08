# A9_PIB_Agent — Agent Card

**Last Updated:** 2026-05-08  
**Version:** 1.2  
**Phase:** 11A  
**Status:** Operational

## Purpose

Composes and delivers Principal Intelligence Briefings (PIBs) — structured email summaries of enterprise assessment findings delivered to C-suite principals. Handles secure one-click action tokens for deep links and delegation flows.

## Entrypoints

| Method | Signature | Returns |
|--------|-----------|---------|
| `generate_and_send` | `async def generate_and_send(briefing_config: BriefingConfig) -> BriefingRun` | BriefingRun with status + email_to + new_situation_count |

## Inputs

- `BriefingConfig` — principal_id, client_id, email_to (optional override), format, dry_run

## Outputs

- `BriefingRun` — run record with status, email_to, new_situation_count, error_message

## Content Sections

1. **New Situations** — DETECTED KPI assessments from latest client assessment run, with Investigate and Delegate one-click tokens; `key_observations` from `Situation` rendered as bullet list when present
2. **Urgency Flags** — Situations open > N days without action
3. **Solutions in Progress** — VA-tracked approved solutions with expected impact
4. **Managed Situations** — Delegation actions taken by this principal, with resolved delegate names

Note: Snooze feature removed (Phase 11A). Assessment runs are now client-scoped — all principals
for a client read from the same enterprise run rather than a principal-tagged run.

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

## Request/Response Models

### BriefingConfig (Input)
```python
principal_id: str                   # Principal to send briefing to
client_id: str                      # Client/tenant ID
email_to: Optional[str]             # Override email (default: from registry)
format: BriefingFormat = "detailed" # "detailed" or "digest"
dry_run: bool = False               # If True, compose but don't send email
```

### BriefingRun (Output)
```python
id: str                             # Generated UUID
principal_id: str                   # Principal ID
client_id: str                      # Client ID
assessment_run_id: Optional[str]    # Latest assessment run ID
email_to: str                       # Actual email address used
format: BriefingFormat              # Format used
new_situation_count: int            # Number of new situations in this run
status: BriefingRunStatus           # "pending" | "sent" | "failed"
generated_at: datetime              # ISO timestamp
error_message: Optional[str]        # Error details if status="failed"
sent_at: Optional[datetime]         # When email was sent
```

## Error Behaviour

| Scenario | Raises | Returns |
|----------|--------|---------|
| Principal email not found (not in registry) | `ValueError` | Exception before response |
| No assessment run exists | None (logs warning) | BriefingRun with status="SENT", new_situation_count=0 |
| SMTP connection fails | Exception logged (non-fatal) | BriefingRun with status="FAILED", error_message set |
| Email render (Jinja2) fails | Exception logged | BriefingRun with status="FAILED" |
| Supabase unavailable | Non-fatal (try/except) | BriefingRun still returned; persists skipped |
| dry_run=True | None | BriefingRun with status="SENT" (email NOT sent) |

**Key Design:** SMTP failures are caught and non-fatal (the briefing compose pipeline is not blocked). Assessment data fetches are non-blocking; empty briefing is sent rather than error.

### BriefingContent (Internal Composition)
```python
principal_id: str
principal_name: str
principal_role: str
client_id: str
assessment_run_id: str
new_situations: List[SituationBriefingItem]      # Detected KPI situations
urgency_flags: List[UrgencyItem]                  # Situations open > N days
solutions_in_progress: List[SolutionProgressItem] # VA-tracked solutions
managed_situations: List[ManagedSituationItem]    # Delegated situations

# Supporting models
situation_context: Optional[SituationContext]     # Impact + urgency metrics
recommended_solution: Optional[RecommendedSolution] # Recommended action
decision_studio_url: str                          # Base URL for deep links
```

### SituationBriefingItem
```python
situation_id: str
kpi_assessment_id: str
kpi_name: str
severity: str                       # "critical" | "high" | "medium" | "low"
severity_score: float
description: str
deviation_summary: str              # e.g., "decreased 32.9% vs baseline"
current_value: Optional[float]
is_new: bool = True                 # True if not in previous run
weeks_open: int = 0                 # 0 for new situations
deep_link_token: Optional[str]      # UUID for "Investigate" deep link
delegate_token: Optional[str]
request_info_token: Optional[str]
key_observations: Optional[List[str]] # Bullet-point observations from Situation
```

## Lifecycle Notes

**Dry Run Mode:** When `dry_run=True`:
1. Principal is still resolved from registry
2. Assessment run is still loaded
3. Content is still composed
4. HTML is still rendered
5. **Email is NOT sent** (SMTP call skipped)
6. BriefingRun is **NOT persisted** to Supabase
7. Status returned is "SENT" (no error)

**Token TTL:** Deep-link tokens (investigate, delegate, request_info) have a 7-day TTL. After expiration, clicking a link in the email returns a 401 or "expired token" message.

**Email Rendering:** Uses Jinja2 template `src/templates/pib_briefing.html`. On template error, falls back to plain-text version.
