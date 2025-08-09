# A9_Deep_Analysis_Agent PRD

<!-- 
CANONICAL PRD DOCUMENT
This is the official, canonical PRD document for this agent.
Last updated: 2025-07-17
-->


## Overview
**Purpose:** Deliver actionable, interpretable insights to support decision-making by providing transparent analysis, clear recommendations, and confidence scores. Emphasizes explainability, auditability, and compliance. Leverages the Unified Registry Access Layer for consistent business glossary, KPI, and data access.



## Hackathon Quick Start

### Development Environment Setup
- Clone the Agent9-Hackathon-Template repository
- Install required dependencies from requirements.txt
- Configure environment variables in .env file based on .env.template

### Key Files and Entry Points
- Main agent implementation: `src/agents/new/A9_Deep_Analysis_Agent_Agent.py`
- Configuration model: `src/agents/new/agent_config_models.py`
- Agent card: `src/agents/new/cards/a9_deep_analysis_agent_agent_card.py`

### Test Data Location
- Sample data available in `test-data/` directory
- Test harnesses in `test-harnesses/` directory

### Integration Points
- Integrates with Agent Registry for orchestration
- Integrates with the Unified Registry Access Layer for KPIs, business processes, and data products
- Uses Registry Factory for provider initialization and configuration
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
- Hardcoded business logic or KPI definitions (use registry data)
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

---

## LLM Integration Prioritization (2025-05-07)

A9_Deep_Analysis_Agent is a high-priority candidate for LLM integration, benefiting from LLM-powered insight extraction, summarization, and recommendations. See the "Agents Prioritized for LLM Integration" table in BACKLOG_REFOCUS.md for a complete rationale and comparison across agents.

---
**Purpose:** Deliver actionable, interpretable insights to support decision-making by providing transparent analysis, clear recommendations, and confidence scores. Emphasizes explainability, auditability, and compliance. Utilizes the Unified Registry Access Layer to access KPIs, business processes, and data products.
**Agent Type:** Clarity Team
**Version:** 1.0

## Functional Requirements

### Core Capabilities (MVP)

**Structured Root Cause Analysis (Kepner-Tregoe “Is/Is Not”)**
- The agent MUST implement a structured root cause analysis process based on the Kepner-Tregoe (KT) “is/is not” methodology.
- This includes:
    - Programmatically generating an “is/is not” table for each flagged issue, specifying:
        - What, Where, When, and Extent: segments/times where the problem IS and IS NOT observed.
        - Change-point detection: When the problem started or deviated from baseline.
        - Cross-segment comparison: Has the problem happened elsewhere, or is it unique?
    - Using LLMs to:
        - Interpret and summarize the KT table.
        - Generate root cause hypotheses, distinguishing features, and targeted diagnostic questions.
        - Recommend next steps based on KT findings.
- The KT-driven analysis must be included in both programmatic and LLM-assisted outputs, and reflected in the agent’s output models and audit logs.

**HITL (Human-in-the-Loop) Enablement:**
- HITL is NOT required for this agent. The configuration model includes a `hitl_enabled` field for protocol consistency, but it should remain False in all environments (DEV/QA/Prod).
- Rationale: Deep Analysis Agent workflows are highly technical and automated, not suitable for human-in-the-loop intervention. All review and approval is automated and orchestrator-controlled. See agent card for further details.

**Registration & Orchestrator Compliance:**
- Registration is orchestrator-controlled. There is no self-registration or legacy registration logic in the agent; all registration is managed by the orchestrator and AgentRegistry for full protocol compliance. See BACKLOG_REFOCUS.md for traceability.

6. General-Purpose LLM for Problem Framing & Clarification
    - Integrate a general-purpose LLM via the centralized A9_LLM_Service, with all requests routed through the Orchestrator Agent for logging and compliance
    - All LLM-powered analysis, summarization, and hypothesis generation must use A9_LLM_Service (no direct LLM API calls)
    - All LLM requests and responses must be validated using strict Pydantic models
    - All LLM outputs must include source attribution, operation metadata, and confidence scores
    - Outputs must be ready for downstream agent and UI consumption
    - Capture and surface natural language (NLP) clarification questions to iteratively refine the analysis

7. Opt-In LLM Enhancement (Pilot)
    - Backend supports LLM-powered analysis as an optional feature, always using the centralized A9_LLM_Service and Orchestrator Agent
    - Direct LLM API calls are strictly forbidden; protocol compliance is mandatory
    - UI surfaces an "Enhance with LLM" button for users to invoke LLM features on demand
    - Implement risk evaluation and user feedback mechanisms to monitor LLM performance and safety

