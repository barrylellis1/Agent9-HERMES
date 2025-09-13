# Business Process Hierarchy Blueprint

## Current MVP Implementation
For the MVP, business processes are simplified to the domain level to reduce complexity and ensure consistent mapping between registries.

## Future Hierarchical Implementation

### Multi-Level Hierarchy

```
Domain
  └── Process
       └── Sub-Process
            └── Activity
```

### Implementation in Business Process Registry

The business process registry will be enhanced with parent-child relationships:

```yaml
- id: "finance"
  name: "Finance"
  domain: "Finance"
  description: "Financial management domain"
  parent_id: null  # Top-level domain
  
- id: "finance_profitability_analysis"
  name: "Profitability Analysis"
  domain: "Finance"
  description: "Analysis of profit margins, cost structures, and profit drivers"
  parent_id: "finance"  # Child of Finance domain
  display_name: "Finance: Profitability Analysis"
  
- id: "finance_profitability_analysis_margin_calculation"
  name: "Margin Calculation"
  domain: "Finance"
  description: "Calculation of profit margins across product lines"
  parent_id: "finance_profitability_analysis"  # Child of Profitability Analysis
  display_name: "Finance: Profitability Analysis: Margin Calculation"
```

### Principal Profile Responsibility Assignment

For principal profiles, responsibilities can be assigned at different levels:

```yaml
# C-Level executive - assigned at domain level
business_processes:
  - "Finance"  # Entire domain
  - "Operations"  # Entire domain

# Director level - assigned at process level
business_processes:
  - "Finance: Profitability Analysis"
  - "Finance: Revenue Growth Analysis"

# Manager level - assigned at sub-process level
business_processes:
  - "Finance: Profitability Analysis: Margin Calculation"
  - "Finance: Revenue Growth Analysis: Regional Trends"
```

### KPI Mapping

KPIs can be mapped to the appropriate level in the hierarchy:

```yaml
- id: gross_margin
  name: "Gross Margin"
  business_process_ids:
    - "finance_profitability_analysis_margin_calculation"  # Most specific
    - "finance_profitability_analysis"  # Parent process
```

### Agent Implementation Requirements

The Principal Context Agent would need to be updated to:
1. Understand the hierarchy
2. Resolve business processes at any level
3. Support inheritance (if a principal is assigned a domain, they get all processes under it)

This approach would allow for flexible assignment of responsibilities while maintaining a clear organizational structure. It also enables more precise KPI mapping and situation awareness at different organizational levels.
