"""
A9_PIB_Agent — Principal Intelligence Briefing composition and delivery.

Assembles the four PIB sections from Supabase data, generates secure tokens
for one-click actions and deep links, renders the Jinja2 HTML email template,
and sends via aiosmtplib (provider-agnostic SMTP).

SMTP configuration via env vars:
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM
    DECISION_STUDIO_URL  (default: http://localhost:5173)
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import aiosmtplib
except ImportError:
    aiosmtplib = None  # type: ignore

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:
    Environment = None  # type: ignore

from src.agents.models.pib_models import (
    BriefingConfig,
    BriefingContent,
    BriefingFormat,
    BriefingRun,
    BriefingRunStatus,
    BriefingToken,
    ManagedSituationItem,
    SituationBriefingItem,
    SolutionProgressItem,
    TokenType,
    UrgencyItem,
)
from src.database.assessment_store import AssessmentStore
from src.database.briefing_store import BriefingStore
from src.database.situations_store import SituationsStore

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"
_TOKEN_TTL_DAYS = 7


class A9_PIB_Agent:
    """
    Principal Intelligence Briefing agent.

    Composes and delivers the PIB email for a given principal + client.
    Follows the same initialization pattern as other A9 agents.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        self.orchestrator = config.get("orchestrator")
        self._assessment_store = AssessmentStore()
        self._briefing_store = BriefingStore()
        self._situations_store = SituationsStore()
        self._ds_url = os.getenv("DECISION_STUDIO_URL", "http://localhost:5173")

    # ------------------------------------------------------------------
    # Agent lifecycle (A2A protocol)
    # ------------------------------------------------------------------

    @classmethod
    async def create(cls, config: Dict[str, Any]) -> "A9_PIB_Agent":
        return cls(config)

    async def connect(self, orchestrator=None) -> None:
        if orchestrator is not None:
            self.orchestrator = orchestrator

    async def disconnect(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Primary entrypoint
    # ------------------------------------------------------------------

    async def generate_and_send(self, briefing_config: BriefingConfig) -> BriefingRun:
        """
        Compose and send the PIB for a principal + client.

        Returns the BriefingRun record with final status.
        """
        logger.info(
            "PIB: starting for principal=%s client=%s dry_run=%s",
            briefing_config.principal_id,
            briefing_config.client_id,
            briefing_config.dry_run,
        )

        # ------------------------------------------------------------------
        # 1. Resolve principal name + email from registry
        # ------------------------------------------------------------------
        principal_info = await self._resolve_principal(briefing_config.principal_id)
        email_to = briefing_config.email_to or principal_info.get("email")
        if not email_to:
            logger.error("PIB: no email address for principal %s — aborting", briefing_config.principal_id)
            raise ValueError(f"No email address for principal {briefing_config.principal_id}")

        # ------------------------------------------------------------------
        # 2. Load latest assessment run
        # ------------------------------------------------------------------
        latest_run = await self._assessment_store.get_latest_run(
            briefing_config.client_id
        )
        if latest_run is None:
            logger.warning("PIB: no completed assessment run found — sending empty briefing")

        assessment_run_id = latest_run["id"] if latest_run else None

        # ------------------------------------------------------------------
        # 3. Create BriefingRun record
        # ------------------------------------------------------------------
        briefing_run = BriefingRun(
            principal_id=briefing_config.principal_id,
            client_id=briefing_config.client_id,
            assessment_run_id=assessment_run_id,
            email_to=email_to,
            format=briefing_config.format,
            new_situation_count=latest_run.get("new_situation_count", 0) if latest_run else 0,
        )
        if not briefing_config.dry_run:
            await self._briefing_store.insert_run(briefing_run)

        # ------------------------------------------------------------------
        # 4. Assemble briefing content
        # ------------------------------------------------------------------
        content = await self._compose(briefing_config, briefing_run, principal_info, latest_run)

        if not content.has_content:
            logger.info("PIB: no content to send for principal %s — skipping", briefing_config.principal_id)
            briefing_run.status = BriefingRunStatus.SENT
            if not briefing_config.dry_run:
                await self._briefing_store.update_run_status(briefing_run.id, BriefingRunStatus.SENT)
            return briefing_run

        # ------------------------------------------------------------------
        # 5. Render HTML template
        # ------------------------------------------------------------------
        html_body = self._render_template(content)

        # ------------------------------------------------------------------
        # 6. Send email
        # ------------------------------------------------------------------
        if briefing_config.dry_run:
            logger.info("PIB [DRY RUN]: would send to %s (%d new situations)", email_to, len(content.new_situations))
            logger.info("PIB [DRY RUN]: HTML preview length = %d chars", len(html_body))
            briefing_run.status = BriefingRunStatus.SENT
        else:
            try:
                await self._send_email(email_to, content, html_body)
                briefing_run.status = BriefingRunStatus.SENT
                await self._briefing_store.update_run_status(briefing_run.id, BriefingRunStatus.SENT)
                logger.info("PIB: email sent to %s", email_to)
            except Exception as e:
                briefing_run.status = BriefingRunStatus.FAILED
                briefing_run.error_message = str(e)
                await self._briefing_store.update_run_status(
                    briefing_run.id, BriefingRunStatus.FAILED, str(e)
                )
                logger.error("PIB: email send failed: %s", e, exc_info=True)

        return briefing_run

    # ------------------------------------------------------------------
    # Composition
    # ------------------------------------------------------------------

    async def _compose(
        self,
        config: BriefingConfig,
        briefing_run: BriefingRun,
        principal_info: Dict[str, Any],
        latest_run: Optional[Dict[str, Any]],
    ) -> BriefingContent:
        """Assemble all four PIB sections."""
        content = BriefingContent(
            principal_id=config.principal_id,
            principal_name=principal_info.get("name", config.principal_id),
            principal_role=principal_info.get("role", "Principal"),
            client_id=config.client_id,
            client_name=self._format_client_name(config.client_id),
            assessment_run_id=briefing_run.assessment_run_id or "",
            briefing_format=config.format,
            decision_studio_url=config.decision_studio_url or self._ds_url,
        )

        expires_at = datetime.now(timezone.utc) + timedelta(days=_TOKEN_TTL_DAYS)

        # Section 1 + 2: New situations + urgency flags
        if latest_run:
            await self._populate_situations(
                content, config, briefing_run, latest_run, expires_at
            )

        # Section 3: Solutions in progress
        await self._populate_solutions(content, config, briefing_run, expires_at)

        # Section 4: Managed situations (delegated BY this principal)
        await self._populate_managed(content, config)

        # Section 1 addendum: Situations delegated TO this principal
        await self._populate_delegated_to_me(content, config, briefing_run, expires_at)

        return content

    async def _populate_situations(
        self,
        content: BriefingContent,
        config: BriefingConfig,
        briefing_run: BriefingRun,
        latest_run: Dict[str, Any],
        expires_at: datetime,
    ) -> None:
        """Build new situations list and urgency flags from kpi_assessments."""
        run_id = latest_run["id"]
        prev_run_id = latest_run.get("previous_run_id")

        # Load all DETECTED assessments for this run
        detected = await self._assessment_store.get_detected_kpi_ids(run_id)
        prev_detected: set = set()
        if prev_run_id:
            prev_detected = set(await self._assessment_store.get_detected_kpi_ids(prev_run_id))

        # Load full assessment rows to get names/descriptions
        assessments = await self._load_assessments(run_id)

        # Load open situations from situations table for descriptions.
        # Index by kpi_name (primary) and id (fallback) — no principal_id filter
        # because the column may not be populated by the offline monitor.
        raw_situations = await self._situations_store.get_open_situations(principal_id=None)
        open_situations: dict = {}
        for s in raw_situations:
            if s.get("kpi_name"):
                open_situations[s["kpi_name"]] = s
            if s.get("id"):
                open_situations.setdefault(s["id"], s)

        for ka in assessments:
            if ka.get("status") != "detected":
                continue

            kpi_id = ka.get("kpi_id", "")
            kpi_name = ka.get("kpi_name") or kpi_id
            is_new = kpi_id not in prev_detected
            sit_data = open_situations.get(kpi_name, {})

            # Generate tokens
            deep_link_token = await self._create_token(
                TokenType.DEEP_LINK, config.principal_id, kpi_id, ka.get("id"), briefing_run.id, expires_at, config.dry_run
            )
            delegate_token = await self._create_token(
                TokenType.DELEGATE, config.principal_id, kpi_id, ka.get("id"), briefing_run.id, expires_at, config.dry_run
            )
            request_info_token = await self._create_token(
                TokenType.REQUEST_INFO, config.principal_id, kpi_id, ka.get("id"), briefing_run.id, expires_at, config.dry_run
            )

            severity_score = ka.get("severity") or 0.0
            severity_label = self._severity_label(severity_score)

            item = SituationBriefingItem(
                situation_id=sit_data.get("id", kpi_id),
                kpi_assessment_id=ka.get("id", ""),
                kpi_name=kpi_name,
                severity=severity_label,
                severity_score=severity_score,
                description=self._clean_description(sit_data.get("description") or sit_data.get("title") or f"{kpi_name} requires attention"),
                deviation_summary="",  # cleaned description already contains the deviation
                current_value=ka.get("kpi_value"),
                is_new=is_new,
                deep_link_token=deep_link_token,
                delegate_token=delegate_token,
                request_info_token=request_info_token,
            )

            if is_new:
                content.new_situations.append(item)

            # Urgency: situation was in prev run too → it's been open at least 1 cycle
            # A rough proxy: check weeks_open from situations table created_at
            created_at_str = sit_data.get("created_at")
            if created_at_str and not is_new:
                try:
                    created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                    weeks_open = int((datetime.now(timezone.utc) - created_at).days / 7)
                    if weeks_open >= config.urgency_threshold_weeks:
                        content.urgency_flags.append(UrgencyItem(
                            situation_id=sit_data.get("id", kpi_id),
                            kpi_name=kpi_name,
                            severity=severity_label,
                            weeks_open=weeks_open,
                            deep_link_token=deep_link_token,
                        ))
                except Exception:
                    pass

    async def _populate_solutions(
        self,
        content: BriefingContent,
        config: BriefingConfig,
        briefing_run: BriefingRun,
        expires_at: datetime,
    ) -> None:
        """Pull in-progress solutions from Value Assurance."""
        try:
            va_solutions = await self._load_va_solutions(config.principal_id, config.client_id)
            for sol in va_solutions:
                approve_token = None
                if sol.get("status", "").upper() in ("ACCEPTED", "PENDING_APPROVAL"):
                    approve_token = await self._create_token(
                        TokenType.APPROVE, config.principal_id,
                        sol.get("situation_id", sol.get("id", "")),
                        None, briefing_run.id, expires_at, config.dry_run
                    )
                raw_kpi = sol.get("kpi_id") or sol.get("kpi_name", "")
                content.solutions_in_progress.append(SolutionProgressItem(
                    solution_id=sol.get("id", ""),
                    solution_title=sol.get("solution_description") or sol.get("option_title") or "Proposed Solution",
                    kpi_name=self._kpi_id_to_display(raw_kpi),
                    status=sol.get("status", "measuring"),
                    expected_impact_lower=sol.get("expected_impact_lower"),
                    expected_impact_upper=sol.get("expected_impact_upper"),
                    accepted_at=self._parse_dt(sol.get("approved_at") or sol.get("accepted_at")),
                    approve_token=approve_token,
                ))
        except Exception as e:
            logger.warning("PIB: VA solutions load failed (non-fatal): %s", e)

    async def _populate_managed(
        self, content: BriefingContent, config: BriefingConfig
    ) -> None:
        """Pull delegated situations from situation_actions."""
        try:
            actions = await self._load_situation_actions(config.principal_id)
            for action in actions:
                target_id = action.get("target_principal_id")
                # Resolve delegate principal ID to display name
                delegated_to_name: Optional[str] = None
                if target_id:
                    delegated_to_name = await self._resolve_principal_name(target_id)
                content.managed_situations.append(ManagedSituationItem(
                    situation_id=action.get("situation_id", ""),
                    kpi_name=action.get("situation_id", ""),  # situation_id stores kpi_name
                    action_type=action.get("action_type", ""),
                    action_taken_at=self._parse_dt(action.get("created_at")) or datetime.utcnow(),
                    delegated_to=delegated_to_name or target_id,
                ))
        except Exception as e:
            logger.warning("PIB: managed situations load failed (non-fatal): %s", e)

    async def _populate_delegated_to_me(
        self,
        content: BriefingContent,
        config: BriefingConfig,
        briefing_run: BriefingRun,
        expires_at: datetime,
    ) -> None:
        """Add situations delegated TO this principal as new situation items."""
        try:
            delegated = await self._load_delegated_to_principal(config.principal_id)
            for action in delegated:
                kpi_name = action.get("situation_id", "")
                delegated_by = action.get("principal_id", "")
                delegated_by_name = await self._resolve_principal_name(delegated_by)

                # Generate tokens for the delegate to act on these
                deep_link_token = await self._create_token(
                    TokenType.DEEP_LINK, config.principal_id, kpi_name,
                    None, briefing_run.id, expires_at, config.dry_run,
                )

                item = SituationBriefingItem(
                    situation_id=kpi_name,
                    kpi_assessment_id="",
                    kpi_name=kpi_name,
                    severity="high",
                    severity_score=0.8,
                    description=f"Assigned to you by {delegated_by_name}",
                    deviation_summary="",
                    is_new=True,
                    deep_link_token=deep_link_token,
                )
                content.new_situations.append(item)
        except Exception as e:
            logger.warning("PIB: delegated-to-me load failed (non-fatal): %s", e)

    async def _resolve_principal_name(self, principal_id: str) -> str:
        """Resolve a principal ID to a display name. Fallback to the ID itself."""
        if not principal_id or not self.orchestrator:
            return principal_id
        try:
            resp = await self.orchestrator.execute_agent_method(
                "A9_Principal_Context_Agent",
                "get_principal_context_by_id",
                {"principal_id": principal_id},
            )
            if isinstance(resp, dict):
                profile = resp.get("profile") or {}
                return profile.get("name") or principal_id
        except Exception:
            pass
        return principal_id

    async def _load_delegated_to_principal(self, principal_id: str) -> List[Dict[str, Any]]:
        """Load situations delegated TO this principal (they are the target)."""
        import httpx as _httpx
        import json
        supabase_url = os.getenv("SUPABASE_URL")
        service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not supabase_url or not service_key:
            return []
        try:
            headers = {
                "apikey": service_key,
                "Authorization": f"Bearer {service_key}",
                "Accept": "application/json",
            }
            async with _httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{supabase_url}/rest/v1/situation_actions",
                    headers=headers,
                    params={
                        "target_principal_id": f"eq.{principal_id}",
                        "action_type": "eq.delegate",
                        "select": "*",
                        "order": "created_at.desc",
                        "limit": "10",
                    },
                )
                if resp.status_code == 200 and resp.content:
                    return json.loads(resp.content)
                return []
        except Exception as e:
            logger.warning("PIB: load_delegated_to_principal failed: %s", e)
            return []

    # ------------------------------------------------------------------
    # Token generation
    # ------------------------------------------------------------------

    async def _create_token(
        self,
        token_type: TokenType,
        principal_id: str,
        situation_id: str,
        kpi_assessment_id: Optional[str],
        briefing_run_id: str,
        expires_at: datetime,
        dry_run: bool,
    ) -> Optional[str]:
        """Generate and persist a single-use token. Returns the token UUID string."""
        import uuid
        token_value = str(uuid.uuid4())
        token = BriefingToken(
            token=token_value,
            token_type=token_type,
            principal_id=principal_id,
            situation_id=situation_id,
            kpi_assessment_id=kpi_assessment_id,
            briefing_run_id=briefing_run_id,
            expires_at=expires_at,
        )
        if not dry_run:
            await self._briefing_store.insert_token(token)
        return token_value

    # ------------------------------------------------------------------
    # Email rendering + delivery
    # ------------------------------------------------------------------

    def _render_template(self, content: BriefingContent) -> str:
        if Environment is None:
            logger.warning("PIB: Jinja2 not installed — falling back to plain text summary")
            return self._plain_text_fallback(content)

        env = Environment(
            loader=FileSystemLoader(str(_TEMPLATES_DIR)),
            autoescape=select_autoescape(["html"]),
        )
        template = env.get_template("pib_briefing.html")
        return template.render(content=content)

    def _plain_text_fallback(self, content: BriefingContent) -> str:
        lines = [
            f"Principal Intelligence Briefing — {content.client_name}",
            f"{content.principal_name} ({content.principal_role})",
            f"Generated: {content.generated_at.strftime('%Y-%m-%d')}",
            "",
            f"NEW SITUATIONS ({len(content.new_situations)}):",
        ]
        for s in content.new_situations:
            lines.append(f"  [{s.severity.upper()}] {s.kpi_name} — {s.description}")
        lines += ["", f"SOLUTIONS IN PROGRESS ({len(content.solutions_in_progress)}):"]
        for sol in content.solutions_in_progress:
            lines.append(f"  {sol.solution_title} — {sol.status}")
        return "\n".join(lines)

    async def _send_email(
        self, email_to: str, content: BriefingContent, html_body: str
    ) -> None:
        if aiosmtplib is None:
            raise RuntimeError(
                "aiosmtplib is not installed. Run: pip install aiosmtplib"
            )

        smtp_host = os.getenv("SMTP_HOST")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")
        smtp_from = os.getenv("SMTP_FROM", smtp_user or "briefing@decision-studios.com")

        if not smtp_host:
            raise RuntimeError("SMTP_HOST env var not set — cannot send PIB email")

        subject = (
            f"Intelligence Briefing — {content.client_name} "
            f"({len(content.new_situations)} new situation{'s' if len(content.new_situations) != 1 else ''})"
        )

        msg = EmailMessage()
        msg["From"] = smtp_from
        msg["To"] = email_to
        msg["Subject"] = subject
        msg.set_content(self._plain_text_fallback(content))
        msg.add_alternative(html_body, subtype="html")

        await aiosmtplib.send(
            msg,
            hostname=smtp_host,
            port=smtp_port,
            username=smtp_user,
            password=smtp_password,
            start_tls=True,
        )

    # ------------------------------------------------------------------
    # Data loaders
    # ------------------------------------------------------------------

    async def _resolve_principal(self, principal_id: str) -> Dict[str, Any]:
        """Fetch principal name, role, email from registry via Orchestrator."""
        if self.orchestrator is None:
            return {"name": principal_id, "role": "Principal", "email": None}
        try:
            resp = await self.orchestrator.execute_agent_method(
                "A9_Principal_Context_Agent",
                "get_principal_context_by_id",
                {"principal_id": principal_id},
            )
            if isinstance(resp, dict):
                profile = resp.get("profile") or {}
                ctx = resp.get("context") or resp.get("principal_context") or resp
                return {
                    "name": profile.get("name") or ctx.get("name") or principal_id,
                    "role": profile.get("title") or ctx.get("role") or "Principal",
                    "email": profile.get("email") or ctx.get("email"),
                }
            else:
                ctx = {}
            return {
                "name": principal_id,
                "role": "Principal",
                "email": None,
            }
        except Exception as e:
            logger.warning("PIB: principal lookup failed: %s", e)
            return {"name": principal_id, "role": "Principal", "email": None}

    async def _load_assessments(self, run_id: str) -> List[Dict[str, Any]]:
        """Load all KPI assessment rows for a run via Supabase REST."""
        import httpx as _httpx
        import json
        supabase_url = os.getenv("SUPABASE_URL")
        service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not supabase_url or not service_key:
            return []
        try:
            headers = {
                "apikey": service_key,
                "Authorization": f"Bearer {service_key}",
                "Accept": "application/json",
            }
            async with _httpx.AsyncClient() as client:
                response = await client.get(
                    f"{supabase_url}/rest/v1/kpi_assessments",
                    headers=headers,
                    params={"run_id": f"eq.{run_id}", "select": "*"},
                )
                response.raise_for_status()
                return json.loads(response.content) if response.content else []
        except Exception as e:
            logger.warning("PIB: load_assessments failed: %s", e)
            return []

    async def _load_va_solutions(
        self, principal_id: str, client_id: str
    ) -> List[Dict[str, Any]]:
        """Load active VA solutions (MEASURING or PENDING_APPROVAL only)."""
        import httpx as _httpx
        import json
        supabase_url = os.getenv("SUPABASE_URL")
        service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not supabase_url or not service_key:
            return []
        try:
            headers = {
                "apikey": service_key,
                "Authorization": f"Bearer {service_key}",
                "Accept": "application/json",
            }
            active_solutions = []
            async with _httpx.AsyncClient() as client:
                for status_val in ("MEASURING", "PENDING_APPROVAL"):
                    response = await client.get(
                        f"{supabase_url}/rest/v1/value_assurance_solutions",
                        headers=headers,
                        params={
                            "status": f"eq.{status_val}",
                            "select": "*",
                            "order": "approved_at.desc",
                            "limit": "5",
                        },
                    )
                    if response.status_code == 200 and response.content:
                        active_solutions += json.loads(response.content)
            return active_solutions
        except Exception as e:
            logger.warning("PIB: load_va_solutions failed: %s", e)
            return []

    async def _load_situation_actions(self, principal_id: str) -> List[Dict[str, Any]]:
        """Load recent delegate actions for this principal."""
        import httpx as _httpx
        import json
        supabase_url = os.getenv("SUPABASE_URL")
        service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not supabase_url or not service_key:
            return []
        try:
            headers = {
                "apikey": service_key,
                "Authorization": f"Bearer {service_key}",
                "Accept": "application/json",
            }
            async with _httpx.AsyncClient() as client:
                delegate_resp = await client.get(
                    f"{supabase_url}/rest/v1/situation_actions",
                    headers=headers,
                    params={
                        "principal_id": f"eq.{principal_id}",
                        "action_type": "eq.delegate",
                        "select": "*",
                        "order": "created_at.desc",
                        "limit": "10",
                    },
                )
                if delegate_resp.status_code == 200 and delegate_resp.content:
                    return json.loads(delegate_resp.content)
                return []
        except Exception as e:
            logger.warning("PIB: load_situation_actions failed: %s", e)
            return []

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _severity_label(score: float) -> str:
        if score >= 0.8:
            return "critical"
        elif score >= 0.6:
            return "high"
        elif score >= 0.4:
            return "medium"
        return "low"

    @staticmethod
    def _clean_description(desc: str) -> str:
        """Strip system jargon from SA descriptions for executive readability."""
        import re
        # Remove "(threshold=red)", "(within green threshold)", etc.
        desc = re.sub(r'\s*\(threshold=\w+\)', '', desc)
        desc = re.sub(r'\s*\(within \w+ threshold\)', '', desc)
        # Replace "vs baseline" with "vs prior year" for clarity
        desc = desc.replace('vs baseline', 'vs prior year')
        return desc.strip()

    @staticmethod
    def _extract_deviation(sit_data: Dict[str, Any]) -> str:
        """
        Extract a concise deviation summary distinct from the description.
        Returns empty string if nothing useful — template skips it when empty.
        """
        payload = sit_data.get("full_payload") or {}
        if isinstance(payload, str):
            import json as _j
            try:
                payload = _j.loads(payload)
            except Exception:
                payload = {}
        # Prefer a numeric kpi_value + percent_change from the full payload
        pct = payload.get("kpi_value", {})
        if isinstance(pct, dict):
            change = pct.get("percent_change")
            if change is not None:
                direction = "decreased" if change < 0 else "increased"
                return f"{direction} {abs(change):.1f}% vs prior year"
        return ""

    _CLIENT_NAMES = {
        "lubricants": "Lubricants Business",
        "bicycle": "Bicycle Co.",
    }

    @classmethod
    def _format_client_name(cls, client_id: str) -> str:
        return cls._CLIENT_NAMES.get(client_id.lower(), client_id.replace("_", " ").title())

    @staticmethod
    def _kpi_id_to_display(kpi_id: str) -> str:
        """Convert a registry KPI ID like 'lub_gross_margin_pct' to 'Gross Margin Pct'."""
        # Strip known prefixes
        for prefix in ("lub_", "fi_", "bic_"):
            if kpi_id.startswith(prefix):
                kpi_id = kpi_id[len(prefix):]
                break
        return kpi_id.replace("_", " ").title()

    @staticmethod
    def _parse_dt(value: Any) -> Optional[datetime]:
        if value is None:
            return None
        try:
            if isinstance(value, datetime):
                return value
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except Exception:
            return None
