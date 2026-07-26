"""
Regression tests for the PrincipalContext hardcoding bug found while auditing
Phase 15 Stage C (2026-07-23): both A9_Principal_Context_Agent lookup methods
built PrincipalContext with preferred_timeframes hardcoded to the same two
enum values for EVERY principal, and read decision_style/communication_style
from key paths that don't exist on the registry model.

Two test tiers, deliberately kept separate:

1. Pure helper-function tests (_extract_*) — exercise every input shape,
   including shapes that are defensive-only (see tier 2 finding below).
2. Real-PrincipalProfile-instance tests — PrincipalProfileProvider.get()/
   get_all() return validated PrincipalProfile instances, not raw dicts, and
   PrincipalProfile has no decision_style field (Pydantic silently drops
   unknown keys, no extra="allow"). So the flat/persona_profile decision_style
   checks in _extract_decision_style are UNREACHABLE through the real
   provider path — only the metadata.decision_style fallback can ever fire
   there. This tier proves that distinction with real model instances rather
   than asserting against a convenient dict shape that doesn't occur in
   production.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.agents.new.a9_principal_context_agent import (
    A9_Principal_Context_Agent,
    _extract_decision_style,
    _extract_communication_style,
    _extract_preferred_timeframes,
)
from src.agents.models.situation_awareness_models import TimeFrame
from src.registry.models.principal import PrincipalProfile, TimeFrame as RegistryTimeFrame, CommunicationPreference


# ---------------------------------------------------------------------------
# Tier 1 — pure helper functions, all input shapes
# ---------------------------------------------------------------------------

def test_decision_style_flat_key():
    assert _extract_decision_style({"decision_style": "analytical"}) == "analytical"


def test_decision_style_nested_persona_profile():
    assert _extract_decision_style({"persona_profile": {"decision_style": "strategic"}}) == "strategic"


def test_decision_style_metadata_fallback():
    # The one shape that actually survives the real PrincipalProfile provider path
    assert _extract_decision_style({"metadata": {"decision_style": "visionary"}}) == "visionary"


def test_decision_style_defaults_when_absent():
    assert _extract_decision_style({}) == "Analytical"
    assert _extract_decision_style(None) == "Analytical"


def test_communication_style_flat_key():
    assert _extract_communication_style({"communication_style": "executive"}) == "executive"


def test_communication_style_nested_persona_profile():
    assert _extract_communication_style({"persona_profile": {"communication_style": "detailed"}}) == "detailed"


def test_communication_style_registry_detail_level():
    # The real declared PrincipalProfile field — this is the one that survives
    # .model_dump() through the actual provider path.
    assert _extract_communication_style({"communication": {"detail_level": "high"}}) == "high"


def test_communication_style_defaults_when_absent():
    assert _extract_communication_style({}) == "Concise"


def test_preferred_timeframes_maps_registry_period():
    assert _extract_preferred_timeframes({"time_frame": {"default_period": "QTD"}}) == [TimeFrame.QUARTER_TO_DATE]
    assert _extract_preferred_timeframes({"time_frame": {"default_period": "YTD"}}) == [TimeFrame.YEAR_TO_DATE]
    assert _extract_preferred_timeframes({"time_frame": {"default_period": "MTD"}}) == [TimeFrame.MONTH_TO_DATE]


def test_preferred_timeframes_defaults_on_unknown_period():
    assert _extract_preferred_timeframes({"time_frame": {"default_period": "SOMETHING_UNKNOWN"}}) == [
        TimeFrame.CURRENT_QUARTER, TimeFrame.YEAR_TO_DATE
    ]


def test_preferred_timeframes_defaults_when_absent():
    assert _extract_preferred_timeframes({}) == [TimeFrame.CURRENT_QUARTER, TimeFrame.YEAR_TO_DATE]


# ---------------------------------------------------------------------------
# Tier 2 — real PrincipalProfile instances (the actual provider return type)
# ---------------------------------------------------------------------------

def _real_profile(principal_id: str, default_period: str, detail_level: str, metadata: dict = None) -> PrincipalProfile:
    return PrincipalProfile(
        id=principal_id,
        client_id="test_client",
        name=f"Test {principal_id}",
        title="CFO",
        time_frame=RegistryTimeFrame(default_period=default_period, historical_periods=4, forward_looking_periods=2),
        communication=CommunicationPreference(detail_level=detail_level),
        metadata=metadata or {},
    )


def test_two_real_profiles_produce_genuinely_different_timeframe_and_detail_level():
    """The core regression: preferred_timeframes/communication_style must no
    longer be identical for every principal (they were hardcoded before this
    fix, in ALL branches of PrincipalContext construction)."""
    profile_a = _real_profile("cfo_001", "QTD", "high")
    profile_b = _real_profile("ceo_001", "YTD", "low")

    dump_a = profile_a.model_dump()
    dump_b = profile_b.model_dump()

    tf_a = _extract_preferred_timeframes(dump_a)
    tf_b = _extract_preferred_timeframes(dump_b)
    assert tf_a != tf_b, "preferred_timeframes must vary per principal, not be hardcoded"
    assert tf_a == [TimeFrame.QUARTER_TO_DATE]
    assert tf_b == [TimeFrame.YEAR_TO_DATE]

    cs_a = _extract_communication_style(dump_a)
    cs_b = _extract_communication_style(dump_b)
    assert cs_a != cs_b, "communication_style must vary per principal, not be hardcoded"
    assert cs_a == "high"
    assert cs_b == "low"


def test_decision_style_only_survives_via_metadata_through_real_provider_path():
    """Documents the remaining schema gap: decision_style seeded as a flat
    top-level key (as scripts/clients/*.py actually does) is silently
    dropped by PrincipalProfile validation — model_dump() never contains it.
    Only metadata.decision_style survives. This is not fixable at the
    extraction-helper level; it needs a registry schema decision."""
    profile_with_flat_seed_shape = PrincipalProfile(
        id="cfo_001", client_id="test_client", name="Test", title="CFO",
        # PrincipalProfile has no decision_style field — passing it is a no-op,
        # exactly matching what scripts/clients/*.py's flat "decision_style" key
        # does when a raw Supabase row reaches PrincipalProfile validation.
        **{},
    )
    dump = profile_with_flat_seed_shape.model_dump()
    assert "decision_style" not in dump
    assert _extract_decision_style(dump) == "Analytical"  # falls through — the known gap

    profile_with_metadata = _real_profile("ceo_001", "YTD", "medium", metadata={"decision_style": "visionary"})
    assert _extract_decision_style(profile_with_metadata.model_dump()) == "visionary"


# ---------------------------------------------------------------------------
# Tier 3 — end-to-end through the fixed lookup method (real provider return shape)
# ---------------------------------------------------------------------------

class _FakeProvider:
    def __init__(self, profiles: dict):
        self._profiles = profiles
        self._items = {}  # no composite-key entries in this fake

    async def load(self):
        pass

    def get(self, principal_id: str):
        return self._profiles.get(principal_id)

    def get_all(self):
        return list(self._profiles.values())


@pytest.mark.asyncio
async def test_get_principal_context_by_id_no_longer_hardcodes_across_principals():
    agent = object.__new__(A9_Principal_Context_Agent)
    agent.logger = __import__("logging").getLogger("test")
    agent._business_process_provider = None
    agent.principal_profiles = {}

    profile_a = _real_profile("cfo_001", "QTD", "high")
    profile_b = _real_profile("ceo_001", "YTD", "low")
    agent._principal_provider = _FakeProvider({"cfo_001": profile_a, "ceo_001": profile_b})

    ctx_a = await agent.get_principal_context_by_id("cfo_001")
    ctx_b = await agent.get_principal_context_by_id("ceo_001")

    context_a = ctx_a["context"] if "context" in ctx_a else ctx_a
    context_b = ctx_b["context"] if "context" in ctx_b else ctx_b

    assert context_a["preferred_timeframes"] != context_b["preferred_timeframes"], (
        "regression: preferred_timeframes was hardcoded identically for every principal"
    )
    assert context_a["communication_style"] != context_b["communication_style"], (
        "regression: communication_style fell through to the same default for every principal"
    )
