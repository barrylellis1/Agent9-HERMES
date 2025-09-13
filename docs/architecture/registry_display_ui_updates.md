# Registry Display UI Updates

## Overview

The Decision Studio UI has been updated to handle domain-level business processes, aligning with our simplified business process structure. These changes ensure that the UI properly displays and interacts with the domain-level business processes we've implemented in the registry files.

## Changes Made

### 1. Business Process Selector

The business process selector has been updated to use domain-level business processes instead of enum values:

```python
# Business process selector
st.header("Business Processes")

# Get business processes from registry instead of enum
if "business_process_options" not in st.session_state:
    st.session_state.business_process_options = ["Finance", "Operations", "Strategy", "HR", "IT"]

# Try to get business processes from registry if orchestrator is available
if st.session_state.orchestrator:
    try:
        # This will be populated in the async section
        pass
    except Exception as e:
        st.warning(f"Error loading business processes: {str(e)}")

# Use domain-level business processes for selection
selected_processes = st.multiselect(
    "Select Business Domains",
    options=st.session_state.business_process_options,
    default=st.session_state.business_processes if isinstance(st.session_state.business_processes[0], str) 
           else ["Finance"],
    key="business_processes_select"
)
st.session_state.business_processes = selected_processes
```

### 2. Principal Context Extraction

The principal context extraction has been updated to handle domain-level business processes:

```python
# Create the principal context
principal_context = PrincipalContext(
    role=profile_data.get('role', 'CFO'),
    principal_id=profile_data.get('id', 'cfo_001'),
    business_processes=profile_data.get('business_processes', ['Finance']),  # Use string-based business processes
    default_filters=profile_data.get('default_filters', {}),
    decision_style=profile_data.get('decision_style', 'Analytical'),
    communication_style=profile_data.get('communication_style', 'Concise'),
    preferred_timeframes=[TimeFrame.CURRENT_QUARTER, TimeFrame.YEAR_TO_DATE]
)
```

### 3. Default Principal Context

The default principal context has been updated to use domain-level business processes:

```python
principal_context = PrincipalContext(
    role="CFO",
    principal_id="cfo_001",
    business_processes=["Finance"],  # Use domain-level business processes
    default_filters={},
    decision_style="Analytical",
    communication_style="Concise",
    preferred_timeframes=[TimeFrame.CURRENT_QUARTER, TimeFrame.YEAR_TO_DATE]
)
```

### 4. Session State Initialization

The initialization of session state for business processes has been updated:

```python
if "business_processes" not in st.session_state:
    st.session_state.business_processes = ["Finance"]  # Use domain-level business processes
```

### 5. Async Section for Loading Business Processes

The async section has been updated to load business processes from the registry:

```python
# Also get business processes from registry
business_process_provider = registry_factory.get_provider("business_process")
if business_process_provider:
    # Get all business processes
    business_processes = business_process_provider.get_all()
    
    # Extract unique domains
    domains = set()
    for bp in business_processes:
        if hasattr(bp, 'domain') and bp.domain:
            domains.add(bp.domain)
        elif hasattr(bp, 'display_name') and ':' in bp.display_name:
            domain = bp.display_name.split(':', 1)[0].strip()
            domains.add(domain)
    
    # Update business process options
    if domains:
        st.session_state.business_process_options = list(domains)
```

## Expected Warnings

The following warnings are expected and have been documented:

1. `WARNING:src.registry.factory:Provider 'business_process' not found in registry factory`
2. `WARNING:src.agents.new.a9_principal_context_agent.A9_Principal_Context_Agent:Business process provider not found, creating default provider`
3. `WARNING:src.registry.factory:Provider 'business_process' exists but may not be properly initialized`
4. `WARNING:src.agents.new.a9_data_product_agent:Data Governance Agent not available for view name resolution`
5. `WARNING:src.registry.factory:Replacing existing kpi provider with new instance`
6. `WARNING:src.registry.factory:Replacing existing principal_profile provider with new instance`
7. `WARNING:src.registry.factory:Replacing existing data_product provider with new instance`
8. `WARNING:src.registry.factory:Replacing existing business_glossary provider with new instance`

These warnings are part of the normal initialization process and do not indicate a problem with the application.

## Future Enhancements

1. **Improve Business Process Provider Initialization**: Update the registry factory to properly initialize the business process provider.
2. **Connect Data Governance Agent**: Implement orchestrator-driven connection of the Data Governance Agent to the Data Product Agent.
3. **Enhance Registry Provider Management**: Improve the management of registry providers to avoid replacement warnings.
4. **Add Caching for Registry Data**: Implement caching for registry data to improve performance.
5. **Implement Hierarchical Business Process Display**: Update the UI to display hierarchical business processes when that feature is implemented.
