# Phase 10C: Multi-Warehouse Connectivity (Snowflake + Databricks)

## Executive Summary

Phase 10C enables Agent9 to connect to customer enterprise data warehouses (Snowflake, Databricks) using schema parsing and native SQL execution. The architecture prioritizes **customer data as-is** — no SQL translation, no enforced ANSI compliance. Customers bring their curated views (with native dialect SQL), Agent9 parses the schema and executes their native SQL through backend-specific managers.

---

## Architecture Decisions

### 1. Schema-Parsing-First Approach (Not SQL Generation)

**Principle:** Customers provide **curated views** with native SQL already optimized for their platform. Agent9 doesn't translate SQL — it parses schemas and executes customer's native SQL as-is.

**Customer Journey:**
1. Customer creates a curated Snowflake/Databricks view (their SQL, their dialect)
2. Customer initiates Data Product Onboarding in Decision Studio
3. Agent9 connects via `SnowflakeManager` / `DatabricksManager`
4. Agent9 queries `INFORMATION_SCHEMA.VIEWS` to fetch the view definition
5. QueryDialect parser extracts: base tables, joins, FK relationships, column lineage
6. Contract YAML stores: **customer's native view SQL** + parsed metadata
7. KPI queries use the **native SQL from the contract** (no translation needed)

**Benefit:** Works with any Snowflake/Databricks schema complexity (UDFs, Iceberg, Unity Catalog, etc.) without Agent9 understanding it.

### 2. Direct SDK Connectors (Phase 10C) → MCP Abstraction (Phase 10D)

**Phase 10C (Now):**
- `SnowflakeManager` and `DatabricksManager` implement `DatabaseManager` ABC
- Direct SDK approach: `snowflake-connector-python`, `databricks-sql-connector`
- Works immediately with trial accounts
- Same execution pattern as BigQueryManager

**Phase 10D (Future):**
- When vendor MCP servers available (Snowflake Cortex MCP, Databricks UC MCP)
- Swap only the `connect()` implementation
- Call sites unchanged (decorator pattern: MCP wrapper around direct SDK)
- No QueryDialect changes needed

### 3. QueryDialect Layer: Schema Parsing Only (Not SQL Translation)

**Scope (Phase 10C):**
- Parse view SQL to extract: table references, joins, column mappings
- Infer semantic roles: fact vs dimension, measure vs dimension
- Build FK relationship graph from parsed SQL
- Store parsed metadata in contract YAML

**Out of Scope (Phase 10D):**
- SQL translation (e.g., BigQuery `EXTRACT(year FROM col)` → Snowflake `YEAR(col)`)
- Date function normalization
- Dialect-specific optimization

**Why:** Customers' native SQL is already correct for their platform. We parse metadata, not translate SQL.

---

## Implementation Roadmap

### Step 1: Create Trial Accounts (User Action)

**Snowflake:**
- Go to https://www.snowflake.com/en/try-snowflake/
- Sign up for 30-day trial ($400 credits)
- Note: account identifier, region, username, password
- Create compute warehouse (Small, 1-2 credits/hour)

**Databricks:**
- Go to https://community.cloud.databricks.com/
- Sign up for Community Edition (free, always-on, 15GB shared cluster)
- Create personal token for API auth
- Note: server hostname, HTTP path, personal access token

**GCS (if using for staging):**
- GCS bucket already exists or create new
- Service account with `storage.objects.create` permission

### Step 2: Create Direct SDK Managers

#### **File:** `src/database/backends/snowflake_manager.py`

```python
class SnowflakeManager(DatabaseManager):
    """Snowflake connector using snowflake-connector-python SDK."""
    
    def __init__(self, config: Dict[str, Any], logger=None):
        # config keys: account, warehouse, database, schema, role (optional)
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.conn = None
    
    async def connect(self, connection_params: Dict[str, Any]) -> bool:
        # connection_params: {user, password} or {user, private_key_path}
        # Build snowflake.connector.connect(account=..., user=..., password=...)
        # Store in self.conn
    
    async def execute_query(self, sql: str, parameters: Dict = None, transaction_id: str = None) -> pd.DataFrame:
        # cursor().execute(sql).fetch_pandas_all()
        # Handle Snowflake-specific exceptions
    
    async def validate_sql(self, sql: str) -> Tuple[bool, Optional[str]]:
        # Only allow SELECT/WITH, block DDL/DML
    
    async def list_views(self, transaction_id: str = None) -> List[str]:
        # Query INFORMATION_SCHEMA.VIEWS where table_type = 'VIEW'
    
    async def create_view(self, view_name: str, sql: str, replace_existing: bool = False, transaction_id: str = None) -> bool:
        # For testing only; production views are customer-managed
    
    # ... implement remaining abstract methods (minimal stubs for read-only usage)
```

