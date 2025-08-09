# A9_Data_Product_Agent Product Requirements Document

<!-- 
CANONICAL PRD DOCUMENT
This is the official, canonical PRD document for this agent.
Last updated: 2025-07-17
-->


## 1. Overview

### 1.1 Purpose
The A9_Data_Product_Agent manages the lifecycle of data products, including creation, version management, deployment tracking, and usage monitoring. It leverages the Unified Registry Access Layer to discover, register, and provide access to data products. It follows Agent9's architectural principles of simplicity, independence, and reliability.

### 1.2 Scope
This document outlines the requirements for version 1.0 of the A9_Data_Product_Agent, focusing on core data product management capabilities.

### 1.3 Target Audience
- System Administrators
- Data Engineers
- Business Analysts
- Data Scientists

## 2. Business Requirements

### 2.1 Business Objectives
1. Provide a standardized interface for data product management
2. Enable efficient data product lifecycle management
3. Support data quality and performance monitoring
4. Facilitate integration with data systems

### 2.2 Key Metrics
- Data processing latency: < 1 second
- Data quality metrics accuracy: > 95%
- System availability: 99.9% uptime
- Error rate: < 1%

## 3. Functional Requirements

### 3.1 Core Data Product Management

#### 3.1.1 Data Product Creation and Registry Integration
- Create new data products with unique IDs
- Configure product properties including version and capabilities
- Set up versioning and status tracking
- Define data sources and transformations
- Register data products with the Unified Registry Access Layer
- Support loading data products from various sources (YAML, JSON, Python modules)
- Provide registry access to data product definitions for other agents

#### 3.1.2 Data Processing
- All data access, joining, filtering, and aggregation must be performed exclusively by the MCP (DuckDB backend) service.
- The agent must never use direct pandas, file I/O, or agent-side data transformation in production.
- The agent only requests and processes business-ready, pre-joined, and pre-aggregated data from MCP endpoints.
- Handle data quality validation and monitor processing performance based on MCP responses only.

#### 3.1.3 Analysis
- Calculate quality metrics (completeness, consistency, accuracy, timeliness)
- Track performance metrics (processing time, resource usage, throughput)
- Monitor usage metrics (requests, errors, success rate)
- Generate comprehensive analysis reports

#### 3.1.4 Data Product Discovery & Matching with Registry Integration (NEW, MVP Alignment)
- Leverage the Unified Registry Access Layer to discover data products
- Map business processes and KPIs to relevant data products
- Use the Data Product Provider to find data products by attribute, domain, or business process
- Support both legacy enum-based discovery and new registry-based discovery

### 3.1.5 LLM Explainability Compliance (2025-06-24)
- All summary and recommendation text fields are routed through the A9_LLM_Service_Agent for explainability and business-user-friendly output.
- LLM calls are protocol-compliant, orchestrator-driven, and fully async with structured event logging and error handling.
- See agent card for implementation and compliance details.
- Accept technical process names and code values as input (not business English)
- Example interface:
  - `async def find_products_for_processes(processes: List[str]) -> List[Dict]`
- Input must be output from Data Governance Agent (already translated)
- Output: List of data products/KPIs, each with technical metadata (e.g., name, description, attributes)
- Example:
```python
# Input (from governance agent)
tech_processes = ["REV_BY_BU", "COST_BY_PROD"]
kpis = await data_product_agent.find_products_for_processes(tech_processes)
# Output
[
  {"name": "REV_BY_BU", "description": "Revenue by Business Unit", "attributes": ["BU_CODE", "REV_AMT"]},
  {"name": "COST_BY_PROD", "description": "Cost by Product Line", "attributes": ["PROD_CODE", "COST_AMT"]}
]
```
- Must validate all input terms and handle unmapped processes with robust error handling
- Log all matching attempts, successes, and failures

### 3.2 Error Handling

#### 3.2.1 Error Response Format
All error responses must be in the following format:
```python
{
    'status': str,  # Must be one of: 'success', 'partial_error', 'error'
    'error': str,   # Detailed error message
    'timestamp': str,  # ISO format timestamp
    'method': str   # Calling method name
}
```

#### 3.2.2 Status Codes
- 'success': Operation completed successfully
- 'partial_error': Validation error occurred, some data may be processed
- 'error': Processing or connection error occurred, operation failed

