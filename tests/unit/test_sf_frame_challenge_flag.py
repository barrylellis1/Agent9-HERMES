"""stage1_allow_frame_challenge — step 1 of the 2026-08-14 evidence-scope test.

WHY THIS FLAG EXISTS
---------------------
The production Stage 1 task statement requires every option to name the
"primary driver of THIS KPI situation" with a recovery_range "proportional to
the observed variance". That wording cannot express a portfolio/exit option —
"stop discounting into this category" doesn't recover a KPI, it changes what's
being measured. Across 21 real-run options (7 arms), 0 challenged the frame.

This flag adds PERMISSION for Stage 1 to propose an alternative-frame option
when the evidence warrants it — it does not require one, and does not remove
task items 1-4. Default False = byte-identical to pre-2026-08-14 production
behaviour, verified by test_default_task_text_is_byte_identical_to_baseline
below.
"""

import inspect

from src.agents.new import a9_solution_finder_agent as sf_mod
from src.agents.agent_config_models import A9_Solution_Finder_Agent_Config


def test_flag_defaults_to_false():
    """Off by default — an existing deployment's behaviour must not shift on upgrade."""
    cfg = A9_Solution_Finder_Agent_Config()  # arch-allow-agent-ctor — config model, not an agent
    assert cfg.stage1_allow_frame_challenge is False


def test_default_task_text_is_byte_identical_to_baseline():
    """The `else` branch (flag off) must be the exact string the 21-option baseline ran.

    Guards against the variant branch's addition accidentally altering the
    control arm too — the failure mode that has confounded three prior
    experiments in this file's sibling tests.
    """
    src = inspect.getsource(sf_mod)
    baseline_task = (
        "1. Form ONE specific hypothesis about the primary driver of this KPI situation\\n\"\n"
        '                                        "2. Propose ONE actionable intervention with a distinct mechanism\\n"'
    )
    assert baseline_task in src, (
        "the unconditional (flag-off) Stage 1 task text has changed — re-baseline "
        "before comparing against it"
    )
    # And the off-branch must NOT contain the new permission clause.
    off_branch_start = src.index("                                else:\n"
                                  "                                    _s1_task = (\n"
                                  f'                                        f"As {{p.name}}, apply your methodology to:\\n"')
    off_branch = src[off_branch_start:off_branch_start + 1600]
    assert "ALTERNATIVE FRAME" not in off_branch


def test_variant_branch_grants_permission_not_a_requirement():
    """The new clause must be phrased as optional — 'MAY', not 'MUST'."""
    src = inspect.getsource(sf_mod)
    idx = src.index("ALTERNATIVE FRAME")
    clause = src[idx: idx + 1200]

    assert "MAY instead propose" in clause
    assert "permission, not a requirement" in clause


def test_variant_branch_is_reachable_only_via_the_config_flag():
    src = inspect.getsource(sf_mod)
    assert 'getattr(self.config, "stage1_allow_frame_challenge", False)' in src


def test_orchestrator_wires_the_env_flag_at_agent_creation():
    """Same protocol as SF_CAUSAL_MAX_HOPS / SF_ENABLE_CAUSAL_GROUNDING — config
    is read once at agent creation, so an experiment arm needs a restart, and
    the arm must be confirmed from the run's own payload, never the shell env."""
    import inspect as _inspect
    from src.agents.new import a9_orchestrator_agent as orch_mod

    src = _inspect.getsource(orch_mod)
    assert "SF_STAGE1_ALLOW_FRAME_CHALLENGE" in src
    assert '"stage1_allow_frame_challenge":' in src