**Key differences from BigQueryManager:**
- Uses connection pool (async_reuse_connections=False by default)
- Handles Snowflake's quoted identifier conventions (`"view_name"`)
- Returns pandas DataFrame (via `.fetch_pandas_all()`)

#### **File:** `src/database/backends/databricks_manager.py`

```python
class DatabricksManager(DatabaseManager):
    """Databricks connector using databricks-sql-connector SDK."""
    
    def __init__(self, config: Dict[str, Any], logger=None):
        # config keys: server_hostname, http_path, catalog, schema
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.conn = None
    
    async def connect(self, connection_params: Dict[str, Any]) -> bool:
        # connection_params: {access_token}
        # Build sql.connect(server_hostname=..., http_path=..., access_token=...)
    
    async def execute_query(self, sql: str, parameters: Dict = None, transaction_id: str = None) -> pd.DataFrame:
        # cursor().execute(sql).fetchall_arrow().to_pandas()
        # Databricks returns pyarrow, convert to DataFrame
    
    # ... implement remaining abstract methods
```

**Key differences from BigQueryManager:**
- Uses Databricks SQL Connector (REST API over HTTP)
- Returns pyarrow Table, convert to pandas
- Catalog.Schema.Table three-level naming (vs Project.Dataset.Table in BQ)

### Step 3: QueryDialect Layer for Schema Parsing

#### **File:** `src/database/dialects/__init__.py` (new directory)

```python
"""
QueryDialect abstraction for platform-adaptive schema parsing.

Handles extraction of metadata from view definitions without translating SQL.
Not responsible for SQL generation or normalization.
"""
```

#### **File:** `src/database/dialects/base_dialect.py`

```python
class QueryDialect(ABC):
    """Base class for SQL dialect parsers."""
    
    @abstractmethod
    async def parse_view_definition(self, sql: str) -> ViewMetadata:
        """
        Parse view SQL to extract base tables, joins, and column lineage.
        
        Returns:
            ViewMetadata: {
                base_tables: [table_name, ...],
                joins: [(left_table, right_table, join_condition), ...],
                column_mappings: {derived_col: source_col, ...},
                is_valid: bool
            }
        """
        pass
    
    @abstractmethod
    async def infer_table_role(self, base_tables: List[str], column_stats: Dict) -> str:
        """Infer FACT vs DIMENSION vs BRIDGE role from table characteristics."""
        pass
```

#### **File:** `src/database/dialects/snowflake_dialect.py`

```python
class SnowflakeDialect(QueryDialect):
    """Parser for Snowflake SQL dialect."""
    
    async def parse_view_definition(self, sql: str) -> ViewMetadata:
        """
        Parse Snowflake view SQL using regex + lightweight tokenization.
        
        Extract:
        - Base tables: FROM, JOIN keywords (handle quoted identifiers "schema.table")
        - Join conditions: ON clauses
        - Column mappings: SELECT list aliasing
        
        Not a full parser — just extract enough for FK and lineage inference.
        """
        # Use regex patterns to find:
        # - FROM "schema"."table" AS alias
        # - LEFT JOIN "schema"."table" ON ...
        # - SELECT col1 AS "alias", col2, ...
        pass
    
    async def infer_table_role(self, base_tables: List[str], column_stats: Dict) -> str:
        """
        Heuristics:
        - Fact: multiple base tables, high row count, numeric aggregates
        - Dimension: single base table, low cardinality, text fields
        """
        pass
```

#### **File:** `src/database/dialects/databricks_dialect.py`

```python
class DatabricksDialect(QueryDialect):
    """Parser for Databricks/Spark SQL dialect."""
    
    async def parse_view_definition(self, sql: str) -> ViewMetadata:
        """
        Similar to Snowflake, but handle:
        - Spark SQL syntax: USING DELTA, partition specifications
        - Three-level naming: catalog.schema.table
        """
        pass
```

