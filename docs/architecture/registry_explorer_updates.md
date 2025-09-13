# Registry Explorer Updates

## Overview

The Registry Explorer tool has been updated to support domain-level business processes and provide better visualization of the registry data. These updates align with the simplified business process structure implemented in the registry files.

## Key Updates

### 1. Business Process Registry Explorer

A new Business Process registry explorer has been implemented with the following features:

- **Domain-Level Process Detection**: Automatically detects and labels domain-level business processes
- **Domain-Based Navigation**: Groups business processes by domain for easier navigation
- **Hierarchical Structure Detection**: Identifies and displays whether the business processes have a hierarchical structure
- **Detailed Process Information**: Shows comprehensive information about each business process

### 2. Business Process Display

The business process display has been enhanced to:

- Identify domain-level processes vs. specific processes
- Extract domain information from display names or explicit domain fields
- Show parent-child relationships when available
- Display associated KPIs and stakeholders
- Provide special information for domain-level processes

### 3. Test Results

Testing with the updated registry files shows:

- **Business Process Registry**:
  - 31 business processes found across 9 domains
  - Domain-level processes correctly identified
  - No hierarchical structure detected in the current implementation

- **Principal Registry**:
  - 4 principal profiles found
  - All profiles using domain-level business processes (e.g., 'Finance')
  - Multiple domains assigned to some principals (e.g., 'Finance', 'Strategy', 'Operations')

## Implementation Details

### Domain Detection Logic

```python
# Extract domain from display_name or use explicit domain field
domain = None
if "domain" in bp_data:
    domain = bp_data["domain"]
elif "display_name" in bp_data and ":" in bp_data["display_name"]:
    domain = bp_data["display_name"].split(":", 1)[0].strip()
else:
    domain = "Other"
```

### Domain-Level Process Detection

```python
# Determine if this is a domain-level process
is_domain_level = False
if "domain" in bp_data and bp_data["domain"] == header_name:
    is_domain_level = True
elif "display_name" in bp_data and ":" not in bp_data["display_name"]:
    # If display_name doesn't have a colon, it might be a domain-level process
    is_domain_level = True
```

### Domain-Based Navigation

```python
# Group by domain for easier navigation
domains = {}
for bp in business_processes:
    # Extract domain from display_name or use explicit domain field
    domain = None
    if "domain" in bp:
        domain = bp["domain"]
    elif "display_name" in bp and ":" in bp["display_name"]:
        domain = bp["display_name"].split(":", 1)[0].strip()
    else:
        domain = "Other"
    
    if domain not in domains:
        domains[domain] = []
    domains[domain].append(bp)

# Domain selection
domain_list = list(domains.keys())
selected_domain = st.selectbox("Select Domain", domain_list)
```

## Future Enhancements

1. **Hierarchical Business Process Visualization**: Implement a tree view for hierarchical business processes when that feature is added
2. **Cross-Registry Relationships**: Show relationships between business processes, KPIs, and principals
3. **Registry Editing**: Add capability to edit registry entries directly from the UI
4. **Search Functionality**: Implement search across all registry types
5. **Validation**: Add validation for registry entries to ensure consistency
