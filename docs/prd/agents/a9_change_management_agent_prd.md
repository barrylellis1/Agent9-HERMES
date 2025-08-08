# A9 Change Management Agent PRD

<!-- 
CANONICAL PRD DOCUMENT
This is the official, canonical PRD document for this agent.
Last updated: 2025-07-17
-->


## Status (2025-06-04)
**Phase 1 (MVP) Complete**
- Protocol-compliant (A2A, Pydantic V2, registry/orchestrator integration)
- All unit and integration tests pass
- No deprecated patterns (config, logging, error handling, etc.)
- Agent is MVP-ready for all core change management scenarios
- Comprehensive implementation of change management models and analysis methods



## Hackathon Quick Start

### Development Environment Setup
- Clone the Agent9-Hackathon-Template repository
- Install required dependencies from requirements.txt
- Configure environment variables in .env file based on .env.template

### Key Files and Entry Points
- Main agent implementation: `src/agents/new/A9_Change_Management_Agent_Agent.py`
- Configuration model: `src/agents/new/agent_config_models.py`
- Agent card: `src/agents/new/cards/a9_change_management_agent_agent_card.py`

### Test Data Location
- Sample data available in `test-data/` directory
- Test harnesses in `test-harnesses/` directory

### Integration Points
- Integrates with Agent Registry for orchestration
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

## Purpose (Universal Change Enablement)
The A9 Change Management Agent provides comprehensive change management capabilities for any type of organizational change—including process, product, service, policy, and organizational changes (not just data)—ensuring smooth transitions and effective stakeholder engagement for all scenarios.

## Universal Change Enablement Vision (2025-04-30)
- The agent must support intake, planning, execution, and monitoring for any change type: process, product, service, policy, or organization.
- All features, models, and integration points must be agnostic to change type and support flexible context and stakeholder mapping.
- Event-driven handoff: The agent listens for `StakeholderEngagementCompleted` events (with sign-off, audit log, and change context) from the Stakeholder Engagement Agent for any change scenario.
- Must maintain strict A2A protocol compliance (Pydantic models for all entrypoints/outputs) and auditability for all change types.
- Feedback, escalation, and resistance management must be available for any change type.

## Compliance & Integration Update (2025-05-12)

- This agent is now fully compliant with Agent9 async, registry, error handling, and centralized logging standards.
- Follows the A9_Agent_Template pattern for config validation, registration, and logging (pattern, not inheritance).
- Registration is orchestrator-controlled (no self-registration or bootstrapping).
- All configuration is validated via Pydantic models.
- **HITL (Human-in-the-Loop) enablement is fully implemented and enforced for all key actions:**
  - Output protocol fields (`human_action_required`, `human_action_type`, etc.) are always present and validated.
  - HITL logic is enforced in code and verified by tests.
- **All integration and testing for this agent is orchestrator-driven and production-like:**
  - Agent inputs and outputs are always real Pydantic model instances, never mocked or stubbed.
  - Integration tests simulate true production workflows, with the orchestrator coordinating all agent calls and data flows.
  - Static workflow tests and direct agent invocation in tests have been deprecated.
- Test coverage is maintained via orchestrator-based persona and workflow scenarios, ensuring compliance with real-world business logic and end-to-end flows.
- Logging uses `A9_SharedLogger` and is propagated to the Orchestrator Agent.
- Error handling is standardized and protocol-compliant.
- Event-driven handoff: The agent listens for `StakeholderEngagementCompleted` events (with sign-off, audit log, and change context) from the Stakeholder Engagement Agent for any change scenario.
- Must maintain strict A2A protocol compliance (Pydantic models for all entrypoints/outputs) and auditability for all change types.
- Feedback, escalation, and resistance management must be available for any change type.

## Core Requirements

### Agent Template Compliance
- Implements A9_Agent_Template patterns
- Uses absolute imports
- Follows standardized error handling
- Implements create_from_registry method
- Uses consistent logging patterns

### Key Features
1. Change Management
   - Change impact analysis
   - Change readiness assessment
   - Change communication
   - Change execution
   - Change monitoring

