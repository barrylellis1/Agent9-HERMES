# Data Product Onboarding Architecture

## Overview

The Data Product Onboarding workflow enables Agent9 to consume data from multiple enterprise platforms (BigQuery, Snowflake, Databricks, HANA) and local sources (DuckDB) through a platform-adaptive approach that leverages native metadata catalogs when available.

## Design Principles

### 1. Platform-Adaptive Metadata Extraction

**Metadata-Rich Platforms** (BigQuery, Snowflake, Databricks, HANA):
- Auto-extract FK relationships from `INFORMATION_SCHEMA.KEY_COLUMN_USAGE`
- Parse view definitions from `INFORMATION_SCHEMA.VIEWS` to identify base tables
- Extract primary keys from `TABLE_CONSTRAINTS`
- Derive table roles (fact/dimension) from schema patterns and view SQL
- **No manual FK mapping or table role selection required**

**DuckDB / Local Files** (Limited Metadata):
- Infer FK relationships via naming conventions (`customer_id` → `customers.id`)
- Require manual table role assignment (fact/dimension)
- Support user-defined relationship mapping
- **Manual curation workflow**

### 2. Fully Curated Data Products

**Critical Requirement**: Data products must be fully curated before Agent9 consumption:
- Star schema models (fact + dimensions) with defined relationships
- Curated views (not raw tables) for consumption
- All FK relationships validated and documented
- Semantic tags assigned to all columns

Agent9 agents consume **curated views**, not raw source tables.

### 3. Semantic Tag Inference with Override

**Auto-Inference Baseline**:
- `measure`: Numeric columns with names like "amount", "revenue", "cost", "total"
- `dimension`: Categorical columns, text fields, codes
- `time`: Date/timestamp columns, columns with "date", "time", "_at" in name
- `identifier`: Columns ending in "_id", "_key", or named "id"

**Manual Override Required**:
- UI must allow users to reclassify columns
- Critical for edge cases (e.g., `customer_count` as dimension vs measure)
- Overrides persist in contract YAML

### 4. KPI Proposals - Helpful but Not Primary

**Onboarding KPI Generation**:
- Lightweight proposals: `SUM(amount)`, `COUNT(DISTINCT customer_id)`
- Confidence scores based on heuristics
- User can accept/reject/modify

**Primary KPI Discovery**:
- Happens downstream in univariate/multivariate analysis flows
- Data analysis agents discover patterns and suggest KPIs
- Onboarding KPIs serve as starting point only

## Workflow Design

### Platform-Adaptive Flow

#### **For BigQuery/Snowflake/Databricks/HANA:**

```
Step 1: Connection Setup
  ├─ Select source system
  ├─ Provide credentials (project, dataset, service account)
  └─ Test connection

Step 2: Schema Discovery
  ├─ Query INFORMATION_SCHEMA.TABLES
  ├─ Filter by table type (VIEW preferred)
  └─ Display table list with row counts

Step 3: Data Product Selection
  ├─ User selects view(s) to onboard
  ├─ Define data product metadata (ID, name, domain, description)
  └─ Auto-detect: View → curated data product

Step 4: Auto-Analysis & Metadata Extraction
  ├─ Query INFORMATION_SCHEMA.COLUMNS for column metadata
  ├─ Query KEY_COLUMN_USAGE for FK relationships
  ├─ Query TABLE_CONSTRAINTS for PK definitions
  ├─ Parse view SQL to identify base tables and joins
  ├─ Auto-infer semantic tags
  └─ Generate KPI proposals

Step 5: Review & Override (Optional)
  ├─ Display extracted metadata
  ├─ Show FK relationships diagram
  ├─ Allow semantic tag overrides
  └─ Refine KPI proposals

Step 6: Contract Generation & Registration
  ├─ Generate contract YAML with all metadata
  ├─ Validate completeness
  ├─ Register to Data Product Registry
  └─ Publish activation context to agents
```

#### **For DuckDB:**

