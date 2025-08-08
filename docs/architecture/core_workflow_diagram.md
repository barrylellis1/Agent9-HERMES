# Agent9 Core Workflow Diagram

## Overview

This document provides a visual representation of the core workflows in the Agent9 platform, showing how different agents interact with each other and the flow of data between them.

## Core Workflow: Automated Situation Awareness to Solution Finding

```mermaid
graph TD
    PC[PC: Principal Context] -->|Principal Context| SA[SA: Situation Awareness]
    SA -->|Situation Data| DA[DA: Deep Analysis]
    DA -->|Analysis Results| SF[SF: Solution Finder]
    SF -->|Solution Options| OA[OA: Orchestrator]
    OA -->|Workflow Control| SA
    OA -->|Workflow Control| DA
    OA -->|Workflow Control| SF
    
    %% Data-related agents
    DP[DP: Data Product] -->|Data Products| SA
    DP -->|Data Products| DA
    DG[DG: Data Governance] -->|Governance Rules| DP
    
    %% Services
    DS[DS: Data Product MCP Service] -->|Data| DP
    
    %% Interface agents
    NI[NI: NLP Interface] -->|Natural Language Processing| SA
    NI -->|Natural Language Processing| DA
    NI -->|Natural Language Processing| SF
    
    %% Service agents
    LS[LS: LLM Service] -->|LLM Processing| SA
    LS -->|LLM Processing| DA
    LS -->|LLM Processing| SF
    LS -->|LLM Processing| NI
    
    %% Orchestration connections
    OA -->|Workflow Control| DP
    OA -->|Workflow Control| DG
    OA -->|Workflow Control| NI
    OA -->|Workflow Control| LS
```

## Detailed Agent Interactions

### 1. Situation Awareness Workflow

```mermaid
sequenceDiagram
    participant OA as OA: Orchestrator
    participant PC as PC: Principal Context
    participant SA as SA: Situation Awareness
    participant DS as DS: Data Product MCP Service
    participant LS as LS: LLM Service
    
    OA->>PC: Get Principal Context
    PC-->>OA: Return Principal Context
    OA->>SA: Initiate Situation Check
    SA->>DS: Request KPI Data
    DS-->>SA: Return KPI Data
    SA->>LS: Process Situation Data
    LS-->>SA: Return Processed Insights
    SA-->>OA: Return Situation Analysis
```

### 2. Deep Analysis Workflow

```mermaid
sequenceDiagram
    participant OA as OA: Orchestrator
    participant SA as SA: Situation Awareness
    participant DA as DA: Deep Analysis
    participant DS as DS: Data Product MCP Service
    participant LS as LS: LLM Service
    
    OA->>SA: Get Situation Data
    SA-->>OA: Return Situation Data
    OA->>DA: Initiate Deep Analysis
    DA->>DS: Request Additional Data
    DS-->>DA: Return Additional Data
    DA->>LS: Process Analysis Data
    LS-->>DA: Return Processed Analysis
    DA-->>OA: Return Deep Analysis Results
```

### 3. Solution Finding Workflow

```mermaid
sequenceDiagram
    participant OA as OA: Orchestrator
    participant DA as DA: Deep Analysis
    participant SF as SF: Solution Finder
    participant LS as LS: LLM Service
    
    OA->>DA: Get Analysis Results
    DA-->>OA: Return Analysis Results
    OA->>SF: Initiate Solution Finding
    SF->>LS: Generate Solution Options
    LS-->>SF: Return Solution Options
    SF->>LS: Evaluate Solution Options
    LS-->>SF: Return Evaluation Results
    SF-->>OA: Return Solution Recommendations
```

## Data Flow Diagram

```mermaid
flowchart TD
    PR[Principal Profile] -->|contract-driven filters| OA[Orchestrator]
    OA -->|business process| DG[Data Governance Agent]
    DG -->|data product + filters| DP[Data Product Agent]
    DP -->|read contract| CT[Contract (with KPIs)]
    CT -->|KPIs & diag. questions| SA[Situation Awareness Agent]
    SA -->|for each KPI & question| NLP[NLP Interface Agent]
    NLP --> DP
    DP --> SA
    SA --> OA
    OA --> SC[Situation/Attention Card]
    LS -->|AI Processing| SF
    
    %% Data inputs
    KD[KPI Data] -->|Input| DS
    HD[Historical Data] -->|Input| DS
    DK[Domain Knowledge] -->|Input| LS
```

## Registry Integration

All agents in the Agent9 platform integrate with the Agent Registry, which provides a centralized mechanism for agent discovery, instantiation, and protocol enforcement.

```mermaid
graph TD
    OA[OA: Orchestrator] -->|Uses| AR[Agent Registry]
    AR -->|Creates| SA[SA: Situation Awareness]
    AR -->|Creates| DA[DA: Deep Analysis]
    AR -->|Creates| SF[SF: Solution Finder]
    AR -->|Creates| PC[PC: Principal Context]
    AR -->|Creates| LS[LS: LLM Service]
    AR -->|Creates| NI[NI: NLP Interface]
    AR -->|Creates| DG[DG: Data Governance]
    AR -->|Creates| DP[DP: Data Product]
```

## Implementation Notes

1. All agent interactions must follow the A2A protocol, using Pydantic models for input/output validation.
2. The Orchestrator Agent is responsible for workflow control and agent coordination.
3. All agents must be instantiated via the Agent Registry using the `create_from_registry` factory method.
4. Error handling and logging should be implemented using the shared logging utility.
5. Context fields (`principal_context`, `situation_context`, `business_context`, `extra`) must be properly propagated between agents.

## References

- [Orchestrator Agent PRD](../prd/agents/a9_orchestrator_agent_prd.md)
- [Situation Awareness Agent PRD](../prd/agents/a9_situation_awareness_agent_prd.md)
- [Deep Analysis Agent PRD](../prd/agents/a9_deep_analysis_agent_prd.md)
- [Solution Finder Agent PRD](../prd/agents/a9_solution_finder_agent_prd.md)
- [Principal Context Agent PRD](../prd/agents/a9_principal_context_agent_prd.md)
- [Data Product MCP Service PRD](../prd/services/a9_data_product_mcp_service_prd.md)
