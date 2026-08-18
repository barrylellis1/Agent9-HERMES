"""Every flag /healthz reports must actually reach the agent that reads it.

WHY THIS FILE EXISTS
--------------------
/healthz was extended to report gated feature state, precisely so "I set the
flag" and "the running system has the flag" could stop being different things.
It then reported `SF_USE_STRUCTURED_OUTPUT` — a variable **nothing read**.

The config field existed on `A9_Solution_Finder_Agent_Config` and the agent had
two call sites consuming it, but the orchestrator never populated it, so it was
pinned to its Pydantic default of False and no deployment could turn it on.
Setting the variable would have made /healthz report `true` for a flag the agent
never saw — reintroducing the exact false confidence the endpoint was added to
remove, with the endpoint itself as the source.

This test closes the loop: a flag is reported ONLY if something consumes it.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "src" / "api" / "main.py"
ORCHESTRATOR = ROOT / "src" / "agents" / "new" / "a9_orchestrator_agent.py"


def _reported_flags() -> list[str]:
    block = re.search(r"_REPORTED_FLAGS\s*=\s*\((.*?)\)", MAIN.read_text(encoding="utf-8"), re.S)
    assert block, "_REPORTED_FLAGS not found in src/api/main.py"
    return re.findall(r'"([A-Z0-9_]+)"', block.group(1))


class TestReportedFlagsAreConsumed:
    @pytest.fixture(scope="class")
    def orchestrator_src(self) -> str:
        return ORCHESTRATOR.read_text(encoding="utf-8")

    def test_there_is_something_to_check(self):
        assert _reported_flags(), "no flags reported — this test would pass vacuously"

    @pytest.mark.parametrize("flag", _reported_flags())
    def test_each_reported_flag_is_read_somewhere(self, flag, orchestrator_src):
        """Reporting a flag nobody reads is worse than not reporting it.

        A reader trusts the endpoint precisely because it is meant to describe
        the running system rather than an intention.
        """
        assert f'os.getenv("{flag}"' in orchestrator_src, (
            f"/healthz reports {flag}, but the orchestrator never reads it. Either wire "
            f"it into the agent config or stop reporting it — a flag that is displayed "
            f"but unread makes the endpoint lie in the one direction it exists to prevent."
        )

    def test_the_previously_unwired_flag_is_now_wired(self, orchestrator_src):
        """Pins the specific gap so it cannot quietly return."""
        assert '"use_structured_output": os.getenv("SF_USE_STRUCTURED_OUTPUT"' in orchestrator_src

    @pytest.mark.parametrize("flag", _reported_flags())
    def test_each_flag_defaults_to_off(self, flag, orchestrator_src):
        """Gated features must be opt-in.

        A default of "true" would turn a flag on everywhere the variable is simply
        absent — which is every environment nobody has touched yet.
        """
        m = re.search(rf'os\.getenv\("{flag}",\s*"([^"]*)"\)', orchestrator_src)
        assert m, f"{flag} is read without an explicit default"
        assert m.group(1).lower() == "false", f"{flag} defaults to {m.group(1)!r}, expected 'false'"


class TestConfigFieldsExistForWiredFlags:
    def test_use_structured_output_is_a_real_config_field(self):
        # The compliance regex matches any A9_-prefixed symbol and cannot tell a
        # config model from an agent; the token must sit on the violating line.
        from src.agents.agent_config_models import A9_Solution_Finder_Agent_Config  # noqa: PLC0415
        cfg = A9_Solution_Finder_Agent_Config()  # arch-allow-agent-ctor — config model, not an agent
        assert cfg.use_structured_output is False
        enabled = A9_Solution_Finder_Agent_Config(use_structured_output=True)  # arch-allow-agent-ctor — config model, not an agent
        assert enabled.use_structured_output is True

    def test_enable_framing_gate_is_a_real_config_field(self):
        from src.agents.agent_config_models import A9_Deep_Analysis_Agent_Config  # noqa: PLC0415
        cfg = A9_Deep_Analysis_Agent_Config()  # arch-allow-agent-ctor — config model, not an agent
        assert cfg.enable_framing_gate is False
        enabled = A9_Deep_Analysis_Agent_Config(enable_framing_gate=True)  # arch-allow-agent-ctor — config model, not an agent
        assert enabled.enable_framing_gate is True

    def test_da_enable_framing_gate_is_read_in_the_real_api_server_path(self):
        """DA is created eagerly at server startup (src/api/runtime.py), unlike
        SF's lazily-created-on-first-call pattern in a9_orchestrator_agent.py.
        The parametrized test above only proves the flag is read SOMEWHERE
        (a9_orchestrator_agent.py, exercised by tests/conftest.py and the
        legacy decision_studio.py Streamlit app) — this pins the specific
        file the production API server (started via
        restart_decision_studio_ui.ps1) actually goes through, so the gap
        this whole file exists to catch cannot reopen one file over."""
        runtime_src = (
            Path(__file__).resolve().parents[2] / "src" / "api" / "runtime.py"
        ).read_text(encoding="utf-8")
        assert 'os.getenv("DA_ENABLE_FRAMING_GATE", "false")' in runtime_src
