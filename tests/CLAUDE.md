# Tests — Agent9-HERMES

## Standard Run Commands

```bash
# Unit tests:
.venv/Scripts/pytest tests/unit/ --timeout=15

# Verbose output for a specific file:
.venv/Scripts/pytest tests/unit/test_a9_market_analysis_agent.py -v --timeout=15

# Integration tests (longer timeout):
.venv/Scripts/pytest tests/integration/ --timeout=30

# Single test function:
.venv/Scripts/pytest tests/unit/test_a9_data_governance_wiring.py::test_name -v --timeout=15
```

## Directory Map

```
tests/
├── conftest.py          — shared pytest fixtures
├── unit/                — 44 files, one per agent + key components
├── integration/         — 9 files (agent-to-agent, API workflow, BigQuery)
├── e2e/                 — end-to-end workflow tests
├── mocks/               — mock_agents.py (shared mock fixtures)
├── component/           — component-level tests
└── architecture/        — architecture compliance tests
```

## Registry Factory Mock Path

Always mock as `src.registry.factory.RegistryFactory` — **not** `registry_factory` (old module name).

```python
@patch("src.registry.factory.RegistryFactory")
def test_something(mock_factory): ...
```

## Fragile Tests

- `test_sa_kpi_registry.py::test_load_kpi_registry` — mock wiring for KPI count is fragile.
  Passes but assertion on exact count may break if YAML data changes. Handle with care.

## Coverage Status (as of 2026-07-31)

- Unit tests: **733 pass**, 3 skipped — no `--ignore` flags needed
- Smoke tests: 3/3 pass
- Integration / e2e: run individually — some require live Supabase or BigQuery
- Suite is fully green — keep it that way. A single red unit test had gone unnoticed for months (`test_dpa_principal_filters` stale since the Sept 2025 Phase 10B-DGA resolver neutralization), which masked new failures on the pre-push checklist.

## Known Coverage Gaps

- Protocol compliance testing inconsistent across agents
- Agent dependency resolution not fully tested
- Registry provider lifecycle not comprehensively tested
- No UI test suite for `decision-studio-ui/` (no jest/vitest configured)
- A9_Risk_Analysis_Agent has no tests (dead code candidate)
