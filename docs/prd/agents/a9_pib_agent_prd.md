# PIB Agent PRD — Principal Intelligence Briefing

## Overview

**Agent Name:** A9_PIB_Agent  
**Status:** [MVP] — 5 entrypoints implemented  
**Last PRD Sync:** 2026-05-02  
**Code Location:** `src/agents/new/a9_pib_agent.py`  
**API Routes:** `src/api/routes/pib.py` (5 endpoints)  
**Alignment:** 100% (all entrypoints implemented, operational)

---

## 1. Purpose & Role in Workflow

The PIB (Principal Intelligence Briefing) Agent transforms assessment results into **actionable email briefings** delivered to principals:
- **Email Composition** — Synthesize SA/DA/SF results into executive-friendly narrative with Jinja2 templates
- **One-Click Actions** — Briefing includes snooze, delegate, request info, approve solution buttons
- **Token Management** — Generate briefing tokens for action tracking and delegation
- **SMTP Delivery** — Send emails to principal mailboxes with delegation flow
- **Delegation** — Route solutions to domain experts for refinement before final approval

Operates as the **delivery layer** between Solution Finder (recommendations) and principal action (delegate/approve/snooze).

---

## 2. Design Philosophy

**Principle: Briefing as Decision Artifact**

PIB produces email briefings that capture the complete decision context: situation (SA), analysis (DA), proposed solutions (SF), market signals (MA), and expected impact (VA). Principals click actions in the email, which flow back to the system via delegation or approval workflows.

### 2.1 Briefing Template Architecture

Jinja2 templates live in `src/templates/`:
- `situation_briefing_base.html` — Core briefing layout
- `situation_briefing_extended.html` — Extended version with benchmarks and recommendations

Templates render:
- **Executive Summary** — 1-2 sentence overview of the situation
- **Key Findings** — Top 3 findings from DA Is/Is Not analysis
- **Recommended Solutions** — SF-generated trade-off matrix with estimated impact
- **Expected Impact** — VA-attributed cost-of-inaction + expected lift
- **One-Click Actions** — Snooze (X days), Delegate (to expert), Request Info, Approve Solution

---

## 3. Entrypoints (5 Implemented)

### 3.1 generate_briefing()

```
Input:
  recommendation_id: str
  principal_id: str
  assessment_context: Dict  # SA/DA/SF/MA/VA results

Output:
  BriefingRunResponse:
    - briefing_id: str
    - content: str (rendered HTML)
    - recipient_email: str
    - status: "success" | "failed"
    - briefing_tokens: List[BriefingToken]
```

**Behavior:**
1. Load principal email from PCA
2. Aggregate SA situation, DA analysis, SF recommendation, MA signals, VA impact
3. Render Jinja2 template with assessment context
4. Generate unique briefing tokens for snooze/delegate/approve actions
5. Return briefing HTML + token list

---

### 3.2 send_briefing()

```
Input:
  briefing_id: str
  recipient_email: str

Output:
  BriefingSendResponse:
    - sent: bool
    - delivery_timestamp: datetime
    - smtp_status: str
```

**Behavior:**
1. Load briefing content + recipient email
2. Compose SMTP message
3. Send via SMTP server (credentials from env vars)
4. Log delivery status to BriefingStore
5. Return delivery confirmation

---

### 3.3 process_briefing_action()

```
Input:
  briefing_token: str  # From email action link
  action: "snooze" | "delegate" | "request_info" | "approve"
  notes: Optional[str]

Output:
  BriefingActionResponse:
    - acknowledged: bool
    - next_step: str
    - delegation_status: Optional[str]
```

**Behavior:**
1. Validate briefing token (check expiry, action permission)
2. Route action:
   - **snooze**: Mark situation snoozed for N days, re-evaluate schedule
   - **delegate**: Route recommendation to domain expert (via email or queue)
   - **request_info**: Log feedback, trigger orchestrator for additional analysis
   - **approve**: Persist solution to VA registry, trigger implementation tracking
3. Return action confirmation + next step

---

### 3.4 resolve_briefing_token()

```
Input:
  briefing_token: str

Output:
  BriefingTokenResolveResponse:
    - token_type: TokenType  # "snooze" | "delegate" | "request_info" | "approve"
    - recommendation_id: str
    - principal_id: str
    - action_context: Dict
    - valid: bool
    - expiry: datetime
```

**Behavior:**
1. Look up token in token store
2. Validate token hasn't expired
3. Return token metadata for action routing
4. Used by API endpoint to route email action links

---

### 3.5 list_briefing_runs()

