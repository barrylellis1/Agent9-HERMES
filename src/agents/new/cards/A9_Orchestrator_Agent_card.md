# A9_Orchestrator_Agent Card

Status: Active — client_id scoped (Phase 10B) (central coordinator, agent registry singleton)

## Overview
The `A9_Orchestrator_Agent` is the central coordinator for all Agent9 workflows. It maintains the agent registry singleton, handles dependency resolution, and provides 7 workflow methods that orchestrate multi-agent pipelines (SA → DA → SF → VA).

## Protocol Entrypoints
- `get_agent(agent_name) -> AgentProtocol`
- `execute_agent_method(agent_name, method, payload) -> Dict`
- `run_situation_awareness_workflow(...) -> Dict`
- `run_deep_analysis_workflow(...) -> Dict`
- `run_solution_finder_workflow(...) -> Dict`
- `run_value_assurance_workflow(...) -> Dict`

## Notes
- All LLM calls in other agents must be routed through the orchestrator → A9_LLM_Service_Agent
- Singleton — do not instantiate directly; use `AgentRegistry.get_agent("A9_Orchestrator_Agent")`
