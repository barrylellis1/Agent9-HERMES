# doc-sync-skip
"""
A9_Accountability_Interview_Agent — LLM-driven KPI ownership onboarding.

Runs a 3-phase conversational interview to help admins assign KPI accountability:
  Phase 1 (process_suggestion): batch-propose KPIs from process ownership
  Phase 2 (gap_resolution): resolve unassigned KPIs one-by-one
  Phase 3 (review): surface conflicts and coverage gaps before final confirmation

The agent returns ProposedAssignment objects. It does NOT write to the registry.
Confirm endpoint (in API routes) writes the approved rows to kpi_accountability.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field

from src.agents.new.a9_llm_service_agent import A9_LLM_Service_Agent, A9_LLM_Request
from src.agents.agent_config_models import A9_LLM_Service_Agent_Config

logger = logging.getLogger(__name__)

# ── Models ─────────────────────────────────────────────────────────────────────


class AccountabilityInterviewRequest(BaseModel):
    session_id: Optional[str] = None       # None = start new session
    client_id: str
    principal_id: Optional[str] = None     # None = interview all principals
    user_message: Optional[str] = None     # None on first turn
    conversation_history: List[dict] = Field(default_factory=list)
    turn_count: int = 0


class ProposedAssignment(BaseModel):
    kpi_id: str
    kpi_name: str
    principal_id: str
    principal_name: str
    scope_dimension: Optional[str] = None
    scope_value: Optional[str] = None
    role: str = "accountable"              # accountable | responsible
    suggestion_source: str                 # "process:<process_id>" | "direct" | "gap"
    status: str = "proposed"              # proposed | confirmed | modified | rejected


class AccountabilityInterviewResponse(BaseModel):
    session_id: str
    agent_message: str
    suggested_responses: List[str] = Field(default_factory=list)
    proposed_assignments: List[ProposedAssignment] = Field(default_factory=list)
    unassigned_kpis: List[dict] = Field(default_factory=list)    # [{id, name}]
    coverage_pct: float = 0.0
    conflict_warnings: List[str] = Field(default_factory=list)
    phase: str = "process_suggestion"      # process_suggestion | gap_resolution | review
    interview_complete: bool = False
    conversation_history: List[dict] = Field(default_factory=list)
    turn_count: int = 0


# Internal session state — not exposed to callers
class _InterviewSession(BaseModel):
    session_id: str
    client_id: str
    principal_id: Optional[str]
    phase: str = "process_suggestion"
    conversation_history: List[dict] = Field(default_factory=list)
    proposed_assignments: List[ProposedAssignment] = Field(default_factory=list)
    all_kpis: List[dict] = Field(default_factory=list)           # [{id, name, domain, business_process_ids}]
    all_processes: List[dict] = Field(default_factory=list)      # [{id, name, kpi_ids}]
    all_principals: List[dict] = Field(default_factory=list)     # [{id, name, title}]
    turn_count: int = 0
    interview_complete: bool = False
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ── Agent ──────────────────────────────────────────────────────────────────────


class A9_Accountability_Interview_Agent:
    """
    Conversational interview agent for KPI accountability onboarding.

    Lifecycle: create() → connect() → interview() calls → disconnect()
    Session state is in-memory; sessions are not persisted across restarts.
    """

    MODEL_CHAT = "claude-haiku-4-5-20251001"    # all chat turns
    MODEL_ANALYSIS = "claude-sonnet-4-6"         # coverage + conflict analysis at Phase 3 entry

    def __init__(self) -> None:
        self._sessions: Dict[str, _InterviewSession] = {}
        self._llm_agent: Optional[A9_LLM_Service_Agent] = None

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    @classmethod
    async def create(cls) -> "A9_Accountability_Interview_Agent":
        agent = cls()
        await agent.connect()
        return agent

    async def connect(self) -> bool:
        try:
            llm_config = A9_LLM_Service_Agent_Config(task_type="general")
            self._llm_agent = await A9_LLM_Service_Agent.create(llm_config.__dict__)
            logger.info("A9_Accountability_Interview_Agent connected")
            return True
        except Exception as exc:
            logger.error("A9_Accountability_Interview_Agent failed to connect: %s", exc)
            return False

    async def disconnect(self) -> bool:
        logger.info("A9_Accountability_Interview_Agent disconnected")
        return True

    # ── Public entrypoint ──────────────────────────────────────────────────────

    async def interview(
        self,
        request: AccountabilityInterviewRequest,
    ) -> AccountabilityInterviewResponse:
        """Single entrypoint for all interview interactions."""
        try:
            if request.session_id is None or request.session_id not in self._sessions:
                return await self._start_session(request)
            return await self._continue_session(request)
        except Exception as exc:
            logger.error("Interview error: %s", exc)
            session_id = request.session_id or str(uuid.uuid4())
            return AccountabilityInterviewResponse(
                session_id=session_id,
                agent_message=f"An error occurred: {exc}",
                phase="process_suggestion",
            )

    # ── Session start ──────────────────────────────────────────────────────────

    async def _start_session(
        self, request: AccountabilityInterviewRequest
    ) -> AccountabilityInterviewResponse:
        session_id = str(uuid.uuid4())

        # Load registry context
        all_kpis, all_processes, all_principals = await self._load_registry_context(
            request.client_id, request.principal_id
        )

        session = _InterviewSession(
            session_id=session_id,
            client_id=request.client_id,
            principal_id=request.principal_id,
            all_kpis=all_kpis,
            all_processes=all_processes,
            all_principals=all_principals,
        )
        self._sessions[session_id] = session

        # Generate opening message — parse out suggested_responses and clean the text
        opening_raw = await self._generate_opening(session)
        opening_assignments = self._extract_assignments(opening_raw, session)
        suggested = self._extract_suggested_responses(opening_raw)
        opening_clean = self._strip_json_blocks(opening_raw)
        self._merge_assignments(session, opening_assignments)
        session.conversation_history.append({"role": "assistant", "content": opening_clean})

        return self._build_response(session, opening_clean, suggested)

    # ── Session continuation ───────────────────────────────────────────────────

    async def _continue_session(
        self, request: AccountabilityInterviewRequest
    ) -> AccountabilityInterviewResponse:
        session = self._sessions[request.session_id]

        if request.user_message:
            session.conversation_history.append(
                {"role": "user", "content": request.user_message}
            )

        # Switch to analysis model at Phase 3 entry; chat model otherwise
        model = (
            self.MODEL_ANALYSIS
            if session.phase == "gap_resolution" and self._all_principals_covered(session)
            else self.MODEL_CHAT
        )

        # Possibly advance phase before calling LLM
        self._maybe_advance_phase(session)

        system_prompt = self._build_system_prompt(session)
        agent_message, new_assignments, updated_statuses, suggested_responses = (
            await self._call_llm_and_parse(session, system_prompt, model)
        )

        # Merge new assignments into session state
        self._merge_assignments(session, new_assignments)

        # Apply status updates (confirmed / modified / rejected)
        for update in updated_statuses:
            self._apply_status_update(session, update)

        session.conversation_history.append(
            {"role": "assistant", "content": agent_message}
        )
        session.turn_count += 1

        # Check for interview completion
        if session.phase == "review" and self._review_complete(agent_message):
            session.interview_complete = True

        return self._build_response(session, agent_message, suggested_responses)

    # ── Phase logic ────────────────────────────────────────────────────────────

    def _maybe_advance_phase(self, session: _InterviewSession) -> None:
        """Advance phase when natural transition conditions are met."""
        if session.phase == "process_suggestion" and self._all_principals_covered(session):
            unassigned = self._get_unassigned_kpis(session)
            if unassigned:
                session.phase = "gap_resolution"
                logger.info(
                    "Session %s: advancing to gap_resolution (%d unassigned KPIs)",
                    session.session_id,
                    len(unassigned),
                )
            else:
                session.phase = "review"
                logger.info("Session %s: advancing directly to review (full coverage)", session.session_id)
        elif session.phase == "gap_resolution" and not self._get_unassigned_kpis(session):
            session.phase = "review"
            logger.info("Session %s: advancing to review (gap resolved)", session.session_id)

    def _all_principals_covered(self, session: _InterviewSession) -> bool:
        """True when at least one process/KPI proposal has been made for every principal."""
        if not session.all_principals:
            return True
        principals_with_proposals = {a.principal_id for a in session.proposed_assignments}
        return all(
            p["id"] in principals_with_proposals for p in session.all_principals
        )

    def _review_complete(self, agent_message: str) -> bool:
        markers = ["coverage complete", "all kpis assigned", "interview complete"]
        lower = agent_message.lower()
        return any(m in lower for m in markers)

    # ── LLM calls ─────────────────────────────────────────────────────────────

    async def _generate_opening(self, session: _InterviewSession) -> str:
        system = self._build_system_prompt(session)
        principals_str = ", ".join(
            f"{p['name']} ({p['title']})" for p in session.all_principals
        ) or "no principals found"
        user_msg = (
            f"Start the accountability interview. "
            f"The principals to cover are: {principals_str}. "
            f"There are {len(session.all_kpis)} KPIs registered for this client. "
            f"Begin with the first principal."
        )
        response = await self._llm_call(system, user_msg, self.MODEL_CHAT)
        return response

    async def _call_llm_and_parse(
        self,
        session: _InterviewSession,
        system_prompt: str,
        model: str,
    ):
        """Call the LLM and parse the response for assignments and suggested responses."""
        conversation_prompt = self._build_conversation_prompt(session)
        raw = await self._llm_call(system_prompt, conversation_prompt, model)

        new_assignments = self._extract_assignments(raw, session)
        updated_statuses = self._extract_status_updates(raw)
        suggested_responses = self._extract_suggested_responses(raw)
        agent_message = self._strip_json_blocks(raw)

        return agent_message, new_assignments, updated_statuses, suggested_responses

    async def _llm_call(self, system_prompt: str, user_prompt: str, model: str) -> str:
        if not self._llm_agent:
            raise RuntimeError("LLM agent not initialized")
        req = A9_LLM_Request(
            request_id=f"interview_{uuid.uuid4().hex[:8]}",
            principal_id="system",
            prompt=user_prompt,
            system_prompt=system_prompt,
            model=model,
            temperature=0.3,
            max_tokens=2048,
            operation="accountability_interview",
        )
        resp = await self._llm_agent.generate(req)
        if resp.status != "success":
            raise RuntimeError(f"LLM call failed: {resp.error_message}")
        return resp.content

    # ── Prompt building ────────────────────────────────────────────────────────

    def _build_system_prompt(self, session: _InterviewSession) -> str:
        kpi_lines = "\n".join(
            f"  - {k['id']} | {k['name']} | processes: {', '.join(k.get('business_process_ids', []) or []) or 'none'}"
            for k in session.all_kpis
        )

        # Group processes by domain for a cleaner admin-facing presentation
        from collections import defaultdict
        domain_map: dict = defaultdict(list)
        for p in session.all_processes:
            domain = p.get("domain") or p["id"].split("_")[0].capitalize()
            domain_map[domain].append(p)
        domain_lines = []
        for domain, procs in sorted(domain_map.items()):
            kpi_count = sum(len(p.get("kpi_ids", [])) for p in procs)
            proc_names = ", ".join(p["name"] for p in procs)
            domain_lines.append(
                f"  {domain} ({len(procs)} processes, {kpi_count} KPIs): {proc_names}"
            )
        process_domain_map = "\n".join(domain_lines)
        process_detail_lines = "\n".join(
            f"    [{p.get('domain', '?')}] {p['id']} | {p['name']} | KPIs: {', '.join(p.get('kpi_ids', []))}"
            for p in session.all_processes
        )
        principal_lines = "\n".join(
            f"  - {p['id']} | {p['name']} ({p.get('title', '')})"
            for p in session.all_principals
        )
        assigned_lines = "\n".join(
            f"  - {a.principal_name} → {a.kpi_name} [{a.role}] scope={a.scope_dimension}:{a.scope_value or 'ALL'} status={a.status}"
            for a in session.proposed_assignments
        ) or "  (none yet)"

        unassigned = self._get_unassigned_kpis(session)
        unassigned_lines = "\n".join(
            f"  - {k['id']} | {k['name']}" for k in unassigned
        ) or "  (all KPIs assigned)"

        coverage_pct = self._compute_coverage_pct(session)

        return f"""You are an AI facilitator helping an ADMIN assign KPI accountability across their leadership team.