#### 3.2.3 Error Types and Messages
- ConfigurationError: "Invalid configuration: {specific_error}"
- RegistrationError: "Failed to register with registry: {specific_error}"
- ProcessingError: "Processing error: {specific_error}"
- ValidationError: "Validation error: {specific_error}"
- TypeError: "Invalid type: {expected_type}. Received: {received_type}"
- FormatError: "Invalid format: {expected_format}. Received: {received_format}"
- MissingFieldError: "Missing required field: {field_name}"
- EmptyValueError: "Empty value for required field: {field_name}"
- ConnectionError: "Connection error: {specific_error}"

#### 3.2.4 Error Handling Requirements
- All methods must validate input parameters before processing
- Must use template's error handling patterns
- Must return error responses instead of raising exceptions
- Error logging must include:
  - Method name
  - Error type
  - Detailed error message
  - Timestamp
  - Stack trace (for processing errors)
- Error responses must be consistent across all methods
- Must handle all error types with appropriate status codes
- Must validate configuration on initialization
- Must validate data format before processing

#### 3.2.5 Registry & Integration Requirements (NEW, MVP Alignment)
- Must use template's register_with_registry method
- Must properly handle registration errors
- Must return proper error responses on failure
- Must properly set up registry reference
- Must validate agent ID format before registration
- Must handle concurrent registration attempts
- All discovery/matching functions must be async
- Input must be compatible with Data Governance Agent output
- Registry integration must follow A9_Agent_Template
- Log all integration attempts and failures

#### 3.2.6 Test Requirements (NEW, MVP Alignment)
- All methods must have test cases for:
  - Success scenarios
  - Validation error scenarios
  - Processing error scenarios
  - Connection error scenarios (where applicable)
  - Integration with Data Governance Agent (input translation)
  - Integration with Principal Context Agent (end-to-end flow)
- Test cases must verify:
  - Return type (Dict[str, Any]) or List[Dict]
  - Status code
  - Error message (if applicable)
  - Timestamp presence
  - Method name in response
  - Input validation for technical terms/code values
- Error messages must match exactly what's expected
- Status codes must be properly checked
- Timestamps must be present in responses
- Method names must be correct in responses

### 3.3 Configuration Management
- Support default configuration values
- Validate configuration on initialization
- Maintain configuration state
- Handle agent-specific settings
- Configuration fields:
  - name
  - version
  - capabilities
  - error_handling

### 3.4 Logging
- Initialize agent-specific logger
- Log initialization and major operations
- Support different log levels (INFO, ERROR)
- Include timestamps in logs
- Log error details with stack traces

## 4. Non-Functional Requirements

### 4.1 Performance
- Process data in real-time
- Handle large data volumes
- Maintain consistent performance
- Support concurrent operations

### 4.2 Reliability
- High availability architecture
- Automatic failover
- Data backup and recovery
- Error handling and recovery

## 5. Technical Requirements

### 5.0 Registry Architecture Integration
- Must integrate with the Unified Registry Access Layer
- Must use the Registry Factory to access providers
- Must use the Data Product Provider for all data product operations
- Must support loading data products from YAML contracts
- Must support data product registration from multiple sources
- Must provide backward compatibility for legacy code using enum values

### 5.1 Protocol Compliance Update (2025-06-24)
- All entrypoints accept only protocol-compliant models: `DataProductNLQSearchInput` and `DataAssetPathRequest` as input; `DataProductNLQSearchOutput` and `DataAssetPathResponse` as output.
- No legacy, deprecated, or stub models are permitted.
- Agent must be instantiated and registered only by the orchestrator; constructor requires a registry reference.
- `register_with_registry` only stores the registry reference, never performs registration.
- All event logging is async/awaited and uses `A9_SharedLogger`.
- All protocol-compliant workflows must propagate and utilize `yaml_contract_text` from the context kwarg.
- All usage and test examples must reflect orchestrator-driven patterns.

### 5.1 System Architecture
- Microservices-based architecture
- RESTful API interface
- Containerized deployment

### 5.2 Performance Optimization
- Implements YAML contract caching mechanism (`_yaml_contract_cache` and `_get_yaml_contract` method)
- Optimizes repeated contract access during agent operation
- Reduces redundant parsing and processing of YAML contracts

### 5.3 Testing and Integration Support
- Provides `load_synthetic_data` method for testing and integration scenarios
- Implements `get_kpi_values` method for querying synthetic KPI data
- Supports development and testing environments with synthetic data generation

### 5.4 User Preference Management
- Includes `get_user_variance_threshold` method for retrieving user-specific preferences
- Supports personalized data presentation based on user settings
- Enables customized threshold configuration for variance reporting

