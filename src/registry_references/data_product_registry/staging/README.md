# Data Product Staging Area

## Purpose
This directory contains **in-progress data product contracts** that are undergoing the onboarding workflow. Contracts remain here until they complete governance approval, at which point they are promoted to the production registry.

## Workflow Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                    Data Product Onboarding                      │
└─────────────────────────────────────────────────────────────────┘

1. Schema Discovery
   └─> Initial contract created in staging/

2. KPI Definition (KPI Assistant)
   └─> Contract updated with KPIs in staging/

3. Query Testing
   └─> Contract updated with test results in staging/

4. Governance Assignment
   └─> Contract updated with ownership/compliance in staging/

5. Governance Approval ✅
   └─> Contract PROMOTED to ../data_products/
   └─> Entry added to data_product_registry.yaml
   └─> Staging copy archived or deleted

6. Situation Awareness Activation
   └─> Reads from ../data_products/ (production only)
```

## Directory Structure

```
staging/
├── README.md                    # This file
├── dp_sales_analytics.yaml      # In-progress: KPI definition complete
├── dp_customer_360.yaml         # In-progress: Query testing
└── archive/                     # Optional: Rejected or superseded contracts
    └── dp_test_*.yaml
```

## Status Indicators

Contracts in staging can have the following statuses (in metadata):

- `status: schema_discovered` - Schema inspection complete
- `status: kpis_defined` - KPI Assistant complete
- `status: queries_tested` - Query validation complete
- `status: governance_pending` - Awaiting governance approval
- `status: approved` - Ready for promotion (should be promoted immediately)
- `status: rejected` - Failed governance review (move to archive/)

## Promotion Criteria

A contract is ready for promotion when:

1. ✅ All KPIs have complete attribute sets
2. ✅ All KPI queries have been tested successfully
3. ✅ Ownership metadata assigned (owner, stakeholders)
4. ✅ Business process mappings complete
5. ✅ Compliance metadata validated
6. ✅ Data Governance Agent approval received

## Promotion Process

**Manual Promotion:**
```bash
# Move contract to production
mv staging/dp_sales_analytics.yaml data_products/dp_sales_analytics.yaml

# Add entry to registry
# Edit data_product_registry.yaml to add new product
```

**Automated Promotion (Phase 3):**
- Data Governance Agent validates all criteria
- Orchestrator automatically promotes contract
- Registry entry created
- Activation context published
- Staging copy archived

## Cleanup Policy

- **Active contracts**: Keep in staging/ during onboarding
- **Approved contracts**: Promote to production, delete from staging
- **Rejected contracts**: Move to archive/ with rejection reason
- **Abandoned contracts**: Delete after 30 days of inactivity
- **Test contracts**: Delete immediately (prefix with `test_` or `temp_`)

## Notes

- Contracts in staging/ are NOT visible to Situation Awareness Console
- Contracts in staging/ are NOT included in production queries
- Only contracts in ../data_products/ are considered "production-ready"
- Staging allows safe iteration without affecting downstream systems