### Step 4: Update Data Product Agent for Schema Parsing

#### **File:** `src/agents/new/a9_data_product_agent.py`

**Add helper method** (line ~1150):
```python
async def _parse_view_definition_for_contract(
    self, 
    view_sql: str, 
    source_system: str
) -> Dict[str, Any]:
    """
    Parse view definition to extract metadata for contract generation.
    
    Returns:
        {
            "base_tables": ["table1", "table2"],
            "foreign_keys": [ForeignKeyRelationship, ...],
            "column_lineage": {derived_col: base_col},
            "inferred_table_role": "FACT" | "DIMENSION",
            "parse_confidence": 0.95,
            "dialect": "snowflake" | "databricks",
            "notes": "Any parsing caveats"
        }
    """
    from src.database.dialects.snowflake_dialect import SnowflakeDialect
    from src.database.dialects.databricks_dialect import DatabricksDialect
    
    dialect_map = {
        "snowflake": SnowflakeDialect(),
        "databricks": DatabricksDialect(),
    }
    
    dialect = dialect_map.get(source_system.lower())
    if not dialect:
        self.logger.warning(f"No dialect parser for {source_system}, using basic metadata")
        return {"base_tables": [], "parse_confidence": 0.0}
    
    metadata = await dialect.parse_view_definition(view_sql)
    return metadata
```

**Update `generate_contract_yaml()`** (line ~1200):
```python
async def generate_contract_yaml(
    self, 
    request: DataProductContractGenerationRequest
) -> DataProductContractGenerationResponse:
    """
    Generate contract YAML for a curated view.
    
    New: Extract view SQL from INFORMATION_SCHEMA, parse it for metadata.
    Store: customer's native view SQL as-is (no translation).
    """
    # Step 1: Fetch view definition from INFORMATION_SCHEMA
    view_sql = await self._get_view_definition(
        table_name=request.table_name,
        source_system=request.source_system
    )
    
    # Step 2: Parse view SQL for metadata
    parsed_metadata = await self._parse_view_definition_for_contract(
        view_sql, request.source_system
    )
    
    # Step 3: Query INFORMATION_SCHEMA for column metadata
    columns = await self._get_column_profiles(
        table_name=request.table_name,
        source_system=request.source_system
    )
    
    # Step 4: Infer semantic tags + FK relationships
    foreign_keys = parsed_metadata.get("foreign_keys", [])
    
    # Step 5: Generate contract YAML
    contract = {
        "metadata": {
            "id": request.data_product_id,
            "name": request.data_product_name,
            "source_system": request.source_system,
            "view_name": request.table_name,
        },
        "view_definition": view_sql,  # STORE CUSTOMER'S NATIVE SQL AS-IS
        "tables": [
            {
                "name": base_table,
                "role": "FACT" | "DIMENSION",  # from parsed_metadata.inferred_table_role
                "columns": [col for col in columns if col.table == base_table],
            }
        ],
        "relationships": foreign_keys,
        "kpis": request.kpi_proposals or [],
    }
    
    return DataProductContractGenerationResponse(
        data_product_id=request.data_product_id,
        contract_yaml=yaml.dump(contract),
        base_tables=parsed_metadata.get("base_tables", []),
        parse_confidence=parsed_metadata.get("parse_confidence", 0.0),
    )
```

### Step 5: Update Manager Factory

#### **File:** `src/database/manager_factory.py` (lines ~30-45)

```python
from src.database.backends.snowflake_manager import SnowflakeManager
from src.database.backends.databricks_manager import DatabricksManager

_registry: Dict[str, Type[DatabaseManager]] = {
    'duckdb': DuckDBManager,
    'bigquery': BigQueryManager,
    'postgres': PostgresManager,
    'postgresql': PostgresManager,
    'supabase': PostgresManager,
    'snowflake': SnowflakeManager,        # ← NEW
    'databricks': DatabricksManager,       # ← NEW
}
```

### Step 6: Update DPA SQL Routing

#### **File:** `src/agents/new/a9_data_product_agent.py` (line ~3338)

**Current routing (BQ regex only):**
```python
if _BQ_PATTERN.search(sql_query):
    # route to BQ
else:
    # route to DuckDB
```

