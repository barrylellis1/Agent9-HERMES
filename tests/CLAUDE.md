# Tests — Agent9-HERMES

## Standard Run Commands

```bash
# Unit tests (always use these exact flags):
.venv/Scripts/pytest tests/unit/ --timeout=15 \
  --ignore=tests/unit/test_a9_data_product_mcp_service_agent_unit.py

# Verbose output for a specific file:
.venv/Scripts/pytest tests/unit/test_a9_situation_awareness_agent.py -v --timeout=15

# Integration tests (longer timeout):
.venv/Scripts/pytest tests/integration/ --timeout=30

# Single test function:
.venv/Scripts/pytest tests/unit/test_a9_orchestrator_agent.py::test_name -v --timeout=15
```

## ALWAYS EXCLUDE This File

```
tests/unit/test_a9_data_product_mcp_service_agent_unit.py
```

Hangs permanently on DuckDB initialization — never terminates. Always pass
`--ignore=tests/unit/test_a9_data_product_mcp_service_agent_unit.py`.

## Directory Map

```
tests/
├── conftest.py          — shared pytest fixtures
├── unit/                — 17 files, one per agent + key components
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

## Coverage Status (as of Feb 2026)

- Unit tests: **42/42 pass**, 6 skipped
- Smoke tests: 3/3 pass
- Integration / e2e: run individually — some require live Supabase or BigQuery

## Known Coverage Gaps

- Protocol compliance testing inconsistent across agents
- Agent dependency resolution not fully tested
- Registry provider lifecycle not comprehensively tested
- No UI test suite for `decision-studio-ui/` (no jest/vitest configured)
- A9_Risk_Analysis_Agent has no tests (dead code candidate)
