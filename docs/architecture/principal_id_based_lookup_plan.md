# Principal ID-Based Lookup Implementation Plan

## Overview

This document outlines the implementation plan for refactoring the Principal Context Agent to use principal IDs as primary keys for lookups instead of role names. This change will align the system with enterprise architecture best practices and eliminate case sensitivity issues.

## Current Implementation

Currently, the Principal Context Agent:
- Loads principals from `principal_registry.yaml`
- Normalizes them into a dictionary keyed by lowercase role name
- Does not use the principal ID (`id: "ceo_001"`) as the lookup key
- Has case sensitivity issues with role name lookups
- Does not support multiple roles per principal

## Target Implementation

The refactored system will:
- Use principal IDs as primary keys for all lookups
- Support multiple roles per principal
- Provide role-to-ID mapping for backward compatibility
- Integrate with enterprise identity management systems
- Eliminate case sensitivity issues

## Implementation Steps

### Phase 1: Core Refactoring

1. **Update Principal Profile Data Structure**
   - Modify `_load_principal_profiles()` to create a dictionary keyed by principal ID
   - Maintain a secondary index for role-based lookups for backward compatibility
   - Store multiple roles per principal when available

```python
# Example implementation
principal_by_id = {}  # Primary lookup by ID
principal_by_role = {}  # Secondary lookup by role (for backward compatibility)

for principal in principals:
    principal_id = principal.get('id')
    if not principal_id:
        continue  # Skip principals without ID
        
    # Store principal by ID
    principal_by_id[principal_id] = {
        "id": principal_id,
        "role": principal.get('role'),
        "name": principal.get('name'),
        # ... other fields
    }
    
    # Also index by role for backward compatibility
    role_key = str(principal.get('role', '')).lower()
    if role_key:
        principal_by_role[role_key] = principal_id  # Store ID reference
```

2. **Create New Lookup Methods**
   - Implement `get_principal_by_id(principal_id)` method
   - Update `_get_profile_case_insensitive()` to use the ID-based lookup when possible

```python
def get_principal_by_id(self, principal_id: str) -> Dict[str, Any]:
    """Get principal profile by ID."""
    return self.principal_profiles_by_id.get(principal_id, {})

def get_principal_by_role(self, role: Union[str, PrincipalRole]) -> Dict[str, Any]:
    """Get principal profile by role (backward compatibility)."""
    # Try to find principal ID for this role
    role_str = str(role).lower()
    principal_id = self.role_to_id_map.get(role_str)
    
    if principal_id:
        # Use ID-based lookup
        return self.get_principal_by_id(principal_id)
    
    # Fall back to case-insensitive role lookup
    return self._get_profile_case_insensitive(role)
```

3. **Update Principal Context Creation**
   - Modify `get_principal_context()` to accept either ID or role
   - Prioritize ID-based lookup when available

```python
async def get_principal_context(self, request: Union[PrincipalProfileRequest, Dict[str, Any], str]) -> PrincipalProfileResponse:
    """Get principal context for a given principal ID or role."""
    try:
        # Handle different input types
        if isinstance(request, str):
            # Check if it's an ID or a role
            if request in self.principal_profiles_by_id:
                principal_id = request
                principal_role = None
            else:
                principal_id = None
                principal_role = request
            request_id = str(uuid.uuid4())
        elif isinstance(request, dict):
            principal_id = request.get('principal_id')
            principal_role = request.get('principal_role') if not principal_id else None
            request_id = request.get('request_id', str(uuid.uuid4()))
        else:
            principal_id = getattr(request, 'principal_id', None)
            principal_role = getattr(request, 'principal_role', None) if not principal_id else None
            request_id = request.request_id
            
        # Log the request
        self.logger.info(f"Getting principal context for ID: {principal_id} or role: {principal_role}")
        
        # Try ID-based lookup first
        if principal_id:
            profile = self.get_principal_by_id(principal_id)
        else:
            # Fall back to role-based lookup
            profile = self.get_principal_by_role(principal_role)
            
        # Rest of the method remains similar...
    except Exception as e:
        # Error handling...
```