2. Change Components
   - Impact Assessment
     - Business impact
     - Technical impact
     - Organizational impact
     - Cultural impact
   - Readiness Assessment
     - Stakeholder readiness
     - Resource readiness
     - System readiness
     - Process readiness
   - Communication Strategy
     - Stakeholder mapping
     - Communication plan
     - Change messaging
     - Feedback mechanisms
   - Execution Planning
     - Change phases
     - Resource allocation
     - Timeline management
     - Training requirements
   - Monitoring & Control
     - Key metrics
     - Progress tracking
     - Issue management
     - Risk management

3. Integration Points
   - Integrates with registry
   - Communicates with other agents (including event-driven handoff from Stakeholder Engagement Agent for any change type)
   - Handles configuration updates
   - Supports data validation
   - Interfaces with change management tools
   - Listens for and processes `StakeholderEngagementCompleted` events for all change scenarios
   - Emits audit and completion events for downstream reporting and analytics
   - Supports escalation and feedback integration for any change type

### Error Handling
- Uses standardized error classes
- Implements proper error logging
- Provides clear error messages
- Handles validation errors
- Handles change management failures
- Handles communication failures

## Implementation Guidelines

### Recent Technical Improvements (2025-06-04)
- All Pydantic models use `ConfigDict` (no deprecated `class Config`)
- Registry and orchestrator integration is robust and protocol-driven
- Defensive coding and error handling use standardized Agent9 patterns
- Centralized logging via `A9_SharedLogger`
- Unit and integration tests are protocol-compliant and pass without warnings or errors
- Robust timestamp handling with ISO format standardization
- Defensive type checking and data validation for all input models
- Structured error handling with specialized error classes
- Comprehensive model validation with fallback mechanisms

### Code Structure
- Single focused class
- Direct change management methods
- Clear data flow
- Basic but reliable performance
- Modular helper methods for component creation
- Defensive data handling with type checking
- Structured model generation for all outputs
- Timestamp standardization using ISO format
- Comprehensive input validation with fallback mechanisms

### Change Components
```python
class ChangeImpact:
    """Represents the impact of a change."""
    
    def __init__(self, category: str, level: float, description: str):
        """
        Initialize a change impact.
        
        Args:
            category: Impact category (business, technical, etc.)
            level: Impact level (0-1)
            description: Description of the impact
        """
        self.category = category
        self.level = level
        self.description = description
        self.mitigation = None
```

### Data Model
```python
class ChangeManagementPlan:
    """Represents a complete change management plan."""
    
    def __init__(self):
        self.change_impacts = []
        self.readiness_assessment = {
            'stakeholders': 0.0,
            'resources': 0.0,
            'systems': 0.0,
            'processes': 0.0
        }
        self.communication_plan = {
            'stakeholders': [],
            'messages': [],
            'timeline': [],
            'channels': []
        }
        self.execution_plan = {
            'phases': [],
            'resources': [],
            'timeline': None,
            'training': []
        }
        self.monitoring = {
            'metrics': [],
            'alerts': [],
            'reports': []
        }
        self.risk_management = {
            'risks': [],
            'mitigations': [],
            'contingencies': []
        }
        self.recommendations = []  # List of prioritized, actionable recommendations
        self.critical_alerts = []  # List of critical alerts for high-risk changes/adoption issues
        self.confidence_score = 0.0
        self.risk_level = 0.0
        self.timestamp = None
        self.value_realization = {
            'baseline': {},
            'projection': {},
            'target': {},
            'actual': {},
            'comparison': {}
        }
```

### Value Realization
- The agent is responsible for orchestrating value realization measurement and reporting. This includes:
  - **Explicit Change-to-KPI Linkage:** Each change must specify one or more KPIs it intends to impact, by name, in the change request input. (Not inferred by persona, story arc, or business process alone.)
  - The input model must include a `kpis` field: a list of KPI names (strings) referencing KPIs in the KPI registry.
  - The agent must use these declared KPIs as the sole basis for value realization tracking, reporting, and dashboard outputs for that change.
  - Capturing baseline, projected (counterfactual), and target KPI values at the start of the change.
  - Tracking actual KPI values over time (monthly, quarterly, on-demand).
  - Calculating value realized and value left (gap) for each KPI.
  - Providing structured explanations for value gaps (reason category, summary, details, source agent, confidence, recommendations).
  - Reporting value realization and value sharing in a dashboard-ready format.
  - Supporting demo outputs for UI and investor review.
  - Ensuring all value realization reporting is based on explicit, declared KPIs for each change (see above).
  - **Data Source Traceability:** The Data Product Agent and Data Governance Agent must be consulted or delegated to in order to identify and validate the authoritative data source for each KPI value (baseline, projection, target, actual). The Change Management Agent must integrate with these agents to ensure all KPI values used in value realization reporting are traceable, high quality, and auditable.

