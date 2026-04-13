# Bootstrap Utilities for Agent9 Trial Environments

These utilities help set up trial/demo environments for Agent9 onboarding workflow validation.

**IMPORTANT**: These are **temporary tools for trial/demo purposes only**. They should be **deprecated** once customers have real curated data in production.

---

## Overview

Agent9 is built to analyze curated data products that already exist in your warehouse. To validate the onboarding workflow during trials or demos, we provide bootstrap utilities that:

1. Create a minimal FI (Finance) Star Schema
2. Load sample data
3. Create a curated view ready for Agent9 discovery

Once you have real curated data products, you can delete these trial schemas and work directly with your production data.

---

## Snowflake Bootstrap

### Prerequisites

- Snowflake trial account with credentials
- `snowflake-connector-python` installed: `pip install snowflake-connector-python`

### Usage

```bash
python scripts/bootstrap_snowflake_trial.py \
    --account xh12345.us-east-1 \
    --warehouse compute_wh \
    --database agent9_trial \
    --schema public \
    --user your_username \
    --password your_password
```

### Environment Variables (Alternative)

```bash
export SNOWFLAKE_ACCOUNT=xh12345.us-east-1
export SNOWFLAKE_WAREHOUSE=compute_wh
export SNOWFLAKE_DATABASE=agent9_trial
export SNOWFLAKE_SCHEMA=public
export SNOWFLAKE_USER=your_username
export SNOWFLAKE_PASSWORD=your_password

python scripts/bootstrap_snowflake_trial.py
```

### What It Creates

**Tables:**
- `CUSTOMERS` (dimension) — Customer entities
- `PRODUCTS` (dimension) — Product catalog
- `PROFIT_CENTERS` (dimension) — Organizational units
- `GL_ACCOUNTS` (dimension) — Chart of accounts
- `FINANCIAL_TRANSACTIONS` (fact) — Sales transactions with FKs

**Views:**
- `FI_STAR_VIEW` — Curated view joining fact + dimensions (ready for Agent9)

**Sample Data:**
- 4 customers (Enterprise & SMB)
- 4 products (Software, Services, Training)
- 3 profit centers (North America, EMEA, APAC)
- 4 GL accounts (Revenue & Expense)
- 8 transactions across 2 months

---

## Databricks Bootstrap

### Prerequisites

- Databricks workspace (Community Edition or paid)
- Personal access token
- `databricks-sql-connector` installed: `pip install databricks-sql-connector`

### Usage

```bash
python scripts/bootstrap_databricks_trial.py \
    --server-hostname adb-123.cloud.databricks.com \
    --http-path /sql/1.0/warehouses/abc123 \
    --token dapi... \
    --catalog main \
    --schema default
```

### Environment Variables (Alternative)

```bash
export DATABRICKS_HOST=adb-123.cloud.databricks.com
export DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/abc123
export DATABRICKS_TOKEN=dapi...
export DATABRICKS_CATALOG=main
export DATABRICKS_SCHEMA=default

python scripts/bootstrap_databricks_trial.py
```

### What It Creates

Same as Snowflake:
- 4 dimension tables + 1 fact table
- `fi_star_view` curated view
- Sample data

---

## Next Steps: Using with Agent9

After bootstrapping your trial environment:

1. **Launch Agent9 Admin Console** (Data Product Onboarding tab)

2. **Create a new data product:**
   - Select source: Snowflake or Databricks
   - Select connection profile: "Snowflake Trial" or "Databricks Community"
   - Provide credentials

3. **OnboardingService auto-discovers:**
   - Tables and views in your schema
   - Schema: columns, types, constraints
   - Foreign key relationships (from INFORMATION_SCHEMA)
   - Semantic tags (measure/dimension/time/identifier)

4. **Review & register:**
   - Confirm auto-extracted metadata
   - Adjust semantic tags if needed
   - Register data product to Agent9 registry

5. **Analyze with Agent9:**
   - Situation Awareness detects KPI anomalies
   - Deep Analysis explains root causes
   - Solution Finder proposes actions

---

## Cleanup: Removing Trial Data

When you're ready to use real production data:

### Snowflake
```sql
DROP SCHEMA agent9_trial CASCADE;
```

### Databricks
```sql
DROP SCHEMA main.default CASCADE;
-- or specify the schema you used:
DROP SCHEMA main.<your_schema> CASCADE;
```

---

## Architecture Notes

### Why Bootstrap Scripts Exist

Agent9's core value is **analysis of curated data**. It does NOT create, load, or modify data (by design):
- No DDL operations (CREATE, ALTER, DROP)
- No DML operations (INSERT, UPDATE, DELETE)
- Read-only discovery and analysis

Bootstrap utilities exist *outside* Agent9 core specifically because data setup is orthogonal to the analysis workflow. Once customers have real curated views, these utilities can be deleted.

### Why Not Include This in Agent9?

1. **Scope**: Agent9 is an analysis engine, not a data warehouse management tool
2. **Risk**: Write operations require different security/governance than analysis
3. **Deprecation**: Trial utilities get replaced by customer's own data pipeline
4. **Simplicity**: Keeping Agent9 read-only simplifies architecture and security model

---

## Troubleshooting

### Snowflake Connection Error
- Verify account identifier (find in Snowflake account URL)
- Check warehouse exists and is running
- Verify user credentials and permissions

### Databricks Connection Error
- Verify HTTP path matches your SQL warehouse/endpoint
- Check personal access token hasn't expired
- Verify catalog/schema permissions

### Foreign Key Constraint Errors
- Scripts use `IF NOT EXISTS` for idempotency
- If tables exist, try dropping schema and re-running
- Verify warehouse/connection supports foreign keys

---

## Questions?

For Agent9 onboarding questions, see:
- `docs/design/data_product_onboarding_architecture.md`
- `src/services/data_product_onboarding_service.py` (OnboardingService implementation)

For platform-specific issues:
- Snowflake: https://docs.snowflake.com/
- Databricks: https://docs.databricks.com/