**New routing (source_system-aware):**
```python
async def execute_sql(
    self, 
    sql_query: Union[str, 'SQLExecutionRequest'], 
    parameters: Optional[Dict[str, Any]] = None, 
    principal_context=None,
    data_product_id: Optional[str] = None  # ← NEW (optional, backward-compatible)
) -> Dict[str, Any]:
    """
    Execute SQL query routing to appropriate backend.
    
    New: If data_product_id provided, look up source_system from registry and route.
    Fall back to current BQ regex + DuckDB logic if no data_product_id.
    """
    # Normalize request
    if isinstance(sql_query, str):
        normalized_sql = sql_query
    else:
        normalized_sql = getattr(sql_query, 'sql', None) or getattr(sql_query, 'sql_query', '')
    
    manager = None
    
    # NEW: Source-system aware routing (if data_product_id provided)
    if data_product_id:
        try:
            data_product = self.data_product_registry.get(data_product_id)
            if data_product:
                source_system = data_product.source_system  # "snowflake", "databricks", etc.
                manager = self._get_connector_for_data_product(source_system)
        except Exception as e:
            self.logger.warning(f"Could not resolve source_system for {data_product_id}: {e}")
    
    # FALLBACK: Current BQ regex + DuckDB logic
    if not manager:
        if _BQ_PATTERN.search(sql_query):
            manager = await self._ensure_bq_connected()
        else:
            manager = self.db_manager  # DuckDB default
    
    # Execute using resolved manager
    return await manager.execute_query(normalized_sql, parameters, transaction_id)

def _get_connector_for_data_product(self, source_system: str):
    """Get or create connector for the given source system."""
    source_system_lower = source_system.lower()
    
    if source_system_lower == "snowflake":
        if not hasattr(self, '_snowflake_manager') or self._snowflake_manager is None:
            from src.database.manager_factory import DatabaseManagerFactory
            config = self._get_connection_config_for_source(source_system)
            self._snowflake_manager = DatabaseManagerFactory.create_manager(
                "snowflake", config, self.logger
            )
        return self._snowflake_manager
    
    elif source_system_lower == "databricks":
        if not hasattr(self, '_databricks_manager') or self._databricks_manager is None:
            from src.database.manager_factory import DatabaseManagerFactory
            config = self._get_connection_config_for_source(source_system)
            self._databricks_manager = DatabaseManagerFactory.create_manager(
                "databricks", config, self.logger
            )
        return self._databricks_manager
    
    elif source_system_lower == "bigquery":
        return await self._ensure_bq_connected()
    
    else:
        self.logger.warning(f"Unknown source system: {source_system}, using DuckDB")
        return self.db_manager
```

### Step 7: Update Connection Profiles

#### **File:** `config/connection_profiles.yaml`

Add two new profiles:

```yaml
- name: snowflake-trial
  system_type: snowflake
  account: <account_identifier>       # e.g., xy12345.us-east-1
  warehouse: compute_wh               # Snowflake warehouse name
  database: <database_name>           # e.g., analytics
  schema: <schema_name>               # e.g., public
  role: analyst                       # optional, default role
  username: <snowflake_user>          # Stored as-is
  password_saved: false               # Password from env var only
  extras:
    password_env: SNOWFLAKE_PASSWORD  # Env var name for password
  
- name: databricks-community
  system_type: databricks
  host: <server_hostname>             # e.g., adb-123456.cloud.databricks.com
  extras:
    http_path: /sql/1.0/warehouses/<warehouse_id>  # From Databricks workspace
    token_env: DATABRICKS_TOKEN       # Env var for personal access token
```

**Credentials (not in YAML):**
- Export env vars before connecting:
  ```bash
  export SNOWFLAKE_PASSWORD="..."
  export DATABRICKS_TOKEN="..."
  ```

### Step 8: Register Snowflake/Databricks Data Products

#### **File:** `src/registry/data_product/data_product_registry.yaml` (add entries)

```yaml
data_products:
  # ... existing BigQuery entry ...
  
  - product_id: "fi_star_schema_snowflake"
    name: "FI Star Schema (Snowflake)"
    domain: "Finance"
    source_system: "snowflake"
    connection_profile: "snowflake-trial"
    tags: ["snowflake", "trial", "demo"]
    yaml_contract_path: "src/registry_references/data_product_registry/data_products/fi_star_schema_snowflake.yaml"
  
  - product_id: "fi_star_schema_databricks"
    name: "FI Star Schema (Databricks)"
    domain: "Finance"
    source_system: "databricks"
    connection_profile: "databricks-community"
    tags: ["databricks", "trial", "demo"]
    yaml_contract_path: "src/registry_references/data_product_registry/data_products/fi_star_schema_databricks.yaml"
```