You are speaking to the ADMIN — not to the principals themselves. The principals are not present.
Always refer to each principal in the THIRD PERSON by name and title (e.g. "Rachel Kim is your COO").
Never use "you" to mean a principal. "You" always refers to the admin you are speaking with.

CURRENT PHASE: {session.phase}
COVERAGE: {coverage_pct:.0%} ({len(session.all_kpis) - len(unassigned)}/{len(session.all_kpis)} KPIs assigned)

REGISTERED PRINCIPALS:
{principal_lines}

REGISTERED KPIs:
{kpi_lines}

BUSINESS PROCESS MAP (grouped by domain):
{process_domain_map}

BUSINESS PROCESS DETAIL (for when you need to list specific processes within a domain):
{process_detail_lines}

PROPOSED ASSIGNMENTS SO FAR:
{assigned_lines}

UNASSIGNED KPIs:
{unassigned_lines}

PHASE INSTRUCTIONS:
- process_suggestion: Use a TWO-STEP approach for each principal:
    STEP 1 — Domain level: Present the business domains as a short list and ask which domain(s)
    the principal is accountable for. Example: "David Torres is your Chief Executive Officer.
    Which business domains is he responsible for? The available domains are: Finance, Strategy,
    Pricing, Product." Set suggested_responses to the domain names (plus "All of them").
    STEP 2 — Confirm KPIs: Once the admin picks domains, immediately expand those domains into
    their specific KPIs and emit an `assignments` block for ALL of them (status="proposed").
    Ask the admin to confirm the proposals. When they confirm, emit a `status_updates` block.
    Then move to the next principal.
