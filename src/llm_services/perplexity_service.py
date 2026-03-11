"""
Perplexity AI Service for Agent9-HERMES

Provides web-search-augmented query capability via the Perplexity API.
Uses the 'sonar' model family which injects live web results into the response.

Falls back gracefully when PERPLEXITY_API_KEY is not set — returns empty results
so the Market Analysis Agent can continue with LLM-only synthesis.
"""

import logging
import os
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
# sonar is Perplexity's search-enabled model; override via PERPLEXITY_MODEL env var
PERPLEXITY_MODEL = os.getenv("PERPLEXITY_MODEL", "sonar")


class PerplexityService:
    """
    Wrapper around the Perplexity AI API.

    Lifecycle:
        service = PerplexityService()
        await service.connect()
        result = await service.search("query text", max_results=5)
        await service.disconnect()

    Result schema:
        {
            "answer": str,           # Perplexity's synthesised answer
            "citations": list[dict], # Raw citation objects from the API
            "error": str | None,     # Present only when a call-level error occurred
        }
    """

    def __init__(self) -> None:
        self.api_key: str = os.getenv("PERPLEXITY_API_KEY", "")
        self._client: Optional[httpx.AsyncClient] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        """Open the shared HTTP client."""
        self._client = httpx.AsyncClient(timeout=30.0)
        logger.debug("PerplexityService: HTTP client opened")

    async def disconnect(self) -> None:
        """Close and release the shared HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.debug("PerplexityService: HTTP client closed")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Run a web-search query via Perplexity and return a structured result.

        Args:
            query:       Natural-language search query.
            max_results: Hint for how many citations to request (best-effort).

        Returns:
            dict with keys:
                - ``answer``    (str)  — Perplexity's synthesised answer text
                - ``citations`` (list) — List of citation dicts from the API
                - ``error``     (str)  — Only present when a call-level error occurred
        """
        if not self.api_key:
            logger.warning(
                "PerplexityService: PERPLEXITY_API_KEY not set — returning empty market signals"
            )
            return {"answer": "", "citations": []}

        if self._client is None:
            await self.connect()

        payload: Dict[str, Any] = {
            "model": PERPLEXITY_MODEL,
            "messages": [{"role": "user", "content": query}],
            "max_tokens": 1024,
            "return_citations": True,
        }

        try:
            response = await self._client.post(  # type: ignore[union-attr]
                PERPLEXITY_API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data: Dict[str, Any] = response.json()  # pydantic-lint: allow — httpx Response.json(), not Pydantic

            answer: str = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            citations: List[Any] = data.get("citations", [])
            logger.info(
                "PerplexityService: search complete — %d citations returned", len(citations)
            )
            return {"answer": answer, "citations": citations}

        except Exception as exc:
            logger.error("PerplexityService: API error — %s", exc)
            return {"answer": "", "citations": [], "error": str(exc)}