### Step 9: Create Contract YAMLs for Trial Data Products

#### **File:** `src/registry_references/data_product_registry/data_products/fi_star_schema_snowflake.yaml`

This contract is generated by the **onboarding workflow**. It contains:
- Customer's native view SQL (from Snowflake)
- Parsed metadata: base tables, FK relationships, column lineage
- Semantic tags and KPI candidates

```yaml
metadata:
  id: fi_star_schema_snowflake
  name: FI Star Schema (Snowflake)
  source_system: snowflake
  description: "Financial data from Snowflake, same structure as BigQuery version"

# Store customer's native Snowflake SQL as-is (no translation)
view_definition: |
  CREATE OR REPLACE VIEW analytics.fi_star_view AS
  SELECT
    ft.transaction_id,
    EXTRACT(YEAR FROM ft.transaction_date) AS fiscal_year,
    EXTRACT(QUARTER FROM ft.transaction_date) AS fiscal_quarter,
    ...
  FROM raw.financial_transactions ft
  LEFT JOIN dim.profit_centers pc ON ft.profit_center_id = pc.profit_center_id
  ...

# Parsed metadata from onboarding
base_tables:
  - name: raw.financial_transactions
    role: FACT
  - name: dim.profit_centers
    role: DIMENSION

relationships:
  - source_table: raw.financial_transactions
    source_column: profit_center_id
    target_table: dim.profit_centers
    target_column: profit_center_id
    confidence: 1.0

columns:
  - name: transaction_id
    data_type: VARCHAR
    semantic_tags: [identifier]
  - name: fiscal_year
    data_type: NUMBER
    semantic_tags: [time]
  - name: transaction_value
    data_type: DECIMAL(18,2)
    semantic_tags: [measure]
  # ... etc

kpis:
  - name: Gross Revenue
    expression: SUM(transaction_value)
    grain: fiscal_month
    dimensions: [profit_center_id, product_id]
    # ... etc
```

### Step 10: Write Tests

#### **File:** `tests/unit/test_snowflake_databricks_connectivity.py`

