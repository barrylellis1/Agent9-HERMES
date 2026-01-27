# Data Product Onboarding UX Enhancements

## Overview
This document outlines the UX improvements for the Agent9 Data Product Onboarding workflow to streamline subsequent onboarding sessions and enable extending existing data products.

## Enhancement 1: Connection Profile Management

### Purpose
Save and reuse database connection credentials across onboarding sessions to avoid re-entering the same information repeatedly.

### Features
1. **Save Connection Profiles**
   - Save current connection with a friendly name
   - Store credentials in browser localStorage
   - Support for BigQuery, DuckDB (extensible to Snowflake, Databricks)

2. **Load Saved Profiles**
   - Display list of saved profiles for the selected source system
   - Show last used timestamp
   - One-click selection to populate connection fields

3. **Manage Profiles**
   - Edit profile names and credentials
   - Delete unused profiles
   - Visual indication of currently selected profile

### Implementation Status
- ✅ Storage utility created (`connectionProfileStorage.ts`)
- ✅ UI component created (`ConnectionProfileManager.tsx`)
- ✅ Integration into Step 1 (Connection Setup) - COMPLETE
- ✅ Profile selection handler wired up
- ✅ Auto-populate connection fields on profile load
- ✅ Disclaimer about localStorage limitations added
- 🔄 Testing and refinement - READY FOR TESTING

### Files Created
- `decision-studio-ui/src/utils/connectionProfileStorage.ts` - Storage layer
- `decision-studio-ui/src/components/ConnectionProfileManager.tsx` - UI component

---

## Enhancement 2: Data Product Reuse (Add KPIs to Existing Products)

### Purpose
Enable users to add new KPIs to already-registered data products without going through the full onboarding workflow.

### Features
1. **Data Product Selection**
   - List existing data products from registry
   - Filter by domain, source system
   - Show summary (table count, existing KPI count)

2. **Skip to KPI Definition**
   - Load existing data product context
   - Pre-populate connection settings
   - Jump directly to Step 5 (KPI Definition)

3. **Incremental Updates**
   - Add new KPIs to existing contract
   - Validate new queries against existing schema
   - Update registry with additional KPIs

### Implementation Plan
1. Create data product selection UI component
2. Add "Extend Existing Product" mode to onboarding workflow
3. Implement contract YAML merging logic
4. Add API endpoint for fetching registered data products
5. Update finalize logic to handle incremental updates

### Implementation Status
- ⏳ Data product selection UI - PENDING
- ⏳ Workflow mode switching - PENDING
- ⏳ Contract merging logic - PENDING
- ⏳ API endpoints - PENDING

---

## Technical Architecture

### Connection Profile Storage
```typescript
interface ConnectionProfile {
  id: string
  name: string
  sourceSystem: 'bigquery' | 'duckdb' | 'snowflake' | 'databricks'
  createdAt: string
  lastUsedAt: string
  bigquery?: { project, dataset, serviceAccountPath }
  duckdb?: { path }
  // ... other systems
}
```

**Storage:** Browser localStorage (key: `agent9_connection_profiles`)

**Security Note:** For production, consider:
- Encrypting sensitive credentials
- Moving to backend storage with proper access controls
- Using secure credential vaults for service account keys

### Data Product Registry Integration
```typescript
interface RegisteredDataProduct {
  id: string
  name: string
  domain: string
  sourceSystem: string
  tables: string[]
  kpiCount: number
  createdAt: string
  contractYamlPath: string
}
```

**API Endpoints Needed:**
- `GET /api/v1/registry/data-products` - List all registered products
- `GET /api/v1/registry/data-products/{id}` - Get product details
- `PATCH /api/v1/registry/data-products/{id}/kpis` - Add KPIs to existing product

---

## User Workflows

### Workflow 1: Using Saved Connection Profile
1. Navigate to Connection Setup (Step 1)
2. Select source system (e.g., BigQuery)
3. Click on saved profile from list
4. Connection fields auto-populate
5. Proceed to Schema Discovery

### Workflow 2: Adding KPIs to Existing Product
1. Start onboarding workflow
2. Select "Extend Existing Data Product" option
3. Choose data product from registry list
4. System loads existing context and jumps to Step 5
5. Define new KPIs using KPI Assistant
6. Validate queries against existing schema
7. Register updates to existing contract

---

## Next Steps

### Immediate (Current Session)
1. ✅ Complete connection profile integration into Step 1
2. Test save/load/delete functionality
3. Add visual polish and error handling

### Short Term (Next Session)
1. Design data product selection UI
2. Implement "Extend Product" workflow mode
3. Create contract YAML merging logic
4. Add registry API endpoints

### Future Enhancements
1. Backend storage for connection profiles
2. Credential encryption and secure vaults
3. Profile sharing across team members
4. Connection testing before saving
5. Snowflake and Databricks support
6. Bulk KPI import from CSV/Excel
7. KPI templates library

---

## Testing Checklist

### Connection Profiles
- [ ] Save profile with valid credentials
- [ ] Load profile and verify fields populate
- [ ] Edit profile name and credentials
- [ ] Delete profile
- [ ] Handle multiple profiles for same source system
- [ ] Verify last used timestamp updates
- [ ] Test with empty state (no saved profiles)

### Data Product Reuse
- [ ] List registered data products
- [ ] Select product and load context
- [ ] Add new KPIs to existing product
- [ ] Validate queries against existing schema
- [ ] Merge KPIs into existing contract
- [ ] Verify registry updates correctly

---

## Security Considerations

### Current Implementation (Development)
- Credentials stored in browser localStorage (unencrypted)
- Suitable for development and testing
- **NOT production-ready**

### Production Requirements
1. **Backend Storage**
   - Store profiles in secure database
   - Associate with user accounts
   - Implement access controls

2. **Credential Encryption**
   - Encrypt sensitive fields at rest
   - Use secure key management
   - Consider credential vaults (HashiCorp Vault, AWS Secrets Manager)

3. **Service Account Security**
   - Never store full service account JSON in browser
   - Use backend proxy for BigQuery connections
   - Implement credential rotation policies

4. **Audit Logging**
   - Log profile creation/modification/deletion
   - Track profile usage
   - Monitor for suspicious activity

---

## Performance Considerations

- localStorage has 5-10MB limit (sufficient for profiles)
- Profile list sorted by last used for quick access
- Lazy loading for data product registry list
- Debounce search/filter operations
- Cache registry data with TTL

---

## Accessibility

- Keyboard navigation for profile selection
- Screen reader support for all actions
- Clear focus indicators
- Descriptive ARIA labels
- Error messages announced to screen readers

