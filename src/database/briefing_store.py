"""
Supabase persistence layer for briefing_runs and briefing_tokens.

Follows the same httpx REST pattern as SituationsStore and AssessmentStore.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

from src.agents.models.pib_models import BriefingRun, BriefingRunStatus, BriefingToken, TokenType

logger = logging.getLogger(__name__)


class BriefingStore:
    """Thin async Supabase client for briefing_runs and briefing_tokens."""

    def __init__(self) -> None:
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not self.supabase_url or not self.supabase_service_key:
            logger.warning(
                "BriefingStore: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set — "
                "briefing persistence is disabled."
            )
            self.enabled = False
            return

        if httpx is None:
            logger.warning("BriefingStore: httpx not installed — briefing persistence disabled.")
            self.enabled = False
            return

        self.enabled = True
        self.headers = {
            "apikey": self.supabase_service_key,
            "Authorization": f"Bearer {self.supabase_service_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self._runs_url = f"{self.supabase_url}/rest/v1/briefing_runs"
        self._tokens_url = f"{self.supabase_url}/rest/v1/briefing_tokens"

    # ------------------------------------------------------------------
    # Briefing runs
    # ------------------------------------------------------------------

    async def insert_run(self, run: BriefingRun) -> bool:
        if not self.enabled:
            return False
        try:
            row = {
                "id": run.id,
                "principal_id": run.principal_id,
                "client_id": run.client_id,
                "assessment_run_id": run.assessment_run_id,
                "sent_at": run.sent_at.isoformat(),
                "new_situation_count": run.new_situation_count,
                "format": run.format.value,
                "email_to": run.email_to,
                "status": run.status.value,
                "error_message": run.error_message,
                "created_at": run.created_at.isoformat(),
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(self._runs_url, headers=self.headers, json=row)
                if response.status_code not in (200, 201, 204):
                    logger.warning(
                        "BriefingStore.insert_run: status %s — %s",
                        response.status_code, response.text[:200],
                    )
                    return False
            return True
        except Exception as exc:
            logger.warning("BriefingStore.insert_run failed: %s", exc)
            return False

    async def update_run_status(
        self, run_id: str, status: BriefingRunStatus, error_message: Optional[str] = None
    ) -> bool:
        if not self.enabled:
            return False
        try:
            patch = {"status": status.value}
            if error_message:
                patch["error_message"] = error_message
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    self._runs_url,
                    headers=self.headers,
                    params={"id": f"eq.{run_id}"},
                    json=patch,
                )
                return response.status_code in (200, 204)
        except Exception as exc:
            logger.warning("BriefingStore.update_run_status failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Briefing tokens
    # ------------------------------------------------------------------

    async def insert_token(self, token: BriefingToken) -> bool:
        if not self.enabled:
            return False
        try:
            row = {
                "id": token.id,
                "token": token.token,
                "token_type": token.token_type.value,
                "principal_id": token.principal_id,
                "situation_id": token.situation_id,
                "kpi_assessment_id": token.kpi_assessment_id,
                "briefing_run_id": token.briefing_run_id,
                "expires_at": token.expires_at.isoformat(),
                "created_at": token.created_at.isoformat(),
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(self._tokens_url, headers=self.headers, json=row)
                if response.status_code not in (200, 201, 204):
                    logger.warning(
                        "BriefingStore.insert_token: status %s — %s",
                        response.status_code, response.text[:200],
                    )
                    return False
            return True
        except Exception as exc:
            logger.warning("BriefingStore.insert_token failed: %s", exc)
            return False

    async def validate_and_consume_token(
        self, token_str: str
    ) -> Optional[Dict[str, Any]]:
        """
        Validate a token: must exist, not expired, not used.
        If valid, marks it as used and returns the token row.
        Returns None if invalid/expired/used.
        """
        if not self.enabled:
            return None
        try:
            now_iso = datetime.now(timezone.utc).isoformat()
            async with httpx.AsyncClient() as client:
                # Fetch token
                response = await client.get(
                    self._tokens_url,
                    headers=self.headers,
                    params={
                        "token": f"eq.{token_str}",
                        "expires_at": f"gt.{now_iso}",
                        "used_at": "is.null",
                        "select": "*",
                    },
                )
                response.raise_for_status()
                rows = json.loads(response.content) if response.content else []
                if not rows:
                    return None

                row = rows[0]

                # Mark as used
                await client.patch(
                    self._tokens_url,
                    headers=self.headers,
                    params={"id": f"eq.{row['id']}"},
                    json={"used_at": now_iso},
                )
                return row
        except Exception as exc:
            logger.warning("BriefingStore.validate_and_consume_token failed: %s", exc)
            return None