### 5.5 Agent-to-Agent Communication
- Implements `context_handoff_a2a` method for protocol-compliant context handoff
- Provides `product_documentation_qna_a2a` method for documentation Q&A functionality
- Supports standardized inter-agent communication patterns
- Cloud-native design

### 5.2 Technology Stack
- Python 3.10+
- FastAPI for REST API
- SQLAlchemy for database
- Docker for containerization
- Kubernetes for orchestration

### 5.3 Integration Points
- Data systems
- Logging infrastructure
- Monitoring system
- Agent registry

### 5.4 Module Structure and Imports
- Error handling module structure:
  - All error classes should be exported through the package's __init__.py
  - Error classes should be organized in a dedicated sub-module
  - Common error types should be accessible via the package root
- Import patterns:
  - Use relative imports within agent packages
  - Use explicit import paths for external dependencies
  - Follow PEP 8 import ordering:
    1. Standard library imports
    2. Third-party imports
    3. Local application imports
  - Example import structure:
    ```python
    from typing import Dict, Any  # Standard library
    import pandas as pd            # Third-party
    from ..agent_registry import AgentRegistry  # Local relative import
    from ..errors import ConfigurationError  # Local relative import
    ```

## 6. Implementation Phases

### Phase 1: Core Implementation (1 week)
- Basic data product management
- Core data processing
- Basic error handling
- Initial logging setup

### Phase 2: Advanced Features (1 week)
- Advanced error handling
- Configuration management
- Enhanced logging
- Performance optimization

## 7. Dependencies

### 7.1 External Dependencies
- Data storage systems
- Logging services
- Monitoring services
- Configuration management

### 7.2 Internal Dependencies
- Unified Registry Access Layer
- Registry Factory and Providers
- Logging Infrastructure
- Monitoring System

## 7.5 Implementation Alignment (2025-04-17)

### Recent Updates (v1.1+)
- **MCP Service-Only Architecture:**
  - All data access, joining, filtering, and aggregation logic is now handled exclusively by the MCP (DuckDB backend) service.
  - The agent no longer uses pandas, direct file I/O, or agent-side data transformation in production.
  - All registry integration and data product onboarding must be performed via MCP endpoints.
- **Return Structure:**
  - `create_data_product` now returns `{'status': 'created', 'data': {...}}` on success, and a structured error dict on failure.
- **Error Handling:**
  - Product creation requires `name` and `description` (both non-empty).
  - Missing/empty fields yield `partial_error` status and a detailed error message.
- **Logging:**
  - All errors and validation failures are logged with method name, error type, and timestamp.
- **Imports:**
  - All imports are absolute (e.g., `from src.agents.new.A9_Data_Product_Agent import ...`).
- **Test Coverage:**
  - 100% coverage for core functionality, error handling, config validation, and async ops.
  - Tests assert on return structure, error handling, and logging patterns.
- **Registry Integration:**
  - Follows A9_Agent_Template registry and creation patterns.
- **Example Code:**
  ```python
  result = await agent.create_data_product({'name': 'foo', 'description': 'bar'})
  assert result['status'] == 'created'
  assert 'data' in result
  ```



## Hackathon Quick Start

### Development Environment Setup
- Clone the Agent9-Hackathon-Template repository
- Install required dependencies from requirements.txt
- Configure environment variables in .env file based on .env.template

### Key Files and Entry Points
- Main agent implementation: `src/agents/new/A9_Data_Product_Agent_Agent.py`
- Configuration model: `src/agents/new/agent_config_models.py`
- Agent card: `src/agents/new/cards/a9_data_product_agent_agent_card.py`

### Test Data Location
- Sample data available in `test-data/` directory
- Test harnesses in `test-harnesses/` directory

### Integration Points
- Integrates with Agent Registry for orchestration
- Follows A2A protocol for agent communication
- Uses shared logging utility for consistent error reporting
- Integrates with the Unified Registry Access Layer for data products and query mappings

### Registry Architecture Integration
- Must use the Registry Factory to initialize and access all registry providers
- Must configure and use appropriate registry providers for data products, contracts, and query templates
- Must use registry data for context-aware data product discovery and access
- Must NOT cache registry data locally; instead, always access the latest data through the Unified Registry Access Layer
- Must support backward compatibility with legacy code
- Must delegate registry operations to the appropriate providers

## Implementation Guidance

### Suggested Implementation Approach
1. Start with the agent's core functionality
2. Implement required protocol methods
3. Add registry integration
4. Implement error handling and logging
5. Add validation and testing