```
Input:
  principal_id: Optional[str] = None
  status: Optional[str] = None  # "sent" | "pending" | "failed"
  limit: int = 50

Output:
  List[BriefingRun]:
    - briefing_id: str
    - principal_id: str
    - recommendation_id: str
    - content_summary: str (first 200 chars)
    - status: BriefingRunStatus
    - created_at: datetime
    - sent_at: Optional[datetime]
```

**Behavior:**
1. Query BriefingStore for briefing runs matching filter criteria
2. Sort by created_at descending
3. Return briefing run summaries (not full HTML)

---

## 4. Briefing Token System

Each briefing generates **unique, expiring tokens** for one-click actions:

```
Token Structure:
  - briefing_token: str (UUID)
  - token_type: TokenType (snooze | delegate | request_info | approve)
  - recommendation_id: str
  - principal_id: str
  - created_at: datetime
  - expires_at: datetime (default: 30 days)
  - action_context: Dict (reason, notes, expert_id for delegation)

Token Lifecycle:
  1. Generated when briefing is created
  2. Embedded in email action links: https://app.example.com/actions/{briefing_token}
  3. Validated when action link is clicked
  4. Consumed/marked as used after action processes
  5. Expire after 30 days (configurable)
```

---

## 5. Email Delivery Flow

```
SA detects situation
  ↓
DA analyzes problem
  ↓
SF generates recommendations
  ↓
MA enriches with market signals
  ↓
VA evaluates expected impact
  ↓
PIB.generate_briefing() → renders HTML
  ↓
PIB.send_briefing() → SMTP delivery
  ↓
Principal receives email with action buttons
  ↓
Principal clicks action (snooze/delegate/approve)
  ↓
PIB.process_briefing_action() → routes to next step
  ↓
(snooze) → reschedule SA assessment
(delegate) → email domain expert for refinement
(request_info) → trigger DA additional analysis
(approve) → register solution to VA + tracking
```

---

## 6. Implementation Status

| Feature | Status | Lines | Notes |
|---|---|---|---|
| Email template rendering (Jinja2) | ✅ Production | all | Renders situation + recommendation context |
| SMTP delivery | ✅ Production | all | Async SMTP via aiosmtplib |
| Briefing token generation/validation | ✅ Production | all | UUID-based, expiring tokens for actions |
| One-click action processing | ✅ Production | all | snooze/delegate/request_info/approve |
| Delegation flow | ✅ Production | all | Routes to domain experts |
| Briefing persistence | ✅ Production | all | BriefingStore in Supabase |

---

## 7. Known Limitations

1. **No Slack delivery** — Email only; Slack integration pending (Phase 11+)
2. **Token expiry fixed** — 30 days; no custom per-briefing expiry
3. **Delegation queue basic** — In-memory; no persistent delegation queue
4. **Template customization limited** — Jinja2 templates are hardcoded; no user theming
5. **HTML email only** — No plain-text alternative for email clients that don't support HTML

---

## 8. Dependencies

- **A9_Situation_Awareness_Agent** — provides situation cards
- **A9_Deep_Analysis_Agent** — provides Is/Is Not analysis + benchmarks
- **A9_Solution_Finder_Agent** — provides recommendations
- **A9_Market_Analysis_Agent** — provides market signals (optional enrichment)
- **A9_Value_Assurance_Agent** — provides impact attribution + cost-of-inaction
- **A9_Principal_Context_Agent** — provides principal email address
- **Jinja2** — template rendering
- **aiosmtplib** — async SMTP delivery
- **BriefingStore** — Supabase table for briefing persistence

---

## 9. Testing

**Unit tests:** `tests/unit/test_a9_pib_agent.py`
- ✅ Token generation and validation
- ✅ Jinja2 template rendering
- ✅ Action routing (snooze, delegate, approve)
- ✅ Email composition
- ✅ SMTP mocking (no live email in CI)

**Integration tests:** Run against live Supabase + SMTP
- Generate briefing from recommendation
- Send email to test mailbox
- Click action link, verify action processes
- Verify delegation email sent to domain expert

---

## 10. Changelog

**v1.0 (2026-02-28)** — Initial MVP with email briefing composition and one-click actions

**v1.1 (2026-03-15)** — Added delegation flow, briefing token system, action link support

**v2.0 (2026-05-02)** — Aligned PRD with DEVELOPMENT_PLAN:
- Documented 5 entrypoints with exact signatures
- Clarified briefing token lifecycle and expiry
- Updated email delivery flow diagram
- Noted delegation queue persistence deferred (Phase 11+)
- Noted Slack integration deferred (Phase 11+)
- Documented Supabase persistence and BriefingStore
- Added implementation status table

---
