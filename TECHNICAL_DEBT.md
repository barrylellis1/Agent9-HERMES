# Technical Debt & Future Enhancements

This document tracks known technical debt and planned enhancements for the Agent9-HERMES project.

## Principal Context Agent

### Role System Redesign
**Priority**: Medium  
**Target**: Post-MVP  
**Description**: Replace the enum-based `PrincipalRole` with a flexible string-based system that can integrate with external HR systems.

**Current Limitation**: 
- The `PrincipalRole` enum in `situation_awareness_models.py` only supports a fixed set of roles ('CFO', 'Finance Manager')
- Current workaround maps other roles (like 'CEO', 'COO') to existing enum values

**Proposed Solution**:
- Implement a `RoleRegistry` class that loads roles from external systems
- Replace enum validation with string-based role identifiers
- Focus on role capabilities rather than role names
- Support dynamic role hierarchies

**Files Affected**:
- `src/agents/models/situation_awareness_models.py`
- `src/agents/a9_principal_context_agent.py`
- `src/registry/providers/principal_provider.py`

### User ID Based Principal Lookup
**Priority**: High  
**Target**: Post-MVP  
**Description**: Replace role-based lookups with user ID based lookups for proper enterprise identity management.

**Current Limitation**:
- The agent uses role names as keys for principal profile lookups instead of principal IDs
- Case sensitivity and format issues with role names
- No proper integration with enterprise identity management
- No support for users with multiple roles
- Principal IDs already exist in the principal registry (e.g., "ceo_001") but aren't used as lookup keys

**Proposed Solution**:
- Use the existing principal IDs from the registry as primary keys for lookups
- Associate roles, permissions, and context with these IDs
- Implement proper identity management integration
- Support role changes and multiple roles per user

**Files Affected**:
- `src/agents/a9_principal_context_agent.py`
- `src/registry/providers/principal_provider.py`
- `decision_studio.py`

### Multi-Principal Context Support
**Priority**: Low  
**Target**: Post-MVP  
**Description**: Add support for retrieving and managing context for multiple principals simultaneously.

**Current Limitation**:
- The agent processes one principal at a time
- No support for team contexts or role combinations

**Proposed Solution**:
- Add methods to fetch and merge multiple principal contexts
- Implement priority rules for resolving conflicts
- Support team-based context scenarios

## Other Technical Debt

*Add other items as they are identified*

## Deprecation & Removal Plan (MCP Service Alignment)

This section tracks deprecations related to consolidating SQL generation/execution in the Data Product MCP Service and preventing functional drift.

### Deprecation Banner Template

Add this banner at the top of any legacy/shim module that is being phased out. It should log a clear warning on import and direct contributors to the replacement path. Set a firm removal date.

```python
# DEPRECATION WARNING
# This module is deprecated and will be removed after {REMOVAL_DATE}.
# Reason: SQL generation/execution must occur exclusively in the MCP Service per PRD.
# Replacement: Use MCP client `src/agents/clients/a9_mcp_client.py` (embedded/remote) or
# call the MCP Service API. For shared logic, use `src/services/mcp_core/`.
import warnings as _warnings
_warnings.warn(
    "[DEPRECATED] {MODULE_NAME} is deprecated and will be removed after {REMOVAL_DATE}. "
    "Use MCP client/service instead.",
    DeprecationWarning,
    stacklevel=2,
)
```

### Targets and Deadlines

- [ ] `src/agents/a9_data_product_mcp_service_agent.py`
  - Action: Extract shared logic to `src/services/mcp_core/`; replace agent-internal DB calls with MCP client.
  - Status: Pending extraction
  - Deprecation banner added: Pending
  - Removal date: YYYY-MM-DD (set after two-week deprecation window)

- [ ] Any direct CSV/DB access under `src/agents/**`
  - Action: Replace with MCP client usage; add inline `# arch-allow-*` only in justified cases.
  - Status: Enforced by architecture tests and pre-commit hook
  - Removal date: Continuous enforcement (N/A)

### Process and Criteria

1. Add deprecation banner to target file(s)
2. Ensure all callers are migrated to MCP client/service (embedded for unit tests, remote for integration/prod)
3. Confirm no remaining references via repo-wide search (CI architecture tests must pass)
4. Wait for deprecation window to elapse (2–4 weeks, based on release cadence)
5. Remove file(s) and update docs/PRDs accordingly

### Compliance Signals

- Architecture tests pass with no banned patterns in `src/agents/**`
- No direct agent construction in `tests/**`
- MCP client is the only data access path in agents
- PR template checkboxes affirmed for PRDs, cards, and config sync