**Rationale:**
- This approach ensures traceability and business alignment for every change initiative.
- KPI selection is transparent and auditable, supporting clear value realization stories for leadership and stakeholders.
- Dashboards and reports will always reflect the KPIs that were actually targeted by the change, not just generic metrics.
- Delegating data source resolution to Data Product and Data Governance Agents ensures data quality, trust, and compliance.

### Agent9 Value Sharing (Optional Feature)

- For a limited period after implementation (e.g., 1 year), a configurable percentage of value realized may be shared with Agent9 as part of the value realization agreement.
- This value sharing period and percentage are tracked and reported alongside value realization metrics.
- The Change Management Agent should:
  - Allow configuration of value sharing terms (percentage, duration, start/end date)
  - Calculate Agent9's share based on realized value within the defined window
  - Report both gross value realized and Agent9's share in outputs and dashboards

### Value Realization Dashboard (Wireframe Vision)

**Purpose:**
- Provide a single view for leadership and stakeholders to track value delivered by changes, with context and explanations.
- Transparently display Agent9 value sharing terms, period, and amounts (if applicable).

**Dashboard Top Section:**
- **Total Value Realized Since Implementation:**
  - Displays the cumulative value delivered from the start of the value sharing period to present.
- **Agent9 Value Sharing (Monthly):**
  - Shows the current month's value realized, Agent9's 10% share, and the running total for the value sharing period (default: 12 months).
- **Estimated Change Not Realized (Value Left on the Table):**
  - Calculates the difference between target value and actual value realized.
  - For each KPI, tracks and displays the estimated value not realized.
  - Provides explanations for the gap (e.g., lack of adoption, unforeseen market conditions, other reasons).
  - Explanations are sourced from Situation Awareness and Stakeholder Analysis agents and are shared in the dashboard/report.
  - **Explanation Structure:**
    - `reason_category`: Enum (e.g., `lack_of_adoption`, `market_conditions`, `technical_issue`, `scope_change`, `other`)
    - `summary`: Short summary (1-2 sentences)
    - `details`: Longer explanation with supporting evidence
    - `source_agent`: Which agent provided the explanation
    - `confidence_score`: (Optional) 0.0–1.0
    - `recommendations`: (Optional) List of actionable steps
  - **Reporting Cadence:**
    - Default: Monthly (aligned with value sharing and KPI reporting)
    - Options: Quarterly and on-demand for leadership reviews
    - Audit trail: All explanations and updates are timestamped for traceability

**Core Features:**
- **KPI Comparison Table/Chart:**
  - Actual vs. Baseline
  - Actual vs. Projection (No Change)
  - Actual vs. Target
- **Trend Visualization:**
  - Line/bar charts showing all four series over time
- **Context Panel:**
  - Key events, risks, or opportunities surfaced by Situation Awareness Agent
  - Stakeholder sentiment/adoption (from Stakeholder Analysis Agent)
- **Recommendations/Alerts:**
  - Actionable recommendations if value is not realized
  - Critical alerts for at-risk KPIs
- **Audit Trail:**
  - Log of key value realization events and explanations

**Data Sources:**
- Change Management Agent (core logic, aggregation)
- Implementation Tracker Agent (completion triggers, process metrics)
- Situation Awareness Agent (context, risk, anomaly explanation)
- Stakeholder Analysis Agent (adoption, sentiment)

**Wireframe (Textual):**

| KPI         | Baseline | Projection | Target | Actual | Value Realized | Value Left | Status   | Explanation (Summary)           | Source Agent         | Recommendations         |
|-------------|----------|------------|--------|--------|----------------|------------|----------|-------------------------------|----------------------|------------------------|
| Revenue     | $10M     | $9.5M      | $11M   | $10.3M | +$0.3M         | $0.7M      | ⚠️      | User adoption lagged in Q2      | Stakeholder Analysis | Increase training, ... |
| Cycle Time  | 30 days  | 32 days    | 20 days| 23 days| -7 days        | 3 days     | ⚠️      | Market disruption in Q2         | Situation Awareness  | Monitor supply chain   |

