# A9 Principal Context Agent PRD

<!-- 
CANONICAL PRD DOCUMENT
This is the official, canonical PRD document for this agent.
Last updated: 2025-07-17
-->


## Overview

> **COMPLIANCE NOTE:**
> - This agent must ONLY be invoked via the AgentRegistry and orchestrator pattern.
> - Do NOT instantiate directly; always use the async factory method `create_from_registry`.
> - **Usage Example:**
> ```python
> principal_agent = await AgentRegistry.get_agent("A9_Principal_Context_Agent")
> result = await principal_agent.set_principal_context(...)
> ```

The A9 Principal Context Agent manages principal context and relationships in business operations, providing essential context-aware functionality for other agents. It leverages the Unified Registry Access Layer to store, retrieve, and manage principal profiles as well as their relationships to business processes and KPIs.

## Purpose
- Manage principal context and relationships
- Provide context-aware recommendations
- Handle access control and permissions
- Maintain context history
- Integrate with HCM systems
- Register and retrieve principal profiles using the Unified Registry Access Layer
- Map principals to business processes and KPIs using registry relationships

## Key Features

- **HITL protocol fields** (`human_action_required`, `human_action_type`, `human_action_context`) are included in all outputs where human approval may be required. HITL enforcement is configurable and defaults to OFF unless explicitly enabled.

### 1. Principal Context Management
- Set and maintain principal context
- Fetch principal profiles from HCM systems
- Register and update principal profiles in the Principal Profile Provider
- Track context history
- Clear context when needed
- Provide responsibilities and filter criteria in business terms (English descriptions) for downstream translation
- Use registry relationships to map principals to business processes, KPIs, and data products
- Automatically default dimensional filters based on principal profile context (e.g., job description, region, business unit) for relevant data products. For example, if the principal is a Sales Manager for Northern Region, automatically add {"Region": "Northern"} to filters for Sales data queries.
- The agent must use an LLM or NLP pipeline to extract potential dimensional filters (e.g., region, business unit, product line) from the principal's job or role description text. These extracted filters should be merged with explicit profile filters and included in the output filters dictionary for downstream translation and query assembly. Example: For a role description "Sales manager for Northern Region, responsible for consumer electronics", the agent should extract and default filters such as {"Region": "Northern", "Product": "Consumer Electronics"}.
- Output structure must include:
  - `responsibilities`: List of business responsibilities (e.g., ["Revenue by Business Unit"])
  - `filters`: Dict of filter criteria (e.g., {"Region": "North America", "Product": "Consumer Electronics"})
- Example output:
```json
{
  "profile": {
    "responsibilities": ["Revenue by Business Unit", "Cost by Product Line"],
    "filters": {"Region": "North America", "Product": "Consumer Electronics"}
  }
}
```

### 2. Access Control
- Role-based access control
- Permission-based access
- Data governance integration
- Context-aware access decisions

### 3. Context Recommendations
- Generate role-based recommendations
- Provide data governance recommendations
- Prioritize recommendations
- Context-aware suggestions

#### LLM Explainability Compliance (2025-06-24)
- All context-aware recommendation descriptions are routed through the A9_LLM_Service_Agent for explainability and business-user-friendly output.
- LLM calls are protocol-compliant, orchestrator-driven, and fully async with structured event logging and error handling.
- See agent card for implementation and compliance details.

### 4. Integration
- HCM system integration
- Registry integration (A9_Agent_Template pattern, async)
- Output must be compatible with Data Governance Agent for business-to-technical translation
- Error handling
- Logging

## Technical Requirements

- Logging is standardized using `A9_SharedLogger`.
- All agent input/output is strictly Pydantic model-based and compliant with A2A/MCP protocols.

### 1. Agent Implementation
- Follow A9_Agent_Template patterns for:
  - Configuration management
  - Registry integration
  - Error handling
  - Logging
  - Async operations
- Use absolute imports for all dependencies
- Implement create_from_registry method
- Use standard error handling patterns

### 2. Dependencies
- Agent Registry
- Unified Registry Access Layer
- Registry Factory and Providers
- HCM System Connector
- Data Governance System
- Logging Framework

### 3. Error Handling
- Use standard error classes from A9_Agent_Template
- Error types:
  - ConfigurationError: Invalid configuration
  - RegistrationError: Failed to register with registry
  - ProcessingError: Failed to process data

### 4. KPI Registry Integration
- Integrates with KPI registry for entity canonicalization
- Uses KPI_REGISTRY for mapping extracted entities to standardized dimensions
- Supports entity extraction from job descriptions with standardized mapping

### 5. Implementation Details
- Uses Pydantic v2 validation with `__private_attributes__` checks for model integrity
- Implements debug logging in initialization for configuration verification
- Provides `extract_entities_from_job_description` method for standardized entity extraction
- Supports fallback handling when KPI registry mapping fails
  - ValidationError: Invalid input data
  - ConnectionError: Connection failures
- Log all context retrieval and output generation attempts, including failures

## API Specification

