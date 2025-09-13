# PR Title

Short summary of the change and the problem it solves.

## Checklist

- [ ] PRD(s) updated before implementation
  - [ ] `docs/prd/services/a9_data_product_mcp_service_prd.md` (if MCP changes)
  - [ ] `docs/prd/agents/a9_data_product_agent_prd.md` (if agent changes)
- [ ] Agent card/config models in sync (Agent9 Code/Config Sync Rule)
  - [ ] `src/agents/new/agent_config_models.py`
  - [ ] `src/agents/new/cards/` (relevant card)
- [ ] Architecture boundaries respected
  - [ ] No direct SQL/DB/CSV/pandas in `src/agents/**`
  - [ ] Data access in agents goes through `src/agents/clients/a9_mcp_client.py`
  - [ ] No direct agent instantiation in `tests/**` (orchestrator-driven only)
- [ ] Architecture tests pass locally
  - [ ] `pytest tests/architecture/test_architecture_compliance.py -q`
- [ ] Pre-commit hook executed
  - [ ] `pre-commit run --all-files` shows no architecture violations
- [ ] Logging & observability
  - [ ] Uses `A9_SharedLogger` for MCP/service changes
  - [ ] Includes transaction_id, query timing, columns/first-row previews (for SQL paths)
- [ ] Security & validation
  - [ ] SELECT-only enforced and validated (no DDL/DML)
  - [ ] Principal filters injected server-side (if applicable)
  - [ ] LLM prompts (if used) are schema-scoped and audited

## Changes

- Summary of key code changes with references to files, functions, and classes.

## Tests

- Describe new/updated tests and how to run them.

## Risks & Rollback

- Known risks and how to mitigate.
- Rollback plan if issues arise.

## Screenshots / Logs (optional)

- Attach relevant logs or screenshots.
