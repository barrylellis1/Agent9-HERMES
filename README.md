# Agent9 LLM MVP Template

## Overview

This repository contains the template and reference materials for the Agent9 LLM MVP Development. The MVP development is designed to evaluate which LLM can most effectively implement Agent9's core workflows with the fewest errors and best performance.

## Project Structure

```
Agent9-MVP-Template/
├── docs/
│   ├── architecture/         # System architecture documentation
│   ├── clarification_sessions/ # LLM requirements clarification session outcomes
│   ├── prd/                  # Product Requirement Documents for agents
│   ├── wireframes/           # UI wireframes and mockups
│   ├── Agent9_Agent_Design_Standards.md  # Agent design standards
│   ├── Agent9_LLM_Requirements_Session_Template.md  # Template for LLM sessions
│   ├── Agent9_LLM_Session_Outcome_Template.md  # Template for session outcomes
│   └── Agent9_MVP_LLM_Development_Plan.md  # Overall MVP development plan
├── src/
│   ├── contracts/            # Data contracts and schemas
│   ├── models/               # Pydantic data models
│   └── registry-references/  # Reference implementations for registries
│       ├── agent_registry/
│       ├── data_product_registry/
│       ├── kpi_registry/
│       └── principal_registry/
├── test-harnesses/           # Test harnesses for validating implementations
├── .env.template             # Environment variable template (copy to .env)
└── .windsurfrules            # Project coding standards and rules
```

## MVP Development Phases

### Phase 1: Requirements Clarification

During this phase, each participating LLM will engage in a 30-minute requirements clarification session to:
- Understand functional requirements
- Identify gaps and overlaps
- Provide recommendations
- Clarify integration points
- Discuss testing approach

The outcomes of these sessions will be documented in the `docs/clarification_sessions/` directory and consolidated into a unified requirements document.

### Phase 2: LLM MVP Development

3-5 top LLMs will each generate a complete solution based on the unified requirements. The solutions will be evaluated based on:
- Relevance to requirements
- Accuracy of implementation
- Bugginess (fewer bugs = better)
- Speed of development
- Cost (LLM credit consumption)

## Getting Started

1. **Environment Setup**:
   - Copy `.env.template` to `.env` and fill in your API keys and credentials
   - Do NOT commit your `.env` file to version control

2. **Requirements Clarification**:
   - Use `docs/Agent9_LLM_Requirements_Session_Template.md` as the template for LLM sessions
   - Document session outcomes in `docs/clarification_sessions/`

3. **Implementation**:
   - Follow the Agent9 Agent Design Standards in `docs/Agent9_Agent_Design_Standards.md`
   - Implement the core workflows based on the unified requirements
   - Use the test harnesses to validate your implementation

## Core Workflows

The MVP development focuses on implementing three core workflows:

1. **Automated Situation Awareness** - Identifies business situations requiring attention
2. **Deep Analysis** - Performs detailed analysis of identified situations
3. **Solution Finding** - Generates and evaluates potential solutions

## Security Guidelines

- Never commit API keys or credentials to version control
- Use environment variables for all sensitive information
- Follow secure coding practices as outlined in the design standards

## Evaluation Criteria

Implementations will be evaluated based on:
- Protocol compliance
- Functional completeness
- Code quality
- UI implementation
- Test coverage
- Performance
- LLM credit consumption

## License

This project is proprietary and confidential. All rights reserved.