```
Step 1: Connection Setup
  ├─ Select DuckDB
  ├─ Provide database path or use default
  └─ Specify schema (default: main)

Step 2: Schema Discovery
  ├─ Query information_schema.tables
  └─ Display table list

Step 3: Data Product Definition
  ├─ Select tables (fact + dimensions)
  ├─ Assign table roles (FACT, DIMENSION, BRIDGE)
  ├─ Define data product metadata
  └─ Manual curation required

Step 4: Manual Relationship Mapping
  ├─ Infer FK relationships via naming conventions
  ├─ User validates/corrects FK → PK mappings
  ├─ Define join conditions
  └─ Assign semantic tags with overrides

Step 5: KPI Proposals & Review
  ├─ Generate KPI proposals
  ├─ Review contract YAML
  └─ Validate completeness

Step 6: Registration
  ├─ Register to Data Product Registry
  └─ Publish activation context
```

## Backend Implementation

### Enhanced Profiling Methods

#### `_profile_table_bigquery` Enhancements

```python
async def _profile_table_bigquery(self, inspection_manager, table_name, settings):
    """
    Profile BigQuery table/view with FK extraction.
    
    Queries:
    1. INFORMATION_SCHEMA.COLUMNS - column metadata
    2. INFORMATION_SCHEMA.KEY_COLUMN_USAGE - FK relationships
    3. INFORMATION_SCHEMA.TABLE_CONSTRAINTS - PK definitions
    4. INFORMATION_SCHEMA.VIEWS - view SQL definition (if applicable)
    """
    # Extract FK relationships
    fk_query = f"""
        SELECT 
            kcu.column_name,
            kcu.referenced_table_name,
            kcu.referenced_column_name
        FROM `{project}.{schema}.INFORMATION_SCHEMA.KEY_COLUMN_USAGE` kcu
        JOIN `{project}.{schema}.INFORMATION_SCHEMA.TABLE_CONSTRAINTS` tc
            ON kcu.constraint_name = tc.constraint_name
        WHERE kcu.table_name = @table_name
          AND tc.constraint_type = 'FOREIGN KEY'
    """
    
    # Parse view definition for base tables
    view_query = f"""
        SELECT view_definition
        FROM `{project}.{schema}.INFORMATION_SCHEMA.VIEWS`
        WHERE table_name = @table_name
    """
```

#### `_profile_table_duckdb` Enhancements

```python
async def _profile_table_duckdb(self, inspection_manager, table_name, settings):
    """
    Profile DuckDB table with FK inference.
    
    Inference heuristics:
    1. Column name matching: customer_id → customers.id
    2. Cardinality validation: many-to-one relationship
    3. Data type compatibility check
    """
    # Infer FK relationships via naming conventions
    for col in columns:
        if col.name.endswith('_id'):
            potential_table = col.name[:-3] + 's'  # customer_id → customers
            # Validate table exists and has matching PK
```

### Data Models Extension

```python
class ForeignKeyRelationship(A9AgentBaseModel):
    """FK relationship extracted from metadata or inferred."""
    
    source_table: str
    source_column: str
    target_table: str
    target_column: str
    confidence: float = 1.0  # 1.0 for catalog-extracted, <1.0 for inferred
    relationship_type: str = "many-to-one"  # many-to-one, one-to-one, many-to-many

class TableProfile(A9AgentBaseModel):
    """Extended with FK relationships."""
    
    name: str
    row_count: Optional[int]
    columns: List[TableColumnProfile]
    primary_keys: List[str]
    foreign_keys: List[ForeignKeyRelationship] = Field(default_factory=list)
    table_role: Optional[str] = None  # FACT, DIMENSION, BRIDGE (for DuckDB)
    view_definition: Optional[str] = None  # For views, store SQL
```

## UI Components

### Platform Detection

