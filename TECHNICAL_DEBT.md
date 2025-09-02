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