- gap_resolution: For each unassigned KPI, ask the admin who among the leadership team owns it.
  When the admin answers, emit an `assignments` block for those direct assignments.
- review: Summarise coverage and any conflicts. When the admin is satisfied, say "Interview complete."

MANDATORY OUTPUT RULES — follow these on EVERY turn:
1. Write a brief plain-text message (no markdown headers, no bullet asterisks).
2. WHENEVER you propose new KPI assignments, include this block (required, not optional):
   ```assignments
   [{{"kpi_id": "net_revenue", "kpi_name": "Net Revenue", "principal_id": "cfo_001", "principal_name": "Sarah Chen", "scope_dimension": null, "scope_value": null, "role": "accountable", "suggestion_source": "process:finance_revenue_growth_analysis", "status": "proposed"}}]
   ```
3. WHENEVER the admin confirms, rejects, or modifies proposals, include this block (required):
   ```status_updates
   [{{"kpi_id": "net_revenue", "principal_id": "cfo_001", "status": "confirmed", "scope_dimension": null, "scope_value": null}}]
   ```
   If the admin says "confirm all" or "yes assign all", emit a status_updates block with ALL
   current proposed assignments set to status="confirmed".
4. End every turn with this block (required):
   ```suggested_responses
   ["Yes, confirm all", "Reject this one", "Change scope to EMEA"]
   ```
