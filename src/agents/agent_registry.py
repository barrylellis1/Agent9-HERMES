"""
Compatibility shim for tests expecting `src.agents.agent_registry`.

Exports:
- registry: singleton instance of AgentRegistry
- AgentRegistry: class definition

This module forwards to `src.agents.a9_orchestrator_agent` to avoid duplication.
"""
from .a9_orchestrator_agent import AgentRegistry, agent_registry as registry

__all__ = ["AgentRegistry", "registry"]
