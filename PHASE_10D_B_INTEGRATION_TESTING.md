# Phase 10D-B: Integration Testing with Vendor MCP Servers

**Goal:** Validate MCPClient, MCPManager, and OnboardingService against real Snowflake and Databricks MCP endpoints.

**Status:** Ready for trial account setup and testing

---

## Prerequisites

### 1. Snowflake Trial Account Setup

**Step 1: Create Snowflake account**
- Go to https://signup.snowflake.com/ and create a trial account
- Note your account URL (e.g., `xy12345.us-east-1.snowflake.app`)
- Create a user with ACCOUNTADMIN role for testing

**Step 2: Enable Snowflake Managed MCP (if available)**
- Snowflake announced managed MCP in public preview
- Check Snowflake documentation for MCP endpoint availability
- May require enterprise edition or specific region

**Step 3: Obtain MCP credentials**
- Create OAuth 2.0 integration for MCP access
- OR use service account with PAT token
- Document endpoint URL and auth token

**Reference:** 
- [Snowflake Managed MCP Server](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-mcp)
- [GitHub Snowflake-Labs/mcp](https://github.com/Snowflake-Labs/mcp)

---

### 2. Databricks Trial Account Setup

**Step 1: Create Databricks workspace**
- Go to https://databricks.com/ and create trial workspace
- Choose cloud (AWS/Azure/GCP) and region
- Create a cluster for testing

**Step 2: Enable MCP support**
- Databricks has managed MCP in GA (general availability)
- Check workspace settings for MCP server availability
- May require specific workspace configuration

**Step 3: Obtain MCP credentials**
- Generate personal access token (PAT) for MCP access
- Document endpoint URL and token
- Ensure workspace is configured for external MCP server access

**Reference:**
- [MCP on Databricks (AWS)](https://docs.databricks.com/aws/en/generative-ai/mcp/)
- [MCP on Databricks (Azure)](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/mcp/)

---

## Validation Checklist

### Phase 10D-B-1: MCPClient Transport Testing

**Test:** Establish connection and list available tools

```python
# tests/unit/test_phase_10d_b_integration.py
import pytest
import os
from src.database.mcp_client import MCPClient

@pytest.mark.skipif(
    not os.getenv("SNOWFLAKE_MCP_ENDPOINT"),
    reason="Set SNOWFLAKE_MCP_ENDPOINT and SNOWFLAKE_MCP_TOKEN to test"
)
@pytest.mark.asyncio
async def test_snowflake_mcp_client_connection():
    endpoint = os.getenv("SNOWFLAKE_MCP_ENDPOINT")
    token = os.getenv("SNOWFLAKE_MCP_TOKEN")
    auth_type = os.getenv("SNOWFLAKE_MCP_AUTH", "bearer")
    
    client = MCPClient(
        endpoint=endpoint,
        auth_token=token,
        auth_type=auth_type
    )
    
    # List available tools
    tools = await client.list_tools()
    print(f"Available tools: {tools}")
    
    # Expected tools (adjust based on actual vendor MCP)
    # For Snowflake: sql_execute, cortex_analyst_*, etc.
    # For Databricks: sql_execute, unity_catalog_*, etc.
    assert len(tools) > 0, "MCP server returned no tools"
    
    await client.close()
```

**Run:**
```bash
# Snowflake
SNOWFLAKE_MCP_ENDPOINT="https://snowflake-mcp-endpoint" \
SNOWFLAKE_MCP_TOKEN="your-token" \
SNOWFLAKE_MCP_AUTH="bearer" \
pytest tests/unit/test_phase_10d_b_integration.py::test_snowflake_mcp_client_connection -v

# Databricks
DATABRICKS_MCP_ENDPOINT="https://databricks-mcp-endpoint" \
DATABRICKS_MCP_TOKEN="your-pat-token" \
DATABRICKS_MCP_AUTH="pat" \
pytest tests/unit/test_phase_10d_b_integration.py::test_databricks_mcp_client_connection -v
```

**Expected Outcome:**
- ✅ Connection succeeds
- ✅ MCP server returns list of available tools
- ✅ Document actual tool names for implementation update

---

### Phase 10D-B-2: Tool Invocation Testing

**Test:** Execute actual queries via MCP

```python
@pytest.mark.asyncio
async def test_snowflake_mcp_sql_execution():
    client = MCPClient(
        endpoint=os.getenv("SNOWFLAKE_MCP_ENDPOINT"),
        auth_token=os.getenv("SNOWFLAKE_MCP_TOKEN")
    )
    
    # Test simple query
    result = await client.call_tool("sql_execute", {
        "sql": "SELECT 1 as test_col"
    })
    
    print(f"Result: {result.get_text()}")
    assert not result.is_error, f"Query failed: {result.get_text()}"
    
    await client.close()
```

**Expected Outcome:**
- ✅ Query executes without error
- ✅ Result returns in expected format (JSON/CSV)
- ✅ Data is parseable into pandas DataFrame
- ✅ Document result format for MCPManager parser

---

### Phase 10D-B-3: MCPManager Integration Testing

**Test:** End-to-end OnboardingService + MCPManager workflow

```python
@pytest.mark.asyncio
async def test_snowflake_mcp_manager_discover_schemas():
    config = {
        "mcp_endpoint": os.getenv("SNOWFLAKE_MCP_ENDPOINT"),
        "schema": "PUBLIC"
    }
    
    manager = MCPManager(vendor="snowflake", config=config)
    
    connected = await manager.connect({
        "mcp_endpoint": os.getenv("SNOWFLAKE_MCP_ENDPOINT"),
        "auth_token": os.getenv("SNOWFLAKE_MCP_TOKEN"),
        "mcp_auth_type": "bearer"
    })
    
    assert connected, "Failed to connect to MCP server"
    
    # List views
    views = await manager.list_views()
    print(f"Available views: {views}")
    
    # Execute query
    df = await manager.execute_query("SELECT 1 as col")
    assert not df.empty, "Query returned empty DataFrame"
    
    await manager.disconnect()
```

**Expected Outcome:**
- ✅ MCPManager connects successfully
- ✅ Schema discovery works
- ✅ Query execution works
- ✅ Results parse to DataFrame correctly

---

### Phase 10D-B-4: OnboardingService Integration

**Test:** Full data product discovery workflow

```python
@pytest.mark.asyncio
async def test_snowflake_onboarding_end_to_end():
    from src.services.data_product_onboarding_service import DataProductOnboardingService
    
    service = DataProductOnboardingService()
    
    # Connect via MCP
    connected = await service.connect(
        connection_config={
            "mcp_endpoint": os.getenv("SNOWFLAKE_MCP_ENDPOINT"),
            "schema": "PUBLIC"
        },
        source_system="snowflake_mcp",
        connection_params={
            "mcp_endpoint": os.getenv("SNOWFLAKE_MCP_ENDPOINT"),
            "auth_token": os.getenv("SNOWFLAKE_MCP_TOKEN"),
            "mcp_auth_type": "bearer"
        }
    )
    
    assert connected, "Failed to connect via OnboardingService"
    
    # Discover tables/views
    tables, errors = await service.discover_tables(schema="PUBLIC")
    print(f"Discovered tables: {tables}")
    assert len(tables) > 0 or len(errors) == 0, f"Discovery failed: {errors}"
    
    await service.disconnect()
```

**Expected Outcome:**
- ✅ OnboardingService works with MCP managers
- ✅ Dialect selection works for `*_mcp` source systems
- ✅ Full workflow: connect → discover → profile → extract FKs → generate contract

---

## Known Issues to Watch For

### Snowflake MCP
1. **Public Preview Status:** Tool names or endpoints may change before GA
2. **Authentication:** May require OAuth 2.0 instead of bearer tokens
3. **Cortex Requirements:** Some tools may require Cortex license or Enterprise edition
4. **Region Availability:** MCP may only be available in specific regions

### Databricks MCP
1. **Workspace Configuration:** MCP may require workspace admin approval
2. **Network Policies:** May have network policy restrictions for external MCP
3. **Token Expiration:** PAT tokens may have short expiration times
4. **Tool Availability:** Tool names depend on Databricks version and MCP version

---

## Implementation Updates Based on Test Results

Once testing reveals actual vendor tool names and response formats:

### Update `src/database/backends/mcp_manager.py`

```python
# Update VENDOR_TOOL_MAPS based on discovered tool names
VENDOR_TOOL_MAPS = {
    "snowflake": {
        "execute_query": "<ACTUAL_TOOL_NAME>",  # Update from testing
        "list_views": "<ACTUAL_TOOL_NAME>",
        "get_metadata": "<ACTUAL_TOOL_NAME>",
    },
    "databricks": {
        "execute_query": "<ACTUAL_TOOL_NAME>",  # Update from testing
        "list_views": "<ACTUAL_TOOL_NAME>",
        "get_metadata": "<ACTUAL_TOOL_NAME>",
    },
}

# Update result parsing if format differs from JSON/CSV
def _parse_mcp_result(self, result_text: str) -> pd.DataFrame:
    # Adjust based on actual vendor response format
    pass
```

### Document Findings

Create `PHASE_10D_B_FINDINGS.md` with:
- Actual tool names for each vendor
- Result formats (JSON/CSV/other)
- Authentication methods that work
- Any quirks or workarounds needed
- Performance characteristics

---

## Success Criteria

- ✅ MCPClient connects to both Snowflake and Databricks MCP endpoints
- ✅ Tool listing returns available tools
- ✅ SQL execution works and returns results
- ✅ MCPManager integrates with OnboardingService
- ✅ Full discovery workflow succeeds
- ✅ Results parse correctly to DataFrames
- ✅ Actual vendor tool names documented
- ✅ Any issues/workarounds discovered and fixed

---

## Timeline

1. **Setup trial accounts** (1-2 hours)
   - Create Snowflake + Databricks accounts
   - Obtain MCP endpoints and auth tokens
   - Verify basic connectivity

2. **Run unit tests against real endpoints** (2-3 hours)
   - MCPClient connection tests
   - Tool invocation tests
   - Document actual tool names

3. **Fix implementation based on findings** (2-4 hours)
   - Update VENDOR_TOOL_MAPS if needed
   - Fix result parsing if needed
   - Update error handling if needed

4. **Full integration workflow testing** (1-2 hours)
   - OnboardingService discovery
   - Contract generation
   - End-to-end validation

**Total estimated time:** 6-11 hours (spread over 1-2 days)

---

## Next After Integration Testing

Once Phase 10D-B integration tests pass:
- Move to Phase 10D-C: Admin Console UI implementation
- UI will support both SDK and MCP connection methods for Snowflake + Databricks
- Full 8-step onboarding workflow