### Phase 2: API and Model Updates

1. **Update Request/Response Models**
   - Add `principal_id` field to `PrincipalProfileRequest`
   - Update validation to allow either ID or role
   - Ensure backward compatibility

```python
class PrincipalProfileRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    principal_id: Optional[str] = None
    principal_role: Optional[Union[str, PrincipalRole]] = None
    
    @validator('principal_role', 'principal_id')
    def validate_principal_identifiers(cls, v, values):
        # Ensure at least one identifier is provided
        if not v and 'principal_id' not in values and 'principal_role' not in values:
            raise ValueError("Either principal_id or principal_role must be provided")
        return v
```

2. **Update SQL Execution Request**
   - Modify `SQLExecutionRequest` to use principal ID
   - Add backward compatibility for role-based requests

```python
class SQLExecutionRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    principal_id: Optional[str] = None
    principal_role: Optional[Union[str, PrincipalRole]] = None
    query: str
    # Other fields...
    
    @validator('principal_id', 'principal_role')
    def validate_principal_identifiers(cls, v, values):
        # Similar validation as above
        return v
```

### Phase 3: UI Integration

1. **Update Decision Studio UI**
   - Modify role selection dropdown to include principal IDs
   - Update API calls to pass principal ID instead of role
   - Maintain backward compatibility

```python
# Example UI code
def get_principals():
    """Get all principals for dropdown."""
    principals = []
    try:
        # Get principals from agent
        response = agent.get_all_principals()
        for principal in response.principals:
            principals.append({
                "id": principal.id,
                "display_name": f"{principal.name} ({principal.role})",
                "role": principal.role
            })
    except Exception as e:
        st.error(f"Error loading principals: {str(e)}")
    return principals

# In UI selection
selected_principal = st.selectbox(
    "Select Principal",
    options=principals,
    format_func=lambda p: p["display_name"]
)

# When making API calls
principal_id = selected_principal["id"]
```

2. **Add Principal Management UI**
   - Create UI for viewing and managing principals
   - Support adding/editing principals with multiple roles
   - Ensure proper ID generation for new principals

### Phase 4: Testing and Validation

1. **Create Test Scripts**
   - Test ID-based lookups
   - Test role-based lookups (backward compatibility)
   - Test multiple roles per principal
   - Test integration with Decision Studio

2. **Performance Testing**
   - Benchmark ID-based lookups vs. role-based lookups
   - Test with large number of principals

3. **Integration Testing**
   - Test with external identity management systems
   - Test with existing workflows and agents

## Files to Modify

1. `src/agents/a9_principal_context_agent.py`
   - Update profile loading and lookup methods
   - Add ID-based lookup functionality
   - Maintain backward compatibility

2. `src/agents/models/situation_awareness_models.py`
   - Update request/response models
   - Add principal ID fields
   - Update validation

3. `decision_studio.py`
   - Update UI to use principal IDs
   - Maintain backward compatibility

4. `src/registry/providers/principal_provider.py`
   - Update provider to support ID-based lookups
   - Add methods for managing principals with multiple roles

## Timeline and Resources

- **Phase 1**: 2 days - Core refactoring
- **Phase 2**: 1 day - API and model updates
- **Phase 3**: 2 days - UI integration
- **Phase 4**: 1 day - Testing and validation

**Total**: 6 days (1-2 developers)

## Risks and Mitigations

1. **Backward Compatibility**
   - Risk: Breaking existing integrations
   - Mitigation: Maintain role-based lookups for backward compatibility

2. **Performance Impact**
   - Risk: Additional lookup overhead
   - Mitigation: Optimize data structures for fast ID-based lookups

3. **Data Migration**
   - Risk: Existing data may not have proper IDs
   - Mitigation: Add ID generation for principals without IDs

## Success Criteria

1. All principal lookups use IDs as primary keys
2. Case sensitivity issues are eliminated
3. Multiple roles per principal are supported
4. Decision Studio UI works with ID-based lookups
5. All tests pass with the new implementation
6. No performance degradation compared to current implementation