### Core Methods
```python
async def set_principal_context(self, principal_id: str, context_data: Dict[str, Any] = None) -> Dict[str, Any]
async def fetch_principal_profile(self, principal_id: str) -> Dict[str, Any]
async def check_access(self, item: Dict[str, Any]) -> bool
async def get_context_recommendations(self) -> List[Dict[str, Any]]
async def get_context_history(self) -> List[Dict[str, Any]]
async def clear_context(self) -> None
```

### Error Types
- ConfigurationError: Invalid configuration
- RegistrationError: Failed to register with registry
- ProcessingError: Failed to process data
- ValidationError: Invalid input data
- ConnectionError: Connection failures

## Testing Requirements

- All tests use Pydantic model instances (no dicts/mocks).
- Integration tests are orchestrator-driven and production-like.

### Unit Tests
- Registry integration
- Context management
- Access control
- Recommendations
- History management
- Error handling
- Output structure for responsibilities and filters (business terms)

### Integration Tests
- HCM system integration
- Registry integration
- Error scenarios
- Configuration validation
- Integration with Data Governance Agent (output must be translatable)

## Security Considerations
- Role-based access control
- Permission validation
- Data governance integration
- Secure context storage
- Error handling security

## Performance Considerations
- Efficient context retrieval
- Caching strategies
- Async operations
- Resource management

## Monitoring & Logging
- Operation logging
- Error tracking
- Performance metrics
- Context history

## Decision Style and Persona Mapping

### 5. Decision Style to Analysis Lens Mapping

The Principal Context Agent is responsible for providing `decision_style` from the principal's `persona_profile` to downstream agents. This enables role-appropriate presentation of analysis.

#### Decision Style Definitions

| Decision Style | Analysis Lens | Primary Consulting Framework | Focus |
|----------------|---------------|------------------------------|-------|
| `analytical` | McKinsey-style | MECE, Issue Trees, Hypothesis-driven | Root cause decomposition, statistical rigor, 80/20 prioritization |
| `visionary` | BCG-style | Growth-Share Matrix, Portfolio View | Strategic implications, market positioning, value creation opportunities |
| `pragmatic` | Bain-style | Results Delivery, Operational Excellence | Quick wins, implementation roadmaps, owners and timelines |
| `decisive` | McKinsey-style | Structured Decision-Making | Clear options, trade-offs, decision criteria |

#### Output Requirements

The Principal Context output MUST include:
```json
{
  "profile": {
    "principal_id": "cfo_001",
    "role": "CFO",
    "decision_style": "analytical",
    "risk_tolerance": "low",
    "communication_style": "concise",
    "responsibilities": ["maximize EBIT", "manage revenue"],
    "filters": {"profit_center_hierarchyid": ["Total"]}
  }
}
```

#### Downstream Agent Usage

- **Deep Analysis Agent**: Uses `decision_style` to frame KT IS/IS-NOT analysis
- **Solution Finder Agent**: Uses `decision_style` to select consulting personas for LLM council
- **Situation Awareness Agent**: Uses `communication_style` to format situation cards

### 6. Guardrails: Personalization vs Attribution

**CRITICAL**: Agent9 adapts presentation FOR the principal, it does NOT speak FOR the principal.

#### Prohibited Patterns
- ❌ "The CFO believes..."
- ❌ "Based on Lars Mikkelsen's perspective..."
- ❌ "The CFO would recommend..."

#### Required Patterns
- ✅ "This analysis is tailored for your analytical decision style..."
- ✅ "Presented with MECE decomposition per your profile preferences..."
- ✅ "Highlighting root cause factors relevant to your CFO responsibilities..."

#### Principal Control
- Principals can view and modify their `decision_style` at any time
- Principals can override the default presentation style per session
- All profile-influenced outputs must be transparent about adaptation

## Future Considerations
- Enhanced recommendation system
- Additional access control features
- Expanded HCM system integration
- Advanced context analysis
- Performance optimizations
- Cross-principal alignment detection (when multiple principals view same situation)


## Hackathon Quick Start

### Development Environment Setup
- Clone the Agent9-Hackathon-Template repository
- Install required dependencies from requirements.txt
- Configure environment variables in .env file based on .env.example

### Key Files and Entry Points
- Main agent implementation: `src/agents/new/A9_Principal_Context_Agent_Agent.py`
- Configuration model: `src/agents/new/agent_config_models.py`
- Agent card: `src/agents/new/cards/a9_principal_context_agent_agent_card.py`

### Test Data Location
- Sample data available in `test-data/` directory
- Test harnesses in `test-harnesses/` directory

### Integration Points
- Integrates with Agent Registry for orchestration
- Integrates with the Unified Registry Access Layer for principal profiles
- Uses the Principal Profile Provider for registry operations
- Follows A2A protocol for agent communication
- Uses shared logging utility for consistent error reporting

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
- Direct enum usage (use registry providers instead)
- Hardcoded principal profile logic (use registry data)
- Initializing registry providers directly (use Registry Factory)

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