```typescript
const isPlatformMetadataRich = (sourceSystem: string): boolean => {
    return ['bigquery', 'snowflake', 'databricks', 'hana'].includes(sourceSystem)
}

// Conditional rendering
{isPlatformMetadataRich(sourceSystem) ? (
    <AutoAnalysisStep />
) : (
    <ManualCurationStep />
)}
```

### Key UI Components

1. **ConnectionSetup**: Source system selection, credential input
2. **SchemaDiscovery**: Table browser with filtering
3. **DataProductSelection**: Table selection + metadata input
4. **AutoAnalysis** (metadata-rich): Display extracted relationships
5. **ManualCuration** (DuckDB): FK mapper, table role selector
6. **SemanticTagEditor**: Inline column classification override
7. **ContractReview**: YAML preview with validation

## Contract YAML Output

```yaml
data_product:
  id: dp_sales_analytics
  name: Sales Analytics
  domain: Finance
  source_system: bigquery
  project: my-gcp-project
  dataset: sales_data

tables:
  - name: sales_fact
    role: FACT
    primary_keys: [sale_id]
    foreign_keys:
      - source_column: customer_id
        target_table: customer_dim
        target_column: customer_id
        confidence: 1.0
      - source_column: product_id
        target_table: product_dim
        target_column: product_id
        confidence: 1.0
    columns:
      - name: sale_id
        data_type: STRING
        semantic_tags: [identifier]
      - name: amount
        data_type: FLOAT64
        semantic_tags: [measure]
      - name: sale_date
        data_type: DATE
        semantic_tags: [time]

  - name: customer_dim
    role: DIMENSION
    primary_keys: [customer_id]
    columns:
      - name: customer_id
        data_type: STRING
        semantic_tags: [identifier]
      - name: customer_name
        data_type: STRING
        semantic_tags: [dimension]

kpis:
  - name: Total Sales
    expression: SUM(amount)
    grain: sale_date
    dimensions: [customer_id, product_id]
    confidence: 0.8
```

## Integration with Agent9 Ecosystem

### Registry Activation

```python
# After registration, publish activation context
activation_context = {
    "data_product_id": data_product_id,
    "source_system": source_system,
    "tables": [t.name for t in tables],
    "kpis": [k.name for k in kpis],
    "timestamp": datetime.utcnow().isoformat()
}

# Notify all agents
await orchestrator.broadcast_event("data_product_registered", activation_context)
```

### Downstream Agent Consumption

**Data Governance Agent**:
- Reads contract YAML for business term → technical attribute mappings
- Uses FK relationships for JOIN generation

**Situation Awareness Agent**:
- Discovers KPIs from registry
- Calls Data Product Agent to execute SQL

**Data Product Agent**:
- Generates SQL using FK relationships from contract
- Enforces SELECT-only queries on curated views

## Testing Strategy

### Unit Tests
- FK extraction from BigQuery INFORMATION_SCHEMA
- FK inference for DuckDB via naming conventions
- Semantic tag inference and override logic
- Contract YAML generation with relationships

### Integration Tests
- End-to-end BigQuery onboarding (automated)
- End-to-end DuckDB onboarding (manual curation)
- Multi-table star schema registration
- Agent consumption of registered data products

## Future Enhancements

1. **Snowflake Support**: Add `SHOW PRIMARY KEYS`, `SHOW IMPORTED KEYS` queries
2. **Databricks Unity Catalog**: Use `DESCRIBE TABLE EXTENDED` for metadata
3. **HANA Support**: Query `SYS.CONSTRAINTS` for relationships
4. **Lineage Tracking**: Parse view SQL to build column-level lineage
5. **Automated Testing**: Generate test queries to validate FK relationships
6. **Cardinality Profiling**: Detect one-to-many vs many-to-many relationships

## Summary

This platform-adaptive approach:
- **Minimizes manual work** for enterprise platforms with rich metadata catalogs
- **Supports local development** with DuckDB through manual curation
- **Ensures data quality** by requiring fully curated data products
- **Enables Agent9 consumption** through standardized contract YAML
- **Scales to multiple platforms** with consistent abstraction layer