```python
"""Tests for Phase 10C: Snowflake and Databricks connectors."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.database.backends.snowflake_manager import SnowflakeManager
from src.database.backends.databricks_manager import DatabricksManager
from src.database.manager_factory import DatabaseManagerFactory
from src.database.dialects.snowflake_dialect import SnowflakeDialect


class TestSnowflakeManager:
    """Unit tests for SnowflakeManager."""
    
    @pytest.mark.asyncio
    async def test_snowflake_manager_creation(self):
        """Verify SnowflakeManager instantiation and registration."""
        config = {
            "account": "test-account",
            "warehouse": "test_wh",
            "database": "test_db",
            "schema": "public"
        }
        manager = SnowflakeManager(config)
        assert manager.config == config
    
    @pytest.mark.asyncio
    async def test_snowflake_connection_validation(self):
        """Verify connection validation (mock Snowflake SDK)."""
        config = {
            "account": "test-account",
            "warehouse": "test_wh",
            "database": "test_db",
            "schema": "public"
        }
        manager = SnowflakeManager(config)
        
        with patch('snowflake.connector.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn
            
            connection_params = {"user": "test_user", "password": "test_pwd"}
            result = await manager.connect(connection_params)
            
            assert result is True
            mock_connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_snowflake_sql_validation_blocks_ddl(self):
        """Verify SQL validation blocks DDL statements."""
        manager = SnowflakeManager({})
        
        is_valid, error = await manager.validate_sql("CREATE TABLE foo (id INT)")
        assert not is_valid
        assert "DDL" in error or "CREATE" in error
    
    @pytest.mark.asyncio
    async def test_snowflake_sql_allows_select(self):
        """Verify SQL validation allows SELECT."""
        manager = SnowflakeManager({})
        
        is_valid, error = await manager.validate_sql("SELECT * FROM my_table")
        assert is_valid
        assert error is None


class TestDatabricksManager:
    """Unit tests for DatabricksManager."""
    
    @pytest.mark.asyncio
    async def test_databricks_manager_creation(self):
        """Verify DatabricksManager instantiation and registration."""
        config = {
            "server_hostname": "adb-123456.cloud.databricks.com",
            "http_path": "/sql/1.0/warehouses/abc123",
            "catalog": "main",
            "schema": "default"
        }
        manager = DatabricksManager(config)
        assert manager.config == config
    
    @pytest.mark.asyncio
    async def test_databricks_connection_validation(self):
        """Verify connection validation (mock Databricks SDK)."""
        config = {
            "server_hostname": "adb-123456.cloud.databricks.com",
            "http_path": "/sql/1.0/warehouses/abc123",
            "catalog": "main",
            "schema": "default"
        }
        manager = DatabricksManager(config)
        
        with patch('databricks.sql.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn
            
            connection_params = {"access_token": "test_token"}
            result = await manager.connect(connection_params)
            
            assert result is True
            mock_connect.assert_called_once()


class TestQueryDialect:
    """Tests for QueryDialect schema parsing."""
    
    @pytest.mark.asyncio
    async def test_snowflake_dialect_parses_view_definition(self):
        """Verify SnowflakeDialect can parse view SQL."""
        dialect = SnowflakeDialect()
        
        view_sql = """
        CREATE OR REPLACE VIEW analytics.sales_view AS
        SELECT 
            s.sale_id,
            s.amount,
            c.customer_name
        FROM raw.sales s
        LEFT JOIN dim.customers c ON s.customer_id = c.customer_id
        """
        
        metadata = await dialect.parse_view_definition(view_sql)
        
        assert "raw.sales" in metadata.base_tables or "sales" in metadata.base_tables
        assert "dim.customers" in metadata.base_tables or "customers" in metadata.base_tables
        assert len(metadata.column_mappings) > 0
    
    @pytest.mark.asyncio
    async def test_snowflake_dialect_infers_fact_vs_dimension(self):
        """Verify role inference (fact vs dimension)."""
        dialect = SnowflakeDialect()
        
        # Mock: a view with multiple base tables + high numeric columns = FACT
        base_tables = ["sales", "customers", "products"]
        column_stats = {
            "numeric_columns": 5,
            "text_columns": 2,
            "date_columns": 1
        }
        
        role = await dialect.infer_table_role(base_tables, column_stats)
        assert role == "FACT"


class TestDPASchemaParsingIntegration:
    """Tests for DPA schema parsing in contract generation."""
    
    @pytest.mark.asyncio
    async def test_dpa_parses_snowflake_view_for_contract(self):
        """Verify DPA can extract view SQL and parse it for contract."""
        # Setup: mock DPA with Snowflake manager
        dpa = A9_Data_Product_Agent(config={})
        dpa._snowflake_manager = AsyncMock(spec=SnowflakeManager)
        dpa.data_product_registry = MagicMock()
        
        # Mock INFORMATION_SCHEMA.VIEWS response
        view_sql = """
        SELECT 
            ft.id,
            SUM(ft.amount) AS total_amount
        FROM fact_table ft
        LEFT JOIN dim_table dt ON ft.dim_id = dt.id
        GROUP BY ft.id
        """
        
        # Call parse method
        parsed = await dpa._parse_view_definition_for_contract(
            view_sql, "snowflake"
        )
        
        assert parsed["base_tables"]  # Should extract fact_table, dim_table
        assert len(parsed.get("foreign_keys", [])) > 0
        assert parsed["parse_confidence"] > 0.0


class TestFactoryRegistration:
    """Tests for manager factory registration."""
    
    def test_factory_has_snowflake_registered(self):
        """Verify Snowflake is registered in factory."""
        supported = DatabaseManagerFactory.get_supported_backends()
        assert "snowflake" in supported
        assert supported["snowflake"] == SnowflakeManager
    
    def test_factory_has_databricks_registered(self):
        """Verify Databricks is registered in factory."""
        supported = DatabaseManagerFactory.get_supported_backends()
        assert "databricks" in supported
        assert supported["databricks"] == DatabricksManager
    
    def test_factory_creates_snowflake_manager(self):
        """Verify factory can create SnowflakeManager."""
        config = {"account": "test", "warehouse": "wh"}
        manager = DatabaseManagerFactory.create_manager("snowflake", config)
        assert isinstance(manager, SnowflakeManager)
    
    def test_factory_creates_databricks_manager(self):
        """Verify factory can create DatabricksManager."""
        config = {"server_hostname": "test.cloud.databricks.com", "http_path": "/sql"}
        manager = DatabaseManagerFactory.create_manager("databricks", config)
        assert isinstance(manager, DatabricksManager)
```