1. Actionable Insights
   - Deliver interpretable analysis results with clear explanations and recommendations
   - Provide confidence scores for all results
   - Output concise text summaries for decision support
   - Leverage registry data for contextual awareness and business relevance

2. Transparency & Lineage
   - Ensure transparency for input data, transformation steps, and analysis lineage
   - Document all analysis steps

3. Audit Logging
   - Log all analysis steps, input parameters, and results
   - Provide exportable audit trails for compliance and review

4. Compliance
   - Implement compliance checks for sensitive data handling
   - Support audit trails for all compliance-relevant actions

5. Metrics & Performance
   - Define and report metrics to track business impact and adoption
   - Monitor and document performance and scalability

---

### Iterative, Orchestrated, Principal-Centric Deep Analysis (Enhancement)

**8. Iterative Problem Investigation & Refinement**
- The Deep Analysis Agent must plan and execute a sequence of data queries and analyses to progressively narrow down the root cause(s) of complex problems.
- The agent adapts its investigation based on intermediate findings, drilling down by segment, time, or other relevant dimensions.
- The agent quantifies the scope and severity of the problem, or determines if no material problem exists, and documents the rationale for its conclusion.

**9. LLM-Driven Investigation Planning with Registry Integration**
- The agent uses an LLM not only for summarization, but also to propose investigation steps, next queries, and hypotheses based on evolving context.
- Investigation planning leverages registry data (KPIs, business processes, data products) for context-aware analysis.
- LLM prompts include relevant registry information to enhance investigation quality.
- The LLM is prompted to act as a business analyst working on behalf of the principal, ensuring all outputs are principal-centric and actionable.

**10. Multi-Agent Orchestration via Orchestration Agent**
- All requests for additional analysis, risk assessment, or agent collaboration must be routed through the Orchestration Agent.
- The Deep Analysis Agent communicates its needs (e.g., risk quantification, stakeholder mapping, data enrichment) to the Orchestration Agent, which delegates requests to appropriate specialized agents and returns results.
- This ensures centralized coordination, logging, protocol enforcement, and auditability.

**11. Quantification & Reporting**
- The agent provides quantitative measures of problem extent (e.g., % of affected revenue, number of impacted customers).
- If no material problem is found, the agent clearly states this and explains the basis for that conclusion.
- All investigation steps, queries, agent engagements, and rationale are logged and can be surfaced for review.

**12. Transparent Investigation Plan**
- The agent maintains a transparent log of its investigation plan, steps taken, queries run, agents engaged, and rationale for each step.
- This plan can be presented to users or auditors on request.

---

### Input Requirements (MVP)
- Pydantic input model with relevant fields for context and analysis parameters
- Field: `data_product_schema` (optional; used for escalation logic and protocol compliance)
- Minimal set of analysis parameters (e.g., thresholds, weights, scope)
- All input models must be strictly validated and protocol-compliant (Agent9 standards)
- See test suite for escalation scenarios using ambiguous `data_product_schema`.

### Output Specifications (MVP)
- Pydantic output model with:
  - Analysis results (interpretable, actionable)
  - Confidence scores
  - Status (success/error)
  - Text summary and recommendation
  - Timestamp
  - Audit log (full trace of analysis, escalation, and LLM involvement)
  - All escalation and LLM output merging logic must be protocol-compliant and auditable
  - Output models and merging logic tested for compliance as of 2025-06-09

## Technical Requirements
- Modular, maintainable architecture
- Registry integration and async operations
- Secure configuration and error handling
- Full compliance with A2A and MCP protocols (see Protocol Compliance)
   - Role-based access
   - Secure data sharing
   - Audit trail for changes
   - Analysis approval workflows

## Monitoring and Maintenance
1. Regular model updates
2. Continuous accuracy monitoring
3. Periodic validation
4. Regular optimization

## Success Metrics
1. Analysis accuracy
2. Prediction confidence
3. Pattern recognition
4. Decision support effectiveness
5. Analysis efficiency

## Input/Output

### Input
```python
{
    "data": List[Dict[str, Any]],  # Pre-fetched query results from A9_Database_Query_Agent
    "context": {
        "analysis_type": "type_of_analysis",
        "focus_areas": ["area1", "area2"],
        "time_window": {
            "start": "2025-04-12",
            "end": "2025-04-12"
        }
    }
}
```

### Output
```python
{
    "status": "success" | "error",
    "analysis": {
        "metrics": Dict[str, float],
        "trends": List[Dict],
        "patterns": List[str],
        "correlations": Dict[str, float],
        "anomalies": List[Dict],
        "data_quality": Dict,
        "business_context": Dict
    },
    "insights": List[Dict],  # With detailed action plans
    "recommendations": List[Dict],  # With implementation plans
    "metadata": {
        "analysis_time": "ISO timestamp",
        "confidence_scores": {
            "overall": float,
            "metrics": float,
            "trends": float
        }
    },
    "timestamp": "ISO timestamp"
}
```

