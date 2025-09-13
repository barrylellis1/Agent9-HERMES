# Orchestrator-Driven Architecture Implementation

## Overview

This document details the implementation of the orchestrator-driven architecture for Agent9, which ensures proper agent lifecycle management, dependency resolution, and communication.

## Key Components

### 1. Enhanced Orchestrator Agent

The Orchestrator Agent has been enhanced to:

- Track and manage agent dependencies
- Ensure proper agent initialization order
- Handle agent lifecycle (creation, connection, disconnection)
- Provide service discovery for inter-agent communication

Key methods added:
- `register_agent_dependency`: Register dependencies for an agent
- `_resolve_agent_dependencies`: Recursively resolve agent dependencies
- `create_agent_with_dependencies`: Create an agent after resolving its dependencies

### 2. Agent Registry

The Agent Registry has been enhanced to:

- Store agent dependencies
- Track agent initialization status
- Provide methods for dependency management
- Support agent factory registration

### 3. Agent Creation and Connection Sequence

The proper sequence for agent creation and connection is:

1. Initialize Registry Factory and providers
2. Create and connect the Orchestrator Agent
3. Create and register the Data Governance Agent
4. Create and register the Principal Context Agent
5. Create and register the Data Product Agent
6. Create and register the Situation Awareness Agent
7. Connect agents in the same order as registration

This sequence is implemented in the `create_and_connect_agents` function.

### 4. Decision Studio Integration

Decision Studio has been refactored to:

- Use the orchestrator-driven architecture
- Delegate agent management to the Orchestrator Agent
- Use the `create_and_connect_agents` function for proper initialization
- Provide visual feedback during the initialization process

## Implementation Details

### Agent Dependencies

```python
# Register agent dependencies
agent_registry.register_agent_dependency("A9_Data_Product_Agent", ["A9_Data_Governance_Agent"])
agent_registry.register_agent_dependency("A9_Situation_Awareness_Agent", ["A9_Data_Product_Agent", "A9_Principal_Context_Agent"])
```

### Dependency Resolution

```python
async def _resolve_agent_dependencies(self, agent_name: str, visited: Set[str] = None) -> None:
    """
    Resolve dependencies for an agent recursively.
    
    Args:
        agent_name: Name of the agent.
        visited: Set of already visited agents (to prevent cycles).
    """
    if visited is None:
        visited = set()
        
    # Prevent cycles
    if agent_name in visited:
        self.logger.warning(f"Dependency cycle detected for {agent_name}")
        return
        
    visited.add(agent_name)
    
    # Get dependencies for this agent
    dependencies = self.registry.get_agent_dependencies(agent_name)
    if not dependencies:
        self.logger.debug(f"No dependencies found for {agent_name}")
        return
        
    self.logger.info(f"Resolving dependencies for {agent_name}: {dependencies}")
    
    # Resolve each dependency recursively
    for dependency in dependencies:
        # First resolve dependencies of the dependency
        await self._resolve_agent_dependencies(dependency, visited)
        
        # Then ensure the dependency is created
        if dependency not in self.registry.list_agents():
            self.logger.info(f"Creating dependency {dependency} for {agent_name}")
            await self.registry.get_agent(dependency)
            
    self.logger.info(f"Dependencies resolved for {agent_name}")
```

### Agent Connection

```python
# Connect agents in the same order
logger.info("Connecting agents in dependency order")

# 1. Connect Data Governance Agent
logger.info("Connecting Data Governance Agent")
try:
    await dg_agent.connect(orchestrator)
except TypeError:
    await dg_agent.connect()

# 2. Connect Principal Context Agent
logger.info("Connecting Principal Context Agent")
try:
    await pc_agent.connect(orchestrator)
except TypeError:
    await pc_agent.connect()

# 3. Connect Data Product Agent
logger.info("Connecting Data Product Agent")
try:
    await dp_agent.connect(orchestrator)
except TypeError:
    await dp_agent.connect()

# 4. Connect Situation Awareness Agent
logger.info("Connecting Situation Awareness Agent")
try:
    await sa_agent.connect(orchestrator)
except TypeError:
    await sa_agent.connect()
```

## Benefits

1. **Proper Dependency Management**
   - Agents are created and connected in the correct order
   - Dependencies are resolved automatically
   - Circular dependencies are detected and handled

2. **Simplified Agent Creation**
   - Decision Studio code is simplified
   - Agent creation is delegated to the Orchestrator
   - Consistent initialization pattern across the system

3. **Improved Error Handling**
   - Graceful handling of missing dependencies
   - Clear error messages for troubleshooting
   - Fallback mechanisms for resilience

4. **Architectural Alignment**
   - Implementation aligns with documented architecture
   - Follows protocol-based communication principles
   - Supports both UI-driven and autonomous workflows

## Future Enhancements

1. **Dynamic Dependency Resolution**
   - Support for dynamic discovery of dependencies
   - Runtime validation of dependency satisfaction

2. **Protocol Validation**
   - Runtime validation of protocol compliance
   - Automatic protocol interface verification

3. **Workflow Orchestration**
   - Enhanced workflow definition and execution
   - Support for complex agent interaction patterns
