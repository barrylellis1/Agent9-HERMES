# A9_Data_Product_MCP_Service_Agent Card

## Agent Overview

The A9_Data_Product_MCP_Service_Agent is the centralized service for all data operations within Agent9-HERMES. It provides a standardized interface for SQL execution and data access, acting as the single authoritative layer for all dynamic SQL generation for data products. This agent handles registry-driven SELECT, JOIN, GROUP BY, and aggregation SQL to provide business-ready, summarized, filtered, and pre-joined data products.

## Protocol Entrypoints

| Method | Purpose | Input Model | Output Model |
|--------|---------|-------------|--------------|
| `async def execute_sql(request)` | Execute SQL statements against DuckDB | `SQLExecutionRequest` | `SQLExecutionResult` |
| `async def get_data_product(request)` | Retrieve data product based on registry definition | `DataProductRequest` | `DataProductResponse` |

## Configuration

This agent uses the `A9_Data_Product_MCP_Service_Config` model defined in `src/agents/agent_config_models.py`.

Key configuration options:
- `sap_data_path`: Path to SAP DataSphere CSV data files
- `registry_path`: Path to registry data files
- `allow_custom_sql`: Whether to allow custom SQL execution
- `validate_sql`: Whether to validate SQL statements for security

## Dependencies

- **External Libraries**: DuckDB, pandas
- **Data Sources**: SAP DataSphere CSV files
- **Registry Dependencies**: Data product registry

## Error Handling

| Error Type | Handling Strategy | Recovery |
|------------|-------------------|----------|
| Missing Data | Return structured error response | Log detailed error with file path |
| Invalid SQL | Validate and return security error | Reject non-SELECT statements |
| Registry Error | Fallback to direct table access | Log registry failure |
| DuckDB Error | Return detailed error message | Close and reinitialize connection if needed |

## Human-in-the-Loop (HITL)

This agent does not require direct HITL interaction. All data operations are automated with security validation.

## Compliance Status

- **Agent9 Design Standards**: ✅ Compliant
- **Protocol Compliance**: ✅ A2A protocol with Pydantic models
- **Registry Integration**: ✅ Data product registry integration
- **Error Handling**: ✅ Structured error responses
- **Documentation**: ✅ Complete with PRD alignment

## Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2025-08-05 | 0.1.0 | Initial implementation with DuckDB integration |

## Notes

- All SQL operations are validated for security (only SELECT statements allowed)
- The agent supports both direct SQL execution and registry-driven data product access
- CSV files are automatically registered as DuckDB tables at initialization