5. Do NOT write to the registry. Only emit the JSON blocks above.
6. Keep text responses to 2-3 sentences. Let the JSON blocks carry the data.
"""

    def _build_conversation_prompt(self, session: _InterviewSession) -> str:
        recent = session.conversation_history[-6:]  # last 3 turns
        lines = []
        for msg in recent:
            role = msg["role"].upper()
            lines.append(f"{role}: {msg['content']}")
        return "\n\n".join(lines) + "\n\nASSISTANT:"

    # ── Parsing helpers ────────────────────────────────────────────────────────

    def _extract_assignments(
        self, raw: str, session: _InterviewSession
    ) -> List[ProposedAssignment]:
        return self._extract_json_block(raw, "assignments", ProposedAssignment)

    def _extract_status_updates(self, raw: str) -> List[dict]:
        return self._extract_json_block(raw, "status_updates", None)

    def _extract_suggested_responses(self, raw: str) -> List[str]:
        block = self._extract_raw_block(raw, "suggested_responses")
        if not block:
            return []
        try:
            parsed = json.loads(block)
            if isinstance(parsed, list):
                return [str(s) for s in parsed]
        except json.JSONDecodeError:
            pass
        return []

    def _extract_json_block(self, raw: str, tag: str, model_class) -> list:
        block = self._extract_raw_block(raw, tag)
        if not block:
            return []
        try:
            parsed = json.loads(block)
            if not isinstance(parsed, list):
                return []
            if model_class is None:
                return parsed
            result = []
            for item in parsed:
                try:
                    result.append(model_class(**item))
                except Exception as e:
                    logger.warning("Skipping malformed %s item: %s — %s", tag, item, e)
            return result
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse %s JSON block: %s", tag, e)
            return []

    def _extract_raw_block(self, raw: str, tag: str) -> Optional[str]:
        start_marker = f"```{tag}"
        end_marker = "```"
        start = raw.find(start_marker)
        if start == -1:
            return None
        start += len(start_marker)
        end = raw.find(end_marker, start)
        if end == -1:
            return None
        return raw[start:end].strip()

    def _strip_json_blocks(self, raw: str) -> str:
        """Remove tagged code blocks from the message shown to the admin."""
        import re
        cleaned = re.sub(r"```(?:assignments|status_updates|suggested_responses)[\s\S]*?```", "", raw)
        return cleaned.strip()

    # ── State management ───────────────────────────────────────────────────────

    def _merge_assignments(
        self, session: _InterviewSession, new_assignments: List[ProposedAssignment]
    ) -> None:
        existing_keys = {
            (a.kpi_id, a.principal_id, a.scope_dimension, a.scope_value)
            for a in session.proposed_assignments
        }
        for assignment in new_assignments:
            key = (assignment.kpi_id, assignment.principal_id, assignment.scope_dimension, assignment.scope_value)
            if key not in existing_keys:
                session.proposed_assignments.append(assignment)
                existing_keys.add(key)

    def _apply_status_update(self, session: _InterviewSession, update: dict) -> None:
        kpi_id = update.get("kpi_id")
        principal_id = update.get("principal_id")
        new_status = update.get("status", "confirmed")
        new_scope_dimension = update.get("scope_dimension")
        new_scope_value = update.get("scope_value")

        for assignment in session.proposed_assignments:
            if assignment.kpi_id == kpi_id and assignment.principal_id == principal_id:
                assignment.status = new_status
                if new_scope_dimension is not None:
                    assignment.scope_dimension = new_scope_dimension
                if new_scope_value is not None:
                    assignment.scope_value = new_scope_value
                break

    # ── Registry data loading ──────────────────────────────────────────────────

    async def _load_registry_context(
        self, client_id: str, principal_id: Optional[str]
    ) -> tuple:
        """Return (kpis, processes, principals) as plain dicts for prompt injection."""
        try:
            from src.registry.factory import RegistryFactory
            factory = RegistryFactory()

            kpi_provider = factory.get_provider("kpi")
            principal_provider = factory.get_provider("principal_profile")
            bp_provider = factory.get_provider("business_process")

            # KPI provider has get_by_client(); others use get_all() + manual filter.
            # All providers are synchronous — no await.
            if kpi_provider and hasattr(kpi_provider, "get_by_client"):
                all_kpis_raw = kpi_provider.get_by_client(client_id)
            elif kpi_provider:
                all_kpis_raw = [
                    k for k in kpi_provider.get_all()
                    if getattr(k, "client_id", None) == client_id
                ]
            else:
                all_kpis_raw = []

            if principal_provider:
                all_principals_raw = [
                    p for p in principal_provider.get_all()
                    if getattr(p, "client_id", None) == client_id
                ]
            else:
                all_principals_raw = []

            if bp_provider:
                all_bp_raw = [
                    b for b in bp_provider.get_all()
                    if getattr(b, "client_id", None) == client_id
                ]
            else:
                all_bp_raw = []

        except Exception as exc:
            logger.error("Failed to load registry context: %s", exc)
            all_kpis_raw, all_principals_raw, all_bp_raw = [], [], []

        # Normalise to plain dicts for prompt injection
        all_kpis = [
            {
                "id": getattr(k, "id", ""),
                "name": getattr(k, "name", ""),
                "domain": getattr(k, "domain", ""),
                "business_process_ids": list(getattr(k, "business_process_ids", None) or []),
            }
            for k in all_kpis_raw
        ]

        # Optionally scope to a single principal
        if principal_id:
            all_principals_raw = [p for p in all_principals_raw if getattr(p, "id", None) == principal_id]

        all_principals = [
            {
                "id": getattr(p, "id", ""),
                "name": getattr(p, "name", ""),
                "title": getattr(p, "title", ""),
            }
            for p in all_principals_raw
        ]

        # Build process → KPI membership from KPI records (business_process_ids)
        process_kpi_map: Dict[str, List[str]] = {}
        for kpi in all_kpis:
            for bp_id in kpi.get("business_process_ids", []):
                process_kpi_map.setdefault(bp_id, []).append(kpi["id"])

        all_processes = []
        for bp in all_bp_raw:
            bp_id = getattr(bp, "id", "")
            bp_name = getattr(bp, "name", bp_id)
            all_processes.append(
                {
                    "id": bp_id,
                    "name": bp_name,
                    "kpi_ids": process_kpi_map.get(bp_id, []),
                }
            )

        # If BP provider returned nothing, derive processes from KPI business_process_ids
        if not all_processes and process_kpi_map:
            for bp_id, kpi_ids in process_kpi_map.items():
                all_processes.append({"id": bp_id, "name": bp_id.replace("_", " ").title(), "kpi_ids": kpi_ids})

        logger.info(
            "Loaded registry context: %d KPIs, %d principals, %d processes for client '%s'",
            len(all_kpis),
            len(all_principals),
            len(all_processes),
            client_id,
        )
        return all_kpis, all_processes, all_principals

    # ── Coverage and conflict helpers ──────────────────────────────────────────

    def _get_unassigned_kpis(self, session: _InterviewSession) -> List[dict]:
        assigned_kpi_ids = {
            a.kpi_id
            for a in session.proposed_assignments
            if a.status in ("proposed", "confirmed", "modified")
        }
        return [k for k in session.all_kpis if k["id"] not in assigned_kpi_ids]

    def _compute_coverage_pct(self, session: _InterviewSession) -> float:
        total = len(session.all_kpis)
        if total == 0:
            return 1.0
        unassigned = len(self._get_unassigned_kpis(session))
        return (total - unassigned) / total

    def _detect_conflicts(self, session: _InterviewSession) -> List[str]:
        """Return warning strings for KPIs with >1 accountable principal at the same scope."""
        from collections import defaultdict
        scope_accountable: Dict[tuple, List[str]] = defaultdict(list)
        for a in session.proposed_assignments:
            if a.role == "accountable" and a.status in ("proposed", "confirmed", "modified"):
                key = (a.kpi_id, a.scope_dimension, a.scope_value)
                scope_accountable[key].append(a.principal_name)

        warnings = []
        for (kpi_id, scope_dim, scope_val), names in scope_accountable.items():
            if len(names) > 1:
                kpi_name = next(
                    (k["name"] for k in session.all_kpis if k["id"] == kpi_id), kpi_id
                )
                scope_label = f"{scope_dim}={scope_val}" if scope_dim else "enterprise-wide"
                warnings.append(
                    f"{kpi_name} ({scope_label}): {len(names)} accountable principals — {', '.join(names)}"
                )
        return warnings

    # ── Response assembly ──────────────────────────────────────────────────────

    def _build_response(
        self,
        session: _InterviewSession,
        agent_message: str,
        suggested_responses: Optional[List[str]] = None,
    ) -> AccountabilityInterviewResponse:
        unassigned = self._get_unassigned_kpis(session)
        coverage = self._compute_coverage_pct(session)
        conflicts = self._detect_conflicts(session) if session.phase == "review" else []

        return AccountabilityInterviewResponse(
            session_id=session.session_id,
            agent_message=agent_message,
            suggested_responses=suggested_responses or [],
            proposed_assignments=list(session.proposed_assignments),
            unassigned_kpis=[{"id": k["id"], "name": k["name"]} for k in unassigned],
            coverage_pct=coverage,
            conflict_warnings=conflicts,
            phase=session.phase,
            interview_complete=session.interview_complete,
            conversation_history=list(session.conversation_history),
            turn_count=session.turn_count,
        )

    # ── Coverage endpoint support ──────────────────────────────────────────────

    async def get_coverage(self, client_id: str) -> dict:
        """
        Compute live coverage from kpi_accountability table.
        Used by GET /api/v1/accountability/coverage/{client_id}.
        """
        try:
            from src.registry.providers.accountability_provider import KPIAccountabilityProvider
            from src.registry.factory import RegistryFactory

            provider = KPIAccountabilityProvider()
            all_records = await provider.get_all(client_id)

            factory = RegistryFactory()
            kpi_provider = factory.get_provider("kpi")
            if kpi_provider and hasattr(kpi_provider, "get_by_client"):
                all_kpis_raw = kpi_provider.get_by_client(client_id)
            elif kpi_provider:
                all_kpis_raw = [k for k in kpi_provider.get_all() if getattr(k, "client_id", None) == client_id]
            else:
                all_kpis_raw = []

            total_kpis = len(all_kpis_raw)
            covered_kpi_ids = {r.kpi_id for r in all_records if r.role.value == "accountable"}
            covered = len(covered_kpi_ids)

            all_kpi_ids = {getattr(k, "id", "") for k in all_kpis_raw}
            unassigned = [
                {"id": kpi_id, "name": next(
                    (getattr(k, "name", kpi_id) for k in all_kpis_raw if getattr(k, "id", "") == kpi_id),
                    kpi_id,
                )}
                for kpi_id in all_kpi_ids - covered_kpi_ids
            ]

            # Principals without any accountable assignment
            principal_provider = factory.get_provider("principal_profile")
            all_principals_raw = (
                [p for p in principal_provider.get_all() if getattr(p, "client_id", None) == client_id]
                if principal_provider else []
            )
            principals_with_assignments = {r.principal_id for r in all_records}
            principals_without = [
                {"id": getattr(p, "id", ""), "name": getattr(p, "name", "")}
                for p in all_principals_raw
                if getattr(p, "id", "") not in principals_with_assignments
            ]

            # Conflicts: >1 accountable at same (kpi_id, scope_dimension, scope_value)
            from collections import defaultdict
            scope_map: Dict[tuple, int] = defaultdict(int)
            for r in all_records:
                if r.role.value == "accountable":
                    scope_map[(r.kpi_id, r.scope_dimension, r.scope_value)] += 1
            kpi_name_map = {getattr(k, "id", ""): getattr(k, "name", "") for k in all_kpis_raw}
            conflicts = [
                {"kpi_id": kpi_id, "kpi_name": kpi_name_map.get(kpi_id, kpi_id), "principal_count": count}
                for (kpi_id, _, _), count in scope_map.items()
                if count > 1
            ]

            coverage_pct = covered / total_kpis if total_kpis else 1.0

            return {
                "covered_kpis": covered,
                "total_kpis": total_kpis,
                "coverage_pct": coverage_pct,
                "unassigned_kpis": unassigned,
                "principals_without_assignments": principals_without,
                "conflicts": conflicts,
            }

        except Exception as exc:
            logger.error("get_coverage error: %s", exc)
            return {
                "covered_kpis": 0,
                "total_kpis": 0,
                "coverage_pct": 0.0,
                "unassigned_kpis": [],
                "principals_without_assignments": [],
                "conflicts": [],
                "error": str(exc),
            }