### Core Functionality to Focus On
- Protocol compliance (A2A)
- Registry integration
- Error handling and logging
- Proper model validation

### Testing Strategy
- Unit tests for core functionality
- Integration tests with mock registry
- End-to-end tests with test harnesses

### Common Pitfalls to Avoid
- Direct agent instantiation (use registry pattern)
- Missing error handling
- Incomplete logging
- Improper model validation

## Success Criteria

### Minimum Viable Implementation
- Agent implements all required protocol methods
- Agent properly integrates with registry
- Agent handles errors and logs appropriately
- Agent validates inputs and outputs

### Stretch Goals
- Enhanced error handling and recovery
- Performance optimizations
- Additional features from Future Enhancements section

### Evaluation Metrics
- Protocol compliance
- Registry integration
- Error handling
- Logging quality
- Input/output validation

---

## 8. Modification History

### 8.1 Version 1.0
- Date: 2025-04-14
- Changes:
  - Initial implementation of core functionality
  - Added structured error handling
  - Implemented configuration management
  - Added comprehensive logging
  - Added test coverage
- Affected Test Cases:
  - Registry Integration Tests
  - Error Handling Tests
  - Configuration Tests
  - Data Processing Tests

### 8.2 Planned Modifications

#### 8.2.1 Enhanced Error Handling
- Purpose: Improve error handling robustness
- Impact Analysis:
  - Input Changes: None
  - Output Changes: More detailed error responses
  - Data Flow Changes: None
- Test Impact:
  - Affected Test Cases: Error Handling Tests
  - New Test Cases Needed: None
  - Test Data Changes: None
- Implementation Plan:
  1. Add more specific error types
  2. Improve error recovery mechanisms
  3. Add retry logic
- Documentation Updates:
  - [ ] Update error handling documentation
  - [ ] Update error response structure
  - [ ] Update usage examples

## 9. Acceptance Criteria

### 9.0 Protocol Compliance (2025-06-24)
- All entrypoints use only protocol-compliant models as defined in code.
- Orchestrator-driven lifecycle is enforced; no agent-side registration or direct instantiation in documentation or code samples.
- All event logging is async/awaited and uses `A9_SharedLogger`.
- YAML contract context is always propagated and accessed via the context kwarg.
- All tests and usage examples are orchestrator-driven.

### 9.1 Functional
- Successful data product creation
- Accurate data processing
- Proper error handling
- Complete documentation
- **Compliance:** All data access, joining, filtering, and aggregation must be performed exclusively by the MCP (DuckDB backend) service. No agent-side pandas/file I/O is permitted in production.

### 9.2 Non-Functional
- Performance meets requirements
- Error handling implemented
- Documentation complete
- Testing coverage verified

## 10. Agent Requirements

### 10.1 Core Agent Interface
- Follow Agent9 agent registry interface requirements
- Implement required Unified Registry integration methods
- Use the Data Product Provider for registry operations
- Use standard error handling patterns
- Maintain consistent logging

### 10.2 Configuration Management
- Support default configuration values
- Validate configuration on initialization
- Maintain configuration state
- Handle agent-specific configuration

### 10.3 Error Handling
- Implement structured error handling
- Log errors appropriately
- Return consistent error responses
- Handle common error types

### 10.4 Logging
- Initialize agent-specific logger
- Log initialization and major operations
- Support different log levels
- Include timestamps in logs

### 10.5 Core Methods
- Implement _initialize for setup
- Implement _setup_logging for logging
- Implement _setup_error_handling for error management
- Implement create_from_registry class method
- Implement _validate_input for input validation
- Implement _format_error for consistent error messages

### 10.6 Error Types
- ConfigurationError: Invalid configuration
- RegistrationError: Failed to register with registry
- ProcessingError: Failed to process data
- ValidationError: Invalid input data
- TypeError: Invalid data type
- FormatError: Invalid ID format
- MissingFieldError: Required field is missing
- EmptyValueError: Required field is empty
- ConnectionError: Connection failures

## 11. Testing Requirements

### 11.1 Test Coverage
- Core functionality: 100%
- Error handling: 100%
- Performance: 80%
- Integration: 80%

### 11.2 Test Scenarios
1. Data product creation
2. Data processing
3. Error handling
4. Configuration management
5. Integration with registry

## 12. Maintenance

### 12.1 Regular Updates
- Performance optimization
- Bug fixes
- Feature enhancements
- Documentation updates

### 12.2 Support
- User documentation
- API documentation
- Troubleshooting guide
- Support channels