- [Trend Chart Here]
- [Context Panel: "Market disruption in Q2", "Stakeholder resistance flagged"]
- [Recommendations/Alerts: "Increase training for adoption", "Monitor competitor activity"]
- [Audit Trail: "Value realization review completed 2025-04-30"]

**On click/expand:**
- Show `details`, `confidence_score`, and full recommendation list for each explanation.


### Output Specifications
- Change plans, impact/risk reports, and progress dashboards
- Audit trails and completion events for downstream agents
- **Prioritized, actionable recommendations:** All outputs must include recommendations with explicit priority (e.g., high, medium, critical) and clear, human-readable, demo-friendly language for change owners and leadership.
- **Critical alerts:** Outputs must flag high-risk changes, blockers, or adoption issues, surfacing actionable alerts for immediate mitigation and follow-up.
- **Demo/UI readiness:** All outputs must be structured for easy display in dashboards and reports, with priorities and critical alerts visually surfaced for users and demos.
- **Structured output models:** All outputs are provided as structured Pydantic models:
  - `ChangePlan`: Contains description, scope, timeline, and resources
  - `ImplementationStrategy`: Contains phases, key milestones, and basic requirements
  - `StakeholderPlan`: Contains key stakeholders, communication plan, and engagement strategy
  - `RiskAssessment`: Contains key risks, mitigation strategies, and risk metrics
  - `ChangeManagementOutput`: Comprehensive output model containing all analysis components
- **Defensive data handling:** All outputs include defensive type checking and fallback mechanisms for handling incomplete or malformed input data

### Implementation Details

#### Helper Methods
The Change Management Agent implements several helper methods to support its core functionality:

- `_get_current_timestamp()`: Standardizes timestamp generation in ISO format
- `_determine_scope()`: Analyzes requirements to determine change scope
- `_create_basic_timeline()`: Generates a standardized timeline structure
- `_estimate_basic_resources()`: Calculates resource requirements based on stakeholders and requirements
- `_identify_basic_milestones()`: Creates milestone list for implementation planning
- `_create_basic_communication_plan()`: Generates communication strategy
- `_determine_basic_engagement_strategy()`: Establishes stakeholder engagement approach
- `_identify_basic_risks()`: Identifies potential risks based on input data
- `_create_basic_mitigation_strategies()`: Generates risk mitigation approaches
- `_generate_basic_risk_metrics()`: Calculates risk metrics with confidence scores
- `_get_future_date()`: Calculates future dates in ISO format for timeline planning

#### Defensive Data Handling
The agent implements robust defensive data handling:
- Type checking for all input fields
- Fallback mechanisms for missing or malformed data
- Structured error handling with specialized error classes
- Standardized timestamp handling

### Error Classes
```python
class ChangeManagementError(Exception):
    """Base error for change management failures"""
    pass

class ImpactAnalysisError(ChangeManagementError):
    """Raised when impact analysis fails"""
    pass

class CommunicationError(ChangeManagementError):
    """Raised when communication fails"""
    pass

class ExecutionError(ChangeManagementError):
    """Raised when execution fails"""
    pass
```

### Logging
- Uses structured logging
- Logs change management process
- Tracks error conditions
- Logs impact assessments
- Logs communication activities
- Logs execution progress

## Testing
- All integration and scenario tests for A9_Change_Management_Agent are orchestrator-driven and use real agent inputs/outputs, never mocks or stubs.
- After agent migration is complete, all integration tests will be refactored to:
  - Use the orchestrator as the only entrypoint
  - Validate end-to-end workflows for C-level personas and business scenarios
  - Assert on real outputs, with no direct agent calls in test bodies
- This ensures tests reflect production-like behavior and validate the full agent ecosystem.

## Success Metrics
- Change adoption rate
- Stakeholder satisfaction
- Timeliness and effectiveness of change implementation
- Reduction of resistance/issues
- Alignment with organizational goals
- **Actionable, prioritized outputs:** Change management outputs are actionable, prioritized, and clearly flag high-risk changes or blockers for demo and production use.
- **Demo/investor feedback:** Demo and investor feedback confirms recommendations and alerts are understandable, actionable, and visually surfaced in the UI.

## Notes
- Focus on change management only
- Clear error handling
- Simple implementation
- Standard logging
- Comprehensive change components
- Stakeholder-centric approach
- Risk-aware planning
- Monitoring integration