### Step 11: Update Documentation

#### **File:** `docs/architecture/phase_10c_snowflake_databricks_connectivity.md`

```markdown
# Phase 10C: Snowflake & Databricks Connectivity

## Architecture Overview

Phase 10C enables Agent9 to connect to customer data warehouses (Snowflake, Databricks) through:
1. **Direct SDK Managers** — SnowflakeManager, DatabricksManager implementing DatabaseManager ABC
2. **QueryDialect Parsers** — Parse customer view SQL to extract schema metadata
3. **Schema-Parsing-First Workflow** — Customer brings curated views, we extract metadata, execute native SQL

## Customer Workflow

1. Customer creates Snowflake/Databricks view with native SQL
2. Customer initiates Data Product Onboarding in Decision Studio
3. Agent9 connects and queries INFORMATION_SCHEMA.VIEWS to fetch view definition
4. QueryDialect parser extracts: base tables, FK relationships, column lineage
5. Contract YAML stores: **customer's native view SQL** + parsed metadata
6. KPI queries execute customer's native SQL (no translation)

## Connection Setup

### Snowflake Trial
```bash
export SNOWFLAKE_PASSWORD="your_password"
# Then connect via Decision Studio Admin Console
```

### Databricks Community
```bash
export DATABRICKS_TOKEN="your_personal_access_token"
# Then connect via Decision Studio Admin Console
```

## QueryDialect: Why No SQL Translation?

Customer views are already optimized for their platform. Translating SQL would:
- Lose optimizations (index hints, Iceberg table pruning, etc.)
- Introduce dialect bugs (EXTRACT vs YEAR vs DATE_TRUNC differences)
- Require dialect expertise we don't have

Instead, we parse metadata and execute customer's native SQL as-is.

## Testing

Mock-based unit tests verify:
- Manager creation and connection validation
- SQL validation (blocks DDL, allows SELECT)
- QueryDialect parsing extracts base tables and FK relationships
- Factory registration of both managers
- DPA can parse views for contract generation

Integration tests (requires live trial accounts):
- Full onboarding workflow: inspect → parse → generate contract
- KPI execution against Snowflake/Databricks views
- Results identical to BigQuery version (same FI Star Schema)

---

**Next Phase (10D):** QueryDialect layer extended to MCP abstraction for vendor-managed servers.
```

---

## Summary

| Component | Purpose |
|-----------|---------|
| **SnowflakeManager** | Direct SDK connector, implements DatabaseManager ABC |
| **DatabricksManager** | Direct SDK connector, implements DatabaseManager ABC |
| **QueryDialect parsers** | Extract schema metadata from customer view SQL (no translation) |
| **DPA updates** | Schema parsing integration, source_system-aware SQL routing |
| **Manager Factory** | Register Snowflake + Databricks backends |
| **Connection Profiles** | Trial account credentials (passwords via env vars) |
| **Data Product Registry** | Register Snowflake/Databricks data products |
| **Contract YAMLs** | Store customer's native SQL + parsed metadata |
| **Tests** | Mock unit tests + integration tests (when accounts available) |

---

## Critical Constraints

1. **No SQL Translation**: Customer's native SQL is executed as-is. QueryDialect parses schema only.
2. **Read-Only Execution**: SELECT/WITH only, no DDL/DML in customer views.
3. **Connection Profiles**: Passwords from env vars only (never stored in YAML).
4. **Phase 10D Gate**: MCP abstraction deferred until vendor MCP servers available.

---

## Success Criteria

- [ ] SnowflakeManager + DatabricksManager implement full DatabaseManager ABC
- [ ] QueryDialect parsers extract base tables + FK relationships from view SQL
- [ ] Data Product Onboarding workflow works with Snowflake/Databricks views
- [ ] Same KPIs execute identically against BigQuery, Snowflake, Databricks
- [ ] Contract YAMLs store customer's native SQL (no translation)
- [ ] Unit tests pass with 95%+ coverage
- [ ] Integration tests pass with trial accounts (optional, user's discretion)