## Modification History

### 2025-06-09
- Test suite fully updated and passing (escalation logic, LLM output merging, audit logging, protocol compliance)
- Input model refactored to use `data_product_schema` (removes legacy `schema`/`data` ambiguity)
- Output model and escalation logic updated for strict Agent9 protocol compliance and auditability
- RuntimeWarning on unawaited coroutine in test mocks mitigated (see test suite for details)
- Compliance with Agent9 Agent Design Standards and audit logging requirements confirmed
- All changes traceable to test cases and standards (see BACKLOG_REFOCUS.md for traceability)

### Current Version
- Version: 1.0

## 6. Implementation Details

### 6.1 Data Processing and Formatting
- Implements timestamp formatting utilities for consistent date/time representation
- Provides standardized DataFrame handling for data analysis operations
- Includes data quality assessment and validation mechanisms

### 6.2 Security and Compliance
- Implements sensitive data detection logic for compliance with data governance policies
- Provides compliance reporting structure for audit requirements
- Ensures proper data handling and masking for sensitive information

### 6.3 Analysis and Insights Generation
- Implements structured insights and recommendations generation approach
- Provides confidence scoring methodology for analysis results
- Includes data quality assessment metrics for reliability evaluation
- Supports anomaly detection and pattern recognition algorithms

### 6.4 Performance and Optimization
- Implements caching mechanisms for repeated analysis operations
- Provides optimized DataFrame operations for large dataset handling
- Includes performance monitoring and logging for analysis operations
- Date: [Release Date]
- Changes: Initial implementation
- Affected Test Cases: All

### 2025-05-12
- Documented HITL rationale: HITL is not required for Deep Analysis Agent; config model includes `hitl_enabled` for protocol consistency only. Card and PRD updated to reflect this compliance and rationale.


### Planned Modifications

#### [Modification Name]
- Purpose: [Brief description]
- Impact Analysis:
  - Input Changes: [List changes]
  - Output Changes: [List changes]
  - Data Flow Changes: [Description]
- Test Impact:
  - Affected Test Cases: [List]
  - New Test Cases Needed: [List]
  - Test Data Changes: [Description]
- Implementation Plan:
  1. [Task 1]
  2. [Task 2]
  3. [Task 3]
- Documentation Updates:
  - [ ] Update input parameters
  - [ ] Update output structure
  - [ ] Update usage examples
  - [ ] Update error handling

## Acceptance Criteria
1. The agent successfully conducts advanced analysis to uncover insights and support decision-making.
2. The agent provides accurate and reliable results.
3. The agent integrates with data systems and output systems as specified.
4. The agent meets performance requirements.
5. The agent is secure and follows access control requirements.
6. All input/output models, escalation logic, and audit logging are protocol-compliant and validated by automated test suite as of 2025-06-09.
7. Test suite must remain fully passing after any future changes (see Modification History for last validated date).


---

## LLM Integration Architecture

All LLM operations for the Deep Analysis Agent will be centralized through a dedicated A9_LLM_Service. This service abstracts LLM provider details, prompt formatting, error handling, and logging. All LLM requests are routed via the Orchestrator Agent to ensure protocol compliance, centralized logging, and future extensibility (multi-model, ensemble, escalation, etc.).

- Agents must never call LLM APIs directly; all LLM usage is through the orchestrator and A9_LLM_Service.
- All LLM input and output payloads must use strict Pydantic models for validation and auditability.
- This architecture supports future features such as ensemble querying and model/provider selection.
- **Backlog:** Enable dynamic LLM provider switching via configuration/environment variable (see BACKLOG_REFOCUS.md, post-MVP). This will allow pluggable providers (Cascade, OpenAI, Azure) with full backward compatibility and test coverage.

---

## Future Consideration: Ensemble LLM Hallucination Mitigation

**Objective:**
Reduce the risk of LLM hallucinations in critical business outputs by leveraging an ensemble of multiple, independent LLM instances.

**Description:**
- For principal-facing or high-stakes queries, the same prompt will be sent to three or more inexpensive LLM instances.
- Responses will be aggregated using consensus or semantic similarity methods.
- If the ensemble agrees, the consensus response is returned. If not, escalate to a stronger model or human review.
- All ensemble responses and aggregation logic will be logged for transparency and auditability.
- This feature will be considered and potentially implemented after initial single-LLM testing and evaluation.

**Benefits:**
- Reduces hallucination risk
- Improves trust and transparency
- Enables cost-effective, robust LLM-based insights

**Status:**
- Not in MVP. To be revisited after single-LLM solution is tested and evaluated.
